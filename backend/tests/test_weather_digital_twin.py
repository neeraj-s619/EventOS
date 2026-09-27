"""
Unit and Integration Tests for HackCelestial 3.0 Weather Digital Twin
Tests:
- Weather service normalization and graceful fallback
- Weather impact engine calculations (rain, wind, heat, visibility)
- Digital Twin simulation: What-If counterfactual isolation (no DB mutation)
- All scenario presets (normal, moderate_rain, heavy_rain, extreme_rain, etc.)
- Uncertainty bounds and probabilistic predictions
- Public signals (GDELT) ingestion and fallback
- Map state GeoJSON output
- Weather Digital Twin API endpoints
"""

import unittest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.database import Base, EventDB, ZoneDB, ProviderDB, VenueDB, ZoneTypeEnum, RiskLevelEnum, ProviderTypeEnum
from app.services.weather_service import WeatherService, WeatherState, classify_rain_intensity, calculate_heat_index
from app.services.weather_impact_engine import WeatherImpactEngine, WeatherImpact
from app.services.digital_twin import DigitalTwinEngine, SCENARIO_PRESETS, DTZoneState
from app.services.public_signals import PublicSignalsService, PublicSignal, PublicSignalSummary
from fastapi.testclient import TestClient
from app.main import app


class TestWeatherDigitalTwin(unittest.TestCase):
    def setUp(self):
        from sqlalchemy.pool import StaticPool
        self.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()

        # Seed sample venue & event
        self.venue = VenueDB(
            venue_id="VENUE-WANKHEDE-TEST",
            name="Wankhede Stadium",
            venue_type="Cricket Stadium",
            address="D Road, Churchgate",
            locality="Churchgate",
            city="Mumbai",
            latitude=18.9375,
            longitude=72.8265,
            official_capacity=33500,
            source_type="VERIFIED_PUBLIC"
        )
        self.db.add(self.venue)

        self.event = EventDB(
            event_id="EVT-WANKHEDE-TEST",
            venue_id="VENUE-WANKHEDE-TEST",
            name="IND vs AUS Wankhede ODI",
            start_date=datetime(2026, 10, 15, 14, 0),
            end_date=datetime(2026, 10, 15, 22, 0),
            expected_visitors=33500,
            city="Mumbai",
            source_type="VERIFIED_PUBLIC"
        )
        self.db.add(self.event)

        # Seed 3 zones
        self.zone_a = ZoneDB(
            zone_id="ZONE-A-BOWL",
            event_id="EVT-WANKHEDE-TEST",
            venue_id="VENUE-WANKHEDE-TEST",
            name="Zone A - Stadium Bowl & Stands",
            zone_type=ZoneTypeEnum.VENUE,
            capacity=28000,
            current_crowd=20000,
            inflow_per_minute=250.0,
            outflow_per_minute=50.0,
            density=2.4,
            latitude=18.9380,
            longitude=72.8260,
            risk_level=RiskLevelEnum.NORMAL
        )
        self.zone_b = ZoneDB(
            zone_id="ZONE-B-CONCOURSE",
            event_id="EVT-WANKHEDE-TEST",
            venue_id="VENUE-WANKHEDE-TEST",
            name="Zone B - North Gate & Covered Concourse",
            zone_type=ZoneTypeEnum.HOSPITALITY,
            capacity=4500,
            current_crowd=2200,
            inflow_per_minute=60.0,
            outflow_per_minute=40.0,
            density=1.5,
            latitude=18.9390,
            longitude=72.8270,
            risk_level=RiskLevelEnum.NORMAL
        )
        self.zone_c = ZoneDB(
            zone_id="ZONE-C-TRANSPORT",
            event_id="EVT-WANKHEDE-TEST",
            venue_id="VENUE-WANKHEDE-TEST",
            name="Zone C - Marine Drive & Churchgate Station Access",
            zone_type=ZoneTypeEnum.TRANSPORT,
            capacity=3000,
            current_crowd=1500,
            inflow_per_minute=50.0,
            outflow_per_minute=30.0,
            density=1.2,
            latitude=18.9360,
            longitude=72.8250,
            risk_level=RiskLevelEnum.NORMAL
        )
        self.db.add_all([self.zone_a, self.zone_b, self.zone_c])

        # Seed 2 providers (transport and hotel)
        self.prov_transport = ProviderDB(
            provider_id="PROV-BEST-BUS",
            event_id="EVT-WANKHEDE-TEST",
            zone_id="ZONE-C-TRANSPORT",
            name="BEST Special Event Fleet",
            type=ProviderTypeEnum.TRANSPORT,
            capacity={"total": 600, "available": 400, "occupied": 200},
            status="active"
        )
        self.prov_hotel = ProviderDB(
            provider_id="PROV-TAJ-PRESIDENT",
            event_id="EVT-WANKHEDE-TEST",
            zone_id="ZONE-B-CONCOURSE",
            name="Vivanta President Mumbai",
            type=ProviderTypeEnum.HOTEL,
            capacity={"total": 150, "available": 80, "occupied": 70},
            status="active"
        )
        self.db.add_all([self.prov_transport, self.prov_hotel])
        self.db.commit()

        from app.core.database import get_db
        def override_get_db():
            session = self.Session()
            try:
                yield session
            finally:
                session.close()

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)

    def tearDown(self):
        from app.core.database import get_db
        app.dependency_overrides.pop(get_db, None)
        self.db.close()
        Base.metadata.drop_all(self.engine)

    def test_01_weather_classification_and_heat_index(self):
        """Test rain intensity categorization and heat index calculation."""
        self.assertEqual(classify_rain_intensity(0.0), "none")
        self.assertEqual(classify_rain_intensity(1.5), "light")
        self.assertEqual(classify_rain_intensity(5.0), "moderate")
        self.assertEqual(classify_rain_intensity(25.0), "heavy")
        self.assertEqual(classify_rain_intensity(65.0), "extreme")

        # Heat index: when temp < 27°C, returns original temp
        self.assertEqual(calculate_heat_index(25.0, 80.0), 25.0)
        # When temp is high and humidity high, perceived temp rises
        hi = calculate_heat_index(38.0, 75.0)
        self.assertGreater(hi, 38.0)

    def test_02_weather_service_fallback(self):
        """Test that WeatherService returns a well-formed fallback WeatherState when network fails."""
        svc = WeatherService()
        fallback = svc._default_weather()
        self.assertTrue(fallback.is_fallback)
        self.assertEqual(fallback.source, "DEFAULT_FALLBACK")
        self.assertAlmostEqual(fallback.lat, 18.9375)
        self.assertAlmostEqual(fallback.lon, 72.8265)
        self.assertEqual(fallback.weather_description, "Partly cloudy")
        self.assertIsInstance(fallback.to_dict(), dict)

    def test_03_weather_impact_engine_cascade(self):
        """Test that rain cascades properly into movement, shelter demand, and risk uplift."""
        engine = WeatherImpactEngine()

        # Dry scenario
        dry_impact = engine.compute_scenario_impact(precipitation_mm_h=0.0)
        self.assertEqual(dry_impact.outdoor_movement_factor, 1.0)
        self.assertEqual(dry_impact.shelter_demand_delta, 0.0)
        self.assertEqual(dry_impact.overall_risk_uplift, 0.0)

        # Heavy rain scenario (35 mm/h)
        rain_impact = engine.compute_scenario_impact(precipitation_mm_h=35.0, wind_speed_kmh=40.0)
        self.assertEqual(rain_impact.rain_intensity, "heavy")
        self.assertLess(rain_impact.outdoor_movement_factor, 1.0)
        self.assertGreater(rain_impact.shelter_demand_delta, 0.0)
        self.assertGreater(rain_impact.transport_demand_multiplier, 1.0)
        self.assertGreater(rain_impact.overall_risk_uplift, 0.3)
        self.assertGreater(len(rain_impact.recommendations), 0)

    def test_04_digital_twin_counterfactual_isolation(self):
        """CRITICAL: Digital Twin must NEVER mutate the real event state or database."""
        twin_engine = DigitalTwinEngine(self.db)

        # Read initial real crowd in Zone B
        initial_real_crowd = self.db.query(ZoneDB).filter(ZoneDB.zone_id == "ZONE-B-CONCOURSE").first().current_crowd
        self.assertEqual(initial_real_crowd, 2200)

        # Run heavy rain simulation on Digital Twin
        sim_state = twin_engine.simulate_scenario(
            event_id="EVT-WANKHEDE-TEST",
            scenario_name="heavy_rain",
            precipitation_mm_h=35.0
        )

        # The simulated state should predict increased crowd in indoor concourse
        zone_b_sim = next(z for z in sim_state.zones if z.zone_id == "ZONE-B-CONCOURSE")
        self.assertGreater(zone_b_sim.simulated_crowd, initial_real_crowd)

        # BUT the actual DB record must remain 100% UNCHANGED
        post_db_zone_b = self.db.query(ZoneDB).filter(ZoneDB.zone_id == "ZONE-B-CONCOURSE").first()
        self.assertEqual(post_db_zone_b.current_crowd, initial_real_crowd)
        self.assertEqual(post_db_zone_b.risk_level, RiskLevelEnum.NORMAL)

    def test_05_digital_twin_scenario_presets(self):
        """Test that all 7 presets produce valid counterfactual states with appropriate risk/crowd shifts."""
        twin_engine = DigitalTwinEngine(self.db)

        for preset_name in SCENARIO_PRESETS.keys():
            result = twin_engine.simulate_scenario("EVT-WANKHEDE-TEST", scenario_name=preset_name)
            self.assertIsNotNone(result)
            self.assertEqual(result.event_id, "EVT-WANKHEDE-TEST")
            self.assertIn("crowd_delta", result.to_dict())
            self.assertIn("baseline_total_crowd", result.to_dict())
            self.assertIn("simulated_total_crowd", result.to_dict())
            self.assertGreater(result.confidence, 0.0)
            self.assertGreater(result.uncertainty_pct, 0.0)

    def test_06_uncertainty_and_probabilistic_predictions(self):
        """Verify that predictions include uncertainty bounds that widen during extreme weather."""
        twin_engine = DigitalTwinEngine(self.db)

        normal_res = twin_engine.simulate_scenario("EVT-WANKHEDE-TEST", scenario_name="normal")
        extreme_res = twin_engine.simulate_scenario("EVT-WANKHEDE-TEST", scenario_name="extreme_rain")

        # Extreme conditions widen the uncertainty bound
        self.assertGreater(extreme_res.uncertainty_pct, normal_res.uncertainty_pct)
        # Confidence is higher for normal conditions than extreme ones
        self.assertGreater(normal_res.confidence, extreme_res.confidence)

    def test_07_public_signals_service(self):
        """Test public signal parsing, relevance calculation, and fallback summary."""
        ps_svc = PublicSignalsService()
        fallback = ps_svc._empty_summary(is_fallback=True)
        self.assertTrue(fallback.is_fallback)
        self.assertEqual(fallback.source, "GDELT_API_FALLBACK")
        self.assertIn("unavailable", fallback.summary_text)

        # Test summary builder with mock signals
        sample_signals = [
            PublicSignal(
                signal_id="sig_1",
                category="weather_event",
                title="Heavy monsoon rain causes traffic jam near Churchgate Mumbai",
                url="https://example.com/news1",
                source_name="mumbailive.com",
                published_at="2026-09-27T00:00:00",
                relevance_score=0.85,
                keywords=["rain", "traffic"],
                sentiment="negative"
            )
        ]
        summary = ps_svc._build_summary(sample_signals)
        self.assertEqual(summary.total_signals, 1)
        self.assertEqual(summary.weather_signals, 1)
        self.assertEqual(summary.overall_alert_level, "moderate")

    def test_08_api_weather_endpoints(self):
        """Test FastAPI weather endpoints."""
        # Current weather
        r1 = self.client.get("/api/v1/weather/current")
        self.assertEqual(r1.status_code, 200)
        data1 = r1.json()
        self.assertEqual(data1["status"], "ok")
        self.assertIn("weather", data1)
        self.assertIn("temperature_c", data1["weather"])

        # Weather forecast
        r2 = self.client.get("/api/v1/weather/forecast")
        self.assertEqual(r2.status_code, 200)
        data2 = r2.json()
        self.assertIn("next_6h_forecast", data2)

        # Weather impact
        r3 = self.client.get("/api/v1/weather/impact")
        self.assertEqual(r3.status_code, 200)
        data3 = r3.json()
        self.assertIn("impact", data3)
        self.assertIn("outdoor_movement_factor", data3["impact"])

        # Preset scenarios list
        r4 = self.client.get("/api/v1/digital-twin/scenarios")
        self.assertEqual(r4.status_code, 200)
        data4 = r4.json()
        self.assertIn("scenarios", data4)
        self.assertIn("heavy_rain", data4["scenarios"])

    def test_09_api_digital_twin_simulation_endpoints(self):
        """Test Digital Twin simulation endpoint with presets and custom parameters."""
        # Preset simulation
        r_preset = self.client.post(
            "/api/v1/events/EVT-WANKHEDE-TEST/digital-twin/simulate",
            json={"scenario_name": "heavy_rain"}
        )
        self.assertEqual(r_preset.status_code, 200)
        data_preset = r_preset.json()
        self.assertEqual(data_preset["status"], "ok")
        self.assertIn("digital_twin", data_preset)
        self.assertEqual(data_preset["digital_twin"]["scenario_name"], "heavy_rain")

        # Custom parameter simulation
        r_custom = self.client.post(
            "/api/v1/events/EVT-WANKHEDE-TEST/digital-twin/simulate",
            json={
                "scenario_name": "normal",
                "precipitation_mm_h": 45.0,
                "wind_speed_kmh": 60.0
            }
        )
        self.assertEqual(r_custom.status_code, 200)
        data_custom = r_custom.json()
        self.assertIn("digital_twin", data_custom)
        dt = data_custom["digital_twin"]
        self.assertEqual(dt["weather"]["precipitation_mm_h"], 45.0)

    def test_10_api_map_state_geojson(self):
        """Test map state API returns GeoJSON compatible coordinates for Wankhede and zones."""
        r = self.client.get("/api/v1/events/EVT-WANKHEDE-TEST/map-state")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("venue", data)
        self.assertAlmostEqual(data["venue"]["lat"], 18.9375)
        self.assertAlmostEqual(data["venue"]["lon"], 72.8265)
        self.assertIn("zones", data)
        self.assertEqual(data["zones"]["type"], "FeatureCollection")
        self.assertGreaterEqual(len(data["zones"]["features"]), 1)


if __name__ == "__main__":
    unittest.main()

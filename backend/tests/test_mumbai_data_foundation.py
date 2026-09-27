"""
Unit and integration test suite for Real-World Mumbai Data Foundation in EVENTOS.
Verifies:
1. Wankhede Stadium metadata and official MCA capacity (~33,500).
2. Jio World Convention Centre metadata and modular room capacities (~33,840).
3. Sub-zone operational allocations and verified sources.
4. Realistic Mumbai transport and hospitality providers.
5. GET /api/v1/events/{event_id}/venue endpoint.
6. GET /api/v1/events/{event_id}/data-sources endpoint.
7. GET /api/v1/events/{event_id}/dashboard consolidated master endpoint.
8. Data mode labeled HYBRID (VERIFIED METADATA + SIMULATED SIGNALS).
"""

import sys
import os
import unittest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import init_db, get_db
from app.main import app
from app.models.database import VenueDB, EventDB, ZoneDB, ProviderDB
from app.services.mumbai_venues import (
    seed_real_mumbai_events, seed_wankhede_event, seed_jwcc_event,
    WANKHEDE_VENUE_METADATA, JWCC_VENUE_METADATA
)


class TestMumbaiDataFoundation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.db = next(get_db())
        cls.client = TestClient(app)
        cls.seeded = seed_real_mumbai_events(cls.db)

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_01_wankhede_venue_metadata(self):
        venue = self.db.query(VenueDB).filter(VenueDB.name == "Wankhede Stadium").first()
        self.assertIsNotNone(venue, "Wankhede Stadium venue record should exist")
        self.assertEqual(venue.city, "Mumbai")
        self.assertEqual(venue.state, "Maharashtra")
        self.assertEqual(venue.country, "India")
        self.assertEqual(venue.official_capacity, 33500)
        self.assertEqual(venue.source_type, "VERIFIED_PUBLIC")
        self.assertIn("Mumbai Cricket Association", venue.source_name)
        self.assertIn("MCA", venue.capacity_basis)
        self.assertAlmostEqual(venue.latitude, 18.9389, places=3)
        self.assertAlmostEqual(venue.longitude, 72.8258, places=3)

    def test_02_jwcc_venue_metadata(self):
        venue = self.db.query(VenueDB).filter(VenueDB.name == "Jio World Convention Centre").first()
        self.assertIsNotNone(venue, "JWCC venue record should exist")
        self.assertEqual(venue.city, "Mumbai")
        self.assertEqual(venue.locality, "Bandra Kurla Complex (BKC)")
        self.assertEqual(venue.official_capacity, 33840)
        self.assertEqual(venue.source_type, "VERIFIED_PUBLIC")
        self.assertIn("Factsheet", venue.source_name)
        self.assertIn("Jasmine", venue.capacity_basis)

    def test_03_wankhede_zones_topology(self):
        event = self.seeded["wankhede"]
        zones = self.db.query(ZoneDB).filter(ZoneDB.event_id == event.event_id).all()
        self.assertEqual(len(zones), 3, "Wankhede should have 3 operational sub-zones")
        
        # Verify zone names & realistic allocations
        bowl = next((z for z in zones if "Bowl" in z.name), None)
        gate = next((z for z in zones if "Churchgate" in z.name or "Gate" in z.name), None)
        approach = next((z for z in zones if "Marine Drive" in z.name), None)
        
        self.assertIsNotNone(bowl, "Bowl zone must exist")
        self.assertIsNotNone(gate, "Gate/Churchgate access zone must exist")
        self.assertIsNotNone(approach, "Marine Drive approach zone must exist")
        
        self.assertEqual(bowl.capacity, 26000)
        self.assertEqual(gate.capacity, 4500)
        self.assertEqual(approach.capacity, 3000)
        total_zone_cap = bowl.capacity + gate.capacity + approach.capacity
        self.assertEqual(total_zone_cap, 33500, "Total zone capacities must sum to Wankhede's official 33,500 capacity")
        
        for z in zones:
            self.assertEqual(z.source_type, "VERIFIED_PUBLIC")
            self.assertIsNotNone(z.description)
            self.assertGreater(len(z.description), 10)

    def test_04_jwcc_zones_topology(self):
        event = self.seeded["jwcc"]
        zones = self.db.query(ZoneDB).filter(ZoneDB.event_id == event.event_id).all()
        self.assertEqual(len(zones), 4, "JWCC should have 4 modular zones")
        
        names = [z.name for z in zones]
        self.assertTrue(any("Jasmine Halls" in n for n in names))
        self.assertTrue(any("Exhibition Pavilions" in n for n in names))
        self.assertTrue(any("Lotus Ballroom" in n for n in names))
        self.assertTrue(any("BKC Transit" in n for n in names))

    def test_05_mumbai_providers(self):
        wankhede_event = self.seeded["wankhede"]
        providers = self.db.query(ProviderDB).filter(ProviderDB.event_id == wankhede_event.event_id).all()
        self.assertGreaterEqual(len(providers), 3)
        
        # Verify real transport / hotel names
        prov_names = [p.name for p in providers]
        self.assertTrue(any("BEST" in n or "Railway" in n for n in prov_names))
        self.assertTrue(any("Taj Mahal Palace" in n or "Trident" in n for n in prov_names))
        
        for p in providers:
            self.assertEqual(p.source_type, "SIMULATED")
            self.assertIsNotNone(p.location)

    def test_06_api_get_venue(self):
        wankhede_event = self.seeded["wankhede"]
        resp = self.client.get(f"/api/v1/events/{wankhede_event.event_id}/venue")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["name"], "Wankhede Stadium")
        self.assertEqual(data["official_capacity"], 33500)
        self.assertEqual(data["source_type"], "VERIFIED_PUBLIC")

    def test_07_api_get_data_sources(self):
        wankhede_event = self.seeded["wankhede"]
        resp = self.client.get(f"/api/v1/events/{wankhede_event.event_id}/data-sources")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["data_mode"], "HYBRID (VERIFIED METADATA + SIMULATED SIGNALS)")
        self.assertIn("venue_metadata", data)
        self.assertIn("telemetry_signals", data)
        self.assertEqual(data["venue_metadata"]["source_type"], "VERIFIED_PUBLIC")
        self.assertEqual(data["telemetry_signals"]["cctv_simulation"]["mode"], "SIMULATED")
        self.assertEqual(data["telemetry_signals"]["whatsapp_sandbox"]["mode"], "SANDBOX / SIMULATED")

    def test_08_api_get_dashboard_master(self):
        wankhede_event = self.seeded["wankhede"]
        resp = self.client.get(f"/api/v1/events/{wankhede_event.event_id}/dashboard")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        
        # Verify master structure
        self.assertEqual(data["data_mode"], "HYBRID (VERIFIED METADATA + SIMULATED SIGNALS)")
        self.assertEqual(data["event"]["event_id"], wankhede_event.event_id)
        self.assertIsNotNone(data["venue"])
        self.assertEqual(data["venue"]["name"], "Wankhede Stadium")
        
        # Verify human-readable zones
        self.assertEqual(len(data["zones"]), 3)
        for z in data["zones"]:
            self.assertIn("Zone", z["name"])
            self.assertIsNotNone(z["description"])
            self.assertGreater(z["operational_capacity"], 0)
            self.assertEqual(z["source_type"], "VERIFIED_PUBLIC")
            
        # Verify KPIs have source & meaning
        kpis = data["kpis"]
        self.assertIn("total_crowd", kpis)
        self.assertIn("total_capacity", kpis)
        self.assertEqual(kpis["total_capacity"]["value"], 33500)
        self.assertIn("meaning", kpis["total_crowd"])
        self.assertIn("source", kpis["total_crowd"])
        self.assertIn("meaning", kpis["total_capacity"])
        self.assertIn("source", kpis["total_capacity"])
        
        # Verify signal provenance
        signals = data["signals"]
        self.assertEqual(signals["cctv"]["mode"], "SIMULATED")
        self.assertEqual(signals["venue_metadata"]["mode"], "VERIFIED_PUBLIC")


if __name__ == "__main__":
    unittest.main()

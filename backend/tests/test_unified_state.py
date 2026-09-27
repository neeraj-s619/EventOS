"""
Phase 11: Unified Event State Consistency Tests
Comprehensive testing of Unified Event State generation and consistency:
- Complete schema verification: timestamp, event metadata, zones, provider capacities, forecasts, active recommendations
- State freshness: reflects crowd updates immediately
- Provider capacity reflection: dynamic recalculation upon provider capacity changes
- Recommendation tracking: active recommendations (pending, approved, executing) are included
- Snapshot persistence in UnifiedEventStateDB
"""

import sys
import os
import unittest
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import init_db, get_db
from app.models.database import (
    EventDB, ZoneDB, ProviderDB, ProviderTypeEnum, ProviderStatusEnum,
    ZoneTypeEnum, RiskLevelEnum, UnifiedEventStateDB, ForecastDB
)
from app.main import get_unified_state
from app.services.cctv_adapter import CCTVAdapter, CCTVTelemetry
from app.services.orchestration import OrchestrationEngine


class TestUnifiedEventState(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def setUp(self):
        self.db = next(get_db())
        self.event = EventDB(
            name="World Expo Unified Test",
            start_date=datetime(2026, 12, 1),
            end_date=datetime(2026, 12, 10),
            expected_visitors=60000
        )
        self.db.add(self.event)
        self.db.commit()
        self.db.refresh(self.event)

        self.zone1 = ZoneDB(
            event_id=self.event.event_id,
            name="Expo Hall A",
            capacity=20000,
            current_crowd=8000,
            inflow_per_minute=100.0,
            outflow_per_minute=80.0,
            density=0.4,
            zone_type=ZoneTypeEnum.VENUE,
            risk_level=RiskLevelEnum.NORMAL
        )
        self.zone2 = ZoneDB(
            event_id=self.event.event_id,
            name="Expo Plaza B",
            capacity=15000,
            current_crowd=4000,
            inflow_per_minute=50.0,
            outflow_per_minute=50.0,
            density=0.266,
            zone_type=ZoneTypeEnum.PEDESTRIAN,
            risk_level=RiskLevelEnum.NORMAL
        )
        self.db.add_all([self.zone1, self.zone2])
        self.db.commit()
        self.db.refresh(self.zone1)
        self.db.refresh(self.zone2)

        self.cctv_adapter = CCTVAdapter(self.db)
        self.orchestration = OrchestrationEngine(self.db)

    def tearDown(self):
        self.db.close()

    def test_unified_state_schema_completeness(self):
        """Unified state returns all required fields and correct data types."""
        state = get_unified_state(self.event.event_id, db=self.db)

        self.assertEqual(state.event_id, self.event.event_id)
        self.assertIsNotNone(state.timestamp)
        total_visitors = sum(z["crowd"] for z in state.zones.values())
        self.assertEqual(total_visitors, 12000)  # 8000 + 4000

        # Check zone data completeness
        self.assertIn(self.zone1.zone_id, state.zones)
        self.assertIn(self.zone2.zone_id, state.zones)

        z1 = state.zones[self.zone1.zone_id]
        expected_keys = [
            "crowd", "inflow", "outflow", "capacity", "utilization",
            "net_flow", "hotel_capacity", "transport_capacity",
            "venue_capacity", "risk_level"
        ]
        for key in expected_keys:
            self.assertIn(key, z1)

    def test_state_freshness_after_crowd_update(self):
        """Unified state reflects newly ingested crowd telemetry without delay."""
        # Initial crowd was 8000
        state1 = get_unified_state(self.event.event_id, db=self.db)
        self.assertEqual(state1.zones[self.zone1.zone_id]["crowd"], 8000)

        # Ingest new CCTV telemetry
        telemetry = CCTVTelemetry(
            zone_id=self.zone1.zone_id,
            people_count=14500,
            inflow_per_minute=220.0,
            outflow_per_minute=70.0
        )
        self.cctv_adapter.ingest_telemetry(telemetry)

        # Fresh query
        state2 = get_unified_state(self.event.event_id, db=self.db)
        self.assertEqual(state2.zones[self.zone1.zone_id]["crowd"], 14500)
        self.assertEqual(state2.zones[self.zone1.zone_id]["inflow"], 220.0)
        total_visitors = sum(z["crowd"] for z in state2.zones.values())
        self.assertEqual(total_visitors, 18500)  # 14500 + 4000

    def test_provider_capacity_dynamic_reflection(self):
        """Unified state accurately aggregates and updates available provider capacity."""
        hotel = ProviderDB(
            event_id=self.event.event_id,
            zone_id=self.zone1.zone_id,
            type=ProviderTypeEnum.HOTEL,
            name="Expo Hotel",
            capacity={"total": 300, "available": 120, "occupied": 180},
            status=ProviderStatusEnum.ACTIVE
        )
        self.db.add(hotel)
        self.db.commit()

        state = get_unified_state(self.event.event_id, db=self.db)
        self.assertEqual(state.zones[self.zone1.zone_id]["hotel_capacity"], 120)

        # Update available rooms
        hotel.capacity = {"total": 300, "available": 45, "occupied": 255}
        self.db.commit()

        state2 = get_unified_state(self.event.event_id, db=self.db)
        self.assertEqual(state2.zones[self.zone1.zone_id]["hotel_capacity"], 45)

    def test_active_recommendations_and_forecasts_in_unified_state(self):
        """Unified state includes forecast predictions and active recommendations."""
        # Add a forecast
        forecast = ForecastDB(
            event_id=self.event.event_id,
            zone_id=self.zone1.zone_id,
            horizon_minutes=20,
            predicted_crowd=16000,
            predicted_inflow=180.0,
            predicted_outflow=90.0,
            predicted_utilization=80.0,
            confidence=0.92
        )
        self.db.add(forecast)

        # Add a recommendation
        rec_data = {
            "type": "increase_transport",
            "description": "Increase shuttle frequency to Expo Hall A",
            "actions": [{"action": "dispatch_buses", "count": 4}],
            "required_providers": []
        }
        self.orchestration.create_recommendation_record(
            event_id=self.event.event_id,
            zone_id=self.zone1.zone_id,
            recommendation=rec_data
        )

        state = get_unified_state(self.event.event_id, db=self.db)
        z1_data = state.zones[self.zone1.zone_id]

        self.assertIn("forecast", z1_data)
        self.assertEqual(len(z1_data["forecast"]), 1)
        self.assertEqual(z1_data["forecast"][0]["predicted_crowd"], 16000)

        self.assertIn("active_recommendations", z1_data)
        self.assertEqual(len(z1_data["active_recommendations"]), 1)
        self.assertEqual(z1_data["active_recommendations"][0]["type"], "increase_transport")

    def test_unified_state_snapshot_persistence(self):
        """Snapshots can be persisted to UnifiedEventStateDB and reloaded."""
        state = get_unified_state(self.event.event_id, db=self.db)

        snapshot = UnifiedEventStateDB(
            event_id=self.event.event_id,
            timestamp=datetime.utcnow(),
            state=state.model_dump(mode="json")
        )
        self.db.add(snapshot)
        self.db.commit()
        self.db.refresh(snapshot)

        self.assertIsNotNone(snapshot.id)
        self.assertEqual(snapshot.state["event_id"], self.event.event_id)
        self.assertEqual(sum(z["crowd"] for z in snapshot.state["zones"].values()), 12000)


if __name__ == "__main__":
    unittest.main()

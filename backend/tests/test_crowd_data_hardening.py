"""
Phases 9 & 14: Crowd Data Hardening & CCTV Adapter Tests
Comprehensive testing of crowd ingestion safeguards:
- Input sanitization (negative people count, negative inflow, negative outflow clamped to 0)
- Zero-capacity zone division-by-zero protection
- CCTVAdapter real vs simulated telemetry ingestion
- Density calculation fallback when density is omitted
- Nonexistent zone error handling
- Source tagging (real_cctv_cv vs simulated_cctv)
"""

import sys
import os
import unittest
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import init_db, get_db
from app.models.database import EventDB, ZoneDB, ZoneTypeEnum, ZoneCrowdStateDB, RiskLevelEnum
from app.services.cctv_adapter import CCTVAdapter, CCTVTelemetry, CrowdDataSource
from app.main import create_crowd_state
from app.schemas.event import ZoneCrowdStateCreate


class TestCrowdDataHardening(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def setUp(self):
        self.db = next(get_db())
        self.event = EventDB(
            name="Crowd Data Hardening Event",
            start_date=datetime(2026, 10, 1),
            end_date=datetime(2026, 10, 5),
            expected_visitors=40000
        )
        self.db.add(self.event)
        self.db.commit()
        self.db.refresh(self.event)

        self.zone = ZoneDB(
            event_id=self.event.event_id,
            name="Grand Concourse",
            capacity=10000,
            current_crowd=2000,
            zone_type=ZoneTypeEnum.VENUE,
            risk_level=RiskLevelEnum.NORMAL
        )
        self.db.add(self.zone)
        self.db.commit()
        self.db.refresh(self.zone)

        self.adapter = CCTVAdapter(self.db)

    def tearDown(self):
        self.db.close()

    def test_negative_values_sanitization_in_cctv_telemetry(self):
        """Negative counts and flows are sanitized to non-negative values."""
        telemetry = CCTVTelemetry(
            zone_id=self.zone.zone_id,
            people_count=-150,
            inflow_per_minute=-25.5,
            outflow_per_minute=-10.0
        )
        self.assertEqual(telemetry.people_count, 0)
        self.assertEqual(telemetry.inflow_per_minute, 0.0)
        self.assertEqual(telemetry.outflow_per_minute, 0.0)

        # Ingest into zone
        state = self.adapter.ingest_telemetry(telemetry)
        self.assertEqual(state.people_count, 0)
        self.assertEqual(state.inflow_per_minute, 0.0)
        self.assertEqual(state.outflow_per_minute, 0.0)

        # Confirm zone was updated with sanitized values
        self.db.refresh(self.zone)
        self.assertEqual(self.zone.current_crowd, 0)
        self.assertEqual(self.zone.inflow_per_minute, 0.0)
        self.assertEqual(self.zone.outflow_per_minute, 0.0)

    def test_zero_capacity_zone_zero_division_protection(self):
        """Zero capacity zone avoids ZeroDivisionError and sets safe density."""
        zero_zone = ZoneDB(
            event_id=self.event.event_id,
            name="Auxiliary Corridor Zero Cap",
            capacity=0,
            current_crowd=0,
            zone_type=ZoneTypeEnum.PEDESTRIAN,
            risk_level=RiskLevelEnum.NORMAL
        )
        self.db.add(zero_zone)
        self.db.commit()
        self.db.refresh(zero_zone)

        telemetry = CCTVTelemetry(
            zone_id=zero_zone.zone_id,
            people_count=120,
            inflow_per_minute=15.0,
            outflow_per_minute=10.0,
            density=None
        )
        # Should not raise ZeroDivisionError
        state = self.adapter.ingest_telemetry(telemetry)
        self.assertEqual(state.density, 0.0)
        self.assertEqual(state.people_count, 120)

    def test_cctv_adapter_real_cv_ingestion(self):
        """Real CV camera ingestion tags source correctly and updates zone metrics."""
        state = self.adapter.ingest_real_cv(
            zone_id=self.zone.zone_id,
            people_count=3500,
            inflow_per_minute=75.0,
            outflow_per_minute=50.0,
            camera_id="CAM-SOUTH-04",
            confidence=0.98,
            movement_direction="NORTH",
            movement_speed=1.2
        )
        self.assertEqual(state.source, "real_cctv_cv")
        self.assertEqual(state.people_count, 3500)
        self.assertEqual(state.density, 0.35)  # 3500 / 10000

        self.db.refresh(self.zone)
        self.assertEqual(self.zone.current_crowd, 3500)
        self.assertEqual(self.zone.density, 0.35)

    def test_cctv_adapter_simulated_ingestion(self):
        """Simulated CCTV ingestion tags source as simulated_cctv."""
        state = self.adapter.ingest_simulated(
            zone_id=self.zone.zone_id,
            people_count=1800,
            inflow_per_minute=40.0,
            outflow_per_minute=35.0
        )
        self.assertEqual(state.source, "simulated_cctv")
        self.assertEqual(state.people_count, 1800)

    def test_create_crowd_state_clamping_via_api(self):
        """API create_crowd_state clamps negative numbers cleanly."""
        payload = ZoneCrowdStateCreate(
            people_count=-200,
            inflow_per_minute=-50.0,
            outflow_per_minute=-20.0,
            density=-0.5
        )
        created = create_crowd_state(self.zone.zone_id, payload, db=self.db)
        self.assertEqual(created.people_count, 0)
        self.assertEqual(created.inflow_per_minute, 0.0)
        self.assertEqual(created.outflow_per_minute, 0.0)
        self.assertEqual(created.density, 0.0)

    def test_ingest_telemetry_nonexistent_zone(self):
        """Ingesting telemetry on non-existent zone raises ValueError."""
        telemetry = CCTVTelemetry(
            zone_id="NON_EXISTENT_ZONE_ID",
            people_count=500,
            inflow_per_minute=10.0,
            outflow_per_minute=5.0
        )
        with self.assertRaises(ValueError):
            self.adapter.ingest_telemetry(telemetry)


if __name__ == "__main__":
    unittest.main()

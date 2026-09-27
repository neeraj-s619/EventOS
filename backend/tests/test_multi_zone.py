"""
Phase 10: Multi-Zone Cascading Scenario Tests
Comprehensive testing of multi-zone cascading dynamics:
- Multi-zone topology: Zone A (venue) -> Zone B (hospitality) -> Zone C (transport hub)
- Scenario 1: Zone A overloaded + Zone B has spare capacity -> demand redirect to B via C transport
- Scenario 2: Both Zone A & Zone B overloaded -> no circular redirect between overloaded zones
- Scenario 3: All zones overloaded (A, B, C) -> system does NOT invent phantom capacity, flags overload/emergency
- Event-wide aggregate risk level calculation reflecting highest severity zone
"""

import sys
import os
import unittest
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import init_db, get_db
from app.models.database import (
    EventDB, ZoneDB, ProviderDB, ProviderTypeEnum, ProviderStatusEnum,
    ZoneTypeEnum, RiskLevelEnum
)
from app.services.orchestration import OrchestrationEngine
from app.services.risk import RiskEngine


class TestMultiZoneCascading(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def setUp(self):
        self.db = next(get_db())
        self.event = EventDB(
            name="Multi-Zone Championship",
            start_date=datetime(2026, 11, 1),
            end_date=datetime(2026, 11, 5),
            expected_visitors=80000
        )
        self.db.add(self.event)
        self.db.commit()
        self.db.refresh(self.event)

        # Zone A: Venue
        self.zone_a = ZoneDB(
            event_id=self.event.event_id,
            name="Zone A - Stadium Bowl",
            capacity=40000,
            current_crowd=15000,
            inflow_per_minute=50.0,
            outflow_per_minute=50.0,
            density=0.375,
            zone_type=ZoneTypeEnum.VENUE,
            risk_level=RiskLevelEnum.NORMAL
        )
        # Zone B: Hospitality
        self.zone_b = ZoneDB(
            event_id=self.event.event_id,
            name="Zone B - Fan Festival & Food",
            capacity=30000,
            current_crowd=10000,
            inflow_per_minute=40.0,
            outflow_per_minute=40.0,
            density=0.333,
            zone_type=ZoneTypeEnum.HOSPITALITY,
            risk_level=RiskLevelEnum.NORMAL
        )
        # Zone C: Transport Hub
        self.zone_c = ZoneDB(
            event_id=self.event.event_id,
            name="Zone C - Transit Center",
            capacity=20000,
            current_crowd=5000,
            inflow_per_minute=30.0,
            outflow_per_minute=30.0,
            density=0.25,
            zone_type=ZoneTypeEnum.TRANSPORT,
            risk_level=RiskLevelEnum.NORMAL
        )
        self.db.add_all([self.zone_a, self.zone_b, self.zone_c])
        self.db.commit()
        for z in [self.zone_a, self.zone_b, self.zone_c]:
            self.db.refresh(z)

        # Providers in Zone C (Transport)
        self.shuttle_c = ProviderDB(
            event_id=self.event.event_id,
            zone_id=self.zone_c.zone_id,
            type=ProviderTypeEnum.TRANSPORT,
            name="Metro Fleet Hub Shuttles",
            capacity={"total": 100, "available": 80, "occupied": 20},
            status=ProviderStatusEnum.ACTIVE
        )
        # Providers in Zone B (Hospitality / Food)
        self.venue_b = ProviderDB(
            event_id=self.event.event_id,
            zone_id=self.zone_b.zone_id,
            type=ProviderTypeEnum.VENUE,
            name="Fan Village Pavilion",
            capacity={"total": 20000, "available": 12000, "occupied": 8000},
            status=ProviderStatusEnum.ACTIVE
        )
        self.db.add_all([self.shuttle_c, self.venue_b])
        self.db.commit()

        self.orchestration = OrchestrationEngine(self.db)
        self.risk_engine = RiskEngine(self.db)

    def tearDown(self):
        self.db.close()

    def test_zone_a_overloaded_redirects_to_zone_b_using_zone_c_transport(self):
        """Zone A overloaded (> 90%) redirects to Zone B (< 60%), utilizing Zone C transit."""
        self.zone_a.current_crowd = 37000  # 92.5% utilization
        self.zone_a.inflow_per_minute = 500.0
        self.zone_a.outflow_per_minute = 50.0
        self.zone_a.density = 0.925
        self.zone_a.risk_level = RiskLevelEnum.CRITICAL

        # Zone B has plenty of space: 10,000 / 30,000 = 33%
        self.zone_b.current_crowd = 10000
        self.zone_b.risk_level = RiskLevelEnum.NORMAL

        self.db.commit()

        recs = self.orchestration.generate_recommendations(self.event.event_id)
        redirect_recs = [r for r in recs if r.get("type") == "demand_redirect"]

        self.assertGreaterEqual(len(redirect_recs), 1)
        # Target zone should be Zone B
        target_zones = [r.get("target_zone_id") for r in redirect_recs]
        self.assertIn(self.zone_b.zone_id, target_zones)

        # Transport shuttles from Zone C should be included in required_providers
        req_provs = []
        for r in redirect_recs:
            req_provs.extend(r.get("required_providers", []))
        self.assertIn(self.shuttle_c.provider_id, req_provs)

    def test_both_zone_a_and_zone_b_overloaded_no_circular_redirect(self):
        """When both Zone A & B are overloaded (> 90%), system does NOT redirect between them."""
        # Zone A overloaded
        self.zone_a.current_crowd = 38000  # 95%
        self.zone_a.inflow_per_minute = 400.0
        self.zone_a.outflow_per_minute = 100.0
        self.zone_a.risk_level = RiskLevelEnum.CRITICAL

        # Zone B also overloaded
        self.zone_b.current_crowd = 28500  # 95%
        self.zone_b.inflow_per_minute = 300.0
        self.zone_b.outflow_per_minute = 80.0
        self.zone_b.risk_level = RiskLevelEnum.CRITICAL

        # Zone C also near capacity (18000 / 20000 = 90%)
        self.zone_c.current_crowd = 18000
        self.zone_c.risk_level = RiskLevelEnum.WARNING

        self.db.commit()

        recs = self.orchestration.generate_recommendations(self.event.event_id)
        # Verify no redirect directs crowd into an already overloaded zone
        for r in recs:
            if r.get("type") == "demand_redirect":
                self.assertNotIn(r.get("target_zone_id"), [self.zone_a.zone_id, self.zone_b.zone_id])

    def test_all_zones_overloaded_does_not_invent_capacity(self):
        """When all zones are > 90% full, system generates zero demand redirects and flags risk."""
        self.zone_a.current_crowd = 39000  # 97.5%
        self.zone_a.risk_level = RiskLevelEnum.CRITICAL

        self.zone_b.current_crowd = 29000  # 96.7%
        self.zone_b.risk_level = RiskLevelEnum.CRITICAL

        self.zone_c.current_crowd = 19500  # 97.5%
        self.zone_c.risk_level = RiskLevelEnum.CRITICAL

        self.db.commit()

        recs = self.orchestration.generate_recommendations(self.event.event_id)
        redirect_recs = [r for r in recs if r.get("type") == "demand_redirect"]

        # No spare zone capacity exists, so no demand redirects can be made
        self.assertEqual(len(redirect_recs), 0)

    def test_event_wide_risk_assessment_multi_zone(self):
        """Event-wide risk assessment properly aggregates maximum zone severity."""
        self.zone_a.current_crowd = 38000
        self.zone_a.inflow_per_minute = 500.0
        self.zone_a.outflow_per_minute = 50.0

        self.zone_b.current_crowd = 5000
        self.zone_b.inflow_per_minute = 20.0
        self.zone_b.outflow_per_minute = 20.0

        self.zone_c.current_crowd = 3000
        self.zone_c.inflow_per_minute = 10.0
        self.zone_c.outflow_per_minute = 10.0

        self.db.commit()

        results = self.risk_engine.assess_event_risk(self.event.event_id)
        self.assertEqual(len(results), 3)

        summary = self.risk_engine.get_risk_summary(self.event.event_id)
        self.assertEqual(summary["overall_risk"], RiskLevelEnum.CRITICAL)
        self.assertGreater(len(summary["critical_zones"]), 0)


if __name__ == "__main__":
    unittest.main()

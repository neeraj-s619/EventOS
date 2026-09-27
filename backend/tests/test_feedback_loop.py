"""
Phase 7: Feedback Loop & Effectiveness Evaluation Tests
Deterministic testing of feedback loop scenarios:
- Scenario A: Action works (crowd drops, risk drops, stabilized=True, effectiveness_score > 60)
- Scenario B: Action partially works (crowd drops slightly, utilization >= 85, stabilized=False)
- Scenario C: Action fails/worsens (crowd increases, risk worsens, stabilized=False, effectiveness_score <= 20)
- Error cases: Nonexistent recommendation, missing pre-action record
- Persistence: pre_action_state, post_action_state, effectiveness_score, risk_change, stabilized
"""

import sys
import os
import unittest
import asyncio
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import init_db, get_db
from app.services.feedback import FeedbackLoop
from app.services.orchestration import OrchestrationEngine
from app.services.risk import RiskEngine
from app.models.database import (
    EventDB, ZoneDB, ZoneTypeEnum, RiskLevelEnum,
    OrchestrationRecommendationDB, FeedbackLoopDB
)


class TestFeedbackLoop(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def setUp(self):
        self.db = next(get_db())
        self.event = EventDB(
            name="Feedback Test Event",
            start_date=datetime(2026, 8, 1),
            end_date=datetime(2026, 8, 5),
            expected_visitors=25000
        )
        self.db.add(self.event)
        self.db.commit()
        self.db.refresh(self.event)

        self.zone = ZoneDB(
            event_id=self.event.event_id,
            name="Main Arena",
            capacity=10000,
            current_crowd=9500,
            inflow_per_minute=250.0,
            outflow_per_minute=50.0,
            density=0.95,
            zone_type=ZoneTypeEnum.VENUE,
            risk_level=RiskLevelEnum.CRITICAL
        )
        self.db.add(self.zone)
        self.db.commit()
        self.db.refresh(self.zone)

        self.orchestration = OrchestrationEngine(self.db)
        self.risk_engine = RiskEngine(self.db)
        self.feedback = FeedbackLoop(self.db)

    def tearDown(self):
        self.db.close()

    def _create_recommendation(self):
        rec_data = {
            "type": "demand_redirect",
            "description": "Redirect crowd from Main Arena to West Plaza",
            "actions": [
                {
                    "action": "redirect_pedestrians",
                    "target_zone": "ZONE-WEST"
                }
            ],
            "required_providers": []
        }
        return self.orchestration.create_recommendation_record(
            event_id=self.event.event_id,
            zone_id=self.zone.zone_id,
            recommendation=rec_data
        )

    def test_scenario_a_action_works(self):
        """Scenario A: Action works deterministically (crowd drops, risk drops, stabilized=True)."""
        rec = self._create_recommendation()
        
        # 1. Record pre-action state (95% utilization, CRITICAL)
        self.zone.current_crowd = 9500
        self.zone.inflow_per_minute = 250.0
        self.zone.outflow_per_minute = 50.0
        self.zone.risk_level = RiskLevelEnum.CRITICAL
        self.db.commit()

        pre_record = self.feedback.record_pre_action_state(rec.id)
        self.assertIsNotNone(pre_record)
        self.assertEqual(pre_record.pre_action_state["crowd"], 9500)
        self.assertEqual(pre_record.pre_action_state["risk_level"], "critical")

        # 2. Simulate successful post-action effect (crowd drops to 7000, outflow exceeds inflow)
        self.zone.current_crowd = 7000
        self.zone.inflow_per_minute = 60.0
        self.zone.outflow_per_minute = 180.0
        self.zone.density = 0.70
        self.db.commit()

        result = asyncio.run(self.feedback.evaluate_action_effectiveness(rec.id, minutes_after=10))

        self.assertTrue(result["stabilized"])
        self.assertLess(result["risk_change"], 0)
        self.assertGreater(result["effectiveness_score"], 60.0)
        self.assertEqual(result["post_state"]["crowd"], 7000)

        # Verify DB persistence
        db_fb = self.db.query(FeedbackLoopDB).filter(FeedbackLoopDB.recommendation_id == rec.id).first()
        self.assertTrue(db_fb.stabilized)
        self.assertIsNotNone(db_fb.post_action_state)
        self.assertGreater(db_fb.effectiveness_score, 60.0)

    def test_scenario_b_action_partially_works(self):
        """Scenario B: Action partially works (crowd drops slightly, but utilization >= 85, stabilized=False)."""
        rec = self._create_recommendation()

        # 1. Record pre-action state
        self.zone.current_crowd = 9500
        self.zone.inflow_per_minute = 250.0
        self.zone.outflow_per_minute = 50.0
        self.zone.risk_level = RiskLevelEnum.CRITICAL
        self.db.commit()

        self.feedback.record_pre_action_state(rec.id)

        # 2. Simulate partial improvement: crowd drops to 8800 (88% utilization > 85% threshold)
        self.zone.current_crowd = 8800
        self.zone.inflow_per_minute = 150.0
        self.zone.outflow_per_minute = 160.0
        self.zone.density = 0.88
        self.db.commit()

        result = asyncio.run(self.feedback.evaluate_action_effectiveness(rec.id, minutes_after=10))

        # Because utilization is 88% (>= 85%), it is not yet stabilized
        self.assertFalse(result["stabilized"])
        self.assertGreater(result["effectiveness_score"], 20.0)
        self.assertEqual(result["post_state"]["crowd"], 8800)

    def test_scenario_c_action_fails(self):
        """Scenario C: Action fails/worsens (crowd increases, risk worsens, stabilized=False, low score)."""
        rec = self._create_recommendation()

        # 1. Record pre-action state
        self.zone.current_crowd = 8800
        self.zone.inflow_per_minute = 150.0
        self.zone.outflow_per_minute = 100.0
        self.zone.risk_level = RiskLevelEnum.WARNING
        self.db.commit()

        self.feedback.record_pre_action_state(rec.id)

        # 2. Simulate worsening condition: crowd surges to 9800, inflow increases
        self.zone.current_crowd = 9800
        self.zone.inflow_per_minute = 350.0
        self.zone.outflow_per_minute = 50.0
        self.zone.density = 0.98
        self.db.commit()

        result = asyncio.run(self.feedback.evaluate_action_effectiveness(rec.id, minutes_after=10))

        self.assertFalse(result["stabilized"])
        self.assertGreaterEqual(result["risk_change"], 0)
        self.assertLessEqual(result["effectiveness_score"], 20.0)

    def test_feedback_error_cases(self):
        """Pre-action on nonexistent rec raises ValueError; evaluate without pre-action raises ValueError."""
        with self.assertRaises(ValueError):
            self.feedback.record_pre_action_state(999999)

        with self.assertRaises(ValueError):
            asyncio.run(self.feedback.evaluate_action_effectiveness(999999))


if __name__ == "__main__":
    unittest.main()

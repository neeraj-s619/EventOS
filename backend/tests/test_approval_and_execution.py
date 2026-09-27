"""
Phases 5 & 6: Human Approval and Action Execution Tests
Comprehensive testing of recommendation approval, rejection, duplicate safeguards,
action execution lifecycle (dispatched -> executing -> executed / failed),
and system-level actions without specific provider assignments.
"""

import sys
import os
import unittest
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import init_db, get_db
from app.services.orchestration import OrchestrationEngine
from app.models.database import (
    EventDB, ZoneDB, ProviderDB, ProviderTypeEnum, ProviderStatusEnum,
    ZoneTypeEnum, OrchestrationRecommendationDB, ActionExecutionDB
)


class TestApprovalAndExecution(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def setUp(self):
        self.db = next(get_db())
        self.event = EventDB(
            name="Approval & Execution Event",
            start_date=datetime(2026, 6, 1),
            end_date=datetime(2026, 6, 5),
            expected_visitors=20000
        )
        self.db.add(self.event)
        self.db.commit()
        self.db.refresh(self.event)

        self.zone = ZoneDB(
            event_id=self.event.event_id,
            name="North Plaza",
            capacity=10000,
            current_crowd=8500,
            zone_type=ZoneTypeEnum.PEDESTRIAN
        )
        self.db.add(self.zone)
        self.db.commit()
        self.db.refresh(self.zone)

        self.provider = ProviderDB(
            event_id=self.event.event_id,
            zone_id=self.zone.zone_id,
            type=ProviderTypeEnum.TRANSPORT,
            name="North Shuttles",
            capacity={"total": 50, "available": 20, "occupied": 30},
            status=ProviderStatusEnum.ACTIVE
        )
        self.db.add(self.provider)
        self.db.commit()
        self.db.refresh(self.provider)

        self.orchestration = OrchestrationEngine(self.db)

    def tearDown(self):
        self.db.close()

    def _create_sample_recommendation(self, provider_id=None):
        rec_data = {
            "type": "increase_transport",
            "description": "Deploy additional shuttles to alleviate North Plaza congestion",
            "actions": [
                {
                    "action": "dispatch_buses",
                    "count": 5,
                    "target_zone": self.zone.zone_id
                }
            ],
            "required_providers": [provider_id] if provider_id else []
        }
        return self.orchestration.create_recommendation_record(
            event_id=self.event.event_id,
            zone_id=self.zone.zone_id,
            recommendation=rec_data
        )

    def test_approve_recommendation(self):
        """Phase 5: Approving a recommendation changes status to approved and logs user."""
        rec = self._create_sample_recommendation(provider_id=self.provider.provider_id)
        self.assertEqual(rec.status, "pending")

        approved = self.orchestration.approve_recommendation(rec.id, approved_by="Commander_Smith")
        self.assertEqual(approved.status, "approved")
        self.assertEqual(approved.approved_by, "Commander_Smith")
        self.assertIsNotNone(approved.approved_at)

        # Verify dispatched actions
        actions = self.db.query(ActionExecutionDB).filter(
            ActionExecutionDB.recommendation_id == rec.id
        ).all()
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0].status, "dispatched")
        self.assertEqual(actions[0].provider_id, self.provider.provider_id)

    def test_reject_recommendation(self):
        """Phase 5: Rejecting a recommendation changes status to rejected and stores reason."""
        rec = self._create_sample_recommendation(provider_id=self.provider.provider_id)
        rejected = self.orchestration.reject_recommendation(
            rec.id,
            rejected_by="Commander_Smith",
            reason="Crowd dispersing on its own"
        )
        self.assertEqual(rejected.status, "rejected")
        self.assertEqual(rejected.approved_by, "Commander_Smith")
        self.assertIn("Crowd dispersing on its own", rejected.description)

        # Confirm no actions were dispatched
        actions = self.db.query(ActionExecutionDB).filter(
            ActionExecutionDB.recommendation_id == rec.id
        ).all()
        self.assertEqual(len(actions), 0)

    def test_duplicate_approve_rejected(self):
        """Duplicate approval attempts are rejected with ValueError."""
        rec = self._create_sample_recommendation(provider_id=self.provider.provider_id)
        self.orchestration.approve_recommendation(rec.id, approved_by="Officer_A")

        with self.assertRaises(ValueError) as ctx:
            self.orchestration.approve_recommendation(rec.id, approved_by="Officer_B")
        self.assertIn("already approved", str(ctx.exception).lower())

    def test_duplicate_reject_rejected(self):
        """Duplicate rejection attempts are rejected with ValueError."""
        rec = self._create_sample_recommendation(provider_id=self.provider.provider_id)
        self.orchestration.reject_recommendation(rec.id, rejected_by="Officer_A", reason="Not needed")

        with self.assertRaises(ValueError) as ctx:
            self.orchestration.reject_recommendation(rec.id, rejected_by="Officer_B", reason="Duplicate")
        self.assertIn("already rejected", str(ctx.exception).lower())

    def test_cannot_cross_approve_or_reject(self):
        """Cannot approve a rejected recommendation, and cannot reject an approved recommendation."""
        rec1 = self._create_sample_recommendation(provider_id=self.provider.provider_id)
        self.orchestration.reject_recommendation(rec1.id, rejected_by="Officer_A", reason="Canceled")
        with self.assertRaises(ValueError):
            self.orchestration.approve_recommendation(rec1.id, approved_by="Officer_B")

        rec2 = self._create_sample_recommendation(provider_id=self.provider.provider_id)
        self.orchestration.approve_recommendation(rec2.id, approved_by="Officer_A")
        with self.assertRaises(ValueError):
            self.orchestration.reject_recommendation(rec2.id, rejected_by="Officer_B", reason="Too late")

    def test_expire_recommendation(self):
        """Expiring a recommendation marks it expired; expired rec cannot be approved/rejected."""
        rec = self._create_sample_recommendation(provider_id=self.provider.provider_id)
        expired = self.orchestration.expire_recommendation(rec.id)
        self.assertEqual(expired.status, "expired")

        with self.assertRaises(ValueError):
            self.orchestration.approve_recommendation(rec.id, approved_by="Officer_A")

        with self.assertRaises(ValueError):
            self.orchestration.reject_recommendation(rec.id, rejected_by="Officer_A", reason="Too late")

    def test_approve_reject_nonexistent(self):
        """Approving or rejecting non-existent ID raises ValueError."""
        with self.assertRaises(ValueError):
            self.orchestration.approve_recommendation(999999, approved_by="Officer_A")

        with self.assertRaises(ValueError):
            self.orchestration.reject_recommendation(999999, rejected_by="Officer_A", reason="None")

    def test_action_lifecycle_success(self):
        """Phase 6: Full action execution lifecycle: dispatched -> executing -> executed."""
        rec = self._create_sample_recommendation(provider_id=self.provider.provider_id)
        self.orchestration.approve_recommendation(rec.id, approved_by="Director_Jones")

        action = self.db.query(ActionExecutionDB).filter(
            ActionExecutionDB.recommendation_id == rec.id
        ).first()
        self.assertIsNotNone(action)
        self.assertEqual(action.status, "dispatched")

        # Start execution
        executing_action = self.orchestration.start_action_execution(action.id)
        self.assertEqual(executing_action.status, "executing")
        self.db.refresh(rec)
        self.assertEqual(rec.status, "executing")

        # Complete execution
        completed_action = self.orchestration.complete_action_execution(
            action.id,
            response_data={"deployed_buses": 5, "route": "Plaza loop"}
        )
        self.assertEqual(completed_action.status, "executed")
        self.assertIsNotNone(completed_action.completed_at)
        self.assertEqual(completed_action.response["deployed_buses"], 5)

        # Recommendation should now also transition to executed
        self.db.refresh(rec)
        self.assertEqual(rec.status, "executed")
        self.assertIsNotNone(rec.executed_at)

    def test_action_lifecycle_failure(self):
        """Phase 6: Action execution failure transitions status to failed with error logged."""
        rec = self._create_sample_recommendation(provider_id=self.provider.provider_id)
        self.orchestration.approve_recommendation(rec.id, approved_by="Director_Jones")

        action = self.db.query(ActionExecutionDB).filter(
            ActionExecutionDB.recommendation_id == rec.id
        ).first()

        self.orchestration.start_action_execution(action.id)
        failed_action = self.orchestration.fail_action_execution(
            action.id,
            error_reason="Fleet bus driver strike / road blockage"
        )
        self.assertEqual(failed_action.status, "failed")
        self.assertIsNotNone(failed_action.completed_at)
        self.assertIn("strike", failed_action.response["error"])

    def test_system_level_action_without_provider(self):
        """Phase 6: System-level actions (e.g. digital signage) work cleanly without provider_id."""
        rec_data = {
            "type": "demand_redirect",
            "description": "Broadcast route advisory via digital signage across perimeter",
            "actions": [
                {
                    "action": "update_digital_signage",
                    "message": "Use West Gate for faster entry",
                    "target_zone": self.zone.zone_id
                }
            ],
            "required_providers": []
        }
        rec = self.orchestration.create_recommendation_record(
            event_id=self.event.event_id,
            zone_id=self.zone.zone_id,
            recommendation=rec_data
        )

        approved = self.orchestration.approve_recommendation(rec.id, approved_by="Signage_Operator")
        self.assertEqual(approved.status, "approved")

        actions = self.db.query(ActionExecutionDB).filter(
            ActionExecutionDB.recommendation_id == rec.id
        ).all()
        self.assertEqual(len(actions), 1)
        self.assertIsNone(actions[0].provider_id)
        self.assertEqual(actions[0].action_type, "update_digital_signage")

        # Execute system action
        completed = self.orchestration.complete_action_execution(
            actions[0].id,
            response_data={"display_id": "SIGN-01", "status": "displayed"}
        )
        self.assertEqual(completed.status, "executed")


if __name__ == "__main__":
    unittest.main()

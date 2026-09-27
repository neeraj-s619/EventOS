"""
Phase 16: Database Integrity & Concurrency Tests
Comprehensive testing of database models, transactions, and integrity:
- Relationship consistency and foreign key linkage
- Transaction rollback safety on failure
- Clean repeated pipeline state writes
- Rapid sequential and multi-threaded data operations without corruption
"""

import sys
import os
import unittest
import threading
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import init_db, get_db, db_session
from app.models.database import (
    EventDB, ZoneDB, ProviderDB, ProviderTypeEnum, ProviderStatusEnum,
    ZoneTypeEnum, RiskLevelEnum, ZoneCrowdStateDB, ForecastDB,
    RiskAssessmentDB, OrchestrationRecommendationDB, ActionExecutionDB,
    FeedbackLoopDB, ProviderCapacityUpdateDB
)


class TestDatabaseIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def setUp(self):
        self.db = next(get_db())
        self.event = EventDB(
            name="DB Integrity Test Event",
            start_date=datetime(2026, 12, 1),
            end_date=datetime(2026, 12, 5),
            expected_visitors=20000
        )
        self.db.add(self.event)
        self.db.commit()
        self.db.refresh(self.event)

        self.zone = ZoneDB(
            event_id=self.event.event_id,
            name="Arena Sector",
            capacity=10000,
            current_crowd=5000,
            zone_type=ZoneTypeEnum.VENUE,
            risk_level=RiskLevelEnum.NORMAL
        )
        self.db.add(self.zone)
        self.db.commit()
        self.db.refresh(self.zone)

    def tearDown(self):
        self.db.close()

    def test_complete_relational_linkage(self):
        """Full entity linkage from Event down to ActionExecution and FeedbackLoop."""
        # 1. Add Provider
        provider = ProviderDB(
            event_id=self.event.event_id,
            zone_id=self.zone.zone_id,
            type=ProviderTypeEnum.VENUE,
            name="Integrity Arena",
            capacity={"total": 10000, "available": 5000, "occupied": 5000},
            status=ProviderStatusEnum.ACTIVE
        )
        self.db.add(provider)

        # 2. Add Crowd State
        crowd_state = ZoneCrowdStateDB(
            zone_id=self.zone.zone_id,
            people_count=5200,
            inflow_per_minute=40.0,
            outflow_per_minute=20.0,
            density=0.52,
            source="test"
        )
        self.db.add(crowd_state)

        # 3. Add Risk Assessment
        risk = RiskAssessmentDB(
            event_id=self.event.event_id,
            zone_id=self.zone.zone_id,
            current_risk=RiskLevelEnum.NORMAL,
            predicted_risk=RiskLevelEnum.NORMAL,
            current_utilization=52.0,
            predicted_utilization=55.0,
            factors={}
        )
        self.db.add(risk)
        self.db.commit()
        self.db.refresh(risk)

        # 4. Add Recommendation
        rec = OrchestrationRecommendationDB(
            event_id=self.event.event_id,
            zone_id=self.zone.zone_id,
            trigger_risk_id=risk.id,
            recommendation_type="monitor_flow",
            description="Continuous monitoring",
            actions=[{"action": "monitor"}],
            status="pending"
        )
        self.db.add(rec)
        self.db.commit()
        self.db.refresh(rec)

        # 5. Add ActionExecution
        action = ActionExecutionDB(
            recommendation_id=rec.id,
            provider_id=provider.provider_id,
            action_type="monitor",
            status="dispatched"
        )
        self.db.add(action)

        # 6. Add FeedbackLoop
        feedback = FeedbackLoopDB(
            event_id=self.event.event_id,
            zone_id=self.zone.zone_id,
            recommendation_id=rec.id,
            pre_action_state={"crowd": 5200},
            stabilized=False
        )
        self.db.add(feedback)
        self.db.commit()

        # Query back and verify relational integrity
        queried_rec = self.db.query(OrchestrationRecommendationDB).filter(
            OrchestrationRecommendationDB.id == rec.id
        ).first()
        self.assertIsNotNone(queried_rec)
        self.assertEqual(queried_rec.event_id, self.event.event_id)
        self.assertEqual(queried_rec.trigger_risk_id, risk.id)

    def test_transaction_rollback_on_failure(self):
        """Simulated mid-operation exception rolls back uncommitted changes cleanly."""
        initial_count = self.db.query(ZoneCrowdStateDB).count()

        try:
            with db_session() as session:
                st = ZoneCrowdStateDB(
                    zone_id=self.zone.zone_id,
                    people_count=1000,
                    inflow_per_minute=10.0,
                    outflow_per_minute=10.0,
                    density=0.1
                )
                session.add(st)
                # Force an intentional exception before commit
                raise RuntimeError("Simulated failure mid-transaction")
        except RuntimeError:
            pass

        # Verify rollback: count did not increment
        final_count = self.db.query(ZoneCrowdStateDB).count()
        self.assertEqual(initial_count, final_count)

    def test_concurrent_writes_thread_safety(self):
        """Simultaneous write operations across threads complete without corrupting DB."""
        num_threads = 5
        records_per_thread = 10
        errors = []

        def worker(thread_idx):
            try:
                db = next(get_db())
                for i in range(records_per_thread):
                    st = ZoneCrowdStateDB(
                        zone_id=self.zone.zone_id,
                        people_count=1000 + (thread_idx * 100) + i,
                        inflow_per_minute=10.0,
                        outflow_per_minute=10.0,
                        density=0.1,
                        source=f"thread_{thread_idx}"
                    )
                    db.add(st)
                    db.commit()
                db.close()
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Thread errors occurred: {errors}")

        # Verify all records were written
        total_written = self.db.query(ZoneCrowdStateDB).filter(
            ZoneCrowdStateDB.source.like("thread_%")
        ).count()
        self.assertEqual(total_written, num_threads * records_per_thread)


if __name__ == "__main__":
    unittest.main()

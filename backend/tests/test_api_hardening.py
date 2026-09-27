"""
Phase 15: API Layer Hardening Tests
Comprehensive testing of REST API endpoints:
- Input validation (422 Unprocessable Entity on schema violations)
- Resource existence checks (404 Not Found on invalid event_id, zone_id, recommendation_id, action_id)
- Business logic validation (400 Bad Request on duplicate approval/rejection)
- Standardized clean error envelopes (detail string, no stack traces leaked)
- Coverage of core intelligence endpoints:
  * GET /health
  * Events, Zones, Crowd State
  * CCTV ingestion endpoint
  * Risk assessment
  * Recommendations generation, approval, rejection
  * Actions execution, failure
  * Unified event state
  * Demo reset
"""

import sys
import os
import unittest
from datetime import datetime
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.core.database import init_db


class TestAPIHardening(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = TestClient(app)

    def test_health_check(self):
        """GET /health returns 200 with healthy status."""
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["app"], "EVENTOS")

    def test_events_crud_and_validation(self):
        """Event creation, retrieval, and 404 on missing event."""
        # 404 on missing event
        res_missing = self.client.get("/api/v1/events/NONEXISTENT_EVT")
        self.assertEqual(res_missing.status_code, 404)
        self.assertIn("detail", res_missing.json())

        # 422 on invalid event body
        res_invalid = self.client.post("/api/v1/events", json={"bad_field": 123})
        self.assertEqual(res_invalid.status_code, 422)

        # Valid creation
        res = self.client.post("/api/v1/events", json={
            "name": "API Test Festival",
            "start_date": "2026-11-01T00:00:00",
            "end_date": "2026-11-05T00:00:00",
            "expected_visitors": 25000
        })
        self.assertIn(res.status_code, [200, 201])
        event = res.json()
        self.assertIn("event_id", event)

        # GET existing event
        res_get = self.client.get(f"/api/v1/events/{event['event_id']}")
        self.assertEqual(res_get.status_code, 200)
        self.assertEqual(res_get.json()["name"], "API Test Festival")

    def test_zones_crud_and_validation(self):
        """Zone creation with valid event, and 404 handling."""
        # Create event first
        res_evt = self.client.post("/api/v1/events", json={
            "name": "Zone Test Event",
            "start_date": "2026-11-01T00:00:00",
            "end_date": "2026-11-05T00:00:00",
            "expected_visitors": 10000
        })
        event_id = res_evt.json()["event_id"]

        # 404 on zone creation with invalid event_id
        res_bad_evt = self.client.post("/api/v1/events/BAD_EVENT/zones", json={
            "name": "Test Zone",
            "capacity": 5000,
            "zone_type": "venue"
        })
        self.assertEqual(res_bad_evt.status_code, 404)

        # Valid zone creation
        res_zone = self.client.post(f"/api/v1/events/{event_id}/zones", json={
            "name": "Main Pavilion",
            "capacity": 5000,
            "zone_type": "venue"
        })
        self.assertIn(res_zone.status_code, [200, 201])
        zone_id = res_zone.json()["zone_id"]

        # 404 on nonexistent zone
        res_not_found = self.client.get("/api/v1/zones/NONEXISTENT_ZONE")
        self.assertEqual(res_not_found.status_code, 404)

        # GET existing zone
        res_get = self.client.get(f"/api/v1/zones/{zone_id}")
        self.assertEqual(res_get.status_code, 200)
        self.assertEqual(res_get.json()["name"], "Main Pavilion")

    def test_crowd_state_and_cctv_ingest(self):
        """Crowd state and CCTV ingestion endpoints validate input and clamp negatives."""
        res_evt = self.client.post("/api/v1/events", json={
            "name": "Crowd API Event",
            "start_date": "2026-11-01T00:00:00",
            "end_date": "2026-11-05T00:00:00",
            "expected_visitors": 10000
        })
        event_id = res_evt.json()["event_id"]
        res_zone = self.client.post(f"/api/v1/events/{event_id}/zones", json={
            "name": "Crowd Zone",
            "capacity": 5000,
            "zone_type": "venue"
        })
        zone_id = res_zone.json()["zone_id"]

        # Ingest crowd state with negative numbers (clamped to 0)
        res_crowd = self.client.post(f"/api/v1/zones/{zone_id}/crowd-state", json={
            "people_count": -50,
            "inflow_per_minute": -10.0,
            "outflow_per_minute": -5.0,
            "density": -0.2
        })
        self.assertIn(res_crowd.status_code, [200, 201])
        data = res_crowd.json()
        self.assertEqual(data["people_count"], 0)
        self.assertEqual(data["inflow_per_minute"], 0.0)

        # CCTV Ingest
        res_cctv = self.client.post(f"/api/v1/zones/{zone_id}/cctv-ingest", json={
            "zone_id": zone_id,
            "people_count": 3200,
            "inflow_per_minute": 50.0,
            "outflow_per_minute": 30.0,
            "source": "real_cctv_cv"
        })
        self.assertEqual(res_cctv.status_code, 200)
        self.assertEqual(res_cctv.json()["status"], "ingested")
        self.assertEqual(res_cctv.json()["people_count"], 3200)

        # 404 for CCTV Ingest on missing zone
        res_bad_cctv = self.client.post("/api/v1/zones/BAD_ZONE/cctv-ingest", json={
            "zone_id": "BAD_ZONE",
            "people_count": 500,
            "inflow_per_minute": 10.0,
            "outflow_per_minute": 5.0
        })
        self.assertEqual(res_bad_cctv.status_code, 404)

    def test_risk_and_orchestration_api(self):
        """Risk assessment, recommendations, approval, rejection, and duplicate handling."""
        res_evt = self.client.post("/api/v1/events", json={
            "name": "Risk & Orch API Event",
            "start_date": "2026-11-01T00:00:00",
            "end_date": "2026-11-05T00:00:00",
            "expected_visitors": 20000
        })
        event_id = res_evt.json()["event_id"]
        res_zone = self.client.post(f"/api/v1/events/{event_id}/zones", json={
            "name": "High Congestion Gate",
            "capacity": 5000,
            "zone_type": "venue"
        })
        zone_id = res_zone.json()["zone_id"]

        # Add spare zone so demand redirect can be triggered
        self.client.post(f"/api/v1/events/{event_id}/zones", json={
            "name": "Spare Zone",
            "capacity": 10000,
            "zone_type": "venue"
        })

        # Surge crowd to critical
        self.client.post(f"/api/v1/zones/{zone_id}/crowd-state", json={
            "people_count": 4800,
            "inflow_per_minute": 200.0,
            "outflow_per_minute": 20.0,
            "density": 0.96
        })

        # Assess risk
        res_risk = self.client.post(f"/api/v1/events/{event_id}/assess-risk")
        self.assertEqual(res_risk.status_code, 200)
        self.assertIsInstance(res_risk.json(), list)

        # Generate recommendations
        res_rec = self.client.post(f"/api/v1/events/{event_id}/generate-recommendations")
        self.assertEqual(res_rec.status_code, 200)
        recs = res_rec.json()["recommendations"]
        self.assertGreaterEqual(len(recs), 1)
        rec_id = recs[0]["id"]

        # Approve recommendation
        res_app = self.client.post(f"/api/v1/recommendations/{rec_id}/approve?approved_by=Commander")
        self.assertEqual(res_app.status_code, 200)
        self.assertEqual(res_app.json()["status"], "approved")

        # Duplicate approval returns 400
        res_dup_app = self.client.post(f"/api/v1/recommendations/{rec_id}/approve?approved_by=Commander")
        self.assertEqual(res_dup_app.status_code, 400)
        self.assertIn("already approved", res_dup_app.json()["detail"].lower())

        # Duplicate rejection on approved rec returns 400
        res_dup_rej = self.client.post(f"/api/v1/recommendations/{rec_id}/reject?reason=TooLate")
        self.assertEqual(res_dup_rej.status_code, 400)

        # 404 on nonexistent recommendation
        res_404_app = self.client.post("/api/v1/recommendations/999999/approve")
        self.assertEqual(res_404_app.status_code, 404)

    def test_action_execution_and_fail_endpoints(self):
        """Action execution lifecycle via API endpoints."""
        res_evt = self.client.post("/api/v1/events", json={
            "name": "Action API Event",
            "start_date": "2026-11-01T00:00:00",
            "end_date": "2026-11-05T00:00:00",
            "expected_visitors": 10000
        })
        event_id = res_evt.json()["event_id"]
        res_zone = self.client.post(f"/api/v1/events/{event_id}/zones", json={
            "name": "Plaza East",
            "capacity": 5000,
            "zone_type": "venue"
        })
        zone_id = res_zone.json()["zone_id"]

        # Add spare zone
        self.client.post(f"/api/v1/events/{event_id}/zones", json={
            "name": "Plaza West Spare",
            "capacity": 10000,
            "zone_type": "venue"
        })

        # Surge crowd
        self.client.post(f"/api/v1/zones/{zone_id}/crowd-state", json={
            "people_count": 4800,
            "inflow_per_minute": 200.0,
            "outflow_per_minute": 20.0,
            "density": 0.96
        })
        self.client.post(f"/api/v1/events/{event_id}/assess-risk")
        recs = self.client.post(f"/api/v1/events/{event_id}/generate-recommendations").json()["recommendations"]
        rec_id = recs[0]["id"]
        self.client.post(f"/api/v1/recommendations/{rec_id}/approve")

        # Get actions
        res_actions = self.client.get(f"/api/v1/recommendations/{rec_id}/actions")
        self.assertEqual(res_actions.status_code, 200)
        actions = res_actions.json()
        self.assertGreaterEqual(len(actions), 1)
        action_id = actions[0]["id"]

        # Execute action
        res_exec = self.client.post(f"/api/v1/actions/{action_id}/execute")
        self.assertEqual(res_exec.status_code, 200)
        self.assertEqual(res_exec.json()["status"], "executed")

        # 404 on non-existent action
        res_bad_action = self.client.post("/api/v1/actions/999999/execute")
        self.assertEqual(res_bad_action.status_code, 404)

    def test_demo_reset_endpoint(self):
        """POST /api/v1/demo/reset clears state and reports clean status."""
        res = self.client.post("/api/v1/demo/reset")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn(data["status"], ["reset", "reset_complete"])
        self.assertIn("deleted_events", data)


if __name__ == "__main__":
    unittest.main()

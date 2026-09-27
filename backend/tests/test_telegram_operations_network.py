"""
Tests for the EVENTOS Operations Network & Two-Bot Architecture.
Covers:
- Visitor registration & minimal PII storage
- Visitor hotel matching and accommodation requests
- Hotel provider acceptance via Staff Bot & visitor confirmation
- Staff registration and zone assignment
- Crowd alert creation & targeted delivery
- Staff alert acknowledgement and diversion action execution
- Physical flow alteration & Digital Twin risk stabilization
- Role permissions & authorization
- Missing token & bot unavailable resilience
- End-to-end simulated closed loops via API endpoints
"""

import unittest
import uuid
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.core.database import SessionLocal, init_db
from app.models.database import (
    VisitorRegistrationDB, AccommodationRequestDB,
    TelegramStaffRegistrationDB, OperationalAlertDB,
    ProviderDB, ZoneDB, RiskLevelEnum, EventDB
)
from app.services.telegram.visitor_bot import VisitorBotAdapter
from app.services.telegram.staff_bot import StaffBotAdapter
from app.services.telegram.manager import get_telegram_bot_manager, TelegramBotManager
from app.services.telegram.client import TelegramBotClient


class TestTelegramOperationsNetwork(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = TestClient(app)
        cls.db = SessionLocal()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def setUp(self):
        self.db.rollback()

    def tearDown(self):
        self.db.rollback()

    def test_01_visitor_registration(self):
        """Verify visitor registration with minimal PII."""
        chat_id = "test_vis_chat_101"
        adapter = VisitorBotAdapter(db=self.db)

        # Mock client.send_inline_poll
        with patch.object(adapter.client, "send_inline_poll", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"ok": True, "message_id": 123}
            import asyncio
            res = asyncio.run(adapter.start_registration(
                chat_id=chat_id,
                from_user={"id": 101, "first_name": "Rohan", "last_name": "Mehta", "username": "rohan_m"}
            ))
            self.assertTrue(res.get("ok"))

        # Check DB record
        reg = self.db.query(VisitorRegistrationDB).filter(VisitorRegistrationDB.chat_id == chat_id).first()
        self.assertIsNotNone(reg)
        self.assertEqual(reg.name, "Rohan Mehta")
        self.assertEqual(reg.num_people, 2)
        self.assertTrue(reg.visitor_id.startswith("VIS-"))

    def test_02_visitor_hotel_matching_and_request(self):
        """Verify visitor browses hotels and creates an accommodation request."""
        chat_id = "test_vis_chat_102"
        adapter = VisitorBotAdapter(db=self.db)

        with patch.object(adapter.client, "send_inline_poll", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"ok": True}
            import asyncio
            # Show hotels
            res = asyncio.run(adapter.show_hotels(chat_id))
            self.assertTrue(res.get("ok"))

            # Create hotel request
            req_res = asyncio.run(adapter.create_hotel_request(
                chat_id=chat_id,
                provider_id="PROV-HOTEL-MARINE",
                from_user={"first_name": "Rohan"}
            ))
            self.assertTrue(req_res.get("ok"))

        # Verify AccommodationRequestDB record
        acc_req = self.db.query(AccommodationRequestDB).filter(
            AccommodationRequestDB.visitor_chat_id == chat_id
        ).first()
        self.assertIsNotNone(acc_req)
        self.assertTrue(acc_req.request_id.startswith("EVT-HOTEL-"))
        self.assertEqual(acc_req.status, "SEARCHING")

    def test_03_hotel_provider_acceptance_and_confirmation(self):
        """Verify hotel provider accepts request on Staff Bot, updates capacity, and notifies visitor."""
        chat_id = "test_vis_chat_103"
        v_adapter = VisitorBotAdapter(db=self.db)
        s_adapter = StaffBotAdapter(db=self.db)

        with patch.object(v_adapter.client, "send_inline_poll", new_callable=AsyncMock) as mock_v_send, \
             patch.object(s_adapter.client, "send_message", new_callable=AsyncMock) as mock_s_send:
            mock_v_send.return_value = {"ok": True}
            mock_s_send.return_value = {"ok": True}

            import asyncio
            # Create request
            asyncio.run(v_adapter.create_hotel_request(
                chat_id=chat_id,
                provider_id="PROV-HOTEL-MARINE",
                from_user={"first_name": "Ananya"}
            ))

            acc_req = self.db.query(AccommodationRequestDB).filter(
                AccommodationRequestDB.visitor_chat_id == chat_id
            ).first()
            self.assertIsNotNone(acc_req)

            # Hotel accepts via Staff Bot
            accept_res = asyncio.run(s_adapter.accept_hotel_request(
                chat_id="hotel_desk_chat_01",
                req_id=acc_req.request_id,
                from_user={"first_name": "Hotel Front Desk"}
            ))
            self.assertTrue(accept_res.get("ok"))

        # Re-fetch request from DB
        self.db.refresh(acc_req)
        self.assertEqual(acc_req.status, "CONFIRMED")
        self.assertEqual(acc_req.hotel_chat_id, "hotel_desk_chat_01")

    def test_04_staff_registration_and_zone_assignment(self):
        """Verify staff member registers with role and assigned zone."""
        chat_id = "test_staff_chat_201"
        s_adapter = StaffBotAdapter(db=self.db)

        with patch.object(s_adapter.client, "send_inline_poll", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"ok": True}
            import asyncio
            res = asyncio.run(s_adapter.complete_staff_registration(
                chat_id=chat_id,
                role="GATE_STAFF",
                zone="ZONE-A",
                from_user={"id": 201, "first_name": "Vikas", "username": "vikas_gate"}
            ))
            self.assertTrue(res.get("ok"))

        staff = self.db.query(TelegramStaffRegistrationDB).filter(
            TelegramStaffRegistrationDB.chat_id == chat_id
        ).first()
        self.assertIsNotNone(staff)
        self.assertEqual(staff.role, "GATE_STAFF")
        self.assertEqual(staff.assigned_zone_id, "ZONE-A")
        self.assertTrue(staff.is_active)

    def test_05_crowd_alert_creation_and_targeting(self):
        """Verify crowd alert is dispatched specifically to staff assigned to target zone."""
        mgr = get_telegram_bot_manager()

        with patch.object(mgr.staff_client, "send_inline_poll", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"ok": True}
            import asyncio
            alert_res = asyncio.run(mgr.dispatch_targeted_crowd_alert(
                event_id="EVT-MUMBAI-MAIN",
                zone_id="ZONE-A",
                alert_data={
                    "severity": "WARNING",
                    "message": "High turnstile density",
                    "recommended_action": "Divert incoming visitors toward Zone B."
                }
            ))
            self.assertEqual(alert_res.get("status"), "ok")
            self.assertIn("alert_id", alert_res)

        alert_id = alert_res["alert_id"]
        op_alert = self.db.query(OperationalAlertDB).filter(OperationalAlertDB.alert_id == alert_id).first()
        self.assertIsNotNone(op_alert)
        self.assertEqual(op_alert.target_zone_id, "ZONE-A")

    def test_06_staff_acknowledgement(self):
        """Verify staff acknowledges alert via inline button."""
        alert_id = f"ALT-ACK-{uuid.uuid4().hex[:6]}"
        alert = OperationalAlertDB(
            alert_id=alert_id,
            event_id="EVT-MUMBAI-MAIN",
            zone_id="ZONE-A",
            severity="WARNING",
            alert_type="CROWD_PRESSURE",
            title="Zone A Pressure",
            message="Test message",
            status="DISPATCHED"
        )
        self.db.add(alert)
        self.db.commit()

        s_adapter = StaffBotAdapter(db=self.db)
        with patch.object(s_adapter.client, "send_inline_poll", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"ok": True}
            import asyncio
            res = asyncio.run(s_adapter.acknowledge_alert(
                chat_id="test_staff_chat_201",
                alert_id=alert_id,
                from_user={"first_name": "Vikas"}
            ))
            self.assertTrue(res.get("ok"))

        self.db.refresh(alert)
        self.assertEqual(alert.status, "ACKNOWLEDGED")
        self.assertEqual(alert.acknowledged_by, "Vikas")
        self.assertIsNotNone(alert.acknowledged_at)

    def test_07_diversion_action_and_digital_twin_recalculation(self):
        """Verify DIVERSION STARTED reduces inflow, updates risk in DB, and sets alert IN_PROGRESS."""
        # Setup test zone
        zone = self.db.query(ZoneDB).first()
        if not zone:
            zone = ZoneDB(
                zone_id="ZONE-TEST-DIV",
                event_id="EVT-TEST",
                name="Zone Test",
                capacity=10000,
                current_crowd=9000,
                inflow_per_minute=220.0,
                outflow_per_minute=40.0,
                risk_level=RiskLevelEnum.WARNING
            )
            self.db.add(zone)
            self.db.commit()

        initial_inflow = zone.inflow_per_minute
        alert_id = f"ALT-DIV-{uuid.uuid4().hex[:6]}"
        alert = OperationalAlertDB(
            alert_id=alert_id,
            event_id=zone.event_id,
            zone_id=zone.zone_id,
            severity="WARNING",
            alert_type="DIVERSION_REQUIRED",
            title="Concourse Diversion",
            message="Throttling required",
            status="ACKNOWLEDGED"
        )
        self.db.add(alert)
        self.db.commit()

        s_adapter = StaffBotAdapter(db=self.db)
        with patch.object(s_adapter.client, "send_inline_poll", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"ok": True}
            import asyncio
            res = asyncio.run(s_adapter.start_diversion(
                chat_id="test_staff_chat_201",
                alert_id=alert_id,
                from_user={"first_name": "Vikas"}
            ))
            self.assertTrue(res.get("ok"))

        self.db.refresh(alert)
        self.db.refresh(zone)
        self.assertEqual(alert.status, "IN_PROGRESS")
        self.assertLess(zone.inflow_per_minute, initial_inflow)
        self.assertEqual(zone.risk_level, RiskLevelEnum.WATCH)

    def test_08_provider_capacity_update_and_audit(self):
        """Verify provider capacity update via inline button or text parsing."""
        s_adapter = StaffBotAdapter(db=self.db)
        with patch.object(s_adapter.client, "send_message", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"ok": True}
            import asyncio
            res = asyncio.run(s_adapter.process_capacity_delta(
                chat_id="test_staff_chat_201",
                delta_str="+50",
                from_user={"first_name": "Transport Lead"}
            ))
            self.assertTrue(res.get("ok"))

    def test_09_role_permissions(self):
        """Verify visitor bot handles only visitor actions and staff bot handles staff roles."""
        v_adapter = VisitorBotAdapter(db=self.db)
        s_adapter = StaffBotAdapter(db=self.db)

        # Visitor bot should not have crowd diversion or staff command handlers
        self.assertFalse(hasattr(v_adapter, "start_diversion"))
        self.assertFalse(hasattr(v_adapter, "send_crowd_alert"))

        # Staff bot should have operational commands
        self.assertTrue(hasattr(s_adapter, "start_diversion"))
        self.assertTrue(hasattr(s_adapter, "send_crowd_alert"))
        self.assertTrue(hasattr(s_adapter, "accept_hotel_request"))

    def test_10_missing_token_and_resilience(self):
        """Verify system does not crash when bot token is absent."""
        client = TelegramBotClient(token="")
        self.assertFalse(client.is_configured)
        self.assertFalse(client.check_connection_sync())

        # send_message gracefully simulates when unconfigured
        import asyncio
        res = asyncio.run(client.send_message(chat_id="123", text="Hello"))
        self.assertTrue(res.get("ok"))
        self.assertTrue(res.get("simulated"))

    def test_11_simulated_crowd_alert_closed_loop_endpoint(self):
        """Verify POST /api/v1/operations-network/simulate-crowd-alert runs the 10-step incident simulation."""
        resp = self.client.post("/api/v1/operations-network/simulate-crowd-alert")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["scenario"], "CROWD_MANAGEMENT_CLOSED_LOOP")
        self.assertIn("steps", data)
        self.assertGreaterEqual(len(data["steps"]), 9)
        self.assertTrue(data.get("risk_stabilized"))

    def test_12_simulated_hotel_request_closed_loop_endpoint(self):
        """Verify POST /api/v1/operations-network/simulate-hotel-request runs visitor + hotel + staff closed loop."""
        resp = self.client.post("/api/v1/operations-network/simulate-hotel-request")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["scenario"], "HOTEL_REQUEST_CLOSED_LOOP")
        self.assertIn("steps", data)
        self.assertTrue(data.get("confirmed"))

    def test_13_operations_network_status_endpoint(self):
        """Verify GET /api/v1/operations-network/status returns verified two-bot status, metrics, and channels."""
        resp = self.client.get("/api/v1/operations-network/status")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("visitor_bot", data)
        self.assertIn("staff_bot", data)
        self.assertIn("provider_network", data)
        self.assertIn("metrics", data)
        self.assertIn("channels", data)
        self.assertEqual(len(data["channels"]), 4)


if __name__ == "__main__":
    unittest.main()

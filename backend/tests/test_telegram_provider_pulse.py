"""
Telegram Provider Pulse & Operations Gateway Tests.
Covers:
- Telegram settings & configuration modes
- Regex & keyword deterministic operational parser
- TelegramBotClient async mocked transport
- API endpoints: status, simulate-response, webhook, poll dispatch, closed-loop demo
- SQLite database update & TelegramMessageAuditDB verification
- ProviderMessagingGateway fallback
- Master dashboard provider_pulse payload integration
"""

import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.config import settings
from app.core.database import SessionLocal, init_db
from app.models.database import (
    ProviderDB, TelegramMessageAuditDB
)
from app.schemas.event import ProviderType
from app.services.telegram.parser import parse_operational_message
from app.services.telegram.client import TelegramBotClient
from app.services.provider_gateway import get_provider_gateway, SandboxAdapter


class TestTelegramProviderPulse(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = TestClient(app)

    def test_01_telegram_config(self):
        """Verify settings properties for Telegram integration."""
        self.assertTrue(hasattr(settings, "telegram_bot_token"))
        self.assertTrue(hasattr(settings, "telegram_mode"))
        self.assertTrue(hasattr(settings, "telegram_webhook_secret"))
        self.assertTrue(hasattr(settings, "is_telegram_configured"))
        self.assertTrue(hasattr(settings, "get_telegram_mode"))
        self.assertIn(settings.get_telegram_mode(), ["polling", "webhook", "sandbox", "disabled"])

    def test_02_operational_parser_deltas_and_resources(self):
        """Verify deterministic regex and operational keyword parsing."""
        # Positive delta seats
        res1 = parse_operational_message("+100 seats")
        self.assertEqual(res1.delta_change, 100)
        self.assertEqual(res1.resource, "seats")
        self.assertTrue(res1.is_valid)

        # Delta with surrounding text
        res2 = parse_operational_message("Depot 4 can dispatch +50 seats immediately")
        self.assertEqual(res2.delta_change, 50)
        self.assertEqual(res2.resource, "seats")

        # Rooms
        res3 = parse_operational_message("82 rooms available")
        val = res3.absolute_value if res3.absolute_value is not None else res3.delta_change
        self.assertEqual(val, 82)
        self.assertEqual(res3.resource, "rooms")

        # Delay
        res4 = parse_operational_message("delay 20 minutes due to traffic")
        self.assertEqual(res4.delay_minutes, 20)
        self.assertEqual(res4.status, "DELAYED")

        # No capacity
        res5 = parse_operational_message("NO CAPACITY AT THIS TIME")
        self.assertEqual(res5.status, "NO_CAPACITY")
        self.assertEqual(res5.absolute_value, 0)

        # Inline button callbacks
        self.assertEqual(parse_operational_message("Accept").status, "ACCEPTED")
        self.assertIn(parse_operational_message("Decline").status, ["NO_CAPACITY", "DECLINED"])
        self.assertEqual(parse_operational_message("Available").status, "AVAILABLE")
        self.assertEqual(parse_operational_message("Delayed").status, "DELAYED")
        self.assertIn(parse_operational_message("Unavailable").status, ["NO_CAPACITY", "UNAVAILABLE"])

    def test_03_telegram_status_endpoint(self):
        """Test /api/v1/telegram/status and /api/integrations/telegram/status."""
        r1 = self.client.get("/api/v1/telegram/status")
        self.assertEqual(r1.status_code, 200)
        d1 = r1.json()
        self.assertIn("status", d1)
        self.assertIn("configured", d1)
        self.assertIn("mode", d1)
        self.assertIn("audit_count", d1)
        self.assertIn("channel", d1)

        r2 = self.client.get("/api/integrations/telegram/status")
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.json()["status"], d1["status"])

    def test_04_telegram_simulate_response_updates_database(self):
        """Verify simulating an operational response updates provider capacity in SQLite and writes audit log."""
        db: Session = SessionLocal()
        try:
            prov = db.query(ProviderDB).filter(ProviderDB.type == ProviderType.TRANSPORT).first()
            self.assertIsNotNone(prov, "At least one transport provider must exist in seed")
            initial_avail = prov.capacity.get("available", 0)

            payload = {
                "provider_id": prov.provider_id,
                "response_text": "+100 seats",
                "event_id": prov.event_id
            }
            res = self.client.post("/api/v1/telegram/simulate-response", json=payload)
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertEqual(data["status"], "ok")
            self.assertIn(data["parsed_resource"], ["transport_capacity", "seats"])
            self.assertEqual(data["parsed_value"], 100)

            # Verify SQLite provider table updated
            db.refresh(prov)
            new_avail = prov.capacity.get("available", 0)
            self.assertEqual(new_avail, initial_avail + 100)

            # Verify audit logged
            audit = db.query(TelegramMessageAuditDB).filter(
                TelegramMessageAuditDB.provider_id == prov.provider_id
            ).order_by(TelegramMessageAuditDB.id.desc()).first()
            self.assertIsNotNone(audit)
            self.assertEqual(audit.raw_text, "+100 seats")
            self.assertEqual(audit.parsed_value, 100)
            self.assertEqual(audit.channel, "TELEGRAM")
        finally:
            db.close()

    def test_05_telegram_closed_loop_demo_scenario(self):
        """Verify the 10-step closed-loop demo: shortage drops from 120 -> 20 seats."""
        res = self.client.post("/api/v1/telegram/demo/closed-loop")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["steps_executed"], 10)
        self.assertEqual(len(data["timeline"]), 10)

        # Verify shortage reduction by exactly 100 seats
        self.assertEqual(data["initial_shortage_seats"] - data["final_shortage_seats"], 100)
        self.assertTrue(data["shortage_mitigated"])

    def test_06_telegram_webhook_secret_verification(self):
        """Verify webhook rejects requests with invalid secret token when secret is configured."""
        with patch.object(settings, "telegram_webhook_secret", "SuperSecretToken123"):
            # Without secret token header -> 403
            r_unauth = self.client.post("/api/v1/telegram/webhook", json={"update_id": 101, "message": {"text": "hello"}})
            self.assertEqual(r_unauth.status_code, 403)

            # With valid secret token header -> 200
            r_auth = self.client.post(
                "/api/v1/telegram/webhook",
                json={"update_id": 102, "message": {"text": "hello"}},
                headers={"X-Telegram-Bot-Api-Secret-Token": "SuperSecretToken123"}
            )
            self.assertEqual(r_auth.status_code, 200)

    def test_07_provider_messaging_gateway_fallback(self):
        """Verify gateway falls back to Sandbox when Telegram is not configured."""
        db: Session = SessionLocal()
        try:
            with patch.object(settings, "telegram_enabled", False), \
                 patch.object(settings, "whatsapp_enabled", False), \
                 patch.object(settings, "whatsapp_mode", "disabled"):
                gateway = get_provider_gateway(db)
                self.assertIsInstance(gateway.adapter, SandboxAdapter)
                self.assertEqual(gateway.channel.lower(), "sandbox")
        finally:
            db.close()

    def test_08_master_dashboard_includes_provider_pulse(self):
        """Verify master dashboard returns provider_pulse and telegram signal."""
        r_events = self.client.get("/api/v1/events")
        self.assertEqual(r_events.status_code, 200)
        events = r_events.json()
        self.assertTrue(len(events) > 0)
        event_id = events[0]["event_id"]

        r_dash = self.client.get(f"/api/v1/events/{event_id}/dashboard")
        self.assertEqual(r_dash.status_code, 200)
        data = r_dash.json()

        self.assertIn("provider_pulse", data)
        self.assertIsNotNone(data["provider_pulse"])
        self.assertIn("channel", data["provider_pulse"])
        self.assertIn("signals", data)
        self.assertIn("telegram", data["signals"])
        self.assertIn(data["signals"]["telegram"]["status"], ["ONLINE", "SANDBOX"])


class TestTelegramAsyncClient(unittest.IsolatedAsyncioTestCase):

    async def test_telegram_bot_client_mocked(self):
        """Verify TelegramBotClient methods with mocked transport."""
        bot = TelegramBotClient(token="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11")
        self.assertTrue(bot.is_configured)

        with patch("httpx.AsyncClient.get") as mock_get, patch("httpx.AsyncClient.post") as mock_post:
            mock_get.return_value = MagicMock(status_code=200, json=lambda: {"ok": True, "result": {"id": 123456, "is_bot": True, "username": "eventos_test_bot"}})
            me = await bot.get_me()
            self.assertIsNotNone(me)
            username = me.get("result", {}).get("username") if "result" in me else me.get("username")
            self.assertEqual(username, "eventos_test_bot")

            mock_post.return_value = MagicMock(status_code=200, json=lambda: {"ok": True, "result": {"message_id": 999}})
            sent = await bot.send_message(chat_id="98765", text="Operational alert")
            self.assertIsNotNone(sent)
            mid = sent.get("result", {}).get("message_id") if "result" in sent else sent.get("message_id")
            self.assertEqual(mid, 999)

            poll_sent = await bot.send_inline_poll(
                chat_id="98765",
                text="Need capacity?",
                buttons=[[{"text": "+50 seats", "callback_data": "cap:+50:seats"}]]
            )
            self.assertIsNotNone(poll_sent)


if __name__ == "__main__":
    unittest.main()

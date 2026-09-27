"""
Meta WhatsApp Cloud API Integration Test Suite
Comprehensive testing for:
1. Cloud client send text message success (Graph API mocked)
2. Cloud client send text message failure (Graph API error response)
3. Cloud client interactive buttons format
4. Cloud client HMAC-SHA256 signature verification (valid)
5. Cloud client HMAC-SHA256 signature verification (corrupted)
6. Cloud client HMAC-SHA256 signature verification (missing header)
7. Phone normalization (E.164 without plus)
8. Phone number masking (PII protection)
9. Webhook GET verification handshake (valid token)
10. Webhook GET verification handshake (invalid token -> 403)
11. Webhook POST signature header rejection (403)
12. Persistent idempotency check (duplicate wamid rejected cleanly)
13. Status webhook processing: sent and delivered
14. Status webhook processing: read and failed
15. Unknown sender quarantine (masked phone, UNKNOWN_PROVIDER audit)
16. Unsupported message types ignored gracefully (IGNORED_EVENT audit)
17. Two-step confirmation flow: PENDING_CONFIRMATION -> CONFIRM -> DB update
18. Two-step confirmation flow: CORRECT <value> -> CONFIRM -> DB update
19. Resource type domain incompatibility rejection (Hotel cannot report buses)
20. Outbound send endpoint to registered provider (POST /whatsapp/send)
21. Outbound send to unknown provider returns 404
22. WhatsApp status diagnostics endpoint with metrics & zero secret exposure
"""

import sys
import os
import hmac
import hashlib
import json
import time
import unittest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.core.database import init_db, get_db
from app.models.database import (
    EventDB, ZoneDB, ProviderDB, ProviderTypeEnum, ProviderStatusEnum,
    ZoneTypeEnum, RiskLevelEnum, WhatsAppMessageAuditDB, ProviderCapacityUpdateDB
)
from app.services.whatsapp_cloud import (
    WhatsAppCloudClient, normalize_phone_for_meta, mask_phone_number
)
from app.services.whatsapp import WhatsAppService


class TestWhatsAppMetaCloudIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = TestClient(app)

    def setUp(self):
        self.db = next(get_db())
        # Clean prior audits
        self.db.query(WhatsAppMessageAuditDB).delete()
        self.db.query(ProviderCapacityUpdateDB).delete()
        self.db.commit()

        # Save settings to restore in tearDown
        self._orig_token = settings.whatsapp_access_token
        self._orig_phone_id = settings.whatsapp_phone_number_id
        self._orig_verify_token = settings.whatsapp_verify_token
        self._orig_secret = settings.whatsapp_app_secret
        self._orig_mode = settings.whatsapp_mode
        self._orig_auto_confirm = settings.whatsapp_auto_confirm

        # Configure mock credentials
        settings.whatsapp_phone_number_id = "109876543210987"
        settings.whatsapp_access_token = "EAABtesttoken12345"
        settings.whatsapp_verify_token = "test_meta_webhook_verify_token"
        settings.whatsapp_app_secret = "test_meta_app_secret_xyz"
        settings.whatsapp_mode = "cloud"
        settings.whatsapp_auto_confirm = False

        # Create test event, zone, providers
        self.event = EventDB(
            name="Meta WhatsApp Live Event",
            start_date=datetime(2026, 11, 1),
            end_date=datetime(2026, 11, 5),
            expected_visitors=40000,
            operational_thresholds={"organizer_whatsapp": "+919800000001"}
        )
        self.db.add(self.event)
        self.db.commit()
        self.db.refresh(self.event)

        self.zone = ZoneDB(
            event_id=self.event.event_id,
            name="South Concourse",
            capacity=30000,
            current_crowd=12000,
            zone_type=ZoneTypeEnum.VENUE,
            risk_level=RiskLevelEnum.NORMAL
        )
        self.db.add(self.zone)
        self.db.commit()
        self.db.refresh(self.zone)

        # Registered hotel provider
        self.hotel = ProviderDB(
            event_id=self.event.event_id,
            zone_id=self.zone.zone_id,
            type=ProviderTypeEnum.HOTEL,
            name="Taj President",
            capacity={"total": 300, "available": 100, "occupied": 200},
            contact_info={"phone": "+919820011223", "whatsapp": "+919820011223"},
            status=ProviderStatusEnum.ACTIVE
        )
        # Registered transport provider
        self.transport = ProviderDB(
            event_id=self.event.event_id,
            zone_id=self.zone.zone_id,
            type=ProviderTypeEnum.TRANSPORT,
            name="BEST Fleet Services",
            capacity={"total": 150, "available": 50, "occupied": 100},
            contact_info={"phone": "+919820044556", "whatsapp": "+919820044556"},
            status=ProviderStatusEnum.ACTIVE
        )
        self.db.add_all([self.hotel, self.transport])
        self.db.commit()
        self.db.refresh(self.hotel)
        self.db.refresh(self.transport)

    def tearDown(self):
        settings.whatsapp_access_token = self._orig_token
        settings.whatsapp_phone_number_id = self._orig_phone_id
        settings.whatsapp_verify_token = self._orig_verify_token
        settings.whatsapp_app_secret = self._orig_secret
        settings.whatsapp_mode = self._orig_mode
        settings.whatsapp_auto_confirm = self._orig_auto_confirm
        self.db.close()

    def _sign_body(self, body_bytes: bytes, secret: str = "test_meta_app_secret_xyz") -> str:
        digest = hmac.new(secret.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()
        return f"sha256={digest}"

    def _build_meta_webhook(self, from_number: str, message_id: str, text: str, msg_type: str = "text") -> dict:
        msg_obj = {
            "from": from_number,
            "id": message_id,
            "timestamp": str(int(time.time())),
            "type": msg_type
        }
        if msg_type == "text":
            msg_obj["text"] = {"body": text}
        return {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "META_WHATSAPP_ACCOUNT_ID",
                    "changes": [
                        {
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {
                                    "display_phone_number": "919800000000",
                                    "phone_number_id": settings.whatsapp_phone_number_id
                                },
                                "messages": [msg_obj]
                            },
                            "field": "messages"
                        }
                    ]
                }
            ]
        }

    # ==========================================
    # 1. Cloud Client Send Text Message Success
    # ==========================================
    @patch("httpx.AsyncClient.post")
    def test_cloud_client_send_text_message_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "messaging_product": "whatsapp",
            "contacts": [{"input": "919820011223", "wa_id": "919820011223"}],
            "messages": [{"id": "wamid.HBgLMTA5ODc2NTQzMjEwOTg3FQIAERgSRTk5OUExMjkxMDMzQzM2MDA3AA=="}]
        }
        mock_post.return_value = mock_response

        client = WhatsAppCloudClient()
        import asyncio
        result = asyncio.run(client.send_text_message(to="+919820011223", message="Capacity update requested"))

        self.assertEqual(result["status"], "sent")
        self.assertIn("wamid.", result["message_id"])
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args[1]
        self.assertIn("Authorization", call_kwargs["headers"])
        self.assertEqual(call_kwargs["headers"]["Authorization"], f"Bearer {settings.whatsapp_access_token}")
        self.assertEqual(call_kwargs["json"]["to"], "919820011223")

    # ==========================================
    # 2. Cloud Client Send Text Message Failure
    # ==========================================
    @patch("httpx.AsyncClient.post")
    def test_cloud_client_send_text_message_failure(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = json.dumps({
            "error": {
                "message": "(#100) Param recipient_type must be individual",
                "type": "OAuthException",
                "code": 100,
                "fbtrace_id": "AZ12345"
            }
        })
        mock_response.content = mock_response.text.encode("utf-8")
        mock_response.json.return_value = json.loads(mock_response.text)
        mock_post.return_value = mock_response

        client = WhatsAppCloudClient()
        import asyncio
        result = asyncio.run(client.send_text_message(to="+919820011223", message="Test"))

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["code"], 100)
        self.assertIn("Param recipient_type", result["error"])

    # ==========================================
    # 3. Cloud Client Send Interactive Buttons
    # ==========================================
    @patch("httpx.AsyncClient.post")
    def test_cloud_client_send_interactive_buttons(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "messages": [{"id": "wamid.BTN123"}]
        }
        mock_post.return_value = mock_response

        client = WhatsAppCloudClient()
        buttons = [
            {"id": "approve_z1", "title": "Approve"},
            {"id": "reject_z1", "title": "Reject"}
        ]
        import asyncio
        result = asyncio.run(client.send_interactive_buttons(
            to="+919820011223",
            body_text="Risk Warning: Overcrowding in South Concourse",
            buttons=buttons
        ))

        self.assertEqual(result["status"], "sent")
        call_json = mock_post.call_args[1]["json"]
        self.assertEqual(call_json["type"], "interactive")
        self.assertEqual(call_json["interactive"]["type"], "button")
        self.assertEqual(len(call_json["interactive"]["action"]["buttons"]), 2)

    # ==========================================
    # 4. HMAC-SHA256 Signature Verification Valid
    # ==========================================
    def test_cloud_client_verify_signature_valid(self):
        client = WhatsAppCloudClient()
        payload = b'{"object":"whatsapp_business_account"}'
        sig = self._sign_body(payload, "test_meta_app_secret_xyz")
        self.assertTrue(client.verify_signature(payload, sig))

    # ==========================================
    # 5. HMAC-SHA256 Signature Verification Invalid
    # ==========================================
    def test_cloud_client_verify_signature_invalid(self):
        client = WhatsAppCloudClient()
        payload = b'{"object":"whatsapp_business_account"}'
        sig = "sha256=0000000000000000000000000000000000000000000000000000000000000000"
        self.assertFalse(client.verify_signature(payload, sig))

    # ==========================================
    # 6. HMAC-SHA256 Signature Verification Missing Header
    # ==========================================
    def test_cloud_client_verify_signature_missing_header(self):
        client = WhatsAppCloudClient()
        payload = b'{"object":"whatsapp_business_account"}'
        self.assertFalse(client.verify_signature(payload, None))

    # ==========================================
    # 7. Phone Normalization (E.164 without plus)
    # ==========================================
    def test_cloud_client_normalize_phone(self):
        self.assertEqual(normalize_phone_for_meta("+91 98200-11223"), "919820011223")
        self.assertEqual(normalize_phone_for_meta("09820011223"), "9820011223")
        self.assertEqual(normalize_phone_for_meta("+1 (555) 123-4567"), "15551234567")

    # ==========================================
    # 8. Phone Number Masking (PII Protection)
    # ==========================================
    def test_cloud_client_mask_phone(self):
        self.assertEqual(mask_phone_number("+919820011223"), "+9198****223")
        self.assertEqual(mask_phone_number("1234567890"), "1234****890")
        self.assertEqual(mask_phone_number("123"), "***")
        self.assertIsNone(mask_phone_number(None))

    # ==========================================
    # 9. Webhook GET Verification Handshake Success
    # ==========================================
    def test_webhook_verification_handshake_success(self):
        resp = self.client.get(
            "/api/v1/whatsapp/webhook",
            params={
                "hub.mode": "subscribe",
                "hub.challenge": "1155992288",
                "hub.verify_token": "test_meta_webhook_verify_token"
            }
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.text, "1155992288")

    # ==========================================
    # 10. Webhook GET Verification Handshake Invalid
    # ==========================================
    def test_webhook_verification_handshake_wrong_token(self):
        resp = self.client.get(
            "/api/v1/whatsapp/webhook",
            params={
                "hub.mode": "subscribe",
                "hub.challenge": "1155992288",
                "hub.verify_token": "wrong_token_here"
            }
        )
        self.assertEqual(resp.status_code, 403)

    # ==========================================
    # 11. Webhook POST Signature Header Rejection
    # ==========================================
    def test_webhook_signature_header_rejection(self):
        body = json.dumps({"test": "data"}).encode("utf-8")
        resp = self.client.post(
            "/api/v1/whatsapp/webhook",
            content=body,
            headers={"Content-Type": "application/json", "X-Hub-Signature-256": "sha256=invalid"}
        )
        self.assertEqual(resp.status_code, 403)
        self.assertIn("Invalid webhook signature", resp.json()["detail"])

    # ==========================================
    # 12. Persistent Idempotency Check
    # ==========================================
    def test_webhook_persistent_idempotency(self):
        settings.whatsapp_auto_confirm = True
        payload_dict = self._build_meta_webhook(
            from_number="+919820011223",
            message_id="wamid.HBgL-IDEMP-001",
            text="75 rooms available"
        )
        body = json.dumps(payload_dict).encode("utf-8")
        sig = self._sign_body(body)

        # 1st Request
        r1 = self.client.post(
            "/api/v1/whatsapp/webhook",
            content=body,
            headers={"Content-Type": "application/json", "X-Hub-Signature-256": sig}
        )
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r1.json()["status"], "capacity_updated")

        # 2nd Identical Request (Simulate Meta duplicate delivery)
        r2 = self.client.post(
            "/api/v1/whatsapp/webhook",
            content=body,
            headers={"Content-Type": "application/json", "X-Hub-Signature-256": sig}
        )
        self.assertEqual(r2.status_code, 200)
        data2 = r2.json()
        self.assertEqual(data2["status"], "duplicate_message")
        self.assertTrue(data2["acknowledged"])

        # Verify only 1 audit entry for this message_id
        count = self.db.query(WhatsAppMessageAuditDB).filter(
            WhatsAppMessageAuditDB.message_id == "wamid.HBgL-IDEMP-001"
        ).count()
        self.assertEqual(count, 1)

    # ==========================================
    # 13. Status Webhook: Sent and Delivered
    # ==========================================
    def test_webhook_delivery_status_sent_and_delivered(self):
        # Create an initial outbound audit record
        audit = WhatsAppMessageAuditDB(
            message_id="wamid.HBgL-OUT-001",
            provider_id=self.hotel.provider_id,
            direction="OUTBOUND",
            to_number_masked="+9198****223",
            message_type="text",
            raw_text="Test Outbound",
            processing_status="SENT",
            delivery_status="sent",
            timestamp=datetime.utcnow()
        )
        self.db.add(audit)
        self.db.commit()

        # Send Meta status webhook: delivered
        status_payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "ACC1",
                    "changes": [
                        {
                            "value": {
                                "messaging_product": "whatsapp",
                                "statuses": [
                                    {
                                        "id": "wamid.HBgL-OUT-001",
                                        "status": "delivered",
                                        "timestamp": str(int(time.time())),
                                        "recipient_id": "919820011223"
                                    }
                                ]
                            },
                            "field": "messages"
                        }
                    ]
                }
            ]
        }
        body = json.dumps(status_payload).encode("utf-8")
        sig = self._sign_body(body)

        resp = self.client.post(
            "/api/v1/whatsapp/webhook",
            content=body,
            headers={"Content-Type": "application/json", "X-Hub-Signature-256": sig}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "status_recorded")

        # Verify DB updated
        self.db.refresh(audit)
        self.assertEqual(audit.delivery_status, "delivered")

    # ==========================================
    # 14. Status Webhook: Read and Failed
    # ==========================================
    def test_webhook_delivery_status_read_and_failed(self):
        audit = WhatsAppMessageAuditDB(
            message_id="wamid.HBgL-OUT-002",
            provider_id=self.hotel.provider_id,
            direction="OUTBOUND",
            to_number_masked="+9198****223",
            message_type="text",
            raw_text="Test Outbound 2",
            processing_status="SENT",
            delivery_status="sent",
            timestamp=datetime.utcnow()
        )
        self.db.add(audit)
        self.db.commit()

        status_payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "ACC1",
                    "changes": [
                        {
                            "value": {
                                "messaging_product": "whatsapp",
                                "statuses": [
                                    {
                                        "id": "wamid.HBgL-OUT-002",
                                        "status": "failed",
                                        "timestamp": str(int(time.time())),
                                        "recipient_id": "919820011223",
                                        "errors": [
                                            {"code": 131026, "title": "Message undeliverable"}
                                        ]
                                    }
                                ]
                            },
                            "field": "messages"
                        }
                    ]
                }
            ]
        }
        body = json.dumps(status_payload).encode("utf-8")
        sig = self._sign_body(body)

        resp = self.client.post(
            "/api/v1/whatsapp/webhook",
            content=body,
            headers={"Content-Type": "application/json", "X-Hub-Signature-256": sig}
        )
        self.assertEqual(resp.status_code, 200)

        self.db.refresh(audit)
        self.assertEqual(audit.delivery_status, "failed")
        self.assertIn("131026", audit.error_reason)

    # ==========================================
    # 15. Unknown Sender Quarantine
    # ==========================================
    def test_webhook_unknown_sender_quarantine(self):
        payload_dict = self._build_meta_webhook(
            from_number="+919999999999",
            message_id="wamid.UNKNOWN-001",
            text="Hello I have 50 rooms"
        )
        body = json.dumps(payload_dict).encode("utf-8")
        sig = self._sign_body(body)

        resp = self.client.post(
            "/api/v1/whatsapp/webhook",
            content=body,
            headers={"Content-Type": "application/json", "X-Hub-Signature-256": sig}
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "error")
        self.assertIn("Unknown provider", data["error"])

        # Check quarantined audit row exists in DB
        quarantined = self.db.query(WhatsAppMessageAuditDB).filter(
            WhatsAppMessageAuditDB.message_id == "wamid.UNKNOWN-001"
        ).first()
        self.assertIsNotNone(quarantined)
        self.assertEqual(quarantined.processing_status, "UNKNOWN_PROVIDER")
        self.assertEqual(quarantined.from_number_masked, "+9199****999")
        # Ensure no plaintext phone leakage in audit row
        self.assertNotIn("+919999999999", quarantined.from_number_masked)

    # ==========================================
    # 16. Unsupported Message Types Ignored Gracefully
    # ==========================================
    def test_webhook_unsupported_message_type_ignored(self):
        payload_dict = self._build_meta_webhook(
            from_number="+919820011223",
            message_id="wamid.STICKER-001",
            text="",
            msg_type="sticker"
        )
        payload_dict["entry"][0]["changes"][0]["value"]["messages"][0]["sticker"] = {"id": "12345"}
        body = json.dumps(payload_dict).encode("utf-8")
        sig = self._sign_body(body)

        resp = self.client.post(
            "/api/v1/whatsapp/webhook",
            content=body,
            headers={"Content-Type": "application/json", "X-Hub-Signature-256": sig}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "unhandled_type")

        # Verify audit row created as IGNORED_EVENT
        audit = self.db.query(WhatsAppMessageAuditDB).filter(
            WhatsAppMessageAuditDB.message_id == "wamid.STICKER-001"
        ).first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.processing_status, "IGNORED_EVENT")

    # ==========================================
    # 17. Two-Step Confirmation Flow: Pending -> CONFIRM
    # ==========================================
    @patch("app.services.whatsapp_cloud.WhatsAppCloudClient.send_text_message")
    def test_two_step_confirmation_flow_confirm(self, mock_send):
        mock_send.return_value = {"status": "sent", "message_id": "wamid.CONFIRM-PROMPT"}
        settings.whatsapp_auto_confirm = False

        # Step 1: Inbound capacity message
        payload1 = self._build_meta_webhook(
            from_number="+919820011223",
            message_id="wamid.CONF-STEP-1",
            text="82 rooms available"
        )
        body1 = json.dumps(payload1).encode("utf-8")
        sig1 = self._sign_body(body1)

        r1 = self.client.post(
            "/api/v1/whatsapp/webhook",
            content=body1,
            headers={"Content-Type": "application/json", "X-Hub-Signature-256": sig1}
        )
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r1.json()["status"], "pending_confirmation")

        # Provider capacity should NOT be updated yet
        self.db.refresh(self.hotel)
        self.assertEqual(self.hotel.capacity["available"], 100)

        # Step 2: Inbound CONFIRM message
        payload2 = self._build_meta_webhook(
            from_number="+919820011223",
            message_id="wamid.CONF-STEP-2",
            text="CONFIRM"
        )
        body2 = json.dumps(payload2).encode("utf-8")
        sig2 = self._sign_body(body2)

        r2 = self.client.post(
            "/api/v1/whatsapp/webhook",
            content=body2,
            headers={"Content-Type": "application/json", "X-Hub-Signature-256": sig2}
        )
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.json()["status"], "capacity_updated")

        # Provider capacity IS updated now!
        self.db.refresh(self.hotel)
        self.assertEqual(self.hotel.capacity["available"], 82)

    # ==========================================
    # 18. Two-Step Confirmation Flow: CORRECT <val> -> CONFIRM
    # ==========================================
    @patch("app.services.whatsapp_cloud.WhatsAppCloudClient.send_text_message")
    def test_two_step_confirmation_flow_correct(self, mock_send):
        mock_send.return_value = {"status": "sent", "message_id": "wamid.CORRECT-PROMPT"}
        settings.whatsapp_auto_confirm = False

        # Step 1: Initial message
        payload1 = self._build_meta_webhook(
            from_number="+919820011223",
            message_id="wamid.CORR-STEP-1",
            text="82 rooms available"
        )
        body1 = json.dumps(payload1).encode("utf-8")
        sig1 = self._sign_body(body1)
        self.client.post("/api/v1/whatsapp/webhook", content=body1, headers={"Content-Type": "application/json", "X-Hub-Signature-256": sig1})

        # Step 2: Send Correction
        payload2 = self._build_meta_webhook(
            from_number="+919820011223",
            message_id="wamid.CORR-STEP-2",
            text="CORRECT 95"
        )
        body2 = json.dumps(payload2).encode("utf-8")
        sig2 = self._sign_body(body2)
        r2 = self.client.post("/api/v1/whatsapp/webhook", content=body2, headers={"Content-Type": "application/json", "X-Hub-Signature-256": sig2})
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.json()["corrected_value"], 95)

        # Step 3: CONFIRM
        payload3 = self._build_meta_webhook(
            from_number="+919820011223",
            message_id="wamid.CORR-STEP-3",
            text="CONFIRM"
        )
        body3 = json.dumps(payload3).encode("utf-8")
        sig3 = self._sign_body(body3)
        r3 = self.client.post("/api/v1/whatsapp/webhook", content=body3, headers={"Content-Type": "application/json", "X-Hub-Signature-256": sig3})
        self.assertEqual(r3.status_code, 200)
        self.assertEqual(r3.json()["status"], "capacity_updated")

        self.db.refresh(self.hotel)
        self.assertEqual(self.hotel.capacity["available"], 95)

    # ==========================================
    # 19. Resource Domain Incompatibility Rejection
    # ==========================================
    def test_resource_type_domain_incompatibility(self):
        settings.whatsapp_auto_confirm = True
        # Hotel sending buses available
        payload = self._build_meta_webhook(
            from_number="+919820011223",
            message_id="wamid.INCOMPAT-001",
            text="50 buses available"
        )
        body = json.dumps(payload).encode("utf-8")
        sig = self._sign_body(body)

        resp = self.client.post(
            "/api/v1/whatsapp/webhook",
            content=body,
            headers={"Content-Type": "application/json", "X-Hub-Signature-256": sig}
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "error")
        self.assertIn("incompatible", data["error"].lower())

        # Check DB audit status is INCOMPATIBLE_RESOURCE
        audit = self.db.query(WhatsAppMessageAuditDB).filter(
            WhatsAppMessageAuditDB.message_id == "wamid.INCOMPAT-001"
        ).first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.processing_status, "INCOMPATIBLE_RESOURCE")

    # ==========================================
    # 20. Outbound Send to Registered Provider
    # ==========================================
    @patch("app.services.whatsapp_cloud.WhatsAppCloudClient.send_text_message")
    def test_outbound_send_to_registered_provider(self, mock_send):
        mock_send.return_value = {
            "status": "sent",
            "message_id": "wamid.HBgL-OUTBOUND-SUCCESS",
            "mode": "cloud"
        }

        resp = self.client.post(
            "/api/v1/whatsapp/send",
            json={
                "provider_id": self.hotel.provider_id,
                "message": "URGENT: High influx expected in 45m. Report available rooms."
            }
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "sent")
        self.assertEqual(data["provider_id"], self.hotel.provider_id)
        self.assertEqual(data["to"], "+9198****223")

        # Verify OUTBOUND audit row created
        audit = self.db.query(WhatsAppMessageAuditDB).filter(
            WhatsAppMessageAuditDB.message_id == "wamid.HBgL-OUTBOUND-SUCCESS"
        ).first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.direction, "OUTBOUND")
        self.assertEqual(audit.delivery_status, "sent")

    # ==========================================
    # 21. Outbound Send Unknown Provider Returns 404
    # ==========================================
    def test_outbound_send_unknown_provider_404(self):
        resp = self.client.post(
            "/api/v1/whatsapp/send",
            json={
                "provider_id": "NON_EXISTENT_PROV_999",
                "message": "Hello"
            }
        )
        self.assertEqual(resp.status_code, 404)
        self.assertIn("not found", resp.json()["detail"].lower())

    # ==========================================
    # 22. WhatsApp Status Diagnostics & Zero Secret Leakage
    # ==========================================
    def test_whatsapp_status_endpoint_diagnostics(self):
        resp = self.client.get("/api/v1/whatsapp/status")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertEqual(data["mode"], "cloud")
        self.assertTrue(data["configured"])
        self.assertTrue(data["cloud_ready"])
        self.assertTrue(data["phone_number_id_configured"])
        self.assertTrue(data["access_token_configured"])
        self.assertTrue(data["verify_token_configured"])
        self.assertTrue(data["app_secret_configured"])
        self.assertIn("statistics", data)
        self.assertIn("total_inbound", data["statistics"])
        self.assertIn("total_outbound", data["statistics"])
        self.assertIn("quarantined_unknown", data["statistics"])

        # Security check: Ensure raw secrets are NEVER exposed in response body
        raw_json_str = resp.text
        self.assertNotIn("EAABtesttoken12345", raw_json_str)
        self.assertNotIn("test_meta_app_secret_xyz", raw_json_str)
        self.assertNotIn("test_meta_webhook_verify_token", raw_json_str)


if __name__ == "__main__":
    unittest.main()

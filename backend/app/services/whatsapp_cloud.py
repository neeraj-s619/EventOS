import hmac
import hashlib
import json
import logging
import re
import time
from typing import Dict, List, Optional, Any
import httpx

from app.core.config import settings

logger = logging.getLogger("eventos.whatsapp.cloud")


def mask_phone_number(phone: Optional[str]) -> Optional[str]:
    """Mask phone number for safe display and logging (Zero PII leak)."""
    if phone is None:
        return None
    s = str(phone).strip()
    if not s:
        return None
    digits = re.sub(r"\D", "", s)
    if len(digits) < 6:
        return "***"
    has_plus = s.startswith("+")
    prefix = digits[:4]
    suffix = digits[-3:]
    return f"{'+' if has_plus else ''}{prefix}****{suffix}"


def normalize_phone_for_meta(phone: str) -> str:
    """Normalize phone number to standard E.164 digits without '+' or symbols for Meta Cloud API."""
    if not phone:
        return ""
    digits = re.sub(r"\D", "", str(phone))
    if digits.startswith("0") and len(digits) == 11:
        digits = digits[1:]
    return digits


class WhatsAppCloudClient:
    """
    Dedicated client for Meta WhatsApp Cloud API (Graph API).
    Provides structured outbound messaging, webhook signature validation,
    and phone number verification.
    """

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_version: Optional[str] = None,
        phone_number_id: Optional[str] = None,
        access_token: Optional[str] = None,
        app_secret: Optional[str] = None,
    ):
        self.api_url = (api_url or settings.whatsapp_api_url or "https://graph.facebook.com").rstrip("/")
        self.api_version = api_version or settings.whatsapp_api_version or "v20.0"
        self.phone_number_id = phone_number_id or settings.whatsapp_phone_number_id
        self.access_token = access_token or settings.get_access_token()
        self.app_secret = app_secret or settings.whatsapp_app_secret

    @property
    def is_configured(self) -> bool:
        """Returns True if minimum required credentials for real Meta Cloud API are present."""
        return bool(self.access_token and self.phone_number_id)

    @property
    def messages_endpoint(self) -> str:
        """Endpoint for sending WhatsApp messages via Meta Graph API."""
        return f"{self.api_url}/{self.api_version}/{self.phone_number_id}/messages"

    def verify_signature(self, payload_bytes: bytes, signature_header: Optional[str]) -> bool:
        """
        Validates X-Hub-Signature-256 header using HMAC-SHA256 with the configured App Secret.
        Returns True if signature matches or if app_secret is not configured.
        """
        if not self.app_secret:
            logger.debug("[WHATSAPP] Webhook signature validation skipped: WHATSAPP_APP_SECRET not configured")
            return True

        if not signature_header or not signature_header.startswith("sha256="):
            logger.warning("[WHATSAPP] Webhook signature rejected: Missing or malformed X-Hub-Signature-256 header")
            return False

        expected_hash = signature_header.split("sha256=", 1)[1].strip()
        computed_hash = hmac.new(
            self.app_secret.encode("utf-8"),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()

        is_valid = hmac.compare_digest(expected_hash, computed_hash)
        if not is_valid:
            logger.warning("[WHATSAPP] Webhook signature verification FAILED: Signature mismatch")
        return is_valid

    async def send_text_message(
        self,
        to: str,
        message: str,
        preview_url: bool = False
    ) -> Dict[str, Any]:
        """
        Sends an outbound text message to a WhatsApp number via Meta Cloud API.
        If credentials are not configured or in sandbox mode, returns a simulated response.
        """
        clean_to = normalize_phone_for_meta(to)
        if not clean_to:
            return {"status": "error", "error": "Invalid recipient phone number"}

        # If not configured for cloud dispatch, run safely in sandbox mode
        if not self.is_configured:
            logger.info(f"[WHATSAPP] Outbound message (SANDBOX): To={mask_phone_number(to)} Text='{message[:40]}...'")
            simulated_id = f"wamid.HBgL{int(time.time() * 1000)}SIMULATED"
            return {
                "status": "simulated",
                "message_id": simulated_id,
                "to": to,
                "recipient_id": clean_to,
                "body": message,
                "mode": "sandbox"
            }

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": clean_to,
            "type": "text",
            "text": {
                "preview_url": preview_url,
                "body": message
            }
        }

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        logger.info(f"[WHATSAPP] Outbound dispatch: To={mask_phone_number(to)} Endpoint={self.messages_endpoint}")

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.post(self.messages_endpoint, json=payload, headers=headers)
                data = response.json() if response.content else {}

                if response.status_code >= 400:
                    error_detail = data.get("error", {})
                    err_msg = error_detail.get("message", response.text)
                    err_code = error_detail.get("code")
                    logger.error(f"[WHATSAPP] Meta API Error ({response.status_code}): {err_msg} (code={err_code})")
                    return {
                        "status": "failed",
                        "error": err_msg,
                        "code": err_code,
                        "http_status": response.status_code,
                        "to": to
                    }

                msg_list = data.get("messages", [])
                meta_id = msg_list[0].get("id") if msg_list else f"wamid-{int(time.time())}"
                logger.info(f"[WHATSAPP] Outbound message SENT successfully: meta_message_id={meta_id}")

                return {
                    "status": "sent",
                    "message_id": meta_id,
                    "to": to,
                    "recipient_id": clean_to,
                    "raw_response": data
                }

            except httpx.RequestError as e:
                logger.error(f"[WHATSAPP] Network error communicating with Meta API: {str(e)}")
                return {"status": "failed", "error": f"Network transport error: {str(e)}", "to": to}
            except Exception as e:
                logger.error(f"[WHATSAPP] Unexpected error sending message: {str(e)}")
                return {"status": "failed", "error": str(e), "to": to}

    async def send_interactive_buttons(
        self,
        to: str,
        message: str = "",
        buttons: Optional[List[Dict[str, str]]] = None,
        body_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sends an interactive quick-reply button message.
        """
        text = body_text or message or "Please choose an action:"
        buttons = buttons or []
        clean_to = normalize_phone_for_meta(to)
        if not clean_to:
            return {"status": "error", "error": "Invalid recipient phone number"}

        if not self.is_configured:
            simulated_id = f"wamid.HBgL{int(time.time() * 1000)}SIM_BTN"
            return {
                "status": "simulated",
                "message_id": simulated_id,
                "to": to,
                "buttons": buttons,
                "mode": "sandbox"
            }

        btn_components = []
        for b in buttons[:3]:  # Meta allows max 3 quick-reply buttons
            btn_components.append({
                "type": "reply",
                "reply": {
                    "id": b.get("id", f"btn_{len(btn_components)}"),
                    "title": b.get("title", "Select")[:20]
                }
            })

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": clean_to,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": text},
                "action": {"buttons": btn_components}
            }
        }

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.post(self.messages_endpoint, json=payload, headers=headers)
                data = response.json() if response.content else {}
                if response.status_code >= 400:
                    err_msg = data.get("error", {}).get("message", response.text)
                    return {"status": "failed", "error": err_msg, "to": to}
                
                msg_list = data.get("messages", [])
                meta_id = msg_list[0].get("id") if msg_list else f"wamid-{int(time.time())}"
                return {"status": "sent", "message_id": meta_id, "to": to}
            except Exception as e:
                return {"status": "failed", "error": str(e), "to": to}

    async def get_phone_number_info(self) -> Dict[str, Any]:
        """Queries Meta Graph API for registered phone number details (display name, quality, status)."""
        if not self.is_configured:
            return {
                "status": "not_configured",
                "message": "Meta Cloud credentials not configured"
            }

        url = f"{self.api_url}/{self.api_version}/{self.phone_number_id}"
        headers = {"Authorization": f"Bearer {self.access_token}"}

        async with httpx.AsyncClient(timeout=8.0) as client:
            try:
                res = await client.get(url, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    return {
                        "status": "connected",
                        "display_phone_number": data.get("display_phone_number"),
                        "verified_name": data.get("verified_name"),
                        "quality_rating": data.get("quality_rating"),
                        "id": data.get("id")
                    }
                return {
                    "status": "error",
                    "error": res.json().get("error", {}).get("message", res.text)
                }
            except Exception as e:
                return {"status": "error", "error": str(e)}

    def verify_configuration(self) -> Dict[str, Any]:
        """Provides diagnostic metadata for current WhatsApp configuration without exposing secrets."""
        return {
            "mode": settings.get_effective_mode(),
            "enabled": settings.whatsapp_enabled,
            "cloud_ready": self.is_configured,
            "api_url": self.api_url,
            "api_version": self.api_version,
            "phone_number_id_configured": bool(self.phone_number_id),
            "access_token_configured": bool(self.access_token),
            "app_secret_configured": bool(self.app_secret),
            "verify_token_configured": bool(settings.whatsapp_verify_token),
            "auto_confirm": settings.whatsapp_auto_confirm
        }

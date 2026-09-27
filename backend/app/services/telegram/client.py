"""
Telegram Bot API HTTP Client.
Direct interaction with official Telegram Bot API (https://api.telegram.org/bot<token>/).
Ensures zero token exposure in logs or exceptions.
"""

import logging
from typing import Dict, Any, Optional, List
import httpx

from app.core.config import settings

logger = logging.getLogger("eventos.telegram.client")


class TelegramBotClient:
    """Client for Telegram Bot API."""

    def __init__(self, token: Optional[str] = None):
        if token is not None:
            self._token = token.strip()
        else:
            self._token = (settings.telegram_bot_token or "").strip()
        self.base_url = "https://api.telegram.org"

    @property
    def is_configured(self) -> bool:
        return bool(self._token and len(self._token) > 5)

    def _get_api_url(self, method: str) -> str:
        if not self.is_configured:
            raise ValueError("Telegram Bot Token is not configured")
        return f"{self.base_url}/bot{self._token}/{method}"

    async def get_me(self) -> Dict[str, Any]:
        """Calls getMe to verify bot token and retrieve bot identity."""
        if not self.is_configured:
            return {"ok": False, "description": "Token not configured"}

        url = self._get_api_url("getMe")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(url)
                data = res.json()
                if not data.get("ok"):
                    logger.warning(f"[TELEGRAM] getMe error: {data.get('description')}")
                return data
        except Exception as e:
            logger.error(f"[TELEGRAM] getMe network error: {type(e).__name__}")
            return {"ok": False, "description": str(type(e).__name__)}

    def check_connection_sync(self) -> bool:
        """Verifies Telegram Bot Token connectivity synchronously with a 30s cache."""
        if not self.is_configured:
            return False
        import time
        now = time.time()
        if hasattr(self, "_last_verified_at") and (now - self._last_verified_at < 30.0):
            return self._is_verified
        try:
            url = self._get_api_url("getMe")
            with httpx.Client(timeout=3.0) as client:
                res = client.get(url)
                self._is_verified = bool(res.status_code == 200 and res.json().get("ok"))
        except Exception:
            self._is_verified = False
        self._last_verified_at = now
        return self._is_verified

    async def send_message(
        self,
        chat_id: str | int,
        text: str,
        reply_markup: Optional[Dict[str, Any]] = None,
        parse_mode: Optional[str] = "Markdown"
    ) -> Dict[str, Any]:
        """Sends a text message with optional inline keyboard."""
        if not self.is_configured:
            return {
                "ok": True,
                "message_id": 999999,
                "result": {
                    "message_id": 999999,
                    "simulated": True,
                    "text": text,
                    "chat": {"id": chat_id}
                },
                "simulated": True,
                "text": text,
                "chat": {"id": chat_id}
            }

        url = self._get_api_url("sendMessage")
        payload: Dict[str, Any] = {
            "chat_id": chat_id,
            "text": text,
        }
        if parse_mode:
            payload["parse_mode"] = parse_mode
        if reply_markup:
            payload["reply_markup"] = reply_markup

        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                res = await client.post(url, json=payload)
                data = res.json()
                if not data.get("ok"):
                    # Retry without Markdown if syntax failed
                    if "can't parse entities" in (data.get("description") or "").lower():
                        payload.pop("parse_mode", None)
                        retry_res = await client.post(url, json=payload)
                        data = retry_res.json()
                    else:
                        logger.warning(f"[TELEGRAM] sendMessage failed: {data.get('description')}")
                if data.get("ok") and isinstance(data.get("result"), dict):
                    ret = dict(data["result"])
                    ret["ok"] = True
                    ret["result"] = data["result"]
                    return ret
                return data
        except Exception as e:
            logger.error(f"[TELEGRAM] sendMessage network exception: {type(e).__name__}")
            return {"ok": False, "description": f"Network exception: {type(e).__name__}"}

    async def send_inline_poll(
        self,
        chat_id: str | int,
        text: str,
        buttons: List[List[Dict[str, str]]]
    ) -> Dict[str, Any]:
        """
        Convenience method to dispatch a message with an inline keyboard.
        buttons: 2D array of dicts with text and callback_data.
        """
        reply_markup = {"inline_keyboard": buttons}
        return await self.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)

    async def answer_callback_query(
        self,
        callback_query_id: str,
        text: Optional[str] = None,
        show_alert: bool = False
    ) -> Dict[str, Any]:
        """Answers a callback query from an inline button press."""
        if not self.is_configured:
            return {"ok": True, "simulated": True}

        url = self._get_api_url("answerCallbackQuery")
        payload: Dict[str, Any] = {
            "callback_query_id": callback_query_id,
            "show_alert": show_alert
        }
        if text:
            payload["text"] = text

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.post(url, json=payload)
                return res.json()
        except Exception as e:
            logger.error(f"[TELEGRAM] answerCallbackQuery error: {type(e).__name__}")
            return {"ok": False, "description": str(type(e).__name__)}

    async def get_updates(
        self,
        offset: Optional[int] = None,
        limit: int = 100,
        timeout: int = 1
    ) -> List[Dict[str, Any]]:
        """Long-polling / updates query via getUpdates."""
        if not self.is_configured:
            return []

        url = self._get_api_url("getUpdates")
        params: Dict[str, Any] = {"limit": limit, "timeout": timeout}
        if offset is not None:
            params["offset"] = offset

        try:
            async with httpx.AsyncClient(timeout=float(timeout + 5)) as client:
                res = await client.get(url, params=params)
                data = res.json()
                if data.get("ok"):
                    return data.get("result", [])
                logger.warning(f"[TELEGRAM] getUpdates error: {data.get('description')}")
                return []
        except Exception as e:
            logger.error(f"[TELEGRAM] getUpdates network error: {type(e).__name__}")
            return []

    async def set_webhook(
        self,
        url: str,
        secret_token: Optional[str] = None,
        max_connections: int = 40
    ) -> Dict[str, Any]:
        """Sets the webhook URL with optional secret token validation."""
        if not self.is_configured:
            return {"ok": False, "description": "Token not configured"}

        endpoint = self._get_api_url("setWebhook")
        payload: Dict[str, Any] = {
            "url": url,
            "max_connections": max_connections,
            "allowed_updates": ["message", "callback_query"]
        }
        if secret_token:
            payload["secret_token"] = secret_token

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(endpoint, json=payload)
                data = res.json()
                logger.info(f"[TELEGRAM] setWebhook response: {data}")
                return data
        except Exception as e:
            logger.error(f"[TELEGRAM] setWebhook error: {type(e).__name__}")
            return {"ok": False, "description": str(type(e).__name__)}

    async def get_webhook_info(self) -> Dict[str, Any]:
        """Gets current webhook configuration state."""
        if not self.is_configured:
            return {"ok": False, "description": "Token not configured"}

        endpoint = self._get_api_url("getWebhookInfo")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(endpoint)
                return res.json()
        except Exception as e:
            logger.error(f"[TELEGRAM] getWebhookInfo error: {type(e).__name__}")
            return {"ok": False, "description": str(type(e).__name__)}

    async def delete_webhook(self, drop_pending_updates: bool = False) -> Dict[str, Any]:
        """Deletes webhook, switching bot to polling mode."""
        if not self.is_configured:
            return {"ok": False, "description": "Token not configured"}

        endpoint = self._get_api_url("deleteWebhook")
        params = {"drop_pending_updates": drop_pending_updates}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(endpoint, params=params)
                data = res.json()
                logger.info(f"[TELEGRAM] deleteWebhook response: {data}")
                return data
        except Exception as e:
            logger.error(f"[TELEGRAM] deleteWebhook error: {type(e).__name__}")
            return {"ok": False, "description": str(type(e).__name__)}

"""
Visitor Telegram Bot Adapter for EVENTOS.
Provides visitor-facing services:
- Registration
- Hotel matching and accommodation requests
- Booking status tracking
- Event and gate navigation assistance
"""

import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.database import (
    VisitorRegistrationDB, AccommodationRequestDB,
    ProviderDB, ProviderTypeEnum, EventDB, TelegramMessageAuditDB
)
from app.services.telegram.client import TelegramBotClient

logger = logging.getLogger("eventos.telegram.visitor")


class VisitorBotAdapter:
    """Adapter handling visitor interactions on the Visitor Bot."""

    def __init__(self, db: Session, client: Optional[TelegramBotClient] = None):
        self.db = db
        # If client not provided, use visitor bot token from settings
        token = settings.get_visitor_bot_token()
        self.client = client or TelegramBotClient(token=token)

    async def handle_update(self, update: Dict[str, Any]) -> Dict[str, Any]:
        """Main dispatcher for incoming updates from the Visitor Bot."""
        if "callback_query" in update:
            return await self._handle_callback(update["callback_query"])
        elif "message" in update:
            return await self._handle_message(update["message"])
        return {"ok": True, "ignored": True}

    async def _handle_callback(self, cb: Dict[str, Any]) -> Dict[str, Any]:
        """Handles inline button presses on the Visitor Bot."""
        cb_id = cb.get("id")
        data = cb.get("data", "")
        chat = cb.get("message", {}).get("chat", {})
        chat_id = str(chat.get("id"))
        from_user = cb.get("from", {})

        if cb_id:
            try:
                await self.client.answer_callback_query(cb_id)
            except Exception:
                pass

        if data == "v_hotels":
            return await self.show_hotels(chat_id)
        elif data == "v_my_reg" or data == "v_booking":
            return await self.show_my_booking(chat_id)
        elif data == "v_info":
            return await self.show_event_info(chat_id)
        elif data == "v_help":
            return await self.show_help(chat_id)
        elif data == "v_register":
            return await self.start_registration(chat_id, from_user)
        elif data.startswith("v_req_hotel:"):
            provider_id = data.split(":", 1)[1]
            return await self.create_hotel_request(chat_id, provider_id, from_user)
        elif data == "v_start":
            return await self.cmd_start(chat_id, from_user)

        return {"ok": True}

    async def _handle_message(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        """Handles incoming text messages on the Visitor Bot."""
        chat_id = str(msg.get("chat", {}).get("id"))
        from_user = msg.get("from", {})
        text = (msg.get("text") or "").strip()

        # Audit incoming message
        self._audit_message(chat_id, from_user, text, direction="INBOUND")

        if not text:
            return {"ok": True, "empty": True}

        cmd = text.split()[0].lower().split("@")[0]

        if cmd in ["/start", "start"]:
            return await self.cmd_start(chat_id, from_user)
        elif cmd in ["/register", "register"]:
            return await self.start_registration(chat_id, from_user)
        elif cmd in ["/hotels", "hotels", "accommodation", "hotel"]:
            return await self.show_hotels(chat_id)
        elif cmd in ["/booking", "/mybooking", "booking", "my booking"]:
            return await self.show_my_booking(chat_id)
        elif cmd in ["/info", "/event", "info"]:
            return await self.show_event_info(chat_id)
        elif cmd in ["/help", "help"]:
            return await self.show_help(chat_id)
        else:
            # Default response
            return await self.cmd_start(chat_id, from_user)

    async def cmd_start(self, chat_id: str, from_user: Dict[str, Any]) -> Dict[str, Any]:
        """Sends the standard /start welcome experience for visitors."""
        text = (
            "━━━━━━━━━━━━━━━━━━━━\n"
            "   🏟️ *EVENTOS VISITOR PORTAL*\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "Welcome to the official event operations assistant.\n\n"
            "What do you need today?"
        )
        buttons = [
            [{"text": "🏨 Find Accommodation", "callback_data": "v_hotels"}],
            [{"text": "📋 My Registration / Booking", "callback_data": "v_my_reg"}],
            [{"text": "ℹ️ Event & Venue Information", "callback_data": "v_info"}],
            [{"text": "❓ Get Help / Transit", "callback_data": "v_help"}],
        ]
        res = await self.client.send_inline_poll(chat_id, text, buttons)
        self._audit_message(chat_id, {}, text, direction="OUTBOUND")
        return res

    async def start_registration(self, chat_id: str, from_user: Dict[str, Any]) -> Dict[str, Any]:
        """Registers a visitor using their Telegram profile information."""
        user_id = str(from_user.get("id", chat_id))
        username = from_user.get("username", "")
        first_name = from_user.get("first_name", "Visitor")
        last_name = from_user.get("last_name", "")
        full_name = f"{first_name} {last_name}".strip()

        # Check existing registration
        reg = self.db.query(VisitorRegistrationDB).filter(VisitorRegistrationDB.chat_id == chat_id).first()
        if not reg:
            reg = VisitorRegistrationDB(
                visitor_id=f"VIS-{uuid.uuid4().hex[:8].upper()}",
                chat_id=chat_id,
                telegram_user_id=user_id,
                telegram_username=username,
                name=full_name,
                num_people=2,
                checkin_date="Today",
                checkout_date="Tomorrow",
                accommodation_requirement="HOTEL",
                registration_state="COMPLETE"
            )
            self.db.add(reg)
            self.db.commit()
            self.db.refresh(reg)

        text = (
            "✅ *VISITOR REGISTRATION CONFIRMED*\n\n"
            f"• *Visitor ID:* `{reg.visitor_id}`\n"
            f"• *Name:* {reg.name}\n"
            f"• *Party Size:* {reg.num_people} Guests\n"
            f"• *Dates:* {reg.checkin_date} – {reg.checkout_date}\n\n"
            "You are registered with the EVENTOS Operations Control Tower.\n"
            "Would you like to request nearby hotel accommodation?"
        )
        buttons = [
            [{"text": "🏨 View Available Hotels", "callback_data": "v_hotels"}],
            [{"text": "⬅️ Back to Main Menu", "callback_data": "v_start"}]
        ]
        res = await self.client.send_inline_poll(chat_id, text, buttons)
        self._audit_message(chat_id, {}, text, direction="OUTBOUND")
        return res

    async def show_hotels(self, chat_id: str) -> Dict[str, Any]:
        """Lists available accommodation providers from the database."""
        # Query hospitality providers
        hotels = self.db.query(ProviderDB).filter(
            ProviderDB.type.in_([ProviderTypeEnum.HOTEL, "HOTEL", "HOSPITALITY"])
        ).all()

        if not hotels:
            # Fallback mock for clean demonstration
            text = (
                "🏨 *ACCOMMODATION NEAR EVENT*\n\n"
                "• *Marine Plaza Hotel*\n"
                "  Available: 82 rooms • 2.1 km from Stadium\n\n"
                "• *Harbour View Stay*\n"
                "  Available: 34 rooms • 2.7 km from Stadium\n"
            )
            buttons = [
                [{"text": "Request: Marine Plaza Hotel (2 Rooms)", "callback_data": "v_req_hotel:PROV-HOTEL-MARINE"}],
                [{"text": "Request: Harbour View Stay (1 Room)", "callback_data": "v_req_hotel:PROV-HOTEL-HARBOUR"}],
                [{"text": "⬅️ Main Menu", "callback_data": "v_start"}]
            ]
            res = await self.client.send_inline_poll(chat_id, text, buttons)
            self._audit_message(chat_id, {}, text, direction="OUTBOUND")
            return res

        text = "🏨 *ACCOMMODATION NEAR EVENT*\nSelect a verified partner to request rooms:\n\n"
        buttons = []
        for h in hotels[:4]:
            cap = h.capacity if isinstance(h.capacity, dict) else {}
            avail = cap.get("available", 45)
            loc = h.location if isinstance(h.location, dict) else {}
            dist = loc.get("distance_km", 2.2)
            text += f"• *{h.name}*\n  {avail} rooms available • {dist} km\n\n"
            buttons.append([{"text": f"Request: {h.name}", "callback_data": f"v_req_hotel:{h.provider_id}"}])

        buttons.append([{"text": "⬅️ Main Menu", "callback_data": "v_start"}])
        res = await self.client.send_inline_poll(chat_id, text, buttons)
        self._audit_message(chat_id, {}, text, direction="OUTBOUND")
        return res

    async def create_hotel_request(
        self, chat_id: str, provider_id: str, from_user: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Creates an accommodation request and notifies EVENTOS operations."""
        # Find or create visitor
        reg = self.db.query(VisitorRegistrationDB).filter(VisitorRegistrationDB.chat_id == chat_id).first()
        if not reg:
            reg = VisitorRegistrationDB(
                visitor_id=f"VIS-{uuid.uuid4().hex[:8].upper()}",
                chat_id=chat_id,
                name=from_user.get("first_name", "Event Visitor"),
                num_people=2
            )
            self.db.add(reg)
            self.db.commit()
            self.db.refresh(reg)

        provider = self.db.query(ProviderDB).filter(ProviderDB.provider_id == provider_id).first()
        hotel_name = provider.name if provider else "Partner Hotel"

        # Unique request ID format: EVT-HOTEL-XXXX
        req_id = f"EVT-HOTEL-{uuid.uuid4().hex[:4].upper()}"
        acc_req = AccommodationRequestDB(
            request_id=req_id,
            visitor_id=reg.visitor_id,
            event_id=provider.event_id if provider else "EVT-MUMBAI-MAIN",
            provider_id=provider_id,
            visitor_chat_id=chat_id,
            guest_name=reg.name,
            num_rooms=2,
            num_guests=reg.num_people or 2,
            checkin_date="Today",
            checkout_date="Tomorrow",
            status="SEARCHING"
        )
        self.db.add(acc_req)
        self.db.commit()
        self.db.refresh(acc_req)

        # Notify visitor
        resp_text = (
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📋 *ACCOMMODATION REQUEST CREATED*\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            f"• *Request ID:* `{req_id}`\n"
            f"• *Hotel:* {hotel_name}\n"
            "• *Required Rooms:* 2\n"
            f"• *Guests:* {acc_req.num_guests}\n"
            "• *Status:* ⏳ *SEARCHING*\n\n"
            "EVENTOS has dispatched this request to the hotel operations desk on the Staff Network.\n"
            "You will be notified immediately when confirmed."
        )
        buttons = [
            [{"text": "🔄 Check Booking Status", "callback_data": "v_my_reg"}],
            [{"text": "⬅️ Main Menu", "callback_data": "v_start"}]
        ]
        res = await self.client.send_inline_poll(chat_id, resp_text, buttons)
        self._audit_message(chat_id, {}, resp_text, direction="OUTBOUND")

        # Forward request to hotel provider via Staff Bot
        try:
            from app.services.telegram.manager import get_telegram_bot_manager
            mgr = get_telegram_bot_manager()
            await mgr.notify_hotel_request(acc_req, hotel_name)
        except Exception as e:
            logger.warning(f"[VISITOR_BOT] notify_hotel_request error: {e}")

        return res

    async def show_my_booking(self, chat_id: str) -> Dict[str, Any]:
        """Displays all accommodation requests for this visitor."""
        reqs = self.db.query(AccommodationRequestDB).filter(
            AccommodationRequestDB.visitor_chat_id == chat_id
        ).order_by(AccommodationRequestDB.created_at.desc()).all()

        if not reqs:
            text = (
                "ℹ️ *NO ACTIVE BOOKINGS*\n\n"
                "You have no pending or confirmed accommodation requests.\n"
                "Use 'Find Accommodation' to browse partner hotels near Wankhede Stadium."
            )
            buttons = [
                [{"text": "🏨 Find Accommodation", "callback_data": "v_hotels"}],
                [{"text": "⬅️ Main Menu", "callback_data": "v_start"}]
            ]
            res = await self.client.send_inline_poll(chat_id, text, buttons)
            self._audit_message(chat_id, {}, text, direction="OUTBOUND")
            return res

        text = "📋 *YOUR ACCOMMODATION REQUESTS*\n\n"
        for r in reqs[:3]:
            hotel = self.db.query(ProviderDB).filter(ProviderDB.provider_id == r.provider_id).first()
            h_name = hotel.name if hotel else "Partner Hotel"
            status_emoji = "✅" if r.status == "CONFIRMED" else "⏳"
            text += (
                f"{status_emoji} *Request:* `{r.request_id}`\n"
                f"• *Hotel:* {h_name}\n"
                f"• *Rooms:* {r.num_rooms} ({r.num_guests} Guests)\n"
                f"• *Status:* *{r.status}*\n"
                f"• *Dates:* {r.checkin_date} to {r.checkout_date}\n\n"
            )

        buttons = [
            [{"text": "🔄 Refresh", "callback_data": "v_my_reg"}],
            [{"text": "🏨 Find More Hotels", "callback_data": "v_hotels"}],
            [{"text": "⬅️ Main Menu", "callback_data": "v_start"}]
        ]
        res = await self.client.send_inline_poll(chat_id, text, buttons)
        self._audit_message(chat_id, {}, text, direction="OUTBOUND")
        return res

    async def notify_booking_confirmed(self, req: AccommodationRequestDB, hotel_name: str) -> Dict[str, Any]:
        """Sends immediate confirmation to visitor when hotel accepts."""
        text = (
            "🎉 *HOTEL CONFIRMED!*\n\n"
            f"Your accommodation request has been accepted by *{hotel_name}*.\n\n"
            f"• *Request ID:* `{req.request_id}`\n"
            f"• *Hotel:* {hotel_name}\n"
            f"• *Rooms Confirmed:* {req.num_rooms}\n"
            f"• *Guests:* {req.num_guests}\n"
            f"• *Check-in:* {req.checkin_date}\n"
            f"• *Check-out:* {req.checkout_date}\n\n"
            "Show this confirmation at reception upon arrival."
        )
        buttons = [
            [{"text": "📋 View Booking Details", "callback_data": "v_my_reg"}],
            [{"text": "ℹ️ Venue Directions", "callback_data": "v_info"}]
        ]
        res = await self.client.send_inline_poll(req.visitor_chat_id, text, buttons)
        self._audit_message(req.visitor_chat_id, {}, text, direction="OUTBOUND")
        return res

    async def show_event_info(self, chat_id: str) -> Dict[str, Any]:
        """Displays venue and transit info."""
        event = self.db.query(EventDB).first()
        event_name = event.name if event else "Mumbai Stadium Operations"
        text = (
            f"🏟️ *EVENT INFORMATION*\n\n"
            f"• *Event:* {event_name}\n"
            "• *Venue:* Wankhede Stadium, Churchgate, Mumbai\n"
            "• *Active Gates:* Gate 1 (Marine Drive), Gate 3 (Churchgate Link), Gate 7 (Vinoo Mankad)\n"
            "• *Transit:* Churchgate Railway Station (200m), BEST Bus Depot (350m)\n"
            "• *Advisory:* Follow green illuminated signage for shortest concourse queues."
        )
        buttons = [
            [{"text": "🏨 Find Accommodation", "callback_data": "v_hotels"}],
            [{"text": "⬅️ Main Menu", "callback_data": "v_start"}]
        ]
        res = await self.client.send_inline_poll(chat_id, text, buttons)
        self._audit_message(chat_id, {}, text, direction="OUTBOUND")
        return res

    async def show_help(self, chat_id: str) -> Dict[str, Any]:
        """Displays help options."""
        text = (
            "❓ *EVENTOS VISITOR HELP DESK*\n\n"
            "Commands:\n"
            "• `/start` — Main options menu\n"
            "• `/hotels` — View and request nearby hotels\n"
            "• `/booking` — Check status of room requests\n"
            "• `/info` — Venue gates and travel guide\n\n"
            "For emergency support, contact Stadium Operations Desk Gate 1."
        )
        buttons = [[{"text": "⬅️ Back to Menu", "callback_data": "v_start"}]]
        res = await self.client.send_inline_poll(chat_id, text, buttons)
        self._audit_message(chat_id, {}, text, direction="OUTBOUND")
        return res

    def _audit_message(
        self, chat_id: str, from_user: Dict[str, Any], text: str, direction: str = "INBOUND"
    ):
        """Audits visitor message in database for dashboard timeline."""
        try:
            audit = TelegramMessageAuditDB(
                message_id=f"VIS-{uuid.uuid4().hex[:12]}",
                channel="VISITOR_BOT",
                direction=direction,
                chat_id=chat_id,
                telegram_user_id=str(from_user.get("id", chat_id)),
                telegram_username=from_user.get("username"),
                message_type="visitor_action",
                raw_text=text[:300] if text else "",
                processing_status="PROCESSED",
                status="delivered"
            )
            self.db.add(audit)
            self.db.commit()
        except Exception as e:
            logger.debug(f"[VISITOR_BOT] Audit log error: {e}")

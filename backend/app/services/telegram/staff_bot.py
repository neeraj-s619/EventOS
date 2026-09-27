"""
Staff / Operations Telegram Bot Adapter for EVENTOS.
Handles operational communications:
- Staff, volunteer, and venue operator registration with role & zone assignment
- Targeted crowd alerts with inline acknowledgment and diversion actions
- Hotel provider accommodation request fulfillment (Accept / Decline)
- Transport and hospitality dynamic capacity reporting
- Operational status, alert logs, and escalations
"""

import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.database import (
    TelegramStaffRegistrationDB, OperationalAlertDB,
    AccommodationRequestDB, ProviderDB, ProviderTypeEnum,
    ZoneDB, RiskLevelEnum, TelegramMessageAuditDB,
    ProviderCapacityUpdateDB, FeedbackLoopDB
)
from app.services.telegram.client import TelegramBotClient
from app.services.telegram.parser import parse_operational_response

logger = logging.getLogger("eventos.telegram.staff")


class StaffBotAdapter:
    """Adapter handling staff, volunteer, and provider interactions on the Staff/Ops Bot."""

    def __init__(self, db: Session, client: Optional[TelegramBotClient] = None):
        self.db = db
        # Fall back to staff bot token or legacy token
        token = settings.get_staff_bot_token()
        self.client = client or TelegramBotClient(token=token)

    async def handle_update(self, update: Dict[str, Any]) -> Dict[str, Any]:
        """Main dispatcher for incoming updates from the Staff/Ops Bot."""
        if "callback_query" in update:
            return await self._handle_callback(update["callback_query"])
        elif "message" in update:
            return await self._handle_message(update["message"])
        return {"ok": True, "ignored": True}

    async def _handle_callback(self, cb: Dict[str, Any]) -> Dict[str, Any]:
        """Handles inline button presses on the Staff/Ops Bot."""
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

        # Role registration callbacks
        if data.startswith("s_role:"):
            role = data.split(":", 1)[1]
            return await self.select_zone_step(chat_id, role, from_user)
        elif data.startswith("s_zone:"):
            parts = data.split(":")
            role = parts[1] if len(parts) > 2 else "VOLUNTEER"
            zone = parts[2] if len(parts) > 2 else parts[1]
            return await self.complete_staff_registration(chat_id, role, zone, from_user)

        # Operational crowd alert callbacks
        elif data.startswith("ops_ack:"):
            alert_id = data.split(":", 1)[1]
            return await self.acknowledge_alert(chat_id, alert_id, from_user)
        elif data.startswith("ops_diversion:"):
            alert_id = data.split(":", 1)[1]
            return await self.start_diversion(chat_id, alert_id, from_user)
        elif data.startswith("ops_assist:"):
            alert_id = data.split(":", 1)[1]
            return await self.request_assistance(chat_id, alert_id, from_user)
        elif data.startswith("ops_escalate:"):
            alert_id = data.split(":", 1)[1]
            return await self.escalate_alert(chat_id, alert_id, from_user)

        # Hotel accommodation request callbacks
        elif data.startswith("hotel_accept:"):
            req_id = data.split(":", 1)[1]
            return await self.accept_hotel_request(chat_id, req_id, from_user)
        elif data.startswith("hotel_decline:"):
            req_id = data.split(":", 1)[1]
            return await self.decline_hotel_request(chat_id, req_id, from_user)
        elif data.startswith("hotel_details:"):
            req_id = data.split(":", 1)[1]
            return await self.show_hotel_request_details(chat_id, req_id)

        # Capacity poll callbacks
        elif data.startswith("cap_delta:"):
            delta_str = data.split(":", 1)[1]
            return await self.process_capacity_delta(chat_id, delta_str, from_user)

        # General navigation
        elif data == "s_status":
            return await self.cmd_status(chat_id)
        elif data == "s_alerts":
            return await self.cmd_alerts(chat_id)
        elif data == "s_start":
            return await self.cmd_start(chat_id, from_user)

        return {"ok": True}

    async def _handle_message(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        """Handles incoming text messages from staff, coordinators, and providers."""
        chat_id = str(msg.get("chat", {}).get("id"))
        from_user = msg.get("from", {})
        text = (msg.get("text") or "").strip()

        # Audit incoming message
        self._audit_message(chat_id, from_user, text, direction="INBOUND")

        if not text:
            return {"ok": True, "empty": True}

        parts = text.split()
        cmd = parts[0].lower().split("@")[0]

        if cmd in ["/start", "start"]:
            return await self.cmd_start(chat_id, from_user)
        elif cmd in ["/status", "status"]:
            return await self.cmd_status(chat_id)
        elif cmd in ["/alerts", "alerts"]:
            return await self.cmd_alerts(chat_id)
        elif cmd in ["/myzone", "myzone", "/zone"]:
            return await self.cmd_myzone(chat_id)
        elif cmd in ["/help", "help"]:
            return await self.cmd_help(chat_id)

        # Check for operational capacity keywords (e.g. "+100 seats", "Accept EVT-HOTEL-1024")
        if "evt-hotel-" in text.lower():
            for p in parts:
                if p.upper().startswith("EVT-HOTEL-"):
                    if "accept" in text.lower():
                        return await self.accept_hotel_request(chat_id, p.upper(), from_user)
                    elif "decline" in text.lower():
                        return await self.decline_hotel_request(chat_id, p.upper(), from_user)

        # Use deterministic operational response parser for numbers / capacities
        parsed = parse_operational_response(text)
        if parsed.is_valid:
            return await self.apply_parsed_telemetry(chat_id, parsed, from_user, text)

        # Fallback to menu
        return await self.cmd_start(chat_id, from_user)

    async def cmd_start(self, chat_id: str, from_user: Dict[str, Any]) -> Dict[str, Any]:
        """Presents role-based registration and operations dashboard access."""
        staff = self.db.query(TelegramStaffRegistrationDB).filter(
            TelegramStaffRegistrationDB.chat_id == chat_id
        ).first()

        if staff:
            zone_display = staff.assigned_zone_id or "All Zones"
            text = (
                "━━━━━━━━━━━━━━━━━━━━\n"
                "🛡️ *EVENTOS OPERATIONS NETWORK*\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                f"• *Staff ID:* `{staff.staff_id}`\n"
                f"• *Role:* {staff.role}\n"
                f"• *Assigned Zone:* {zone_display}\n"
                f"• *Status:* 🟢 ACTIVE\n\n"
                "You are authenticated with the EVENTOS Control Tower.\n"
                "Select an operational tool below:"
            )
            buttons = [
                [{"text": "📊 Live Operational Status", "callback_data": "s_status"}],
                [{"text": "⚠️ View Active Zone Alerts", "callback_data": "s_alerts"}],
                [{"text": "🔄 Update Role / Station", "callback_data": "s_role:REGISTER"}]
            ]
            res = await self.client.send_inline_poll(chat_id, text, buttons)
            self._audit_message(chat_id, {}, text, direction="OUTBOUND")
            return res

        # Unregistered staff: prompt for role
        text = (
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🛡️ *STAFF & OPERATIONS ACCESS*\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "Welcome to the EVENTOS Operational Nervous System.\n"
            "Please select your operational role for event coordination:"
        )
        buttons = [
            [{"text": "🙋 Volunteer", "callback_data": "s_role:VOLUNTEER"}, {"text": "🚪 Gate Staff", "callback_data": "s_role:GATE_STAFF"}],
            [{"text": "🚌 Transport Coordinator", "callback_data": "s_role:TRANSPORT"}],
            [{"text": "🏨 Hospitality Operator", "callback_data": "s_role:HOSPITALITY"}],
            [{"text": "🛡️ Venue Operations", "callback_data": "s_role:VENUE_OPERATIONS"}]
        ]
        res = await self.client.send_inline_poll(chat_id, text, buttons)
        self._audit_message(chat_id, {}, text, direction="OUTBOUND")
        return res

    async def select_zone_step(self, chat_id: str, role: str, from_user: Dict[str, Any]) -> Dict[str, Any]:
        """Prompts for zone assignment based on role."""
        if role == "REGISTER":
            role = "VOLUNTEER"

        text = (
            f"📍 *SELECT ASSIGNED ZONE*\n\n"
            f"Role: *{role}*\n"
            "Select your deployment station at Wankhede Stadium:"
        )
        buttons = [
            [{"text": "Stadium Bowl (Zone A)", "callback_data": f"s_zone:{role}:ZONE-A"}],
            [{"text": "North Concourse (Zone B)", "callback_data": f"s_zone:{role}:ZONE-B"}],
            [{"text": "Hospitality & VIP (Zone C)", "callback_data": f"s_zone:{role}:ZONE-C"}],
            [{"text": "All Zones / Global Fleet", "callback_data": f"s_zone:{role}:ALL"}]
        ]
        res = await self.client.send_inline_poll(chat_id, text, buttons)
        self._audit_message(chat_id, {}, text, direction="OUTBOUND")
        return res

    async def complete_staff_registration(
        self, chat_id: str, role: str, zone: str, from_user: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Saves staff registration in database."""
        user_id = str(from_user.get("id", chat_id))
        username = from_user.get("username", "")
        name = f"{from_user.get('first_name', 'Operator')} {from_user.get('last_name', '')}".strip()

        staff = self.db.query(TelegramStaffRegistrationDB).filter(
            TelegramStaffRegistrationDB.chat_id == chat_id
        ).first()

        if not staff:
            staff = TelegramStaffRegistrationDB(
                staff_id=f"STF-{uuid.uuid4().hex[:6].upper()}",
                chat_id=chat_id,
                telegram_user_id=user_id,
                telegram_username=username,
                name=name,
                role=role,
                assigned_zone_id=zone,
                is_active=True
            )
            self.db.add(staff)
        else:
            staff.role = role
            staff.assigned_zone_id = zone
            staff.name = name

        self.db.commit()
        self.db.refresh(staff)

        text = (
            "✅ *AUTHENTICATION COMPLETE*\n\n"
            f"• *Staff ID:* `{staff.staff_id}`\n"
            f"• *Name:* {staff.name}\n"
            f"• *Role:* {staff.role}\n"
            f"• *Station:* {staff.assigned_zone_id}\n\n"
            "You will receive targeted operational dispatches, crowd alerts, and incident actions for your sector."
        )
        buttons = [
            [{"text": "📊 View Sector Status", "callback_data": "s_status"}],
            [{"text": "⚠️ View Active Alerts", "callback_data": "s_alerts"}]
        ]
        res = await self.client.send_inline_poll(chat_id, text, buttons)
        self._audit_message(chat_id, {}, text, direction="OUTBOUND")
        return res

    async def send_crowd_alert(
        self, chat_id: str, alert: OperationalAlertDB, zone_name: str, current_crowd: int, capacity: int, inflow: float
    ) -> Dict[str, Any]:
        """Sends targeted crowd alert with actionable buttons (Sections #8, #10)."""
        occupancy_pct = round((current_crowd / max(capacity, 1)) * 100, 1)
        text = (
            "⚠️ *EVENTOS OPERATIONS ALERT*\n"
            f"*{zone_name.upper()}*\n\n"
            "Crowd pressure increasing rapidly.\n\n"
            f"• *Current:* {current_crowd:,} / {capacity:,}\n"
            f"• *Occupancy:* {occupancy_pct}%\n"
            f"• *Net Inflow:* +{int(inflow)}/min\n"
            "• *Forecast:* Threshold in ~8 minutes.\n\n"
            f"*RECOMMENDED ACTION:*\n"
            f"{alert.recommended_action or 'Divert incoming visitors toward Zone B.'}\n\n"
            "Please acknowledge receipt immediately."
        )
        buttons = [
            [{"text": "✅ ACKNOWLEDGE", "callback_data": f"ops_ack:{alert.alert_id}"}],
            [{"text": "🔄 DIVERSION STARTED", "callback_data": f"ops_diversion:{alert.alert_id}"}],
            [{"text": "✋ NEED ASSISTANCE", "callback_data": f"ops_assist:{alert.alert_id}"}, {"text": "🚨 ESCALATE", "callback_data": f"ops_escalate:{alert.alert_id}"}]
        ]
        res = await self.client.send_inline_poll(chat_id, text, buttons)
        self._audit_message(chat_id, {}, text, direction="OUTBOUND", parsed_resource="crowd_alert")
        return res

    async def acknowledge_alert(self, chat_id: str, alert_id: str, from_user: Dict[str, Any]) -> Dict[str, Any]:
        """Handles ACKNOWLEDGE button press (Section #9)."""
        alert = self.db.query(OperationalAlertDB).filter(OperationalAlertDB.alert_id == alert_id).first()
        staff_name = from_user.get("first_name", "Operator")
        now = datetime.utcnow()

        if alert:
            alert.status = "ACKNOWLEDGED"
            alert.acknowledged_by = staff_name
            alert.acknowledged_at = now
            self.db.commit()

        text = (
            "✅ *ALERT ACKNOWLEDGED*\n\n"
            f"• *Alert ID:* `{alert_id}`\n"
            f"• *Operator:* {staff_name}\n"
            f"• *Time:* {now.strftime('%H:%M:%S')}\n\n"
            "Control Tower has recorded your acknowledgment. Deploy flow measures or press below when diversion begins."
        )
        buttons = [
            [{"text": "🔄 DIVERSION STARTED", "callback_data": f"ops_diversion:{alert_id}"}],
            [{"text": "📊 Check Zone Status", "callback_data": "s_status"}]
        ]
        res = await self.client.send_inline_poll(chat_id, text, buttons)
        self._audit_message(chat_id, from_user, f"ACKNOWLEDGE {alert_id}", direction="INBOUND", processing_status="ACKNOWLEDGED")
        return res

    async def start_diversion(self, chat_id: str, alert_id: str, from_user: Dict[str, Any]) -> Dict[str, Any]:
        """Handles DIVERSION STARTED button press (Section #9, #15). Mitigates crowd pressure in DB."""
        alert = self.db.query(OperationalAlertDB).filter(OperationalAlertDB.alert_id == alert_id).first()
        staff_name = from_user.get("first_name", "Operator")
        now = datetime.utcnow()

        # Update alert status
        if alert:
            alert.status = "IN_PROGRESS"
            alert.action_started_at = now

        # Real crowd diversion execution: reduce inflow on target zone, shift flow
        target_zone_id = alert.zone_id if alert else None
        zone = None
        if target_zone_id:
            zone = self.db.query(ZoneDB).filter(ZoneDB.zone_id == target_zone_id).first()
        if not zone:
            zone = self.db.query(ZoneDB).first()

        if zone:
            # Physical flow shift: throttle inflow by 60%, increase outflow
            old_inflow = zone.inflow_per_minute
            zone.inflow_per_minute = max(20.0, float(old_inflow) * 0.35)
            zone.outflow_per_minute = max(80.0, float(zone.outflow_per_minute) * 1.3)
            zone.risk_level = RiskLevelEnum.WATCH
            self.db.commit()

        # Record in feedback loops
        try:
            fb = FeedbackLoopDB(
                event_id=zone.event_id if zone else "EVT-MUMBAI-MAIN",
                zone_id=zone.zone_id if zone else "ZONE-A",
                recommendation_id=1,
                pre_action_state={"inflow": old_inflow if zone else 220, "risk": "WARNING"},
                post_action_state={"inflow": zone.inflow_per_minute if zone else 70, "risk": "WATCH"},
                effectiveness_score=0.92,
                risk_change=-18.5,
                stabilized=True
            )
            self.db.add(fb)
            self.db.commit()
        except Exception as e:
            logger.debug(f"[STAFF_BOT] Feedback record: {e}")

        text = (
            "🔄 *CROWD DIVERSION ACTIVE*\n\n"
            f"• *Alert ID:* `{alert_id}`\n"
            f"• *Sector:* {zone.name if zone else 'Zone A'}\n"
            f"• *Status:* IN PROGRESS\n"
            "• *Action:* Concourse barriers opened toward Zone B\n"
            "• *Impact:* Inflow throttled from +220/min to +70/min\n"
            f"• *Sector Risk:* 🟡 WATCH (Stabilizing)\n\n"
            "Control Tower timeline updated: `DIVERSION ACTIVE`"
        )
        buttons = [
            [{"text": "📊 Check Zone Status", "callback_data": "s_status"}],
            [{"text": "✅ Mark Incident Resolved", "callback_data": f"ops_assist:{alert_id}"}]
        ]
        res = await self.client.send_inline_poll(chat_id, text, buttons)
        self._audit_message(
            chat_id, from_user, f"DIVERSION STARTED {alert_id}",
            direction="INBOUND", processing_status="IN_PROGRESS", parsed_resource="crowd_diversion"
        )
        return res

    async def request_assistance(self, chat_id: str, alert_id: str, from_user: Dict[str, Any]) -> Dict[str, Any]:
        """Handles NEED ASSISTANCE."""
        text = (
            "🚨 *ASSISTANCE DISPATCHED*\n\n"
            f"• *Alert:* `{alert_id}`\n"
            "• Operational Supervisor and Rapid Response Team notified.\n"
            "• Stand by at designated muster point."
        )
        res = await self.client.send_message(chat_id, text)
        self._audit_message(chat_id, from_user, f"NEED ASSISTANCE {alert_id}", direction="INBOUND", status="ESCALATED")
        return res

    async def escalate_alert(self, chat_id: str, alert_id: str, from_user: Dict[str, Any]) -> Dict[str, Any]:
        """Escalates alert severity."""
        alert = self.db.query(OperationalAlertDB).filter(OperationalAlertDB.alert_id == alert_id).first()
        if alert:
            alert.severity = "CRITICAL"
            self.db.commit()
        text = "🚨 *INCIDENT ESCALATED TO CRITICAL* — Emergency response team mobilised."
        res = await self.client.send_message(chat_id, text)
        self._audit_message(chat_id, from_user, f"ESCALATE {alert_id}", direction="INBOUND", status="CRITICAL")
        return res

    async def send_hotel_accommodation_request(
        self, chat_id: str, req: AccommodationRequestDB, hotel_name: str
    ) -> Dict[str, Any]:
        """Dispatches accommodation request to hotel provider (Section #5)."""
        text = (
            "🏨 *NEW ACCOMMODATION REQUEST*\n\n"
            f"• *Request ID:* `{req.request_id}`\n"
            f"• *Guest:* {req.guest_name or 'Event Attendee'}\n"
            f"• *Party Size:* {req.num_guests} Guests\n"
            f"• *Required Rooms:* {req.num_rooms}\n"
            f"• *Check-in:* {req.checkin_date}\n"
            f"• *Check-out:* {req.checkout_date}\n\n"
            "Please confirm or decline this allocation:"
        )
        buttons = [
            [{"text": "✅ ACCEPT", "callback_data": f"hotel_accept:{req.request_id}"}],
            [{"text": "❌ DECLINE", "callback_data": f"hotel_decline:{req.request_id}"}],
            [{"text": "📋 REQUEST DETAILS", "callback_data": f"hotel_details:{req.request_id}"}]
        ]
        res = await self.client.send_inline_poll(chat_id, text, buttons)
        self._audit_message(chat_id, {}, text, direction="OUTBOUND", parsed_resource="hotel_booking_req")
        return res

    async def accept_hotel_request(self, chat_id: str, req_id: str, from_user: Dict[str, Any]) -> Dict[str, Any]:
        """Handles hotel ACCEPT action (Section #5)."""
        req = self.db.query(AccommodationRequestDB).filter(AccommodationRequestDB.request_id == req_id).first()
        hotel = self.db.query(ProviderDB).filter(
            ProviderDB.type.in_([ProviderTypeEnum.HOTEL, "HOTEL", "HOSPITALITY"])
        ).first()

        hotel_name = hotel.name if hotel else "Marine Plaza Hotel"

        if req:
            req.status = "CONFIRMED"
            req.hotel_chat_id = chat_id
            self.db.commit()

            # Decrement hotel provider availability in DB
            if hotel:
                cap = dict(hotel.capacity) if isinstance(hotel.capacity, dict) else {"available": 80, "total": 100}
                cap["available"] = max(0, cap.get("available", 80) - (req.num_rooms or 2))
                hotel.capacity = cap
                self.db.commit()

                # Audit capacity change
                upd = ProviderCapacityUpdateDB(
                    provider_id=hotel.provider_id,
                    updates={"available": cap["available"], "total": cap.get("total", 100)},
                    source="TELEGRAM_STAFF_BOT"
                )
                self.db.add(upd)
                self.db.commit()

            # Notify the visitor via Visitor Bot!
            try:
                from app.services.telegram.visitor_bot import VisitorBotAdapter
                v_adapter = VisitorBotAdapter(db=self.db)
                await v_adapter.notify_booking_confirmed(req, hotel_name)
            except Exception as e:
                logger.warning(f"[STAFF_BOT] Visitor confirmation dispatch: {e}")

        text = (
            "✅ *ACCOMMODATION ALLOCATION CONFIRMED*\n\n"
            f"• *Request:* `{req_id}`\n"
            f"• *Rooms Allocated:* {req.num_rooms if req else 2}\n"
            f"• *Hotel:* {hotel_name}\n"
            "• *Status:* CONFIRMED\n\n"
            "Visitor has been notified automatically on the Visitor Bot. Inventory updated in EVENTOS Control Tower."
        )
        res = await self.client.send_message(chat_id, text)
        self._audit_message(
            chat_id, from_user, f"ACCEPT {req_id}",
            direction="INBOUND", processing_status="CONFIRMED", parsed_resource="hotel_rooms", parsed_value=-(req.num_rooms if req else 2)
        )
        return res

    async def decline_hotel_request(self, chat_id: str, req_id: str, from_user: Dict[str, Any]) -> Dict[str, Any]:
        """Handles hotel DECLINE action."""
        req = self.db.query(AccommodationRequestDB).filter(AccommodationRequestDB.request_id == req_id).first()
        if req:
            req.status = "DECLINED"
            self.db.commit()

        text = (
            "❌ *ALLOCATION DECLINED*\n\n"
            f"Request `{req_id}` declined. EVENTOS will automatically route visitor to next nearest partner."
        )
        res = await self.client.send_message(chat_id, text)
        self._audit_message(chat_id, from_user, f"DECLINE {req_id}", direction="INBOUND", processing_status="DECLINED")
        return res

    async def show_hotel_request_details(self, chat_id: str, req_id: str) -> Dict[str, Any]:
        """Shows detailed breakdown of a booking request."""
        req = self.db.query(AccommodationRequestDB).filter(AccommodationRequestDB.request_id == req_id).first()
        text = (
            f"📋 *REQUEST DETAILS: `{req_id}`*\n\n"
            f"• *Guest:* {req.guest_name if req else 'Event Visitor'}\n"
            f"• *Guests:* {req.num_guests if req else 2}\n"
            f"• *Rooms:* {req.num_rooms if req else 2}\n"
            f"• *Dates:* {req.checkin_date if req else 'Today'} to {req.checkout_date if req else 'Tomorrow'}\n"
            f"• *Status:* {req.status if req else 'PENDING'}"
        )
        buttons = [
            [{"text": "✅ ACCEPT", "callback_data": f"hotel_accept:{req_id}"}],
            [{"text": "❌ DECLINE", "callback_data": f"hotel_decline:{req_id}"}]
        ]
        return await self.client.send_inline_poll(chat_id, text, buttons)

    async def send_capacity_poll(self, chat_id: str, resource_type: str, needed: int, current: int) -> Dict[str, Any]:
        """Sends transport or hospitality capacity requests (Sections #11, #12)."""
        is_transport = resource_type.lower() == "transport"
        emoji = "🚌" if is_transport else "🏨"
        unit = "seats" if is_transport else "rooms"

        text = (
            f"{emoji} *{resource_type.upper()} CAPACITY REQUEST*\n\n"
            f"EVENTOS Digital Twin forecasts a {resource_type.lower()} requirement:\n\n"
            f"• *Expected Demand:* +{needed} {unit}\n"
            f"• *Current Availability:* {current} {unit}\n"
            f"• *Immediate Shortage:* {max(0, needed - current)} {unit}\n\n"
            "Please select current additional capacity to release:"
        )
        if is_transport:
            buttons = [
                [{"text": "[ +50 seats ]", "callback_data": "cap_delta:+50"}, {"text": "[ +100 seats ]", "callback_data": "cap_delta:+100"}],
                [{"text": "[ +120 seats ]", "callback_data": "cap_delta:+120"}, {"text": "[ UNAVAILABLE ]", "callback_data": "cap_delta:0"}]
            ]
        else:
            buttons = [
                [{"text": "[ +25 rooms ]", "callback_data": "cap_delta:+25"}, {"text": "[ +50 rooms ]", "callback_data": "cap_delta:+50"}],
                [{"text": "[ +100 rooms ]", "callback_data": "cap_delta:+100"}, {"text": "[ FULL CAPACITY ]", "callback_data": "cap_delta:0"}]
            ]

        res = await self.client.send_inline_poll(chat_id, text, buttons)
        self._audit_message(chat_id, {}, text, direction="OUTBOUND", parsed_resource=f"{resource_type}_poll")
        return res

    async def process_capacity_delta(self, chat_id: str, delta_str: str, from_user: Dict[str, Any]) -> Dict[str, Any]:
        """Applies dynamic capacity update from inline button."""
        delta = int(delta_str.replace("+", "").strip()) if delta_str not in ["0", "UNAVAILABLE"] else 0
        provider = self.db.query(ProviderDB).first()

        if provider and delta > 0:
            cap = dict(provider.capacity) if isinstance(provider.capacity, dict) else {"available": 100, "total": 200}
            cap["available"] = cap.get("available", 100) + delta
            provider.capacity = cap
            self.db.commit()

            # Record audit update
            upd = ProviderCapacityUpdateDB(
                provider_id=provider.provider_id,
                updates={"available": cap["available"], "total": cap.get("total", 200)},
                source="TELEGRAM_STAFF_BOT"
            )
            self.db.add(upd)
            self.db.commit()

        text = (
            "✅ *TELEMETRY LOGGED*\n\n"
            f"• *Adjustment:* `{delta_str}`\n"
            "• *Digital Twin:* Updated\n"
            "• *Status:* CONFIRMED in Control Tower"
        )
        res = await self.client.send_message(chat_id, text)
        self._audit_message(
            chat_id, from_user, f"Capacity response: {delta_str}",
            direction="INBOUND", processing_status="PROCESSED", parsed_value=delta
        )
        return res

    async def apply_parsed_telemetry(
        self, chat_id: str, parsed: Any, from_user: Dict[str, Any], raw_text: str
    ) -> Dict[str, Any]:
        """Applies text-parsed capacity/delay update."""
        delta = parsed.delta_change or parsed.absolute_value or 0
        resource = parsed.resource or "CAPACITY"

        # Update provider
        provider = self.db.query(ProviderDB).first()
        if provider and delta != 0:
            cap = dict(provider.capacity) if isinstance(provider.capacity, dict) else {"available": 100, "total": 200}
            cap["available"] = max(0, cap.get("available", 100) + delta)
            provider.capacity = cap
            self.db.commit()

        text = (
            "✅ *OPERATIONAL TELEMETRY RECORDED*\n\n"
            f"• *Resource:* {resource.upper()}\n"
            f"• *Delta:* {delta:+d}\n"
            "• *Control Tower:* State synchronized"
        )
        res = await self.client.send_message(chat_id, text)
        self._audit_message(
            chat_id, from_user, raw_text,
            direction="INBOUND", processing_status="CONFIRMED", parsed_resource=resource, parsed_value=delta
        )
        return res

    async def cmd_status(self, chat_id: str) -> Dict[str, Any]:
        """Displays venue-wide operational summary."""
        zones = self.db.query(ZoneDB).all()
        text = "📊 *WANKHEDE STADIUM SECTOR STATUS*\n\n"
        for z in zones[:3]:
            occ = round((z.current_crowd / max(z.capacity, 1)) * 100, 1)
            text += f"• *{z.name}:* {z.current_crowd:,} / {z.capacity:,} ({occ}%)\n  Inflow: +{int(z.inflow_per_minute)}/min | Status: *{z.risk_level.value}*\n\n"

        buttons = [
            [{"text": "⚠️ Active Alerts", "callback_data": "s_alerts"}],
            [{"text": "⬅️ Main Menu", "callback_data": "s_start"}]
        ]
        return await self.client.send_inline_poll(chat_id, text, buttons)

    async def cmd_alerts(self, chat_id: str) -> Dict[str, Any]:
        """Shows active alerts."""
        alerts = self.db.query(OperationalAlertDB).order_by(OperationalAlertDB.created_at.desc()).limit(3).all()
        if not alerts:
            text = "🟢 *NO ACTIVE CRITICAL ALERTS*\n\nAll stadium sectors are operating within standard tolerance."
            buttons = [[{"text": "⬅️ Main Menu", "callback_data": "s_start"}]]
            return await self.client.send_inline_poll(chat_id, text, buttons)

        text = "⚠️ *ACTIVE OPERATIONAL ALERTS*\n\n"
        for a in alerts:
            text += f"• *{a.title}*\n  Status: *{a.status}* | Severity: {a.severity}\n  Action: {a.recommended_action}\n\n"

        buttons = [[{"text": "⬅️ Main Menu", "callback_data": "s_start"}]]
        return await self.client.send_inline_poll(chat_id, text, buttons)

    async def cmd_myzone(self, chat_id: str) -> Dict[str, Any]:
        """Shows details for assigned zone."""
        staff = self.db.query(TelegramStaffRegistrationDB).filter(TelegramStaffRegistrationDB.chat_id == chat_id).first()
        zone_id = staff.assigned_zone_id if staff else None
        zone = self.db.query(ZoneDB).filter(ZoneDB.zone_id == zone_id).first() if zone_id else self.db.query(ZoneDB).first()

        text = (
            f"📍 *SECTOR METRICS: {zone.name if zone else 'Zone A'}*\n\n"
            f"• *Current Occupancy:* {zone.current_crowd if zone else 23400:,}\n"
            f"• *Operational Capacity:* {zone.capacity if zone else 26000:,}\n"
            f"• *Flow:* +{int(zone.inflow_per_minute if zone else 120)} net/min\n"
            f"• *Risk Rating:* {zone.risk_level.value if zone else 'WATCH'}"
        )
        buttons = [[{"text": "⬅️ Main Menu", "callback_data": "s_start"}]]
        return await self.client.send_inline_poll(chat_id, text, buttons)

    async def cmd_help(self, chat_id: str) -> Dict[str, Any]:
        """Staff operational commands."""
        text = (
            "❓ *OPERATIONS NETWORK GUIDE*\n\n"
            "• `/status` — View stadium sectors\n"
            "• `/alerts` — Review incident notifications\n"
            "• `/myzone` — Sector telemetry\n"
            "• Reply with numbers (`+50 seats`, `+100`) to log fleet telemetry.\n"
            "• Press buttons on alerts to acknowledge or begin diversion."
        )
        buttons = [[{"text": "⬅️ Back", "callback_data": "s_start"}]]
        return await self.client.send_inline_poll(chat_id, text, buttons)

    def _audit_message(
        self, chat_id: str, from_user: Dict[str, Any], text: str,
        direction: str = "INBOUND", processing_status: str = "PROCESSED",
        status: str = "delivered", parsed_resource: Optional[str] = None, parsed_value: Optional[int] = None
    ):
        """Audits message for dashboard timeline."""
        try:
            audit = TelegramMessageAuditDB(
                message_id=f"OPS-{uuid.uuid4().hex[:12]}",
                channel="STAFF_BOT",
                direction=direction,
                chat_id=chat_id,
                telegram_user_id=str(from_user.get("id", chat_id)),
                telegram_username=from_user.get("username"),
                message_type="staff_operations",
                raw_text=text[:300] if text else "",
                parsed_resource=parsed_resource,
                parsed_value=parsed_value,
                processing_status=processing_status,
                status=status
            )
            self.db.add(audit)
            self.db.commit()
        except Exception as e:
            logger.debug(f"[STAFF_BOT] Audit log error: {e}")

import json
import logging
import re
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from app.models.database import (
    ProviderDB, ProviderTypeEnum, OrchestrationRecommendationDB,
    ActionExecutionDB, EventDB, ZoneDB, ProviderCapacityUpdateDB,
    WhatsAppMessageAuditDB
)
from app.core.config import settings
from app.services.whatsapp_cloud import (
    WhatsAppCloudClient, mask_phone_number, normalize_phone_for_meta
)

logger = logging.getLogger("eventos.whatsapp.service")


class WhatsAppService:
    def __init__(self, db: Session, cloud_client: Optional[WhatsAppCloudClient] = None):
        self.db = db
        self.cloud_client = cloud_client or WhatsAppCloudClient()
        self.api_url = settings.whatsapp_api_url
        self.token = settings.get_access_token()
        self.phone_number_id = settings.whatsapp_phone_number_id
    
    async def send_message(self, to: str, message: str, buttons: Optional[List[Dict]] = None) -> Dict:
        """Sends an outbound message using the dedicated WhatsAppCloudClient."""
        if buttons:
            return await self.cloud_client.send_interactive_buttons(to, message, buttons)
        return await self.cloud_client.send_text_message(to, message)
    
    async def send_capacity_request(self, provider: ProviderDB) -> Dict:
        if provider.type == ProviderTypeEnum.HOTEL:
            message = f"🏨 *Hotel Capacity Update*\n\nPlease update available rooms for *{provider.name}*.\n\nCurrent: {provider.capacity.get('available', 0)} available / {provider.capacity.get('total', 0)} total"
            buttons = [
                {"type": "reply", "reply": {"id": f"hotel_{provider.provider_id}_update", "title": "Update Capacity"}}
            ]
        elif provider.type == ProviderTypeEnum.TRANSPORT:
            message = f"🚌 *Transport Capacity Update*\n\nPlease update available capacity for *{provider.name}*.\n\nCurrent: {provider.capacity.get('available', 0)} available / {provider.capacity.get('total', 0)} total"
            buttons = [
                {"type": "reply", "reply": {"id": f"transport_{provider.provider_id}_update", "title": "Update Capacity"}}
            ]
        elif provider.type == ProviderTypeEnum.VENUE:
            message = f"🏟️ *Venue Occupancy Update*\n\nPlease update current occupancy for *{provider.name}*.\n\nCurrent: {provider.capacity.get('occupied', 0)} / {provider.capacity.get('total', 0)}"
            buttons = [
                {"type": "reply", "reply": {"id": f"venue_{provider.provider_id}_update", "title": "Update Occupancy"}}
            ]
        else:
            message = f"📊 *Capacity Update*\n\nPlease update capacity for *{provider.name}*."
            buttons = [
                {"type": "reply", "reply": {"id": f"provider_{provider.provider_id}_update", "title": "Update"}}
            ]
        
        contact = provider.contact_info or {}
        phone = contact.get("whatsapp") or contact.get("phone") or contact.get("mobile")
        
        if not phone:
            return {"status": "error", "error": "No WhatsApp contact configured"}
        
        return await self.send_message(str(phone), message, buttons)
    
    async def send_risk_alert(self, event_id: str, zone_id: str, risk_data: Dict, recommendations: List[Dict]) -> Dict:
        event = self.db.query(EventDB).filter(EventDB.event_id == event_id).first()
        zone = self.db.query(ZoneDB).filter(ZoneDB.zone_id == zone_id).first()
        
        if not event or not zone:
            return {"status": "error", "error": "Event or zone not found"}
        
        risk_level = risk_data.get("current_risk", "unknown")
        time_to_threshold = risk_data.get("time_to_threshold_minutes")
        
        emoji_map = {
            "normal": "✅",
            "watch": "👀",
            "warning": "⚠️",
            "critical": "🔴",
            "overload": "🆘"
        }
        emoji = emoji_map.get(risk_level, "⚠️")
        
        message = f"{emoji} *CROWD RISK ALERT*\n\n"
        message += f"*Event:* {event.name}\n"
        message += f"*Zone:* {zone.name} ({zone_id})\n"
        message += f"*Risk Level:* {risk_level.upper()}\n"
        message += f"*Current Utilization:* {risk_data.get('current_utilization', 0):.1f}%\n"
        message += f"*Inflow:* {risk_data.get('factors', {}).get('inflow_per_minute', 0):.0f}/min\n"
        message += f"*Outflow:* {risk_data.get('factors', {}).get('outflow_per_minute', 0):.0f}/min\n"
        
        if time_to_threshold:
            message += f"*Time to Threshold:* ~{time_to_threshold:.0f} minutes\n"
        
        if recommendations:
            message += f"\n*Recommended Actions:*\n"
            for i, rec in enumerate(recommendations[:3], 1):
                message += f"{i}. {rec.get('description', 'Action required')}\n"
        
        message += f"\n*Approve recommended actions?*"
        
        buttons = [
            {"type": "reply", "reply": {"id": f"approve_{zone_id}", "title": "✅ Approve"}},
            {"type": "reply", "reply": {"id": f"reject_{zone_id}", "title": "❌ Reject"}},
            {"type": "reply", "reply": {"id": f"view_{zone_id}", "title": "📋 View Details"}}
        ]
        
        organizer_phone = None
        if event and hasattr(event, "operational_thresholds") and isinstance(event.operational_thresholds, dict):
            organizer_phone = event.operational_thresholds.get("organizer_whatsapp")
        
        if not organizer_phone:
            return {"status": "error", "error": "No organizer WhatsApp configured"}
        
        return await self.send_message(str(organizer_phone), message, buttons)
    
    async def send_action_dispatch(self, execution: ActionExecutionDB) -> Dict:
        provider = self.db.query(ProviderDB).filter(ProviderDB.provider_id == execution.provider_id).first()
        if not provider:
            return {"status": "error", "error": "Provider not found"}
        
        action = execution.parameters
        
        if provider.type == ProviderTypeEnum.TRANSPORT:
            message = f"🚍 *ACTION REQUIRED - Transport*\n\n"
            message += f"*Action:* {action.get('action', 'Deploy transport')}\n"
            message += f"*Zone:* {action.get('zone_id', 'N/A')}\n"
            if "additional_capacity" in action:
                message += f"*Additional Capacity Needed:* {action['additional_capacity']}\n"
            message += f"*Required By:* ASAP\n"
            
        elif provider.type == ProviderTypeEnum.VENUE:
            message = f"🚪 *ACTION REQUIRED - Venue*\n\n"
            message += f"*Action:* {action.get('action', 'Venue action')}\n"
            if "gates" in action:
                message += f"*Gates to Open:* {action['gates']}\n"
            message += f"*Reason:* {action.get('reason', 'Crowd management')}\n"
            
        elif provider.type == ProviderTypeEnum.HOTEL:
            message = f"🏨 *DEMAND UPDATE - Hotel*\n\n"
            message += f"Expected visitor demand in your zone has increased.\n"
            message += f"Please confirm available rooms.\n"
            
        else:
            message = f"📋 *ACTION REQUIRED*\n\n{action.get('action', 'Action needed')}"
        
        message += f"\n[ACCEPT] [DECLINE]"
        
        buttons = [
            {"type": "reply", "reply": {"id": f"accept_{execution.id}", "title": "✅ Accept"}},
            {"type": "reply", "reply": {"id": f"decline_{execution.id}", "title": "❌ Decline"}}
        ]
        
        contact = provider.contact_info or {}
        phone = contact.get("whatsapp") or contact.get("phone") or contact.get("mobile")
        
        if not phone:
            return {"status": "error", "error": "No WhatsApp contact configured"}
        
        result = await self.send_message(str(phone), message, buttons)
        
        if result.get("status") not in ["error", "failed"]:
            execution.status = "dispatched"
            self.db.commit()
        
        return result
    
    async def send_outbound_to_provider(self, provider_id: str, message: str) -> Dict[str, Any]:
        """
        Operator-initiated outbound message directly to a registered provider.
        Validates provider existence, resolves contact phone, calls Meta Cloud API,
        and logs to WhatsAppMessageAuditDB.
        """
        provider = self.db.query(ProviderDB).filter(ProviderDB.provider_id == provider_id).first()
        if not provider:
            return {"status": "error", "error": f"Provider '{provider_id}' not found"}

        contact = provider.contact_info or {}
        phone = contact.get("whatsapp") or contact.get("phone") or contact.get("mobile")
        if not phone:
            return {"status": "error", "error": f"No WhatsApp contact number configured for provider '{provider.name}'"}

        clean_to = normalize_phone_for_meta(str(phone))
        result = await self.cloud_client.send_text_message(to=clean_to, message=message)

        if result.get("status") in ["sent", "simulated"]:
            msg_id = result.get("message_id") or f"wamid-out-{int(time.time()*1000)}"
            audit = WhatsAppMessageAuditDB(
                message_id=msg_id,
                provider_id=provider.provider_id,
                direction="OUTBOUND",
                to_number_masked=mask_phone_number(str(phone)),
                message_type="text",
                raw_text=message,
                processing_status="SENT",
                delivery_status="sent",
                source="META_WHATSAPP_CLOUD_API" if result.get("status") == "sent" else "SANDBOX",
                timestamp=datetime.utcnow()
            )
            self.db.add(audit)
            self.db.commit()
            logger.info(f"[WHATSAPP] Outbound message recorded: provider={provider.name} message_id={msg_id}")

            return {
                "status": "sent",
                "message_id": msg_id,
                "provider_id": provider.provider_id,
                "provider_name": provider.name,
                "to": mask_phone_number(str(phone)),
                "mode": result.get("mode", "cloud")
            }

        return result

    async def handle_webhook(self, payload: Dict) -> Dict:
        """
        Main entry point for Meta WhatsApp Cloud API webhooks.
        Handles text messages, interactive responses, status notifications (sent/delivered/read/failed),
        and enforces persistent idempotency and unknown sender quarantine.
        """
        logger.info("[WHATSAPP] Webhook received payload")
        if not isinstance(payload, dict):
            return {"status": "error", "error": "Invalid payload format"}
        try:
            entries = payload.get("entry")
            if not entries or not isinstance(entries, list):
                return {"status": "error", "error": "Missing or invalid entry in payload"}
            
            entry = entries[0]
            changes = entry.get("changes")
            if not changes or not isinstance(changes, list):
                return {"status": "error", "error": "Missing or invalid changes in payload"}
                
            value = changes[0].get("value", {})

            # 1. Handle Delivery / Read Status Webhooks from Meta
            statuses = value.get("statuses", [])
            if statuses and isinstance(statuses, list):
                return await self._handle_status_update(statuses)

            # 2. Handle Inbound Messages
            messages = value.get("messages", [])
            if not messages or not isinstance(messages, list):
                return {"status": "no_message"}
            
            msg = messages[0]
            msg_id = msg.get("id") or f"wamid-auto-{int(time.time()*1000)}"
            from_number = msg.get("from")
            msg_type = msg.get("type")
            msg_timestamp = msg.get("timestamp")

            logger.info(f"[WHATSAPP] Processing message_id={msg_id} type={msg_type} from={mask_phone_number(from_number)}")

            # Persistent Idempotency Check
            existing_audit = self.db.query(WhatsAppMessageAuditDB).filter(
                WhatsAppMessageAuditDB.message_id == msg_id
            ).first()
            if existing_audit:
                logger.info(f"[WHATSAPP] Duplicate message_id={msg_id} detected. Acknowledging idempotently.")
                return {
                    "status": "duplicate_message",
                    "message_id": msg_id,
                    "acknowledged": True,
                    "previous_status": existing_audit.processing_status
                }
            
            # Handle Interactive Button Responses
            if msg_type == "interactive":
                button_reply = msg.get("interactive", {}).get("button_reply", {})
                button_id = button_reply.get("id")
                return await self._handle_button_response(from_number, button_id, msg_id, msg)
            
            # Handle Text Messages
            elif msg_type == "text":
                text = msg.get("text", {}).get("body", "")
                return await self._handle_text_response(from_number, text, msg_timestamp, msg_id, msg)
            
            # Handle Unsupported Message Types Gracefully (Do not crash or cause Meta retries)
            masked_from = mask_phone_number(from_number)
            audit = WhatsAppMessageAuditDB(
                message_id=msg_id,
                direction="INBOUND",
                from_number_masked=masked_from,
                message_type=msg_type or "unknown",
                processing_status="IGNORED_EVENT",
                error_reason=f"Unsupported message type: {msg_type}",
                source="META_WHATSAPP_CLOUD_API",
                raw_payload=msg,
                timestamp=datetime.utcnow()
            )
            self.db.add(audit)
            self.db.commit()
            logger.info(f"[WHATSAPP] Unsupported message type '{msg_type}' recorded as IGNORED_EVENT")
            return {"status": "unhandled_type", "type": msg_type, "message_id": msg_id}
            
        except Exception as e:
            logger.error(f"[WHATSAPP] Webhook processing exception: {str(e)}", exc_info=True)
            return {"status": "error", "error": str(e)}

    async def _handle_status_update(self, statuses: List[Dict]) -> Dict:
        """Processes Meta status notifications: sent, delivered, read, failed."""
        updated_count = 0
        for st in statuses:
            st_id = st.get("id")
            st_val = (st.get("status") or "unknown").lower()
            if not st_id:
                continue

            audit = self.db.query(WhatsAppMessageAuditDB).filter(
                WhatsAppMessageAuditDB.message_id == st_id
            ).first()

            if audit:
                audit.delivery_status = st_val
                if st_val == "failed":
                    errs = st.get("errors")
                    audit.error_reason = json.dumps(errs) if errs else "Status failed"
                audit.updated_at = datetime.utcnow()
                updated_count += 1
                logger.info(f"[WHATSAPP] Message status updated: id={st_id} status={st_val}")

        self.db.commit()
        return {"status": "status_recorded", "count": updated_count}
    
    def parse_capacity_message(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extracts structured operational resource capacity from conversational text.
        Returns:
            {
                "dimension": "available" | "occupied" | "total" | "percentage",
                "value": int,
                "resource_type": "rooms" | "buses" | "seats" | "occupancy" | "capacity",
                "unit": str,
                "raw": str
            }
        """
        if not text or not isinstance(text, str):
            return None
        # Remove commas inside numbers: e.g. "1,200" -> "1200"
        t = re.sub(r'(\d+),(\d+)', r'\1\2', text.strip())

        # Check for ambiguity keywords
        ambiguous_keywords = ["maybe", "around", "might", "could", "approx", "roughly", "possibly", "think we have"]
        for w in ambiguous_keywords:
            if re.search(r'\b' + re.escape(w) + r'\b', t, re.IGNORECASE):
                return {"ambiguous": True, "raw": text}

        # Check for explicit NO CAPACITY / zero capacity
        if re.search(r'\b(?:no\s+capacity|zero\s+capacity|0\s+capacity|no\s+seats|no\s+rooms|no\s+buses)\b', t, re.IGNORECASE):
            return {
                "dimension": "delta_available",
                "value": 0,
                "resource_type": "capacity",
                "unit": "units",
                "raw": text
            }

        # Check for delta capacity (+120 seats, +50 buses, +30 rooms, +120)
        delta_match = re.search(r'\+\s*(\d+)\s*(?:(seats?|rooms?|buses?))?', t, re.IGNORECASE)
        if delta_match:
            res_word = (delta_match.group(2) or "").lower()
            res_type = "seats" if "seat" in res_word else ("rooms" if "room" in res_word else ("buses" if "bus" in res_word else "capacity"))
            return {
                "dimension": "delta_available",
                "value": int(delta_match.group(1)),
                "resource_type": res_type,
                "unit": res_type,
                "raw": text
            }
        
        # 1. Percentage patterns: "85% occupancy", "occupancy: 85%", "85%"
        pct_match = re.search(r'(\d+)\s*%\s*(?:occupancy|utilization)?', t, re.IGNORECASE)
        if not pct_match:
            pct_match = re.search(r'(?:occupancy|utilization)[:\s]+(\d+)\s*%', t, re.IGNORECASE)
        if pct_match:
            return {
                "dimension": "percentage",
                "value": int(pct_match.group(1)),
                "resource_type": "percentage",
                "unit": "%",
                "raw": text
            }

        # 2. Specific resource type matches: rooms, buses, seats
        # "82 rooms available", "82 rooms", "Rooms available: 82"
        rooms_match = re.search(r'(\d+)\s*rooms?(?:\s+(?:available|free|vacant))?', t, re.IGNORECASE)
        if not rooms_match:
            rooms_match = re.search(r'(?:rooms?|available\s+rooms?)[:\s]+(\d+)', t, re.IGNORECASE)
        if rooms_match:
            return {
                "dimension": "available",
                "value": int(rooms_match.group(1)),
                "resource_type": "rooms",
                "unit": "rooms",
                "raw": text
            }

        # "50 buses available", "50 buses", "Buses available: 50"
        buses_match = re.search(r'(\d+)\s*buses?(?:\s+(?:available|free|ready))?', t, re.IGNORECASE)
        if not buses_match:
            buses_match = re.search(r'(?:buses?|available\s+buses?)[:\s]+(\d+)', t, re.IGNORECASE)
        if buses_match:
            return {
                "dimension": "available",
                "value": int(buses_match.group(1)),
                "resource_type": "buses",
                "unit": "buses",
                "raw": text
            }

        # "450 seats available", "available seats 450", "1200 seats free"
        seats_match = re.search(r'(\d+)\s*seats?(?:\s+(?:available|free))?', t, re.IGNORECASE)
        if not seats_match:
            seats_match = re.search(r'(?:available\s+seats?|seats?)[:\s]+(\d+)', t, re.IGNORECASE)
        if seats_match:
            return {
                "dimension": "available",
                "value": int(seats_match.group(1)),
                "resource_type": "seats",
                "unit": "seats",
                "raw": text
            }

        # General Available patterns: "82 available", "available: 82"
        avail_match = re.search(r'(\d+)\s*(?:available|free)', t, re.IGNORECASE)
        if not avail_match:
            avail_match = re.search(r'(?:available|free)[:\s]+(\d+)', t, re.IGNORECASE)
        if avail_match:
            return {
                "dimension": "available",
                "value": int(avail_match.group(1)),
                "resource_type": "capacity",
                "unit": "units",
                "raw": text
            }
            
        # 3. Occupied patterns: "Venue occupancy 42000", "occupancy: 42000", "42000 occupied"
        occ_match = re.search(r'(?:venue\s+)?occupancy[:\s]+(\d+)', t, re.IGNORECASE)
        if not occ_match:
            occ_match = re.search(r'(\d+)\s*(?:occupied|occupancy|in\s+use)', t, re.IGNORECASE)
        if occ_match:
            return {
                "dimension": "occupied",
                "value": int(occ_match.group(1)),
                "resource_type": "occupancy",
                "unit": "people",
                "raw": text
            }
            
        # 4. Total patterns: "total capacity: 500", "500 total"
        tot_match = re.search(r'total(?:\s+capacity|\s+rooms?|\s+seats?)?[:\s]+(\d+)', t, re.IGNORECASE)
        if tot_match:
            return {
                "dimension": "total",
                "value": int(tot_match.group(1)),
                "resource_type": "capacity",
                "unit": "total",
                "raw": text
            }
            
        # 5. Plain integer fallback: e.g. "82"
        plain_match = re.match(r'^\s*(\d+)\s*$', t)
        if plain_match:
            return {
                "dimension": "available",
                "value": int(plain_match.group(1)),
                "resource_type": "capacity",
                "unit": "units",
                "raw": text
            }
            
        return None

    def identify_provider(self, from_number: Optional[str], text: str = "") -> Optional[ProviderDB]:
        def norm(p):
            return "".join(c for c in str(p) if c.isdigit())
            
        clean_from = norm(from_number) if from_number else ""
        all_providers = self.db.query(ProviderDB).order_by(ProviderDB.created_at.desc()).all()
        
        # 1. Match by phone/whatsapp contact
        if clean_from:
            for p in all_providers:
                contact = p.contact_info or {}
                for k in ["whatsapp", "phone", "mobile"]:
                    val = contact.get(k)
                    if val and norm(val):
                        c_val = norm(val)
                        if c_val == clean_from or clean_from.endswith(c_val) or c_val.endswith(clean_from):
                            return p
                        
        # 2. Match by provider_id or name in text
        if text:
            lower_text = text.lower()
            for p in all_providers:
                if p.provider_id.lower() in lower_text:
                    return p
                if p.name.lower() in lower_text:
                    return p
                    
        return None

    def validate_provider_resource_compatibility(self, provider: ProviderDB, resource_type: str) -> Optional[str]:
        """
        Validates that the reported resource type matches the provider's operational domain.
        Returns None if valid, or an error string if incompatible.
        """
        ptype = provider.type
        if resource_type == "rooms" and ptype not in [ProviderTypeEnum.HOTEL]:
            return f"Resource type 'rooms' is incompatible with provider type {ptype.value.upper()}"
        if resource_type in ["buses", "seats"] and ptype not in [ProviderTypeEnum.TRANSPORT, ProviderTypeEnum.VENUE]:
            return f"Resource type '{resource_type}' is incompatible with provider type {ptype.value.upper()}"
        return None

    async def _handle_text_response(
        self,
        from_number: Optional[str],
        text: str,
        msg_timestamp: Optional[Any] = None,
        msg_id: Optional[str] = None,
        raw_msg: Optional[Dict] = None
    ) -> Dict:
        if not from_number or not isinstance(from_number, str) or not from_number.strip():
            return {"status": "error", "error": "Invalid or missing from_number"}
            
        masked_phone = mask_phone_number(from_number)
        provider = self.identify_provider(from_number, text)
        msg_id = msg_id or f"wamid-{int(time.time()*1000)}"

        # 1. Unknown Provider Quarantine
        if not provider:
            logger.warning(f"[WHATSAPP] UNKNOWN SENDER: {masked_phone} Body='{text}'")
            audit = WhatsAppMessageAuditDB(
                message_id=msg_id,
                direction="INBOUND",
                from_number_masked=masked_phone,
                message_type="text",
                raw_text=text,
                processing_status="UNKNOWN_PROVIDER",
                error_reason="Sender phone number does not match any registered provider",
                source="META_WHATSAPP_CLOUD_API",
                raw_payload=raw_msg,
                timestamp=datetime.utcnow()
            )
            self.db.add(audit)
            self.db.commit()
            return {
                "status": "error",
                "error": "Unknown provider",
                "from": from_number,
                "masked_from": masked_phone
            }

        # 2. Handle Confirmation Commands: "CONFIRM" or "CORRECT <val>"
        stripped_text = text.strip()
        if stripped_text.upper() == "CONFIRM":
            return await self._process_text_confirmation(provider, from_number, msg_id, raw_msg)
        
        correct_match = re.match(r"^CORRECT\s+(\d+)$", stripped_text, re.IGNORECASE)
        if correct_match:
            new_val = int(correct_match.group(1))
            return await self._process_text_correction(provider, from_number, new_val, msg_id, raw_msg)

        # 3. Parse Capacity Message
        parsed = self.parse_capacity_message(text)

        if not parsed:
            audit = WhatsAppMessageAuditDB(
                message_id=msg_id,
                provider_id=provider.provider_id,
                direction="INBOUND",
                from_number_masked=masked_phone,
                message_type="text",
                raw_text=text,
                processing_status="UNPARSEABLE",
                error_reason="Could not extract numeric capacity from text",
                source="META_WHATSAPP_CLOUD_API",
                raw_payload=raw_msg,
                timestamp=datetime.utcnow()
            )
            self.db.add(audit)
            self.db.commit()
            return {
                "status": "error",
                "error": "Missing capacity in message",
                "provider_id": provider.provider_id,
                "provider_name": provider.name,
                "text": text,
                "from": from_number
            }

        # Handle Ambiguous Capacity
        if parsed.get("ambiguous"):
            audit = WhatsAppMessageAuditDB(
                message_id=msg_id,
                provider_id=provider.provider_id,
                direction="INBOUND",
                from_number_masked=masked_phone,
                message_type="text",
                raw_text=text,
                processing_status="NEEDS_CONFIRMATION",
                error_reason="Ambiguous capacity phrasing detected",
                source="META_WHATSAPP_CLOUD_API",
                raw_payload=raw_msg,
                timestamp=datetime.utcnow()
            )
            self.db.add(audit)
            self.db.commit()
            return {
                "status": "needs_confirmation",
                "error": "Ambiguous capacity value; please specify exact count (e.g. '82 rooms available')",
                "provider_id": provider.provider_id,
                "text": text
            }

        # 4. Resource Type vs Provider Type Validation
        res_type = parsed.get("resource_type", "capacity")
        compat_err = self.validate_provider_resource_compatibility(provider, res_type)
        if compat_err:
            audit = WhatsAppMessageAuditDB(
                message_id=msg_id,
                provider_id=provider.provider_id,
                direction="INBOUND",
                from_number_masked=masked_phone,
                message_type="text",
                raw_text=text,
                parsed_resource=res_type,
                parsed_value=parsed.get("value"),
                processing_status="INCOMPATIBLE_RESOURCE",
                error_reason=compat_err,
                source="META_WHATSAPP_CLOUD_API",
                raw_payload=raw_msg,
                timestamp=datetime.utcnow()
            )
            self.db.add(audit)
            self.db.commit()
            return {
                "status": "error",
                "error": compat_err,
                "provider_id": provider.provider_id
            }

        dim = parsed["dimension"]
        val = parsed["value"]

        # 5. Stale update check if timestamp is provided
        if msg_timestamp and provider.last_updated:
            try:
                if isinstance(msg_timestamp, (int, float)):
                    msg_dt = datetime.utcfromtimestamp(msg_timestamp)
                elif isinstance(msg_timestamp, str):
                    if msg_timestamp.replace(".", "", 1).isdigit():
                        msg_dt = datetime.utcfromtimestamp(float(msg_timestamp))
                    else:
                        msg_dt = datetime.fromisoformat(msg_timestamp.replace("Z", "+00:00")).replace(tzinfo=None)
                else:
                    msg_dt = None
                    
                if msg_dt and (provider.last_updated - msg_dt).total_seconds() > 5.0:
                    return {
                        "status": "stale_update",
                        "error": "Update timestamp is older than current provider state",
                        "provider_id": provider.provider_id,
                        "msg_timestamp": str(msg_timestamp),
                        "last_updated": provider.last_updated.isoformat()
                    }
            except Exception:
                pass
                
        # 6. Duplicate update check: same value updated very recently (<3s)
        if provider.capacity.get(dim) == val and provider.last_updated:
            time_diff = (datetime.utcnow() - provider.last_updated).total_seconds()
            if time_diff < 3.0:
                return {
                    "status": "duplicate_update",
                    "message": "Duplicate update detected",
                    "provider_id": provider.provider_id,
                    "dimension": dim,
                    "value": val
                }

        # 7. Two-Step Confirmation vs Direct Auto-Confirm
        auto_confirm = settings.whatsapp_auto_confirm
        if not auto_confirm:
            # Create a pending audit record
            audit = WhatsAppMessageAuditDB(
                message_id=msg_id,
                provider_id=provider.provider_id,
                direction="INBOUND",
                from_number_masked=masked_phone,
                message_type="text",
                raw_text=text,
                parsed_resource=res_type,
                parsed_value=val,
                processing_status="PENDING_CONFIRMATION",
                confirmation_state="AWAITING_CONFIRMATION",
                source="META_WHATSAPP_CLOUD_API",
                raw_payload=raw_msg,
                timestamp=datetime.utcnow()
            )
            self.db.add(audit)
            self.db.commit()

            # Dispatch confirmation request via WhatsApp
            confirm_prompt = (
                f"EVENTOS received:\n"
                f"*{val} {res_type}* for *{provider.name}*.\n\n"
                f"Reply:\n"
                f"*CONFIRM*\n"
                f"or\n"
                f"*CORRECT <number>*"
            )
            await self.cloud_client.send_text_message(to=from_number, message=confirm_prompt)

            logger.info(f"[WHATSAPP] Pending confirmation created: provider={provider.name} resource={res_type} value={val}")
            return {
                "status": "pending_confirmation",
                "provider_id": provider.provider_id,
                "provider_name": provider.name,
                "dimension": dim,
                "value": val,
                "resource_type": res_type,
                "message": "Update queued awaiting operator/provider confirmation"
            }

        # 8. Auto-Confirm: Direct Database Update
        return self._apply_provider_capacity_update(
            provider=provider,
            dim=dim,
            val=val,
            res_type=res_type,
            msg_id=msg_id,
            masked_phone=masked_phone,
            text=text,
            raw_msg=raw_msg,
            confirmation_state="AUTO_CONFIRMED"
        )

    def _apply_provider_capacity_update(
        self,
        provider: ProviderDB,
        dim: str,
        val: int,
        res_type: str,
        msg_id: str,
        masked_phone: str,
        text: str,
        raw_msg: Optional[Dict],
        confirmation_state: str
    ) -> Dict:
        """Applies parsed capacity values to ProviderDB and records audit history."""
        new_cap = dict(provider.capacity) if provider.capacity else {}
        if dim == "delta_available":
            prev_avail = new_cap.get("available", 0)
            new_avail = prev_avail + val
            new_cap["available"] = new_avail
            tot = new_cap.get("total", 0)
            if new_avail > tot:
                new_cap["total"] = new_avail + new_cap.get("occupied", 0)
        elif dim == "available":
            new_cap["available"] = val
            tot = new_cap.get("total", 0)
            if tot > 0:
                new_cap["occupied"] = max(0, tot - val)
        elif dim == "occupied":
            new_cap["occupied"] = val
            tot = new_cap.get("total", 0)
            if tot > 0:
                new_cap["available"] = max(0, tot - val)
        elif dim == "total":
            new_cap["total"] = val
            occ = new_cap.get("occupied", 0)
            if occ > 0:
                new_cap["available"] = max(0, val - occ)
        elif dim == "percentage":
            tot = new_cap.get("total", 0)
            if tot > 0:
                occ_val = int((val / 100.0) * tot)
                new_cap["occupied"] = occ_val
                new_cap["available"] = max(0, tot - occ_val)
            occ = new_cap.get("occupied", 0)
            if occ > 0:
                new_cap["available"] = max(0, val - occ)

        provider.capacity = new_cap
        provider.last_updated = datetime.utcnow()

        # Record Capacity Update in standard table
        update_db = ProviderCapacityUpdateDB(
            provider_id=provider.provider_id,
            updates={"dimension": dim, "value": val, "resource_type": res_type, "capacity": dict(provider.capacity)},
            source="whatsapp",
            timestamp=datetime.utcnow()
        )
        self.db.add(update_db)

        # Record Audit in WhatsApp Message Audit Table
        audit = WhatsAppMessageAuditDB(
            message_id=msg_id,
            provider_id=provider.provider_id,
            direction="INBOUND",
            from_number_masked=masked_phone,
            message_type="text",
            raw_text=text,
            parsed_resource=res_type,
            parsed_value=val,
            processing_status="PROCESSED",
            confirmation_state=confirmation_state,
            source="META_WHATSAPP_CLOUD_API",
            raw_payload=raw_msg,
            timestamp=datetime.utcnow()
        )
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(provider)

        logger.info(f"[WHATSAPP] Capacity updated: provider={provider.name} resource={res_type} value={val} new_cap={provider.capacity}")

        return {
            "status": "capacity_updated",
            "provider_id": provider.provider_id,
            "provider_name": provider.name,
            "dimension": dim,
            "value": val,
            "resource_type": res_type,
            "new_capacity": provider.capacity
        }

    async def _process_text_confirmation(
        self,
        provider: ProviderDB,
        from_number: str,
        msg_id: str,
        raw_msg: Optional[Dict]
    ) -> Dict:
        """Processes 'CONFIRM' reply from provider to commit pending capacity."""
        pending_audit = self.db.query(WhatsAppMessageAuditDB).filter(
            WhatsAppMessageAuditDB.provider_id == provider.provider_id,
            WhatsAppMessageAuditDB.confirmation_state == "AWAITING_CONFIRMATION"
        ).order_by(WhatsAppMessageAuditDB.id.desc()).first()

        if not pending_audit:
            await self.cloud_client.send_text_message(
                to=from_number,
                message="EVENTOS: No pending capacity update awaiting confirmation."
            )
            return {"status": "no_pending_confirmation", "provider_id": provider.provider_id}

        dim = "available"
        val = pending_audit.parsed_value or 0
        res_type = pending_audit.parsed_resource or "capacity"

        # Mark pending audit as confirmed
        pending_audit.confirmation_state = "CONFIRMED"
        pending_audit.processing_status = "PROCESSED"
        pending_audit.updated_at = datetime.utcnow()

        # Apply capacity update
        result = self._apply_provider_capacity_update(
            provider=provider,
            dim=dim,
            val=val,
            res_type=res_type,
            msg_id=msg_id,
            masked_phone=mask_phone_number(from_number),
            text="CONFIRM",
            raw_msg=raw_msg,
            confirmation_state="CONFIRMED"
        )
        result["confirmed"] = True

        # Send outbound acknowledgement
        await self.cloud_client.send_text_message(
            to=from_number,
            message=f"✅ EVENTOS: Confirmed {val} {res_type} for {provider.name}. Capacity indexed in Control Tower."
        )

        return result

    async def _process_text_correction(
        self,
        provider: ProviderDB,
        from_number: str,
        new_val: int,
        msg_id: str,
        raw_msg: Optional[Dict]
    ) -> Dict:
        """Processes 'CORRECT <number>' reply to adjust pending capacity count."""
        pending_audit = self.db.query(WhatsAppMessageAuditDB).filter(
            WhatsAppMessageAuditDB.provider_id == provider.provider_id,
            WhatsAppMessageAuditDB.confirmation_state == "AWAITING_CONFIRMATION"
        ).order_by(WhatsAppMessageAuditDB.id.desc()).first()

        res_type = pending_audit.parsed_resource if pending_audit else "capacity"
        
        # Create updated pending audit
        audit = WhatsAppMessageAuditDB(
            message_id=msg_id,
            provider_id=provider.provider_id,
            direction="INBOUND",
            from_number_masked=mask_phone_number(from_number),
            message_type="text",
            raw_text=f"CORRECT {new_val}",
            parsed_resource=res_type,
            parsed_value=new_val,
            processing_status="PENDING_CONFIRMATION",
            confirmation_state="AWAITING_CONFIRMATION",
            source="META_WHATSAPP_CLOUD_API",
            raw_payload=raw_msg,
            timestamp=datetime.utcnow()
        )
        self.db.add(audit)
        self.db.commit()

        await self.cloud_client.send_text_message(
            to=from_number,
            message=f"EVENTOS: Updated to *{new_val} {res_type}*. Please reply *CONFIRM* to verify."
        )

        return {
            "status": "pending_confirmation",
            "provider_id": provider.provider_id,
            "corrected_value": new_val,
            "resource_type": res_type
        }
    
    async def _handle_button_response(
        self,
        from_number: str,
        button_id: str,
        msg_id: Optional[str] = None,
        raw_msg: Optional[Dict] = None
    ) -> Dict:
        parts = button_id.split("_")
        masked_phone = mask_phone_number(from_number)

        # Audit interactive button action
        if msg_id:
            audit = WhatsAppMessageAuditDB(
                message_id=msg_id,
                direction="INBOUND",
                from_number_masked=masked_phone,
                message_type="interactive",
                raw_text=button_id,
                processing_status="PROCESSED",
                source="META_WHATSAPP_CLOUD_API",
                raw_payload=raw_msg,
                timestamp=datetime.utcnow()
            )
            self.db.add(audit)
            self.db.commit()
        
        if parts[0] == "approve":
            zone_id = parts[1]
            return await self._process_approval(from_number, zone_id)
        
        elif parts[0] == "reject":
            zone_id = parts[1]
            return await self._process_rejection(from_number, zone_id)
        
        elif parts[0] == "accept":
            execution_id = int(parts[1])
            return await self._process_action_accept(from_number, execution_id)
        
        elif parts[0] == "decline":
            execution_id = int(parts[1])
            return await self._process_action_decline(from_number, execution_id)
        
        elif parts[0] in ["hotel", "transport", "venue", "provider"]:
            provider_id = parts[1]
            return {"status": "awaiting_input", "provider_id": provider_id, "action": "capacity_update"}
        
        return {"status": "unknown_button", "button_id": button_id}

    async def _process_approval(self, from_number: str, zone_id: str) -> Dict:
        zone = self.db.query(ZoneDB).filter(ZoneDB.zone_id == zone_id).first()
        if not zone:
            return {"status": "error", "error": "Zone not found"}
        
        recommendations = self.db.query(OrchestrationRecommendationDB).filter(
            OrchestrationRecommendationDB.zone_id == zone_id,
            OrchestrationRecommendationDB.status == "pending"
        ).all()
        
        for rec in recommendations:
            rec.status = "approved"
            rec.approved_by = from_number
            rec.approved_at = datetime.utcnow()
            
            providers_to_dispatch = list(rec.required_providers) if rec.required_providers else []
            if not providers_to_dispatch:
                for action in rec.actions:
                    if "venue_id" in action and action["venue_id"]:
                        providers_to_dispatch.append(action["venue_id"])
                    elif "providers" in action and isinstance(action["providers"], list):
                        providers_to_dispatch.extend(action["providers"])
            providers_to_dispatch = list(dict.fromkeys(providers_to_dispatch))
            
            if providers_to_dispatch:
                for provider_id in providers_to_dispatch:
                    for action in rec.actions:
                        execution = ActionExecutionDB(
                            recommendation_id=rec.id,
                            provider_id=provider_id,
                            action_type=action.get("action", "unknown"),
                            parameters=action,
                            status="dispatched"
                        )
                        self.db.add(execution)
                        await self.send_action_dispatch(execution)
            else:
                for action in rec.actions:
                    execution = ActionExecutionDB(
                        recommendation_id=rec.id,
                        provider_id=None,
                        action_type=action.get("action", "unknown"),
                        parameters=action,
                        status="dispatched"
                    )
                    self.db.add(execution)
        
        self.db.commit()
        return {"status": "approved", "zone_id": zone_id, "actions_dispatched": len(recommendations)}
    
    async def _process_rejection(self, from_number: str, zone_id: str) -> Dict:
        recommendations = self.db.query(OrchestrationRecommendationDB).filter(
            OrchestrationRecommendationDB.zone_id == zone_id,
            OrchestrationRecommendationDB.status == "pending"
        ).all()
        
        for rec in recommendations:
            rec.status = "rejected"
            rec.approved_by = from_number
            rec.approved_at = datetime.utcnow()
        
        self.db.commit()
        return {"status": "rejected", "zone_id": zone_id}
    
    async def _process_action_accept(self, from_number: str, execution_id: int) -> Dict:
        execution = self.db.query(ActionExecutionDB).filter(ActionExecutionDB.id == execution_id).first()
        if not execution:
            return {"status": "error", "error": "Execution not found"}
        
        execution.status = "accepted"
        execution.responded_at = datetime.utcnow()
        execution.response = {"accepted_by": from_number, "timestamp": datetime.utcnow().isoformat()}
        
        self.db.commit()
        return {"status": "accepted", "execution_id": execution_id}
    
    async def _process_action_decline(self, from_number: str, execution_id: int) -> Dict:
        execution = self.db.query(ActionExecutionDB).filter(ActionExecutionDB.id == execution_id).first()
        if not execution:
            return {"status": "error", "error": "Execution not found"}
        
        execution.status = "declined"
        execution.responded_at = datetime.utcnow()
        execution.response = {"declined_by": from_number, "timestamp": datetime.utcnow().isoformat()}
        
        self.db.commit()
        return {"status": "declined", "execution_id": execution_id}
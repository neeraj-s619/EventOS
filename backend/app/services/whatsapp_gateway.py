"""
EVENTOS WhatsApp Gateway & Human Operational Telemetry Architecture.
Provides a decoupled gateway interface supporting:
1. SandboxAdapter (Default): Operational telemetry layer where human providers report
   real-world capacity (+120 seats, +50 seats, NO CAPACITY) to close the Digital Twin capacity gap,
   without requiring Meta developer credentials.
2. MetaCloudAdapter: Optional direct Meta Graph API integration when credentials are configured.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
import time
import re

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.database import (
    ProviderDB, ProviderTypeEnum, ProviderCapacityUpdateDB,
    WhatsAppMessageAuditDB, EventDB
)
from app.services.whatsapp_cloud import (
    WhatsAppCloudClient, mask_phone_number, normalize_phone_for_meta
)

logger = logging.getLogger("eventos.whatsapp.gateway")


# ─────────────────────────────────────────────────────────────────
# Data Transfer Models
# ─────────────────────────────────────────────────────────────────

@dataclass
class OperationalCapacityRequest:
    """Outbound operational poll sent to a service provider."""
    request_id: str
    event_id: str
    provider_id: str
    provider_name: str
    zone_id: Optional[str]
    required_capacity: int
    weather_trigger: str
    message: str
    suggested_replies: List[str]
    status: str = "DISPATCHED"
    dispatched_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    channel: str = "WHATSAPP_SANDBOX"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ProviderOperationalResponse:
    """Inbound operational response reported by a provider."""
    provider_id: str
    provider_name: str
    raw_text: str
    delta_capacity: int
    new_available_capacity: int
    dimension: str
    resource_type: str
    status: str
    message_id: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    channel: str = "WHATSAPP_SANDBOX"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ─────────────────────────────────────────────────────────────────
# Abstract Gateway Base
# ─────────────────────────────────────────────────────────────────

class BaseWhatsAppGateway(ABC):
    """Abstract interface defining the WhatsApp communications gateway."""

    @property
    @abstractmethod
    def gateway_name(self) -> str:
        """Name of the active gateway adapter."""
        pass

    @property
    @abstractmethod
    def is_sandbox(self) -> bool:
        """True if operating in sandbox operational telemetry mode."""
        pass

    @abstractmethod
    async def dispatch_capacity_poll(
        self,
        provider_id: str,
        event_id: str,
        required_capacity: int,
        weather_trigger: str,
        zone_id: Optional[str] = None
    ) -> OperationalCapacityRequest:
        """Dispatches a capacity inquiry to a registered provider."""
        pass

    @abstractmethod
    async def ingest_provider_telemetry(
        self,
        provider_id: str,
        response_text: str,
        event_id: Optional[str] = None
    ) -> ProviderOperationalResponse:
        """Ingests and parses human operational response from a provider."""
        pass

    @abstractmethod
    def get_gateway_status(self) -> Dict[str, Any]:
        """Returns the gateway operating state and adapter health."""
        pass


# ─────────────────────────────────────────────────────────────────
# Sandbox Adapter (Default Operational Telemetry)
# ─────────────────────────────────────────────────────────────────

class SandboxAdapter(BaseWhatsAppGateway):
    """
    Operational Telemetry Sandbox Gateway.
    Allows testing, live simulation, and judge demonstrations of the complete
    human-in-the-loop capacity feedback loop without depending on external Meta servers.
    """

    def __init__(self, db: Session):
        self.db = db

    @property
    def gateway_name(self) -> str:
        return "WHATSAPP_OPERATIONS_SANDBOX"

    @property
    def is_sandbox(self) -> bool:
        return True

    def get_gateway_status(self) -> Dict[str, Any]:
        recent_audits = self.db.query(WhatsAppMessageAuditDB).order_by(
            WhatsAppMessageAuditDB.timestamp.desc()
        ).limit(5).all()

        return {
            "mode": "SANDBOX_ACTIVE",
            "display_badge": "WHATSAPP OPERATIONS: SANDBOX ACTIVE • Meta Cloud: NOT CONFIGURED",
            "gateway_name": self.gateway_name,
            "is_sandbox": True,
            "meta_cloud_configured": settings.is_cloud_ready(),
            "telemetry_type": "Human Operational Telemetry Loop",
            "description": "Interactive local sandbox handling capacity inquiries and delta updates",
            "audit_trail_count": self.db.query(WhatsAppMessageAuditDB).count(),
            "last_activity": recent_audits[0].timestamp.isoformat() if recent_audits and recent_audits[0].timestamp else None
        }

    async def dispatch_capacity_poll(
        self,
        provider_id: str,
        event_id: str,
        required_capacity: int,
        weather_trigger: str,
        zone_id: Optional[str] = None
    ) -> OperationalCapacityRequest:
        provider = self.db.query(ProviderDB).filter(ProviderDB.provider_id == provider_id).first()
        if not provider:
            raise ValueError(f"Provider '{provider_id}' not found")

        contact = provider.contact_info or {}
        phone = contact.get("whatsapp") or contact.get("phone") or "919876543210"
        masked = mask_phone_number(str(phone))

        req_id = f"op-req-{int(time.time()*1000)}"
        msg = (
            f"🌧️ *EVENTOS Operational Capacity Poll*\n\n"
            f"*Condition:* {weather_trigger}\n"
            f"*Requirement:* Additional {required_capacity} capacity needed immediately for *{provider.name}*.\n\n"
            f"Please reply with your available standby units:\n"
            f"• *+{required_capacity} seats* (or rooms/buses)\n"
            f"• *+{max(10, required_capacity // 2)} seats*\n"
            f"• *NO CAPACITY*"
        )

        suggested = [
            f"+{required_capacity} seats",
            f"+{max(10, required_capacity // 2)} seats",
            "NO CAPACITY"
        ]

        # Audit outbound record
        audit = WhatsAppMessageAuditDB(
            message_id=req_id,
            provider_id=provider.provider_id,
            direction="OUTBOUND",
            to_number_masked=masked,
            message_type="operational_poll",
            raw_text=msg,
            processing_status="DISPATCHED",
            delivery_status="delivered",
            source="WHATSAPP_SANDBOX",
            timestamp=datetime.utcnow()
        )
        self.db.add(audit)
        self.db.commit()

        logger.info(f"[WHATSAPP_SANDBOX] Dispatched operational poll {req_id} to provider {provider.name}")

        return OperationalCapacityRequest(
            request_id=req_id,
            event_id=event_id,
            provider_id=provider.provider_id,
            provider_name=provider.name,
            zone_id=zone_id or provider.zone_id,
            required_capacity=required_capacity,
            weather_trigger=weather_trigger,
            message=msg,
            suggested_replies=suggested,
            status="DISPATCHED",
            channel="WHATSAPP_SANDBOX"
        )

    async def ingest_provider_telemetry(
        self,
        provider_id: str,
        response_text: str,
        event_id: Optional[str] = None
    ) -> ProviderOperationalResponse:
        provider = self.db.query(ProviderDB).filter(ProviderDB.provider_id == provider_id).first()
        if not provider:
            raise ValueError(f"Provider '{provider_id}' not found")

        contact = provider.contact_info or {}
        phone = contact.get("whatsapp") or contact.get("phone") or "919876543210"
        masked = mask_phone_number(str(phone))

        msg_id = f"wamid-sandbox-{int(time.time()*1000)}"
        text = response_text.strip()

        # Parse text response for delta, absolute count, or zero capacity
        delta = 0
        dim = "available"
        res_type = "seats" if provider.type == ProviderTypeEnum.TRANSPORT else (
            "rooms" if provider.type == ProviderTypeEnum.HOTEL else "capacity"
        )
        status = "CONFIRMED"

        upper_text = text.upper()

        if "NO CAPACITY" in upper_text or "ZERO" in upper_text or upper_text == "0":
            delta = 0
            status = "NO_CAPACITY"
        else:
            # Check for +<number> (delta)
            delta_match = re.search(r'\+\s*(\d+)', text)
            if delta_match:
                delta = int(delta_match.group(1))
            else:
                # Fallback to plain number
                num_match = re.search(r'(\d+)', text)
                if num_match:
                    num_val = int(num_match.group(1))
                    # If provider already has capacity, treat as delta or new available
                    delta = num_val
                else:
                    status = "UNPARSEABLE"

        # Apply update to provider in DB if parsed successfully
        curr_cap = dict(provider.capacity) if provider.capacity else {"available": 0, "total": 0, "occupied": 0}
        curr_avail = curr_cap.get("available", 0)
        curr_total = curr_cap.get("total", 0)

        if status == "CONFIRMED":
            new_avail = curr_avail + delta
            # If new available exceeds total, expand total as well
            new_total = max(curr_total, new_avail + curr_cap.get("occupied", 0))
            curr_cap["available"] = new_avail
            curr_cap["total"] = new_total
            provider.capacity = curr_cap
            provider.last_updated = datetime.utcnow()

            # Record capacity update
            cap_update = ProviderCapacityUpdateDB(
                provider_id=provider.provider_id,
                updates={"delta": delta, "new_available": new_avail, "raw_text": text},
                source="whatsapp_sandbox",
                timestamp=datetime.utcnow()
            )
            self.db.add(cap_update)
        else:
            new_avail = curr_avail

        # Record audit message
        audit = WhatsAppMessageAuditDB(
            message_id=msg_id,
            provider_id=provider.provider_id,
            direction="INBOUND",
            from_number_masked=masked,
            message_type="operational_response",
            raw_text=text,
            parsed_resource=res_type,
            parsed_value=delta,
            processing_status="PROCESSED" if status == "CONFIRMED" else "FLAGGED",
            confirmation_state="CONFIRMED" if status == "CONFIRMED" else "NOT_APPLIED",
            source="WHATSAPP_SANDBOX",
            timestamp=datetime.utcnow()
        )
        self.db.add(audit)
        self.db.commit()

        logger.info(
            f"[WHATSAPP_SANDBOX] Ingested response from {provider.name}: '{text}' "
            f"-> delta={delta}, new_available={new_avail}, status={status}"
        )

        return ProviderOperationalResponse(
            provider_id=provider.provider_id,
            provider_name=provider.name,
            raw_text=text,
            delta_capacity=delta,
            new_available_capacity=new_avail,
            dimension=dim,
            resource_type=res_type,
            status=status,
            message_id=msg_id,
            channel="WHATSAPP_SANDBOX"
        )


# ─────────────────────────────────────────────────────────────────
# Meta Cloud Adapter (Optional Fallback)
# ─────────────────────────────────────────────────────────────────

class MetaCloudAdapter(BaseWhatsAppGateway):
    """
    Production Meta WhatsApp Cloud API Adapter.
    Active only when access token and phone number ID are present in environment/settings.
    """

    def __init__(self, db: Session, cloud_client: Optional[WhatsAppCloudClient] = None):
        self.db = db
        self.cloud_client = cloud_client or WhatsAppCloudClient()
        self._fallback_sandbox = SandboxAdapter(db)

    @property
    def gateway_name(self) -> str:
        return "META_WHATSAPP_CLOUD_API"

    @property
    def is_sandbox(self) -> bool:
        return False

    def get_gateway_status(self) -> Dict[str, Any]:
        if not self.cloud_client.is_configured:
            status = self._fallback_sandbox.get_gateway_status()
            status["meta_cloud_configured"] = False
            status["fallback_active"] = True
            return status

        return {
            "mode": "META_CLOUD_ACTIVE",
            "display_badge": f"WHATSAPP OPERATIONS: META CLOUD LIVE ({self.cloud_client.api_version})",
            "gateway_name": self.gateway_name,
            "is_sandbox": False,
            "meta_cloud_configured": True,
            "api_version": self.cloud_client.api_version,
            "phone_number_id": self.cloud_client.phone_number_id,
            "telemetry_type": "Direct Meta Cloud API Graph Webhook",
            "description": "Production Meta WhatsApp Cloud API connection"
        }

    async def dispatch_capacity_poll(
        self,
        provider_id: str,
        event_id: str,
        required_capacity: int,
        weather_trigger: str,
        zone_id: Optional[str] = None
    ) -> OperationalCapacityRequest:
        if not self.cloud_client.is_configured:
            logger.info("[WHATSAPP_GATEWAY] Meta Cloud not configured — using SandboxAdapter")
            return await self._fallback_sandbox.dispatch_capacity_poll(
                provider_id, event_id, required_capacity, weather_trigger, zone_id
            )

        provider = self.db.query(ProviderDB).filter(ProviderDB.provider_id == provider_id).first()
        if not provider:
            raise ValueError(f"Provider '{provider_id}' not found")

        contact = provider.contact_info or {}
        phone = contact.get("whatsapp") or contact.get("phone")
        if not phone:
            raise ValueError(f"Provider '{provider.name}' has no phone configured")

        clean_to = normalize_phone_for_meta(str(phone))
        msg = (
            f"🌧️ *EVENTOS Operational Alert*\n\n"
            f"*Condition:* {weather_trigger}\n"
            f"*Required Capacity:* +{required_capacity} seats.\n"
            f"Reply with available standby capacity."
        )

        res = await self.cloud_client.send_text_message(to=clean_to, message=msg)
        req_id = res.get("message_id") or f"op-req-{int(time.time()*1000)}"

        return OperationalCapacityRequest(
            request_id=req_id,
            event_id=event_id,
            provider_id=provider.provider_id,
            provider_name=provider.name,
            zone_id=zone_id or provider.zone_id,
            required_capacity=required_capacity,
            weather_trigger=weather_trigger,
            message=msg,
            suggested_replies=[f"+{required_capacity} seats", "NO CAPACITY"],
            status="DISPATCHED",
            channel="META_CLOUD"
        )

    async def ingest_provider_telemetry(
        self,
        provider_id: str,
        response_text: str,
        event_id: Optional[str] = None
    ) -> ProviderOperationalResponse:
        # Re-use robust sandbox parsing and DB updates
        return await self._fallback_sandbox.ingest_provider_telemetry(
            provider_id, response_text, event_id
        )


# ─────────────────────────────────────────────────────────────────
# Gateway Factory
# ─────────────────────────────────────────────────────────────────

def get_whatsapp_gateway(db: Session) -> BaseWhatsAppGateway:
    """
    Factory creating the appropriate WhatsAppGateway implementation.
    If Meta Cloud credentials are present and mode is 'cloud', returns MetaCloudAdapter.
    Otherwise returns the reliable, zero-credential SandboxAdapter.
    """
    if settings.get_effective_mode() == "cloud" and settings.is_cloud_ready():
        return MetaCloudAdapter(db)
    return SandboxAdapter(db)

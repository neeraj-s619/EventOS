"""
EVENTOS Provider Messaging Gateway & Multi-Channel Adapter Architecture.
Provides an enterprise messaging gateway abstraction supporting:
1. TelegramAdapter (LIVE / Primary): Bi-directional Telegram Bot API with inline keyboards and polling/webhook.
2. WhatsAppAdapter (Secondary/Cloud): Meta Cloud API integration.
3. SandboxAdapter (Local Fallback): Zero-credential interactive operational loop for local dev & demo.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
import time

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.database import (
    ProviderDB, ProviderTypeEnum, ProviderCapacityUpdateDB,
    TelegramMessageAuditDB, WhatsAppMessageAuditDB, EventDB
)
from app.services.telegram.client import TelegramBotClient
from app.services.telegram.service import TelegramService
from app.services.telegram.parser import parse_operational_message

logger = logging.getLogger("eventos.provider.gateway")


# ─────────────────────────────────────────────────────────────────
# Data Transfer Objects
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
    channel: str = "TELEGRAM"

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
    channel: str = "TELEGRAM"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ─────────────────────────────────────────────────────────────────
# Base Provider Adapter Interface
# ─────────────────────────────────────────────────────────────────

class BaseProviderAdapter(ABC):
    """Abstract interface for messaging transport adapters."""

    @property
    @abstractmethod
    def adapter_name(self) -> str:
        """Name of the adapter."""
        pass

    @property
    @abstractmethod
    def channel(self) -> str:
        """Channel name (TELEGRAM, WHATSAPP, SANDBOX)."""
        pass

    @property
    @abstractmethod
    def is_live(self) -> bool:
        """True if connected to real external network APIs."""
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
        """Dispatches capacity poll to provider."""
        pass

    @abstractmethod
    async def ingest_provider_telemetry(
        self,
        provider_id: str,
        response_text: str,
        event_id: Optional[str] = None
    ) -> ProviderOperationalResponse:
        """Ingests and parses human operational response."""
        pass

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Returns health and operational metrics."""
        pass


# ─────────────────────────────────────────────────────────────────
# Telegram Adapter (LIVE / Primary)
# ─────────────────────────────────────────────────────────────────

class TelegramAdapter(BaseProviderAdapter):
    """
    Live Telegram Bot Adapter.
    Communicates with providers via Telegram Bot API with inline keyboards and webhook/polling.
    """

    def __init__(self, db: Session, client: Optional[TelegramBotClient] = None):
        self.db = db
        self.client = client or TelegramBotClient()
        self.service = TelegramService(db=db, client=self.client)

    @property
    def adapter_name(self) -> str:
        return "TELEGRAM_BOT_ADAPTER"

    @property
    def channel(self) -> str:
        return "TELEGRAM"

    @property
    def is_live(self) -> bool:
        return self.client.is_configured

    def get_status(self) -> Dict[str, Any]:
        stat = self.service.get_telemetry_status()
        stat["adapter"] = self.adapter_name
        stat["channel"] = self.channel
        stat["is_live"] = self.is_live
        return stat

    async def dispatch_capacity_poll(
        self,
        provider_id: str,
        event_id: str,
        required_capacity: int,
        weather_trigger: str,
        zone_id: Optional[str] = None
    ) -> OperationalCapacityRequest:
        res = await self.service.dispatch_capacity_poll(
            provider_id=provider_id,
            event_id=event_id,
            required_capacity=required_capacity,
            weather_trigger=weather_trigger,
            zone_id=zone_id
        )

        return OperationalCapacityRequest(
            request_id=res["request_id"],
            event_id=event_id,
            provider_id=res["provider_id"],
            provider_name=res["provider_name"],
            zone_id=zone_id,
            required_capacity=required_capacity,
            weather_trigger=weather_trigger,
            message=res["message"],
            suggested_replies=[f"+{required_capacity} seats", "+50 seats", "NO CAPACITY"],
            status=res["delivery_status"].upper(),
            channel="TELEGRAM"
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

        parsed = parse_operational_message(
            response_text,
            default_resource=provider.type.value
        )

        chat_id = (provider.contact_info or {}).get("telegram_chat_id", "local_sandbox")

        res = self.service._apply_operational_response(
            provider=provider,
            parsed=parsed,
            raw_text=response_text,
            chat_id=str(chat_id),
            telegram_user_id="operator_console",
            msg_type="telemetry_ingest"
        )

        return ProviderOperationalResponse(
            provider_id=provider.provider_id,
            provider_name=provider.name,
            raw_text=response_text,
            delta_capacity=res["delta"],
            new_available_capacity=res["new_available"],
            dimension="available",
            resource_type=res["resource_type"],
            status=res["status"],
            message_id=res["audit_id"],
            channel="TELEGRAM"
        )


# ─────────────────────────────────────────────────────────────────
# Sandbox Adapter (Local Fallback)
# ─────────────────────────────────────────────────────────────────

class SandboxAdapter(BaseProviderAdapter):
    """
    Local Operational Telemetry Sandbox.
    Zero-credential fallback ensuring testing and judge demonstrations always work.
    """

    def __init__(self, db: Session):
        self.db = db

    @property
    def adapter_name(self) -> str:
        return "OPERATIONS_SANDBOX_ADAPTER"

    @property
    def channel(self) -> str:
        return "SANDBOX"

    @property
    def is_live(self) -> bool:
        return False

    def get_status(self) -> Dict[str, Any]:
        count = self.db.query(TelegramMessageAuditDB).count()
        return {
            "adapter": self.adapter_name,
            "channel": self.channel,
            "is_live": False,
            "display_badge": "SANDBOX ACTIVE (TELEGRAM NOT CONFIGURED)",
            "description": "Local operational telemetry sandbox for evaluation and testing",
            "audit_trail_count": count
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

        req_id = f"op-sb-poll-{int(time.time() * 1000)}"
        msg = (
            f"🌧️ *EVENTOS Operational Capacity Poll*\n\n"
            f"*Condition:* {weather_trigger}\n"
            f"*Requirement:* Additional +{required_capacity} seats needed immediately for *{provider.name}*.\n\n"
            f"Please confirm standby capacity."
        )

        audit = TelegramMessageAuditDB(
            message_id=req_id,
            provider_id=provider.provider_id,
            channel="SANDBOX",
            direction="OUTBOUND",
            chat_id="sandbox_console",
            message_type="operational_poll",
            raw_text=msg,
            parsed_resource="transport_capacity",
            parsed_value=required_capacity,
            processing_status="DISPATCHED",
            status="delivered",
            timestamp=datetime.utcnow()
        )
        self.db.add(audit)
        self.db.commit()

        return OperationalCapacityRequest(
            request_id=req_id,
            event_id=event_id,
            provider_id=provider.provider_id,
            provider_name=provider.name,
            zone_id=zone_id or provider.zone_id,
            required_capacity=required_capacity,
            weather_trigger=weather_trigger,
            message=msg,
            suggested_replies=[f"+{required_capacity} seats", "+50 seats", "NO CAPACITY"],
            status="DISPATCHED",
            channel="SANDBOX"
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

        parsed = parse_operational_message(
            response_text,
            default_resource=provider.type.value
        )

        curr_cap = dict(provider.capacity) if provider.capacity else {"available": 0, "total": 0, "occupied": 0}
        curr_avail = curr_cap.get("available", 0)
        curr_total = curr_cap.get("total", 0)

        delta = parsed.quantity or 0 if parsed.status == "CONFIRMED" else 0
        new_avail = (curr_avail + delta) if parsed.is_delta else (parsed.quantity or curr_avail)

        if parsed.status == "CONFIRMED":
            new_total = max(curr_total, new_avail + curr_cap.get("occupied", 0))
            curr_cap["available"] = new_avail
            curr_cap["total"] = new_total
            provider.capacity = curr_cap
            provider.last_updated = datetime.utcnow()

            cap_update = ProviderCapacityUpdateDB(
                provider_id=provider.provider_id,
                updates={"delta": delta, "new_available": new_avail, "raw_text": response_text},
                source="sandbox",
                timestamp=datetime.utcnow()
            )
            self.db.add(cap_update)

        msg_id = f"tg-msg-{int(time.time() * 1000)}"
        audit = TelegramMessageAuditDB(
            message_id=msg_id,
            provider_id=provider.provider_id,
            channel="SANDBOX",
            direction="INBOUND",
            chat_id="sandbox_console",
            message_type="telemetry_ingest",
            raw_text=response_text,
            parsed_resource=parsed.resource_type,
            parsed_value=delta,
            processing_status="PROCESSED" if parsed.status != "UNPARSEABLE" else "FLAGGED",
            status="confirmed" if parsed.status == "CONFIRMED" else "processed",
            timestamp=datetime.utcnow()
        )
        self.db.add(audit)
        self.db.commit()

        return ProviderOperationalResponse(
            provider_id=provider.provider_id,
            provider_name=provider.name,
            raw_text=response_text,
            delta_capacity=delta,
            new_available_capacity=new_avail,
            dimension="available",
            resource_type=parsed.resource_type,
            status=parsed.status,
            message_id=msg_id,
            channel="SANDBOX"
        )


# ─────────────────────────────────────────────────────────────────
# WhatsApp Adapter (Legacy / Cloud compatibility)
# ─────────────────────────────────────────────────────────────────

class WhatsAppAdapter(BaseProviderAdapter):
    """Adapter maintaining compatibility with WhatsApp Cloud API."""

    def __init__(self, db: Session):
        self.db = db
        # Delegate to existing MetaCloudAdapter if available
        from app.services.whatsapp_gateway import MetaCloudAdapter
        self._meta = MetaCloudAdapter(db)

    @property
    def adapter_name(self) -> str:
        return "WHATSAPP_CLOUD_ADAPTER"

    @property
    def channel(self) -> str:
        return "WHATSAPP"

    @property
    def is_live(self) -> bool:
        return settings.is_cloud_ready()

    def get_status(self) -> Dict[str, Any]:
        return self._meta.get_gateway_status()

    async def dispatch_capacity_poll(
        self,
        provider_id: str,
        event_id: str,
        required_capacity: int,
        weather_trigger: str,
        zone_id: Optional[str] = None
    ) -> OperationalCapacityRequest:
        req = await self._meta.dispatch_capacity_poll(
            provider_id, event_id, required_capacity, weather_trigger, zone_id
        )
        return OperationalCapacityRequest(
            request_id=req.request_id,
            event_id=req.event_id,
            provider_id=req.provider_id,
            provider_name=req.provider_name,
            zone_id=req.zone_id,
            required_capacity=req.required_capacity,
            weather_trigger=req.weather_trigger,
            message=req.message,
            suggested_replies=req.suggested_replies,
            status=req.status,
            channel="WHATSAPP"
        )

    async def ingest_provider_telemetry(
        self,
        provider_id: str,
        response_text: str,
        event_id: Optional[str] = None
    ) -> ProviderOperationalResponse:
        res = await self._meta.ingest_provider_telemetry(provider_id, response_text, event_id)
        return ProviderOperationalResponse(
            provider_id=res.provider_id,
            provider_name=res.provider_name,
            raw_text=res.raw_text,
            delta_capacity=res.delta_capacity,
            new_available_capacity=res.new_available_capacity,
            dimension=res.dimension,
            resource_type=res.resource_type,
            status=res.status,
            message_id=res.message_id,
            channel="WHATSAPP"
        )


# ─────────────────────────────────────────────────────────────────
# Provider Messaging Gateway (Facade)
# ─────────────────────────────────────────────────────────────────

class ProviderMessagingGateway:
    """
    Unified operational communications gateway.
    Dispatches through the active adapter (Telegram, WhatsApp, or Sandbox).
    Business logic talks ONLY to this gateway.
    """

    def __init__(self, adapter: BaseProviderAdapter):
        self.adapter = adapter

    @property
    def channel(self) -> str:
        return self.adapter.channel

    @property
    def is_live(self) -> bool:
        return self.adapter.is_live

    @property
    def is_sandbox(self) -> bool:
        return not self.adapter.is_live

    def get_status(self) -> Dict[str, Any]:
        return self.adapter.get_status()

    def get_gateway_status(self) -> Dict[str, Any]:
        # Alias for backward compatibility with existing tests
        return self.adapter.get_status()

    async def dispatch_capacity_poll(
        self,
        provider_id: str,
        event_id: str,
        required_capacity: int,
        weather_trigger: str,
        zone_id: Optional[str] = None
    ) -> OperationalCapacityRequest:
        return await self.adapter.dispatch_capacity_poll(
            provider_id, event_id, required_capacity, weather_trigger, zone_id
        )

    async def ingest_provider_telemetry(
        self,
        provider_id: str,
        response_text: str,
        event_id: Optional[str] = None
    ) -> ProviderOperationalResponse:
        return await self.adapter.ingest_provider_telemetry(
            provider_id, response_text, event_id
        )


# ─────────────────────────────────────────────────────────────────
# Factory
# ─────────────────────────────────────────────────────────────────

def get_provider_gateway(db: Session, force_adapter: Optional[str] = None) -> ProviderMessagingGateway:
    """
    Factory creating the active ProviderMessagingGateway.
    Priority:
      1. TelegramAdapter if token is configured or requested
      2. WhatsAppAdapter if Cloud is configured
      3. SandboxAdapter (zero-credential reliable fallback)
    """
    if force_adapter == "telegram" or (force_adapter is None and settings.is_telegram_configured()):
        return ProviderMessagingGateway(TelegramAdapter(db))
    elif force_adapter == "whatsapp" or (force_adapter is None and settings.is_cloud_ready()):
        return ProviderMessagingGateway(WhatsAppAdapter(db))
    return ProviderMessagingGateway(SandboxAdapter(db))

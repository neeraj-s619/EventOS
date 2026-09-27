"""
Deterministic Structured Operational Response Parser for Telegram Provider Pulse.
Translates human and inline responses into standardized capacity/availability telemetry.
"""

from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
import re


@dataclass
class OperationalParseResult:
    """Standardized representation of parsed operational telemetry."""
    raw_text: str
    resource_type: str  # transport_capacity, hotel_rooms, delay, capacity, status, command
    quantity: Optional[int] = None
    minutes: Optional[int] = None
    is_delta: bool = True
    action: str = "add"  # add, set, delay, none, accept, decline, unknown
    status: str = "CONFIRMED"  # CONFIRMED, NO_CAPACITY, DELAYED, ACCEPTED, DECLINED, UNPARSEABLE

    @property
    def delta_change(self) -> Optional[int]:
        return self.quantity if self.is_delta else None

    @property
    def absolute_value(self) -> Optional[int]:
        return self.quantity

    @property
    def resource(self) -> str:
        if "transport" in self.resource_type:
            return "seats"
        elif "hotel" in self.resource_type:
            return "rooms"
        return self.resource_type

    @property
    def delay_minutes(self) -> Optional[int]:
        return self.minutes

    @property
    def is_valid(self) -> bool:
        return self.status != "UNPARSEABLE"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def parse_operational_message(text: str, default_resource: str = "transport_capacity") -> OperationalParseResult:
    """
    Parses a provider's text message or inline callback data deterministically.
    Examples:
      - "+100 seats" -> { resource_type: "transport_capacity", quantity: 100, is_delta: True }
      - "82 rooms available" -> { resource_type: "hotel_rooms", quantity: 82, is_delta: True }
      - "delay 20 minutes" -> { resource_type: "delay", minutes: 20, action: "delay" }
      - "available 50" -> { resource_type: "capacity", quantity: 50, is_delta: False, action: "set" }
      - "NO CAPACITY" -> { resource_type: "capacity", quantity: 0, status: "NO_CAPACITY" }
    """
    if not text or not isinstance(text, str):
        return OperationalParseResult(
            raw_text="",
            resource_type="unknown",
            action="unknown",
            status="UNPARSEABLE"
        )

    raw = text.strip()
    norm = raw.lower()

    # 1. Handle callback data payloads (e.g. cap:+100, status:accept)
    if norm.startswith("cap:"):
        val_str = norm.split(":", 1)[1]
        if val_str in ["0", "none", "no"]:
            return OperationalParseResult(
                raw_text=raw,
                resource_type=default_resource,
                quantity=0,
                is_delta=True,
                action="none",
                status="NO_CAPACITY"
            )
        try:
            qty = int(val_str.replace("+", "").strip())
            return OperationalParseResult(
                raw_text=raw,
                resource_type=default_resource,
                quantity=qty,
                is_delta=True,
                action="add",
                status="CONFIRMED"
            )
        except ValueError:
            pass

    if norm in ["status:accept", "accept", "accepted"]:
        return OperationalParseResult(
            raw_text=raw,
            resource_type="status",
            action="accept",
            status="ACCEPTED"
        )
    if norm in ["state:available", "available"]:
        return OperationalParseResult(
            raw_text=raw,
            resource_type="status",
            action="accept",
            status="AVAILABLE"
        )
    if norm in ["status:decline", "decline", "declined"]:
        return OperationalParseResult(
            raw_text=raw,
            resource_type="status",
            action="decline",
            status="DECLINED"
        )
    if norm in ["state:unavailable", "unavailable"]:
        return OperationalParseResult(
            raw_text=raw,
            resource_type="status",
            action="decline",
            status="UNAVAILABLE"
        )
    if norm in ["status:delayed", "delayed", "delay"]:
        return OperationalParseResult(
            raw_text=raw,
            resource_type="delay",
            action="delay",
            status="DELAYED"
        )

    # 2. Check for Delay responses
    delay_match = re.search(r'delay\s*(\d+)\s*(?:min|minute|m)?', norm)
    if not delay_match:
        delay_match = re.search(r'(\d+)\s*(?:min|minute)s?\s*delay', norm)
    if delay_match:
        mins = int(delay_match.group(1))
        return OperationalParseResult(
            raw_text=raw,
            resource_type="delay",
            minutes=mins,
            is_delta=False,
            action="delay",
            status="DELAYED"
        )

    # 3. Check for No Capacity / Full / None
    if re.search(r'\b(no\s+capacity|zero|unavailable|none|full|0\s*seats|0\s*rooms)\b', norm) or norm in ["0", "no", "decline"]:
        return OperationalParseResult(
            raw_text=raw,
            resource_type=default_resource,
            quantity=0,
            is_delta=True,
            action="none",
            status="NO_CAPACITY"
        )

    # 4. Check for Acceptance / Decline
    if norm in ["accept", "accepted", "agree", "confirm", "yes", "ok", "standby"]:
        return OperationalParseResult(
            raw_text=raw,
            resource_type="status",
            action="accept",
            status="ACCEPTED"
        )
    if norm in ["decline", "declined", "reject", "cancel"]:
        return OperationalParseResult(
            raw_text=raw,
            resource_type="status",
            action="decline",
            status="DECLINED"
        )

    # 5. Check for "available <number>" or "capacity <number>" (absolute count)
    avail_match = re.search(r'(?:available|capacity|standby)\s*(\d+)', norm)
    if avail_match:
        qty = int(avail_match.group(1))
        res_type = "hotel_rooms" if "room" in norm else (
            "transport_capacity" if "seat" in norm or "bus" in norm else default_resource
        )
        return OperationalParseResult(
            raw_text=raw,
            resource_type=res_type,
            quantity=qty,
            is_delta=False,
            action="set",
            status="CONFIRMED"
        )

    # 6. Check for hotel rooms (e.g. "82 rooms available", "+50 rooms", "82 rooms")
    room_match = re.search(r'(\+?\d+)\s*(?:room|bed|hotel|keys)s?', norm)
    if room_match:
        val_str = room_match.group(1)
        qty = int(val_str.replace("+", "").strip())
        return OperationalParseResult(
            raw_text=raw,
            resource_type="hotel_rooms",
            quantity=qty,
            is_delta=True,
            action="add",
            status="CONFIRMED"
        )

    # 7. Check for transport capacity / seats (e.g. "+100 seats", "100 seats", "+50 buses")
    seat_match = re.search(r'(\+?\d+)\s*(?:seat|bus|shuttle|vehicle|transit|pax)s?', norm)
    if seat_match:
        val_str = seat_match.group(1)
        qty = int(val_str.replace("+", "").strip())
        return OperationalParseResult(
            raw_text=raw,
            resource_type="transport_capacity",
            quantity=qty,
            is_delta=True,
            action="add",
            status="CONFIRMED"
        )

    # 8. Check for explicit delta with plus sign (e.g. "+100", "+ 50")
    delta_match = re.search(r'^\s*\+\s*(\d+)', norm)
    if delta_match:
        qty = int(delta_match.group(1))
        return OperationalParseResult(
            raw_text=raw,
            resource_type=default_resource,
            quantity=qty,
            is_delta=True,
            action="add",
            status="CONFIRMED"
        )

    # 9. Plain standalone number (e.g. "100")
    plain_num = re.search(r'^\s*(\d+)\s*$', norm)
    if plain_num:
        qty = int(plain_num.group(1))
        return OperationalParseResult(
            raw_text=raw,
            resource_type=default_resource,
            quantity=qty,
            is_delta=True,
            action="add",
            status="CONFIRMED"
        )

    # 10. Could not extract structured operational data
    return OperationalParseResult(
        raw_text=raw,
        resource_type="unknown",
        action="unknown",
        status="UNPARSEABLE"
    )


# Alias for backward compatibility
parse_operational_response = parse_operational_message


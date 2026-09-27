from sqlalchemy import Column, String, Integer, Float, DateTime, Enum as SQLEnum, ForeignKey, Text, JSON, Boolean
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
from typing import Dict, Any, List, Optional
import uuid
import enum

Base = declarative_base()


class EventStatusEnum(str, enum.Enum):
    PLANNING = "planning"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ZoneTypeEnum(str, enum.Enum):
    VENUE = "venue"
    HOSPITALITY = "hospitality"
    TRANSPORT = "transport"
    PEDESTRIAN = "pedestrian"
    PARKING = "parking"
    MIXED = "mixed"


class RiskLevelEnum(str, enum.Enum):
    NORMAL = "normal"
    WATCH = "watch"
    WARNING = "warning"
    CRITICAL = "critical"
    OVERLOAD = "overload"


class ProviderTypeEnum(str, enum.Enum):
    HOTEL = "hotel"
    TRANSPORT = "transport"
    VENUE = "venue"
    RESTAURANT = "restaurant"
    PARKING = "parking"
    MEDICAL = "medical"
    OTHER = "other"


class ProviderStatusEnum(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    FULL = "full"


class CapacityDimensionEnum(str, enum.Enum):
    TOTAL = "total"
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    OPERATIONAL = "operational"


def gen_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


class VenueDB(Base):
    __tablename__ = "venues"

    venue_id = Column(String(32), primary_key=True, default=lambda: gen_id("VENUE"))
    name = Column(String(255), nullable=False)
    venue_type = Column(String(100), default="Cricket Stadium")
    address = Column(String(255), nullable=False)
    locality = Column(String(100), nullable=False)
    city = Column(String(50), default="Mumbai")
    state = Column(String(50), default="Maharashtra")
    country = Column(String(50), default="India")
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    official_capacity = Column(Integer, nullable=False, default=0)
    capacity_basis = Column(String(255), nullable=True)
    source_name = Column(String(150), nullable=True)
    source_url = Column(String(255), nullable=True)
    source_type = Column(String(50), default="VERIFIED_PUBLIC")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    events_rel = relationship("EventDB", back_populates="venue_rel")
    zones_rel = relationship("ZoneDB", back_populates="venue_rel")


class EventDB(Base):
    __tablename__ = "events"

    event_id = Column(String(32), primary_key=True, default=lambda: gen_id("EVT"))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    expected_visitors = Column(Integer, nullable=False)
    status = Column(SQLEnum(EventStatusEnum), default=EventStatusEnum.PLANNING)
    operational_thresholds = Column(JSON, default=dict)
    zones = Column(JSON, default=list)
    venues = Column(JSON, default=list)
    schedule = Column(JSON, default=list)
    city = Column(String(50), default="Mumbai", nullable=True)
    state = Column(String(50), default="Maharashtra", nullable=True)
    country = Column(String(50), default="India", nullable=True)
    venue_id = Column(String(32), ForeignKey("venues.venue_id"), nullable=True)
    event_type = Column(String(100), default="Cricket Match", nullable=True)
    source_type = Column(String(50), default="VERIFIED_PUBLIC", nullable=True)
    source_url = Column(String(255), nullable=True)
    data_status = Column(String(50), default="HYBRID", nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    venue_rel = relationship("VenueDB", back_populates="events_rel")
    zones_rel = relationship("ZoneDB", back_populates="event", cascade="all, delete-orphan")
    providers_rel = relationship("ProviderDB", back_populates="event", cascade="all, delete-orphan")


class ZoneDB(Base):
    __tablename__ = "zones"

    zone_id = Column(String(32), primary_key=True, default=lambda: gen_id("ZONE"))
    event_id = Column(String(32), ForeignKey("events.event_id"), nullable=False)
    venue_id = Column(String(32), ForeignKey("venues.venue_id"), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    zone_type = Column(SQLEnum(ZoneTypeEnum), default=ZoneTypeEnum.MIXED)
    boundary = Column(JSON, nullable=True)
    capacity = Column(Integer, default=0)
    operational_capacity = Column(Integer, nullable=True)
    current_crowd = Column(Integer, default=0)
    inflow_per_minute = Column(Float, default=0.0)
    outflow_per_minute = Column(Float, default=0.0)
    density = Column(Float, default=0.0)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    source_type = Column(String(50), default="VERIFIED_PUBLIC", nullable=True)
    providers = Column(JSON, default=list)
    venues = Column(JSON, default=list)
    cameras = Column(JSON, default=list)
    transport_nodes = Column(JSON, default=list)
    expected_demand = Column(Integer, default=0)
    risk_level = Column(SQLEnum(RiskLevelEnum), default=RiskLevelEnum.NORMAL)
    time_to_threshold = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    venue_rel = relationship("VenueDB", back_populates="zones_rel")
    event = relationship("EventDB", back_populates="zones_rel")
    crowd_states = relationship("ZoneCrowdStateDB", back_populates="zone", cascade="all, delete-orphan")
    providers_rel = relationship("ProviderDB", back_populates="zone")

    @property
    def utilization(self) -> float:
        if self.capacity == 0:
            return 0.0
        return (self.current_crowd / self.capacity) * 100

    @property
    def net_flow(self) -> float:
        return self.inflow_per_minute - self.outflow_per_minute


class ZoneCrowdStateDB(Base):
    __tablename__ = "zone_crowd_states"

    id = Column(Integer, primary_key=True, autoincrement=True)
    zone_id = Column(String(32), ForeignKey("zones.zone_id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    people_count = Column(Integer, nullable=False)
    inflow_per_minute = Column(Float, nullable=False)
    outflow_per_minute = Column(Float, nullable=False)
    density = Column(Float, nullable=False)
    movement_direction = Column(String(50), nullable=True)
    movement_speed = Column(Float, nullable=True)
    source = Column(String(50), default="simulated")

    zone = relationship("ZoneDB", back_populates="crowd_states")


class ProviderDB(Base):
    __tablename__ = "providers"

    provider_id = Column(String(32), primary_key=True, default=lambda: gen_id("PROV"))
    event_id = Column(String(32), ForeignKey("events.event_id"), nullable=False)
    zone_id = Column(String(32), ForeignKey("zones.zone_id"), nullable=False)
    type = Column(SQLEnum(ProviderTypeEnum), nullable=False)
    name = Column(String(255), nullable=False)
    capacity = Column(JSON, default=dict)
    status = Column(SQLEnum(ProviderStatusEnum), default=ProviderStatusEnum.ACTIVE)
    contact_info = Column(JSON, nullable=True)
    provider_metadata = Column(JSON, default=dict)
    source_type = Column(String(50), default="SIMULATED", nullable=True)
    source_name = Column(String(100), nullable=True)
    location = Column(String(255), nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    event = relationship("EventDB", back_populates="providers_rel")
    zone = relationship("ZoneDB", back_populates="providers_rel")
    capacity_updates = relationship("ProviderCapacityUpdateDB", back_populates="provider", cascade="all, delete-orphan")

    @property
    def total_capacity(self) -> int:
        if not self.capacity or not isinstance(self.capacity, dict):
            return 0
        return self.capacity.get("total", 0)

    @property
    def available_capacity(self) -> int:
        if not self.capacity or not isinstance(self.capacity, dict):
            return 0
        return self.capacity.get("available", 0)

    @property
    def occupied_capacity(self) -> int:
        if not self.capacity or not isinstance(self.capacity, dict):
            return 0
        if "occupied" in self.capacity:
            return self.capacity["occupied"]
        total = self.total_capacity
        available = self.available_capacity
        if total > 0 and available is not None:
            return max(0, total - available)
        return 0

    @property
    def utilization(self) -> float:
        total = self.total_capacity
        if total <= 0:
            return 0.0
        return (self.occupied_capacity / total) * 100.0


class ProviderCapacityUpdateDB(Base):
    __tablename__ = "provider_capacity_updates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider_id = Column(String(32), ForeignKey("providers.provider_id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    updates = Column(JSON, nullable=False)
    source = Column(String(50), default="whatsapp")

    provider = relationship("ProviderDB", back_populates="capacity_updates")


class UnifiedEventStateDB(Base):
    __tablename__ = "unified_event_states"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(32), ForeignKey("events.event_id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    state = Column(JSON, nullable=False)

    event = relationship("EventDB")


class ForecastDB(Base):
    __tablename__ = "forecasts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(32), ForeignKey("events.event_id"), nullable=False)
    zone_id = Column(String(32), ForeignKey("zones.zone_id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    horizon_minutes = Column(Integer, nullable=False)
    predicted_crowd = Column(Integer, nullable=False)
    predicted_inflow = Column(Float, nullable=False)
    predicted_outflow = Column(Float, nullable=False)
    predicted_utilization = Column(Float, nullable=False)
    confidence = Column(Float, default=1.0)

    event = relationship("EventDB")
    zone = relationship("ZoneDB")


class RiskAssessmentDB(Base):
    __tablename__ = "risk_assessments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(32), ForeignKey("events.event_id"), nullable=False)
    zone_id = Column(String(32), ForeignKey("zones.zone_id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    current_risk = Column(SQLEnum(RiskLevelEnum), nullable=False)
    predicted_risk = Column(SQLEnum(RiskLevelEnum), nullable=False)
    current_utilization = Column(Float, nullable=False)
    predicted_utilization = Column(Float, nullable=False)
    time_to_threshold = Column(Float, nullable=True)
    factors = Column(JSON, default=dict)

    event = relationship("EventDB")
    zone = relationship("ZoneDB")


class OrchestrationRecommendationDB(Base):
    __tablename__ = "orchestration_recommendations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(32), ForeignKey("events.event_id"), nullable=False)
    zone_id = Column(String(32), ForeignKey("zones.zone_id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    trigger_risk_id = Column(Integer, ForeignKey("risk_assessments.id"), nullable=True)
    recommendation_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    actions = Column(JSON, nullable=False)
    target_zone_id = Column(String(32), nullable=True)
    required_providers = Column(JSON, default=list)
    status = Column(String(50), default="pending")
    approved_by = Column(String(255), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    executed_at = Column(DateTime, nullable=True)

    event = relationship("EventDB")
    zone = relationship("ZoneDB")
    trigger_risk = relationship("RiskAssessmentDB")


class ActionExecutionDB(Base):
    __tablename__ = "action_executions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    recommendation_id = Column(Integer, ForeignKey("orchestration_recommendations.id"), nullable=False)
    provider_id = Column(String(32), ForeignKey("providers.provider_id"), nullable=True)
    action_type = Column(String(100), nullable=False)
    parameters = Column(JSON, default=dict)
    status = Column(String(50), default="pending")
    response = Column(JSON, nullable=True)
    requested_at = Column(DateTime, default=datetime.utcnow)
    responded_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    recommendation = relationship("OrchestrationRecommendationDB")
    provider = relationship("ProviderDB")


class FeedbackLoopDB(Base):
    __tablename__ = "feedback_loops"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(32), ForeignKey("events.event_id"), nullable=False)
    zone_id = Column(String(32), ForeignKey("zones.zone_id"), nullable=False)
    recommendation_id = Column(Integer, ForeignKey("orchestration_recommendations.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    pre_action_state = Column(JSON, nullable=False)
    post_action_state = Column(JSON, nullable=True)
    effectiveness_score = Column(Float, nullable=True)
    risk_change = Column(Float, nullable=True)
    stabilized: bool = Column(Boolean, default=False)

    event = relationship("EventDB")
    zone = relationship("ZoneDB")
    recommendation = relationship("OrchestrationRecommendationDB")


class WhatsAppMessageAuditDB(Base):
    __tablename__ = "whatsapp_message_audits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(String(100), unique=True, index=True, nullable=False)
    provider_id = Column(String(32), ForeignKey("providers.provider_id"), nullable=True)
    direction = Column(String(20), nullable=False)  # INBOUND, OUTBOUND
    from_number_masked = Column(String(64), nullable=True)
    to_number_masked = Column(String(64), nullable=True)
    message_type = Column(String(30), default="text")
    raw_text = Column(Text, nullable=True)
    parsed_resource = Column(String(50), nullable=True)  # rooms, seats, capacity, percentage
    parsed_value = Column(Integer, nullable=True)
    processing_status = Column(String(50), nullable=False)  # PROCESSED, PENDING_CONFIRMATION, DUPLICATE, UNKNOWN_PROVIDER, UNPARSEABLE, IGNORED_EVENT, SENT, FAILED
    confirmation_state = Column(String(50), nullable=True)  # AWAITING_CONFIRMATION, CONFIRMED, AUTO_CONFIRMED, REJECTED
    delivery_status = Column(String(30), nullable=True)  # sent, delivered, read, failed
    error_reason = Column(Text, nullable=True)
    source = Column(String(50), default="META_WHATSAPP_CLOUD_API")
    raw_payload = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    provider = relationship("ProviderDB")


class TelegramMessageAuditDB(Base):
    __tablename__ = "telegram_message_audits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(String(100), unique=True, index=True, nullable=False)
    provider_id = Column(String(32), ForeignKey("providers.provider_id"), nullable=True)
    channel = Column(String(30), default="TELEGRAM")
    direction = Column(String(20), nullable=False)  # INBOUND, OUTBOUND
    chat_id = Column(String(64), nullable=True)
    telegram_user_id = Column(String(64), nullable=True)
    telegram_username = Column(String(64), nullable=True)
    telegram_message_id = Column(String(64), nullable=True)
    message_type = Column(String(50), default="text")  # command, operational_poll, operational_response, callback_query
    raw_text = Column(Text, nullable=True)
    parsed_resource = Column(String(50), nullable=True)  # transport_capacity, hotel_rooms, delay, general_capacity
    parsed_value = Column(Integer, nullable=True)
    processing_status = Column(String(50), nullable=False, default="PROCESSED")  # PROCESSED, UNKNOWN_PROVIDER, UNPARSEABLE, FAILED, DISPATCHED
    status = Column(String(50), default="sent")  # sent, delivered, confirmed, pending
    raw_payload = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    provider = relationship("ProviderDB")


class TelegramProviderMappingDB(Base):
    """Mapping between a Telegram Chat / User ID and an internal EVENTOS Provider."""
    __tablename__ = "telegram_provider_mappings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider_id = Column(String(32), ForeignKey("providers.provider_id"), nullable=False)
    chat_id = Column(String(64), unique=True, index=True, nullable=False)
    user_id = Column(String(64), nullable=True)
    username = Column(String(64), nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    verified_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    provider = relationship("ProviderDB")


class WeatherObservationDB(Base):
    """Cached weather observations from Open-Meteo for Wankhede Stadium."""
    __tablename__ = "weather_observations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    observed_at = Column(DateTime, nullable=False)
    fetched_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    # Core measurements
    temperature_c = Column(Float, nullable=True)
    feels_like_c = Column(Float, nullable=True)
    humidity_pct = Column(Float, nullable=True)
    precipitation_mm_h = Column(Float, default=0.0)
    wind_speed_kmh = Column(Float, nullable=True)
    wind_direction_deg = Column(Float, nullable=True)
    visibility_m = Column(Float, nullable=True)
    weather_code = Column(Integer, nullable=True)
    # Derived / classified
    rain_intensity = Column(String(20), default="none")
    weather_description = Column(String(100), nullable=True)
    is_raining = Column(Boolean, default=False)
    is_thunderstorm = Column(Boolean, default=False)
    is_extreme = Column(Boolean, default=False)
    # Source
    source = Column(String(50), default="OPEN_METEO_LIVE")
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)
    confidence = Column(Float, default=1.0)
    is_fallback = Column(Boolean, default=False)
    # Raw payload
    raw_payload = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class VisitorRegistrationDB(Base):
    """Event visitor registration via Visitor Telegram Bot."""
    __tablename__ = "visitor_registrations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    visitor_id = Column(String(32), unique=True, index=True, nullable=False)
    chat_id = Column(String(64), index=True, nullable=False)
    telegram_user_id = Column(String(64), nullable=True)
    telegram_username = Column(String(64), nullable=True)
    name = Column(String(100), nullable=False)
    num_people = Column(Integer, default=1)
    checkin_date = Column(String(50), nullable=True)
    checkout_date = Column(String(50), nullable=True)
    accommodation_requirement = Column(String(50), default="HOTEL")
    registration_state = Column(String(50), default="COMPLETE")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AccommodationRequestDB(Base):
    """Accommodation booking request created by visitor, fulfilled by hotel provider via Staff Bot."""
    __tablename__ = "accommodation_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(String(32), unique=True, index=True, nullable=False)  # e.g. EVT-HOTEL-1024
    visitor_id = Column(String(32), ForeignKey("visitor_registrations.visitor_id"), nullable=True)
    event_id = Column(String(32), ForeignKey("events.event_id"), nullable=True)
    provider_id = Column(String(32), ForeignKey("providers.provider_id"), nullable=True)
    visitor_chat_id = Column(String(64), nullable=False)
    hotel_chat_id = Column(String(64), nullable=True)
    guest_name = Column(String(100), nullable=True)
    num_rooms = Column(Integer, default=1)
    num_guests = Column(Integer, default=1)
    checkin_date = Column(String(50), default="Today")
    checkout_date = Column(String(50), default="Tomorrow")
    status = Column(String(50), default="SEARCHING")  # SEARCHING, OFFERED, CONFIRMED, DECLINED, CANCELLED
    hotel_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    provider = relationship("ProviderDB")
    visitor = relationship("VisitorRegistrationDB")


class TelegramStaffRegistrationDB(Base):
    """Staff, volunteers, gate marshals, transport & hospitality operators registered on Staff Bot."""
    __tablename__ = "telegram_staff_registrations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    staff_id = Column(String(32), unique=True, index=True, nullable=False)  # e.g. STF-XXXXXX
    chat_id = Column(String(64), unique=True, index=True, nullable=False)
    telegram_user_id = Column(String(64), nullable=True)
    telegram_username = Column(String(64), nullable=True)
    name = Column(String(100), nullable=True)
    role = Column(String(50), nullable=False)  # VOLUNTEER, GATE_STAFF, TRANSPORT, HOSPITALITY, VENUE_OPERATIONS, SUPERVISOR
    assigned_zone_id = Column(String(32), nullable=True)  # ZONE-XXXX or ALL
    provider_id = Column(String(32), ForeignKey("providers.provider_id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    provider = relationship("ProviderDB")


class OperationalAlertDB(Base):
    """Operational alerts dispatched to staff with acknowledgment and diversion tracking."""
    __tablename__ = "operational_alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_id = Column(String(32), unique=True, index=True, nullable=False)  # e.g. ALT-XXXXXX
    event_id = Column(String(32), ForeignKey("events.event_id"), nullable=True)
    zone_id = Column(String(32), ForeignKey("zones.zone_id"), nullable=True)
    severity = Column(String(30), default="WARNING")  # INFO, WATCH, WARNING, CRITICAL
    alert_type = Column(String(50), nullable=False)  # CROWD_PRESSURE, DIVERSION_REQUIRED, TRANSPORT_SHORTAGE, HOTEL_DEMAND
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    recommended_action = Column(Text, nullable=True)
    target_role = Column(String(50), nullable=True)  # VOLUNTEER, GATE_STAFF, TRANSPORT, HOSPITALITY, ALL
    target_zone_id = Column(String(32), nullable=True)
    status = Column(String(50), default="APPROVED")  # PENDING_APPROVAL, APPROVED, DISPATCHED, ACKNOWLEDGED, IN_PROGRESS, RESOLVED, ESCALATED
    acknowledged_by = Column(String(100), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    action_started_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    event = relationship("EventDB")
    zone = relationship("ZoneDB")
from pydantic import BaseModel, Field, model_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class EventStatus(str, Enum):
    PLANNING = "planning"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ZoneType(str, Enum):
    VENUE = "venue"
    HOSPITALITY = "hospitality"
    TRANSPORT = "transport"
    PEDESTRIAN = "pedestrian"
    PARKING = "parking"
    MIXED = "mixed"


class RiskLevel(str, Enum):
    NORMAL = "normal"
    WATCH = "watch"
    WARNING = "warning"
    CRITICAL = "critical"
    OVERLOAD = "overload"


class ProviderType(str, Enum):
    HOTEL = "hotel"
    TRANSPORT = "transport"
    VENUE = "venue"
    RESTAURANT = "restaurant"
    PARKING = "parking"
    MEDICAL = "medical"
    OTHER = "other"


class ProviderStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    FULL = "full"


class CapacityDimension(str, Enum):
    TOTAL = "total"
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    OPERATIONAL = "operational"


class VenueCreate(BaseModel):
    name: str
    venue_type: str = "Cricket Stadium"
    address: str
    locality: str
    city: str = "Mumbai"
    state: str = "Maharashtra"
    country: str = "India"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    official_capacity: int = 0
    capacity_basis: Optional[str] = None
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    source_type: str = "VERIFIED_PUBLIC"


class VenueResponse(BaseModel):
    venue_id: str
    name: str
    venue_type: str
    address: str
    locality: str
    city: str
    state: str
    country: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    official_capacity: int
    capacity_basis: Optional[str] = None
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    source_type: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EventCreate(BaseModel):
    name: str
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime
    expected_visitors: int
    operational_thresholds: Dict[str, float] = Field(default_factory=dict)
    schedule: List[Dict[str, Any]] = Field(default_factory=list)
    city: Optional[str] = "Mumbai"
    state: Optional[str] = "Maharashtra"
    country: Optional[str] = "India"
    venue_id: Optional[str] = None
    event_type: Optional[str] = "Cricket Match"
    source_type: Optional[str] = "VERIFIED_PUBLIC"
    source_url: Optional[str] = None
    data_status: Optional[str] = "HYBRID"


class EventUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    expected_visitors: Optional[int] = None
    status: Optional[EventStatus] = None
    operational_thresholds: Optional[Dict[str, float]] = None
    schedule: Optional[List[Dict[str, Any]]] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    venue_id: Optional[str] = None
    event_type: Optional[str] = None
    source_type: Optional[str] = None
    source_url: Optional[str] = None
    data_status: Optional[str] = None


class EventResponse(BaseModel):
    event_id: str
    name: str
    description: Optional[str]
    start_date: datetime
    end_date: datetime
    expected_visitors: int
    status: EventStatus
    operational_thresholds: Optional[Dict[str, float]] = None
    zones: Optional[List[str]] = None
    venues: Optional[List[str]] = None
    schedule: Optional[List[Dict[str, Any]]] = None
    city: Optional[str] = "Mumbai"
    state: Optional[str] = "Maharashtra"
    country: Optional[str] = "India"
    venue_id: Optional[str] = None
    event_type: Optional[str] = None
    source_type: Optional[str] = "VERIFIED_PUBLIC"
    source_url: Optional[str] = None
    data_status: Optional[str] = "HYBRID"
    venue: Optional[VenueResponse] = None
    created_at: datetime
    updated_at: datetime

    @model_validator(mode='after')
    def set_defaults(self):
        if self.operational_thresholds is None:
            self.operational_thresholds = {}
        if self.zones is None:
            self.zones = []
        if self.venues is None:
            self.venues = []
        if self.schedule is None:
            self.schedule = []
        return self

    class Config:
        from_attributes = True


class ZoneCreate(BaseModel):
    name: str
    zone_type: ZoneType = ZoneType.MIXED
    boundary: Optional[Dict[str, Any]] = None
    capacity: int = 0
    operational_capacity: Optional[int] = None
    expected_demand: int = 0
    venue_id: Optional[str] = None
    description: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    source_type: Optional[str] = "VERIFIED_PUBLIC"


class ZoneUpdate(BaseModel):
    name: Optional[str] = None
    zone_type: Optional[ZoneType] = None
    boundary: Optional[Dict[str, Any]] = None
    capacity: Optional[int] = None
    operational_capacity: Optional[int] = None
    current_crowd: Optional[int] = None
    inflow_per_minute: Optional[float] = None
    outflow_per_minute: Optional[float] = None
    density: Optional[float] = None
    expected_demand: Optional[int] = None
    risk_level: Optional[RiskLevel] = None
    time_to_threshold: Optional[float] = None
    venue_id: Optional[str] = None
    description: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    source_type: Optional[str] = None


class ZoneResponse(BaseModel):
    zone_id: str
    event_id: str
    venue_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    zone_type: ZoneType
    boundary: Optional[Dict[str, Any]]
    capacity: int
    operational_capacity: Optional[int] = None
    current_crowd: int
    inflow_per_minute: float
    outflow_per_minute: float
    density: float
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    source_type: Optional[str] = "VERIFIED_PUBLIC"
    providers: List[str]
    venues: List[str]
    cameras: List[str]
    transport_nodes: List[str]
    expected_demand: int
    risk_level: RiskLevel
    time_to_threshold: Optional[float]
    created_at: datetime
    updated_at: datetime
    utilization: float
    net_flow: float

    class Config:
        from_attributes = True


class ZoneCrowdStateCreate(BaseModel):
    people_count: int
    inflow_per_minute: float
    outflow_per_minute: float
    density: float
    movement_direction: Optional[str] = None
    movement_speed: Optional[float] = None
    source: str = "simulated"


class ZoneCrowdStateResponse(BaseModel):
    id: int
    zone_id: str
    timestamp: datetime
    people_count: int
    inflow_per_minute: float
    outflow_per_minute: float
    density: float
    movement_direction: Optional[str]
    movement_speed: Optional[float]
    source: str

    class Config:
        from_attributes = True


class ProviderCreate(BaseModel):
    zone_id: str
    type: ProviderType
    name: str
    capacity: Dict[CapacityDimension, int] = {}
    contact_info: Optional[Dict[str, str]] = None
    metadata: Optional[Dict[str, Any]] = None


class ProviderUpdate(BaseModel):
    name: Optional[str] = None
    capacity: Optional[Dict[CapacityDimension, int]] = None
    status: Optional[ProviderStatus] = None
    contact_info: Optional[Dict[str, str]] = None
    metadata: Optional[Dict[str, Any]] = None


class ProviderResponse(BaseModel):
    provider_id: str
    event_id: str
    zone_id: str
    type: ProviderType
    name: str
    capacity: Dict[CapacityDimension, int]
    status: ProviderStatus
    contact_info: Optional[Dict[str, str]]
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    source_type: Optional[str] = "SIMULATED"
    source_name: Optional[str] = None
    location: Optional[str] = None
    last_updated: datetime
    created_at: datetime
    total_capacity: int
    available_capacity: int
    occupied_capacity: int
    utilization: float

    class Config:
        from_attributes = True

    @model_validator(mode='before')
    @classmethod
    def extract_from_orm(cls, data: Any) -> Any:
        if hasattr(data, 'provider_metadata'):
            return {
                "provider_id": data.provider_id,
                "event_id": data.event_id,
                "zone_id": data.zone_id,
                "type": data.type,
                "name": data.name,
                "capacity": data.capacity or {},
                "status": data.status,
                "contact_info": data.contact_info,
                "metadata": data.provider_metadata if isinstance(data.provider_metadata, dict) else {},
                "source_type": getattr(data, "source_type", "SIMULATED") or "SIMULATED",
                "source_name": getattr(data, "source_name", None),
                "location": getattr(data, "location", None),
                "last_updated": data.last_updated,
                "created_at": data.created_at,
                "total_capacity": data.total_capacity,
                "available_capacity": data.available_capacity,
                "occupied_capacity": data.occupied_capacity,
                "utilization": data.utilization
            }
        return data


class ProviderCapacityUpdateRequest(BaseModel):
    provider_id: str
    updates: Dict[CapacityDimension, int]
    source: str = "whatsapp"


class UnifiedEventStateResponse(BaseModel):
    event_id: str
    timestamp: datetime
    zones: Dict[str, Dict[str, Any]]

    class Config:
        from_attributes = True


class SignalStatus(BaseModel):
    status: str
    mode: str
    description: str
    source: str
    last_updated: Optional[str] = None


class WhatsAppSendRequest(BaseModel):
    provider_id: str
    message: str


class WeatherStateSchema(BaseModel):
    """Normalized current weather for Wankhede Stadium."""
    temperature_c: float
    feels_like_c: float
    humidity_pct: float
    precipitation_mm_h: float
    wind_speed_kmh: float
    wind_direction_deg: float
    visibility_m: float
    weather_code: int
    rain_intensity: str
    weather_description: str
    is_raining: bool
    is_thunderstorm: bool
    is_extreme: bool
    hourly_precip_probability: List[float] = Field(default_factory=list)
    hourly_precip_mm: List[float] = Field(default_factory=list)
    source: str
    lat: float
    lon: float
    observed_at: str
    fetched_at: str
    data_age_seconds: float
    confidence: float
    is_fallback: bool


class WeatherImpactSchema(BaseModel):
    """Computed weather impact on event state."""
    precipitation_mm_h: float
    temperature_c: float
    humidity_pct: float
    wind_speed_kmh: float
    rain_intensity: str
    outdoor_movement_factor: float
    shelter_demand_delta: float
    transport_demand_multiplier: float
    wind_risk: float
    heat_stress: float
    visibility_risk: float
    outdoor_zone_crowd_adjustment_pct: float
    indoor_zone_crowd_adjustment_pct: float
    transport_zone_crowd_adjustment_pct: float
    overall_risk_uplift: float
    confidence: float
    uncertainty_pct: float
    summary: str
    recommendations: List[str] = Field(default_factory=list)


class DigitalTwinSimulateRequest(BaseModel):
    """Request body for POST /events/{id}/digital-twin/simulate"""
    scenario_name: str = "normal"
    precipitation_mm_h: Optional[float] = None
    temperature_c: Optional[float] = None
    humidity_pct: Optional[float] = None
    wind_speed_kmh: Optional[float] = None
    visibility_m: Optional[float] = None


class DashboardMasterResponse(BaseModel):
    event: EventResponse
    venue: Optional[VenueResponse] = None
    data_mode: str = "HYBRID"
    zones: List[Dict[str, Any]]
    providers: List[Dict[str, Any]]
    signals: Dict[str, SignalStatus]
    kpis: Dict[str, Any]
    forecasts: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    timeline: List[Dict[str, Any]]
    whatsapp_integration: Optional[Dict[str, Any]] = None
    provider_pulse: Optional[Dict[str, Any]] = None
    weather: Optional[Dict[str, Any]] = None          # Live weather state
    digital_twin: Optional[Dict[str, Any]] = None     # Live-weather digital twin state
    public_signals: Optional[Dict[str, Any]] = None   # GDELT public signal summary
    timestamp: datetime = Field(default_factory=datetime.utcnow)
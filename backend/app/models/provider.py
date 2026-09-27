from enum import Enum
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import uuid


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


class Provider(BaseModel):
    provider_id: str = Field(default_factory=lambda: f"PROV-{uuid.uuid4().hex[:8].upper()}")
    event_id: str
    zone_id: str
    type: ProviderType
    name: str
    capacity: Dict[CapacityDimension, int] = Field(default_factory=dict)
    status: ProviderStatus = ProviderStatus.ACTIVE
    contact_info: Optional[Dict[str, str]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def total_capacity(self) -> int:
        return self.capacity.get(CapacityDimension.TOTAL, 0)

    @property
    def available_capacity(self) -> int:
        return self.capacity.get(CapacityDimension.AVAILABLE, 0)

    @property
    def occupied_capacity(self) -> int:
        return self.capacity.get(CapacityDimension.OCCUPIED, 0)

    @property
    def utilization(self) -> float:
        total = self.total_capacity
        if total == 0:
            return 0.0
        occupied = self.occupied_capacity
        return (occupied / total) * 100

    def update_capacity(self, dimension: CapacityDimension, value: int):
        self.capacity[dimension] = value
        self.last_updated = datetime.utcnow()

    class Config:
        from_attributes = True
        use_enum_values = True


class HotelProvider(Provider):
    type: ProviderType = ProviderType.HOTEL
    rooms_total: int = 0
    rooms_available: int = 0
    rooms_occupied: int = 0

    @property
    def total_capacity(self) -> int:
        return self.rooms_total

    @property
    def available_capacity(self) -> int:
        return self.rooms_available

    @property
    def occupied_capacity(self) -> int:
        return self.rooms_occupied


class TransportProvider(Provider):
    type: ProviderType = ProviderType.TRANSPORT
    route_id: Optional[str] = None
    vehicle_capacity: int = 0
    vehicles_available: int = 0
    current_passengers: int = 0

    @property
    def total_capacity(self) -> int:
        return self.vehicle_capacity * max(self.vehicles_available, 1)

    @property
    def available_capacity(self) -> int:
        return self.total_capacity - self.current_passengers


class VenueProvider(Provider):
    type: ProviderType = ProviderType.VENUE
    max_occupancy: int = 0
    current_occupancy: int = 0

    @property
    def total_capacity(self) -> int:
        return self.max_occupancy

    @property
    def available_capacity(self) -> int:
        return self.max_occupancy - self.current_occupancy

    @property
    def occupied_capacity(self) -> int:
        return self.current_occupancy


class ProviderCapacityUpdate(BaseModel):
    provider_id: str
    updates: Dict[CapacityDimension, int]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str = "whatsapp"


class ZoneCapacitySnapshot(BaseModel):
    zone_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    total_capacity: int
    available_capacity: int
    provider_breakdown: Dict[ProviderType, Dict[str, int]]
    transport_capacity: int
    venue_capacity: int
    accommodation_capacity: int

    class Config:
        from_attributes = True
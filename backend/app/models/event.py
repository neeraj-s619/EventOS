from enum import Enum
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import uuid


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


class Event(BaseModel):
    event_id: str = Field(default_factory=lambda: f"EVT-{uuid.uuid4().hex[:8].upper()}")
    name: str
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime
    expected_visitors: int
    status: EventStatus = EventStatus.PLANNING
    operational_thresholds: Dict[str, float] = Field(default_factory=dict)
    zones: List[str] = Field(default_factory=list)
    venues: List[str] = Field(default_factory=list)
    schedule: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class Zone(BaseModel):
    zone_id: str = Field(default_factory=lambda: f"ZONE-{uuid.uuid4().hex[:8].upper()}")
    event_id: str
    name: str
    zone_type: ZoneType = ZoneType.MIXED
    boundary: Optional[Dict[str, Any]] = None
    capacity: int = 0
    current_crowd: int = 0
    inflow_per_minute: float = 0.0
    outflow_per_minute: float = 0.0
    density: float = 0.0
    providers: List[str] = Field(default_factory=list)
    venues: List[str] = Field(default_factory=list)
    cameras: List[str] = Field(default_factory=list)
    transport_nodes: List[str] = Field(default_factory=list)
    expected_demand: int = 0
    risk_level: RiskLevel = RiskLevel.NORMAL
    time_to_threshold: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def utilization(self) -> float:
        if self.capacity == 0:
            return 0.0
        return (self.current_crowd / self.capacity) * 100

    @property
    def net_flow(self) -> float:
        return self.inflow_per_minute - self.outflow_per_minute

    class Config:
        from_attributes = True


class ZoneCrowdState(BaseModel):
    zone_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    people_count: int
    inflow_per_minute: float
    outflow_per_minute: float
    density: float
    movement_direction: Optional[str] = None
    movement_speed: Optional[float] = None
    source: str = "simulated"

    class Config:
        from_attributes = True
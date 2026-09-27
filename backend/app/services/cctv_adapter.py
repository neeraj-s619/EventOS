from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.models.database import ZoneDB, ZoneCrowdStateDB


class CrowdDataSource(str, Enum):
    SIMULATED_CCTV = "simulated_cctv"
    REAL_CCTV_CV = "real_cctv_cv"
    TURNSTILE = "turnstile"
    MANUAL_OVERRIDE = "manual_override"


class CCTVTelemetry(BaseModel):
    zone_id: str
    people_count: int
    inflow_per_minute: float
    outflow_per_minute: float
    density: Optional[float] = None
    movement_direction: Optional[str] = None
    movement_speed: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: CrowdDataSource = CrowdDataSource.REAL_CCTV_CV
    camera_id: Optional[str] = None
    confidence: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)

    @field_validator("people_count", mode="before")
    @classmethod
    def sanitize_people_count(cls, v: Any) -> int:
        try:
            val = int(v)
            return max(0, val)
        except (ValueError, TypeError):
            return 0

    @field_validator("inflow_per_minute", mode="before")
    @classmethod
    def sanitize_inflow(cls, v: Any) -> float:
        try:
            val = float(v)
            return max(0.0, val)
        except (ValueError, TypeError):
            return 0.0

    @field_validator("outflow_per_minute", mode="before")
    @classmethod
    def sanitize_outflow(cls, v: Any) -> float:
        try:
            val = float(v)
            return max(0.0, val)
        except (ValueError, TypeError):
            return 0.0


class CCTVAdapter:
    """
    Adapter interface separating SIMULATED_CCTV from REAL_CCTV_CV inputs.
    Standardizes ingestion from real Computer Vision / Optical Flow systems
    or simulated CCTV generators while guaranteeing data integrity.
    """

    def __init__(self, db: Session):
        self.db = db

    def ingest_telemetry(self, telemetry: CCTVTelemetry) -> ZoneCrowdStateDB:
        zone = self.db.query(ZoneDB).filter(ZoneDB.zone_id == telemetry.zone_id).first()
        if not zone:
            raise ValueError(f"Zone {telemetry.zone_id} not found")

        # Calculate density if not provided or invalid
        density = telemetry.density
        if density is None or density < 0:
            density = (telemetry.people_count / zone.capacity) if zone.capacity > 0 else 0.0
        density = max(0.0, float(density))

        crowd_state = ZoneCrowdStateDB(
            zone_id=zone.zone_id,
            timestamp=telemetry.timestamp or datetime.utcnow(),
            people_count=telemetry.people_count,
            inflow_per_minute=telemetry.inflow_per_minute,
            outflow_per_minute=telemetry.outflow_per_minute,
            density=density,
            movement_direction=telemetry.movement_direction,
            movement_speed=telemetry.movement_speed,
            source=telemetry.source.value if isinstance(telemetry.source, CrowdDataSource) else str(telemetry.source)
        )

        zone.current_crowd = telemetry.people_count
        zone.inflow_per_minute = telemetry.inflow_per_minute
        zone.outflow_per_minute = telemetry.outflow_per_minute
        zone.density = density
        zone.updated_at = datetime.utcnow()

        self.db.add(crowd_state)
        self.db.commit()
        self.db.refresh(crowd_state)
        self.db.refresh(zone)

        return crowd_state

    def ingest_real_cv(
        self,
        zone_id: str,
        people_count: int,
        inflow_per_minute: float,
        outflow_per_minute: float,
        density: Optional[float] = None,
        movement_direction: Optional[str] = None,
        movement_speed: Optional[float] = None,
        camera_id: Optional[str] = None,
        confidence: float = 1.0,
        timestamp: Optional[datetime] = None
    ) -> ZoneCrowdStateDB:
        telemetry = CCTVTelemetry(
            zone_id=zone_id,
            people_count=people_count,
            inflow_per_minute=inflow_per_minute,
            outflow_per_minute=outflow_per_minute,
            density=density,
            movement_direction=movement_direction,
            movement_speed=movement_speed,
            timestamp=timestamp or datetime.utcnow(),
            source=CrowdDataSource.REAL_CCTV_CV,
            camera_id=camera_id,
            confidence=confidence
        )
        return self.ingest_telemetry(telemetry)

    def ingest_simulated(
        self,
        zone_id: str,
        people_count: int,
        inflow_per_minute: float,
        outflow_per_minute: float,
        density: Optional[float] = None,
        movement_direction: Optional[str] = None,
        movement_speed: Optional[float] = None,
        timestamp: Optional[datetime] = None
    ) -> ZoneCrowdStateDB:
        telemetry = CCTVTelemetry(
            zone_id=zone_id,
            people_count=people_count,
            inflow_per_minute=inflow_per_minute,
            outflow_per_minute=outflow_per_minute,
            density=density,
            movement_direction=movement_direction,
            movement_speed=movement_speed,
            timestamp=timestamp or datetime.utcnow(),
            source=CrowdDataSource.SIMULATED_CCTV
        )
        return self.ingest_telemetry(telemetry)

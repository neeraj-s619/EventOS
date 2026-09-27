"""
PDR (Pedestrian Dead-Reckoning) Aggregate Movement Signal Adapter for EVENTOS.
Strictly implements macro-level crowd flow signal ingestion in compliance with
docs/PDR_GPS_ARCHITECTURE.md:
- Privacy-by-design: App-independent, ZERO individual visitor tracking.
- Macro flow vectors: Ingests aggregate device clusters and headings.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.database import ZoneDB, ZoneCrowdStateDB


class PDRSignalInput(BaseModel):
    zone_id: str
    device_count: int = Field(ge=0, description="Aggregate number of detected devices in movement cluster")
    heading_degrees: float = Field(ge=0.0, le=360.0, description="Average heading angle (0=N, 90=E, 180=S, 270=W)")
    speed_mps: float = Field(default=1.2, ge=0.0, le=10.0, description="Average walking speed in m/s")
    movement_direction: Optional[str] = None
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)

    @field_validator("device_count", mode="before")
    @classmethod
    def sanitize_device_count(cls, v: Any) -> int:
        try:
            return max(0, int(v))
        except (ValueError, TypeError):
            return 0


class PDRAdapter:
    """
    Adapter for aggregate pedestrian flow vector telemetry.
    Translates collective heading, cluster size, and velocity into zone ingress/egress dynamics.
    """

    def __init__(self, db: Session):
        self.db = db

    def _heading_to_direction(self, heading: float) -> str:
        compass = ["NORTH", "NORTHEAST", "EAST", "SOUTHEAST", "SOUTH", "SOUTHWEST", "WEST", "NORTHWEST"]
        idx = int((heading + 22.5) / 45) % 8
        return compass[idx]

    def ingest_pdr_signal(self, signal: PDRSignalInput) -> Dict[str, Any]:
        zone = self.db.query(ZoneDB).filter(ZoneDB.zone_id == signal.zone_id).first()
        if not zone:
            raise ValueError(f"Zone {signal.zone_id} not found")

        direction = signal.movement_direction or self._heading_to_direction(signal.heading_degrees)

        # Macro flow dynamics:
        # Heading towards south/southeast is typical entry corridor in demo topology
        # We calculate inflow/outflow balance from cluster velocity and size
        flow_rate = (signal.device_count * signal.speed_mps) / 2.0  # rate per minute
        if 45.0 <= signal.heading_degrees <= 225.0:
            inflow = round(flow_rate * 0.8, 1)
            outflow = round(flow_rate * 0.2, 1)
        else:
            inflow = round(flow_rate * 0.2, 1)
            outflow = round(flow_rate * 0.8, 1)

        # Scale estimated crowd
        new_crowd = max(0, zone.current_crowd + int(inflow - outflow))
        density = (new_crowd / zone.capacity) if zone.capacity > 0 else 0.0

        crowd_state = ZoneCrowdStateDB(
            zone_id=zone.zone_id,
            timestamp=signal.timestamp or datetime.utcnow(),
            people_count=new_crowd,
            inflow_per_minute=inflow,
            outflow_per_minute=outflow,
            density=density,
            movement_direction=direction,
            movement_speed=signal.speed_mps,
            source="pdr_aggregate"
        )

        zone.current_crowd = new_crowd
        zone.inflow_per_minute = inflow
        zone.outflow_per_minute = outflow
        zone.density = density
        zone.updated_at = datetime.utcnow()

        self.db.add(crowd_state)
        self.db.commit()
        self.db.refresh(crowd_state)
        self.db.refresh(zone)

        return {
            "status": "pdr_signal_ingested",
            "zone_id": zone.zone_id,
            "device_cluster_count": signal.device_count,
            "heading_degrees": signal.heading_degrees,
            "direction": direction,
            "speed_mps": signal.speed_mps,
            "inflow_per_minute": inflow,
            "outflow_per_minute": outflow,
            "calculated_people_count": new_crowd,
            "density": round(density, 3),
            "source": "pdr_aggregate",
            "crowd_state_id": crowd_state.id
        }

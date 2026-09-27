"""
GPS Fleet Tracking Adapter for EVENTOS.
Strictly implements transport vehicle tracking in compliance with
docs/PDR_GPS_ARCHITECTURE.md:
- ZERO individual visitor GPS collection.
- Monitors transit fleet supply (buses, shuttles, vans) to calculate dynamic transport capacity.
- Feeds into ProviderDB and ProviderCapacityUpdateDB.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.database import ProviderDB, ProviderTypeEnum, ProviderCapacityUpdateDB, ZoneDB


class FleetSignalInput(BaseModel):
    vehicle_id: str
    zone_id: str
    provider_id: Optional[str] = None
    vehicle_type: str = Field(default="bus", description="bus, shuttle, metro, van")
    capacity: int = Field(default=50, ge=1)
    occupied_seats: int = Field(default=0, ge=0)
    available_seats: Optional[int] = None
    status: str = Field(default="in_transit", description="in_transit, arrived, boarding, idle")
    eta_minutes: float = Field(default=5.0, ge=0.0)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)

    @field_validator("occupied_seats", mode="before")
    @classmethod
    def sanitize_occupied(cls, v: Any) -> int:
        try:
            return max(0, int(v))
        except (ValueError, TypeError):
            return 0


# In-memory registry for live vehicle fleet tracking states
_FLEET_REGISTRY: Dict[str, Dict[str, Any]] = {}


class GPSFleetAdapter:
    """
    Adapter for transport fleet tracking telemetry.
    Aggregates active vehicles per zone and updates transport provider capacity in real-time.
    """

    def __init__(self, db: Session):
        self.db = db

    def ingest_fleet_signal(self, signal: FleetSignalInput) -> Dict[str, Any]:
        global _FLEET_REGISTRY

        # Compute available seats
        available = signal.available_seats
        if available is None:
            available = max(0, signal.capacity - signal.occupied_seats)
        else:
            available = max(0, available)

        # Store vehicle state in live registry
        vehicle_record = {
            "vehicle_id": signal.vehicle_id,
            "provider_id": signal.provider_id,
            "zone_id": signal.zone_id,
            "vehicle_type": signal.vehicle_type,
            "capacity": signal.capacity,
            "occupied_seats": signal.occupied_seats,
            "available_seats": available,
            "status": signal.status,
            "eta_minutes": signal.eta_minutes,
            "latitude": signal.latitude,
            "longitude": signal.longitude,
            "last_ping": signal.timestamp.isoformat() if signal.timestamp else datetime.utcnow().isoformat()
        }
        _FLEET_REGISTRY[signal.vehicle_id] = vehicle_record

        # Match or identify provider
        provider = None
        if signal.provider_id:
            provider = self.db.query(ProviderDB).filter(ProviderDB.provider_id == signal.provider_id).first()
        
        if not provider:
            # Match first transport provider in zone
            provider = self.db.query(ProviderDB).filter(
                ProviderDB.zone_id == signal.zone_id,
                ProviderDB.type == ProviderTypeEnum.TRANSPORT
            ).first()

        provider_updated = False
        if provider:
            # Aggregate available capacity from all registered vehicles for this provider or zone
            zone_vehicles = [
                v for v in _FLEET_REGISTRY.values()
                if v.get("zone_id") == signal.zone_id and (not v.get("provider_id") or v.get("provider_id") == provider.provider_id)
            ]
            
            total_fleet_cap = sum(v["capacity"] for v in zone_vehicles)
            total_available = sum(v["available_seats"] for v in zone_vehicles)
            total_occupied = sum(v["occupied_seats"] for v in zone_vehicles)

            # Update provider capacity
            cap = dict(provider.capacity) if provider.capacity else {}
            cap["total"] = max(cap.get("total", 0), total_fleet_cap)
            cap["available"] = total_available
            cap["occupied"] = total_occupied
            provider.capacity = cap
            provider.last_updated = datetime.utcnow()

            # Audit log
            audit = ProviderCapacityUpdateDB(
                provider_id=provider.provider_id,
                updates={"available": total_available, "occupied": total_occupied, "source": "gps_fleet"},
                source="gps_fleet",
                timestamp=datetime.utcnow()
            )
            self.db.add(audit)
            self.db.commit()
            self.db.refresh(provider)
            provider_updated = True

        return {
            "status": "fleet_signal_ingested",
            "vehicle": vehicle_record,
            "provider_updated": provider_updated,
            "provider_id": provider.provider_id if provider else None,
            "zone_fleet_count": len([v for v in _FLEET_REGISTRY.values() if v.get("zone_id") == signal.zone_id])
        }

    def get_fleet_status(self, zone_id: Optional[str] = None) -> Dict[str, Any]:
        global _FLEET_REGISTRY
        vehicles = list(_FLEET_REGISTRY.values())
        if zone_id:
            vehicles = [v for v in vehicles if v.get("zone_id") == zone_id]

        total_capacity = sum(v["capacity"] for v in vehicles)
        available_seats = sum(v["available_seats"] for v in vehicles)
        occupied_seats = sum(v["occupied_seats"] for v in vehicles)

        return {
            "active_vehicles_count": len(vehicles),
            "total_fleet_capacity": total_capacity,
            "total_available_seats": available_seats,
            "total_occupied_seats": occupied_seats,
            "vehicles": vehicles
        }

    @classmethod
    def reset_registry(cls):
        global _FLEET_REGISTRY
        _FLEET_REGISTRY.clear()

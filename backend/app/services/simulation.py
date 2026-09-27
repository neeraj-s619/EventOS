import random
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.database import EventDB, ZoneDB, ZoneCrowdStateDB, ProviderDB, ProviderTypeEnum


class CrowdSimulator:
    def __init__(self, db: Session):
        self.db = db
    
    def simulate_event_scenario(self, event_id: str) -> Dict:
        event = self.db.query(EventDB).filter(EventDB.event_id == event_id).first()
        if not event:
            raise ValueError("Event not found")
        
        zones = self.db.query(ZoneDB).filter(ZoneDB.event_id == event_id).all()
        
        for zone in zones:
            self._simulate_zone_crowd(zone)
        
        self.db.commit()
        return {"status": "simulated", "zones_updated": len(zones)}
    
    def _simulate_zone_crowd(self, zone: ZoneDB):
        base_crowd = zone.current_crowd
        hour = datetime.utcnow().hour
        
        event_factor = 1.0
        if 18 <= hour <= 22:
            event_factor = 1.5
        elif 10 <= hour <= 16:
            event_factor = 1.2
        elif 0 <= hour <= 5:
            event_factor = 0.3
        
        venue_providers = self.db.query(ProviderDB).filter(
            ProviderDB.zone_id == zone.zone_id,
            ProviderDB.type == ProviderTypeEnum.VENUE
        ).all()
        
        venue_capacity = sum(p.capacity.get("total", 0) for p in venue_providers)
        if venue_capacity > 0:
            max_crowd = min(zone.capacity, venue_capacity)
        else:
            max_crowd = zone.capacity
        
        if base_crowd == 0:
            base_crowd = int(max_crowd * 0.1 * event_factor)
        
        inflow_base = max_crowd * 0.02 * event_factor
        outflow_base = max_crowd * 0.015 * event_factor
        
        noise = random.uniform(-0.3, 0.3)
        inflow = max(0, inflow_base * (1 + noise))
        outflow = max(0, outflow_base * (1 + noise))
        
        if base_crowd > max_crowd * 0.8:
            outflow *= 1.5
            inflow *= 0.5
        
        new_crowd = int(base_crowd + inflow - outflow)
        new_crowd = max(0, min(new_crowd, max_crowd))
        
        density = new_crowd / max(zone.capacity, 1)
        
        crowd_state = ZoneCrowdStateDB(
            zone_id=zone.zone_id,
            people_count=new_crowd,
            inflow_per_minute=inflow,
            outflow_per_minute=outflow,
            density=density,
            movement_direction=self._random_direction(),
            movement_speed=random.uniform(0.5, 2.0),
            source="simulated_cctv"
        )
        
        zone.current_crowd = new_crowd
        zone.inflow_per_minute = inflow
        zone.outflow_per_minute = outflow
        zone.density = density
        zone.updated_at = datetime.utcnow()
        
        self.db.add(crowd_state)
    
    def _random_direction(self) -> str:
        directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        return random.choice(directions)


class ProviderSimulator:
    def __init__(self, db: Session):
        self.db = db
    
    def simulate_provider_updates(self, event_id: str) -> Dict:
        providers = self.db.query(ProviderDB).filter(ProviderDB.event_id == event_id).all()
        
        for provider in providers:
            self._simulate_provider(provider)
        
        self.db.commit()
        return {"status": "simulated", "providers_updated": len(providers)}
    
    def _simulate_provider(self, provider: ProviderDB):
        if provider.type == ProviderTypeEnum.HOTEL:
            total = provider.capacity.get("total", 200)
            occupied = provider.capacity.get("occupied", int(total * 0.6))
            change = random.randint(-5, 5)
            occupied = max(0, min(total, occupied + change))
            provider.capacity["occupied"] = occupied
            provider.capacity["available"] = total - occupied
            
        elif provider.type == ProviderTypeEnum.TRANSPORT:
            total = provider.capacity.get("total", 500)
            occupied = provider.capacity.get("occupied", int(total * 0.4))
            change = random.randint(-20, 20)
            occupied = max(0, min(total, occupied + change))
            provider.capacity["occupied"] = occupied
            provider.capacity["available"] = total - occupied
            
        elif provider.type == ProviderTypeEnum.VENUE:
            total = provider.capacity.get("total", zone.capacity if (zone := self.db.query(ZoneDB).filter(ZoneDB.zone_id == provider.zone_id).first()) else 50000)
            occupied = provider.capacity.get("occupied", int(total * 0.7))
            change = random.randint(-100, 100)
            occupied = max(0, min(total, occupied + change))
            provider.capacity["occupied"] = occupied
            provider.capacity["available"] = total - occupied
        
        provider.last_updated = datetime.utcnow()


def create_demo_event(db: Session) -> EventDB:
    event = EventDB(
        name="Mumbai Mega Sports Event",
        description="Large scale sports tournament with 150,000 expected visitors",
        start_date=datetime(2026, 1, 10),
        end_date=datetime(2026, 1, 15),
        expected_visitors=150000,
        operational_thresholds={
            "crowd_warning": 70.0,
            "crowd_critical": 85.0,
            "movement_warning": 80.0,
            "movement_critical": 95.0
        },
        schedule=[
            {"date": "2026-01-10", "time": "10:00", "event": "Opening Ceremony", "venue": "Venue A", "expected_attendance": 50000},
            {"date": "2026-01-11", "time": "14:00", "event": "Match Day 1", "venue": "Venue A", "expected_attendance": 60000},
            {"date": "2026-01-12", "time": "14:00", "event": "Match Day 2", "venue": "Venue B", "expected_attendance": 55000},
            {"date": "2026-01-13", "time": "18:00", "event": "Semi Finals", "venue": "Venue A", "expected_attendance": 70000},
            {"date": "2026-01-14", "time": "18:00", "event": "Finals", "venue": "Venue A", "expected_attendance": 75000},
            {"date": "2026-01-15", "time": "10:00", "event": "Closing Ceremony", "venue": "Venue A", "expected_attendance": 40000}
        ]
    )
    db.add(event)
    db.flush()
    
    zones_data = [
        {
            "name": "Zone A - Main Venue District",
            "zone_type": "venue",
            "capacity": 80000,
            "expected_demand": 65000,
            "boundary": {"type": "polygon", "coordinates": [[72.8, 19.0], [72.9, 19.0], [72.9, 19.1], [72.8, 19.1]]}
        },
        {
            "name": "Zone B - Hospitality District",
            "zone_type": "hospitality",
            "capacity": 25000,
            "expected_demand": 15000,
            "boundary": {"type": "polygon", "coordinates": [[72.9, 19.0], [73.0, 19.0], [73.0, 19.1], [72.9, 19.1]]}
        },
        {
            "name": "Zone C - Transport Hub",
            "zone_type": "transport",
            "capacity": 15000,
            "expected_demand": 10000,
            "boundary": {"type": "polygon", "coordinates": [[72.8, 19.1], [72.9, 19.1], [72.9, 19.2], [72.8, 19.2]]}
        }
    ]
    
    zone_objects = []
    for zdata in zones_data:
        zone = ZoneDB(event_id=event.event_id, **zdata)
        db.add(zone)
        zone_objects.append(zone)
    db.flush()
    
    event.zones = [z.zone_id for z in zone_objects]
    event.venues = [zone_objects[0].zone_id, zone_objects[1].zone_id]
    
    providers_data = [
        {"zone_id": zone_objects[1].zone_id, "type": ProviderTypeEnum.HOTEL, "name": "Hotel Grand Palace", "capacity": {"total": 300, "available": 120, "occupied": 180}},
        {"zone_id": zone_objects[1].zone_id, "type": ProviderTypeEnum.HOTEL, "name": "Hotel Sea View", "capacity": {"total": 250, "available": 82, "occupied": 168}},
        {"zone_id": zone_objects[1].zone_id, "type": ProviderTypeEnum.HOTEL, "name": "Hotel City Center", "capacity": {"total": 400, "available": 150, "occupied": 250}},
        {"zone_id": zone_objects[1].zone_id, "type": ProviderTypeEnum.HOTEL, "name": "Budget Inn Express", "capacity": {"total": 180, "available": 45, "occupied": 135}},
        {"zone_id": zone_objects[1].zone_id, "type": ProviderTypeEnum.HOTEL, "name": "Luxury Suites Mumbai", "capacity": {"total": 200, "available": 60, "occupied": 140}},
        
        {"zone_id": zone_objects[2].zone_id, "type": ProviderTypeEnum.TRANSPORT, "name": "Metro Line 1", "capacity": {"total": 2000, "available": 1200, "occupied": 800}},
        {"zone_id": zone_objects[2].zone_id, "type": ProviderTypeEnum.TRANSPORT, "name": "Bus Route 42", "capacity": {"total": 800, "available": 320, "occupied": 480}},
        {"zone_id": zone_objects[2].zone_id, "type": ProviderTypeEnum.TRANSPORT, "name": "Shuttle Service A", "capacity": {"total": 600, "available": 180, "occupied": 420}},
        {"zone_id": zone_objects[2].zone_id, "type": ProviderTypeEnum.TRANSPORT, "name": "Taxi Pool", "capacity": {"total": 400, "available": 150, "occupied": 250}},
        {"zone_id": zone_objects[2].zone_id, "type": ProviderTypeEnum.TRANSPORT, "name": "Auto Rickshaw Stand", "capacity": {"total": 300, "available": 96, "occupied": 204}},
        
        {"zone_id": zone_objects[0].zone_id, "type": ProviderTypeEnum.VENUE, "name": "Main Stadium", "capacity": {"total": 50000, "available": 8000, "occupied": 42000}},
        {"zone_id": zone_objects[0].zone_id, "type": ProviderTypeEnum.VENUE, "name": "Indoor Arena", "capacity": {"total": 15000, "available": 5000, "occupied": 10000}},
        {"zone_id": zone_objects[0].zone_id, "type": ProviderTypeEnum.VENUE, "name": "Training Grounds", "capacity": {"total": 5000, "available": 2000, "occupied": 3000}},
    ]
    
    for pdata in providers_data:
        provider = ProviderDB(event_id=event.event_id, **pdata)
        db.add(provider)
    
    db.commit()
    db.refresh(event)
    return event
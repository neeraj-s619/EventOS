from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import os

from app.core.config import settings
from app.core.database import init_db, get_db, SessionLocal
from app.models.database import (
    EventDB, ZoneDB, ProviderDB, ZoneCrowdStateDB, ForecastDB,
    OrchestrationRecommendationDB, ActionExecutionDB, ProviderCapacityUpdateDB
)
from app.schemas.event import (
    EventCreate, EventUpdate, EventResponse,
    ZoneCreate, ZoneUpdate, ZoneResponse,
    ZoneCrowdStateCreate, ZoneCrowdStateResponse,
    ProviderCreate, ProviderUpdate, ProviderResponse,
    ProviderCapacityUpdateRequest, UnifiedEventStateResponse
)
from app.api.intelligence import router as intelligence_router, integrations_router
from app.api.nugen import router as nugen_router
from app.services.telegram.manager import get_telegram_bot_manager, TelegramBotManager
from app.services.telegram.polling import TelegramPollingWorker

bot_manager: Optional[TelegramBotManager] = None
telegram_worker: Optional[TelegramPollingWorker] = None


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(intelligence_router)
app.include_router(integrations_router)
app.include_router(nugen_router)

static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", include_in_schema=False)
@app.get("/dashboard", include_in_schema=False)
def serve_dashboard():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "EVENTOS Control Tower Dashboard", "docs": "/docs"}


@app.on_event("startup")
def startup_event():
    global telegram_worker, bot_manager
    init_db()
    db = next(get_db())
    try:
        from app.services.mumbai_venues import seed_real_mumbai_events
        seed_real_mumbai_events(db)
    except Exception as e:
        import logging
        logging.getLogger("eventos").warning("Startup Mumbai seeding skipped/error: %s", e)
    finally:
        db.close()

    try:
        bot_manager = get_telegram_bot_manager()
        res = bot_manager.start()
        telegram_worker = bot_manager.staff_worker
        import logging
        logging.getLogger("eventos").info("Telegram Operations Network initialized: %s", res)
    except Exception as e:
        import logging
        logging.getLogger("eventos").warning("Telegram Operations Network startup warning: %s", e)


@app.on_event("shutdown")
def shutdown_event():
    global telegram_worker, bot_manager
    if bot_manager:
        try:
            bot_manager.stop()
        except Exception:
            pass
    elif telegram_worker:
        try:
            telegram_worker.stop()
        except Exception:
            pass


@app.get("/health")
def health_check():
    return {"status": "healthy", "app": settings.app_name, "version": settings.app_version}


# Event endpoints
@app.post("/api/v1/events", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(event: EventCreate, db: Session = Depends(get_db)):
    event_data = event.model_dump()
    event_data.setdefault("operational_thresholds", {})
    event_data.setdefault("schedule", [])
    db_event = EventDB(**event_data)
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


@app.get("/api/v1/events", response_model=List[EventResponse])
def list_events(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(EventDB).offset(skip).limit(limit).all()


@app.get("/api/v1/events/{event_id}", response_model=EventResponse)
def get_event(event_id: str, db: Session = Depends(get_db)):
    event = db.query(EventDB).filter(EventDB.event_id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@app.patch("/api/v1/events/{event_id}", response_model=EventResponse)
def update_event(event_id: str, event_update: EventUpdate, db: Session = Depends(get_db)):
    event = db.query(EventDB).filter(EventDB.event_id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    update_data = event_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(event, field, value)
    event.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(event)
    return event


@app.delete("/api/v1/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(event_id: str, db: Session = Depends(get_db)):
    event = db.query(EventDB).filter(EventDB.event_id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    db.delete(event)
    db.commit()


# Zone endpoints
@app.post("/api/v1/events/{event_id}/zones", response_model=ZoneResponse, status_code=status.HTTP_201_CREATED)
def create_zone(event_id: str, zone: ZoneCreate, db: Session = Depends(get_db)):
    event = db.query(EventDB).filter(EventDB.event_id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    db_zone = ZoneDB(event_id=event_id, **zone.model_dump())
    db.add(db_zone)
    
    event.zones.append(db_zone.zone_id)
    event.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_zone)
    return db_zone


@app.get("/api/v1/events/{event_id}/zones", response_model=List[ZoneResponse])
def list_zones(event_id: str, db: Session = Depends(get_db)):
    event = db.query(EventDB).filter(EventDB.event_id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return db.query(ZoneDB).filter(ZoneDB.event_id == event_id).all()


@app.get("/api/v1/zones/{zone_id}", response_model=ZoneResponse)
def get_zone(zone_id: str, db: Session = Depends(get_db)):
    zone = db.query(ZoneDB).filter(ZoneDB.zone_id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    return zone


@app.patch("/api/v1/zones/{zone_id}", response_model=ZoneResponse)
def update_zone(zone_id: str, zone_update: ZoneUpdate, db: Session = Depends(get_db)):
    zone = db.query(ZoneDB).filter(ZoneDB.zone_id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    
    update_data = zone_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(zone, field, value)
    zone.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(zone)
    return zone


@app.delete("/api/v1/zones/{zone_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_zone(zone_id: str, db: Session = Depends(get_db)):
    zone = db.query(ZoneDB).filter(ZoneDB.zone_id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    db.delete(zone)
    db.commit()


# Zone Crowd State endpoints
@app.post("/api/v1/zones/{zone_id}/crowd-state", response_model=ZoneCrowdStateResponse, status_code=status.HTTP_201_CREATED)
def create_crowd_state(zone_id: str, crowd_state: ZoneCrowdStateCreate, db: Session = Depends(get_db)):
    zone = db.query(ZoneDB).filter(ZoneDB.zone_id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    
    people_count = max(0, crowd_state.people_count)
    inflow = max(0.0, crowd_state.inflow_per_minute)
    outflow = max(0.0, crowd_state.outflow_per_minute)
    density = crowd_state.density
    if density is None or density < 0:
        density = (people_count / zone.capacity) if zone.capacity > 0 else 0.0
    else:
        density = max(0.0, float(density))
        
    crowd_dict = crowd_state.model_dump()
    crowd_dict["people_count"] = people_count
    crowd_dict["inflow_per_minute"] = inflow
    crowd_dict["outflow_per_minute"] = outflow
    crowd_dict["density"] = density
    
    db_crowd = ZoneCrowdStateDB(zone_id=zone_id, **crowd_dict)
    db.add(db_crowd)
    
    zone.current_crowd = people_count
    zone.inflow_per_minute = inflow
    zone.outflow_per_minute = outflow
    zone.density = density
    zone.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_crowd)
    return db_crowd


@app.get("/api/v1/zones/{zone_id}/crowd-state", response_model=List[ZoneCrowdStateResponse])
def get_crowd_history(zone_id: str, limit: int = 100, db: Session = Depends(get_db)):
    zone = db.query(ZoneDB).filter(ZoneDB.zone_id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    return db.query(ZoneCrowdStateDB).filter(
        ZoneCrowdStateDB.zone_id == zone_id
    ).order_by(ZoneCrowdStateDB.timestamp.desc()).limit(limit).all()


# Provider endpoints
@app.post("/api/v1/events/{event_id}/providers", response_model=ProviderResponse, status_code=status.HTTP_201_CREATED)
def create_provider(event_id: str, provider: ProviderCreate, db: Session = Depends(get_db)):
    event = db.query(EventDB).filter(EventDB.event_id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    zone = db.query(ZoneDB).filter(ZoneDB.zone_id == provider.zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    
    prov_data = provider.model_dump()
    if "metadata" in prov_data:
        prov_data["provider_metadata"] = prov_data.pop("metadata") or {}
    db_provider = ProviderDB(event_id=event_id, **prov_data)
    db.add(db_provider)
    
    zone.providers.append(db_provider.provider_id)
    zone.updated_at = datetime.utcnow()
    event.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_provider)
    return db_provider


@app.get("/api/v1/events/{event_id}/providers", response_model=List[ProviderResponse])
def list_providers(event_id: str, db: Session = Depends(get_db)):
    event = db.query(EventDB).filter(EventDB.event_id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return db.query(ProviderDB).filter(ProviderDB.event_id == event_id).all()


@app.get("/api/v1/providers/{provider_id}", response_model=ProviderResponse)
def get_provider(provider_id: str, db: Session = Depends(get_db)):
    provider = db.query(ProviderDB).filter(ProviderDB.provider_id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    return provider


@app.patch("/api/v1/providers/{provider_id}", response_model=ProviderResponse)
def update_provider(provider_id: str, provider_update: ProviderUpdate, db: Session = Depends(get_db)):
    provider = db.query(ProviderDB).filter(ProviderDB.provider_id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    update_data = provider_update.model_dump(exclude_unset=True)
    if "metadata" in update_data:
        update_data["provider_metadata"] = update_data.pop("metadata") or {}
    for field, value in update_data.items():
        setattr(provider, field, value)
    provider.last_updated = datetime.utcnow()
    
    db.commit()
    db.refresh(provider)
    return provider


@app.post("/api/v1/providers/capacity-update", response_model=ProviderResponse)
def update_provider_capacity(update: ProviderCapacityUpdateRequest, db: Session = Depends(get_db)):
    provider = db.query(ProviderDB).filter(ProviderDB.provider_id == update.provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    cap = dict(provider.capacity) if provider.capacity else {}
    serialized_updates = {}
    for dim, value in update.updates.items():
        key = dim.value if hasattr(dim, "value") else str(dim)
        cap[key] = value
        serialized_updates[key] = value
    provider.capacity = cap
    provider.last_updated = datetime.utcnow()
    
    audit_update = ProviderCapacityUpdateDB(
        provider_id=provider.provider_id,
        updates=serialized_updates,
        source="api"
    )
    db.add(audit_update)
    
    db.commit()
    db.refresh(provider)
    return provider


# Unified Event State
@app.get("/api/v1/events/{event_id}/unified-state", response_model=UnifiedEventStateResponse)
def get_unified_state(event_id: str, db: Session = Depends(get_db)):
    event = db.query(EventDB).filter(EventDB.event_id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    zones = db.query(ZoneDB).filter(ZoneDB.event_id == event_id).all()
    providers = db.query(ProviderDB).filter(ProviderDB.event_id == event_id).all()
    
    zone_data = {}
    for zone in zones:
        zone_providers = [p for p in providers if p.zone_id == zone.zone_id]
        
        hotel_capacity = sum(p.capacity.get("available", 0) for p in zone_providers if p.type.value == "hotel")
        transport_capacity = sum(p.capacity.get("available", 0) for p in zone_providers if p.type.value == "transport")
        venue_capacity = sum(p.capacity.get("available", 0) for p in zone_providers if p.type.value == "venue")
        
        zone_forecasts = db.query(ForecastDB).filter(ForecastDB.zone_id == zone.zone_id).order_by(ForecastDB.timestamp.desc()).limit(3).all()
        forecast_summary = [
            {
                "horizon_minutes": f.horizon_minutes,
                "predicted_crowd": f.predicted_crowd,
                "predicted_utilization": f.predicted_utilization,
                "confidence": f.confidence
            }
            for f in zone_forecasts
        ]

        zone_recs = db.query(OrchestrationRecommendationDB).filter(
            OrchestrationRecommendationDB.zone_id == zone.zone_id,
            OrchestrationRecommendationDB.status.in_(["pending", "approved", "executing", "dispatched"])
        ).all()
        recommendation_summary = [
            {
                "id": r.id,
                "type": r.recommendation_type,
                "status": r.status,
                "description": r.description
            }
            for r in zone_recs
        ]

        zone_data[zone.zone_id] = {
            "name": zone.name,
            "description": getattr(zone, "description", None),
            "zone_type": zone.zone_type.value if hasattr(zone.zone_type, "value") else str(zone.zone_type),
            "crowd": zone.current_crowd,
            "inflow": zone.inflow_per_minute,
            "outflow": zone.outflow_per_minute,
            "capacity": zone.capacity,
            "operational_capacity": getattr(zone, "operational_capacity", None) or zone.capacity,
            "utilization": zone.utilization,
            "net_flow": zone.net_flow,
            "hotel_capacity": hotel_capacity,
            "transport_capacity": transport_capacity,
            "venue_capacity": venue_capacity,
            "risk_level": zone.risk_level.value if hasattr(zone.risk_level, "value") else str(zone.risk_level),
            "time_to_threshold": zone.time_to_threshold,
            "source_type": getattr(zone, "source_type", "VERIFIED_PUBLIC") or "VERIFIED_PUBLIC",
            "forecast": forecast_summary,
            "active_recommendations": recommendation_summary,
            "providers": [
                {
                    "provider_id": p.provider_id,
                    "type": p.type.value if hasattr(p.type, "value") else str(p.type),
                    "name": p.name,
                    "location": getattr(p, "location", None),
                    "source_type": getattr(p, "source_type", "SIMULATED") or "SIMULATED",
                    "status": p.status.value if hasattr(p.status, "value") else str(p.status),
                    "available": p.capacity.get("available", 0),
                    "total": p.capacity.get("total", 0)
                }
                for p in zone_providers
            ]
        }
    
    return UnifiedEventStateResponse(
        event_id=event_id,
        timestamp=datetime.utcnow(),
        zones=zone_data
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
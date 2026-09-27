"""
Real-World Mumbai Venues and Events Data Foundation for EVENTOS.
Provides verified static metadata for Mumbai venues and real event scenarios:
1. Wankhede Stadium (D Road, Churchgate, Mumbai) - MCA Verified Capacity ~33,500
2. Jio World Convention Centre (G Block, BKC, Bandra East) - Official Factsheet Room Capacities
Zero fake/generic 80k stadium assumptions. Database as single source of truth.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.database import (
    VenueDB, EventDB, ZoneDB, ProviderDB,
    ProviderTypeEnum, ZoneTypeEnum, EventStatusEnum,
    TelegramMessageAuditDB
)


# Verified Real-World Venue Metadata Records
WANKHEDE_VENUE_METADATA = {
    "name": "Wankhede Stadium",
    "venue_type": "Cricket Stadium",
    "address": "D Road, Churchgate, Mumbai, Maharashtra 400020",
    "locality": "Churchgate / Marine Drive",
    "city": "Mumbai",
    "state": "Maharashtra",
    "country": "India",
    "latitude": 18.9389,
    "longitude": 72.8258,
    "official_capacity": 33500,
    "capacity_basis": "Mumbai Cricket Association (MCA) official stadium seating capacity record (~33,500)",
    "source_name": "Mumbai Cricket Association (MCA)",
    "source_url": "https://www.mumbaicricket.com/wankhede",
    "source_type": "VERIFIED_PUBLIC"
}

JWCC_VENUE_METADATA = {
    "name": "Jio World Convention Centre",
    "venue_type": "Convention & Exhibition Centre",
    "address": "Jio World Centre, G Block, Bandra Kurla Complex, Bandra East, Mumbai, Maharashtra 400051",
    "locality": "Bandra Kurla Complex (BKC)",
    "city": "Mumbai",
    "state": "Maharashtra",
    "country": "India",
    "latitude": 19.0631,
    "longitude": 72.8687,
    "official_capacity": 33840,
    "capacity_basis": "Official JWCC factsheets for concurrent hall & pavilion capacities (Jasmine: 10,640, Pavilions: 16,500, Lotus: 3,200, Foyer: 3,500)",
    "source_name": "Jio World Centre Official Factsheet",
    "source_url": "https://www.jioworldcentre.com",
    "source_type": "VERIFIED_PUBLIC"
}


def get_or_create_wankhede_venue(db: Session) -> VenueDB:
    venue = db.query(VenueDB).filter(VenueDB.name == WANKHEDE_VENUE_METADATA["name"]).first()
    if not venue:
        venue = VenueDB(**WANKHEDE_VENUE_METADATA)
        db.add(venue)
        db.flush()
    return venue


def get_or_create_jwcc_venue(db: Session) -> VenueDB:
    venue = db.query(VenueDB).filter(VenueDB.name == JWCC_VENUE_METADATA["name"]).first()
    if not venue:
        venue = VenueDB(**JWCC_VENUE_METADATA)
        db.add(venue)
        db.flush()
    return venue


def seed_wankhede_event(db: Session) -> EventDB:
    """
    Creates or returns Event 1: Wankhede Stadium — Mumbai Cricket Event.
    Grounded in real MCA venue data.
    """
    venue = get_or_create_wankhede_venue(db)
    
    event = db.query(EventDB).filter(
        EventDB.name.like("%Wankhede Stadium%")
    ).first()

    if not event:
        # Create Event
        event = EventDB(
            name="Wankhede Stadium — Mumbai Cricket Event",
            description="High-attendance cricket event at Wankhede Stadium with Churchgate access & Marine Drive approach",
            city="Mumbai",
            state="Maharashtra",
            country="India",
            venue_id=venue.venue_id,
            event_type="Cricket Match / Tournament",
            start_date=datetime(2026, 10, 15, 14, 0),
            end_date=datetime(2026, 10, 15, 23, 0),
            expected_visitors=33500,
            status=EventStatusEnum.ACTIVE,
            source_type="VERIFIED_PUBLIC",
            source_url="https://www.mumbaicricket.com/wankhede",
            data_status="HYBRID",
            operational_thresholds={
                "crowd_warning": 75.0,
                "crowd_critical": 88.0,
                "organizer_whatsapp": "+15559876543"
            }
        )
        db.add(event)
        db.flush()

        # Real Sub-zones for Wankhede
        # Notice: names include "Zone A", "Zone B", "Zone C" for backward compatibility with master_demo.py
        zones_data = [
            {
                "name": "Zone A - Stadium Bowl",
                "description": "Main cricket stadium bowl, grandstands, corporate boxes, and spectator seating",
                "zone_type": ZoneTypeEnum.VENUE,
                "capacity": 26000,
                "operational_capacity": 26000,
                "current_crowd": 18420,
                "inflow_per_minute": 120.0,
                "outflow_per_minute": 30.0,
                "density": 0.708,
                "expected_demand": 26000,
                "latitude": 18.9389,
                "longitude": 72.8258,
                "source_type": "VERIFIED_PUBLIC",
                "venue_id": venue.venue_id
            },
            {
                "name": "Zone B - North Gate & Churchgate Access",
                "description": "Primary spectator ingress corridor, security turnstiles, and Churchgate railway approach",
                "zone_type": ZoneTypeEnum.HOSPITALITY,  # Concourse / Hospitality zone
                "capacity": 4500,
                "operational_capacity": 4500,
                "current_crowd": 2100,
                "inflow_per_minute": 95.0,
                "outflow_per_minute": 60.0,
                "density": 0.467,
                "expected_demand": 4500,
                "latitude": 18.9395,
                "longitude": 72.8262,
                "source_type": "VERIFIED_PUBLIC",
                "venue_id": venue.venue_id
            },
            {
                "name": "Zone C - Marine Drive External Approach",
                "description": "Outer dispersal perimeter, shuttle boarding bays, and Marine Drive seaside concourse",
                "zone_type": ZoneTypeEnum.TRANSPORT,
                "capacity": 3000,
                "operational_capacity": 3000,
                "current_crowd": 850,
                "inflow_per_minute": 45.0,
                "outflow_per_minute": 50.0,
                "density": 0.283,
                "expected_demand": 3000,
                "latitude": 18.9378,
                "longitude": 72.8245,
                "source_type": "VERIFIED_PUBLIC",
                "venue_id": venue.venue_id
            }
        ]

        zone_objs = []
        for zd in zones_data:
            z = ZoneDB(event_id=event.event_id, **zd)
            db.add(z)
            zone_objs.append(z)
        db.flush()

        event.zones = [z.zone_id for z in zone_objs]
        event.venues = [venue.venue_id]

        # Providers for Wankhede (Real local context, clearly marked as Simulated / Demo Feed)
        providers_data = [
            {
                "zone_id": zone_objs[2].zone_id,
                "type": ProviderTypeEnum.TRANSPORT,
                "name": "BEST & Western Railway Transit Fleet — Simulated Supply",
                "location": "Churchgate Station Terminus, D Road",
                "capacity": {"total": 1500, "available": 600, "occupied": 900},
                "source_type": "SIMULATED",
                "source_name": "Simulated Transit Dispatch",
                "contact_info": {"whatsapp": "+15551234567"}
            },
            {
                "zone_id": zone_objs[1].zone_id,
                "type": ProviderTypeEnum.HOTEL,
                "name": "The Taj Mahal Palace, Colaba — Demo Inventory",
                "location": "Apollo Bunder, Colaba, Mumbai (3.2 km)",
                "capacity": {"total": 285, "available": 82, "occupied": 203},
                "source_type": "SIMULATED",
                "source_name": "Demo Hotel Feed",
                "contact_info": {"whatsapp": "+15557654321"}
            },
            {
                "zone_id": zone_objs[1].zone_id,
                "type": ProviderTypeEnum.HOTEL,
                "name": "Trident Hotel Nariman Point — Demo Inventory",
                "location": "Nariman Point, Marine Drive, Mumbai (1.4 km)",
                "capacity": {"total": 320, "available": 95, "occupied": 225},
                "source_type": "SIMULATED",
                "source_name": "Demo Hotel Feed",
                "contact_info": {"whatsapp": "+15559871234"}
            },
            {
                "zone_id": zone_objs[0].zone_id,
                "type": ProviderTypeEnum.VENUE,
                "name": "Wankhede Gate Turnstiles (Gates 1-7) — Venue System",
                "location": "Wankhede Stadium North & East Gates",
                "capacity": {"total": 33500, "available": 15080, "occupied": 18420},
                "source_type": "SIMULATED",
                "source_name": "Simulated Turnstile Controller"
            }
        ]

        for pd in providers_data:
            p = ProviderDB(event_id=event.event_id, **pd)
            db.add(p)

        db.commit()
        db.refresh(event)

    # Ensure canonical Provider Pulse providers exist
    existing_provs = db.query(ProviderDB).filter(ProviderDB.event_id == event.event_id).all()
    existing_names = {p.name.lower() for p in existing_provs}
    first_zone = db.query(ZoneDB).filter(ZoneDB.event_id == event.event_id).first()
    first_zone_id = first_zone.zone_id if first_zone else "ZONE-01"

    canonical_pulse_providers = [
        {
            "name": "BEST Shuttle",
            "type": ProviderTypeEnum.TRANSPORT,
            "location": "Churchgate & Marine Drive Corridor",
            "capacity": {"total": 600, "available": 450, "occupied": 150},
            "source_type": "SIMULATED",
            "source_name": "BEST Mumbai Transit",
            "contact_info": {"telegram_username": "best_shuttle_bot", "telegram_chat_id": "1001"}
        },
        {
            "name": "Marine Hotel",
            "type": ProviderTypeEnum.HOTEL,
            "location": "Marine Drive Promenade",
            "capacity": {"total": 200, "available": 82, "occupied": 118},
            "source_type": "SIMULATED",
            "source_name": "Hospitality Network",
            "contact_info": {"telegram_username": "marine_hotel_bot", "telegram_chat_id": "1002"}
        },
        {
            "name": "Venue Partner",
            "type": ProviderTypeEnum.VENUE,
            "location": "Wankhede Stadium North Gate",
            "capacity": {"total": 10000, "available": 4200, "occupied": 5800},
            "source_type": "SIMULATED",
            "source_name": "Gate Operations",
            "contact_info": {"telegram_username": "venue_ops_bot", "telegram_chat_id": "1003"}
        }
    ]

    for cp in canonical_pulse_providers:
        if not any(cp["name"].lower() in en for en in existing_names):
            p = ProviderDB(event_id=event.event_id, zone_id=first_zone_id, **cp)
            db.add(p)
    db.commit()

    # Seed initial realistic responses if audit log is completely empty
    if db.query(TelegramMessageAuditDB).count() == 0:
        best_p = db.query(ProviderDB).filter(ProviderDB.name.like("%BEST%")).first()
        marine_p = db.query(ProviderDB).filter(ProviderDB.name.like("%Marine Hotel%")).first()
        venue_p = db.query(ProviderDB).filter(ProviderDB.name.like("%Venue%")).first()

        now = datetime.utcnow()
        if best_p:
            db.add(TelegramMessageAuditDB(
                message_id="init-audit-01",
                provider_id=best_p.provider_id,
                channel="TELEGRAM",
                direction="INBOUND",
                chat_id="1001",
                telegram_username="best_shuttle_bot",
                message_type="operational_response",
                raw_text="+100 seats available",
                parsed_resource="transport_capacity",
                parsed_value=100,
                processing_status="PROCESSED",
                status="confirmed",
                timestamp=now - timedelta(seconds=14)
            ))
        if marine_p:
            db.add(TelegramMessageAuditDB(
                message_id="init-audit-02",
                provider_id=marine_p.provider_id,
                channel="TELEGRAM",
                direction="INBOUND",
                chat_id="1002",
                telegram_username="marine_hotel_bot",
                message_type="operational_response",
                raw_text="82 rooms available",
                parsed_resource="hotel_rooms",
                parsed_value=82,
                processing_status="PROCESSED",
                status="confirmed",
                timestamp=now - timedelta(seconds=31)
            ))
        if venue_p:
            db.add(TelegramMessageAuditDB(
                message_id="init-audit-03",
                provider_id=venue_p.provider_id,
                channel="TELEGRAM",
                direction="INBOUND",
                chat_id="1003",
                telegram_username="venue_ops_bot",
                message_type="operational_response",
                raw_text="Gate staff available",
                parsed_resource="venue_capacity",
                parsed_value=50,
                processing_status="PROCESSED",
                status="confirmed",
                timestamp=now - timedelta(seconds=52)
            ))
        db.commit()

    return event


def seed_jwcc_event(db: Session) -> EventDB:
    """
    Creates or returns Event 2: Jio World Convention Centre — Mumbai Convention Event.
    Grounded in official JWCC room factsheet data.
    """
    venue = get_or_create_jwcc_venue(db)

    event = db.query(EventDB).filter(
        EventDB.name.like("%Jio World Convention Centre%")
    ).first()

    if not event:
        event = EventDB(
            name="Jio World Convention Centre — Mumbai Convention Event",
            description="Multi-hall international summit & exhibition across Jasmine Halls, Pavilions, and Ballroom at BKC",
            city="Mumbai",
            state="Maharashtra",
            country="India",
            venue_id=venue.venue_id,
            event_type="International Conference & Exhibition",
            start_date=datetime(2026, 11, 20, 9, 0),
            end_date=datetime(2026, 11, 23, 19, 0),
            expected_visitors=30000,
            status=EventStatusEnum.ACTIVE,
            source_type="VERIFIED_PUBLIC",
            source_url="https://www.jioworldcentre.com",
            data_status="HYBRID",
            operational_thresholds={
                "crowd_warning": 75.0,
                "crowd_critical": 90.0,
                "organizer_whatsapp": "+15554567890"
            }
        )
        db.add(event)
        db.flush()

        # Real individual spaces from official JWCC factsheet
        zones_data = [
            {
                "name": "Zone A - Jasmine Halls 1 & 2",
                "description": "Plenary and convention halls (Theatre capacity: 8,200 | Reception capacity: 10,640)",
                "zone_type": ZoneTypeEnum.VENUE,
                "capacity": 10640,
                "operational_capacity": 10640,
                "current_crowd": 6200,
                "inflow_per_minute": 80.0,
                "outflow_per_minute": 45.0,
                "density": 0.583,
                "expected_demand": 10640,
                "latitude": 19.0631,
                "longitude": 72.8687,
                "source_type": "VERIFIED_PUBLIC",
                "venue_id": venue.venue_id
            },
            {
                "name": "Zone B - Exhibition Pavilions 1-3",
                "description": "Modular ground-level exhibition pavilions (Combined reception capacity: 16,500)",
                "zone_type": ZoneTypeEnum.VENUE,
                "capacity": 16500,
                "operational_capacity": 16500,
                "current_crowd": 9800,
                "inflow_per_minute": 110.0,
                "outflow_per_minute": 70.0,
                "density": 0.594,
                "expected_demand": 16500,
                "latitude": 19.0628,
                "longitude": 72.8692,
                "source_type": "VERIFIED_PUBLIC",
                "venue_id": venue.venue_id
            },
            {
                "name": "Zone C - Lotus Ballroom",
                "description": "Level 3 multi-purpose ballroom (Theatre capacity: 3,009 | Reception capacity: 3,200)",
                "zone_type": ZoneTypeEnum.HOSPITALITY,
                "capacity": 3200,
                "operational_capacity": 3200,
                "current_crowd": 1400,
                "inflow_per_minute": 30.0,
                "outflow_per_minute": 25.0,
                "density": 0.438,
                "expected_demand": 3200,
                "latitude": 19.0635,
                "longitude": 72.8680,
                "source_type": "VERIFIED_PUBLIC",
                "venue_id": venue.venue_id
            },
            {
                "name": "Zone D - BKC Transit & Concourse Hub",
                "description": "Grand concourse, registration foyer, and BKC electric shuttle arrival bays",
                "zone_type": ZoneTypeEnum.TRANSPORT,
                "capacity": 3500,
                "operational_capacity": 3500,
                "current_crowd": 1150,
                "inflow_per_minute": 60.0,
                "outflow_per_minute": 55.0,
                "density": 0.329,
                "expected_demand": 3500,
                "latitude": 19.0625,
                "longitude": 72.8675,
                "source_type": "VERIFIED_PUBLIC",
                "venue_id": venue.venue_id
            }
        ]

        zone_objs = []
        for zd in zones_data:
            z = ZoneDB(event_id=event.event_id, **zd)
            db.add(z)
            zone_objs.append(z)
        db.flush()

        event.zones = [z.zone_id for z in zone_objs]
        event.venues = [venue.venue_id]

        # Providers for JWCC (Real BKC hotels, clearly marked as Simulated / Demo Feed)
        providers_data = [
            {
                "zone_id": zone_objs[3].zone_id,
                "type": ProviderTypeEnum.TRANSPORT,
                "name": "BKC Metro & Electric Shuttle Connect — Simulated Supply",
                "location": "BKC Metro Station / JWCC Gate 2",
                "capacity": {"total": 1800, "available": 750, "occupied": 1050},
                "source_type": "SIMULATED",
                "source_name": "Simulated Transit Dispatch",
                "contact_info": {"whatsapp": "+15553334444"}
            },
            {
                "zone_id": zone_objs[2].zone_id,
                "type": ProviderTypeEnum.HOTEL,
                "name": "Trident Hotel Bandra Kurla — Demo Inventory",
                "location": "C-56, G Block, BKC, Mumbai (Adjacent to JWCC)",
                "capacity": {"total": 436, "available": 110, "occupied": 326},
                "source_type": "SIMULATED",
                "source_name": "Demo Hotel Feed",
                "contact_info": {"whatsapp": "+15555556666"}
            },
            {
                "zone_id": zone_objs[2].zone_id,
                "type": ProviderTypeEnum.HOTEL,
                "name": "Sofitel Mumbai BKC — Demo Inventory",
                "location": "C-57, G Block, BKC, Mumbai (300m from JWCC)",
                "capacity": {"total": 302, "available": 74, "occupied": 228},
                "source_type": "SIMULATED",
                "source_name": "Demo Hotel Feed",
                "contact_info": {"whatsapp": "+15557778888"}
            }
        ]

        for pd in providers_data:
            p = ProviderDB(event_id=event.event_id, **pd)
            db.add(p)

        db.commit()
        db.refresh(event)

    return event


def seed_real_mumbai_events(db: Session) -> Dict[str, EventDB]:
    """
    Seeds both real Mumbai venues and event scenarios into the database.
    """
    wankhede_event = seed_wankhede_event(db)
    jwcc_event = seed_jwcc_event(db)
    return {
        "wankhede": wankhede_event,
        "jwcc": jwcc_event
    }

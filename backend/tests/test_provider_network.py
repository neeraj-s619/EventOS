"""
Phase 8: Provider Network Hardening Tests

Tests provider network functionality:
- HOTEL: available rooms, zero rooms, capacity update, stale update
- TRANSPORT: available capacity, zero capacity, capacity update
- VENUE: available capacity, occupied capacity, additional gates/actions
- Provider unavailable/offline
- Multiple providers in the same zone
- Provider updates reflected in Unified Event State
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import init_db, get_db
from app.models.database import (
    EventDB, ZoneDB, ZoneCrowdStateDB, ProviderDB, ProviderTypeEnum,
    ProviderStatusEnum
)
from datetime import datetime


def create_test_scenario(db):
    """Create a complete test scenario with multiple providers."""
    from app.core.database import init_db
    init_db()
    
    event = EventDB(
        name="Provider Test Event",
        start_date=datetime(2026, 1, 10),
        end_date=datetime(2026, 1, 15),
        expected_visitors=100000,
        operational_thresholds={
            "crowd_warning": 70.0,
            "crowd_critical": 85.0,
        },
        schedule=[]
    )
    db.add(event)
    db.flush()
    
    # Zone A: Venue zone
    zone_a = ZoneDB(
        event_id=event.event_id,
        name="Zone A Venue",
        zone_type="venue",
        capacity=50000,
        current_crowd=40000,
        inflow_per_minute=2000,
        outflow_per_minute=1500,
        density=40000/50000,
    )
    db.add(zone_a)
    db.flush()
    
    # Zone B: Hospitality zone
    zone_b = ZoneDB(
        event_id=event.event_id,
        name="Zone B Hospitality",
        zone_type="hospitality",
        capacity=25000,
        current_crowd=5000,
        inflow_per_minute=200,
        outflow_per_minute=150,
        density=5000/25000,
    )
    db.add(zone_b)
    db.flush()
    
    # Zone C: Transport zone
    zone_c = ZoneDB(
        event_id=event.event_id,
        name="Zone C Transport",
        zone_type="transport",
        capacity=20000,
        current_crowd=3000,
        inflow_per_minute=300,
        outflow_per_minute=250,
        density=3000/20000,
    )
    db.add(zone_c)
    db.flush()
    
    # Add providers
    # Hotels in Zone B
    hotel1 = ProviderDB(
        event_id=event.event_id,
        zone_id=zone_b.zone_id,
        type=ProviderTypeEnum.HOTEL,
        name="Hotel Grand",
        capacity={"total": 300, "available": 150, "occupied": 150},
        status="ACTIVE",
        contact_info={"whatsapp": "+1234567890", "phone": "+1234567890"}
    )
    hotel2 = ProviderDB(
        event_id=event.event_id,
        zone_id=zone_b.zone_id,
        type=ProviderTypeEnum.HOTEL,
        name="Hotel Budget",
        capacity={"total": 200, "available": 50, "occupied": 150},
        status="ACTIVE",
        contact_info={"whatsapp": "+1234567891"}
    )
    hotel3 = ProviderDB(
        event_id=event.event_id,
        zone_id=zone_b.zone_id,
        type=ProviderTypeEnum.HOTEL,
        name="Hotel Closed",
        capacity={"total": 100, "available": 0, "occupied": 100},
        status="INACTIVE",
        contact_info={"whatsapp": "+1234567893"}
    )
    
    # Transport in Zone C
    transport1 = ProviderDB(
        event_id=event.event_id,
        zone_id=zone_c.zone_id,
        type=ProviderTypeEnum.TRANSPORT,
        name="Metro Line 1",
        capacity={"total": 2000, "available": 1500, "occupied": 500},
        status="ACTIVE",
        contact_info={"whatsapp": "+1234567892"}
    )
    transport2 = ProviderDB(
        event_id=event.event_id,
        zone_id=zone_c.zone_id,
        type=ProviderTypeEnum.TRANSPORT,
        name="Bus Route 10",
        capacity={"total": 800, "available": 0, "occupied": 800},
        status="ACTIVE",
        contact_info={"whatsapp": "+1234567894"}
    )
    transport3 = ProviderDB(
        event_id=event.event_id,
        zone_id=zone_c.zone_id,
        type=ProviderTypeEnum.TRANSPORT,
        name="Shuttle Service",
        capacity={"total": 600, "available": 300, "occupied": 300},
        status="INACTIVE",
        contact_info={"whatsapp": "+1234567895"}
    )
    
    # Venues in Zone A
    venue1 = ProviderDB(
        event_id=event.event_id,
        zone_id=zone_a.zone_id,
        type=ProviderTypeEnum.VENUE,
        name="Main Stadium",
        capacity={"total": 50000, "available": 10000, "occupied": 40000},
        status="ACTIVE",
        contact_info={"whatsapp": "+1234567896"}
    )
    venue2 = ProviderDB(
        event_id=event.event_id,
        zone_id=zone_a.zone_id,
        type=ProviderTypeEnum.VENUE,
        name="Indoor Arena",
        capacity={"total": 15000, "available": 2000, "occupied": 13000},
        status="ACTIVE",
        contact_info={"whatsapp": "+1234567897"}
    )
    
    all_providers = [hotel1, hotel2, hotel3, transport1, transport2, transport3, venue1, venue2]
    
    for p in [zone_a, zone_b, zone_c]:
        p.providers = []
    
    all_providers_db = [hotel1, hotel2, hotel3, transport1, transport2, transport3, venue1, venue2]
    for p in all_providers_db:
        p.zone_id = zone_b.zone_id if p.type == ProviderTypeEnum.HOTEL else (zone_c.zone_id if p.type == ProviderTypeEnum.TRANSPORT else zone_a.zone_id)
        p.event_id = event.event_id
    
    db.add_all(all_providers_db)
    db.commit()
    
    return event, zone_a, zone_b, zone_c


def setup_environment():
    init_db()
    db = next(get_db())
    return db


def test_hotel_provider():
    """Test HOTEL provider functionality."""
    print("  Testing HOTEL provider...")
    
    db = setup_environment()
    
    try:
        event, zone_a, zone_b, zone_c = create_test_scenario(db)
        
        # Test 1: Hotel with available rooms - query by specific name
        hotel = db.query(ProviderDB).filter(
            ProviderDB.event_id == event.event_id,
            ProviderDB.type == ProviderTypeEnum.HOTEL,
            ProviderDB.status == ProviderStatusEnum.ACTIVE,
            ProviderDB.name == "Hotel Grand"
        ).first()
        
        assert hotel is not None
        assert hotel.capacity["available"] > 0
        assert hotel.capacity["total"] == hotel.capacity["available"] + hotel.capacity["occupied"]
        
        print(f"    Hotel: {hotel.name}, Available: {hotel.capacity['available']}/{hotel.capacity['total']}")
        
        # Test 2: Hotel with zero available rooms
        full_hotel = db.query(ProviderDB).filter(
            ProviderDB.name == "Hotel Closed"
        ).first()
        
        assert full_hotel is not None
        assert full_hotel.capacity["available"] == 0
        assert full_hotel.status == ProviderStatusEnum.INACTIVE
        
        print(f"    Full hotel: {full_hotel.name}, Available: {full_hotel.capacity['available']}")
        
        # Test 3: Capacity update
        original_available = hotel.capacity["available"]
        hotel.capacity = {"total": 300, "available": 100, "occupied": 200}
        hotel.last_updated = datetime.utcnow()
        db.commit()
        
        db.refresh(hotel)
        assert hotel.capacity["available"] == 100
        assert hotel.capacity["occupied"] == 200
        
        print(f"    Updated hotel: {hotel.name}, Available: {hotel.capacity['available']}")
        
        # Test 4: Stale update detection (simulated)
        old_update = hotel.last_updated
        hotel.capacity["available"] = 80
        hotel.last_updated = datetime.utcnow()
        db.commit()
        
        db.refresh(hotel)
        assert hotel.last_updated > old_update
        
        print(f"    Stale update detected: last_updated changed")
        
        # Test 5: Contact info
        assert hotel.contact_info is not None
        assert "whatsapp" in hotel.contact_info
        
        print(f"    Contact info: {hotel.contact_info}")
        
        print(f"    Status: PASS")
        return True
        
    except Exception as e:
        print(f"    Status: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_transport_provider():
    """Test TRANSPORT provider functionality."""
    print("  Testing TRANSPORT provider...")
    
    db = setup_environment()
    
    try:
        event, zone_a, zone_b, zone_c = create_test_scenario(db)
        
        # Test 1: Transport with available capacity - query by specific name
        transport = db.query(ProviderDB).filter(
            ProviderDB.event_id == event.event_id,
            ProviderDB.type == ProviderTypeEnum.TRANSPORT,
            ProviderDB.status == ProviderStatusEnum.ACTIVE,
            ProviderDB.name == "Metro Line 1"
        ).first()
        
        assert transport is not None
        assert transport.capacity["available"] > 0
        
        print(f"    Transport: {transport.name}, Available: {transport.capacity['available']}/{transport.capacity['total']}")
        
        # Test 2: Transport with zero capacity
        full_transport = db.query(ProviderDB).filter(
            ProviderDB.name == "Bus Route 10"
        ).first()
        
        assert full_transport is not None
        assert full_transport.capacity["available"] == 0
        
        print(f"    Full transport: {full_transport.name}, Available: {full_transport.capacity['available']}")
        
        # Test 3: Inactive transport
        inactive_transport = db.query(ProviderDB).filter(
            ProviderDB.name == "Shuttle Service"
        ).first()
        
        assert inactive_transport is not None
        assert inactive_transport.status == ProviderStatusEnum.INACTIVE
        
        print(f"    Inactive transport: {inactive_transport.name}")
        
        # Test 4: Capacity update
        original_available = transport.capacity["available"]
        transport.capacity = {"total": 2000, "available": 1000, "occupied": 1000}
        transport.last_updated = datetime.utcnow()
        db.commit()
        
        db.refresh(transport)
        assert transport.capacity["available"] == 1000
        
        print(f"    Updated transport: {transport.name}, Available: {transport.capacity['available']}")
        
        # Test 5: Contact info
        assert transport.contact_info is not None
        assert "whatsapp" in transport.contact_info
        
        print(f"    Status: PASS")
        return True
        
    except Exception as e:
        print(f"    Status: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_venue_provider():
    """Test VENUE provider functionality."""
    print("  Testing VENUE provider...")
    
    db = setup_environment()
    
    try:
        event, zone_a, zone_b, zone_c = create_test_scenario(db)
        
        # Test 1: Venue with available capacity
        venue = db.query(ProviderDB).filter(
            ProviderDB.event_id == event.event_id,
            ProviderDB.type == ProviderTypeEnum.VENUE,
            ProviderDB.status == "ACTIVE"
        ).first()
        
        assert venue is not None
        assert venue.capacity["available"] > 0
        
        print(f"    Venue: {venue.name}, Available: {venue.capacity['available']}/{venue.capacity['total']}")
        
        # Test 2: Occupied capacity
        assert venue.capacity["occupied"] > 0
        assert venue.capacity["available"] + venue.capacity["occupied"] == venue.capacity["total"]
        
        print(f"    Occupied: {venue.capacity['occupied']}, Available: {venue.capacity['available']}")
        
        # Test 3: Multiple venues in same zone
        venues = db.query(ProviderDB).filter(
            ProviderDB.zone_id == zone_a.zone_id,
            ProviderDB.type == ProviderTypeEnum.VENUE
        ).all()
        
        assert len(venues) == 2
        
        print(f"    Venues in zone: {[v.name for v in venues]}")
        
        # Test 4: Additional gates action
        # (This is tested in orchestration tests)
        
        print(f"    Status: PASS")
        return True
        
    except Exception as e:
        print(f"    Status: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_provider_unavailable():
    """Test provider unavailable/offline handling."""
    print("  Testing provider unavailable/offline...")
    
    db = setup_environment()
    
    try:
        event, zone_a, zone_b, zone_c = create_test_scenario(db)
        
        # Find an active provider and make it INACTIVE
        provider = db.query(ProviderDB).filter(
            ProviderDB.event_id == event.event_id,
            ProviderDB.status == "ACTIVE"
        ).first()
        
        assert provider is not None
        provider.status = "INACTIVE"
        db.commit()
        
        # Verify it's no longer returned in ACTIVE queries
        active_providers = db.query(ProviderDB).filter(
            ProviderDB.event_id == event.event_id,
            ProviderDB.status == "ACTIVE"
        ).all()
        
        assert provider not in active_providers
        
        print(f"    Provider {provider.name} marked INACTIVE")
        print(f"    Active providers count: {len(active_providers)}")
        
        print(f"    Status: PASS")
        return True
        
    except Exception as e:
        print(f"    Status: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_multiple_providers_same_zone():
    """Test multiple providers in the same zone."""
    print("  Testing multiple providers in same zone...")
    
    db = setup_environment()
    
    try:
        event, zone_a, zone_b, zone_c = create_test_scenario(db)
        
        # Zone B should have 3 hotels
        hotels = db.query(ProviderDB).filter(
            ProviderDB.zone_id == zone_b.zone_id,
            ProviderDB.type == ProviderTypeEnum.HOTEL
        ).all()
        
        assert len(hotels) == 3
        
        # Zone C should have 3 transports
        transports = db.query(ProviderDB).filter(
            ProviderDB.zone_id == zone_c.zone_id,
            ProviderDB.type == ProviderTypeEnum.TRANSPORT
        ).all()
        
        assert len(transports) == 3
        
        # Zone A should have 2 venues
        venues = db.query(ProviderDB).filter(
            ProviderDB.zone_id == zone_a.zone_id,
            ProviderDB.type == ProviderTypeEnum.VENUE
        ).all()
        
        assert len(venues) == 2
        
        # Total providers
        total = db.query(ProviderDB).filter(
            ProviderDB.event_id == event.event_id
        ).count()
        
        assert total == 8
        
        print(f"    Hotels: {len(hotels)}, Transports: {len(transports)}, Venues: {len(venues)}")
        print(f"    Total providers: {total}")
        
        print(f"    Status: PASS")
        return True
        
    except Exception as e:
        print(f"    Status: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_provider_updates_unified_state():
    """Test provider updates reflected in Unified Event State."""
    print("  Testing provider updates reflected in Unified Event State...")
    
    db = setup_environment()
    
    try:
        event, zone_a, zone_b, zone_c = create_test_scenario(db)
        
        # Get initial unified state
        from app.main import get_unified_state
        unified = get_unified_state(event.event_id, db)
        
        zone_b_state = unified.zones[zone_b.zone_id]
        initial_hotel_cap = zone_b_state["hotel_capacity"]
        
        print(f"    Initial hotel capacity in Zone B: {initial_hotel_cap}")
        
        # Update a specific hotel's capacity (Hotel Grand)
        hotel = db.query(ProviderDB).filter(
            ProviderDB.zone_id == zone_b.zone_id,
            ProviderDB.type == ProviderTypeEnum.HOTEL,
            ProviderDB.status == ProviderStatusEnum.ACTIVE,
            ProviderDB.name == "Hotel Grand"
        ).first()
        
        assert hotel is not None
        original_available = hotel.capacity["available"]
        hotel.capacity = {"total": hotel.capacity["total"], "available": hotel.capacity["available"] + 50, "occupied": hotel.capacity["occupied"] - 50}
        hotel.last_updated = datetime.utcnow()
        db.commit()
        
        # Get updated unified state
        unified2 = get_unified_state(event.event_id, db)
        zone_b_state2 = unified2.zones[zone_b.zone_id]
        updated_hotel_cap = zone_b_state2["hotel_capacity"]
        
        print(f"    Updated hotel capacity in Zone B: {updated_hotel_cap}")
        assert updated_hotel_cap == initial_hotel_cap + 50
        
        print(f"    Unified state updated correctly")
        
        print(f"    Status: PASS")
        return True
        
    except Exception as e:
        print(f"    Status: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_provider_stale_update():
    """Test stale provider update detection."""
    print("  Testing stale provider update detection...")
    
    db = setup_environment()
    
    try:
        event, zone_a, zone_b, zone_c = create_test_scenario(db)
        
        provider = db.query(ProviderDB).filter(
            ProviderDB.event_id == event.event_id,
            ProviderDB.status == "ACTIVE"
        ).first()
        
        old_update = provider.last_updated
        
        # Simulate time passing
        import time
        time.sleep(0.1)
        
        provider.capacity["available"] = 100
        provider.last_updated = datetime.utcnow()
        db.commit()
        
        db.refresh(provider)
        
        assert provider.last_updated > old_update
        
        print(f"    Stale update detected: last_updated changed from {old_update} to {provider.last_updated}")
        
        print(f"    Status: PASS")
        return True
        
    except Exception as e:
        print(f"    Status: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_provider_contact_info():
    """Test provider contact information."""
    print("  Testing provider contact information...")
    
    db = setup_environment()
    
    try:
        event, zone_a, zone_b, zone_c = create_test_scenario(db)
        
        providers = db.query(ProviderDB).filter(
            ProviderDB.event_id == event.event_id,
            ProviderDB.status == "ACTIVE"  # Only test ACTIVE providers
        ).all()
        
        for p in providers:
            assert p.contact_info is not None, f"Provider {p.name} missing contact_info"
            assert "whatsapp" in p.contact_info or "phone" in p.contact_info, \
                f"Provider {p.name} missing WhatsApp/phone"
        
        print(f"    All {len(providers)} active providers have valid contact info")
        
        # Test WhatsApp message format
        for p in providers:
            if "whatsapp" in p.contact_info:
                whatsapp = p.contact_info["whatsapp"]
                assert whatsapp.startswith("+"), f"Invalid WhatsApp format: {whatsapp}"
        
        print(f"    Status: PASS")
        return True
        
    except Exception as e:
        print(f"    Status: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    from app.core.database import init_db, get_db
    from app.models.database import (
        EventDB, ZoneDB, ZoneCrowdStateDB, ProviderDB, ProviderTypeEnum,
        ProviderStatusEnum
    )
    from datetime import datetime
    
    results = []
    results.append(("HOTEL provider", test_hotel_provider()))
    results.append(("TRANSPORT provider", test_transport_provider()))
    results.append(("VENUE provider", test_venue_provider()))
    results.append(("Provider unavailable", test_provider_unavailable()))
    results.append(("Multiple providers same zone", test_multiple_providers_same_zone()))
    results.append(("Provider updates unified state", test_provider_updates_unified_state()))
    results.append(("Stale update detection", test_provider_stale_update()))
    results.append(("Provider contact info", test_provider_contact_info()))
    
    print("\n" + "=" * 60)
    print("PHASE 8 SUMMARY")
    print("=" * 60)
    for name, passed in results:
        print(f"  {name}: {'PASS' if passed else 'FAIL'}")
    
    all_passed = all(passed for _, passed in results)
    print(f"\nOverall: {'ALL PASSED' if all_passed else 'SOME FAILED'}")
    sys.exit(0 if all_passed else 1)
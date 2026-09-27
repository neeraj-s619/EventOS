"""
Phase 4: Orchestration Complete Coverage Tests

Tests all recommendation types and edge cases:
1. demand_redirect
2. increase_transport  
3. venue_action
4. No alternative capacity
5. Multiple zones simultaneously at risk
6. Required provider unavailable
7. No risk -> zero recommendations
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import init_db, get_db
from app.services.orchestration import OrchestrationEngine
from app.services.risk import RiskEngine
from app.services.forecasting import DemandForecaster
from app.models.database import (
    EventDB, ZoneDB, ZoneCrowdStateDB, ProviderDB, ProviderTypeEnum,
    RiskLevelEnum
)
from datetime import datetime


def create_test_event(db):
    event = EventDB(
        name="Orchestration Test Event",
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
    return event


def create_zone_with_state(db, event_id, name, zone_type, capacity, crowd, inflow, outflow, providers=None):
    """Create zone with crowd state."""
    zone = ZoneDB(
        event_id=event_id,
        name=name,
        zone_type=zone_type,
        capacity=capacity,
        current_crowd=crowd,
        inflow_per_minute=inflow,
        outflow_per_minute=outflow,
        density=crowd / capacity if capacity > 0 else 0,
    )
    db.add(zone)
    db.flush()
    
    crowd_state = ZoneCrowdStateDB(
        zone_id=zone.zone_id,
        people_count=crowd,
        inflow_per_minute=inflow,
        outflow_per_minute=outflow,
        density=crowd / capacity if capacity > 0 else 0,
        movement_direction="N",
        movement_speed=1.0,
        source="test"
    )
    db.add(crowd_state)
    
    if providers:
        for p in providers:
            p.zone_id = zone.zone_id
            p.event_id = event_id
            db.add(p)
    
    return zone


def setup_environment():
    init_db()
    db = next(get_db())
    return db


def test_demand_redirect():
    """Test demand_redirect recommendation with spare capacity."""
    print("  Testing demand_redirect...")
    
    db = setup_environment()
    orchestration = OrchestrationEngine(db)
    risk_engine = RiskEngine(db)
    
    try:
        event = create_test_event(db)
        
        # Zone A: Overloaded
        zone_a = create_zone_with_state(db, event.event_id, "Zone A Overloaded", "venue",
                                       50000, 48000, 4000, 500)
        
        # Zone B: Spare capacity (hospitality)
        hotel_b = ProviderDB(
            event_id=event.event_id,
            zone_id="",  # will be set after zone creation
            type=ProviderTypeEnum.HOTEL,
            name="Hotel Spare",
            capacity={"total": 300, "available": 150, "occupied": 150},
            status="ACTIVE"
        )
        zone_b = create_zone_with_state(db, event.event_id, "Zone B Spare", "hospitality",
                                       30000, 5000, 100, 150, [hotel_b])
        
        # Zone C: Transport
        transport_c = ProviderDB(
            event_id=event.event_id,
            zone_id="",
            type=ProviderTypeEnum.TRANSPORT,
            name="Metro Line",
            capacity={"total": 2000, "available": 1000, "occupied": 1000},
            status="ACTIVE"
        )
        zone_c = create_zone_with_state(db, event.event_id, "Zone C Transport", "transport",
                                       20000, 3000, 100, 150, [transport_c])
        
        # Update provider zone_ids
        hotel_b.zone_id = zone_b.zone_id
        transport_c.zone_id = zone_c.zone_id
        db.commit()
        
        # Run risk assessment
        risk_engine = RiskEngine(db)
        risk_engine.assess_zone_risk(zone_a.zone_id)
        risk_engine.assess_zone_risk(zone_b.zone_id)
        risk_engine.assess_zone_risk(zone_c.zone_id)
        
        # Generate recommendations
        recommendations = orchestration.generate_recommendations(event.event_id)
        
        # Should have demand_redirect
        redirect_recs = [r for r in recommendations if r["type"] == "demand_redirect"]
        assert len(redirect_recs) == 1, f"Expected 1 demand_redirect, got {len(redirect_recs)}"
        
        rec = redirect_recs[0]
        assert rec["source_zone_id"] == zone_a.zone_id
        assert rec["target_zone_id"] == zone_b.zone_id
        assert "redirect_flow" in str(rec["actions"])
        assert "update_signage" in str(rec["actions"])
        assert rec["priority"] == "high"
        
        print(f"    Source: {zone_a.name} -> Target: {zone_b.name}")
        print(f"    Actions: {rec['actions']}")
        print(f"    Required providers: {rec['required_providers']}")
        print(f"    Status: PASS")
        return True
        
    except Exception as e:
        print(f"    Status: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_increase_transport():
    """Test increase_transport recommendation with available transport in SAME zone."""
    print("  Testing increase_transport...")
    
    db = setup_environment()
    orchestration = OrchestrationEngine(db)
    risk_engine = RiskEngine(db)
    
    try:
        event = create_test_event(db)
        
        # Zone A: Overloaded with transport bottleneck, HAS transport in SAME zone
        transport_a = ProviderDB(
            event_id=event.event_id,
            zone_id="",
            type=ProviderTypeEnum.TRANSPORT,
            name="Zone A Bus Depot",
            capacity={"total": 1000, "available": 800, "occupied": 200},
            status="ACTIVE"
        )
        zone_a = create_zone_with_state(db, event.event_id, "Zone A Overloaded", "venue",
                                        50000, 48000, 4000, 500, [transport_a])
        
        # Zone B: Normal
        zone_b = create_zone_with_state(db, event.event_id, "Zone B Normal", "hospitality",
                                        30000, 10000, 100, 150)
        
        # Zone C: Normal
        zone_c = create_zone_with_state(db, event.event_id, "Zone C Normal", "transport",
                                        20000, 5000, 100, 150)
        
        db.commit()
        
        # Run risk
        risk_engine.assess_zone_risk(zone_a.zone_id)
        risk_engine.assess_zone_risk(zone_b.zone_id)
        risk_engine.assess_zone_risk(zone_c.zone_id)
        
        # Generate
        recommendations = orchestration.generate_recommendations(event.event_id)
        
        # Should have increase_transport for Zone A
        transport_recs = [r for r in recommendations if r["type"] == "increase_transport"]
        assert len(transport_recs) >= 1, f"Expected increase_transport, got {len(transport_recs)}"
        
        rec = transport_recs[0]
        assert rec["zone_id"] == zone_a.zone_id
        assert "deploy_transport" in str(rec["actions"])
        
        print(f"    Zone: {rec['zone_id']}")
        print(f"    Actions: {rec['actions']}")
        print(f"    Required providers: {rec['required_providers']}")
        print(f"    Status: PASS")
        return True
        
    except Exception as e:
        print(f"    Status: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_venue_action():
    """Test venue_action recommendation."""
    print("  Testing venue_action...")
    
    db = setup_environment()
    orchestration = OrchestrationEngine(db)
    risk_engine = RiskEngine(db)
    
    try:
        event = create_test_event(db)
        
        # Zone A: Overloaded with venue
        venue_a = ProviderDB(
            event_id=event.event_id,
            zone_id="",
            type=ProviderTypeEnum.VENUE,
            name="Main Stadium",
            capacity={"total": 50000, "available": 5000, "occupied": 45000},
            status="ACTIVE"
        )
        zone_a = create_zone_with_state(db, event.event_id, "Zone A Venue", "venue",
                                       50000, 48000, 4000, 500, [venue_a])
        
        # Zone B: Normal
        zone_b = create_zone_with_state(db, event.event_id, "Zone B Normal", "hospitality",
                                       30000, 10000, 100, 150)
        
        venue_a.zone_id = zone_a.zone_id
        db.commit()
        
        # Run risk
        risk_engine.assess_zone_risk(zone_a.zone_id)
        risk_engine.assess_zone_risk(zone_b.zone_id)
        
        # Generate
        recommendations = orchestration.generate_recommendations(event.event_id)
        
        # Should have venue_action
        venue_recs = [r for r in recommendations if r["type"] == "venue_action"]
        assert len(venue_recs) >= 1, f"Expected venue_action, got {len(venue_recs)}"
        
        rec = venue_recs[0]
        assert rec["zone_id"] == zone_a.zone_id
        assert "open_additional_gates" in str(rec["actions"]) or "restrict_entry" in str(rec["actions"])
        
        print(f"    Zone: {rec['zone_id']}")
        print(f"    Actions: {rec['actions']}")
        print(f"    Status: PASS")
        return True
        
    except Exception as e:
        print(f"    Status: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_no_alternative_capacity():
    """Test no alternative capacity -> no fake recommendations."""
    print("  Testing no alternative capacity...")
    
    db = setup_environment()
    orchestration = OrchestrationEngine(db)
    risk_engine = RiskEngine(db)
    
    try:
        event = create_test_event(db)
        
        # Zone A: Overloaded
        zone_a = create_zone_with_state(db, event.event_id, "Zone A Overloaded", "venue",
                                       50000, 48000, 4000, 500)
        
        # Zone B: ALSO overloaded (no spare)
        zone_b = create_zone_with_state(db, event.event_id, "Zone B Overloaded", "hospitality",
                                       20000, 19000, 500, 100)
        
        # Zone C: ALSO overloaded
        zone_c = create_zone_with_state(db, event.event_id, "Zone C Overloaded", "transport",
                                       15000, 14000, 1000, 50)
        
        db.commit()
        
        # Run risk
        risk_engine.assess_zone_risk(zone_a.zone_id)
        risk_engine.assess_zone_risk(zone_b.zone_id)
        risk_engine.assess_zone_risk(zone_c.zone_id)
        
        # Generate
        recommendations = orchestration.generate_recommendations(event.event_id)
        
        # Should have NO demand_redirect (no spare capacity)
        redirect_recs = [r for r in recommendations if r["type"] == "demand_redirect"]
        assert len(redirect_recs) == 0, f"Expected 0 demand_redirect, got {len(redirect_recs)}"
        
        # May have venue_action or transport if those exist
        print(f"    Total recommendations: {len(recommendations)}")
        print(f"    Demand redirects: {len(redirect_recs)} (expected 0)")
        print(f"    Status: PASS")
        return True
        
    except Exception as e:
        print(f"    Status: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_multiple_zones_at_risk():
    """Test multiple zones simultaneously at risk."""
    print("  Testing multiple zones at risk...")
    
    db = setup_environment()
    orchestration = OrchestrationEngine(db)
    risk_engine = RiskEngine(db)
    
    try:
        event = create_test_event(db)
        
        # Zone A: Critical
        zone_a = create_zone_with_state(db, event.event_id, "Zone A Critical", "venue",
                                       50000, 48000, 4000, 500)
        
        # Zone B: Warning (also overloaded)
        zone_b = create_zone_with_state(db, event.event_id, "Zone B Warning", "venue",
                                       40000, 36000, 2000, 300)
        
        # Zone C: Normal with spare
        zone_c = create_zone_with_state(db, event.event_id, "Zone C Spare", "hospitality",
                                       30000, 5000, 100, 150)
        
        db.commit()
        
        # Run risk
        risk_engine.assess_zone_risk(zone_a.zone_id)
        risk_engine.assess_zone_risk(zone_b.zone_id)
        risk_engine.assess_zone_risk(zone_c.zone_id)
        
        # Generate
        recommendations = orchestration.generate_recommendations(event.event_id)
        
        # Should have recommendations for BOTH zone_a and zone_b
        zone_a_recs = [r for r in recommendations if r.get("zone_id") == zone_a.zone_id or r.get("source_zone_id") == zone_a.zone_id]
        zone_b_recs = [r for r in recommendations if r.get("zone_id") == zone_b.zone_id or r.get("source_zone_id") == zone_b.zone_id]
        
        assert len(zone_a_recs) > 0, f"Zone A should have recommendations"
        assert len(zone_b_recs) > 0, f"Zone B should have recommendations"
        
        print(f"    Zone A recommendations: {len(zone_a_recs)}")
        print(f"    Zone B recommendations: {len(zone_b_recs)}")
        print(f"    Total: {len(recommendations)}")
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
    """Test required provider unavailable."""
    print("  Testing required provider unavailable...")
    
    db = setup_environment()
    orchestration = OrchestrationEngine(db)
    risk_engine = RiskEngine(db)
    
    try:
        event = create_test_event(db)
        
        # Zone A: Overloaded with venue
        venue_a = ProviderDB(
            event_id=event.event_id,
            zone_id="",
            type=ProviderTypeEnum.VENUE,
            name="Stadium",
            capacity={"total": 50000, "available": 5000, "occupied": 45000},
            status="INACTIVE"  # Unavailable!
        )
        zone_a = create_zone_with_state(db, event.event_id, "Zone A Venue", "venue",
                                       50000, 48000, 4000, 500, [venue_a])
        
        # Zone B: Normal
        zone_b = create_zone_with_state(db, event.event_id, "Zone B Normal", "hospitality",
                                       30000, 10000, 100, 150)
        
        venue_a.zone_id = zone_a.zone_id
        db.commit()
        
        # Run risk
        risk_engine.assess_zone_risk(zone_a.zone_id)
        risk_engine.assess_zone_risk(zone_b.zone_id)
        
        # Generate
        recommendations = orchestration.generate_recommendations(event.event_id)
        
        # Venue action should still be generated but with INACTIVE provider
        venue_recs = [r for r in recommendations if r["type"] == "venue_action"]
        
        # Should still generate recommendation (orchestration doesn't filter by provider status)
        print(f"    Recommendations generated: {len(recommendations)}")
        print(f"    Venue actions: {len(venue_recs)}")
        
        # The recommendation will include the inactive provider
        if venue_recs:
            rec = venue_recs[0]
            print(f"    Required providers: {rec['required_providers']}")
            assert venue_a.provider_id in rec['required_providers']
        
        print(f"    Status: PASS")
        return True
        
    except Exception as e:
        print(f"    Status: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_no_risk_no_recommendations():
    """Test no risk -> zero recommendations."""
    print("  Testing no risk -> zero recommendations...")
    
    db = setup_environment()
    orchestration = OrchestrationEngine(db)
    risk_engine = RiskEngine(db)
    
    try:
        event = create_test_event(db)
        
        # All zones normal
        zone_a = create_zone_with_state(db, event.event_id, "Zone A Normal", "venue",
                                       50000, 25000, 200, 150)
        zone_b = create_zone_with_state(db, event.event_id, "Zone B Normal", "hospitality",
                                       30000, 10000, 100, 150)
        zone_c = create_zone_with_state(db, event.event_id, "Zone C Normal", "transport",
                                       20000, 5000, 50, 80)
        
        db.commit()
        
        # Run risk
        risk_engine.assess_zone_risk(zone_a.zone_id)
        risk_engine.assess_zone_risk(zone_b.zone_id)
        risk_engine.assess_zone_risk(zone_c.zone_id)
        
        # Generate
        recommendations = orchestration.generate_recommendations(event.event_id)
        
        # Should have NO recommendations
        assert len(recommendations) == 0, f"Expected 0 recommendations, got {len(recommendations)}"
        
        print(f"    Recommendations: {len(recommendations)} (expected 0)")
        print(f"    Status: PASS")
        return True
        
    except Exception as e:
        print(f"    Status: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_transport_bottleneck_with_available_transport():
    """Test transport bottleneck with available transport in another zone."""
    print("  Testing transport bottleneck with available transport...")
    
    db = setup_environment()
    orchestration = OrchestrationEngine(db)
    risk_engine = RiskEngine(db)
    
    try:
        event = create_test_event(db)
        
        # Zone A: Overloaded, needs transport out
        zone_a = create_zone_with_state(db, event.event_id, "Zone A Overloaded", "venue",
                                       50000, 48000, 4000, 500)
        
        # Zone B: Spare capacity
        hotel_b = ProviderDB(
            event_id=event.event_id,
            zone_id="",
            type=ProviderTypeEnum.HOTEL,
            name="Hotel B",
            capacity={"total": 300, "available": 150, "occupied": 150},
            status="ACTIVE"
        )
        zone_b = create_zone_with_state(db, event.event_id, "Zone B Spare", "hospitality",
                                       30000, 5000, 100, 150, [hotel_b])
        
        # Zone C: Transport hub with AVAILABLE transport
        transport_c = ProviderDB(
            event_id=event.event_id,
            zone_id="",
            type=ProviderTypeEnum.TRANSPORT,
            name="Metro",
            capacity={"total": 2000, "available": 1500, "occupied": 500},
            status="ACTIVE"
        )
        zone_c = create_zone_with_state(db, event.event_id, "Zone C Transport", "transport",
                                       20000, 3000, 100, 150, [transport_c])
        
        hotel_b.zone_id = zone_b.zone_id
        transport_c.zone_id = zone_c.zone_id
        db.commit()
        
        # Run risk
        risk_engine.assess_zone_risk(zone_a.zone_id)
        risk_engine.assess_zone_risk(zone_b.zone_id)
        risk_engine.assess_zone_risk(zone_c.zone_id)
        
        # Generate
        recommendations = orchestration.generate_recommendations(event.event_id)
        
        # Should have demand_redirect with transport_available = True
        redirect_recs = [r for r in recommendations if r["type"] == "demand_redirect"]
        assert len(redirect_recs) == 1
        
        rec = redirect_recs[0]
        assert rec["transport_available"] == True, "Transport should be available"
        
        # Should also have increase_transport from Zone C
        transport_recs = [r for r in recommendations if r["type"] == "increase_transport"]
        
        print(f"    Demand redirect: {len(redirect_recs)}")
        print(f"    Increase transport: {len(transport_recs)}")
        print(f"    Transport available: {rec['transport_available']}")
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
    results = []
    results.append(("Demand Redirect", test_demand_redirect()))
    results.append(("Increase Transport", test_increase_transport()))
    results.append(("Venue Action", test_venue_action()))
    results.append(("No Alternative Capacity", test_no_alternative_capacity()))
    results.append(("Multiple Zones at Risk", test_multiple_zones_at_risk()))
    results.append(("Provider Unavailable", test_provider_unavailable()))
    results.append(("No Risk -> Zero Recs", test_no_risk_no_recommendations()))
    results.append(("Transport Bottleneck + Available", test_transport_bottleneck_with_available_transport()))
    
    print("\n" + "=" * 60)
    print("PHASE 4 SUMMARY")
    print("=" * 60)
    for name, passed in results:
        print(f"  {name}: {'PASS' if passed else 'FAIL'}")
    
    all_passed = all(passed for _, passed in results)
    print(f"\nOverall: {'ALL PASSED' if all_passed else 'SOME FAILED'}")
    sys.exit(0 if all_passed else 1)
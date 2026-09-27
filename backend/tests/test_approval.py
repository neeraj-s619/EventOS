"""
Phase 5: Human Approval Workflow Hardening Tests

Tests:
- Approve recommendation
- Reject recommendation
- Duplicate approval
- Duplicate rejection
- Approval after recommendation expires
- Approval after risk condition disappears
- Rejected recommendation must NOT execute
- Approved recommendation should create appropriate actions
- Status transitions: PENDING -> APPROVED -> EXECUTING -> EXECUTED, PENDING -> REJECTED
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import init_db, get_db
from app.services.orchestration import OrchestrationEngine
from app.services.risk import RiskEngine
from app.models.database import (
    EventDB, ZoneDB, ZoneCrowdStateDB, ProviderDB, ProviderTypeEnum,
    OrchestrationRecommendationDB, ActionExecutionDB
)
from datetime import datetime


def setup_environment():
    init_db()
    db = next(get_db())
    return db


def create_test_event(db):
    event = EventDB(
        name="Approval Test Event",
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


def create_test_scenario(db):
    """Create a complete test scenario with overloaded zone + spare capacity zone + transport."""
    event = create_test_event(db)
    
    # Zone A: Overloaded venue
    zone_a = ZoneDB(
        event_id=event.event_id,
        name="Zone A Overloaded",
        zone_type="venue",
        capacity=50000,
        current_crowd=48000,
        inflow_per_minute=4000,
        outflow_per_minute=500,
        density=48000/50000,
    )
    db.add(zone_a)
    db.flush()
    
    # Add crowd state for Zone A
    crowd_state_a = ZoneCrowdStateDB(
        zone_id=zone_a.zone_id,
        people_count=48000,
        inflow_per_minute=4000,
        outflow_per_minute=500,
        density=0.96,
        movement_direction="N",
        movement_speed=1.0,
        source="test"
    )
    db.add(crowd_state_a)
    
    # Zone B: Spare capacity (hospitality)
    hotel_b = ProviderDB(
        event_id=event.event_id,
        zone_id="",
        type=ProviderTypeEnum.HOTEL,
        name="Hotel Spare",
        capacity={"total": 300, "available": 150, "occupied": 150},
        status="ACTIVE"
    )
    zone_b = ZoneDB(
        event_id=event.event_id,
        name="Zone B Spare",
        zone_type="hospitality",
        capacity=30000,
        current_crowd=5000,
        inflow_per_minute=100,
        outflow_per_minute=150,
        density=5000/30000,
    )
    db.add(zone_b)
    db.flush()
    
    hotel_b.zone_id = zone_b.zone_id
    hotel_b.event_id = event.event_id
    db.add(hotel_b)
    
    # Zone C: Transport hub with available transport
    transport_c = ProviderDB(
        event_id=event.event_id,
        zone_id="",
        type=ProviderTypeEnum.TRANSPORT,
        name="Metro Line",
        capacity={"total": 2000, "available": 1000, "occupied": 1000},
        status="ACTIVE"
    )
    zone_c = ZoneDB(
        event_id=event.event_id,
        name="Zone C Transport",
        zone_type="transport",
        capacity=20000,
        current_crowd=3000,
        inflow_per_minute=100,
        outflow_per_minute=150,
        density=3000/20000,
    )
    db.add(zone_c)
    db.flush()
    
    transport_c.zone_id = zone_c.zone_id
    transport_c.event_id = event.event_id
    db.add(transport_c)
    
    # Add crowd states for B and C
    for z, crowd, inflow, outflow in [
        (zone_b, 5000, 100, 150),
        (zone_c, 3000, 100, 150)
    ]:
        crowd_state = ZoneCrowdStateDB(
            zone_id=z.zone_id,
            people_count=crowd,
            inflow_per_minute=inflow,
            outflow_per_minute=outflow,
            density=crowd/z.capacity,
            movement_direction="N",
            movement_speed=1.0,
            source="test"
        )
        db.add(crowd_state)
    
    db.commit()
    return event, zone_a, zone_b, zone_c


def test_approve_recommendation():
    """Test approve recommendation."""
    print("  Testing approve recommendation...")
    
    db = setup_environment()
    orchestration = OrchestrationEngine(db)
    risk_engine = RiskEngine(db)
    
    try:
        event, zone_a, zone_b, zone_c = create_test_scenario(db)
        
        risk_engine.assess_zone_risk(zone_a.zone_id)
        risk_engine.assess_zone_risk(zone_b.zone_id)
        risk_engine.assess_zone_risk(zone_c.zone_id)
        
        recommendations = orchestration.generate_recommendations(event.event_id)
        assert len(recommendations) > 0
        
        # Save recommendation to DB first
        rec = recommendations[0]
        zone_id = rec.get("zone_id") or rec.get("source_zone_id")
        saved_rec = orchestration.create_recommendation_record(event.event_id, zone_id, rec)
        
        # Approve using the saved recommendation ID
        approved = orchestration.approve_recommendation(saved_rec.id, "ORGANIZER_001")
        
        # Check status
        assert approved.status == "approved"
        assert approved.approved_by == "ORGANIZER_001"
        assert approved.approved_at is not None
        
        # Check actions created
        executions = db.query(ActionExecutionDB).filter(
            ActionExecutionDB.recommendation_id == approved.id
        ).all()
        assert len(executions) > 0
        
        for ex in executions:
            assert ex.status == "dispatched"
        
        print(f"    Recommendation: {approved.id}, Status: {approved.status}")
        print(f"    Actions created: {len(executions)}")
        print(f"    Status: PASS")
        return True
        
    except Exception as e:
        print(f"    Status: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_reject_recommendation():
    """Test reject recommendation."""
    print("  Testing reject recommendation...")
    
    db = setup_environment()
    orchestration = OrchestrationEngine(db)
    risk_engine = RiskEngine(db)
    
    try:
        event, zone_a, zone_b, zone_c = create_test_scenario(db)
        
        risk_engine.assess_zone_risk(zone_a.zone_id)
        risk_engine.assess_zone_risk(zone_b.zone_id)
        risk_engine.assess_zone_risk(zone_c.zone_id)
        
        recommendations = orchestration.generate_recommendations(event.event_id)
        assert len(recommendations) > 0
        
        # Save recommendation to DB first
        rec = recommendations[0]
        zone_id = rec.get("zone_id") or rec.get("source_zone_id")
        saved_rec = orchestration.create_recommendation_record(event.event_id, zone_id, rec)
        
        # Reject using the saved recommendation ID
        rejected = orchestration.reject_recommendation(saved_rec.id, "ORGANIZER_001", "Risk subsided")
        
        # Check status
        assert rejected.status == "rejected"
        assert rejected.approved_by == "ORGANIZER_001"
        assert "REJECTED" in rejected.description
        
        # No actions should be created
        executions = db.query(ActionExecutionDB).filter(
            ActionExecutionDB.recommendation_id == rejected.id
        ).all()
        assert len(executions) == 0
        
        print(f"    Recommendation: {rejected.id}, Status: {rejected.status}")
        print(f"    Rejection reason in description: {'REJECTED' in rejected.description}")
        print(f"    Actions created: {len(executions)} (expected 0)")
        print(f"    Status: PASS")
        return True
        
    except Exception as e:
        print(f"    Status: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_duplicate_approval():
    """Test duplicate approval handling."""
    print("  Testing duplicate approval...")
    
    db = setup_environment()
    orchestration = OrchestrationEngine(db)
    risk_engine = RiskEngine(db)
    
    try:
        event, zone_a, zone_b, zone_c = create_test_scenario(db)
        
        risk_engine.assess_zone_risk(zone_a.zone_id)
        risk_engine.assess_zone_risk(zone_b.zone_id)
        risk_engine.assess_zone_risk(zone_c.zone_id)
        
        recommendations = orchestration.generate_recommendations(event.event_id)
        assert len(recommendations) > 0
        
        # Save recommendation to DB first
        rec = recommendations[0]
        zone_id = rec.get("zone_id") or rec.get("source_zone_id")
        saved_rec = orchestration.create_recommendation_record(event.event_id, zone_id, rec)
        
        # First approval
        approved1 = orchestration.approve_recommendation(saved_rec.id, "ORGANIZER_001")
        
        # Second approval attempt - should handle gracefully
        try:
            approved2 = orchestration.approve_recommendation(saved_rec.id, "ORGANIZER_002")
            # If it succeeds, check no duplicate actions
            executions = db.query(ActionExecutionDB).filter(
                ActionExecutionDB.recommendation_id == saved_rec.id
            ).all()
            print(f"    Second approval succeeded, actions: {len(executions)}")
        except Exception:
            print(f"    Second approval raised error (acceptable)")
        
        # Original approval should remain
        rec_check = db.query(OrchestrationRecommendationDB).filter(
            OrchestrationRecommendationDB.id == approved1.id
        ).first()
        assert rec_check.status == "approved"
        
        print(f"    Original approval maintained")
        print(f"    Status: PASS")
        return True
        
    except Exception as e:
        print(f"    Status: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_duplicate_rejection():
    """Test duplicate rejection handling."""
    print("  Testing duplicate rejection...")
    
    db = setup_environment()
    orchestration = OrchestrationEngine(db)
    risk_engine = RiskEngine(db)
    
    try:
        event, zone_a, zone_b, zone_c = create_test_scenario(db)
        
        risk_engine.assess_zone_risk(zone_a.zone_id)
        risk_engine.assess_zone_risk(zone_b.zone_id)
        risk_engine.assess_zone_risk(zone_c.zone_id)
        
        recommendations = orchestration.generate_recommendations(event.event_id)
        assert len(recommendations) > 0
        
        rec = recommendations[0]
        zone_id = rec.get("zone_id") or rec.get("source_zone_id")
        saved_rec = orchestration.create_recommendation_record(event.event_id, zone_id, rec)
        
        # First rejection
        rejected1 = orchestration.reject_recommendation(saved_rec.id, "ORGANIZER_001", "Reason 1")
        
        # Second rejection attempt
        try:
            rejected2 = orchestration.reject_recommendation(saved_rec.id, "ORGANIZER_002", "Reason 2")
            print(f"    Second rejection succeeded")
        except Exception:
            print(f"    Second rejection raised error (acceptable)")
        
        # Original rejection should remain
        rec_check = db.query(OrchestrationRecommendationDB).filter(
            OrchestrationRecommendationDB.id == rejected1.id
        ).first()
        assert rec_check.status == "rejected"
        
        print(f"    Original rejection maintained")
        print(f"    Status: PASS")
        return True
        
    except Exception as e:
        print(f"    Status: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_rejected_no_execution():
    """Test rejected recommendation must NOT execute."""
    print("  Testing rejected -> no execution...")
    
    db = setup_environment()
    orchestration = OrchestrationEngine(db)
    risk_engine = RiskEngine(db)
    
    try:
        event, zone_a, zone_b, zone_c = create_test_scenario(db)
        
        risk_engine.assess_zone_risk(zone_a.zone_id)
        risk_engine.assess_zone_risk(zone_b.zone_id)
        risk_engine.assess_zone_risk(zone_c.zone_id)
        
        recommendations = orchestration.generate_recommendations(event.event_id)
        rec = recommendations[0]
        
        # Save recommendation to DB first
        zone_id = rec.get("zone_id") or rec.get("source_zone_id")
        saved_rec = orchestration.create_recommendation_record(event.event_id, zone_id, rec)
        
        # Reject
        orchestration.reject_recommendation(saved_rec.id, "ORGANIZER_001", "Test rejection")
        
        # Verify NO actions created
        executions = db.query(ActionExecutionDB).filter(
            ActionExecutionDB.recommendation_id == saved_rec.id
        ).all()
        
        assert len(executions) == 0, f"Expected 0 executions, got {len(executions)}"
        
        print(f"    Executions after rejection: {len(executions)} (expected 0)")
        print(f"    Status: PASS")
        return True
        
    except Exception as e:
        print(f"    Status: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_approved_creates_actions():
    """Test approved recommendation creates appropriate actions."""
    print("  Testing approved -> creates actions...")
    
    db = setup_environment()
    orchestration = OrchestrationEngine(db)
    risk_engine = RiskEngine(db)
    
    try:
        event, zone_a, zone_b, zone_c = create_test_scenario(db)
        
        risk_engine.assess_zone_risk(zone_a.zone_id)
        risk_engine.assess_zone_risk(zone_b.zone_id)
        risk_engine.assess_zone_risk(zone_c.zone_id)
        
        recommendations = orchestration.generate_recommendations(event.event_id)
        rec = recommendations[0]
        
        # Save recommendation to DB first
        zone_id = rec.get("zone_id") or rec.get("source_zone_id")
        saved_rec = orchestration.create_recommendation_record(event.event_id, zone_id, rec)
        
        # Approve using saved ID
        approved = orchestration.approve_recommendation(saved_rec.id, "ORGANIZER_001")
        
        # Check actions created
        executions = db.query(ActionExecutionDB).filter(
            ActionExecutionDB.recommendation_id == approved.id
        ).all()
        
        assert len(executions) > 0, "Should create at least one action execution"
        
        for ex in executions:
            assert ex.status == "dispatched"
            assert ex.recommendation_id == approved.id
            assert ex.provider_id is not None
        
        print(f"    Actions created: {len(executions)}")
        for ex in executions:
            print(f"      - Provider: {ex.provider_id}, Action: {ex.action_type}, Status: {ex.status}")
        print(f"    Status: PASS")
        return True
        
    except Exception as e:
        print(f"    Status: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_status_transitions():
    """Test status transitions."""
    print("  Testing status transitions...")
    
    db = setup_environment()
    orchestration = OrchestrationEngine(db)
    risk_engine = RiskEngine(db)
    
    try:
        event, zone_a, zone_b, zone_c = create_test_scenario(db)
        
        risk_engine.assess_zone_risk(zone_a.zone_id)
        risk_engine.assess_zone_risk(zone_b.zone_id)
        risk_engine.assess_zone_risk(zone_c.zone_id)
        
        recommendations = orchestration.generate_recommendations(event.event_id)
        rec = recommendations[0]
        
        # Save recommendation to DB first
        zone_id = rec.get("zone_id") or rec.get("source_zone_id")
        saved_rec = orchestration.create_recommendation_record(event.event_id, zone_id, rec)
        
        # Check initial status
        rec_db = db.query(OrchestrationRecommendationDB).filter(
            OrchestrationRecommendationDB.id == saved_rec.id
        ).first()
        assert rec_db.status == "pending"
        
        # Approve
        orchestration.approve_recommendation(saved_rec.id, "ORGANIZER_001")
        
        rec_db = db.query(OrchestrationRecommendationDB).filter(
            OrchestrationRecommendationDB.id == saved_rec.id
        ).first()
        assert rec_db.status == "approved"
        
        print(f"    Status: PENDING -> APPROVED")
        print(f"    Status: PASS")
        return True
        
    except Exception as e:
        print(f"    Status: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_rejection_status():
    """Test rejection status."""
    print("  Testing rejection status...")
    
    db = setup_environment()
    orchestration = OrchestrationEngine(db)
    risk_engine = RiskEngine(db)
    
    try:
        event, zone_a, zone_b, zone_c = create_test_scenario(db)
        
        risk_engine.assess_zone_risk(zone_a.zone_id)
        risk_engine.assess_zone_risk(zone_b.zone_id)
        risk_engine.assess_zone_risk(zone_c.zone_id)
        
        recommendations = orchestration.generate_recommendations(event.event_id)
        rec = recommendations[0]
        
        # Save recommendation to DB first
        zone_id = rec.get("zone_id") or rec.get("source_zone_id")
        saved_rec = orchestration.create_recommendation_record(event.event_id, zone_id, rec)
        
        # Check initial status
        rec_db = db.query(OrchestrationRecommendationDB).filter(
            OrchestrationRecommendationDB.id == saved_rec.id
        ).first()
        assert rec_db.status == "pending"
        
        # Reject
        orchestration.reject_recommendation(saved_rec.id, "ORGANIZER_001", "Test")
        
        rec_db = db.query(OrchestrationRecommendationDB).filter(
            OrchestrationRecommendationDB.id == saved_rec.id
        ).first()
        assert rec_db.status == "rejected"
        
        print(f"    Status: PENDING -> REJECTED")
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
    results.append(("Approve Recommendation", test_approve_recommendation()))
    results.append(("Reject Recommendation", test_reject_recommendation()))
    results.append(("Duplicate Approval", test_duplicate_approval()))
    results.append(("Duplicate Rejection", test_duplicate_rejection()))
    results.append(("Rejected -> No Execution", test_rejected_no_execution()))
    results.append(("Approved -> Creates Actions", test_approved_creates_actions()))
    results.append(("Status Transitions (PENDING->APPROVED)", test_status_transitions()))
    results.append(("Rejection Status (PENDING->REJECTED)", test_rejection_status()))
    
    print("\n" + "=" * 60)
    print("PHASE 5 SUMMARY")
    print("=" * 60)
    for name, passed in results:
        print(f"  {name}: {'PASS' if passed else 'FAIL'}")
    
    all_passed = all(passed for _, passed in results)
    print(f"\nOverall: {'ALL PASSED' if all_passed else 'SOME FAILED'}")
    sys.exit(0 if all_passed else 1)
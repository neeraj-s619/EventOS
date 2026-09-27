"""
EVENTOS Stress Demo Scenario

Creates a controlled high-load scenario that naturally triggers the orchestration loop:
- ZONE A (Venue): High crowd, high inflow, approaching CRITICAL threshold
- ZONE B (Hospitality): Spare capacity for redirection
- ZONE C (Transport): Available transport for intervention
"""

import sys
import os
import asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import init_db, get_db
from app.services.simulation import CrowdSimulator, ProviderSimulator
from app.services.forecasting import DemandForecaster
from app.services.risk import RiskEngine
from app.services.orchestration import OrchestrationEngine
from app.services.feedback import FeedbackLoop
from app.models.database import (
    EventDB, ZoneDB, ProviderDB, ProviderTypeEnum,
    OrchestrationRecommendationDB, ActionExecutionDB, RiskLevelEnum,
    FeedbackLoopDB
)


def create_stress_event(db):
    """Create an event with pre-configured high-stress conditions."""
    from datetime import datetime
    
    event = EventDB(
        name="Mumbai Mega Sports Event - STRESS DEMO",
        description="Controlled stress scenario for orchestration demo",
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
            {"date": "2026-01-10", "time": "18:00", "event": "Peak Match", "venue": "Venue A", "expected_attendance": 75000},
        ]
    )
    db.add(event)
    db.flush()
    
    # ZONE A - Main Venue District (HIGH STRESS)
    # Capacity: 80,000 | Need ~72,000+ crowd (90% util) for CRITICAL
    zone_a = ZoneDB(
        event_id=event.event_id,
        name="Zone A - Main Venue District",
        zone_type="venue",
        boundary={"type": "polygon", "coordinates": [[72.8, 19.0], [72.9, 19.0], [72.9, 19.1], [72.8, 19.1]]},
        capacity=80000,
        expected_demand=75000,
    )
    db.add(zone_a)
    
    # ZONE B - Hospitality District (SPARE CAPACITY)
    # Capacity: 25,000 | Low crowd, high spare capacity
    zone_b = ZoneDB(
        event_id=event.event_id,
        name="Zone B - Hospitality District",
        zone_type="hospitality",
        boundary={"type": "polygon", "coordinates": [[72.9, 19.0], [73.0, 19.0], [73.0, 19.1], [72.9, 19.1]]},
        capacity=25000,
        expected_demand=15000,
    )
    db.add(zone_b)
    
    # ZONE C - Transport Hub (AVAILABLE TRANSPORT)
    # Capacity: 15,000 | Moderate crowd, transport available
    zone_c = ZoneDB(
        event_id=event.event_id,
        name="Zone C - Transport Hub",
        zone_type="transport",
        boundary={"type": "polygon", "coordinates": [[72.8, 19.1], [72.9, 19.1], [72.9, 19.2], [72.8, 19.2]]},
        capacity=15000,
        expected_demand=10000,
    )
    db.add(zone_c)
    db.flush()
    
    event.zones = [zone_a.zone_id, zone_b.zone_id, zone_c.zone_id]
    event.venues = [zone_a.zone_id]
    
    # Providers for ZONE A (Venue)
    venue_a = ProviderDB(
        event_id=event.event_id,
        zone_id=zone_a.zone_id,
        type=ProviderTypeEnum.VENUE,
        name="Main Stadium",
        capacity={"total": 50000, "available": 5000, "occupied": 45000},
        status="ACTIVE"
    )
    venue_b = ProviderDB(
        event_id=event.event_id,
        zone_id=zone_a.zone_id,
        type=ProviderTypeEnum.VENUE,
        name="Indoor Arena",
        capacity={"total": 15000, "available": 2000, "occupied": 13000},
        status="ACTIVE"
    )
    
    # Providers for ZONE B (Hotels - SPARE CAPACITY)
    hotel1 = ProviderDB(
        event_id=event.event_id,
        zone_id=zone_b.zone_id,
        type=ProviderTypeEnum.HOTEL,
        name="Hotel Grand Palace",
        capacity={"total": 300, "available": 120, "occupied": 180},
        status="ACTIVE"
    )
    hotel2 = ProviderDB(
        event_id=event.event_id,
        zone_id=zone_b.zone_id,
        type=ProviderTypeEnum.HOTEL,
        name="Hotel Sea View",
        capacity={"total": 250, "available": 100, "occupied": 150},
        status="ACTIVE"
    )
    hotel3 = ProviderDB(
        event_id=event.event_id,
        zone_id=zone_b.zone_id,
        type=ProviderTypeEnum.HOTEL,
        name="Hotel City Center",
        capacity={"total": 400, "available": 200, "occupied": 200},
        status="ACTIVE"
    )
    hotel4 = ProviderDB(
        event_id=event.event_id,
        zone_id=zone_b.zone_id,
        type=ProviderTypeEnum.HOTEL,
        name="Budget Inn Express",
        capacity={"total": 180, "available": 80, "occupied": 100},
        status="ACTIVE"
    )
    hotel5 = ProviderDB(
        event_id=event.event_id,
        zone_id=zone_b.zone_id,
        type=ProviderTypeEnum.HOTEL,
        name="Luxury Suites Mumbai",
        capacity={"total": 200, "available": 90, "occupied": 110},
        status="ACTIVE"
    )
    
    # Providers for ZONE C (Transport - AVAILABLE)
    transport1 = ProviderDB(
        event_id=event.event_id,
        zone_id=zone_c.zone_id,
        type=ProviderTypeEnum.TRANSPORT,
        name="Metro Line 1",
        capacity={"total": 2000, "available": 1200, "occupied": 800},
        status="ACTIVE"
    )
    transport2 = ProviderDB(
        event_id=event.event_id,
        zone_id=zone_c.zone_id,
        type=ProviderTypeEnum.TRANSPORT,
        name="Bus Route 42",
        capacity={"total": 800, "available": 400, "occupied": 400},
        status="ACTIVE"
    )
    transport3 = ProviderDB(
        event_id=event.event_id,
        zone_id=zone_c.zone_id,
        type=ProviderTypeEnum.TRANSPORT,
        name="Shuttle Service A",
        capacity={"total": 600, "available": 300, "occupied": 300},
        status="ACTIVE"
    )
    transport4 = ProviderDB(
        event_id=event.event_id,
        zone_id=zone_c.zone_id,
        type=ProviderTypeEnum.TRANSPORT,
        name="Taxi Pool",
        capacity={"total": 400, "available": 200, "occupied": 200},
        status="ACTIVE"
    )
    transport5 = ProviderDB(
        event_id=event.event_id,
        zone_id=zone_c.zone_id,
        type=ProviderTypeEnum.TRANSPORT,
        name="Auto Rickshaw Stand",
        capacity={"total": 300, "available": 150, "occupied": 150},
        status="ACTIVE"
    )
    
    all_providers = [venue_a, venue_b, hotel1, hotel2, hotel3, hotel4, hotel5, 
                     transport1, transport2, transport3, transport4, transport5]
    
    for p in all_providers:
        db.add(p)
    
    db.commit()
    db.refresh(event)
    return event, [zone_a, zone_b, zone_c]


def set_stress_crowd_state(db, zones):
    """Manually set high-stress crowd state for ZONE A, normal for others."""
    from app.models.database import ZoneCrowdStateDB
    from datetime import datetime
    
    zone_a, zone_b, zone_c = zones
    
    # ZONE A: HIGH STRESS
    # Capacity 80,000 | Crowd 72,000 = 90% utilization (CRITICAL)
    # Inflow 2,500/min | Outflow 500/min | Net +2,000/min (rapid accumulation)
    zone_a.current_crowd = 72000
    zone_a.inflow_per_minute = 2500.0
    zone_a.outflow_per_minute = 500.0
    zone_a.density = 72000 / 80000
    zone_a.updated_at = datetime.utcnow()
    
    crowd_a = ZoneCrowdStateDB(
        zone_id=zone_a.zone_id,
        people_count=72000,
        inflow_per_minute=2500.0,
        outflow_per_minute=500.0,
        density=0.9,
        movement_direction="N",
        movement_speed=1.0,
        source="simulated_cctv"
    )
    
    # ZONE B: NORMAL / SPARE CAPACITY
    # Capacity 25,000 | Crowd 5,000 = 20% utilization (NORMAL)
    zone_b.current_crowd = 5000
    zone_b.inflow_per_minute = 100.0
    zone_b.outflow_per_minute = 150.0
    zone_b.density = 5000 / 25000
    zone_b.updated_at = datetime.utcnow()
    
    crowd_b = ZoneCrowdStateDB(
        zone_id=zone_b.zone_id,
        people_count=5000,
        inflow_per_minute=100.0,
        outflow_per_minute=150.0,
        density=0.2,
        movement_direction="S",
        movement_speed=1.5,
        source="simulated_cctv"
    )
    
    # ZONE C: NORMAL / TRANSPORT AVAILABLE
    # Capacity 15,000 | Crowd 3,000 = 20% utilization (NORMAL)
    zone_c.current_crowd = 3000
    zone_c.inflow_per_minute = 200.0
    zone_c.outflow_per_minute = 250.0
    zone_c.density = 3000 / 15000
    zone_c.updated_at = datetime.utcnow()
    
    crowd_c = ZoneCrowdStateDB(
        zone_id=zone_c.zone_id,
        people_count=3000,
        inflow_per_minute=200.0,
        outflow_per_minute=250.0,
        density=0.2,
        movement_direction="E",
        movement_speed=2.0,
        source="simulated_cctv"
    )
    
    db.add_all([crowd_a, crowd_b, crowd_c])
    db.commit()


def run_stress_demo():
    print("=" * 50)
    print("EVENTOS STRESS DEMO")
    print("=" * 50)
    
    # Initialize
    init_db()
    db = next(get_db())
    
    try:
        # 1. Create stress event
        print("\n[1/8] Creating stress event...")
        event, zones = create_stress_event(db)
        zone_a, zone_b, zone_c = zones
        print(f"     Event: {event.event_id} - {event.name}")
        print(f"     Zones: {len(zones)} created")
        
        # 2. Set high-stress crowd state
        print("\n[2/8] Setting crowd state...")
        set_stress_crowd_state(db, zones)
        
        # Refresh zones
        db.refresh(zone_a)
        db.refresh(zone_b)
        db.refresh(zone_c)
        
        print(f"     ZONE A: crowd={zone_a.current_crowd:,}, inflow={zone_a.inflow_per_minute:.0f}/min, "
              f"outflow={zone_a.outflow_per_minute:.0f}/min, util={zone_a.utilization:.1f}%")
        print(f"     ZONE B: crowd={zone_b.current_crowd:,}, util={zone_b.utilization:.1f}%")
        print(f"     ZONE C: crowd={zone_c.current_crowd:,}, util={zone_c.utilization:.1f}%")
        
        # 3. Demand Forecast
        print("\n[3/8] Running demand forecast...")
        forecaster = DemandForecaster(db)
        forecasts_a = forecaster.forecast_zone_demand(zone_a.zone_id, horizon_minutes=30, interval_minutes=10)
        ttt_a = forecaster.calculate_time_to_threshold(zone_a)
        
        print(f"     ZONE A Forecast:")
        for f in forecasts_a:
            print(f"       +{f['horizon_minutes']}min: {f['predicted_crowd']:,} people "
                  f"({f['predicted_utilization']:.1f}% util, conf={f['confidence']:.1f})")
        print(f"     Time to 85% threshold: {ttt_a:.1f} minutes" if ttt_a else "     Time to threshold: N/A")
        
        # 4. Risk Assessment
        print("\n[4/8] Running risk assessment...")
        risk_engine = RiskEngine(db)
        risk_a = risk_engine.assess_zone_risk(zone_a.zone_id)
        risk_b = risk_engine.assess_zone_risk(zone_b.zone_id)
        risk_c = risk_engine.assess_zone_risk(zone_c.zone_id)
        
        print(f"     ZONE A: {risk_a['current_risk']} (util={risk_a['current_utilization']:.1f}%, "
              f"predicted={risk_a['predicted_risk']}, TTT={risk_a['time_to_threshold_minutes']:.1f}min)")
        print(f"     ZONE B: {risk_b['current_risk']} (util={risk_b['current_utilization']:.1f}%)")
        print(f"     ZONE C: {risk_c['current_risk']} (util={risk_c['current_utilization']:.1f}%)")
        
        # 5. Orchestration
        print("\n[5/8] Generating orchestration recommendations...")
        orchestration = OrchestrationEngine(db)
        recommendations = orchestration.generate_recommendations(event.event_id)
        
        print(f"     Generated {len(recommendations)} recommendation(s)")
        for rec in recommendations:
            print(f"       - [{rec['type']}] {rec['description']}")
            print(f"         Priority: {rec['priority']}")
            print(f"         Target zone: {rec.get('target_zone_id', 'N/A')}")
            print(f"         Required providers: {len(rec.get('required_providers', []))}")
            for action in rec['actions']:
                print(f"         Action: {action}")
        
        # 6. Save Recommendations
        print("\n[6/8] Saving recommendations...")
        saved_recs = []
        for rec in recommendations:
            zone_id = rec.get("zone_id") or rec.get("source_zone_id")
            if zone_id:
                saved = orchestration.create_recommendation_record(event.event_id, zone_id, rec)
                saved_recs.append(saved)
                print(f"       Saved recommendation {saved.id}: {saved.recommendation_type}")
        
        # 7. Approval Workflow
        print("\n[7/8] Testing approval workflow...")
        if saved_recs:
            rec = saved_recs[0]
            approved = orchestration.approve_recommendation(rec.id, "ORGANIZER_DEMO")
            print(f"     Approved recommendation {approved.id} by {approved.approved_by}")
            
            executions = db.query(ActionExecutionDB).filter(
                ActionExecutionDB.recommendation_id == rec.id
            ).all()
            print(f"     Created {len(executions)} action execution(s):")
            for ex in executions:
                print(f"       - {ex.provider_id}: {ex.action_type} (status: {ex.status})")
        else:
            print("     No recommendations to approve")
        
        # 8. Feedback Loop
        print("\n[8/8] Testing feedback loop...")
        feedback = FeedbackLoop(db)
        if saved_recs:
            rec = saved_recs[0]
            fb = feedback.record_pre_action_state(rec.id)
            print(f"     Recorded pre-action state (feedback_id: {fb.id})")
            
            # Simulate post-action state by updating crowd
            db.refresh(zone_a)
            zone_a.inflow_per_minute = 800.0  # Reduced inflow after redirect
            zone_a.outflow_per_minute = 800.0  # Increased outflow
            zone_a.current_crowd = 71000
            zone_a.updated_at = __import__('datetime').datetime.utcnow()
            db.commit()
            
            eval_result = asyncio.run(feedback.evaluate_action_effectiveness(rec.id))
            print(f"     Evaluation complete:")
            print(f"       Effectiveness: {eval_result['effectiveness_score']:.1f}/100")
            print(f"       Risk change: {eval_result['risk_change']}")
            print(f"       Stabilized: {eval_result['stabilized']}")
        
        # Unified State
        print("\n" + "-" * 50)
        print("UNIFIED EVENT STATE")
        print("-" * 50)
        
        # Refresh all
        for z in zones:
            db.refresh(z)
        
        providers = db.query(ProviderDB).filter(ProviderDB.event_id == event.event_id).all()
        
        print(f"\nEvent: {event.event_id} ({event.name})")
        print(f"\nZONE A - {zone_a.name}")
        print(f"  Current crowd:    {zone_a.current_crowd:,}")
        print(f"  Capacity:         {zone_a.capacity:,}")
        print(f"  Utilization:      {zone_a.utilization:.1f}%")
        print(f"  Inflow:           {zone_a.inflow_per_minute:.0f}/min")
        print(f"  Outflow:          {zone_a.outflow_per_minute:.0f}/min")
        print(f"  Net flow:         {zone_a.net_flow:.0f}/min")
        if forecasts_a:
            for f in forecasts_a:
                print(f"  +{f['horizon_minutes']} min:        {f['predicted_crowd']:,} people ({f['predicted_utilization']:.1f}% util)")
        print(f"  Risk:             {zone_a.risk_level.value.upper()}")
        print(f"  Time to threshold: {ttt_a:.1f} min" if ttt_a else "  Time to threshold: N/A")
        
        # Zone B capacity
        hotel_providers = [p for p in providers if p.zone_id == zone_b.zone_id and p.type == ProviderTypeEnum.HOTEL]
        hotel_cap = sum(p.capacity.get("available", 0) for p in hotel_providers)
        print(f"\nZONE B - {zone_b.name} (Spare Capacity)")
        print(f"  Available hotel capacity: {hotel_cap} rooms")
        
        # Zone C transport
        transport_providers = [p for p in providers if p.zone_id == zone_c.zone_id and p.type == ProviderTypeEnum.TRANSPORT]
        transport_cap = sum(p.capacity.get("available", 0) for p in transport_providers)
        print(f"\nZONE C - {zone_c.name} (Transport)")
        print(f"  Available transport capacity: {transport_cap} people/min")
        
        # Orchestration summary
        print("\n" + "-" * 50)
        print("ORCHESTRATION SUMMARY")
        print("-" * 50)
        
        if saved_recs:
            rec = saved_recs[0]
            target_zone = db.query(ZoneDB).filter(ZoneDB.zone_id == rec.target_zone_id).first()
            print(f"\nRecommendation: {rec.recommendation_type}")
            print(f"Reason: {rec.description}")
            print(f"Target zone: {target_zone.name if target_zone else rec.target_zone_id}")
            print(f"Required providers: {', '.join(rec.required_providers) if rec.required_providers else 'None'}")
            print(f"Actions:")
            for action in rec.actions:
                print(f"  - {action}")
            
            print("\n" + "-" * 50)
            print("APPROVAL")
            print("-" * 50)
            print(f"\nStatus: {rec.status.upper()}")
            print(f"Approved by: {rec.approved_by}")
            print(f"Approved at: {rec.approved_at}")
            
            executions = db.query(ActionExecutionDB).filter(
                ActionExecutionDB.recommendation_id == rec.id
            ).all()
            print("\n" + "-" * 50)
            print("EXECUTION")
            print("-" * 50)
            for ex in executions:
                print(f"\nProvider: {ex.provider_id}")
                print(f"Action: {ex.action_type}")
                print(f"Status: {ex.status}")
                print(f"Requested: {ex.requested_at}")
            
            # Feedback
            fb = db.query(FeedbackLoopDB).filter(
                FeedbackLoopDB.recommendation_id == rec.id
            ).first()
            if fb:
                print("\n" + "-" * 50)
                print("FEEDBACK")
                print("-" * 50)
                print(f"\nEffectiveness: {fb.effectiveness_score:.1f}/100")
                print(f"Risk change: {fb.risk_change}")
                print(f"Stabilized: {fb.stabilized}")
                if fb.post_action_state:
                    print(f"Post-action crowd: {fb.post_action_state.get('crowd')}")
                    print(f"Post-action risk: {fb.post_action_state.get('risk_level')}")
        
        print("\n" + "=" * 50)
        print("STRESS DEMO COMPLETE")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = run_stress_demo()
    sys.exit(0 if success else 1)
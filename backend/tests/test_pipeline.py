import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import init_db, get_db
from app.services.simulation import create_demo_event
from app.services.forecasting import DemandForecaster
from app.services.risk import RiskEngine
from app.services.orchestration import OrchestrationEngine
from app.services.feedback import FeedbackLoop
from app.models.database import EventDB, ZoneDB, ProviderDB, OrchestrationRecommendationDB, ActionExecutionDB


def test_full_pipeline():
    print("=" * 60)
    print("TESTING EVENTOS CORE PIPELINE")
    print("=" * 60)
    
    # Initialize database
    print("\n1. Initializing database...")
    init_db()
    print("   [OK] Database initialized")
    
    # Get DB session
    db = next(get_db())
    
    try:
        # Create demo event
        print("\n2. Creating demo event (Mumbai Mega Sports Event)...")
        event = create_demo_event(db)
        print(f"   [OK] Event created: {event.event_id} - {event.name}")
        print(f"   Expected visitors: {event.expected_visitors}")
        
        # Check zones
        zones = db.query(ZoneDB).filter(ZoneDB.event_id == event.event_id).all()
        print(f"\n3. Zones created: {len(zones)}")
        for zone in zones:
            print(f"   - {zone.zone_id}: {zone.name} (capacity: {zone.capacity}, type: {zone.zone_type.value})")
        
        # Check providers
        providers = db.query(ProviderDB).filter(ProviderDB.event_id == event.event_id).all()
        print(f"\n4. Providers created: {len(providers)}")
        by_type = {}
        for p in providers:
            by_type[p.type.value] = by_type.get(p.type.value, 0) + 1
        for ptype, count in by_type.items():
            print(f"   - {ptype}: {count}")
        
        # Simulate crowd data
        print("\n5. Simulating crowd data...")
        from app.services.simulation import CrowdSimulator, ProviderSimulator
        crowd_sim = CrowdSimulator(db)
        crowd_result = crowd_sim.simulate_event_scenario(event.event_id)
        print(f"   [OK] Crowd simulation: {crowd_result}")
        
        # Check updated zone states
        zones = db.query(ZoneDB).filter(ZoneDB.event_id == event.event_id).all()
        for zone in zones:
            print(f"   - {zone.name}: crowd={zone.current_crowd}, inflow={zone.inflow_per_minute:.1f}/min, outflow={zone.outflow_per_minute:.1f}/min, utilization={zone.utilization:.1f}%")
        
        # Test forecasting
        print("\n6. Testing demand forecasting...")
        forecaster = DemandForecaster(db)
        for zone in zones:
            forecasts = forecaster.forecast_zone_demand(zone.zone_id, horizon_minutes=30, interval_minutes=10)
            time_to_threshold = forecaster.calculate_time_to_threshold(zone)
            print(f"   - {zone.name}:")
            print(f"     Current: {zone.current_crowd} people ({zone.utilization:.1f}% util)")
            print(f"     Net flow: {zone.net_flow:.1f}/min")
            print(f"     Time to 85% threshold: {time_to_threshold:.1f} min" if time_to_threshold else "     Time to threshold: N/A (not accumulating)")
            for f in forecasts[:3]:
                print(f"     +{f['horizon_minutes']}min: {f['predicted_crowd']} people ({f['predicted_utilization']:.1f}% util, conf={f['confidence']:.1f})")
        
        # Test risk assessment
        print("\n7. Testing risk engine...")
        risk_engine = RiskEngine(db)
        risk_summary = risk_engine.get_risk_summary(event.event_id)
        print(f"   Overall risk: {risk_summary['overall_risk']}")
        print(f"   Risk distribution: {risk_summary['risk_distribution']}")
        for cz in risk_summary['critical_zones']:
            print(f"   CRITICAL ZONE: {cz['name']} - {cz['risk_level']} (util: {cz['utilization']:.1f}%, TTT: {cz['time_to_threshold']:.1f}min)")
        
        # Test orchestration
        print("\n8. Testing orchestration engine...")
        orchestration = OrchestrationEngine(db)
        recommendations = orchestration.generate_recommendations(event.event_id)
        print(f"   Generated {len(recommendations)} recommendations:")
        for rec in recommendations:
            print(f"   - [{rec['type']}] {rec['description']}")
            print(f"     Priority: {rec['priority']}, Actions: {len(rec['actions'])}, Providers: {len(rec['required_providers'])}")
        
        # Save recommendations
        print("\n9. Saving recommendations to database...")
        for rec in recommendations:
            zone_id = rec.get("zone_id") or rec.get("source_zone_id")
            if zone_id:
                saved = orchestration.create_recommendation_record(event.event_id, zone_id, rec)
                print(f"   [OK] Saved recommendation {saved.id}: {saved.recommendation_type}")
        
        # Test approval workflow
        print("\n10. Testing approval workflow...")
        pending_recs = db.query(OrchestrationRecommendationDB).filter(
            OrchestrationRecommendationDB.event_id == event.event_id,
            OrchestrationRecommendationDB.status == "pending"
        ).all()
        
        if pending_recs:
            rec = pending_recs[0]
            approved = orchestration.approve_recommendation(rec.id, "ORGANIZER_001")
            print(f"   [OK] Approved recommendation {approved.id} by {approved.approved_by}")
            
            # Check action executions created
            executions = db.query(ActionExecutionDB).filter(
                ActionExecutionDB.recommendation_id == rec.id
            ).all()
            print(f"   Created {len(executions)} action executions:")
            for ex in executions:
                print(f"     - {ex.provider_id}: {ex.action_type} (status: {ex.status})")
        
        # Test feedback loop
        print("\n11. Testing feedback loop...")
        feedback = FeedbackLoop(db)
        
        # Record pre-state for a recommendation
        if pending_recs:
            rec = pending_recs[1] if len(pending_recs) > 1 else pending_recs[0]
            fb = feedback.record_pre_action_state(rec.id)
            print(f"   [OK] Recorded pre-action state (feedback_id: {fb.id})")
            print(f"     Pre-state: crowd={fb.pre_action_state['crowd']}, inflow={fb.pre_action_state['inflow']:.1f}, risk={fb.pre_action_state['risk_level']}")
            
            # Simulate some time passing and re-evaluate
            print("   Simulating post-action state...")
            eval_result = feedback.evaluate_action_effectiveness(rec.id)
            print(f"   [OK] Evaluation complete:")
            print(f"     Effectiveness: {eval_result['effectiveness_score']:.1f}/100")
            print(f"     Risk change: {eval_result['risk_change']}")
            print(f"     Stabilized: {eval_result['stabilized']}")
        
        # Test unified state
        print("\n12. Testing unified event state...")
        from app.main import get_unified_state
        unified = get_unified_state(event.event_id, db)
        print(f"   [OK] Unified state generated for {len(unified.zones)} zones")
        for zone_id, data in unified.zones.items():
            print(f"   - {zone_id}: crowd={data['crowd']}, util={data['utilization']:.1f}%, risk={data['risk_level']}")
            print(f"     Hotel cap: {data['hotel_capacity']}, Transport cap: {data['transport_capacity']}, Venue cap: {data['venue_capacity']}")
        
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED [OK]")
        print("=" * 60)
        print("\nEventOS Core Pipeline is operational!")
        print(f"Event: {event.event_id} ({event.name})")
        print(f"Zones: {len(zones)}")
        print(f"Providers: {len(providers)}")
        print(f"Recommendations: {len(recommendations)}")
        
    except Exception as e:
        print(f"\n[ERROR] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()
    
    return True


import unittest


class TestPipelineSuite(unittest.TestCase):
    def test_pipeline_execution(self):
        result = test_full_pipeline()
        self.assertTrue(result)


if __name__ == "__main__":
    success = test_full_pipeline()
    sys.exit(0 if success else 1)
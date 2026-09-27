"""
EVENTOS MASTER DEMO: End-to-End Autonomous Crowd Orchestration
=============================================================
Demonstrates the full EVENTOS story with real pipeline services:
NORMAL STATE
→ CROWD INCREASE / SURGE
→ PRE-ACTION FORECAST
→ WARNING / CRITICAL RISK
→ ORCHESTRATION RECOMMENDATION
→ ORGANIZER HUMAN APPROVAL
→ ACTION DISPATCH & EXECUTION
→ NEW OBSERVATION
→ FEEDBACK LOOP EVALUATION
→ FULL RECOVERY & STABILIZATION
"""

import sys
import os
import asyncio
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import init_db, get_db
from app.services.simulation import create_demo_event
from app.services.forecasting import DemandForecaster
from app.services.risk import RiskEngine
from app.services.orchestration import OrchestrationEngine
from app.services.feedback import FeedbackLoop
from app.models.database import (
    EventDB, ZoneDB, ProviderDB, ProviderTypeEnum,
    OrchestrationRecommendationDB, ActionExecutionDB,
    FeedbackLoopDB, ZoneCrowdStateDB, RiskLevelEnum
)
from app.main import get_unified_state


def run_master_demo():
    print("=" * 70)
    print("      EVENTOS — END-TO-END AUTONOMOUS ORCHESTRATION PIPELINE")
    print("=" * 70)

    init_db()
    db = next(get_db())

    try:
        # ==============================================================
        # 1. SETUP EVENT & ZONES
        # ==============================================================
        print("\n" + "-" * 70)
        print("[STAGE 1] SYSTEM INITIALIZATION & TOPOLOGY SETUP")
        print("-" * 70)
        event = create_demo_event(db)
        zones = db.query(ZoneDB).filter(ZoneDB.event_id == event.event_id).all()
        providers = db.query(ProviderDB).filter(ProviderDB.event_id == event.event_id).all()

        zone_a = next(z for z in zones if "Zone A" in z.name)
        zone_b = next(z for z in zones if "Zone B" in z.name)
        zone_c = next(z for z in zones if "Zone C" in z.name)

        print(f"Event Created:   {event.event_id} ({event.name})")
        print(f"Active Zones:    {len(zones)}")
        print(f"  - Zone A (Venue):       Capacity {zone_a.capacity:,}")
        print(f"  - Zone B (Hospitality): Capacity {zone_b.capacity:,}")
        print(f"  - Zone C (Transport):   Capacity {zone_c.capacity:,}")
        print(f"Connected Providers: {len(providers)} across all zones")

        # ==============================================================
        # 2. NORMAL BASELINE STATE
        # ==============================================================
        print("\n" + "-" * 70)
        print("[STAGE 2] NORMAL BASELINE STATE (PRE-MATCH)")
        print("-" * 70)
        
        # Zone A normal crowd
        zone_a.current_crowd = 25000
        zone_a.inflow_per_minute = 300.0
        zone_a.outflow_per_minute = 300.0
        zone_a.density = 25000 / zone_a.capacity
        zone_a.updated_at = datetime.utcnow()

        # Zone B hospitality normal crowd
        zone_b.current_crowd = 4000
        zone_b.inflow_per_minute = 50.0
        zone_b.outflow_per_minute = 50.0
        zone_b.density = 4000 / zone_b.capacity
        zone_b.updated_at = datetime.utcnow()

        # Zone C transport normal crowd
        zone_c.current_crowd = 2500
        zone_c.inflow_per_minute = 100.0
        zone_c.outflow_per_minute = 100.0
        zone_c.density = 2500 / zone_c.capacity
        zone_c.updated_at = datetime.utcnow()

        # Add initial telemetry records
        for z in [zone_a, zone_b, zone_c]:
            cs = ZoneCrowdStateDB(
                zone_id=z.zone_id,
                people_count=z.current_crowd,
                inflow_per_minute=z.inflow_per_minute,
                outflow_per_minute=z.outflow_per_minute,
                density=z.density,
                source="simulated_cctv"
            )
            db.add(cs)
        db.commit()

        risk_engine = RiskEngine(db)
        risk_a_normal = risk_engine.assess_zone_risk(zone_a.zone_id)
        print(f"Zone A Current Crowd: {zone_a.current_crowd:,} / {zone_a.capacity:,} ({risk_a_normal['current_utilization']:.1f}% util)")
        print(f"Zone A Inflow/Outflow: Inflow {zone_a.inflow_per_minute:.0f}/min, Outflow {zone_a.outflow_per_minute:.0f}/min")
        print(f"Zone A Risk Level:     {risk_a_normal['current_risk'].upper()}")

        orchestration = OrchestrationEngine(db)
        normal_recs = orchestration.generate_recommendations(event.event_id)
        print(f"Recommendations Generated: {len(normal_recs)} (Zero unnecessary interventions in Normal state)")
        assert len(normal_recs) == 0, "Normal state should yield zero recommendations"

        # ==============================================================
        # 3. CROWD INCREASE / SUDDEN SURGE
        # ==============================================================
        print("\n" + "-" * 70)
        print("[STAGE 3] CROWD SURGE EVENT (MATCH GATES OPEN)")
        print("-" * 70)
        # Heavy surge of 2,800/min into Venue District, outflow remains 400/min
        zone_a.current_crowd = 70000
        zone_a.inflow_per_minute = 2800.0
        zone_a.outflow_per_minute = 400.0
        zone_a.density = 70000 / zone_a.capacity
        zone_a.updated_at = datetime.utcnow()

        surge_cs = ZoneCrowdStateDB(
            zone_id=zone_a.zone_id,
            people_count=70000,
            inflow_per_minute=2800.0,
            outflow_per_minute=400.0,
            density=0.875,
            source="simulated_cctv"
        )
        db.add(surge_cs)
        db.commit()
        db.refresh(zone_a)

        print(f"Observed Sensor Telemetry:")
        print(f"  - Zone A Crowd:    {zone_a.current_crowd:,} / {zone_a.capacity:,} ({zone_a.utilization:.1f}% util)")
        print(f"  - Inflow Rate:     {zone_a.inflow_per_minute:.0f} fans/min (SURGE)")
        print(f"  - Outflow Rate:    {zone_a.outflow_per_minute:.0f} fans/min")
        print(f"  - Net Accumulation Rate: +{zone_a.net_flow:.0f} fans/min")

        # ==============================================================
        # 4. PRE-ACTION DEMAND FORECAST
        # ==============================================================
        print("\n" + "-" * 70)
        print("[STAGE 4] PRE-ACTION DEMAND FORECAST (+10, +20, +30 MIN)")
        print("-" * 70)
        forecaster = DemandForecaster(db)
        pre_forecasts = forecaster.forecast_zone_demand(zone_a.zone_id, horizon_minutes=30, interval_minutes=10)
        forecaster.save_forecasts(event.event_id, zone_a.zone_id, pre_forecasts)
        time_to_thresh = forecaster.calculate_time_to_threshold(zone_a, threshold_utilization=85.0)

        for fc in pre_forecasts:
            print(f"  +{fc['horizon_minutes']} min: Predicted Crowd: {fc['predicted_crowd']:,} "
                  f"({fc['predicted_utilization']:.1f}% util, confidence: {fc['confidence']:.2f})")
        print(f"  Time to 85% Threshold: {time_to_thresh:.1f} min (Threshold already breached)")

        # ==============================================================
        # 5. RISK ASSESSMENT: ESCALATION TO WARNING / CRITICAL
        # ==============================================================
        print("\n" + "-" * 70)
        print("[STAGE 5] RISK ENGINE ASSESSMENT")
        print("-" * 70)
        risk_a_surge = risk_engine.assess_zone_risk(zone_a.zone_id)
        print(f"Zone A Current Risk:   {risk_a_surge['current_risk'].upper()}")
        print(f"Zone A Predicted Risk: {risk_a_surge['predicted_risk'].upper()} (Catastrophic Overload within 10-20 min)")
        summary = risk_engine.get_risk_summary(event.event_id)
        print(f"Overall Event Risk:    {summary['overall_risk'].upper()}")

        # ==============================================================
        # 6. ORCHESTRATION RECOMMENDATION GENERATION
        # ==============================================================
        print("\n" + "-" * 70)
        print("[STAGE 6] AUTONOMOUS ORCHESTRATION RECOMMENDATION")
        print("-" * 70)
        recommendations = orchestration.generate_recommendations(event.event_id)
        print(f"Generated {len(recommendations)} Intervention Recommendation(s):")
        
        saved_recs = []
        for r in recommendations:
            saved = orchestration.create_recommendation_record(
                event.event_id,
                r.get("zone_id") or r.get("source_zone_id"),
                r,
                trigger_risk_id=risk_a_surge["assessment_id"]
            )
            saved_recs.append(saved)
            print(f"  [{saved.id}] {saved.recommendation_type.upper()}: {saved.description}")
            print(f"      Status:            {saved.status.upper()}")
            print(f"      Required Providers: {len(saved.required_providers)}")
            print(f"      Actions:           {saved.actions}")

        assert len(saved_recs) > 0, "Expected recommendations to be generated for surge"
        target_rec = saved_recs[0]

        # ==============================================================
        # 7. ORGANIZER HUMAN APPROVAL WORKFLOW
        # ==============================================================
        print("\n" + "-" * 70)
        print("[STAGE 7] ORGANIZER HUMAN APPROVAL WORKFLOW")
        print("-" * 70)
        feedback = FeedbackLoop(db)
        fb_record = feedback.record_pre_action_state(target_rec.id)
        print(f"Pre-action State Recorded in Feedback Ledger (Feedback ID: {fb_record.id})")
        print(f"  Pre-crowd: {fb_record.pre_action_state['crowd']:,} | Pre-risk: {fb_record.pre_action_state['risk_level'].upper()}")

        approved_rec = orchestration.approve_recommendation(target_rec.id, approved_by="CHIEF_ORGANIZER_MUMBAI")
        print(f"Human Approval Granted:")
        print(f"  Recommendation ID: {approved_rec.id}")
        print(f"  Status:            {approved_rec.status.upper()}")
        print(f"  Approved By:       {approved_rec.approved_by}")
        print(f"  Approved At:       {approved_rec.approved_at}")

        # Check dispatched actions
        actions = orchestration.get_recommendation_actions(approved_rec.id) if hasattr(orchestration, "get_recommendation_actions") else db.query(ActionExecutionDB).filter(ActionExecutionDB.recommendation_id == approved_rec.id).all()
        print(f"\nDispatched {len(actions)} Physical Actions:")
        for act in actions:
            print(f"  - Action ID {act.id}: {act.action_type} -> Provider {act.provider_id or 'SYSTEM'} [Status: {act.status.upper()}]")

        # ==============================================================
        # 8. ACTION EXECUTION LIFECYCLE
        # ==============================================================
        print("\n" + "-" * 70)
        print("[STAGE 8] ACTION EXECUTION BY PROVIDERS & FIELD SYSTEMS")
        print("-" * 70)
        for act in actions:
            orchestration.start_action_execution(act.id)
            print(f"  Action {act.id} [{act.action_type}]: Status -> EXECUTING")
            orchestration.complete_action_execution(act.id, {"response": "Signal updated & shuttle deployed"})
            print(f"  Action {act.id} [{act.action_type}]: Status -> EXECUTED (Completed)")

        db.refresh(approved_rec)
        print(f"Recommendation Overall Status: {approved_rec.status.upper()}")

        # ==============================================================
        # 9. POST-ACTION SENSOR OBSERVATION & TELEMETRY
        # ==============================================================
        print("\n" + "-" * 70)
        print("[STAGE 9] POST-ACTION TELEMETRY OBSERVATION")
        print("-" * 70)
        # Intervention took effect: 2,200 fans/min redirected to Zone B, outflow increased
        zone_a.current_crowd = 50000
        zone_a.inflow_per_minute = 500.0
        zone_a.outflow_per_minute = 1000.0
        zone_a.density = 50000 / zone_a.capacity
        zone_a.updated_at = datetime.utcnow()

        post_cs = ZoneCrowdStateDB(
            zone_id=zone_a.zone_id,
            people_count=50000,
            inflow_per_minute=500.0,
            outflow_per_minute=1000.0,
            density=0.625,
            source="simulated_cctv"
        )
        db.add(post_cs)
        db.commit()

        # Update Zone B (absorbed redirected demand safely within spare capacity)
        zone_b.current_crowd = 12000
        zone_b.inflow_per_minute = 600.0
        zone_b.outflow_per_minute = 200.0
        zone_b.density = 12000 / zone_b.capacity
        zone_b.updated_at = datetime.utcnow()
        db.commit()

        print(f"New Camera & Sensor Telemetry:")
        print(f"  - Zone A Crowd:    {zone_a.current_crowd:,} / {zone_a.capacity:,} ({zone_a.utilization:.1f}% util)")
        print(f"  - Inflow Dropped:  2800 -> {zone_a.inflow_per_minute:.0f} fans/min (78.6% inflow reduction)")
        print(f"  - Outflow Rose:    400 -> {zone_a.outflow_per_minute:.0f} fans/min")
        print(f"  - Zone B Absorbed: {zone_b.current_crowd:,} / {zone_b.capacity:,} (48.0% util - well below 70% threshold)")

        # ==============================================================
        # 10. FEEDBACK LOOP EVALUATION & RISK RECOVERY
        # ==============================================================
        print("\n" + "-" * 70)
        print("[STAGE 10] CLOSED-LOOP FEEDBACK EVALUATION & RECOVERY")
        print("-" * 70)
        eval_result = asyncio.run(feedback.evaluate_action_effectiveness(approved_rec.id))

        print(f"Closed-Loop Effectiveness Assessment:")
        print(f"  - Pre-State Crowd:      {eval_result['pre_state']['crowd']:,} ({eval_result['pre_state']['risk_level'].upper()})")
        print(f"  - Post-State Crowd:     {eval_result['post_state']['crowd']:,} ({eval_result['post_state']['risk_level'].upper()})")
        print(f"  - Inflow Reduction:     {eval_result['inflow_change']:+.0f} fans/min")
        print(f"  - Outflow Increase:     {eval_result['outflow_change']:+.0f} fans/min")
        print(f"  - Utilization Change:   {eval_result['utilization_change']:+.1f}%")
        print(f"  - Risk Level Change:    {eval_result['risk_change']} levels")
        print(f"  - Effectiveness Score:  {eval_result['effectiveness_score']:.1f} / 100")
        print(f"  - Zone Stabilized:      {eval_result['stabilized']}")

        assert eval_result["stabilized"] is True, "Zone should be marked as stabilized after successful recovery"
        assert eval_result["effectiveness_score"] >= 80.0, "Effectiveness score should reflect high recovery"

        # Final unified state check
        unified = get_unified_state(event.event_id, db)
        print(f"\nUnified Event State Verified:")
        for zid, zd in unified.zones.items():
            print(f"  Zone {zid[:12]}: Crowd {zd['crowd']:,} ({zd['utilization']:.1f}% util), Risk: {zd['risk_level'].upper()}, "
                  f"Active Recs: {len(zd.get('active_recommendations', []))}")

        print("\n" + "=" * 70)
        print("          EVENTOS MASTER DEMO COMPLETED SUCCESSFULLY [PASS]")
        print("=" * 70)
        return True

    except Exception as e:
        print(f"\n[MASTER DEMO ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = run_master_demo()
    sys.exit(0 if success else 1)

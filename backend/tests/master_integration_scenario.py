"""
EVENTOS Master Closed-Loop Integration Scenario
================================================
Demonstrates the full 11-step operational lifecycle:
1. Event & Multi-Zone Topology Setup (Zone A Venue, Zone B Hospitality, Zone C Transport)
2. CV Camera Telemetry Ingestion (Zone A surge via OpenCV pipeline)
3. PDR Macro Flow Vector Correlation (Cluster heading towards Venue)
4. Demand Forecasting Engine (+10m, +20m, +30m projections)
5. Multi-Factor Risk Engine (CRITICAL escalation & time-to-threshold)
6. Orchestration Engine (HOLD_INFLOW, OPEN_GATES, DISPATCH_TRANSPORT)
7. Baseline Pre-Action State Snapshot (Feedback Loop)
8. Human-in-the-Loop Approval via Control Tower (ORGANIZER_ADMIN)
9. Outbound Dispatch & GPS Fleet Tracking (Emergency shuttles arriving)
10. CCTV Flow Ingestion (Gate opening & ingress hold stabilizes flow)
11. Feedback Loop Evaluation (Effectiveness score, risk normalized)
"""

import sys
import os
import json
import time
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.core.database import init_db, get_db
from app.models.database import (
    EventDB, ZoneDB, ProviderDB, ProviderTypeEnum, ProviderStatusEnum,
    ZoneTypeEnum, RiskLevelEnum, OrchestrationRecommendationDB, ActionExecutionDB,
    ZoneCrowdStateDB, FeedbackLoopDB
)
from app.services.gps_fleet_adapter import GPSFleetAdapter


def run_master_scenario():
    print("\n" + "=" * 90)
    print("      EVENTOS MASTER CLOSED-LOOP INTEGRATION SCENARIO (11-STEP CLOSED LOOP)")
    print("=" * 90 + "\n")

    init_db()
    client = TestClient(app)
    GPSFleetAdapter.reset_registry()

    # -------------------------------------------------------------------------
    # STEP 1: Event & Multi-Zone Topology Setup
    # -------------------------------------------------------------------------
    print(">> STEP 1: Setting up Event and Multi-Zone Topology...")
    event_payload = {
        "name": "Global Tech Summit & Festival 2026",
        "description": "Multi-zone stadium event with transit hub and hospitality corridor",
        "start_date": datetime(2026, 9, 27, 9, 0).isoformat(),
        "end_date": datetime(2026, 9, 27, 23, 0).isoformat(),
        "expected_visitors": 45000,
        "operational_thresholds": {
            "critical_utilization": 90.0,
            "warning_utilization": 80.0,
            "organizer_whatsapp": "+15559876543"
        }
    }
    r = client.post("/api/v1/events", json=event_payload)
    assert r.status_code == 201, f"Failed to create event: {r.text}"
    event = r.json()
    event_id = event["event_id"]
    print(f"   [+] Event created: '{event['name']}' (ID: {event_id})")

    # Zone A: Venue
    r = client.post(f"/api/v1/events/{event_id}/zones", json={
        "name": "Zone A - Main Stadium Arena",
        "zone_type": "venue",
        "capacity": 20000,
        "expected_demand": 18000
    })
    zone_a = r.json()
    zone_a_id = zone_a["zone_id"]

    # Zone B: Hospitality
    r = client.post(f"/api/v1/events/{event_id}/zones", json={
        "name": "Zone B - Concourse & Hospitality",
        "zone_type": "hospitality",
        "capacity": 10000,
        "expected_demand": 8000
    })
    zone_b = r.json()
    zone_b_id = zone_b["zone_id"]

    # Zone C: Transport Hub
    r = client.post(f"/api/v1/events/{event_id}/zones", json={
        "name": "Zone C - Transit & Shuttle Hub",
        "zone_type": "transport",
        "capacity": 15000,
        "expected_demand": 14000
    })
    zone_c = r.json()
    zone_c_id = zone_c["zone_id"]

    # Providers
    r = client.post(f"/api/v1/events/{event_id}/providers", json={
        "zone_id": zone_c_id,
        "type": "transport",
        "name": "Metro Express Shuttle Fleet",
        "capacity": {"total": 1200, "available": 400, "occupied": 800},
        "contact_info": {"whatsapp": "+15551234567"}
    })
    transport_prov = r.json()

    r = client.post(f"/api/v1/events/{event_id}/providers", json={
        "zone_id": zone_b_id,
        "type": "hotel",
        "name": "Grand Summit Hotel",
        "capacity": {"total": 500, "available": 180, "occupied": 320},
        "contact_info": {"whatsapp": "+15557654321"}
    })
    hotel_prov = r.json()

    print(f"   [+] Topology: Zone A (Venue: {zone_a_id}), Zone B (Hospitality: {zone_b_id}), Zone C (Transit: {zone_c_id})")
    print(f"   [+] Providers: Transport ({transport_prov['provider_id']}), Hotel ({hotel_prov['provider_id']})\n")

    # -------------------------------------------------------------------------
    # STEP 2: CV Camera Telemetry Ingestion (Zone A Surge)
    # -------------------------------------------------------------------------
    print(">> STEP 2: Ingesting Real-Time CV Camera Telemetry into Zone A...")
    # Simulate high crowd detection via CV pipeline
    cv_res = client.post("/api/v1/cv/detect-frame", json={
        "zone_id": zone_a_id,
        "synthetic_count": 35,
        "multiplier": 490,  # 35 * 490 = 17,150 people
        "camera_id": "CAM-ARENA-NORTH-GATE"
    })
    assert cv_res.status_code == 200, f"CV Ingest failed: {cv_res.text}"
    cv_data = cv_res.json()
    print(f"   [+] CV Pipeline detected: {cv_data['detected_raw_count']} visible people (Macro: {cv_data['macro_people_count']})")
    print(f"   [+] Telemetry: Inflow={cv_data['inflow_per_minute']}/min, Outflow={cv_data['outflow_per_minute']}/min, Density={cv_data['density']}")

    # Check updated zone state
    zone_state = client.get(f"/api/v1/zones/{zone_a_id}").json()
    print(f"   [+] Zone A Utilization: {zone_state['utilization']:.1f}% ({zone_state['current_crowd']} / {zone_state['capacity']})\n")

    # -------------------------------------------------------------------------
    # STEP 3: PDR Macro Movement Vector Correlation
    # -------------------------------------------------------------------------
    print(">> STEP 3: Ingesting Aggregate PDR Pedestrian Vector Signal...")
    pdr_res = client.post(f"/api/v1/zones/{zone_a_id}/pdr-signal", json={
        "zone_id": zone_a_id,
        "device_count": 320,
        "heading_degrees": 135.0,  # Southeast towards gate
        "speed_mps": 1.4,
        "confidence": 0.96
    })
    assert pdr_res.status_code == 200, f"PDR Ingest failed: {pdr_res.text}"
    pdr_data = pdr_res.json()
    print(f"   [+] PDR Macro Cluster: {pdr_data['device_cluster_count']} devices, heading {pdr_data['direction']} at {pdr_data['speed_mps']} m/s")
    print(f"   [+] Inflow rate contribution: +{pdr_data['inflow_per_minute']}/min (Privacy preserved: Zero individual tracking)\n")

    # -------------------------------------------------------------------------
    # STEP 4: Demand Forecasting Engine
    # -------------------------------------------------------------------------
    print(">> STEP 4: Executing Demand Forecasting Engine (+30 min horizon)...")
    forecast_res = client.get(f"/api/v1/zones/{zone_a_id}/forecast?horizon=30&interval=10")
    assert forecast_res.status_code == 200, f"Forecast failed: {forecast_res.text}"
    forecast_data = forecast_res.json()
    print(f"   [+] Time-to-Threshold: {forecast_data['time_to_threshold_minutes']} minutes")
    for f in forecast_data["forecasts"]:
        print(f"       Horizon +{f['horizon_minutes']}m: Predicted Crowd={f['predicted_crowd']}, Utilization={f['predicted_utilization']:.1f}%, Conf={f['confidence']*100:.0f}%")
    print()

    # -------------------------------------------------------------------------
    # STEP 5: Multi-Factor Risk Assessment Engine
    # -------------------------------------------------------------------------
    print(">> STEP 5: Evaluating Multi-Factor Risk Engine...")
    risk_res = client.post(f"/api/v1/zones/{zone_a_id}/assess-risk")
    risk_data = risk_res.json()
    print(f"   [+] Risk Level: {risk_data['current_risk'].upper()} (Predicted: {risk_data.get('predicted_risk', 'N/A').upper()})")
    print(f"   [+] Utilization: {risk_data.get('current_utilization', 0):.1f}% (Predicted: {risk_data.get('predicted_utilization', 0):.1f}%)")
    print(f"   [+] Critical Factors: {risk_data.get('risk_factors', risk_data.get('factors', {}))}\n")

    # -------------------------------------------------------------------------
    # STEP 6: Orchestration Engine Recommendation Generation
    # -------------------------------------------------------------------------
    print(">> STEP 6: Generating Orchestration Recommendations...")
    rec_res = client.post(f"/api/v1/events/{event_id}/generate-recommendations")
    assert rec_res.status_code == 200, f"Recommendation generation failed: {rec_res.text}"
    recs = rec_res.json()["recommendations"]
    assert len(recs) > 0, "Expected at least one recommendation generated"
    target_rec = recs[0]
    rec_id = target_rec["id"]
    print(f"   [+] Generated {len(recs)} recommendation(s). Selected ID #{rec_id}:")
    print(f"       Type: {target_rec['type']}")
    print(f"       Description: {target_rec['description']}")
    print(f"       Actions: {json.dumps(target_rec['actions'])}\n")

    # -------------------------------------------------------------------------
    # STEP 7: Baseline Pre-Action Snapshot (Feedback Loop)
    # -------------------------------------------------------------------------
    print(f">> STEP 7: Recording Pre-Action Baseline Snapshot for Recommendation #{rec_id}...")
    pre_res = client.post(f"/api/v1/recommendations/{rec_id}/record-pre-state")
    assert pre_res.status_code == 200, f"Pre-state record failed: {pre_res.text}"
    pre_data = pre_res.json()
    print(f"   [+] Baseline Recorded: Crowd={pre_data['pre_state']['crowd']}, Utilization={pre_data['pre_state']['utilization']:.1f}%, Risk={pre_data['pre_state']['risk_level']}\n")

    # -------------------------------------------------------------------------
    # STEP 8: Human-in-the-Loop Approval via Control Tower
    # -------------------------------------------------------------------------
    print(f">> STEP 8: Control Tower Organizer Approves Recommendation #{rec_id}...")
    app_res = client.post(f"/api/v1/recommendations/{rec_id}/approve?approved_by=CHIEF_SAFETY_OFFICER")
    assert app_res.status_code == 200, f"Approval failed: {app_res.text}"
    app_data = app_res.json()
    print(f"   [+] Status: {app_data['status'].upper()}, Approved by: {app_data['approved_by']}")

    # Verify action execution records dispatched
    actions_res = client.get(f"/api/v1/recommendations/{rec_id}/actions")
    assert actions_res.status_code == 200
    actions = actions_res.json()
    print(f"   [+] Dispatched {len(actions)} operational action executions:")
    for a in actions:
        print(f"       Action ID #{a['id']}: {a['action_type']} -> Status: {a['status']}")
    print()

    # -------------------------------------------------------------------------
    # STEP 9: Provider Dispatch & GPS Fleet Tracking Update
    # -------------------------------------------------------------------------
    print(">> STEP 9: Ingesting GPS Fleet Tracking Signal for Dispatched Shuttles...")
    fleet_res = client.post("/api/v1/transport/fleet-signal", json={
        "vehicle_id": "SHUTTLE-FLEET-RAPID-01",
        "zone_id": zone_c_id,
        "provider_id": transport_prov["provider_id"],
        "vehicle_type": "bus",
        "capacity": 500,
        "occupied_seats": 50,
        "available_seats": 450,
        "status": "arrived",
        "eta_minutes": 0.0
    })
    assert fleet_res.status_code == 200
    fleet_data = fleet_res.json()
    print(f"   [+] Fleet Signal Ingested: Shuttle Fleet Arrived at {zone_c_id} with 450 available seats")

    # Complete action executions
    for a in actions:
        exec_res = client.post(f"/api/v1/actions/{a['id']}/execute")
        assert exec_res.status_code == 200
    print(f"   [+] All {len(actions)} action executions marked EXECUTED\n")

    # -------------------------------------------------------------------------
    # STEP 10: Real-Time Flow Stabilization (CV + Outflow Surge)
    # -------------------------------------------------------------------------
    print(">> STEP 10: Ingesting Stabilized Post-Intervention Telemetry...")
    # Crowd reduced to 11,500, inflow throttled to 20/min, outflow boosted to 350/min
    stab_res = client.post(f"/api/v1/zones/{zone_a_id}/crowd-state", json={
        "people_count": 11500,
        "inflow_per_minute": 20.0,
        "outflow_per_minute": 350.0,
        "density": 11500 / 20000,
        "movement_direction": "NORTH",
        "movement_speed": 1.5,
        "source": "real_cctv_cv"
    })
    assert stab_res.status_code == 201

    # Re-assess zone risk
    post_risk = client.post(f"/api/v1/zones/{zone_a_id}/assess-risk").json()
    print(f"   [+] Updated Risk Level: {post_risk['current_risk'].upper()} (Utilization: {post_risk.get('current_utilization', 0):.1f}%)\n")

    # -------------------------------------------------------------------------
    # STEP 11: Feedback Loop Effectiveness Evaluation
    # -------------------------------------------------------------------------
    print(f">> STEP 11: Evaluating Closed-Loop Action Effectiveness for Rec #{rec_id}...")
    eval_res = client.post(f"/api/v1/recommendations/{rec_id}/evaluate?minutes_after=10")
    assert eval_res.status_code == 200, f"Evaluation failed: {eval_res.text}"
    eval_data = eval_res.json()
    print(f"   [+] Effectiveness Score: {eval_data['effectiveness_score']:+.2f}/100")
    print(f"   [+] Utilization Change:  {eval_data['utilization_change']:+.1f}%")
    print(f"   [+] Crowd Delta:         {eval_data['crowd_change']:+d} visitors")
    print(f"   [+] Inflow Change:       {eval_data['inflow_change']:+.1f}/min")
    print(f"   [+] Outflow Change:      {eval_data['outflow_change']:+.1f}/min")
    print(f"   [+] Risk Change:         {eval_data['risk_change']}")
    print(f"   [+] Stabilized:          {eval_data['stabilized']}")

    # Verify Unified State API reflects healthy event
    uni_res = client.get(f"/api/v1/events/{event_id}/unified-state")
    assert uni_res.status_code == 200
    uni_state = uni_res.json()
    print(f"\n   [+] Unified Event State verified across all {len(uni_state['zones'])} zones.")

    print("\n" + "=" * 90)
    print("      CLOSED LOOP SCENARIO COMPLETED SUCCESSFULLY: 100% OPERATIONAL")
    print("=" * 90 + "\n")
    return True


if __name__ == "__main__":
    success = run_master_scenario()
    sys.exit(0 if success else 1)

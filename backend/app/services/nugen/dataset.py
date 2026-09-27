"""
EVENTOS Domain-Specific Alignment Dataset for Nugen Intelligence.
HackCelestial 3.0 Task 2: Model Alignment & Customization.

Contains structured, verified event operations alignment pairs covering:
A. Crowd Intelligence
B. Weather Impact
C. Cascading Propagation
D. Transport Capacity Synthesis
E. Hospitality Capacity Synthesis
F. Operational Recommendations (NORMAL, WATCH, WARNING, CRITICAL)
G. Strict Human-in-the-Loop Safeguards
"""

import json
import os
from typing import List, Dict, Any


ALIGNMENT_DATASET_ITEMS: List[Dict[str, Any]] = [
    # ── CATEGORY A: CROWD INTELLIGENCE ────────────────────────────────────────
    {
        "category": "CROWD_INTELLIGENCE",
        "title": "Concourse Inflow Surge & Imminent Safety Threshold Breach",
        "input": {
            "event_name": "Mumbai Premier League — Wankhede Stadium",
            "zone_id": "ZONE-A",
            "zone_name": "Zone A - Stadium Bowl",
            "current_crowd": 23660,
            "capacity": 26000,
            "utilization_pct": 91.0,
            "inflow_per_minute": 120.0,
            "outflow_per_minute": 30.0,
            "net_flow_per_minute": 90.0,
            "sensor_telemetry": {
                "cctv_optical_flow": 123.0,
                "pdr_step_inflow": 116.0,
                "gps_fused_density": 0.78
            },
            "weather": {
                "precipitation_mm_h": 2.0,
                "temperature_c": 29.0,
                "wind_speed_kmh": 14.0
            },
            "providers_status": {
                "transport_available": 450,
                "hotel_available": 82
            }
        },
        "expected_reasoning": {
            "risk_level": "WARNING",
            "confidence": 0.92,
            "summary": "Zone A Stadium Bowl utilization reached 91% with strong net inflow (+90/min). Multi-sensor fusion (CCTV 123/m, PDR 116/m) confirms sustained positive crowd pressure. Predicted threshold breach (95%) in ~7 minutes.",
            "forecast": {
                "horizon_minutes": 10,
                "predicted_occupancy": 94.8,
                "minutes_to_threshold": 7.2
            },
            "affected_zones": ["ZONE-A", "ZONE-B"],
            "direct_impacts": [
                "Stadium Bowl concourse egress congestion",
                "North Gate entry funnel bottleneck"
            ],
            "cascading_impacts": [
                "Pressure deflection toward Zone B (Churchgate access)",
                "Elevated exit queue times at Gate 3 & Gate 4"
            ],
            "recommended_actions": [
                {
                    "action_id": "ACT-DIV-001",
                    "type": "divert_crowd",
                    "priority": "HIGH",
                    "target_zone": "ZONE-A",
                    "description": "Divert incoming pedestrian stream at Gate 3 concourse toward Zone B North Stand approach",
                    "estimated_impact": "Reduces net inflow into Stadium Bowl by 40 people/minute",
                    "human_approval_required": True
                },
                {
                    "action_id": "ACT-SIG-001",
                    "type": "update_signage",
                    "priority": "MEDIUM",
                    "target_zone": "ZONE-B",
                    "description": "Switch dynamic LED directional boards to indicate alternate concourse route",
                    "estimated_impact": "Smooths pedestrian distribution across parallel corridors",
                    "human_approval_required": False
                }
            ],
            "required_resources": [
                {
                    "resource_type": "security_marshals",
                    "required_units": 8,
                    "current_available": 24,
                    "gap": 0,
                    "urgency": "IMMEDIATE"
                }
            ],
            "weather_contribution": 0.12,
            "transport_impact": {
                "demand_increase_pct": 14.0,
                "bottleneck_risk": "MEDIUM",
                "required_additional_seats": 0,
                "recommended_route": "Churchgate Fast EMU"
            },
            "hospitality_impact": {
                "demand_increase_rooms": 0,
                "shelter_deficit": 0,
                "partner_holding_sufficient": True
            },
            "uncertainty": {"lower": 93.1, "upper": 96.2},
            "human_approval_required": True,
            "data_quality": {"missing": [], "stale": [], "conflicting": []},
            "model_metadata": {
                "model_id": "nugen-aligned-eventos-v1",
                "base_model": "nugen-base-v1",
                "model_type": "domain_aligned",
                "customized": True,
                "alignment_name": "eventos_domain_alignment_v1"
            }
        }
    },

    # ── CATEGORY B: WEATHER IMPACT ───────────────────────────────────────────
    {
        "category": "WEATHER_IMPACT",
        "title": "Sudden Heavy Rain Influx & Covered Shelter Movement Redistribution",
        "input": {
            "event_name": "Mumbai Premier League — Wankhede Stadium",
            "zone_id": "ZONE-A",
            "zone_name": "Zone A - Stadium Bowl",
            "current_crowd": 22620,
            "capacity": 26000,
            "utilization_pct": 87.0,
            "inflow_per_minute": 85.0,
            "outflow_per_minute": 40.0,
            "weather": {
                "precipitation_mm_h": 18.0,
                "rain_probability": 84,
                "wind_speed_kmh": 32.0,
                "duration_minutes": 45
            },
            "sensor_telemetry": {
                "cctv_optical_flow": 82.0,
                "pdr_step_inflow": 88.0,
                "gps_fused_density": 0.74
            },
            "providers_status": {
                "transport_available": 350,
                "hotel_available": 82
            }
        },
        "expected_reasoning": {
            "risk_level": "WARNING",
            "confidence": 0.88,
            "summary": "18 mm/h rainfall combined with 87% baseline occupancy causes sharp reduction in outdoor walking velocity and triggers rapid crowd convergence into covered concourses. High shelter demand in Stadium Bowl.",
            "forecast": {
                "horizon_minutes": 15,
                "predicted_occupancy": 93.6,
                "minutes_to_threshold": 9.5
            },
            "affected_zones": ["ZONE-A", "ZONE-C"],
            "direct_impacts": [
                "Pedestrian outdoor walking speed drops 45% on external walkways",
                "Mass movement toward covered concourses and shelter overhangs",
                "Slippage risk on unprotected stairs and external ramps"
            ],
            "cascading_impacts": [
                "Marine Drive external approach congestion due to umbrella friction",
                "Early departure wave increasing bus feeder demand at Depot 4"
            ],
            "recommended_actions": [
                {
                    "action_id": "ACT-WTH-001",
                    "type": "deploy_shelter",
                    "priority": "HIGH",
                    "target_zone": "ZONE-A",
                    "description": "Unlock auxiliary covered concourse holding areas in Pavilion Level 2",
                    "estimated_impact": "Absorbs 800 displaced spectators from exposed lower tier",
                    "human_approval_required": True
                },
                {
                    "action_id": "ACT-TRN-002",
                    "type": "request_transport",
                    "priority": "HIGH",
                    "target_zone": "ZONE-B",
                    "description": "Request 100 additional standby shuttle seats from BEST Transit Desk",
                    "estimated_impact": "Pre-positions fleet before match egress surge intensifies",
                    "human_approval_required": True
                }
            ],
            "required_resources": [
                {
                    "resource_type": "transport",
                    "required_units": 100,
                    "current_available": 350,
                    "gap": 0,
                    "urgency": "STANDBY"
                }
            ],
            "weather_contribution": 0.72,
            "transport_impact": {
                "demand_increase_pct": 34.0,
                "bottleneck_risk": "HIGH",
                "required_additional_seats": 100,
                "recommended_route": "Depot 4 Shuttle Bay"
            },
            "hospitality_impact": {
                "demand_increase_rooms": 20,
                "shelter_deficit": 0,
                "partner_holding_sufficient": True
            },
            "uncertainty": {"lower": 91.0, "upper": 95.8},
            "human_approval_required": True,
            "data_quality": {"missing": [], "stale": [], "conflicting": []},
            "model_metadata": {
                "model_id": "nugen-aligned-eventos-v1",
                "base_model": "nugen-base-v1",
                "model_type": "domain_aligned",
                "customized": True,
                "alignment_name": "eventos_domain_alignment_v1"
            }
        }
    },

    # ── CATEGORY C: CASCADING EFFECTS ────────────────────────────────────────
    {
        "category": "CASCADING_EFFECTS",
        "title": "Multi-Hop Cascade: Rain -> Approach Blockage -> Gate Surge -> Transit Shock",
        "input": {
            "event_name": "Mumbai Premier League — Wankhede Stadium",
            "zone_id": "ZONE-C",
            "zone_name": "Zone C - Marine Drive External Approach",
            "current_crowd": 2850,
            "capacity": 3000,
            "utilization_pct": 95.0,
            "weather": {
                "precipitation_mm_h": 28.0,
                "waterlogging_depth_cm": 8.0,
                "wind_speed_kmh": 44.0
            },
            "downstream_zones": ["ZONE-B", "ZONE-A"],
            "providers_status": {
                "transport_available": 200,
                "hotel_available": 82
            }
        },
        "expected_reasoning": {
            "risk_level": "CRITICAL",
            "confidence": 0.94,
            "summary": "Multi-hop operational cascade initiated: 28 mm/h rain causes 8 cm waterlogging on Marine Drive approach -> pedestrian velocity collapses -> crowds bottleneck at Churchgate subway entrance -> Zone B North Gate becomes sole dry entry point -> Zone A experiences acute localized queue surge.",
            "forecast": {
                "horizon_minutes": 15,
                "predicted_occupancy": 98.2,
                "minutes_to_threshold": 4.5
            },
            "affected_zones": ["ZONE-C", "ZONE-B", "ZONE-A"],
            "direct_impacts": [
                "Waterlogging halts Marine Drive pedestrian curb lane movement",
                "Zone C utilization exceeds 95% threshold"
            ],
            "cascading_impacts": [
                "Pedestrians re-route to Churchgate Subway and North Gate (Zone B)",
                "Station concourse queue spills toward railway tracks",
                "Emergency vehicle lane compromised along Marine Drive",
                "Urgent demand for 150 additional transit bus seats"
            ],
            "recommended_actions": [
                {
                    "action_id": "ACT-CAS-001",
                    "type": "traffic_diversion",
                    "priority": "URGENT",
                    "target_zone": "ZONE-C",
                    "description": "Request Mumbai Traffic Police to divert private vehicles from Marine Drive north lane for exclusive pedestrian safety corridor",
                    "estimated_impact": "Clears 1,200 m² of dry walking surface within 4 minutes",
                    "human_approval_required": True
                },
                {
                    "action_id": "ACT-CAS-002",
                    "type": "gate_reassignment",
                    "priority": "URGENT",
                    "target_zone": "ZONE-B",
                    "description": "Open North Gate auxiliary service portals 2B and 2C for bidirectional relief",
                    "estimated_impact": "Increases throughput by 140 persons/minute",
                    "human_approval_required": True
                }
            ],
            "required_resources": [
                {
                    "resource_type": "police_traffic_escort",
                    "required_units": 4,
                    "current_available": 8,
                    "gap": 0,
                    "urgency": "IMMEDIATE"
                },
                {
                    "resource_type": "transport",
                    "required_units": 150,
                    "current_available": 200,
                    "gap": 0,
                    "urgency": "IMMEDIATE"
                }
            ],
            "weather_contribution": 0.86,
            "transport_impact": {
                "demand_increase_pct": 52.0,
                "bottleneck_risk": "CRITICAL",
                "required_additional_seats": 150,
                "recommended_route": "Churchgate Egress Special Express"
            },
            "hospitality_impact": {
                "demand_increase_rooms": 45,
                "shelter_deficit": 12,
                "partner_holding_sufficient": True
            },
            "uncertainty": {"lower": 96.0, "upper": 100.0},
            "human_approval_required": True,
            "data_quality": {"missing": [], "stale": [], "conflicting": []},
            "model_metadata": {
                "model_id": "nugen-aligned-eventos-v1",
                "base_model": "nugen-base-v1",
                "model_type": "domain_aligned",
                "customized": True,
                "alignment_name": "eventos_domain_alignment_v1"
            }
        }
    },

    # ── CATEGORY D: TRANSPORT CAPACITY SYNTHESIS ─────────────────────────────
    {
        "category": "TRANSPORT_CAPACITY",
        "title": "Operational Transport Deficit Calculation & Closed-Loop Fulfillment",
        "input": {
            "required_capacity": 120,
            "reason": "Egress surge following early match rain delay",
            "active_providers": [
                {"name": "BEST Shuttle Depot 4", "available": 80, "type": "BUS"},
                {"name": "Private Feeder Fleet", "available": 40, "type": "SHUTTLE"}
            ],
            "current_transport_gap": 120
        },
        "expected_reasoning": {
            "risk_level": "WATCH",
            "confidence": 0.95,
            "summary": "120 additional transport seats required to evacuate egress surge. Inbound fleet inventory confirms BEST Shuttle (80 seats) and Private Feeder (40 seats). Total available supply = 120 seats. Transport deficit completely eliminated.",
            "forecast": {
                "horizon_minutes": 15,
                "predicted_occupancy": 76.0,
                "minutes_to_threshold": None
            },
            "affected_zones": ["ZONE-B"],
            "direct_impacts": ["Egress queue cleared at Gate 3 transit stop"],
            "cascading_impacts": ["Prevents concourse backup onto North Stand access"],
            "recommended_actions": [
                {
                    "action_id": "ACT-TRN-003",
                    "type": "confirm_dispatch",
                    "priority": "HIGH",
                    "target_zone": "ZONE-B",
                    "description": "Authorize simultaneous departure of 4 BEST feeder buses and 2 private shuttles",
                    "estimated_impact": "Evacuates 120 waiting spectators within 6 minutes",
                    "human_approval_required": True
                }
            ],
            "required_resources": [
                {
                    "resource_type": "transport",
                    "required_units": 120,
                    "current_available": 120,
                    "gap": 0,
                    "urgency": "IMMEDIATE"
                }
            ],
            "weather_contribution": 0.45,
            "transport_impact": {
                "demand_increase_pct": 22.0,
                "bottleneck_risk": "LOW",
                "required_additional_seats": 0,
                "recommended_route": "Churchgate Direct Route 108"
            },
            "hospitality_impact": {"demand_increase_rooms": 0, "shelter_deficit": 0, "partner_holding_sufficient": True},
            "uncertainty": {"lower": 72.0, "upper": 80.0},
            "human_approval_required": True,
            "data_quality": {"missing": [], "stale": [], "conflicting": []},
            "model_metadata": {
                "model_id": "nugen-aligned-eventos-v1",
                "base_model": "nugen-base-v1",
                "model_type": "domain_aligned",
                "customized": True,
                "alignment_name": "eventos_domain_alignment_v1"
            }
        }
    },

    # ── CATEGORY E: HOSPITALITY CAPACITY SYNTHESIS ───────────────────────────
    {
        "category": "HOSPITALITY_CAPACITY",
        "title": "Hospitality Partner Demand Aggregation & Surge Absorption",
        "input": {
            "stranded_attendees": 180,
            "reason": "Severe rain halting suburban train service on Western Line",
            "hotel_partner_inventory": [
                {"name": "Hotel Vivanta Cuffe Parade", "available_rooms": 50},
                {"name": "Marine Plaza Hotel", "available_rooms": 80},
                {"name": "Trident Nariman Point", "available_rooms": 50}
            ]
        },
        "expected_reasoning": {
            "risk_level": "WATCH",
            "confidence": 0.93,
            "summary": "180 attendees seeking overnight or immediate holding accommodation due to suburban rail suspension. Partner aggregate capacity: Vivanta (50), Marine Plaza (80), Trident (50) = 180 rooms. Complete capacity match achieved.",
            "forecast": {
                "horizon_minutes": 30,
                "predicted_occupancy": 72.0,
                "minutes_to_threshold": None
            },
            "affected_zones": ["ZONE-C"],
            "direct_impacts": ["Stranded attendee holding deficit resolved"],
            "cascading_impacts": ["Prevents overcrowding in stadium lobby and medical stations"],
            "recommended_actions": [
                {
                    "action_id": "ACT-HOS-001",
                    "type": "hotel_holding_dispatch",
                    "priority": "MEDIUM",
                    "target_zone": "ZONE-C",
                    "description": "Issue voucher allocations across Vivanta, Marine Plaza, and Trident partner desks",
                    "estimated_impact": "Smoothly accommodates 180 stranded visitors",
                    "human_approval_required": True
                }
            ],
            "required_resources": [
                {
                    "resource_type": "hospitality",
                    "required_units": 180,
                    "current_available": 180,
                    "gap": 0,
                    "urgency": "STANDBY"
                }
            ],
            "weather_contribution": 0.88,
            "transport_impact": {"demand_increase_pct": 0.0, "bottleneck_risk": "LOW", "required_additional_seats": 0},
            "hospitality_impact": {
                "demand_increase_rooms": 180,
                "shelter_deficit": 0,
                "partner_holding_sufficient": True
            },
            "uncertainty": {"lower": 68.0, "upper": 76.0},
            "human_approval_required": True,
            "data_quality": {"missing": [], "stale": [], "conflicting": []},
            "model_metadata": {
                "model_id": "nugen-aligned-eventos-v1",
                "base_model": "nugen-base-v1",
                "model_type": "domain_aligned",
                "customized": True,
                "alignment_name": "eventos_domain_alignment_v1"
            }
        }
    },

    # ── CATEGORY F: OPERATIONAL RECOMMENDATIONS (NORMAL / WATCH) ─────────────
    {
        "category": "OPERATIONAL_RECOMMENDATION_NORMAL",
        "title": "Nominal Match Egress Baseline — Normal Risk State",
        "input": {
            "event_name": "Mumbai Premier League — Wankhede Stadium",
            "zone_id": "ZONE-A",
            "zone_name": "Zone A - Stadium Bowl",
            "current_crowd": 16500,
            "capacity": 26000,
            "utilization_pct": 63.5,
            "inflow_per_minute": 20.0,
            "outflow_per_minute": 45.0,
            "weather": {
                "precipitation_mm_h": 0.0,
                "temperature_c": 27.5,
                "wind_speed_kmh": 12.0
            },
            "providers_status": {
                "transport_available": 520,
                "hotel_available": 110
            }
        },
        "expected_reasoning": {
            "risk_level": "NORMAL",
            "confidence": 0.96,
            "summary": "All sectors operating within baseline capacity thresholds (63.5% utilization). Egress velocity normal with negative net flow (-25/min). Weather clear. No active intervention warranted.",
            "forecast": {
                "horizon_minutes": 10,
                "predicted_occupancy": 61.2,
                "minutes_to_threshold": None
            },
            "affected_zones": [],
            "direct_impacts": ["Routine orderly match exit"],
            "cascading_impacts": [],
            "recommended_actions": [],
            "required_resources": [],
            "weather_contribution": 0.0,
            "transport_impact": {"demand_increase_pct": 0.0, "bottleneck_risk": "LOW", "required_additional_seats": 0},
            "hospitality_impact": {"demand_increase_rooms": 0, "shelter_deficit": 0, "partner_holding_sufficient": True},
            "uncertainty": {"lower": 59.0, "upper": 63.0},
            "human_approval_required": False,
            "data_quality": {"missing": [], "stale": [], "conflicting": []},
            "model_metadata": {
                "model_id": "nugen-aligned-eventos-v1",
                "base_model": "nugen-base-v1",
                "model_type": "domain_aligned",
                "customized": True,
                "alignment_name": "eventos_domain_alignment_v1"
            }
        }
    },

    # ── CATEGORY G: HUMAN-IN-THE-LOOP SAFETY GATE ────────────────────────────
    {
        "category": "HUMAN_IN_THE_LOOP",
        "title": "Mandatory Human Approval Gate on High-Risk Interventions",
        "input": {
            "event_name": "Mumbai Premier League — Wankhede Stadium",
            "zone_id": "ZONE-A",
            "zone_name": "Zone A - Stadium Bowl",
            "current_crowd": 24900,
            "capacity": 26000,
            "utilization_pct": 95.8,
            "weather": {"precipitation_mm_h": 22.0, "wind_speed_kmh": 38.0}
        },
        "expected_reasoning": {
            "risk_level": "CRITICAL",
            "confidence": 0.91,
            "summary": "Zone A utilization at 95.8%. Imminent overflow danger. Emergency ingress stoppage recommended. In accordance with safety protocol, action requires explicit organizer / incident commander authorization before execution.",
            "forecast": {
                "horizon_minutes": 5,
                "predicted_occupancy": 98.0,
                "minutes_to_threshold": 2.1
            },
            "affected_zones": ["ZONE-A", "ZONE-B"],
            "direct_impacts": ["Crush danger at entry turnstiles A3-A6"],
            "cascading_impacts": ["External perimeter crowd compression"],
            "recommended_actions": [
                {
                    "action_id": "ACT-CRIT-001",
                    "type": "halt_ingress",
                    "priority": "URGENT",
                    "target_zone": "ZONE-A",
                    "description": "Temporarily pause Gate 3 turnstiles and activate perimeter holding pen",
                    "estimated_impact": "Halts inflow immediately, stabilizing concourse density at 0.85 ppl/m²",
                    "human_approval_required": True
                }
            ],
            "required_resources": [
                {
                    "resource_type": "police_rapid_response",
                    "required_units": 12,
                    "current_available": 16,
                    "gap": 0,
                    "urgency": "IMMEDIATE"
                }
            ],
            "weather_contribution": 0.65,
            "transport_impact": {"demand_increase_pct": 40.0, "bottleneck_risk": "CRITICAL", "required_additional_seats": 200},
            "hospitality_impact": {"demand_increase_rooms": 25, "shelter_deficit": 0, "partner_holding_sufficient": True},
            "uncertainty": {"lower": 96.5, "upper": 99.5},
            "human_approval_required": True,
            "data_quality": {"missing": [], "stale": [], "conflicting": []},
            "model_metadata": {
                "model_id": "nugen-aligned-eventos-v1",
                "base_model": "nugen-base-v1",
                "model_type": "domain_aligned",
                "customized": True,
                "alignment_name": "eventos_domain_alignment_v1"
            }
        }
    }
]


def get_domain_dataset() -> List[Dict[str, Any]]:
    """Returns the in-memory canonical EVENTOS alignment dataset."""
    return ALIGNMENT_DATASET_ITEMS


def export_alignment_dataset_jsonl(filepath: str) -> int:
    """
    Exports the domain alignment dataset to standard JSONL format
    compatible with Nugen v3 alignment ingestion (`POST /api/v3/alignment`).
    Each line contains a prompt and structured JSON completion.
    """
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    count = 0
    with open(filepath, "w", encoding="utf-8") as f:
        for item in ALIGNMENT_DATASET_ITEMS:
            record = {
                "messages": [
                    {
                        "role": "system",
                        "content": "You are the Nugen Domain-Aligned Event Operations Intelligence Engine for EVENTOS. Analyze event state and produce structured JSON operational intelligence."
                    },
                    {
                        "role": "user",
                        "content": json.dumps({
                            "task": "ANALYZE_EVENT_OPERATIONS_STATE",
                            "category": item["category"],
                            "title": item["title"],
                            "state": item["input"]
                        })
                    },
                    {
                        "role": "assistant",
                        "content": json.dumps(item["expected_reasoning"])
                    }
                ],
                "metadata": {
                    "domain": "event_operations",
                    "category": item["category"],
                    "alignment_target": "EVENTOS_CONTROL_TOWER_V1"
                }
            }
            f.write(json.dumps(record) + "\n")
            count += 1
    return count

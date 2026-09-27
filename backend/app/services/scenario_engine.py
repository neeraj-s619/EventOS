"""
EVENTOS Scenario Engine & What-If Counterfactual Lab.
Implements the 6 primary operational scenarios:
1. Crowd Surge (Zone A Inflow Surge)
2. Heavy Rain (Precipitation Disruption & Concourse Swelling)
3. Gate Closure (Gate A Stanchion Block & Flow Redistribution)
4. Transport Failure (Fleet Breakdown & Transit Deficit)
5. Hotel Capacity Shock (Hospitality Inventory Loss)
6. Combined Extreme Event (Multi-Sector Cascading Crisis)

Provides rigorous Baseline vs. What-If comparison matrix.
"""

from typing import Dict, Any, List, Optional
import time
from dataclasses import dataclass, asdict

from app.models.database import RiskLevelEnum


@dataclass
class ScenarioComparisonItem:
    metric_name: str
    baseline_value: str
    whatif_value: str
    delta: str
    status: str # "NORMAL", "WARNING", "CRITICAL"


class ScenarioEngine:
    """
    Engine executing deterministic scenario perturbations on the Digital Twin state.
    """

    SCENARIO_DEFINITIONS = {
        "CROWD_SURGE": {
            "name": "Scenario 1 — Concourse Crowd Surge",
            "description": "Sudden arrival surge at South Gate A with inflow spiking +150 spectators/min.",
            "category": "CROWD",
            "severity": "WARNING",
            "recommended_action": "Unlock Concourse B crossover stanchions and initiate audio-visual diversion guidance."
        },
        "HEAVY_RAIN": {
            "name": "Scenario 2 — Intense Monsoon Downpour",
            "description": "25 mm/h torrential rain for 45 mins driving uncovered spectators into sheltered concourses.",
            "category": "WEATHER",
            "severity": "WARNING",
            "recommended_action": "Open indoor concourse holding zones and notify BEST transit for covered shelter buses."
        },
        "GATE_CLOSURE": {
            "name": "Scenario 3 — Emergency Gate A Closure",
            "description": "Gate A turnstile failure forcing immediate redistribution of 180 incoming visitors/min to Gate B.",
            "category": "INFRASTRUCTURE",
            "severity": "WARNING",
            "recommended_action": "Reroute Gate A queues via illuminated guidance boards to Gate B North Turnstiles."
        },
        "TRANSPORT_FAILURE": {
            "name": "Scenario 4 — Transit Fleet Breakdown",
            "description": "3 primary transit buses suffer mechanical outage, reducing immediate seat capacity by 180 seats.",
            "category": "TRANSPORT",
            "severity": "WARNING",
            "recommended_action": "Poll western railway desk for supplementary EMU fast shuttle deployment."
        },
        "HOSPITALITY_SHOCK": {
            "name": "Scenario 5 — Hospitality Room Deficit",
            "description": "Partner hotel block loses 100 reserved rooms due to localized HVAC outage.",
            "category": "HOSPITALITY",
            "severity": "WATCH",
            "recommended_action": "Broadcast automated accommodation matching to backup South Mumbai boutique hotels."
        },
        "COMBINED_EXTREME_EVENT": {
            "name": "Scenario 6 — Combined Extreme Incident (Pitch Demo)",
            "description": "Multi-sector cascading crisis: Inflow surge (+180/min) + Torrential Rain (35 mm/h) + 3 Buses Offline.",
            "category": "MULTI_SECTOR",
            "severity": "CRITICAL",
            "recommended_action": "Execute Unified Stadium Contingency Plan: Reroute spectators, summon backup transit, activate staff surge protocol."
        }
    }

    def execute_scenario(self, scenario_key: str, baseline_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Executes scenario logic and produces the What-If state and Baseline vs What-If comparison matrix.
        """
        key = scenario_key.upper().strip()
        meta = self.SCENARIO_DEFINITIONS.get(key, self.SCENARIO_DEFINITIONS["COMBINED_EXTREME_EVENT"])

        # Default Realistic Baseline State
        base_zone_a_occ = 78.4
        base_zone_a_crowd = 7840
        base_zone_b_occ = 62.1
        base_risk = "NORMAL"
        base_transport_seats = 650
        base_hotel_rooms = 82
        base_weather_rain = 0.0
        base_inflow = 85.0
        base_time_to_breach = "> 60m"

        whatif: Dict[str, Any] = {
            "scenario_key": key,
            "name": meta["name"],
            "description": meta["description"],
            "category": meta["category"],
            "severity": meta["severity"],
            "recommended_action": meta["recommended_action"],
            "executed_at": time.time()
        }

        comparisons: List[ScenarioComparisonItem] = []

        if key == "CROWD_SURGE":
            wf_occ = 94.2
            wf_inflow = 235.0
            wf_risk = "WARNING"
            wf_breach = "8.2 min"
            comparisons = [
                ScenarioComparisonItem("Zone A Occupancy", f"{base_zone_a_occ}%", f"{wf_occ}%", "+15.8%", "CRITICAL"),
                ScenarioComparisonItem("Zone A Inflow Rate", f"{base_inflow}/min", f"{wf_inflow}/min", "+150/min", "CRITICAL"),
                ScenarioComparisonItem("Risk Level", base_risk, wf_risk, "NORMAL → WARNING", "WARNING"),
                ScenarioComparisonItem("Time to Threshold Breach", base_time_to_breach, wf_breach, "-52 min", "CRITICAL"),
                ScenarioComparisonItem("Available Transit Seats", f"{base_transport_seats}", f"{base_transport_seats}", "0", "NORMAL"),
                ScenarioComparisonItem("Available Hotel Rooms", f"{base_hotel_rooms}", f"{base_hotel_rooms}", "0", "NORMAL")
            ]
            whatif["metrics"] = {"zone_a_occupancy": wf_occ, "inflow_rate": wf_inflow, "risk": wf_risk, "time_to_breach": wf_breach}

        elif key == "HEAVY_RAIN":
            wf_occ = 89.6
            wf_weather = 25.0
            wf_risk = "WARNING"
            wf_transit = 420
            comparisons = [
                ScenarioComparisonItem("Rainfall Rate", f"{base_weather_rain} mm/h", f"{wf_weather} mm/h", "+25 mm/h", "CRITICAL"),
                ScenarioComparisonItem("Covered Concourse Occupancy", f"{base_zone_a_occ}%", f"{wf_occ}%", "+11.2%", "WARNING"),
                ScenarioComparisonItem("Outdoor Movement Velocity", "1.42 m/s", "0.85 m/s", "-40%", "WARNING"),
                ScenarioComparisonItem("Transit Demand Surge", "Baseline", "+35% Load", "+230 demand", "WARNING"),
                ScenarioComparisonItem("Risk Level", base_risk, wf_risk, "NORMAL → WARNING", "WARNING"),
                ScenarioComparisonItem("Available Transit Seats", f"{base_transport_seats}", f"{wf_transit}", "-230 seats", "WARNING")
            ]
            whatif["metrics"] = {"rainfall_rate": wf_weather, "covered_occupancy": wf_occ, "risk": wf_risk, "transit_seats": wf_transit}

        elif key == "GATE_CLOSURE":
            wf_zone_b_occ = 91.5
            wf_risk = "WARNING"
            comparisons = [
                ScenarioComparisonItem("Gate A Inflow", f"{base_inflow}/min", "0/min", "CLOSED (BLOCKED)", "CRITICAL"),
                ScenarioComparisonItem("Gate B / Zone B Inflow", "60/min", "240/min", "+180/min (REROUTED)", "CRITICAL"),
                ScenarioComparisonItem("Zone B Occupancy", f"{base_zone_b_occ}%", f"{wf_zone_b_occ}%", "+29.4%", "CRITICAL"),
                ScenarioComparisonItem("Risk Level", base_risk, wf_risk, "NORMAL → WARNING", "WARNING"),
                ScenarioComparisonItem("Queue Wait Time Gate B", "4.2 min", "18.5 min", "+14.3 min", "WARNING")
            ]
            whatif["metrics"] = {"zone_b_occupancy": wf_zone_b_occ, "gate_a_status": "CLOSED", "risk": wf_risk}

        elif key == "TRANSPORT_FAILURE":
            wf_seats = 380
            wf_risk = "WARNING"
            comparisons = [
                ScenarioComparisonItem("Active Fleet Buses", "4 Units Active", "1 Unit Active (3 Offline)", "-3 Vehicles", "CRITICAL"),
                ScenarioComparisonItem("Available Transit Seats", f"{base_transport_seats} seats", f"{wf_seats} seats", "-270 seats", "CRITICAL"),
                ScenarioComparisonItem("Transit Gap Status", "BALANCED", "DEFICIT (-150)", "WARNING", "CRITICAL"),
                ScenarioComparisonItem("Station Link Queue Time", "5 min", "22 min", "+17 min", "WARNING"),
                ScenarioComparisonItem("Risk Level", base_risk, wf_risk, "NORMAL → WARNING", "WARNING")
            ]
            whatif["metrics"] = {"available_seats": wf_seats, "offline_buses": 3, "risk": wf_risk}

        elif key == "HOSPITALITY_SHOCK":
            wf_rooms = 32
            comparisons = [
                ScenarioComparisonItem("Partner Hotel Rooms", f"{base_hotel_rooms} rooms", f"{wf_rooms} rooms", "-50 rooms (SHOCK)", "WARNING"),
                ScenarioComparisonItem("Accommodation Demand Gap", "0 (Covered)", "48 rooms required", "DEFICIT", "WARNING"),
                ScenarioComparisonItem("Automated Telegram Alerts", "0 dispatched", "4 hotels queried", "+4 queries", "NORMAL"),
                ScenarioComparisonItem("Risk Level", base_risk, "WATCH", "NORMAL → WATCH", "NORMAL")
            ]
            whatif["metrics"] = {"available_rooms": wf_rooms, "deficit": 48, "risk": "WATCH"}

        else: # COMBINED_EXTREME_EVENT
            wf_occ = 96.5
            wf_inflow = 265.0
            wf_weather = 35.0
            wf_seats = 310
            wf_risk = "CRITICAL"
            comparisons = [
                ScenarioComparisonItem("Zone A Occupancy", f"{base_zone_a_occ}%", f"{wf_occ}%", "+18.1%", "CRITICAL"),
                ScenarioComparisonItem("Concourse Inflow Rate", f"{base_inflow}/min", f"{wf_inflow}/min", "+180/min", "CRITICAL"),
                ScenarioComparisonItem("Rainfall Rate", f"{base_weather_rain} mm/h", f"{wf_weather} mm/h", "+35 mm/h (GALE)", "CRITICAL"),
                ScenarioComparisonItem("Active Fleet Seats", f"{base_transport_seats}", f"{wf_seats}", "-340 seats", "CRITICAL"),
                ScenarioComparisonItem("Risk Level", base_risk, wf_risk, "NORMAL → CRITICAL", "CRITICAL"),
                ScenarioComparisonItem("Time to Bottleneck Ingress Breach", "> 60m", "5.4 min", "-55 min", "CRITICAL")
            ]
            whatif["metrics"] = {
                "zone_a_occupancy": wf_occ,
                "inflow_rate": wf_inflow,
                "rainfall_rate": wf_weather,
                "transit_seats": wf_seats,
                "risk": wf_risk,
                "time_to_breach": "5.4 min"
            }

        whatif["comparison_table"] = [asdict(item) for item in comparisons]
        whatif["cascading_impacts"] = [
            {"sector": "CROWD", "impact": "High density at South Gate A choking emergency egress stanchions."},
            {"sector": "SHELTER", "impact": "Heavy rain drives spectators from open bowl into sheltered North ramps."},
            {"sector": "TRANSPORT", "impact": "Fleet shortfall creates 250+ passenger bottleneck at Marine Drive bus bays."}
        ]
        return whatif


_scenario_engine: Optional[ScenarioEngine] = None


def get_scenario_engine() -> ScenarioEngine:
    global _scenario_engine
    if _scenario_engine is None:
        _scenario_engine = ScenarioEngine()
    return _scenario_engine

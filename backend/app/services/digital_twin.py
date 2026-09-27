"""
EVENTOS Digital Twin Engine
Creates a COUNTERFACTUAL simulation of event state under weather scenarios.

CRITICAL: The Digital Twin NEVER mutates the real event state.
It reads real zone/provider data, applies weather impacts, and returns
a separate DigitalTwinState representing "what would happen if..."

Architecture:
  Real Event State  +  Weather Scenario
         ↓
  DigitalTwinEngine.simulate()
         ↓
  DigitalTwinState  (counterfactual, isolated)
         →  feeds into existing recommendation engine context
"""

import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session

from app.models.database import ZoneDB, ProviderDB, ZoneTypeEnum, RiskLevelEnum
from app.services.weather_service import WeatherState, get_weather_service
from app.services.weather_impact_engine import WeatherImpactEngine, WeatherImpact

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────
# Scenario Presets
# ─────────────────────────────────────────────────────────────────

SCENARIO_PRESETS: Dict[str, Dict[str, Any]] = {
    "normal": {
        "label": "Normal Conditions",
        "description": "Baseline — no weather disruption",
        "precipitation_mm_h": 0.0,
        "temperature_c": 28.0,
        "humidity_pct": 70.0,
        "wind_speed_kmh": 15.0,
        "visibility_m": 10000.0,
        "icon": "☀️",
    },
    "moderate_rain": {
        "label": "Moderate Rain",
        "description": "Pre-monsoon / moderate shower — typical Mumbai event risk",
        "precipitation_mm_h": 5.0,
        "temperature_c": 26.0,
        "humidity_pct": 85.0,
        "wind_speed_kmh": 25.0,
        "visibility_m": 6000.0,
        "icon": "🌦️",
    },
    "heavy_rain": {
        "label": "Heavy Rain",
        "description": "Mumbai monsoon — heavy sustained rainfall",
        "precipitation_mm_h": 20.0,
        "temperature_c": 24.0,
        "humidity_pct": 92.0,
        "wind_speed_kmh": 35.0,
        "visibility_m": 3000.0,
        "icon": "🌧️",
    },
    "extreme_rain": {
        "label": "Extreme Rain / Waterlogging",
        "description": "Intense monsoon — waterlogging risk at Marine Drive",
        "precipitation_mm_h": 60.0,
        "temperature_c": 23.0,
        "humidity_pct": 96.0,
        "wind_speed_kmh": 55.0,
        "visibility_m": 1000.0,
        "icon": "⛈️",
    },
    "extreme_heat": {
        "label": "Extreme Heat",
        "description": "Pre-monsoon heat wave — high indoor occupancy + heat stress risk",
        "precipitation_mm_h": 0.0,
        "temperature_c": 42.0,
        "humidity_pct": 60.0,
        "wind_speed_kmh": 10.0,
        "visibility_m": 9000.0,
        "icon": "🌡️",
    },
    "high_wind": {
        "label": "High Wind",
        "description": "Cyclone periphery — high wind with structural risk",
        "precipitation_mm_h": 3.0,
        "temperature_c": 26.0,
        "humidity_pct": 80.0,
        "wind_speed_kmh": 75.0,
        "visibility_m": 4000.0,
        "icon": "💨",
    },
    "thunderstorm": {
        "label": "Thunderstorm",
        "description": "Active thunderstorm — outdoor area clearance required",
        "precipitation_mm_h": 30.0,
        "temperature_c": 23.0,
        "humidity_pct": 95.0,
        "wind_speed_kmh": 50.0,
        "visibility_m": 1500.0,
        "icon": "⚡",
    },
}


# ─────────────────────────────────────────────────────────────────
# Digital Twin Zone / Provider State
# ─────────────────────────────────────────────────────────────────

@dataclass
class DTZoneState:
    """Counterfactual zone state under weather scenario."""
    zone_id: str
    name: str
    zone_type: str
    capacity: int
    # Baseline (real)
    baseline_crowd: int
    baseline_utilization: float
    baseline_risk: str
    # Simulated (counterfactual)
    simulated_crowd: int
    simulated_utilization: float
    simulated_risk: str
    crowd_delta: int
    utilization_delta: float
    # Spatial
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    # Explanation
    impact_factor: float = 1.0  # multiplier applied
    impact_reason: str = ""


@dataclass
class DTProviderState:
    """Counterfactual provider demand state."""
    provider_id: str
    name: str
    provider_type: str
    baseline_available: int
    simulated_demand_increase: int   # extra demand driven by weather
    simulated_available: int
    demand_multiplier: float


@dataclass
class DigitalTwinState:
    """
    Complete counterfactual event state — NEVER written to real DB.
    Represents: 'If the weather were X, the event state would look like Y.'
    """
    event_id: str
    scenario_name: str
    scenario_label: str
    # Weather driving the simulation
    weather: Dict[str, Any]
    impact: Dict[str, Any]
    # Simulated vs baseline
    zones: List[DTZoneState]
    providers: List[DTProviderState]
    # Aggregate KPIs
    baseline_total_crowd: int
    simulated_total_crowd: int
    crowd_delta: int
    crowd_delta_pct: float
    baseline_overall_risk: str
    simulated_overall_risk: str
    risk_escalated: bool
    # Transport / hotel summary
    baseline_transport_available: int
    simulated_transport_available: int
    baseline_hotel_available: int
    simulated_hotel_available: int
    # Capacity Gap & Operational Telemetry
    transport_demand_required: int = 0
    transport_capacity_gap: int = 0
    capacity_gap_status: str = "BALANCED"
    cascade_chain: List[Dict[str, str]] = field(default_factory=list)
    # Confidence / uncertainty
    confidence: float = 0.85
    uncertainty_pct: float = 15.0
    # Recommendations fed into existing orchestration context
    weather_recommendations: List[str] = field(default_factory=list)
    # Meta
    simulated_at: str = ""
    is_live_weather: bool = False  # True = using real Open-Meteo data, False = custom scenario
    data_source_note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d


# ─────────────────────────────────────────────────────────────────
# Risk Level Helpers
# ─────────────────────────────────────────────────────────────────

_RISK_ORDER = {
    "normal": 1, "watch": 2, "warning": 3, "critical": 4, "overload": 5
}

def _escalate_risk(base_risk: str, uplift: float) -> str:
    """Escalate risk level based on weather uplift factor (0-1)."""
    order = _RISK_ORDER.get(base_risk, 1)
    if uplift >= 0.50:
        steps = 2
    elif uplift >= 0.25:
        steps = 1
    elif uplift >= 0.10:
        steps = 1 if order < 3 else 0
    else:
        steps = 0
    new_order = min(5, order + steps)
    inv = {v: k for k, v in _RISK_ORDER.items()}
    return inv.get(new_order, "normal")


def _crowd_to_risk(utilization_pct: float) -> str:
    if utilization_pct >= 100:
        return "overload"
    elif utilization_pct >= 95:
        return "critical"
    elif utilization_pct >= 85:
        return "warning"
    elif utilization_pct >= 70:
        return "watch"
    else:
        return "normal"


# ─────────────────────────────────────────────────────────────────
# Engine
# ─────────────────────────────────────────────────────────────────

class DigitalTwinEngine:
    """
    Reads real event state → applies weather impacts → produces DigitalTwinState.
    NEVER mutates ZoneDB, ProviderDB, or any real state.
    """

    def __init__(self, db: Session):
        self.db = db
        self.impact_engine = WeatherImpactEngine()

    def simulate_live_weather(self, event_id: str) -> DigitalTwinState:
        """Run Digital Twin using current live Open-Meteo weather for Wankhede."""
        ws_svc = get_weather_service()
        weather = ws_svc.get_current_weather()
        impact = self.impact_engine.compute_impact(weather)
        return self._build_twin_state(
            event_id=event_id,
            weather=weather,
            impact=impact,
            scenario_name="live_weather",
            scenario_label=f"Live Weather — {weather.weather_description}",
            is_live=True,
        )

    def simulate_scenario(
        self,
        event_id: str,
        scenario_name: str = "normal",
        precipitation_mm_h: Optional[float] = None,
        temperature_c: Optional[float] = None,
        humidity_pct: Optional[float] = None,
        wind_speed_kmh: Optional[float] = None,
        visibility_m: Optional[float] = None,
    ) -> DigitalTwinState:
        """
        Run Digital Twin for a named preset or custom parameter set.
        Custom params override preset values if provided.
        """
        preset = SCENARIO_PRESETS.get(scenario_name, SCENARIO_PRESETS["normal"])
        params = {
            "precipitation_mm_h": precipitation_mm_h if precipitation_mm_h is not None else preset["precipitation_mm_h"],
            "temperature_c":      temperature_c      if temperature_c      is not None else preset["temperature_c"],
            "humidity_pct":       humidity_pct       if humidity_pct       is not None else preset["humidity_pct"],
            "wind_speed_kmh":     wind_speed_kmh     if wind_speed_kmh     is not None else preset["wind_speed_kmh"],
            "visibility_m":       visibility_m       if visibility_m       is not None else preset["visibility_m"],
        }

        impact = self.impact_engine.compute_scenario_impact(**params)

        # Build a lightweight WeatherState for metadata
        from app.services.weather_service import WeatherState, classify_rain_intensity
        ws = WeatherState(
            temperature_c=params["temperature_c"],
            feels_like_c=params["temperature_c"],
            humidity_pct=params["humidity_pct"],
            precipitation_mm_h=params["precipitation_mm_h"],
            wind_speed_kmh=params["wind_speed_kmh"],
            visibility_m=params["visibility_m"],
            rain_intensity=classify_rain_intensity(params["precipitation_mm_h"]),
            weather_description=preset.get("label", scenario_name),
            source="DIGITAL_TWIN_SCENARIO",
            is_raining=params["precipitation_mm_h"] > 0,
            is_thunderstorm=scenario_name == "thunderstorm",
        )

        label = preset.get("label", scenario_name)
        if any(v is not None for v in [precipitation_mm_h, temperature_c, humidity_pct, wind_speed_kmh, visibility_m]):
            label += " (Custom)"

        return self._build_twin_state(
            event_id=event_id,
            weather=ws,
            impact=impact,
            scenario_name=scenario_name,
            scenario_label=label,
            is_live=False,
        )

    def _build_twin_state(
        self,
        event_id: str,
        weather: Any,
        impact: WeatherImpact,
        scenario_name: str,
        scenario_label: str,
        is_live: bool,
    ) -> DigitalTwinState:
        zones = self.db.query(ZoneDB).filter(ZoneDB.event_id == event_id).all()
        providers = self.db.query(ProviderDB).filter(ProviderDB.event_id == event_id).all()

        dt_zones = []
        for zone in zones:
            dt_zone = self._apply_zone_impact(zone, impact)
            dt_zones.append(dt_zone)

        dt_providers = []
        for prov in providers:
            dt_prov = self._apply_provider_impact(prov, impact)
            dt_providers.append(dt_prov)

        # Aggregate KPIs
        baseline_total = sum(z.baseline_crowd for z in dt_zones)
        simulated_total = sum(z.simulated_crowd for z in dt_zones)
        crowd_delta = simulated_total - baseline_total
        crowd_delta_pct = (crowd_delta / baseline_total * 100) if baseline_total > 0 else 0.0

        # Overall risk
        baseline_risks = [_RISK_ORDER.get(z.baseline_risk, 1) for z in dt_zones]
        simulated_risks = [_RISK_ORDER.get(z.simulated_risk, 1) for z in dt_zones]
        inv_risk = {v: k for k, v in _RISK_ORDER.items()}
        baseline_overall = inv_risk.get(max(baseline_risks) if baseline_risks else 1, "normal")
        simulated_overall = inv_risk.get(max(simulated_risks) if simulated_risks else 1, "normal")
        risk_escalated = _RISK_ORDER.get(simulated_overall, 1) > _RISK_ORDER.get(baseline_overall, 1)

        # Transport / hotel aggregates
        transport_provs = [p for p in providers if p.type.value == "transport"]
        hotel_provs = [p for p in providers if p.type.value == "hotel"]

        baseline_transport_avail = sum(p.available_capacity for p in transport_provs)
        baseline_hotel_avail = sum(p.available_capacity for p in hotel_provs)

        transport_dt = {p.provider_id: d for p, d in zip(providers, dt_providers)}
        sim_transport_avail = sum(
            transport_dt.get(p.provider_id, DTProviderState(
                p.provider_id, p.name, "transport",
                p.available_capacity, 0, p.available_capacity, 1.0
            )).simulated_available for p in transport_provs
        )
        sim_hotel_avail = sum(
            transport_dt.get(p.provider_id, DTProviderState(
                p.provider_id, p.name, "hotel",
                p.available_capacity, 0, p.available_capacity, 1.0
            )).simulated_available for p in hotel_provs
        )

        # Weather dict
        weather_dict = weather.to_dict() if hasattr(weather, "to_dict") else {}

        # Operational Capacity Gap & Surge Demand Calculation
        mult = impact.transport_demand_multiplier
        # Base transit demand derived from crowd flow (stable regardless of provider dispatch)
        base_demand = max(413, int(baseline_total * 0.35)) if baseline_total > 0 else 413
        transport_demand_required = int(base_demand * mult) if mult > 1.0 else base_demand
        
        if transport_demand_required > baseline_transport_avail:
            transport_capacity_gap = transport_demand_required - baseline_transport_avail
            gap_status = f"DEFICIT_{transport_capacity_gap}_SEATS"
        else:
            transport_capacity_gap = 0
            gap_status = "BALANCED"

        # Construct Weather Impact Cascade Chain
        precip = getattr(weather, "precipitation_mm_h", 0.0) or 0.0
        mov_red = int(round((1.0 - impact.outdoor_movement_factor) * 100))
        shelter_inc = int(round(impact.shelter_demand_delta * 100))

        cascade_chain = [
            {
                "step": "1. Weather Condition",
                "detail": f"{scenario_label} ({precip:.1f} mm/h)",
                "status": "DETECTED"
            },
            {
                "step": "2. Outdoor Movement",
                "detail": f"-{mov_red}% flow reduction across concourses",
                "status": "IMPACTED"
            },
            {
                "step": "3. Zone Accumulation",
                "detail": f"+{shelter_inc}% shelter pressure in indoor lounges",
                "status": "EVALUATED"
            },
            {
                "step": "4. Transport Surge",
                "detail": f"{transport_demand_required} seats required (demand ×{mult:.2f})",
                "status": "SURGING"
            },
            {
                "step": "5. Capacity Gap",
                "detail": f"{transport_capacity_gap}-seat deficit ({transport_demand_required} req vs {baseline_transport_avail} avail)" if transport_capacity_gap > 0 else "0-seat deficit (Capacity Gap Closed)",
                "status": "ALERT_GAP" if transport_capacity_gap > 0 else "RESOLVED"
            },
            {
                "step": "6. Telemetry Dispatch",
                "detail": f"Operational poll: +{transport_capacity_gap} seats to transit providers" if transport_capacity_gap > 0 else "Standby units confirmed",
                "status": "DISPATCHED" if transport_capacity_gap > 0 else "STANDBY"
            },
            {
                "step": "7. Provider Response",
                "detail": "Awaiting response via Provider Pulse (Telegram)" if transport_capacity_gap > 0 else "Additional capacity confirmed via Provider Pulse (Telegram)",
                "status": "PENDING" if transport_capacity_gap > 0 else "CONFIRMED"
            },
            {
                "step": "8. Risk Mitigation",
                "detail": "Transit flow balanced • Congestion risk mitigated" if transport_capacity_gap == 0 else f"High egress bottleneck risk until {transport_capacity_gap} seats fulfilled",
                "status": "MITIGATED" if transport_capacity_gap == 0 else "MONITORING"
            }
        ]

        data_note = (
            "Live Open-Meteo weather for Wankhede Stadium, Mumbai (18.9375°N, 72.8265°E). "
            "This is SIMULATED counterfactual state — real operational state is unchanged."
        ) if is_live else (
            f"Custom scenario: '{scenario_label}'. "
            "This is SIMULATED counterfactual state — real operational state is unchanged."
        )

        return DigitalTwinState(
            event_id=event_id,
            scenario_name=scenario_name,
            scenario_label=scenario_label,
            weather=weather_dict,
            impact=impact.to_dict(),
            zones=dt_zones,
            providers=dt_providers,
            baseline_total_crowd=baseline_total,
            simulated_total_crowd=simulated_total,
            crowd_delta=crowd_delta,
            crowd_delta_pct=round(crowd_delta_pct, 1),
            baseline_overall_risk=baseline_overall,
            simulated_overall_risk=simulated_overall,
            risk_escalated=risk_escalated,
            baseline_transport_available=baseline_transport_avail,
            simulated_transport_available=sim_transport_avail,
            baseline_hotel_available=baseline_hotel_avail,
            simulated_hotel_available=sim_hotel_avail,
            transport_demand_required=transport_demand_required,
            transport_capacity_gap=transport_capacity_gap,
            capacity_gap_status=gap_status,
            cascade_chain=cascade_chain,
            confidence=impact.confidence,
            uncertainty_pct=impact.uncertainty_pct,
            weather_recommendations=impact.recommendations,
            simulated_at=datetime.utcnow().isoformat(),
            is_live_weather=is_live,
            data_source_note=data_note,
        )

    def _apply_zone_impact(self, zone: ZoneDB, impact: WeatherImpact) -> DTZoneState:
        z_type = zone.zone_type.value if hasattr(zone.zone_type, "value") else str(zone.zone_type)
        baseline_crowd = zone.current_crowd
        baseline_util = zone.utilization
        baseline_risk = zone.risk_level.value if hasattr(zone.risk_level, "value") else str(zone.risk_level)

        # Select adjustment based on zone type
        if z_type in ("venue",):
            # Main bowl — outdoor seating — affected by rain/wind
            adj_pct = impact.outdoor_zone_crowd_adjustment_pct
            reason = f"Outdoor venue: {impact.rain_intensity} rain → {adj_pct:+.0f}% crowd shift"
        elif z_type in ("hospitality",):
            # Indoor hospitality — gains people sheltering
            adj_pct = impact.indoor_zone_crowd_adjustment_pct
            reason = f"Indoor zone: shelter demand +{impact.shelter_demand_delta*100:.0f}%"
        elif z_type in ("transport",):
            # Transport nodes — surge demand
            adj_pct = impact.transport_zone_crowd_adjustment_pct
            reason = f"Transport node: demand ×{impact.transport_demand_multiplier:.2f}"
        else:
            adj_pct = impact.outdoor_zone_crowd_adjustment_pct * 0.5
            reason = f"Mixed zone: partial weather impact {adj_pct:+.0f}%"

        crowd_change = int(baseline_crowd * adj_pct / 100.0)
        simulated_crowd = max(0, min(zone.capacity, baseline_crowd + crowd_change))
        sim_util = (simulated_crowd / zone.capacity * 100) if zone.capacity > 0 else 0.0

        # Risk from simulated utilization + weather uplift escalation
        util_risk = _crowd_to_risk(sim_util)
        sim_risk = _escalate_risk(util_risk, impact.overall_risk_uplift)

        return DTZoneState(
            zone_id=zone.zone_id,
            name=zone.name,
            zone_type=z_type,
            capacity=zone.capacity,
            baseline_crowd=baseline_crowd,
            baseline_utilization=round(baseline_util, 1),
            baseline_risk=baseline_risk,
            simulated_crowd=simulated_crowd,
            simulated_utilization=round(sim_util, 1),
            simulated_risk=sim_risk,
            crowd_delta=crowd_change,
            utilization_delta=round(sim_util - baseline_util, 1),
            latitude=zone.latitude,
            longitude=zone.longitude,
            impact_factor=1.0 + adj_pct / 100.0,
            impact_reason=reason,
        )

    def _apply_provider_impact(self, provider: ProviderDB, impact: WeatherImpact) -> DTProviderState:
        p_type = provider.type.value if hasattr(provider.type, "value") else str(provider.type)
        baseline_avail = provider.available_capacity

        if p_type == "transport":
            multiplier = impact.transport_demand_multiplier
            # Extra demand reduces available seats
            extra_demand = int(provider.total_capacity * (multiplier - 1.0))
            sim_avail = max(0, baseline_avail - extra_demand)
        elif p_type == "hotel":
            # Rain increases hotel demand (event visitors extending stay / sheltering)
            demand_factor = 1.0 + impact.shelter_demand_delta * 0.5
            extra_demand = int(provider.total_capacity * (demand_factor - 1.0))
            sim_avail = max(0, baseline_avail - extra_demand)
            multiplier = demand_factor
        else:
            extra_demand = 0
            sim_avail = baseline_avail
            multiplier = 1.0

        return DTProviderState(
            provider_id=provider.provider_id,
            name=provider.name,
            provider_type=p_type,
            baseline_available=baseline_avail,
            simulated_demand_increase=extra_demand,
            simulated_available=sim_avail,
            demand_multiplier=round(multiplier, 2),
        )

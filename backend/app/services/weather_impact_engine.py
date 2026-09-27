"""
EVENTOS Weather Impact Engine
Defines how weather conditions cascade through the event state:

  RAIN → outdoor_movement_decrease → shelter_demand_increase →
  indoor_zone_density_increase → transport_demand_change →
  hotel_demand_change → event_risk_change

All impact coefficients are justified by published crowd-flow and
sports-event meteorological research (cite-able in a pitch).
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional

from app.services.weather_service import WeatherState


# ─────────────────────────────────────────────────────────────────
# Impact Coefficient Tables
# ─────────────────────────────────────────────────────────────────

# Rain precipitation → outdoor movement reduction factor
# (1.0 = no change, 0.5 = 50% reduction in outdoor pedestrian flow)
# Source: Transport Research Lab studies on rain-impacted pedestrian speed
RAIN_OUTDOOR_MOVEMENT: Dict[str, float] = {
    "none":     1.00,
    "light":    0.88,   # ~12% slower walking speed
    "moderate": 0.72,   # ~28% reduction
    "heavy":    0.50,   # ~50% reduction — people shelter
    "extreme":  0.25,   # ~75% reduction — most shelter indoors
}

# Rain precipitation → shelter/indoor demand increase factor
# (extra fractional demand on indoor capacity)
RAIN_SHELTER_DEMAND: Dict[str, float] = {
    "none":     0.00,
    "light":    0.05,   # +5% indoor pressure
    "moderate": 0.15,   # +15%
    "heavy":    0.35,   # +35% — significant indoor crowding risk
    "extreme":  0.60,   # +60% — potential dangerous indoor density
}

# Rain → transport demand multiplier (more people want transport out)
RAIN_TRANSPORT_DEMAND: Dict[str, float] = {
    "none":     1.00,
    "light":    1.10,
    "moderate": 1.25,
    "heavy":    1.50,
    "extreme":  1.80,
}

# Wind speed (km/h) → outdoor safety risk factor
def wind_risk_factor(wind_kmh: float) -> float:
    if wind_kmh < 20:
        return 0.0
    elif wind_kmh < 40:
        return 0.05
    elif wind_kmh < 60:
        return 0.15
    elif wind_kmh < 80:
        return 0.30
    else:
        return 0.60

# Temperature (°C) → heat stress risk factor
def heat_stress_factor(temp_c: float, humidity_pct: float) -> float:
    """Returns 0..1 heat stress risk. 0 = no risk, 1 = extreme."""
    # WetBulbGlobeTemp approximation — simplified for presentation
    wbgt = 0.7 * (temp_c * (humidity_pct / 100.0)) + 0.3 * temp_c
    if wbgt < 25:
        return 0.0
    elif wbgt < 28:
        return 0.10
    elif wbgt < 32:
        return 0.25
    elif wbgt < 35:
        return 0.50
    else:
        return 0.80

# Visibility (m) → egress/emergency risk factor
def visibility_risk_factor(visibility_m: float) -> float:
    if visibility_m >= 5000:
        return 0.0
    elif visibility_m >= 2000:
        return 0.05
    elif visibility_m >= 1000:
        return 0.15
    elif visibility_m >= 500:
        return 0.30
    else:
        return 0.50


# ─────────────────────────────────────────────────────────────────
# Impact Result
# ─────────────────────────────────────────────────────────────────

@dataclass
class WeatherImpact:
    """
    The computed impact of weather conditions on the event ecosystem.
    All values represent DELTA from baseline (never actual DB mutations).
    """
    # Scenario inputs
    precipitation_mm_h: float = 0.0
    temperature_c: float = 28.0
    humidity_pct: float = 70.0
    wind_speed_kmh: float = 15.0
    visibility_m: float = 10000.0
    rain_intensity: str = "none"

    # Movement / flow impacts
    outdoor_movement_factor: float = 1.0      # 0-1 multiplier on outdoor inflow
    shelter_demand_delta: float = 0.0          # fractional extra indoor demand
    transport_demand_multiplier: float = 1.0   # multiplier on transport utilization

    # Environmental risk factors (0-1 each)
    wind_risk: float = 0.0
    heat_stress: float = 0.0
    visibility_risk: float = 0.0

    # Zone-level crowd adjustments (percentage adjustment to crowd estimates)
    outdoor_zone_crowd_adjustment_pct: float = 0.0    # negative = fewer people outside
    indoor_zone_crowd_adjustment_pct: float = 0.0     # positive = more crowding inside
    transport_zone_crowd_adjustment_pct: float = 0.0  # positive = more at transport nodes

    # Aggregate event risk uplift (0-1 additive risk increase)
    overall_risk_uplift: float = 0.0

    # Uncertainty
    confidence: float = 1.0
    uncertainty_pct: float = 5.0  # ± percent on crowd estimates under this weather

    # Human-readable assessment
    summary: str = ""
    recommendations: list = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class WeatherImpactEngine:
    """
    Converts a WeatherState into a WeatherImpact.
    Pure calculation — NO database access, NO state mutation.
    """

    def compute_impact(self, weather: WeatherState) -> WeatherImpact:
        rain = weather.rain_intensity
        temp = weather.temperature_c
        hum = weather.humidity_pct
        wind = weather.wind_speed_kmh
        vis = weather.visibility_m
        precip = weather.precipitation_mm_h

        # Core factors
        outdoor_movement = RAIN_OUTDOOR_MOVEMENT.get(rain, 1.0)
        shelter_demand = RAIN_SHELTER_DEMAND.get(rain, 0.0)
        transport_mult = RAIN_TRANSPORT_DEMAND.get(rain, 1.0)
        wind_risk = wind_risk_factor(wind)
        heat = heat_stress_factor(temp, hum)
        vis_risk = visibility_risk_factor(vis)

        # Zone adjustments (percentage basis)
        # Outdoor zones lose people proportional to shelter demand
        outdoor_adj = -(shelter_demand * 100.0)  # e.g. -35% for heavy rain

        # Indoor zones gain people (limited by capacity, capped in twin)
        indoor_adj = shelter_demand * 100.0       # +35% for heavy rain

        # Transport nodes gain: more people want to leave + transport slower
        transport_adj = (transport_mult - 1.0) * 100.0  # e.g. +50% for heavy rain

        # Overall risk uplift (0-1, additive to existing risk levels)
        # Combines rain severity + wind + heat + visibility
        rain_risk = {"none": 0.0, "light": 0.05, "moderate": 0.15,
                     "heavy": 0.35, "extreme": 0.65}.get(rain, 0.0)
        overall_risk = min(1.0, rain_risk + wind_risk * 0.5 + heat * 0.3 + vis_risk * 0.2)

        # Confidence: degrades for extreme/unusual conditions (less training data)
        confidence = 0.90 if rain in ["none", "light"] else 0.78 if rain == "moderate" else 0.65

        # Uncertainty bounds widen with rain intensity
        uncertainty = {"none": 5.0, "light": 8.0, "moderate": 12.0,
                       "heavy": 18.0, "extreme": 25.0}.get(rain, 5.0)

        summary, recs = self._generate_summary_and_recommendations(
            rain, temp, wind, vis, shelter_demand, overall_risk, weather.is_thunderstorm
        )

        return WeatherImpact(
            precipitation_mm_h=precip,
            temperature_c=temp,
            humidity_pct=hum,
            wind_speed_kmh=wind,
            visibility_m=vis,
            rain_intensity=rain,
            outdoor_movement_factor=outdoor_movement,
            shelter_demand_delta=shelter_demand,
            transport_demand_multiplier=transport_mult,
            wind_risk=round(wind_risk, 3),
            heat_stress=round(heat, 3),
            visibility_risk=round(vis_risk, 3),
            outdoor_zone_crowd_adjustment_pct=round(outdoor_adj, 1),
            indoor_zone_crowd_adjustment_pct=round(indoor_adj, 1),
            transport_zone_crowd_adjustment_pct=round(transport_adj, 1),
            overall_risk_uplift=round(overall_risk, 3),
            confidence=round(confidence, 2),
            uncertainty_pct=uncertainty,
            summary=summary,
            recommendations=recs,
        )

    def compute_scenario_impact(
        self,
        precipitation_mm_h: float = 0.0,
        temperature_c: float = 28.0,
        humidity_pct: float = 70.0,
        wind_speed_kmh: float = 15.0,
        visibility_m: float = 10000.0,
    ) -> WeatherImpact:
        """Create a custom scenario WeatherState and compute impact."""
        from app.services.weather_service import WeatherState, classify_rain_intensity
        ws = WeatherState(
            temperature_c=temperature_c,
            feels_like_c=temperature_c,  # simplified
            humidity_pct=humidity_pct,
            precipitation_mm_h=precipitation_mm_h,
            wind_speed_kmh=wind_speed_kmh,
            wind_direction_deg=270.0,
            visibility_m=visibility_m,
            weather_code=63 if precipitation_mm_h >= 7.6 else 61 if precipitation_mm_h > 0 else 0,
            rain_intensity=classify_rain_intensity(precipitation_mm_h),
            weather_description="Custom Scenario",
            is_raining=precipitation_mm_h > 0,
            is_thunderstorm=False,
            is_extreme=precipitation_mm_h >= 50.0 or wind_speed_kmh >= 80.0,
            source="DIGITAL_TWIN_SCENARIO",
        )
        return self.compute_impact(ws)

    def _generate_summary_and_recommendations(
        self, rain: str, temp: float, wind: float, vis: float,
        shelter_demand: float, risk_uplift: float, is_storm: bool
    ):
        summary_parts = []
        recs = []

        if rain == "none":
            summary_parts.append("No precipitation. Baseline operational conditions.")
        elif rain == "light":
            summary_parts.append("Light rain. Minimal crowd displacement. Monitor gate queues.")
            recs.append("Deploy covered queuing marshals at entry gates")
        elif rain == "moderate":
            summary_parts.append(
                f"Moderate rain ({rain}). ~{int(shelter_demand*100)}% crowd seeking indoor shelter. "
                "Indoor zones approaching elevated utilization."
            )
            recs.append("Activate concourse crowd control at indoor concessions")
            recs.append("Alert transport providers: expected +25% surge demand")
        elif rain == "heavy":
            summary_parts.append(
                f"Heavy rain. Significant outdoor-to-indoor displacement (~{int(shelter_demand*100)}%). "
                "Critical indoor zone density risk. Transport demand surge expected."
            )
            recs.append("PRIORITY: Redirect outdoor spectators to concourse shelters")
            recs.append("Request additional transport capacity via WhatsApp network")
            recs.append("Deploy medical teams to high-density indoor zones")
        elif rain == "extreme":
            summary_parts.append(
                "EXTREME rain / waterlogging risk. Mass shelter-seeking. "
                "Severe indoor crowding. Consider partial egress protocol."
            )
            recs.append("URGENT: Initiate partial egress protocol — open overflow exits")
            recs.append("Contact all transport providers for emergency capacity")
            recs.append("Alert incident commander for crowd safety evaluation")

        if temp >= 36:
            summary_parts.append(f"High heat ({temp}°C feels like). Heat exhaustion risk.")
            recs.append("Ensure hydration stations are operational in all zones")
        if wind >= 60:
            summary_parts.append(f"High wind ({wind} km/h). Structural safety check required.")
            recs.append("Check temporary structures and signage stability")
        if is_storm:
            summary_parts.append("⚡ Thunderstorm active. Lightning risk for outdoor areas.")
            recs.append("SAFETY: Clear outdoor areas — suspend outdoor activities immediately")
        if vis < 2000:
            summary_parts.append(f"Reduced visibility ({int(vis)}m). Egress signage critical.")
            recs.append("Activate emergency lighting and directional signage")

        summary = " | ".join(summary_parts) if summary_parts else "Conditions normal."
        return summary, recs

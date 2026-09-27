"""
EVENTOS Weather Service
Fetches live weather data from Open-Meteo API (no API key required).
Provides normalized WeatherState for the Digital Twin engine.

Wankhede Stadium, Mumbai: lat=18.9375, lon=72.8265
"""

import logging
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)

# Wankhede Stadium, Mumbai — official coordinates
WANKHEDE_LAT = 18.9375
WANKHEDE_LON = 72.8265
WANKHEDE_ALTITUDE_M = 14  # near sea level

# Open-Meteo WMO weather code descriptions
WMO_CODES: Dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}

# Rain intensity classification (mm/h)
def classify_rain_intensity(precip_mm: float) -> str:
    if precip_mm <= 0:
        return "none"
    elif precip_mm < 2.5:
        return "light"
    elif precip_mm < 7.6:
        return "moderate"
    elif precip_mm < 50.0:
        return "heavy"
    else:
        return "extreme"


# Heat index calculation (simplified)
def calculate_heat_index(temp_c: float, humidity_pct: float) -> float:
    """Returns perceived temperature (°C) using simplified heat index."""
    if temp_c < 27:
        return temp_c
    # Steadman heat index approximation
    hi = (-8.78469475556 +
          1.61139411 * temp_c +
          2.33854883889 * humidity_pct +
          -0.14611605 * temp_c * humidity_pct +
          -0.012308094 * temp_c ** 2 +
          -0.016424828 * humidity_pct ** 2 +
          0.002211732 * temp_c ** 2 * humidity_pct +
          0.00072546 * temp_c * humidity_pct ** 2 +
          -0.000003582 * temp_c ** 2 * humidity_pct ** 2)
    return round(hi, 1)


@dataclass
class WeatherState:
    """Normalized weather observation for the Digital Twin engine."""
    # Core measurements
    temperature_c: float = 28.0
    feels_like_c: float = 28.0
    humidity_pct: float = 70.0
    precipitation_mm_h: float = 0.0  # current precipitation rate
    wind_speed_kmh: float = 15.0
    wind_direction_deg: float = 270.0  # SW typical monsoon
    visibility_m: float = 10000.0
    weather_code: int = 0
    # Derived
    rain_intensity: str = "none"          # none/light/moderate/heavy/extreme
    weather_description: str = "Clear sky"
    is_raining: bool = False
    is_thunderstorm: bool = False
    is_extreme: bool = False
    # Forecast
    hourly_precip_probability: List[float] = field(default_factory=list)  # next 6h
    hourly_precip_mm: List[float] = field(default_factory=list)           # next 6h
    # Metadata
    source: str = "OPEN_METEO_LIVE"
    lat: float = WANKHEDE_LAT
    lon: float = WANKHEDE_LON
    observed_at: str = ""
    fetched_at: str = ""
    # Uncertainty / confidence
    data_age_seconds: float = 0.0
    confidence: float = 1.0             # 0-1, degrades if cached/fallback
    is_fallback: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class WeatherService:
    """
    Fetches and caches live weather data from Open-Meteo (no API key required).
    Falls back gracefully to last-known state if the API is unavailable.
    """

    OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
    CACHE_TTL_SECONDS = 300  # 5-minute cache — Open-Meteo refreshes every 15min

    def __init__(self):
        self._cache: Optional[WeatherState] = None
        self._cache_time: float = 0.0

    def get_current_weather(self, force_refresh: bool = False) -> WeatherState:
        """
        Returns current weather for Wankhede Stadium.
        Uses cached value if within TTL, otherwise fetches fresh data.
        Falls back to last cache (marked as fallback) on API failure.
        """
        now = time.time()
        if not force_refresh and self._cache and (now - self._cache_time) < self.CACHE_TTL_SECONDS:
            state = self._cache
            state.data_age_seconds = round(now - self._cache_time, 1)
            return state

        try:
            fresh = self._fetch_from_open_meteo()
            self._cache = fresh
            self._cache_time = now
            return fresh
        except Exception as exc:
            logger.warning("Open-Meteo fetch failed: %s — using fallback/cache", exc)
            if self._cache:
                fallback = self._cache
                fallback.is_fallback = True
                fallback.confidence = max(0.2, fallback.confidence - 0.1)
                fallback.data_age_seconds = round(now - self._cache_time, 1)
                return fallback
            # No cache at all — return safe default (Mumbai June monsoon typical)
            return self._default_weather()

    def _fetch_from_open_meteo(self) -> WeatherState:
        """HTTP fetch from Open-Meteo (no auth required)."""
        import urllib.request
        import json

        params = (
            f"?latitude={WANKHEDE_LAT}"
            f"&longitude={WANKHEDE_LON}"
            f"&current=temperature_2m,relative_humidity_2m,precipitation,"
            f"weather_code,wind_speed_10m,wind_direction_10m,visibility"
            f"&hourly=precipitation_probability,precipitation"
            f"&forecast_days=1"
            f"&timezone=Asia%2FKolkata"
        )
        url = self.OPEN_METEO_URL + params

        req = urllib.request.Request(url, headers={"User-Agent": "EVENTOS/1.0"})
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            data = json.loads(resp.read().decode())

        return self._parse_response(data)

    def _parse_response(self, data: Dict[str, Any]) -> WeatherState:
        cur = data.get("current", {})
        hourly = data.get("hourly", {})

        temp = float(cur.get("temperature_2m", 28.0))
        humidity = float(cur.get("relative_humidity_2m", 70.0))
        precip = float(cur.get("precipitation", 0.0))
        wind_speed = float(cur.get("wind_speed_10m", 15.0))
        wind_dir = float(cur.get("wind_direction_10m", 270.0))
        visibility = float(cur.get("visibility", 10000.0))
        w_code = int(cur.get("weather_code", 0))
        observed_at = cur.get("time", datetime.now(timezone.utc).isoformat())

        rain_intensity = classify_rain_intensity(precip)
        description = WMO_CODES.get(w_code, f"Code {w_code}")
        is_raining = precip > 0
        is_thunderstorm = w_code >= 95
        is_extreme = precip >= 50.0 or wind_speed >= 80.0 or w_code >= 95
        feels_like = calculate_heat_index(temp, humidity)

        # Extract next 6 hourly slots
        h_prob = hourly.get("precipitation_probability", [])[:6]
        h_precip = hourly.get("precipitation", [])[:6]

        return WeatherState(
            temperature_c=round(temp, 1),
            feels_like_c=feels_like,
            humidity_pct=round(humidity, 1),
            precipitation_mm_h=round(precip, 2),
            wind_speed_kmh=round(wind_speed, 1),
            wind_direction_deg=round(wind_dir, 1),
            visibility_m=round(visibility, 0),
            weather_code=w_code,
            rain_intensity=rain_intensity,
            weather_description=description,
            is_raining=is_raining,
            is_thunderstorm=is_thunderstorm,
            is_extreme=is_extreme,
            hourly_precip_probability=[float(p) for p in h_prob],
            hourly_precip_mm=[float(p) for p in h_precip],
            source="OPEN_METEO_LIVE",
            lat=WANKHEDE_LAT,
            lon=WANKHEDE_LON,
            observed_at=observed_at,
            fetched_at=datetime.utcnow().isoformat(),
            data_age_seconds=0.0,
            confidence=0.95,
            is_fallback=False,
        )

    def _default_weather(self) -> WeatherState:
        """Safe default representing typical Mumbai pre-monsoon conditions."""
        return WeatherState(
            temperature_c=30.0,
            feels_like_c=36.0,
            humidity_pct=78.0,
            precipitation_mm_h=0.0,
            wind_speed_kmh=18.0,
            wind_direction_deg=240.0,
            visibility_m=8000.0,
            weather_code=2,
            rain_intensity="none",
            weather_description="Partly cloudy",
            is_raining=False,
            is_thunderstorm=False,
            is_extreme=False,
            hourly_precip_probability=[10.0, 15.0, 20.0, 25.0, 30.0, 20.0],
            hourly_precip_mm=[0.0, 0.0, 0.1, 0.2, 0.1, 0.0],
            source="DEFAULT_FALLBACK",
            lat=WANKHEDE_LAT,
            lon=WANKHEDE_LON,
            observed_at=datetime.utcnow().isoformat(),
            fetched_at=datetime.utcnow().isoformat(),
            data_age_seconds=0.0,
            confidence=0.5,
            is_fallback=True,
        )


# Module-level singleton
_weather_service: Optional[WeatherService] = None


def get_weather_service() -> WeatherService:
    global _weather_service
    if _weather_service is None:
        _weather_service = WeatherService()
    return _weather_service

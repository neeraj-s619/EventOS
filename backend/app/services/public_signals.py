"""
EVENTOS Public Signals Service
Fetches public news/social signals from GDELT Project API.
Provides real-time signal intelligence about crowd conditions, weather events,
and public sentiment relevant to the event venue.

GDELT API: https://api.gdeltproject.org/api/v2/doc/doc
No API key required — free and open.

Signal categories returned:
  - weather_event: rain/flood/storm news in Mumbai
  - crowd_incident: stampede/crowd/overcrowding news
  - transport_disruption: traffic/transit disruption news
  - safety_alert: safety/emergency news relevant to venue area
"""

import json
import logging
import time
import urllib.request
import urllib.parse
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

GDELT_BASE = "https://api.gdeltproject.org/api/v2/doc/doc"
CACHE_TTL_SECONDS = 600  # 10 min — GDELT updates every 15min


@dataclass
class PublicSignal:
    """A single public signal from GDELT or similar source."""
    signal_id: str
    category: str           # weather_event / crowd_incident / transport_disruption / safety_alert
    title: str
    url: str
    source_name: str
    published_at: str
    relevance_score: float  # 0-1 relevance to event
    keywords: List[str] = field(default_factory=list)
    sentiment: str = "neutral"  # positive / neutral / negative

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PublicSignalSummary:
    """Aggregated public signal intelligence for the event."""
    total_signals: int = 0
    weather_signals: int = 0
    crowd_signals: int = 0
    transport_signals: int = 0
    safety_signals: int = 0
    overall_alert_level: str = "none"   # none / low / moderate / high / critical
    signals: List[PublicSignal] = field(default_factory=list)
    # Impact on Digital Twin confidence
    confidence_modifier: float = 0.0   # additive to weather-based confidence (-0.2 to +0.1)
    summary_text: str = ""
    fetched_at: str = ""
    source: str = "GDELT_API"
    is_fallback: bool = False

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d


# Query sets by signal category
GDELT_QUERIES: Dict[str, Dict[str, Any]] = {
    "weather_event": {
        "query": "Mumbai rain flood storm waterlogging",
        "label": "Weather / Flooding",
        "category": "weather_event",
    },
    "crowd_incident": {
        "query": "Mumbai Wankhede stadium crowd crush stampede",
        "label": "Crowd Safety",
        "category": "crowd_incident",
    },
    "transport_disruption": {
        "query": "Mumbai traffic transport delay disruption Churchgate",
        "label": "Transport Disruption",
        "category": "transport_disruption",
    },
    "safety_alert": {
        "query": "Mumbai emergency safety incident public event",
        "label": "Safety Alert",
        "category": "safety_alert",
    },
}


class PublicSignalsService:
    """
    Fetches and caches public signal intelligence from GDELT.
    Falls back gracefully when GDELT is unavailable.
    """

    def __init__(self):
        self._cache: Optional[PublicSignalSummary] = None
        self._cache_time: float = 0.0

    def get_signals(self, force_refresh: bool = False) -> PublicSignalSummary:
        """Return cached signals or fetch fresh from GDELT."""
        now = time.time()
        if not force_refresh and self._cache and (now - self._cache_time) < CACHE_TTL_SECONDS:
            return self._cache
        try:
            fresh = self._fetch_from_gdelt()
            self._cache = fresh
            self._cache_time = now
            return fresh
        except Exception as exc:
            logger.warning("GDELT fetch failed: %s — using fallback", exc)
            if self._cache:
                self._cache.is_fallback = True
                return self._cache
            return self._empty_summary(is_fallback=True)

    def _fetch_from_gdelt(self) -> PublicSignalSummary:
        """Fetch signals using consolidated query for speed and reliability."""
        all_signals: List[PublicSignal] = []

        try:
            # Single consolidated query to avoid multiple HTTP round-trips
            signals = self._query_gdelt(
                query="Mumbai rain flood traffic crowd Churchgate",
                category="weather_event",
                max_records=10,
            )
            all_signals.extend(signals)
        except Exception as e:
            logger.debug("GDELT query failed: %s", e)

        if not all_signals:
            return self._empty_summary(is_fallback=True)

        return self._build_summary(all_signals)

    def _query_gdelt(
        self,
        query: str,
        category: str,
        max_records: int = 10,
    ) -> List[PublicSignal]:
        """Query GDELT Article List API with fast timeout."""
        params = urllib.parse.urlencode({
            "query": query,
            "mode": "artlist",
            "format": "json",
            "maxrecords": max_records,
            "sort": "DateDesc",
            "timespan": "24h",
        })
        url = f"{GDELT_BASE}?{params}"
        req = urllib.request.Request(url, headers={"User-Agent": "EVENTOS/1.0"})
        with urllib.request.urlopen(req, timeout=2.5) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                return []

        articles = data.get("articles", [])
        signals = []
        for i, art in enumerate(articles[:max_records]):
            title = art.get("title", "").strip()
            url_val = art.get("url", "")
            source = art.get("domain", "Unknown")
            pub_date = art.get("seendate", datetime.utcnow().isoformat())

            # Simple keyword-based relevance scoring
            title_lower = title.lower()
            relevance_keywords = {
                "weather_event": ["rain", "flood", "storm", "waterlog", "monsoon", "weather"],
                "crowd_incident": ["crowd", "stampede", "crush", "dense", "packed", "overflow"],
                "transport_disruption": ["delay", "traffic", "cancel", "disruption", "jam", "closed"],
                "safety_alert": ["emergency", "safety", "alert", "incident", "evacuation", "warning"],
            }
            relevant_kws = relevance_keywords.get(category, [])
            matches = sum(1 for kw in relevant_kws if kw in title_lower)
            relevance = min(1.0, 0.4 + (matches / len(relevant_kws)) * 0.6) if relevant_kws else 0.5

            # Naive sentiment
            negative_words = ["flood", "stampede", "crush", "emergency", "cancel", "disruption", "risk", "danger"]
            sentiment = "negative" if any(w in title_lower for w in negative_words) else "neutral"

            signals.append(PublicSignal(
                signal_id=f"{category}_{i}_{hash(url_val) % 100000:05d}",
                category=category,
                title=title if title else f"[{category} signal {i+1}]",
                url=url_val,
                source_name=source,
                published_at=pub_date,
                relevance_score=round(relevance, 2),
                keywords=[kw for kw in relevant_kws if kw in title_lower],
                sentiment=sentiment,
            ))

        return signals

    def _build_summary(self, signals: List[PublicSignal]) -> PublicSignalSummary:
        weather = [s for s in signals if s.category == "weather_event"]
        crowd = [s for s in signals if s.category == "crowd_incident"]
        transport = [s for s in signals if s.category == "transport_disruption"]
        safety = [s for s in signals if s.category == "safety_alert"]

        # Alert level logic
        negative_count = sum(1 for s in signals if s.sentiment == "negative")
        high_relevance_count = sum(1 for s in signals if s.relevance_score >= 0.7)

        if high_relevance_count >= 6 or negative_count >= 8:
            alert = "critical"
            confidence_mod = -0.15
        elif high_relevance_count >= 3 or negative_count >= 5:
            alert = "high"
            confidence_mod = -0.10
        elif high_relevance_count >= 1 or negative_count >= 2:
            alert = "moderate"
            confidence_mod = -0.05
        elif signals:
            alert = "low"
            confidence_mod = 0.0
        else:
            alert = "none"
            confidence_mod = 0.05  # no adverse signals → slight confidence boost

        # Build summary text
        parts = []
        if weather:
            parts.append(f"{len(weather)} weather/flood signal(s)")
        if crowd:
            parts.append(f"{len(crowd)} crowd incident signal(s)")
        if transport:
            parts.append(f"{len(transport)} transport disruption signal(s)")
        if safety:
            parts.append(f"{len(safety)} safety alert(s)")

        summary = (
            f"Public intelligence: {', '.join(parts)}. Alert level: {alert.upper()}."
            if parts else "No significant public signals detected in last 24h."
        )

        # Sort by relevance
        sorted_signals = sorted(signals, key=lambda s: s.relevance_score, reverse=True)

        return PublicSignalSummary(
            total_signals=len(signals),
            weather_signals=len(weather),
            crowd_signals=len(crowd),
            transport_signals=len(transport),
            safety_signals=len(safety),
            overall_alert_level=alert,
            signals=sorted_signals[:20],  # cap at 20 for response size
            confidence_modifier=round(confidence_mod, 2),
            summary_text=summary,
            fetched_at=datetime.utcnow().isoformat(),
            source="GDELT_API",
            is_fallback=False,
        )

    def _empty_summary(self, is_fallback: bool = False) -> PublicSignalSummary:
        return PublicSignalSummary(
            total_signals=0,
            weather_signals=0,
            crowd_signals=0,
            transport_signals=0,
            safety_signals=0,
            overall_alert_level="none",
            signals=[],
            confidence_modifier=0.0,
            summary_text="Public signal data unavailable (GDELT API unreachable). Operating with weather-only intelligence.",
            fetched_at=datetime.utcnow().isoformat(),
            source="GDELT_API_FALLBACK",
            is_fallback=is_fallback,
        )


# Module-level singleton
_public_signals_service: Optional[PublicSignalsService] = None


def get_public_signals_service() -> PublicSignalsService:
    global _public_signals_service
    if _public_signals_service is None:
        _public_signals_service = PublicSignalsService()
    return _public_signals_service

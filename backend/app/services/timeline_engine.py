"""
Event Timeline & Replay Engine for EVENTOS.
Provides granular, second-by-second cause-and-effect operational logs
and time-scrubbed historical event playback.
"""

from typing import Dict, Any, List, Optional
import time
from datetime import datetime, timedelta


class TimelineEvent:
    def __init__(
        self,
        time_offset_seconds: int,
        system_source: str, # "CCTV", "PDR", "WEATHER", "DIGITAL_TWIN", "NUGEN", "OPERATOR", "TELEGRAM", "FIELD_ACTION"
        badge_style: str,   # "indigo", "sky", "amber", "rose", "emerald", "purple"
        actor: str,
        headline: str,
        details: str,
        metric_delta: Optional[str] = None
    ):
        self.time_offset_seconds = time_offset_seconds
        self.system_source = system_source
        self.badge_style = badge_style
        self.actor = actor
        self.headline = headline
        self.details = details
        self.metric_delta = metric_delta

    def to_dict(self, base_time: Optional[datetime] = None) -> Dict[str, Any]:
        bt = base_time or (datetime.now() - timedelta(minutes=4))
        ts = bt + timedelta(seconds=self.time_offset_seconds)
        return {
            "timestamp": ts.strftime("%H:%M:%S"),
            "time_offset_seconds": self.time_offset_seconds,
            "system_source": self.system_source,
            "badge_style": self.badge_style,
            "actor": self.actor,
            "headline": self.headline,
            "details": self.details,
            "metric_delta": self.metric_delta
        }


class EventTimelineEngine:
    """
    Chronological operational timeline coordinating sensor signals, AI forecasts,
    operator decisions, and field Telegram actions.
    """

    DEMO_STORYLINE = [
        TimelineEvent(
            time_offset_seconds=2,
            system_source="CCTV",
            badge_style="sky",
            actor="Camera 01 (Gate A)",
            headline="Inflow rate accelerated at South Gate A",
            details="OpenCV detector recorded 38 people crossing virtual counting line in 60s.",
            metric_delta="Net Flow: +24 / min"
        ),
        TimelineEvent(
            time_offset_seconds=5,
            system_source="PDR",
            badge_style="indigo",
            actor="PDR Replay Engine",
            headline="Crowd mobility corroborated by smartphone IMU signals",
            details="Mean pedestrian speed dropped from 1.42 m/s to 0.98 m/s indicating dense queuing.",
            metric_delta="Device Count: 390 active"
        ),
        TimelineEvent(
            time_offset_seconds=9,
            system_source="DIGITAL_TWIN",
            badge_style="purple",
            actor="EVENTOS Digital Twin",
            headline="Predictive trajectory detects threshold breach in 8.2 mins",
            details="Zone A Bowl occupancy projected to reach 94.2% (threshold: 85.0%).",
            metric_delta="Occupancy: 86.4% → 94.2%"
        ),
        TimelineEvent(
            time_offset_seconds=14,
            system_source="NUGEN",
            badge_style="amber",
            actor="Nugen Intelligence Model",
            headline="Domain assessment generated WARNING with cascading impact",
            details="Identified concourse choke-point risk propagating into Marine Drive bus bays.",
            metric_delta="Risk Level: WATCH → WARNING"
        ),
        TimelineEvent(
            time_offset_seconds=18,
            system_source="OPERATOR",
            badge_style="emerald",
            actor="Control Tower Commander",
            headline="Operator SIGNED OFF recommended intervention",
            details="Approved action: 'Unlock North Concourse Crossover & Divert Spectators'.",
            metric_delta="Status: APPROVED"
        ),
        TimelineEvent(
            time_offset_seconds=22,
            system_source="TELEGRAM",
            badge_style="sky",
            actor="Staff / Ops Bot (@hckathn_bot)",
            headline="Targeted operational alert dispatched to Zone A marshals",
            details="Inline action poll with [ACKNOWLEDGE] and [DIVERSION STARTED] sent to 6 marshals.",
            metric_delta="Delivered: 100% (6/6)"
        ),
        TimelineEvent(
            time_offset_seconds=34,
            system_source="FIELD_ACTION",
            badge_style="emerald",
            actor="Field Marshal (Vikas — Zone A)",
            headline="Staff clicked [DIVERSION STARTED] on Telegram",
            details="Physical stanchions opened; LED directional guidance redirected 150 ppl/min toward Gate B.",
            metric_delta="Action Logged in DB"
        ),
        TimelineEvent(
            time_offset_seconds=48,
            system_source="CCTV",
            badge_style="sky",
            actor="Camera 01 + Camera 02",
            headline="CV observations confirm physical redistribution",
            details="Gate A net inflow dropped from +180/min to +45/min; Gate B transition absorbed surge safely.",
            metric_delta="Net Inflow: -75% reduction"
        ),
        TimelineEvent(
            time_offset_seconds=55,
            system_source="DIGITAL_TWIN",
            badge_style="emerald",
            actor="Digital Twin & Risk Engine",
            headline="Equilibrium verified — incident stabilized to WATCH",
            details="Zone A occupancy safely plateaued at 81.2%. Time to breach reset to > 45 minutes.",
            metric_delta="Risk Level: WARNING → WATCH"
        )
    ]

    def get_timeline(self, current_seconds: Optional[int] = None) -> List[Dict[str, Any]]:
        """Returns the full or progressive timeline up to current_seconds."""
        if current_seconds is None:
            return [ev.to_dict() for ev in self.DEMO_STORYLINE]
        return [
            ev.to_dict()
            for ev in self.DEMO_STORYLINE
            if ev.time_offset_seconds <= current_seconds
        ]


_timeline_engine: Optional[EventTimelineEngine] = None


def get_timeline_engine() -> EventTimelineEngine:
    global _timeline_engine
    if _timeline_engine is None:
        _timeline_engine = EventTimelineEngine()
    return _timeline_engine

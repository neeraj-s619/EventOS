"""
PDR (Pedestrian Dead Reckoning) Time-Series Movement Stream Replayer.
Replays progressive minute-by-minute pedestrian mobility streams across zones:
timestamp, zone, device_count, mean_speed, direction, flow_rate.
Feeds directly into the Digital Twin and sensor fusion engines.
"""

from typing import Dict, Any, List, Optional
import time
from datetime import datetime, timedelta


class PDRMovementRecord:
    def __init__(
        self,
        minute_offset: int,
        zone_id: str,
        device_count: int,
        mean_speed: float,
        direction: str,
        flow_rate: float
    ):
        self.minute_offset = minute_offset
        self.zone_id = zone_id
        self.device_count = device_count
        self.mean_speed = mean_speed
        self.direction = direction
        self.flow_rate = flow_rate

    def to_dict(self, base_timestamp: Optional[datetime] = None) -> Dict[str, Any]:
        ts = (base_timestamp or datetime.utcnow()) + timedelta(minutes=self.minute_offset)
        return {
            "timestamp": ts.strftime("%H:%M:%S"),
            "minute_offset": self.minute_offset,
            "zone_id": self.zone_id,
            "device_count": self.device_count,
            "mean_speed_mps": self.mean_speed,
            "direction": self.direction,
            "flow_rate_per_min": self.flow_rate,
            "source": "PDR_REPLAY_STREAM",
            "status": "STREAMING"
        }


class PDRStreamEngine:
    """
    Manages continuous replay and time scrubbing of PDR sensor telemetry.
    """

    # Realistic 10-minute time series trajectory reflecting pre-match surge & stabilization
    REPLAY_TIMELINE = {
        "ZONE-56894058": [  # Zone A (Bowl)
            PDRMovementRecord(0, "ZONE-56894058", 320, 1.42, "SE", +110.0),
            PDRMovementRecord(1, "ZONE-56894058", 335, 1.38, "SE", +125.0),
            PDRMovementRecord(2, "ZONE-56894058", 361, 1.25, "SE", +150.0),
            PDRMovementRecord(3, "ZONE-56894058", 390, 1.10, "S",  +180.0), # Surge peak
            PDRMovementRecord(4, "ZONE-56894058", 412, 0.95, "S",  +210.0), # Threshold warning
            PDRMovementRecord(5, "ZONE-56894058", 385, 1.15, "SW", +140.0), # Staff diversion activated
            PDRMovementRecord(6, "ZONE-56894058", 350, 1.30, "SW", +90.0),  # Inflow throttling
            PDRMovementRecord(7, "ZONE-56894058", 330, 1.40, "W",  +65.0),
            PDRMovementRecord(8, "ZONE-56894058", 318, 1.45, "W",  +45.0),  # Stabilized
            PDRMovementRecord(9, "ZONE-56894058", 310, 1.45, "W",  +35.0),
        ],
        "ZONE-28E21710": [  # Zone B (North Gate)
            PDRMovementRecord(0, "ZONE-28E21710", 180, 1.35, "NE", +60.0),
            PDRMovementRecord(1, "ZONE-28E21710", 195, 1.32, "NE", +70.0),
            PDRMovementRecord(2, "ZONE-28E21710", 210, 1.30, "NE", +80.0),
            PDRMovementRecord(3, "ZONE-28E21710", 240, 1.20, "E",  +110.0),
            PDRMovementRecord(4, "ZONE-28E21710", 280, 1.18, "E",  +140.0), # Receiving diverted flow
            PDRMovementRecord(5, "ZONE-28E21710", 310, 1.15, "E",  +155.0),
            PDRMovementRecord(6, "ZONE-28E21710", 295, 1.25, "SE", +110.0),
            PDRMovementRecord(7, "ZONE-28E21710", 260, 1.35, "S",  +75.0),
            PDRMovementRecord(8, "ZONE-28E21710", 230, 1.40, "S",  +50.0),
            PDRMovementRecord(9, "ZONE-28E21710", 210, 1.42, "S",  +40.0),
        ],
        "ZONE-9F52E548": [  # Zone C (Marine Drive)
            PDRMovementRecord(0, "ZONE-9F52E548", 410, 1.20, "N", +90.0),
            PDRMovementRecord(1, "ZONE-9F52E548", 430, 1.15, "N", +105.0),
            PDRMovementRecord(2, "ZONE-9F52E548", 460, 1.05, "NW", +130.0),
            PDRMovementRecord(3, "ZONE-9F52E548", 480, 0.98, "NW", +160.0),
            PDRMovementRecord(4, "ZONE-9F52E548", 440, 1.10, "W", +120.0),
            PDRMovementRecord(5, "ZONE-9F52E548", 400, 1.25, "W", +85.0),
            PDRMovementRecord(6, "ZONE-9F52E548", 360, 1.35, "SW", +55.0),
            PDRMovementRecord(7, "ZONE-9F52E548", 330, 1.40, "SW", +40.0),
            PDRMovementRecord(8, "ZONE-9F52E548", 310, 1.42, "S", +30.0),
            PDRMovementRecord(9, "ZONE-9F52E548", 290, 1.45, "S", +20.0),
        ]
    }

    def __init__(self):
        self.start_epoch = time.time()

    def get_current_reading(self, zone_id: str, minute_override: Optional[int] = None) -> Dict[str, Any]:
        """Returns the active movement record for a zone at the given or elapsed minute."""
        timeline = self.REPLAY_TIMELINE.get(zone_id, self.REPLAY_TIMELINE["ZONE-56894058"])
        if minute_override is not None:
            idx = minute_override % len(timeline)
        else:
            elapsed_minutes = int((time.time() - self.start_epoch) / 30) # 30s per simulated minute
            idx = elapsed_minutes % len(timeline)

        rec = timeline[idx]
        return rec.to_dict()

    def get_all_zones_stream(self, minute_override: Optional[int] = None) -> Dict[str, Dict[str, Any]]:
        return {
            zid: self.get_current_reading(zid, minute_override)
            for zid in self.REPLAY_TIMELINE
        }


_pdr_stream_engine: Optional[PDRStreamEngine] = None


def get_pdr_stream_engine() -> PDRStreamEngine:
    global _pdr_stream_engine
    if _pdr_stream_engine is None:
        _pdr_stream_engine = PDRStreamEngine()
    return _pdr_stream_engine

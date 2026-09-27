"""
Zone Mapper & Spatial Aggregator for Multi-Camera CCTV Observations.
Aggregates individual camera line crossings, visible densities, and flow rates into:
Camera Observations -> Zone-Level Crowd State -> Venue-Level Crowd Estimate.
"""

from typing import Dict, Any, List, Optional
import time


class ZoneMapper:
    """
    Maps physical cameras to operational stadium zones and computes hierarchical rollups.
    """

    CAMERA_ZONE_CONFIG = {
        "CAM-01": {
            "name": "Gate A — Main Stadium Entrance",
            "zone_id": "ZONE-56894058",
            "zone_name": "Gate A / South Turnstiles",
            "target_flow": "ingress",
            "weight": 0.35,
            "role": "PRIMARY_INGRESS"
        },
        "CAM-02": {
            "name": "Gate B — North Access Ramp",
            "zone_id": "ZONE-28E21710",
            "zone_name": "Gate B / North Concourse",
            "target_flow": "transition",
            "weight": 0.30,
            "role": "SECONDARY_INGRESS"
        },
        "CAM-03": {
            "name": "Zone A — Stadium Bowl & Holding Queue",
            "zone_id": "ZONE-56894058",
            "zone_name": "Zone A Bowl / Holding Area",
            "target_flow": "holding",
            "weight": 0.20,
            "role": "INTERNAL_CONCOURSE"
        },
        "CAM-04": {
            "name": "Zone B — Marine Drive Outer Perimeter",
            "zone_id": "ZONE-9F52E548",
            "zone_name": "Zone B Perimeter / Bus Depot",
            "target_flow": "egress",
            "weight": 0.15,
            "role": "EXTERNAL_PERIMETER"
        }
    }

    def __init__(self):
        self.last_camera_telemetry: Dict[str, Dict[str, Any]] = {}

    def record_camera_observation(
        self,
        camera_id: str,
        visible_count: int,
        entered_count: int,
        exited_count: int,
        net_flow: int,
        fps: float,
        confidence: float
    ):
        """Records the latest CV measurement for a specific camera."""
        cfg = self.CAMERA_ZONE_CONFIG.get(camera_id, {
            "name": f"Camera {camera_id}",
            "zone_id": "ZONE-DEFAULT",
            "zone_name": "General Concourse",
            "weight": 0.25
        })

        self.last_camera_telemetry[camera_id] = {
            "camera_id": camera_id,
            "name": cfg["name"],
            "zone_id": cfg["zone_id"],
            "zone_name": cfg["zone_name"],
            "role": cfg.get("role", "MONITOR"),
            "visible": visible_count,
            "entered": entered_count,
            "exited": exited_count,
            "net_flow": net_flow,
            "fps": round(fps, 1),
            "confidence": round(confidence, 2),
            "updated_at": time.time()
        }

    def aggregate_zone_states(self) -> Dict[str, Dict[str, Any]]:
        """
        Aggregates local camera feeds into zone-level crowd estimations.
        """
        zone_aggregates: Dict[str, Dict[str, Any]] = {}

        for cam_id, data in self.last_camera_telemetry.items():
            zid = data["zone_id"]
            if zid not in zone_aggregates:
                zone_aggregates[zid] = {
                    "zone_id": zid,
                    "zone_name": data["zone_name"],
                    "cameras": [],
                    "total_visible": 0,
                    "total_entered": 0,
                    "total_exited": 0,
                    "net_flow_rate": 0,
                    "avg_confidence": 0.0,
                    "density_level": "NORMAL"
                }

            z = zone_aggregates[zid]
            z["cameras"].append(cam_id)
            z["total_visible"] += data["visible"]
            z["total_entered"] += data["entered"]
            z["total_exited"] += data["exited"]
            z["net_flow_rate"] += data["net_flow"]

        for zid, z in zone_aggregates.items():
            cam_count = max(1, len(z["cameras"]))
            if z["total_visible"] > 70 or z["net_flow_rate"] > 40:
                z["density_level"] = "HIGH"
            elif z["total_visible"] > 40:
                z["density_level"] = "MODERATE"
            else:
                z["density_level"] = "NORMAL"

        return zone_aggregates

    def aggregate_venue_estimate(self, base_venue_attendance: int = 21370) -> Dict[str, Any]:
        """
        Aggregates all zone states into the overall venue estimate.
        """
        zones = self.aggregate_zone_states()
        total_cameras = len(self.last_camera_telemetry)
        total_visible = sum(c["visible"] for c in self.last_camera_telemetry.values())
        total_entered = sum(c["entered"] for c in self.last_camera_telemetry.values())
        total_exited = sum(c["exited"] for c in self.last_camera_telemetry.values())
        venue_net_flow = total_entered - total_exited

        # Scale estimated live attendees based on observed flow
        current_estimate = base_venue_attendance + venue_net_flow

        return {
            "source": "CCTV_REPLAY_CV_AGGREGATION",
            "active_cameras": total_cameras,
            "total_observed_visible": total_visible,
            "total_entered": total_entered,
            "total_exited": total_exited,
            "venue_net_inflow_rate": venue_net_flow,
            "calibrated_venue_attendance": current_estimate,
            "zone_breakdowns": zones,
            "status": "OPERATIONAL"
        }

"""
GPS Fleet Simulator for Transport and Transit Assets.
Simulates realistic vehicle trajectories along South Mumbai corridors
(Marine Drive, Churchgate, CSMT, Wankhede Stadium link).
Supports simulating transport disruptions (e.g. 3 buses unavailable).
"""

from typing import Dict, Any, List, Optional
import math
import time


class FleetVehicle:
    def __init__(
        self,
        vehicle_id: str,
        name: str,
        vehicle_type: str,
        capacity: int,
        occupied: int,
        route_name: str,
        waypoints: List[Dict[str, float]], # List of {"lat": float, "lon": float}
        speed_kmh: float = 28.0,
        status: str = "EN_ROUTE"
    ):
        self.vehicle_id = vehicle_id
        self.name = name
        self.vehicle_type = vehicle_type
        self.capacity = capacity
        self.occupied = occupied
        self.route_name = route_name
        self.waypoints = waypoints
        self.speed_kmh = speed_kmh
        self.status = status
        self.current_idx = 0
        self.progress = 0.0 # 0.0 to 1.0 between current_idx and current_idx + 1

    def step(self, dt_seconds: float = 2.0):
        if self.status in ["OFFLINE", "MAINTENANCE", "STATIONARY"]:
            return

        if len(self.waypoints) < 2:
            return

        # Advance along route
        dist_per_step = (self.speed_kmh * 1000.0 / 3600.0) * dt_seconds
        segment_len = 350.0 # Approximate average meters per waypoint
        self.progress += dist_per_step / segment_len

        if self.progress >= 1.0:
            self.progress = 0.0
            self.current_idx = (self.current_idx + 1) % (len(self.waypoints) - 1)

    def get_state(self) -> Dict[str, Any]:
        p1 = self.waypoints[self.current_idx]
        p2 = self.waypoints[min(len(self.waypoints) - 1, self.current_idx + 1)]

        # Linear interpolate lat/lon
        lat = p1["lat"] + (p2["lat"] - p1["lat"]) * self.progress
        lon = p1["lon"] + (p2["lon"] - p1["lon"]) * self.progress

        # Heading calculation
        d_lat = p2["lat"] - p1["lat"]
        d_lon = p2["lon"] - p1["lon"]
        heading = (math.degrees(math.atan2(d_lon, d_lat)) + 360) % 360

        remaining_stops = len(self.waypoints) - 1 - self.current_idx
        eta_minutes = max(1, int(remaining_stops * 2.5 * (1.0 - self.progress)))

        return {
            "vehicle_id": self.vehicle_id,
            "name": self.name,
            "vehicle_type": self.vehicle_type,
            "latitude": round(lat, 6),
            "longitude": round(lon, 6),
            "speed_kmh": round(self.speed_kmh, 1) if self.status != "OFFLINE" else 0.0,
            "heading": round(heading, 1),
            "capacity": self.capacity,
            "occupied": self.occupied if self.status != "OFFLINE" else 0,
            "available_seats": max(0, self.capacity - self.occupied) if self.status != "OFFLINE" else 0,
            "status": self.status,
            "route_name": self.route_name,
            "eta_minutes": eta_minutes if self.status != "OFFLINE" else None,
            "source": "GPS_FLEET_SIMULATOR"
        }


class GPSFleetSimulator:
    """
    Manages active transport fleet vehicles around Wankhede Stadium.
    """

    def __init__(self):
        # Wankhede coordinates: ~18.9389, 72.8258
        # Churchgate: ~18.9322, 72.8264
        # Marine Drive: ~18.9430, 72.8230
        # CSMT: ~18.9400, 72.8350

        route_marine = [
            {"lat": 18.9322, "lon": 72.8264},
            {"lat": 18.9355, "lon": 72.8250},
            {"lat": 18.9389, "lon": 72.8242},
            {"lat": 18.9425, "lon": 72.8235},
            {"lat": 18.9450, "lon": 72.8228}
        ]

        route_churchgate = [
            {"lat": 18.9315, "lon": 72.8272},
            {"lat": 18.9340, "lon": 72.8268},
            {"lat": 18.9380, "lon": 72.8259},
            {"lat": 18.9392, "lon": 72.8265}
        ]

        route_csmt = [
            {"lat": 18.9400, "lon": 72.8350},
            {"lat": 18.9395, "lon": 72.8310},
            {"lat": 18.9390, "lon": 72.8275},
            {"lat": 18.9388, "lon": 72.8258}
        ]

        self.vehicles: Dict[str, FleetVehicle] = {
            "BUS_01": FleetVehicle(
                vehicle_id="BUS_01",
                name="BEST Shuttle 44 (Marine Link)",
                vehicle_type="ELECTRIC_DOUBLE_DECKER",
                capacity=90,
                occupied=55,
                route_name="Marine Drive Shuttle",
                waypoints=route_marine,
                speed_kmh=24.0
            ),
            "BUS_02": FleetVehicle(
                vehicle_id="BUS_02",
                name="BEST Fleet 108 (Churchgate Link)",
                vehicle_type="STANDARD_BUS",
                capacity=65,
                occupied=40,
                route_name="Churchgate Station Feeder",
                waypoints=route_churchgate,
                speed_kmh=22.0
            ),
            "BUS_03": FleetVehicle(
                vehicle_id="BUS_03",
                name="Western Railway Special Feeder",
                vehicle_type="STANDARD_BUS",
                capacity=70,
                occupied=30,
                route_name="Station Link Express",
                waypoints=route_marine[::-1],
                speed_kmh=26.0
            ),
            "BUS_04": FleetVehicle(
                vehicle_id="BUS_04",
                name="CSMT Intermodal Connector",
                vehicle_type="ARTICULATED_BUS",
                capacity=110,
                occupied=75,
                route_name="CSMT East-West Connector",
                waypoints=route_csmt,
                speed_kmh=20.0
            ),
            "AMBULANCE_01": FleetVehicle(
                vehicle_id="AMBULANCE_01",
                name="108 South Rapid Medical",
                vehicle_type="EMERGENCY_AMBULANCE",
                capacity=2,
                occupied=0,
                route_name="Perimeter Standby",
                waypoints=[{"lat": 18.9380, "lon": 72.8248}, {"lat": 18.9395, "lon": 72.8245}],
                speed_kmh=0.0,
                status="STATIONARY"
            )
        }

    def update_fleet(self, dt: float = 2.0) -> List[Dict[str, Any]]:
        for v in self.vehicles.values():
            v.step(dt)
        return [v.get_state() for v in self.vehicles.values()]

    def get_fleet_telemetry(self) -> Dict[str, Any]:
        states = self.update_fleet(dt=1.5)
        total_capacity = sum(v["capacity"] for v in states if v["status"] != "OFFLINE")
        total_occupied = sum(v["occupied"] for v in states if v["status"] != "OFFLINE")
        available_seats = total_capacity - total_occupied
        offline_count = sum(1 for v in states if v["status"] == "OFFLINE")

        return {
            "source": "GPS_FLEET_SIMULATOR",
            "active_vehicles": len(states) - offline_count,
            "offline_vehicles": offline_count,
            "total_fleet_capacity": total_capacity,
            "total_occupied_seats": total_occupied,
            "total_available_seats": available_seats,
            "capacity_gap_status": "DEFICIT" if available_seats < 80 else "BALANCED",
            "vehicles": states
        }

    def simulate_transport_failure(self, num_offline: int = 3) -> Dict[str, Any]:
        """Simulates breakdown/unavailability of buses (Scenario 4)."""
        affected = ["BUS_01", "BUS_02", "BUS_03"][:num_offline]
        for vid in affected:
            if vid in self.vehicles:
                self.vehicles[vid].status = "OFFLINE"

        telemetry = self.get_fleet_telemetry()
        telemetry["event"] = "TRANSPORT_FAILURE_INJECTED"
        telemetry["affected_vehicles"] = affected
        return telemetry

    def reset_fleet(self):
        for v in self.vehicles.values():
            if v.vehicle_type != "EMERGENCY_AMBULANCE":
                v.status = "EN_ROUTE"
            else:
                v.status = "STATIONARY"


_fleet_sim: Optional[GPSFleetSimulator] = None


def get_gps_fleet_simulator() -> GPSFleetSimulator:
    global _fleet_sim
    if _fleet_sim is None:
        _fleet_sim = GPSFleetSimulator()
    return _fleet_sim

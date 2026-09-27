"""
Tests for EVENTOS Operational Simulation Platform & Sensor Pipelines.
Covers:
- CCTV Computer Vision Pipeline (Detector, Tracker, Line Counter, Zone Mapper)
- Multi-camera aggregation across 4 cameras
- PDR Time-Series Movement Stream
- GPS Fleet Simulator & Transport Failure injection
- Scenario Engine: All 6 Scenarios & Baseline vs What-If Comparison
- Event Timeline & Replay Engine
- API endpoints for all simulation pipelines
"""

import unittest
from fastapi.testclient import TestClient

from app.main import app
from app.cctv.processor.detector import PedestrianDetector
from app.cctv.processor.tracker import CentroidTracker
from app.cctv.processor.line_counter import VirtualLineCounter
from app.cctv.processor.zone_mapper import ZoneMapper
from app.cctv.service.cctv_service import get_cctv_service
from app.services.pdr_stream import get_pdr_stream_engine
from app.services.gps_fleet_simulator import get_gps_fleet_simulator
from app.services.scenario_engine import get_scenario_engine
from app.services.timeline_engine import get_timeline_engine


class TestOperationalSimulationPlatform(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_cctv_tracker_and_line_crossing(self):
        """Verify tracker tracks IDs and virtual line counter records IN, OUT, and NET."""
        tracker = CentroidTracker()
        counter = VirtualLineCounter(line_y=180, initial_in=10, initial_out=5)

        # Frame 1: Object above line
        boxes1 = [(100, 120, 40, 60)] # cy = 150 < 180
        tracked1 = tracker.update(boxes1)
        self.assertEqual(len(tracked1), 1)
        oid = list(tracked1.keys())[0]

        # Frame 2: Object below line within tracker max_distance (dy = 40 < 70)
        prev_objs = dict(tracker.objects)
        boxes2 = [(100, 160, 40, 60)] # cy = 190 > 180
        tracked2 = tracker.update(boxes2)
        counts = counter.process_tracks(tracker.objects, prev_objs)

        self.assertEqual(counts["entered"], 11)
        self.assertEqual(counts["exited"], 5)
        self.assertEqual(counts["net"], 6)

    def test_02_cctv_zone_mapper_aggregation(self):
        """Verify 4 camera observations aggregate into zone states and venue estimate."""
        mapper = ZoneMapper()
        mapper.record_camera_observation("CAM-01", 45, 40, 15, 25, 14.8, 0.92)
        mapper.record_camera_observation("CAM-02", 30, 28, 18, 10, 15.0, 0.90)
        mapper.record_camera_observation("CAM-03", 50, 45, 20, 25, 14.5, 0.91)
        mapper.record_camera_observation("CAM-04", 25, 22, 12, 10, 15.1, 0.93)

        venue = mapper.aggregate_venue_estimate(base_venue_attendance=20000)
        self.assertEqual(venue["active_cameras"], 4)
        self.assertEqual(venue["total_observed_visible"], 150)
        self.assertEqual(venue["venue_net_inflow_rate"], 70)
        self.assertEqual(venue["calibrated_venue_attendance"], 20070)
        self.assertIn("zone_breakdowns", venue)

    def test_03_pdr_movement_stream(self):
        """Verify PDR replay stream delivers progressive time-series movement records."""
        pdr = get_pdr_stream_engine()
        stream = pdr.get_all_zones_stream(minute_override=3) # Peak surge
        self.assertIn("ZONE-56894058", stream)
        zone_a = stream["ZONE-56894058"]
        self.assertEqual(zone_a["minute_offset"], 3)
        self.assertEqual(zone_a["device_count"], 390)
        self.assertEqual(zone_a["direction"], "S")
        self.assertEqual(zone_a["source"], "PDR_REPLAY_STREAM")

    def test_04_gps_fleet_simulator(self):
        """Verify GPS fleet simulator advances positions and handles simulated breakdown."""
        sim = get_gps_fleet_simulator()
        sim.reset_fleet()

        initial_telemetry = sim.get_fleet_telemetry()
        self.assertEqual(initial_telemetry["offline_vehicles"], 0)
        self.assertGreater(initial_telemetry["total_available_seats"], 100)

        # Inject transport failure (3 buses offline)
        fail_telemetry = sim.simulate_transport_failure(num_offline=3)
        self.assertEqual(fail_telemetry["offline_vehicles"], 3)
        self.assertEqual(fail_telemetry["capacity_gap_status"], "DEFICIT")

        sim.reset_fleet()
        reset_telemetry = sim.get_fleet_telemetry()
        self.assertEqual(reset_telemetry["offline_vehicles"], 0)

    def test_05_scenario_engine_all_six_scenarios(self):
        """Verify Scenario Engine executes all 6 deterministic scenarios and outputs comparison matrix."""
        engine = get_scenario_engine()
        scenarios = ["CROWD_SURGE", "HEAVY_RAIN", "GATE_CLOSURE", "TRANSPORT_FAILURE", "HOSPITALITY_SHOCK", "COMBINED_EXTREME_EVENT"]

        for sc in scenarios:
            res = engine.execute_scenario(sc)
            self.assertEqual(res["scenario_key"], sc)
            self.assertIn("comparison_table", res)
            self.assertGreaterEqual(len(res["comparison_table"]), 4)
            self.assertIn("cascading_impacts", res)

        # Verify Combined Extreme Event (Pitch Demo)
        combined = engine.execute_scenario("COMBINED_EXTREME_EVENT")
        self.assertEqual(combined["severity"], "CRITICAL")
        self.assertEqual(combined["metrics"]["risk"], "CRITICAL")
        self.assertEqual(combined["metrics"]["time_to_breach"], "5.4 min")

    def test_06_timeline_engine(self):
        """Verify EventTimelineEngine outputs cause-and-effect chronology log."""
        timeline = get_timeline_engine()
        events = timeline.get_timeline()
        self.assertGreaterEqual(len(events), 8)

        # Verify chronology contains key actors
        sources = [ev["system_source"] for ev in events]
        self.assertIn("CCTV", sources)
        self.assertIn("PDR", sources)
        self.assertIn("DIGITAL_TWIN", sources)
        self.assertIn("NUGEN", sources)
        self.assertIn("OPERATOR", sources)
        self.assertIn("TELEGRAM", sources)

    def test_07_api_cv_and_venue_aggregation_endpoints(self):
        """Verify API endpoints for CCTV cameras, telemetry, and spatial venue aggregation."""
        cams_res = self.client.get("/api/v1/cv/cameras")
        self.assertEqual(cams_res.status_code, 200)
        self.assertGreaterEqual(len(cams_res.json()["cameras"]), 3)

        tele_res = self.client.get("/api/v1/cv/telemetry/CAM-01")
        self.assertEqual(tele_res.status_code, 200)
        self.assertEqual(tele_res.json()["camera_id"], "CAM-01")

        agg_res = self.client.get("/api/v1/cv/venue-aggregation")
        self.assertEqual(agg_res.status_code, 200)
        agg_data = agg_res.json()
        self.assertIn("calibrated_venue_attendance", agg_data)
        self.assertIn("zones", agg_data)

    def test_08_api_pdr_and_gps_endpoints(self):
        """Verify API endpoints for PDR movement streams and GPS fleet telemetry."""
        pdr_res = self.client.get("/api/v1/pdr/stream")
        self.assertEqual(pdr_res.status_code, 200)

        gps_res = self.client.get("/api/v1/gps/fleet")
        self.assertEqual(gps_res.status_code, 200)
        self.assertIn("vehicles", gps_res.json())

        # Test failure injection endpoint
        fail_res = self.client.post("/api/v1/gps/fleet/simulate-failure")
        self.assertEqual(fail_res.status_code, 200)
        self.assertEqual(fail_res.json()["offline_vehicles"], 3)

        # Reset fleet
        reset_res = self.client.post("/api/v1/gps/fleet/reset")
        self.assertEqual(reset_res.status_code, 200)

    def test_09_api_scenario_and_timeline_endpoints(self):
        """Verify API endpoints for scenarios listing, execution, and timeline replay."""
        list_res = self.client.get("/api/v1/scenarios/list")
        self.assertEqual(list_res.status_code, 200)
        self.assertEqual(len(list_res.json()["scenarios"]), 6)

        exec_res = self.client.post("/api/v1/scenarios/execute", json={"scenario_key": "COMBINED_EXTREME_EVENT"})
        self.assertEqual(exec_res.status_code, 200)
        data = exec_res.json()
        self.assertEqual(data["scenario_key"], "COMBINED_EXTREME_EVENT")
        self.assertIn("comparison_table", data)

        tl_res = self.client.get("/api/v1/timeline/events")
        self.assertEqual(tl_res.status_code, 200)
        self.assertGreaterEqual(len(tl_res.json()["timeline"]), 8)


if __name__ == "__main__":
    unittest.main()

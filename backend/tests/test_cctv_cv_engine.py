"""
Tests for CCTV Computer Vision Video Inference, Tracking, and Telemetry in EVENTOS.
Verifies:
- CCTVEngine camera registry and metadata
- ObjectTracker centroid tracking and virtual line crossing
- CameraFeed detection and frame annotation
- CV Telemetry with PDR corroboration and macro aggregation
- FastAPI endpoints: /cv/cameras, /cv/telemetry/{camera_id}, /cv/stream/{camera_id}
"""

import unittest
import numpy as np
from fastapi.testclient import TestClient
from app.main import app
from app.services.cctv_engine import ObjectTracker, CameraFeed, CCTVEngine, get_cctv_engine


class TestCCTVComputerVision(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.engine = get_cctv_engine()

    def test_cctv_engine_camera_registration(self):
        """Verify all 3 cameras are registered with correct metadata."""
        cameras = self.engine.cameras
        self.assertIn("CAM-01", cameras)
        self.assertIn("CAM-02", cameras)
        self.assertIn("CAM-03", cameras)

        cam1 = cameras["CAM-01"]
        self.assertEqual(cam1.camera_id, "CAM-01")
        self.assertIn("Entrance", cam1.name)
        self.assertEqual(cam1.target_fps, 15)

    def test_object_tracker_centroid_tracking(self):
        """Verify centroid distance matching assigns persistent IDs."""
        tracker = ObjectTracker(line_y=180)
        
        # Frame 1: 2 pedestrians detected
        rects_f1 = [(100, 100, 30, 60), (300, 100, 30, 60)]
        tracked_f1 = tracker.update(rects_f1)
        self.assertEqual(len(tracked_f1), 2)
        initial_ids = set(tracked_f1.keys())

        # Frame 2: Pedestrians move down 15 pixels
        rects_f2 = [(102, 115, 30, 60), (298, 115, 30, 60)]
        tracked_f2 = tracker.update(rects_f2)
        self.assertEqual(len(tracked_f2), 2)
        updated_ids = set(tracked_f2.keys())

        # Persistent IDs should be maintained
        self.assertEqual(initial_ids, updated_ids)

    def test_virtual_line_crossing_inflow(self):
        """Verify crossing from above line_y to below increments in_count."""
        tracker = ObjectTracker(line_y=180)
        initial_in = tracker.in_count

        # Start pedestrian above line (y=100, cy=130)
        tracker.update([(100, 100, 40, 60)])
        
        # Cross below line (y=160, cy=190) -> crosses line_y=180
        tracker.update([(100, 160, 40, 60)])

        self.assertEqual(tracker.in_count, initial_in + 1)

    def test_virtual_line_crossing_outflow(self):
        """Verify crossing from below line_y to above increments out_count."""
        tracker = ObjectTracker(line_y=180)
        initial_out = tracker.out_count

        # Start pedestrian below line (y=200, cy=230)
        tracker.update([(100, 200, 40, 60)])
        
        # Cross above line (y=140, cy=170) -> crosses line_y=180
        tracker.update([(100, 140, 40, 60)])

        self.assertEqual(tracker.out_count, initial_out + 1)

    def test_telemetry_payload_structure(self):
        """Verify telemetry provides required metrics, PDR corroboration, and macro aggregation."""
        telem = self.engine.get_telemetry("CAM-01")
        self.assertEqual(telem["status"], "ok")
        self.assertEqual(telem["source_provenance"], "SIMULATED CCTV REPLAY")
        self.assertEqual(telem["inference_status"], "COMPUTER VISION ACTIVE")
        self.assertIn("metrics", telem)
        self.assertIn("currently_visible", telem["metrics"])
        self.assertIn("net_flow", telem["metrics"])
        self.assertIn("pdr_corroboration", telem)
        self.assertIn("fused_flow_rate", telem["pdr_corroboration"])
        self.assertIn("macro_aggregation", telem)
        self.assertGreater(telem["macro_aggregation"]["zone_crowd_estimate"], 1000)

    def test_api_cv_cameras(self):
        """Test GET /api/v1/cv/cameras endpoint."""
        res = self.client.get("/api/v1/cv/cameras")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("cameras", data)
        self.assertEqual(len(data["cameras"]), 4)

    def test_api_cv_telemetry(self):
        """Test GET /api/v1/cv/telemetry/{camera_id} endpoint."""
        res = self.client.get("/api/v1/cv/telemetry/CAM-01")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["camera_id"], "CAM-01")
        self.assertEqual(data["source_provenance"], "SIMULATED CCTV REPLAY")

    def test_api_cv_stream_head(self):
        """Test CCTV stream generator produces valid multipart JPEG frames."""
        gen = self.engine.generate_annotated_stream("CAM-01")
        first_frame = next(gen)
        self.assertIn(b"--frame", first_frame)
        self.assertIn(b"Content-Type: image/jpeg", first_frame)
        self.assertGreater(len(first_frame), 1000)


if __name__ == "__main__":
    unittest.main()

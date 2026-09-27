"""
Phase 21: Integration Adapters Test Suite
Validates:
1. Meta WhatsApp Cloud API Webhook Handshake (GET verification)
2. WhatsApp Integration Status reporting
3. OpenCV Computer Vision Frame & Stream Ingestion Pipeline
4. PDR (Pedestrian Dead-Reckoning) Aggregate Movement Signal Adapter
5. GPS Fleet Tracking Adapter for Dynamic Transport Supply
"""

import sys
import os
import unittest
from datetime import datetime
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.core.database import init_db, get_db
from app.models.database import (
    EventDB, ZoneDB, ProviderDB, ProviderTypeEnum, ProviderStatusEnum,
    ZoneTypeEnum, RiskLevelEnum, ZoneCrowdStateDB
)
from app.core.config import settings
from app.services.gps_fleet_adapter import GPSFleetAdapter


class TestIntegrationAdapters(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = TestClient(app)

    def setUp(self):
        GPSFleetAdapter.reset_registry()
        self.db = next(get_db())
        
        self.event = EventDB(
            name="Integration Verification Event",
            start_date=datetime(2026, 8, 1),
            end_date=datetime(2026, 8, 5),
            expected_visitors=30000
        )
        self.db.add(self.event)
        self.db.commit()
        self.db.refresh(self.event)

        self.venue_zone = ZoneDB(
            event_id=self.event.event_id,
            name="Main Arena",
            capacity=15000,
            current_crowd=5000,
            zone_type=ZoneTypeEnum.VENUE,
            risk_level=RiskLevelEnum.NORMAL
        )
        self.transit_zone = ZoneDB(
            event_id=self.event.event_id,
            name="Transit Hub C",
            capacity=8000,
            current_crowd=2000,
            zone_type=ZoneTypeEnum.TRANSPORT,
            risk_level=RiskLevelEnum.NORMAL
        )
        self.db.add_all([self.venue_zone, self.transit_zone])
        self.db.commit()
        self.db.refresh(self.venue_zone)
        self.db.refresh(self.transit_zone)

        # Transport Provider
        self.bus_provider = ProviderDB(
            event_id=self.event.event_id,
            zone_id=self.transit_zone.zone_id,
            type=ProviderTypeEnum.TRANSPORT,
            name="Metro Fleet Service",
            capacity={"total": 500, "available": 200, "occupied": 300},
            status=ProviderStatusEnum.ACTIVE
        )
        self.db.add(self.bus_provider)
        self.db.commit()
        self.db.refresh(self.bus_provider)

    def tearDown(self):
        self.db.close()

    def test_whatsapp_webhook_handshake_success(self):
        """Meta Cloud API sends GET with hub.challenge and valid hub.verify_token."""
        token = settings.whatsapp_verify_token or "eventos_webhook_verify_token"
        response = self.client.get(
            f"/api/v1/whatsapp/webhook?hub.mode=subscribe&hub.challenge=987654321&hub.verify_token={token}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "987654321")

    def test_whatsapp_webhook_handshake_forbidden_on_wrong_token(self):
        """Invalid verify token returns 403 Forbidden."""
        response = self.client.get(
            "/api/v1/whatsapp/webhook?hub.mode=subscribe&hub.challenge=987654321&hub.verify_token=wrong_token"
        )
        self.assertEqual(response.status_code, 403)

    def test_whatsapp_status_endpoint(self):
        """Status endpoint honestly reports local webhook active and Meta not connected."""
        response = self.client.get("/api/v1/whatsapp/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["local_webhook"], "ACTIVE")
        self.assertIn("NOT CONNECTED", data["meta_whatsapp_cloud_api"])

    def test_cv_detect_frame_synthetic(self):
        """CV frame detector processes synthetic crowd frame and ingests into CCTV adapter."""
        payload = {
            "zone_id": self.venue_zone.zone_id,
            "synthetic_count": 22,
            "camera_id": "CAM-ARENA-GATE-1",
            "multiplier": 50
        }
        response = self.client.post("/api/v1/cv/detect-frame", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["source"], "real_cctv_cv")
        self.assertEqual(data["detected_raw_count"], 22)
        self.assertEqual(data["macro_people_count"], 1100)

        # Verify database updated
        self.db.refresh(self.venue_zone)
        self.assertEqual(self.venue_zone.current_crowd, 1100)
        latest_state = self.db.query(ZoneCrowdStateDB).filter(
            ZoneCrowdStateDB.zone_id == self.venue_zone.zone_id
        ).order_by(ZoneCrowdStateDB.id.desc()).first()
        self.assertEqual(latest_state.source, "real_cctv_cv")

    def test_cv_stream_demo(self):
        """Multi-frame CV detection stream processes sequential time-steps."""
        payload = {
            "zone_id": self.venue_zone.zone_id,
            "steps": 3,
            "start_count": 10,
            "count_step": 5
        }
        response = self.client.post("/api/v1/cv/stream-demo", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["stream_frames"]), 3)
        self.assertEqual(data["stream_frames"][0]["detected_raw_count"], 10)
        self.assertEqual(data["stream_frames"][2]["detected_raw_count"], 20)

    def test_pdr_signal_ingestion(self):
        """Aggregate PDR movement vector ingests macro flow without individual tracking."""
        payload = {
            "zone_id": self.venue_zone.zone_id,
            "device_count": 180,
            "heading_degrees": 135.0,
            "speed_mps": 1.4,
            "confidence": 0.95
        }
        response = self.client.post(f"/api/v1/zones/{self.venue_zone.zone_id}/pdr-signal", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "pdr_signal_ingested")
        self.assertEqual(data["source"], "pdr_aggregate")
        self.assertEqual(data["direction"], "SOUTHEAST")
        self.assertGreater(data["inflow_per_minute"], 0)

        # Verify DB
        latest_state = self.db.query(ZoneCrowdStateDB).filter(
            ZoneCrowdStateDB.zone_id == self.venue_zone.zone_id
        ).order_by(ZoneCrowdStateDB.id.desc()).first()
        self.assertEqual(latest_state.source, "pdr_aggregate")

    def test_gps_fleet_signal_and_status(self):
        """GPS fleet tracking updates dynamic transport provider capacity and queryable status."""
        signal = {
            "vehicle_id": "SHUTTLE-METRO-01",
            "zone_id": self.transit_zone.zone_id,
            "provider_id": self.bus_provider.provider_id,
            "vehicle_type": "bus",
            "capacity": 60,
            "occupied_seats": 15,
            "available_seats": 45,
            "status": "arrived",
            "eta_minutes": 0.0
        }
        response = self.client.post("/api/v1/transport/fleet-signal", json=signal)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "fleet_signal_ingested")
        self.assertTrue(data["provider_updated"])

        # Check fleet status endpoint
        status_resp = self.client.get(f"/api/v1/transport/fleet-status?zone_id={self.transit_zone.zone_id}")
        self.assertEqual(status_resp.status_code, 200)
        fleet_data = status_resp.json()
        self.assertEqual(fleet_data["active_vehicles_count"], 1)
        self.assertEqual(fleet_data["total_available_seats"], 45)

        # Check DB provider updated
        self.db.refresh(self.bus_provider)
        self.assertEqual(self.bus_provider.capacity["available"], 45)


if __name__ == "__main__":
    unittest.main()

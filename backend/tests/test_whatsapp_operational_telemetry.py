"""
Unit & Integration Tests for WhatsApp Gateway and Human Operational Telemetry Architecture.
Validates:
1. WhatsAppGateway factory selection and Sandbox fallback
2. Operational capacity poll dispatching
3. Human operational response parsing (+120 seats, +50 seats, NO CAPACITY)
4. DB capacity updates on ProviderDB
5. Digital Twin capacity gap calculation and closure
6. Control Tower API routes (/whatsapp/sandbox/request, /whatsapp/sandbox/respond, /whatsapp/operations)
"""

import unittest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.models.database import (
    Base, EventDB, ZoneDB, ProviderDB, ProviderTypeEnum,
    WhatsAppMessageAuditDB, ProviderCapacityUpdateDB
)
from app.services.whatsapp_gateway import (
    get_whatsapp_gateway, SandboxAdapter, MetaCloudAdapter,
    OperationalCapacityRequest, ProviderOperationalResponse
)
from app.services.digital_twin import DigitalTwinEngine
from app.main import app
from app.core.database import get_db


class TestWhatsAppOperationalTelemetry(unittest.TestCase):

    def setUp(self):
        # In-memory SQLite with static pool for clean test isolation
        self.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.db = self.SessionLocal()

        # Seed minimal event, zone, and providers
        self.event = EventDB(
            event_id="EVT-MUMBAI-01",
            name="IND vs AUS Wankhede",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow(),
            expected_visitors=33500,
            status="active"
        )
        self.db.add(self.event)

        self.zone = ZoneDB(
            zone_id="ZONE-CONCOURSE-A",
            event_id="EVT-MUMBAI-01",
            name="Concourse Gate 3",
            zone_type="transport",
            capacity=3000,
            current_crowd=1200,
            inflow_per_minute=40.0,
            outflow_per_minute=20.0
        )
        self.db.add(self.zone)

        # Transport provider: 450 available seats
        self.transport_prov = ProviderDB(
            provider_id="PROV-BEST-TRANSIT",
            event_id="EVT-MUMBAI-01",
            zone_id="ZONE-CONCOURSE-A",
            name="BEST Special Fleet Wankhede",
            type=ProviderTypeEnum.TRANSPORT,
            capacity={"total": 1500, "available": 450, "occupied": 1050},
            contact_info={"whatsapp": "+919820011223", "phone": "02222851234"},
            source_type="SIMULATED"
        )
        self.db.add(self.transport_prov)

        # Hotel provider: 80 available rooms
        self.hotel_prov = ProviderDB(
            provider_id="PROV-HOTEL-TAJ",
            event_id="EVT-MUMBAI-01",
            zone_id="ZONE-CONCOURSE-A",
            name="Taj Mahal Palace Standby",
            type=ProviderTypeEnum.HOTEL,
            capacity={"total": 300, "available": 80, "occupied": 220},
            contact_info={"whatsapp": "+919820099887"},
            source_type="SIMULATED"
        )
        self.db.add(self.hotel_prov)
        self.db.commit()

        # Setup TestClient with DB dependency override
        def override_get_db():
            try:
                yield self.db
            finally:
                pass

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_gateway_factory_defaults_to_sandbox(self):
        gateway = get_whatsapp_gateway(self.db)
        self.assertTrue(gateway.is_sandbox)
        self.assertEqual(gateway.gateway_name, "WHATSAPP_OPERATIONS_SANDBOX")
        status = gateway.get_gateway_status()
        self.assertEqual(status["mode"], "SANDBOX_ACTIVE")
        self.assertIn("SANDBOX ACTIVE", status["display_badge"])

    def test_dispatch_operational_poll(self):
        gateway = SandboxAdapter(self.db)
        import asyncio
        req = asyncio.run(gateway.dispatch_capacity_poll(
            provider_id="PROV-BEST-TRANSIT",
            event_id="EVT-MUMBAI-01",
            required_capacity=170,
            weather_trigger="Heavy Rain (40 mm/h) — Transport Surge"
        ))
        self.assertIsInstance(req, OperationalCapacityRequest)
        self.assertEqual(req.required_capacity, 170)
        self.assertEqual(req.status, "DISPATCHED")
        self.assertIn("+170 seats", req.suggested_replies)

        # Verify audit log in DB
        audit = self.db.query(WhatsAppMessageAuditDB).filter(
            WhatsAppMessageAuditDB.message_id == req.request_id
        ).first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.direction, "OUTBOUND")
        self.assertEqual(audit.source, "WHATSAPP_SANDBOX")

    def test_ingest_provider_response_delta_seats(self):
        gateway = SandboxAdapter(self.db)
        import asyncio
        # Provider responds with +120 seats
        resp = asyncio.run(gateway.ingest_provider_telemetry(
            provider_id="PROV-BEST-TRANSIT",
            response_text="+120 seats",
            event_id="EVT-MUMBAI-01"
        ))
        self.assertIsInstance(resp, ProviderOperationalResponse)
        self.assertEqual(resp.delta_capacity, 120)
        self.assertEqual(resp.status, "CONFIRMED")
        self.assertEqual(resp.new_available_capacity, 570)  # 450 + 120 = 570

        # Check DB updated
        prov = self.db.query(ProviderDB).filter(ProviderDB.provider_id == "PROV-BEST-TRANSIT").first()
        self.assertEqual(prov.available_capacity, 570)

        # Check audit log recorded
        audit = self.db.query(WhatsAppMessageAuditDB).filter(
            WhatsAppMessageAuditDB.message_id == resp.message_id
        ).first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.direction, "INBOUND")
        self.assertEqual(audit.parsed_value, 120)

    def test_ingest_provider_response_no_capacity(self):
        gateway = SandboxAdapter(self.db)
        import asyncio
        resp = asyncio.run(gateway.ingest_provider_telemetry(
            provider_id="PROV-BEST-TRANSIT",
            response_text="NO CAPACITY at this time",
            event_id="EVT-MUMBAI-01"
        ))
        self.assertEqual(resp.delta_capacity, 0)
        self.assertEqual(resp.status, "NO_CAPACITY")

        # Capacity should remain unchanged at 450
        prov = self.db.query(ProviderDB).filter(ProviderDB.provider_id == "PROV-BEST-TRANSIT").first()
        self.assertEqual(prov.available_capacity, 450)

    def test_digital_twin_capacity_gap_and_closure(self):
        dt_engine = DigitalTwinEngine(self.db)

        # 1. Before provider augmentation: Heavy rain causes surge
        twin_before = dt_engine.simulate_scenario("EVT-MUMBAI-01", scenario_name="heavy_rain")
        self.assertGreater(twin_before.transport_demand_required, 0)
        self.assertGreaterEqual(twin_before.transport_capacity_gap, 0)
        self.assertIsInstance(twin_before.cascade_chain, list)
        self.assertGreaterEqual(len(twin_before.cascade_chain), 6)

        initial_gap = twin_before.transport_capacity_gap

        # 2. Ingest +170 seats via Sandbox
        gateway = SandboxAdapter(self.db)
        import asyncio
        asyncio.run(gateway.ingest_provider_telemetry(
            provider_id="PROV-BEST-TRANSIT",
            response_text="+200 seats",
            event_id="EVT-MUMBAI-01"
        ))

        # 3. Recalculate twin
        twin_after = dt_engine.simulate_scenario("EVT-MUMBAI-01", scenario_name="heavy_rain")
        # Capacity gap should now be reduced or closed completely
        self.assertLess(twin_after.transport_capacity_gap, initial_gap + 1)
        self.assertEqual(twin_after.transport_capacity_gap, 0)
        self.assertEqual(twin_after.capacity_gap_status, "BALANCED")

    def test_api_sandbox_request_and_respond_endpoints(self):
        # 1. Dispatch operational request
        req_res = self.client.post("/api/v1/whatsapp/sandbox/request", json={
            "provider_id": "PROV-BEST-TRANSIT",
            "event_id": "EVT-MUMBAI-01",
            "required_capacity": 170,
            "weather_trigger": "Heavy Rain 40mm/h Surge"
        })
        self.assertEqual(req_res.status_code, 200)
        data = req_res.json()
        self.assertEqual(data["status"], "dispatched")
        self.assertIn("request", data)
        self.assertEqual(data["request"]["required_capacity"], 170)

        # 2. Respond to operational request with +120 seats
        resp_res = self.client.post("/api/v1/whatsapp/sandbox/respond", json={
            "provider_id": "PROV-BEST-TRANSIT",
            "response_text": "+120 seats",
            "event_id": "EVT-MUMBAI-01"
        })
        self.assertEqual(resp_res.status_code, 200)
        resp_data = resp_res.json()
        self.assertEqual(resp_data["status"], "processed")
        self.assertEqual(resp_data["response"]["delta_capacity"], 120)
        self.assertEqual(resp_data["response"]["new_available_capacity"], 570)
        self.assertIn("digital_twin", resp_data)

    def test_api_operations_endpoint(self):
        ops_res = self.client.get("/api/v1/whatsapp/operations")
        self.assertEqual(ops_res.status_code, 200)
        ops_data = ops_res.json()
        self.assertEqual(ops_data["status"], "ok")
        self.assertIn("gateway", ops_data)
        self.assertEqual(ops_data["gateway"]["is_sandbox"], True)
        self.assertIn("display_badge", ops_data["gateway"])
        self.assertIn("providers", ops_data)
        self.assertGreaterEqual(len(ops_data["providers"]), 2)


if __name__ == "__main__":
    unittest.main()

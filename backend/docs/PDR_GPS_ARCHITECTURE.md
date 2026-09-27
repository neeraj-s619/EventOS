# EVENTOS Architecture: Pedestrian Dead Reckoning (PDR) & GPS Policy

## Overview & Design Principles

EVENTOS is built on an **app-independent, privacy-preserving, macro-level crowd orchestration architecture**.

### Core Architecture Principles:
1. **Zero App Mandate**: EVENTOS does not require event attendees, spectators, or visitors to install any mobile application.
2. **Privacy by Design**: No individual tracking, visitor device tracking, or personal GPS tracing is performed in the core operational pipeline.
3. **Aggregate Spatial Ingestion**: Decisions are driven by aggregate sensor streams:
   - Computer Vision (CV) cameras & CCTV density/flow analytics
   - Turnstile and optical gate ingress/egress counts
   - Venue access and section scanners
   - Transport hub dispatch and passenger counters
   - Direct provider capacity feeds via WhatsApp and standard APIs

---

## Position on PDR (Pedestrian Dead Reckoning)

```
+-------------------------------------------------------------+
| PDR = OPTIONAL FUTURE INPUT                                 |
| NOT REQUIRED FOR CORE EVENTOS OPERATION                     |
+-------------------------------------------------------------+
```

### Why PDR Is NOT in the Core MVP:
- **Dependency Inversion**: Requiring PDR forces dependency on a proprietary B2C mobile application running on attendee smartphones, conflicting with EVENTOS's core value proposition of immediate deployment at any large-scale event.
- **Battery & Sensor Overhead**: Continuous IMU (accelerometer/gyroscope) integration drains visitor battery and requires complex device-level drift compensation.
- **Operational Redundancy**: Macro crowd risk (utilization, flow rates, bottlenecks, surges) is more reliably and comprehensively measured at boundary zones, gates, and corridors using fixed visual and barrier sensors.

### Optional Future Integration Channels for PDR:
If an event organizer already deploys an official event app or authorized wearable device, PDR telemetry may be ingested in the future via:
1. **Authorized Host Event App SDK**: Aggregated, anonymized position histograms sent at fixed intervals.
2. **Wearable / Staff Badge System**: Operational staff, security, and steward tracking for responder dispatch.
3. **Anonymized Mesh Anchors**: Aggregate Bluetooth Low Energy (BLE) / Ultra-Wideband (UWB) beacon densities.

**Under no circumstances will EVENTOS synthesize fake PDR telemetry or mandate individual device tracking for core pipeline operations.**

---

## Position on Visitor GPS Tracking

```
+-------------------------------------------------------------+
| INDIVIDUAL VISITOR GPS = NOT IMPLEMENTED / NOT REQUIRED      |
| MACRO ZONE TELEMETRY = PRIMARY DATA SOURCE                  |
+-------------------------------------------------------------+
```

### Rationale:
- **Urban Canyon / Indoor Failure**: GPS suffers from multipath error and complete signal loss inside stadiums, enclosed arenas, transit hubs, and covered walkways.
- **Privacy & Regulatory Compliance**: Continuous individual GPS collection triggers GDPR, DPDP (Digital Personal Data Protection Act, India), and international privacy liabilities without providing finer resolution than corridor cameras.
- **Scalability**: Ingesting raw GPS points from 150,000 visitors every 5 seconds creates unnecessary bandwidth and storage overhead without improving macro-zone risk assessment.

---

## Summary Matrix

| Data Source | Status | Purpose | Dependency |
|-------------|--------|---------|------------|
| **CCTV / CV Optical Flow** | **Primary Core** | People counts, flow rates, directional vectors | Fixed cameras / feeds |
| **Turnstiles / Gate Counters**| **Primary Core** | Ingress and egress ground truth | Venue access systems |
| **Provider Capacity Feeds** | **Primary Core** | Hotel, transport, venue availability updates | WhatsApp / REST API |
| **Staff Radios / Dispatch** | **Primary Core** | Human confirmation and approval workflow | Organizer dashboard |
| **PDR (Pedestrian Dead Reckoning)** | **OPTIONAL FUTURE INPUT** | Micro-wayfinding within official app | Optional host app SDK |
| **Individual GPS Tracking** | **NOT REQUIRED / EXCLUDED** | N/A (Privacy & architectural policy) | None |

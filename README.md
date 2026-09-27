# EventOS

> **Privacy-Preserving, Real-Time Crowd Orchestration & Venue Intelligence Operating System**

EventOS is an app-independent, real-time macro-level crowd orchestration and operational intelligence platform designed for large-scale stadiums, arenas, and metropolitan event venues.

---

## 🌟 Key Features

- **Privacy-Preserving & App-Independent**: Zero application mandate for attendees. Decisions are driven by aggregate sensor streams, CCTV/CV density estimation, optical turnstiles, and transport counters.
- **Real-Time Digital Twin & Multi-Zone Topology**: Continuous modeling of crowd density, inflow/outflow velocity, and bottleneck hazards across venue zones.
- **Predictive Risk & Early Warning Engine**: Forecasting surges, congestion buildup, and weather impact scenarios before critical thresholds are breached.
- **Multi-Channel Operational Gateway**:
  - **WhatsApp Cloud Integration**: Automated alerts and bidirectional operational telemetry for event staff and service providers.
  - **Telegram Command & Pulse Bots**: Interactive command center for staff dispatch and attendee advisory services.
  - **NuGen AI Orchestrator**: Automated decision support, risk analysis, and actionable response playbooks.
- **Interactive Operations Command Dashboard**: Real-time CCTV feeds, zone status visualization, dispatch triggers, and decision logs.

---

## 🏗️ Project Architecture

```
eventos/
├── backend/
│   ├── app/
│   │   ├── api/            # FastAPI routes & intelligence endpoints
│   │   ├── core/           # Configuration, security & database setup
│   │   ├── models/         # SQLAlchemy ORM models & database schemas
│   │   ├── schemas/        # Pydantic data contracts
│   │   ├── services/       # Core engines (CV, Digital Twin, Weather, Risk, NuGen AI)
│   │   ├── integrations/   # Messaging & bot integrations (Telegram, WhatsApp)
│   │   └── static/         # Frontend dashboard & CCTV assets
│   ├── docs/               # Architecture documents and specifications
│   ├── tests/              # Master integration scenarios & stress tests
│   └── requirements.txt    # Python dependencies
├── frontend/
│   └── index.html          # Lightweight frontend entrypoint
└── .env.example            # Environment configuration template
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- SQLite or PostgreSQL

### Setup & Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/neeraj-s619/EventOS.git
   cd EventOS
   ```

2. **Backend Setup:**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials (API keys, Telegram bot tokens, etc.)
   ```

4. **Run the Application:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Access the Operations Center:**
   Open [http://localhost:8000](http://localhost:8000) in your browser.

---

## 🌐 Frontend Netlify Deployment

A standalone deployment package for [Netlify](https://www.netlify.com/) is pre-built and packaged:

- **Instant Drop Deploy**: Drag & drop [eventos-netlify-deploy.zip](file:///c:/Users/neera/OneDrive/Documents/Default%20Project/eventos/eventos-netlify-deploy.zip) directly into [app.netlify.com/drop](https://app.netlify.com/drop).
- **Backend Connection**: Configure your FastAPI backend host via the dashboard's top-bar `API` button or customize `_redirects` / `netlify.toml` in `frontend/`.
- See [frontend/README.md](file:///c:/Users/neera/OneDrive/Documents/Default%20Project/eventos/frontend/README.md) for full instructions.

---

## 🧪 Testing & Verification

Run the comprehensive integration scenario test suite:
```bash
python -m tests.master_integration_scenario
```

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

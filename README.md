# Incident Response Agent
> **AI-Powered DevOps Incident Command Center powered by Hindsight Long-Term Memory**

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React%20%2B%20Vite-61DAFB?logo=react)](https://vitejs.dev)
[![Hindsight](https://img.shields.io/badge/Memory-Hindsight-8A2BE2)](https://hindsight.vectorize.io)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## 📌 Project Overview

**Incident Response Agent** is an autonomous and human-in-the-loop DevOps & SRE incident response command center. It remembers past incidents, their root causes, diagnostic evidence, executed remediation actions, and which runbooks succeeded. 

When a critical outage or anomaly occurs, the agent queries **Hindsight Long-Term Memory** to recall historical parallels. By synthesizing past incident postmortems with real-time telemetry (metrics, logs, traces, canary deployments), it provides faster, higher-confidence recommendations while keeping human SREs in control.

> **The Central Hackathon Idea:**  
> *"Incident A teaches the system. Incident B benefits from that memory."*

---

## 💡 Hackathon Problem & Business Case

### Problem
In high-velocity engineering organizations:
1. **Context Loss:** Every time an incident occurs, on-call engineers spend precious minutes rediscovering symptoms and troubleshooting from scratch.
2. **Knowledge Trapped in Silos:** Postmortems are written in wikis or Google Docs and forgotten.
3. **Repeated Mistakes:** Recurring regression bugs, memory leaks, and connection pool timeouts cause repeated downtime.

### Solution
An incident response agent with **bi-directional long-term memory**:
- **Recall Before Acting:** Retrieves prior postmortems and runbooks matching current symptoms.
- **Investigate & Reason:** Formulates probabilistic hypotheses with confidence scores and evidence chains.
- **Human-in-the-Loop:** Submits action recommendations for operator approval before execution.
- **Continuous Learning Loop:** Retains every postmortem directly into Hindsight to prevent recurring failures.

---

## 🏛️ System Architecture

```
                                  🚨 INCIDENT
                                       │
                                       ▼
                              TELEMETRY NORMALIZATION
                                       │
                                       ▼
                       🧠 HINDSIGHT RECALL (arecall)
                                       │
                         ┌─────────────┴─────────────┐
                         ▼                           ▼
                  Similar Incidents          Past Resolutions & Runbooks
                         │                           │
                         └─────────────┬─────────────┘
                                       ▼
                                AI INVESTIGATION
                                       │
                         ┌─────────────┴─────────────┐
                         ▼                           ▼
                  Hypothesis Engine           Evidence Correlator
                         │                           │
                         └─────────────┬─────────────┘
                                       ▼
                               RUNBOOK MATCHING
                                       │
                                       ▼
                            RECOMMENDATION ENGINE
                                       │
                                       ▼
                                HUMAN APPROVAL
                               (Approve / Reject)
                                       │
                                       ▼
                             INCIDENT RESOLUTION
                                       │
                                       ▼
                         AUTOMATED POSTMORTEM GENERATION
                                       │
                                       ▼
                       🧠 HINDSIGHT RETAIN (aretain)
                                       │
                                       ▼
                     FUTURE SIMILAR INCIDENTS RECALL FASTER
```

---

## 🔁 The Core Learning Loop

```
DEMO PART 1                                       DEMO PART 2
(Cold State)                                      (Warmed State)
────────────                                      ──────────────
IR-001 (High CPU & Memory)                        IR-002 (High CPU & Memory)
     │                                                 │
     ▼                                                 ▼
Hindsight: No Memory Yet                         Hindsight: RECALLS IR-001!
     │                                                 │
AI investigates from raw logs                    Instant correlation with
and metric telemetry                             "Deployment-related memory leak"
     │                                                 │
Recommends Rollback & Restart                    Recommends proven Runbook:
     │                                           "API Gateway Memory Leak Recovery"
Operator Approves & Resolves                           │
     │                                           Faster resolution, higher confidence!
Postmortem Generated &
Retained into Hindsight (aretain)
```

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Backend** | Python 3.11+, FastAPI, SQLAlchemy, Pydantic v2, SQLite, Uvicorn |
| **Agent & Memory** | `hindsight-client` (Hindsight Cloud & Local Fallback), Groq / OpenAI LLM APIs |
| **Frontend** | React 18, Vite, JetBrains Mono & Inter typography, Vanilla CSS Design System |
| **Testing** | Pytest, Pytest-Asyncio, HTTPX |
| **DevOps** | Docker, Docker Compose, Nginx |

---

## 📁 Project Structure

```
Incident-Response-Agent/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── hypothesis_engine.py    # Formulates hypotheses from symptoms
│   │   │   ├── incident_agent.py       # Orchestrates recall -> analysis -> recommendation
│   │   │   └── recommendation_engine.py# Generates actionable steps with confidence
│   │   ├── data/
│   │   │   ├── incidents.json          # Pre-configured demo scenarios
│   │   │   └── runbooks.json           # Standard SRE runbooks
│   │   ├── models/                     # Pydantic & SQLAlchemy data schemas
│   │   ├── routers/                    # FastAPI endpoints (incidents, agents, memory, etc.)
│   │   ├── services/
│   │   │   ├── hindsight_service.py    # Official Hindsight SDK integration (aretain, arecall, areflect)
│   │   │   ├── llm_service.py          # Groq / OpenAI LLM integration with fallback
│   │   │   ├── postmortem_service.py   # Postmortem generation & retention
│   │   │   └── runbook_service.py      # Runbook catalog & diagnostic matcher
│   │   ├── config.py                   # Pydantic Settings & environment variables
│   │   ├── database.py                 # SQLite database models & session
│   │   └── main.py                     # FastAPI application entrypoint
│   ├── tests/                          # Comprehensive pytest suite
│   ├── requirements.txt                # Python dependencies
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── IncidentDetail.jsx      # Command center view with hypotheses, memory, & approvals
│   │   │   ├── IncidentList.jsx        # Sidebar incident feed with status badges
│   │   │   ├── LearningLoopModal.jsx   # Interactive modal explaining the Hindsight loop
│   │   │   ├── MemoryLibrary.jsx       # Retained knowledge bank explorer
│   │   │   ├── RunbooksPage.jsx        # SRE Runbook library & diagnostic procedures
│   │   │   └── SimulatorPanel.jsx      # Hackathon demo runner & incident injector
│   │   ├── App.jsx                     # Root UI layout & real-time polling
│   │   ├── hooks.jsx                   # React hooks (useToast, useInterval)
│   │   ├── index.css                   # SRE Dark Command Center design system
│   │   └── utils.js                    # API client & formatting helpers
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   └── vite.config.js
├── scripts/
│   ├── seed_demo.py                    # Seeds demo incidents into database
│   └── verify_learning_loop.py         # End-to-end automated verification script
├── docker-compose.yml
├── master_prompt.txt
└── README.md
```

---

## 🚀 Quickstart & Installation

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- (Optional) Docker & Docker Compose

### 1. Clone & Set Up Backend

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
```

Edit `.env` if you have API keys (both are optional; local fallbacks are fully enabled):
```env
HINDSIGHT_API_KEY=your_hindsight_api_key_here
HINDSIGHT_BANK_ID=incident-response-team
HINDSIGHT_BASE_URL=https://api.hindsight.vectorize.io

LLM_API_KEY=your_groq_or_openai_api_key_here
LLM_PROVIDER=groq
LLM_MODEL=llama-3.3-70b-versatile
```

### 2. Start Backend Server

```bash
uvicorn app.main:app --reload --port 8000
```
Backend API docs will be live at: [http://localhost:8000/docs](http://localhost:8000/docs)

### 3. Set Up & Start Frontend

Open a new terminal:
```bash
cd frontend

# Install npm packages
npm install

# Start development server
npm run dev
```
Frontend will be running at: [http://localhost:5173](http://localhost:5173)

---

## 🎬 Hackathon Demonstration Walkthrough

Follow these steps to demonstrate the Hindsight learning loop:

1. **Open Command Center:** Navigate to `http://localhost:5173`.
2. **Click "1. Trigger Incident A (Cold)":**
   - Injects **IR-001** (`api-gateway` High CPU & Memory degradation).
3. **Investigate Incident A:**
   - Click on **IR-001** in the sidebar.
   - Click **"⚡ Run AI Investigation"**.
   - Note the **Hindsight Memory Panel**: *No prior operational memory found (First occurrence)*.
   - The AI identifies `Memory Leak` from raw telemetry.
4. **Approve & Resolve Incident A:**
   - Review the recommended action: *"Rollback latest deployment v2.14.0"*.
   - Click **"Approve & Execute"**.
   - Status changes to **MITIGATED**.
5. **Generate Postmortem & Retain to Hindsight:**
   - Scroll to the Postmortem section and click **"Generate Postmortem"**.
   - Review root cause and timeline.
   - Click **"🧠 Retain in Hindsight"**.
   - **Knowledge is now permanently memorized!**
6. **Click "2. Trigger Incident B (Warm)":**
   - Injects **IR-002** (A similar memory degradation issue on `api-gateway`).
7. **Investigate Incident B & Witness Recall:**
   - Select **IR-002** and click **"⚡ Run AI Investigation"**.
   - **Hindsight Memory Panel lights up:**
     - 🧠 *Historical Incident Found: IR-001*
     - Previous Root Cause: *Deployment-related memory leak*
     - Previous Resolution: *Rollback deployment + restart service*
     - Recommended Runbook: *API Gateway Memory Leak Recovery*
   - Recommendation confidence is elevated with historical backing!

---

## 🧪 Automated Verification Script

Run the standalone verification script to test the entire learning loop programmatically:

```bash
python scripts/verify_learning_loop.py
```

Expected output:
```
==================================================
HINDSIGHT LEARNING LOOP VERIFICATION
==================================================

Incident A: PASS
Postmortem A: PASS
Hindsight Retain: PASS
Incident B: PASS
Hindsight Recall: PASS
Previous Root Cause: PASS
Previous Resolution: PASS
Previous Runbook: PASS
Historical Recommendation: PASS

OVERALL: PASS
==================================================
```

---

## 🧪 Running Unit & Integration Tests

Run backend pytest suite:
```bash
cd backend
pytest
```
All 16 test cases covering health, incidents, agents, memory, approvals, and postmortems will pass.

---

## 🐳 Docker Deployment

To launch the entire platform with Docker Compose:

```bash
docker-compose up --build
```
- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`

---

## 🛡️ License

MIT License. Built for the Hindsight Hackathon.

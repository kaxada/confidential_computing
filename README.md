# Confidential Computing Distributed RAG System

A privacy-preserving, distributed Retrieval-Augmented Generation (RAG) system designed for sensitive healthcare data. This system enables a central Hub to securely query multiple independent Site Nodes (e.g., hospitals, clinics) without exposing raw patient data, leveraging Differential Privacy (DP), Role-Based Access Control (RBAC), and PHI scrubbing.

## System Overview

### Architecture: Hub-and-Spoke
The system consists of two main components:
1.  **Central Hub (Backend + Frontend):** Orchestrates queries, manages user authentication, and aggregates results from sites. It serves as the single pane of glass for users.
2.  **Site Nodes (Site 1, Site 2, Site 3):** Independent, self-contained RAG systems running at different locations. Each site maintains its own local vector database and processes queries locally, returning only anonymized insights to the Hub.

### Key Features
*   **Privacy-First:** Differential privacy noise is applied to vector retrieval based on user roles.
*   **Data Sovereignty:** Raw data never leaves the site node. Only aggregated, scrubbed answers are transmitted.
*   **Intelligent Routing:** The Hub uses LLM reasoning to route queries to the most relevant site(s) (e.g., "Diabetes" -> Site 1, "Cancer" -> Site 2).
*   **Safety Guardrails:** Built-in checks for emergency medical situations and self-harm detection.
*   **Role-Based Access:** Granular control over data visibility (e.g., Students see high-privacy summaries, PIs see detailed reports).

---

## Quick Start (Local Development)

The easiest way to run the entire system (Hub + 3 Sites) locally is using the dev script.

### Prerequisites
*   **Python 3.9+**
*   **Node.js 18+ & npm**
*   **PostgreSQL 15+** (Running locally on port 5432 with user/pass `postgres`/`postgres`)
*   **OpenAI API Key** (Required for RAG generation)

### 1. Configure Environment
Create a `.env` file in `backend/` and `frontend/`:

**`backend/.env`**:
```bash
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/confidential_rag
JWT_SECRET=dev-secret-change-me
OPENAI_API_KEY=sk-proj-...
```

**`frontend/.env`** (optional, defaults are usually fine):
```bash
VITE_API_BASE=http://localhost:8000
```

### 2. Run All Services
We have a unified script that sets up virtual environments, installs dependencies, builds local vector databases for all sites, and starts all servers.

```bash
./run_dev.sh
```

This will start:
*   **Hub Backend:** http://localhost:8000
*   **Hub Frontend:** http://localhost:5173
*   **Site 1 (Primary Care):** http://localhost:8080
*   **Site 2 (Oncology):** http://localhost:8081
*   **Site 3 (Emergency):** http://localhost:8082

### 3. Access the App
Open **http://localhost:5173** in your browser.
*   **Login:** `admin@example.com` / `admin` (or sign up and approve yourself via DB if needed)

---

## Deployment (AWS)

The project includes production-ready deployment scripts and GitHub Actions workflows for a multi-node AWS architecture.

### Infrastructure Requirement
*   **1 Hub Instance:** Amazon Linux 2023 (t3.medium recommended)
*   **3 Site Instances:** Amazon Linux 2023 (t3.small/medium)

### GitHub Secrets Configuration
Set the following secrets in your GitHub repository to enable automated deployment:

| Secret | Description |
| :--- | :--- |
| `HUB_HOST` | IP address of the Central Hub instance |
| `SITE_1_HOST` | IP address of Site Node 1 |
| `SITE_2_HOST` | IP address of Site Node 2 |
| `SITE_3_HOST` | IP address of Site Node 3 |
| `USER` | SSH Username (e.g., `ec2-user`) |
| `SSH_KEY` | Private SSH Key (PEM format) |
| `POSTGRES_PASSWORD` | DB Password for the Hub |
| `JWT_SECRET` | Secret for auth tokens |
| `OPENAI_API_KEY` | Key for LLM operations on Site Nodes |

### Deployment Workflows
1.  **Deploy Hub (`.github/workflows/deploy-hub.yml`):**
    *   Triggers on changes to `backend/`, `frontend/`, or `infra/`.
    *   Deploys Backend (FastAPI) and Frontend (Vite build served by Nginx) to `HUB_HOST`.
    *   Configures the Hub to communicate with the 3 Site Nodes on port 8000.

2.  **Deploy Sites (`.github/workflows/deploy-site.yml`):**
    *   Triggers on changes to `site-node-*/` or `infra/`.
    *   Runs **3 parallel jobs** to deploy each site code to its respective host (`SITE_X_HOST`).
    *   Sets up the environment, builds the vector DB (if missing), and starts the service on port 8000.

---

## Project Structure

```text
├── backend/                # Central Hub API (FastAPI)
│   ├── app/routes/         # Chat & Auth endpoints
│   ├── app/services/       # Router (LLM-based), Aggregator, Site Manager
│   └── app/core/           # Config & Security
├── frontend/               # User Interface (React + Vite)
│   ├── src/components/     # ChatView, AdminPanel, Sidebar
│   └── src/styles.css      # Custom styling with Markdown support
├── site-node-one/          # Site 1 (Primary Care) Source
├── site-node-two/          # Site 2 (Oncology) Source
├── site-node-three/        # Site 3 (Emergency) Source
├── infra/                  # Infrastructure as Code
│   ├── scripts/            # Deployment scripts (deploy_hub.sh, deploy_site.sh)
│   └── systemd/            # Systemd service templates
├── data/                   # Shared data schemas or seeds (if any)
├── run_dev.sh              # Local development orchestrator
└── README.md               # This documentation
```

---

## Security & Privacy

### Privacy Levels
Each query is processed under a specific privacy level, determining the amount of Differential Privacy (DP) noise injected into the vector retrieval process:
*   **High:** Strict privacy, high noise. (For Students/Interns)
*   **Moderate:** Balanced privacy. (For Auditors/Analysts)
*   **Low:** Minimal noise. (For Clinicians)
*   **None:** Raw data access. (For PIs/Admins only)

### PHI Scrubbing
All responses generated by Site Nodes pass through a **PHI Scrubber** (Regex + NLP) to redact sensitive entities (Names, SSNs, Dates, Locations) before being sent back to the Hub.

### Safety Guards
The system includes active guardrails to detect:
*   **Emergency Phrases:** ("I'm having a heart attack") -> Blocks RAG, advises calling 911.
*   **Self-Harm:** -> Provides crisis resources.

---

## Component Details

### Backend (Hub)
*   **Intelligent Router:** Uses GPT-4 to analyze the user's query and the detailed metadata of each site to decide where to route the request (e.g., *Site 2* for Oncology questions).
*   **Aggregator:** Receives responses from multiple sites and synthesizes them into a single, coherent answer for the user.

### Site Nodes
*   **Vector Database:** Uses **ChromaDB** running locally on the node.
*   **Data Source:** Each site has its own CSV dataset (`site1_medical_data_large.csv`, etc.) representing its local patient records.
*   **API:** A lightweight FastAPI wrapper that accepts queries, performs the RAG workflow, and returns anonymized results.
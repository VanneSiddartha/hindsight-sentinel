# Hindsight Sentinel — Comprehensive Master Technical Report

---

## 1. Executive Summary & Mission Overview

**Hindsight Sentinel** is an open-source agentic workflow and risk intelligence platform built for modern software engineering teams and autonomous DevOps deployment pipelines.

### The Problem
As AI agents gain autonomy in writing code, updating Kubernetes manifests, and deploying services, they frequently repeat past production mistakes. Traditional CI/CD tools catch syntax errors, but they have zero memory of organizational postmortems or past outage root causes. When an agent strips a legacy header or omits a connection timeout retry for the second time, it causes repeated downtime.

### The Solution
Hindsight Sentinel solves this by introducing a **closed-loop organizational experience memory** powered by **Vectorize Hindsight**. Rather than acting as a static storage layer, Hindsight Sentinel retrieves relevant postmortems **BEFORE** AI agents begin planning. The agents analyze past lessons, proactively inject risk mitigation fallbacks into their decisions and code patches, and prevent repeated failures. When a new incident occurs, the system automatically extracts a structured experience memory and retains it in Hindsight for future tasks.

---

## 2. Technology Stack & Frameworks

| Layer | Technologies Used | Description & Purpose |
|---|---|---|
| **Backend Runtime** | Python 3.11 / 3.13, FastAPI | High-performance async REST API framework |
| **Agent Orchestration** | Custom Agentic Pipeline, Pydantic v2 | Type-safe data validation & sequential agent execution |
| **LLM Reasoning** | Groq SDK (`llama-3.3-70b-versatile`) | Fast, structured LLM reasoning for planning & reflection |
| **Vector Memory Engine** | Vectorize Hindsight SDK (`hindsight-client`, `hindsight-api`) | Official Vectorize SDK for vector indexing, semantic recall, and experience retention |
| **Frontend Framework** | React 18, TypeScript, Vite | Modern, responsive dark-mode Single Page Application |
| **Styling & Icons** | Tailwind CSS, Lucide React Icons | Premium design system with color-coded risk states and live feed |
| **Testing & Eval** | Pytest, Custom Evaluation Harness | Automated unit test suite & empirical benchmark reporting (JSON/CSV) |

---

## 3. End-to-End Closed-Loop Architecture

```
                    ┌─────────────────────────┐
                    │       USER TASK         │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │ Hindsight Retrieval     │
                    │ (recall_experiences)   │
                    └────────────┬────────────┘
                                 │
                     Recalled Past Experiences
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │ Risk Engine Evaluation  │
                    │ (NORMAL/CAUTION/HIGH)   │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │  1. PLANNER AGENT       │
                    │  (Memory Influenced)    │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │  2. CODER AGENT         │
                    │  (Injects Fallback)     │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │  3. TESTER AGENT        │
                    │  (Validates Code Patch) │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │  4. SECURITY AGENT      │
                    │  (Security Compliance)  │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │ Post-Run Extraction     │
                    │ (extract_experience)    │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │ Hindsight Retain        │
                    │ (client.retain)         │
                    └─────────────────────────┘
                                 │
                                 ▼
                        Future Task Runs
```

---

## 4. Deep Dive: The 4 Autonomous AI Agents

Each agent in `backend/app/agents/` plays a specialized role in the execution pipeline:

### 1. Planner Agent (`planner.py`)
- **Role:** Analyzes the task description, target service, environment, and **recalled Hindsight memories**.
- **Memory Functionality:** If Hindsight retrieved a past incident (e.g. `[exp-incident-01]`), the Planner explicitly injects a **Memory Influence Statement** into its decision text:
  > `[MEMORY INFLUENCE - Hindsight Precedent exp-incident-01]: Previous incident shows that executing this task without fallback handling resulted in FAILURE. Lesson Learned: 'Always preserve X-Legacy-Auth header fallback'. Planner Decision Modification: Incorporating proactive fallback into roadmap.`
- **Output:** Structured 3-step action roadmap passed to the Coder agent.

### 2. Coder Agent (`coder.py`)
- **Role:** Translates the Planner's roadmap into specific code modifications and configuration diffs.
- **Memory Functionality:** When Hindsight memory is active, the Coder injects proactive risk mitigation code directly into the patch diff (e.g., adding `X-Legacy-Auth` header fallback logic or connection pool retry loops).
- **Output:** Unified unified code patch diff (`diff`) and action summary.

### 3. Tester Agent (`tester.py`)
- **Role:** Validates the code patch against automated integration and regression test suites.
- **Memory Functionality:** 
  - **With Memory:** Because Coder applied the proactive fallback, integration tests **PASS** (`14/14 passed`).
  - **Without Memory (Unlearned Baseline):** Code patch omits legacy header fallback → integration tests **FAIL** (`AuthenticationMismatchError: 401 Unauthorized`).
- **Output:** Detailed test execution logs and pass/fail status (`SUCCESS` / `FAILED`).

### 4. Security Agent (`security.py`)
- **Role:** Conducts static security scanning (SAST) and security posture compliance audit.
- **Memory Functionality:** If risk posture is `HIGH RISK` or upstream tests failed, Security flags a warning or blocks automated deployment pending human approval (`BLOCKED_BY_RISK`).
- **Output:** Deployment readiness clearance (`SUCCESS`, `WARNING`, or `SKIPPED`).

---

## 5. How Experience Memory is Shared, Stored & Retained

### Data Shape (`ExperienceModel`)
Workflow experiences include the following structured fields:
```python
class ExperienceModel(BaseModel):
    experience_id: str          # e.g., "exp-incident-01"
    context: str                # Task description
    service_name: str           # Target microservice (e.g., "payment-auth")
    agents_involved: List[str]  # ["planner", "coder", "tester", "security"]
    decision: str               # Original agent decision
    action: str                 # Applied code patch
    validation: str             # Test output / failure log
    outcome: str                # Observed workflow outcome, including "ANALYZED"
    root_cause: Optional[str]   # Only set when established by observed evidence
    lesson: str                 # Derived from recorded decisions and validation
    future_applicability: str   # Scope of future applicability
    workflow_id: Optional[str]  # Originating workflow, when applicable
    workflow_type: Optional[str]
    task_description: Optional[str]
    version: Optional[str]
    environment: Optional[str]
    agent_activities: List[ExperienceAgentActivity]
    tags: List[str]             # Context tags (e.g., ["legacy auth", "api v2"])
    source: str                 # "workflow" (real workflow) or "demo" (seeded sample)
    metadata_status: str        # "persisted" or "temporary"
    hindsight_status: str       # Remote retain result
```

### Vector Memory Indexing & Hindsight SDK
1. **Retention (`retain.py`):** Stores list/detail metadata in SQLite (`data/experiences.sqlite3`) and calls `client.retain()` on Vectorize Hindsight with the configured bank ID. Local metadata and Hindsight statuses remain distinct.
2. **Pre-Execution Retrieval (`recall.py`):** Before agents run, `client.recall(bank_id=..., query=task)` performs vector semantic search to retrieve the top matching historical postmortems.
3. **Automatic Post-Run Extraction (`extract.py`):** Completed workflows with a reported outcome produce an `ExperienceModel(source="workflow")` associated with the workflow ID. Analysis-only runs are labelled `ANALYZED`; root causes are left empty unless observed evidence establishes them.
4. **Experience History (`GET /experiences`):** Reads persisted SQLite metadata, returning workflow and demo records together. Demo seeding is idempotent and does not replace workflow records.

---

## 6. Explainable Risk Engine Rules (`risk_engine.py`)

Hindsight Sentinel avoids black-box ambiguity by enforcing an explainable rule engine:

- **NORMAL (Green):** 0 matching past failure patterns. Mandatory phrase: `"No known risk detected."`
- **CAUTION (Yellow):** 1 related past experience match.
- **HIGH RISK (Red):** 2+ matching conditions, OR 1 strong match to a past `FAILURE` with matching context tags.

---

## 7. UI & Dashboard Walkthrough (`http://localhost:3000`)

```
┌────────────────────────────────────────────────────────────────────────────────┐
│  [HERO RISK BADGE]  NORMAL (Green)  /  CAUTION (Yellow)  /  HIGH RISK (Red)    │
├────────────────────────────────────────────────────────────────────────────────┤
│  [TASK BAR] [ Enter task description... ]  [▶ Replay Closed-Loop Demo (Run 1->2)] │
├──────────────────────────────────────────────────┬─────────────────────────────┤
│  LEFT PANEL: Live Agent Pipeline                 │  RIGHT PANEL: Hindsight     │
│  - Planner Agent (Roadmap & Memory Callouts)     │  - Recalled Memories & IDs  │
│  - Coder Agent (Code Diffs & Fallbacks)          │  - Relevance Scores (95%)   │
│  - Tester Agent (Test Logs & Pass/Fail)          │  - Retained Lessons         │
│  - Security Agent (Compliance Clearance)         │  - New Extracted Experience │
└──────────────────────────────────────────────────┴─────────────────────────────┘
```

### Key UI Features
1. **Top Hero Risk Badge:** Color-coded status banner (`NORMAL` green, `CAUTION` yellow, `HIGH RISK` red) updating dynamically.
2. **1-Click Closed-Loop Replay Demo Button:** Runs the 2-step demonstration:
   - **Run 1 (Unlearned / Memory OFF):** The controlled legacy-auth scenario fails → a workflow experience is extracted and retained when Hindsight is configured (`source=workflow`).
   - **Run 2 (Memory Active / Memory ON):** Recalls newly retained memory → Planner preserves fallback → Tests PASS!
3. **Left Panel (Live Agent Pipeline):** Displays live step execution with **Hindsight Memory Influenced** badges and code diffs.
4. **Right Panel (Hindsight Evidence & Extracted Experience):** Displays recalled incident cards and the **New Experience Extracted & Retained** card.
5. **Experience Memory Vault (`ExperienceHistory.tsx`):** Searchable, source-filterable archive of persisted workflow and demo experiences with their recorded validation, agent activity, retention status, and applicability details.

---

## 8. Empirical Evaluation Benchmark Results

The evaluation harness ([`run_eval.py`](file:///c:/BOT/backend/tests/evaluation/run_eval.py)) executed 6 synthetic production incident scenarios comparing Baseline (Memory OFF) vs. Sentinel (Memory ON):

| Benchmark Metric | Baseline (Memory OFF) | Sentinel (Hindsight Memory ON) | Improvement |
|---|---|---|---|
| **Correct Retrieval Rate** | N/A | **100.0%** (6/6 scenarios matched) | Perfect Match |
| **Risk Interception Rate** | N/A | **100.0%** (6/6 risks intercepted) | 100% Gated |
| **Repeated Mistake Count** | 6 Failures (100%) | **0 Failures (0%)** | **100% Reduction** |

Results are stored in [`data/eval_results.json`](file:///c:/BOT/data/eval_results.json) and [`data/eval_results.csv`](file:///c:/BOT/data/eval_results.csv).

---

## 9. Test Suite Verification Summary

Backend tests cover the following paths:
- `tests/test_closed_loop.py` — Verifies 2-run memory learning cycle.
- `tests/test_step2_pipeline.py` — Verifies 4-agent sequential pipeline.
- `tests/test_step3_experience.py` — Verifies retain, recall, reflect methods.
- `tests/test_step4_risk_engine.py` — Verifies risk engine rules & exact phrases.
- `tests/test_step6_replay.py` — Verifies baseline vs interception replay logic.
- `tests/test_experience_persistence.py` — Verifies workflow extraction, Hindsight success/failure reporting, API listing, demo coexistence, deduplication, and restart persistence.

---

## 10. Operational Guide & Commands

### Start Backend API Server
```bash
cd c:\BOT\backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Start Frontend UI Application
```bash
cd c:\BOT\frontend
cmd /c npm run dev
```

### Run Closed-Loop Test Suite
```bash
cd c:\BOT\backend
python -m pytest tests/test_closed_loop.py -s
```

### Run Evaluation Benchmark Script
```bash
cd c:\BOT\backend
python tests/evaluation/run_eval.py
```

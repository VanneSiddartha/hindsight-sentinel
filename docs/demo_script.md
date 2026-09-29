# Hindsight Sentinel — Live Demo Presentation Script (60-Second Walkthrough)

## Demo Goal
Demonstrate to judges how **Hindsight Sentinel** intercepts agentic deployment failures before they hit production, transforming past postmortems into real-time risk intelligence.

---

## Step-by-Step Script & Actions

### 1. The Opening Hook (0 - 15 Seconds)
> **Speaker:** "AI agents are deploying code faster than ever — but when an agent repeats a mistake that cost your team an outage last month, that's not automation, that's liability. Meet **Hindsight Sentinel**."

- **Screen Action:** Show top of Dashboard with **NORMAL — No known risk detected** badge in green.

---

### 2. The 1-Click Replay Demo (15 - 45 Seconds)
> **Speaker:** "Let's run a live 30-second replay of a real incident: upgrading API v2 with legacy auth middleware."

- **Screen Action:** Click **"Replay Demo (30s Before/After)"** button.

#### Phase 1: Baseline Attempt (No Hindsight Memory)
> **Speaker:** "First attempt, without Hindsight memory. The system sees no risk. The agent pipeline runs, strips legacy auth headers, and boom — integration tests fail with 401 Unauthorized."

- **Screen Action:** Replay banner shows **Demo Phase 1/2**. Pipeline displays `NORMAL` risk badge and red `FAILED` test log.

#### Phase 2: Interception Attempt (Hindsight Memory Active)
> **Speaker:** "3 seconds later, the exact same task runs with Hindsight memory active. Instantly, Sentinel recalls past incident `[exp-incident-01]`. The top risk badge flips to **HIGH RISK** in red! Hindsight instructs the Planner and Coder to inject legacy auth fallbacks, and Security gates deployment for human approval."

- **Screen Action:** Replay banner transitions to **Demo Phase 2/2**. Badge turns **HIGH RISK** (red), Evidence panel displays matched memory `[exp-incident-01]` (Relevance: 95%), and deployment status updates to `BLOCKED_BY_RISK`.

---

### 3. The Memory Vault & Real Benchmark Impact (45 - 60 Seconds)
> **Speaker:** "Over in the Experience History Vault, every postmortem lesson is stored with root causes, decisions, and future applicability tags. In our evaluation harness across 6 production scenarios, Hindsight Sentinel reduced repeated agent mistakes from 100% down to 0% with a 100% correct retrieval rate."

- **Screen Action:** Click **"Experience History"** tab to highlight the memory vault, then conclude.

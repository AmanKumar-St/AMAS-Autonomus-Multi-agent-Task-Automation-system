# AMAS — Autonomous Multi-Agent Task Automation System

[![PraisonAI](https://img.shields.io/badge/PraisonAI-1.7.11-blue.svg)](https://praison.ai)
[![Provider Agnostic](https://img.shields.io/badge/LLM-Provider--Agnostic-purple.svg)](https://github.com)
[![TypeScript](https://img.shields.io/badge/TypeScript-React%2019-3178C6.svg)](https://www.typescriptlang.org)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-yellow.svg)](https://python.org)
[![Vite](https://img.shields.io/badge/Frontend-Vite%20%7C%20TailwindCSS-646CFF.svg)](https://vitejs.dev)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

**AMAS (Autonomous Multi-Agent Task Automation System)** is an enterprise-grade agentic workflow orchestration platform. It transforms standard prompt-and-response AI into an autonomous execution engine that dynamically plans, executes, audits, and self-heals complex analytical and operational tasks.

Unlike fragile LLM wrappers or monolithic chat interfaces that hallucinate calculations and fabricate data, AMAS implements **dynamic Directed Acyclic Graph (DAG) task synthesis**, **strict 5-tier tool hierarchy precedence**, a **shared typed blackboard memory**, **independent verification gates with mathematical recalculation**, **multi-provider web intelligence**, and **provider-agnostic model routing**.

---

## Table of Contents

1. [Executive Overview & Philosophy](#1-executive-overview--philosophy)
2. [End-to-End System Architecture](#2-end-to-end-system-architecture)
3. [Frontend Design & Workflow Studio](#3-frontend-design--workflow-studio)
4. [Control Plane & DAG Orchestration Engine](#4-control-plane--dag-orchestration-engine)
5. [Runtime Engine & PraisonAI Integration](#5-runtime-engine--praisonai-integration)
6. [The 6 Specialized Agent Roles](#6-the-6-specialized-agent-roles)
7. [Provider-Agnostic LLM Routing & Health Monitoring](#7-provider-agnostic-llm-routing--health-monitoring)
8. [Multi-Tier Tool Ecosystem & Policy](#8-multi-tier-tool-ecosystem--policy)
9. [Internet Search & Real-Time Web Intelligence](#9-internet-search--real-time-web-intelligence)
10. [Independent Verification & Adversarial Audit Gate](#10-independent-verification--adversarial-audit-gate)
11. [Self-Healing & Diagnostic Recovery Agent](#11-self-healing--diagnostic-recovery-agent)
12. [Security Architecture & Restricted Execution](#12-security-architecture--restricted-execution)
13. [Persistence, SQLite Schema & Storage Layer](#13-persistence-sqlite-schema--storage-layer)
14. [Repository Structure](#14-repository-structure)
15. [CLI & REST API Reference](#15-cli--rest-api-reference)
16. [Quick Start & Local Setup](#16-quick-start--local-setup)
17. [Quality Benchmarks & Evaluation Suite](#17-quality-benchmarks--evaluation-suite)

---

## 1. Executive Overview & Philosophy

Modern LLM applications frequently fail in production due to three architectural flaws:
1. **Monolithic Hallucination**: Asking a single conversational model to do research, solve math, format code, and verify its own output leads to fabrication of facts and erroneous calculations.
2. **Brittle Rigid Routing**: Hardcoding rule engines (`if "finance" in prompt: run_finance()`) breaks as soon as a user asks multi-domain questions.
3. **Context Degradation & Isolation**: Multi-agent pipelines often pass unstructured conversational snippets between agents like a game of telephone, losing precision, table data, and citations.

### The AMAS Design Principles

- **Zero Hardcoded Routing**: High-level natural language objectives are compiled dynamically by an autonomous Planning Agent into a valid topological DAG with dependency constraints and least-privilege tool allocations.
- **Strict Separation of Concerns**: Research agents gather facts; Analysis agents calculate statistics using deterministic code tools; Execution agents synthesize deliverables; Verification agents independently audit accuracy.
- **Authentic Grounding (Zero Fabrication Policy)**: All live data comes from verified search engines, market APIs, or local documents. When live data is unavailable, agents honestly state the limitation rather than synthesizing fake figures.
- **Shared Scoped Blackboard Memory**: A typed blackboard state preserves data structures, intermediate calculations, citations, and accumulated research findings across all workflow steps.
- **Independent Adversarial Audits**: Deliverables are never certified on the generating agent's word. An independent Verification Auditor re-runs math formulas, checks evidence coverage, inspects source citations, and computes an objective quality score.
- **Structured Self-Healing**: When a step fails, the system does not enter infinite retry loops. It applies classified recovery strategies (provider switching, tool substitution, argument sanitization, replanning, or human approval).

---

## 2. End-to-End System Architecture

The following diagram illustrates the complete AMAS architectural stack:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 PRESENTATION LAYER                                     │
│  React 19 + TypeScript + Vite + Tailwind CSS | Workflow Studio | Real-time SSE Stream  │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ HTTP / Server-Sent Events (SSE)
┌───────────────────────────────────────────▼────────────────────────────────────────────┐
│                             API GATEWAY & EXPRESS SERVER                               │
│        REST Endpoints (/api/workflow/run, /api/providers, /api/tools, /api/runs)       │
│                  Process Isolation | UTF-8 Streaming | JSON Boundary Parser            │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ CLI Spawning / In-Process Runner
┌───────────────────────────────────────────▼────────────────────────────────────────────┐
│                                  AMAS CONTROL PLANE                                    │
│   ┌────────────────────────┐  ┌────────────────────────┐  ┌────────────────────────┐   │
│   │   RunManager (Orch)    │  │   TaskGraph (DAG DFS)  │  │  PolicyManager (RBAC)  │   │
│   └───────────┬────────────┘  └───────────┬────────────┘  └───────────┬────────────┘   │
│               │                           │                           │                │
│   ┌───────────▼────────────┐  ┌───────────▼────────────┐  ┌───────────▼────────────┐   │
│   │  EventBus (Pub/Sub)    │  │  RecoveryAgent (Heal)  │  │ VerificationAuditor    │   │
│   └────────────────────────┘  └────────────────────────┘  └────────────────────────┘   │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ Task Dispatch & Blackboard Context
┌───────────────────────────────────────────▼────────────────────────────────────────────┐
│                             AMAS RUNTIME & AGENT ENGINE                                │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │  RunMemory (Scoped Blackboard, State Storage, Accumulated Task Results)        │   │
│   └───────────────────────────────────────┬────────────────────────────────────────┘   │
│                                           │                                            │
│   ┌──────────────────────┐  ┌─────────────▼────────┐  ┌────────────────────────────┐   │
│   │ Dynamic DAG Planner  │  │   PraisonRuntime     │  │ Argument Sanitizer & Glue  │   │
│   └──────────────────────┘  └─────────────┬────────┘  └────────────────────────────┘   │
└───────────────────────────────────────────┼────────────────────────────────────────────┘
                                            │
                 ┌──────────────────────────┴──────────────────────────┐
                 ▼                                                     ▼
┌──────────────────────────────────┐        ┌────────────────────────────────────────┐
│     PROVIDER-AGNOSTIC LLM LAYER   │        │       MULTI-TIER TOOL ECOSYSTEM        │
│  ┌────────────────────────────┐  │        │  ┌──────────────────────────────────┐  │
│  │   ProviderManager Router   │  │        │  │ Tier 1: PraisonAI Official Tools │  │
│  │ (Health-Aware / Fallbacks) │  │        │  │ (WebSearch, FileRead, CodeInterp)│  │
│  └─────────────┬──────────────┘  │        │  └────────────────┬─────────────────┘  │
│                │                 │        │                   │                    │
│   ┌────────────┼────────────┐    │        │  ┌────────────────▼─────────────────┐  │
│   ▼            ▼            ▼    │        │  │ Tier 2: LangChain Community      │  │
│  Groq     OpenRouter    Gemini   │        │  │ (Wikipedia Retriever)            │  │
│ (Fast)    (Frontier)    (Context)│        │  └────────────────┬─────────────────┘  │
│   │            │            │    │        │                   │                    │
│   └────────────┬────────────┘    │        │  ┌────────────────▼─────────────────┐  │
│                ▼                 │        │  │ Tier 4: Official SDK Integrations│  │
│     Local OpenAI Compatible      │        │  │ (Tavily, Yahoo Finance, Exa)     │  │
│     (Ollama / vLLM / LM Studio)  │        │  └────────────────┬─────────────────┘  │
└──────────────────────────────────┘        │                   │                    │
                                            │  ┌────────────────▼─────────────────┐  │
                                            │  │ Tier 5: Pure Custom Calculators  │  │
                                            │  │ (Risk Math, Anomaly Z-Score, Art)│  │
                                            │  └──────────────────────────────────┘  │
                                            └───────────────────┬────────────────────┘
                                                                │
                                                                ▼
                                            ┌────────────────────────────────────────┐
                                            │        PERSISTENCE & STORAGE           │
                                            │  SQLite3 (amas.db) | Artifact Files    │
                                            └────────────────────────────────────────┘
```

---

## 3. Frontend Design & Workflow Studio

The frontend is built on **React 19**, **TypeScript**, and **Tailwind CSS**, designed for maximum clarity, real-time observability, and actionable intelligence.

### Interactive Workflow Studio (`WorkflowStudio.tsx`)

- **Interactive Scenario Presets**: One-click execution of real-world scenarios:
  1. *India Floods & Relief*: Real-time casualty tracking, State Disaster Response Fund (SDRF) metrics, infrastructure damage breakdown.
  2. *IPL & Global Sports*: Live sports wire retrieval of match outcomes, team scorelines, and player MVPs.
  3. *Oscars & Box Office*: Global revenues, Academy Awards won, Rotten Tomatoes/Metacritic consensus.
  4. *SpaceX Starship Telemetry*: Flight telemetry, stage separation status, Raptor engine performance.
  5. *Stock Risk & Math*: Live 30-day volatility and Sharpe ratio computation for equities (e.g., AAPL, NVDA).
  6. *Telemetry Anomaly Detection*: Statistical outlier and sensor spike detection.
- **Live DAG Execution Visualizer**: Displays task nodes, dependencies, current execution status (`PENDING`, `RUNNING`, `COMPLETED`, `FAILED`, `VERIFIED`), assigned agent roles, and execution duration in milliseconds.
- **Dedicated Markdown Renderer (`MarkdownRenderer`)**:
  - Full GitHub Flavored Markdown (GFM) parsing.
  - Formatted data tables with dark headers, subtle border dividers, and alternating row backgrounds.
  - Headings (`#`, `##`, `###`) with distinct font hierarchies and indigo accents.
  - Unordered and ordered lists with custom bullet styling.
  - Syntax-highlighted code blocks, blockquotes, and external citation hyperlinks.
- **Domain-Specific Deliverable Displays**:
  - *Disaster Deliverable*: 4 high-impact stat cards (Fatalities, Relief Funds, Infrastructure Damage, Affected Population), state-by-state regional breakdown grid (Assam, Gujarat, Kerala, Bihar), and executive factual synthesis.
  - *Financial Deliverable*: Risk metric cards (Sharpe Ratio, Annualized Volatility, Return), verified math tables, and price series summaries.
  - *Anomaly Deliverable*: Outlier flags, Z-score thresholds ($> 2.2\sigma$), and sensor distribution telemetry.
  - *Aerospace Deliverable*: Flight milestone statuses, window telemetry, and propulsion telemetry.
- **Real-Time SSE Event Stream**: Displays live agent logs, verification audit events, and self-healing transitions as they happen.
- **Provider Settings Modal (`ProviderSettingsModal.tsx`)**: Allows switching active LLM providers on the fly, editing endpoint parameters, and performing real-time latency ping tests.

---

## 4. Control Plane & DAG Orchestration Engine

The AMAS Control Plane orchestrates all multi-agent workflows without static code paths:

### 1. Dynamic DAG Planning (`amas/runtime/planner.py`)
When a user submits an objective, the Planning Agent analyzes the prompt and emits a structured JSON task graph.
- **Topological Dependencies**: Tasks explicitly declare dependencies (e.g., `dependencies: ["task_1"]`).
- **Least-Privilege Tool Assignment**: Each task is assigned an agent role and restricted to only the tools needed for that step.
- **Anti-Placeholder Validation**: System prompts enforce concrete search terms. The planner is forbidden from emitting template placeholders (e.g., `{region}`, `{date}`, `{{deaths}}`) which cause search failure.
- **Cycle Detection**: The `TaskGraph` (`amas/control_plane/task_graph.py`) performs Depth-First Search (DFS) validation prior to execution, rejecting any cyclic or malformed graphs.

### 2. Shared Blackboard Memory (`amas/runtime/memory.py`)
Agents communicate through a typed, thread-safe blackboard:
- **`completed_task_results`**: Automatically records the output of every completed task.
- **`get_accumulated_results_text()`**: Concatenates upstream findings into an organized context block, ensuring downstream analysis and execution agents have full access to earlier research.
- **Key-Value Store**: Allows agents to share numerical series, tickers, timestamps, and calculation parameters.
- **Deliverable Aggregation**: `RunManager._build_latest_computation()` aggregates research findings, computed metrics, state breakdowns, and citations into a unified delivery payload.

---

## 5. Runtime Engine & PraisonAI Integration

The Runtime Engine (`amas/runtime/praison_runtime.py`) connects the control plane to agent execution:

### PraisonAI Glue
- Leverages `praisonaiagents` for agent role configuration, goal framing, and tool attachment.
- When PraisonAI is installed, tasks run through native PraisonAI agent structures.
- If PraisonAI native team execution is unavailable, AMAS seamlessly uses its robust internal execution fallback while preserving full agent roles, tool calling, and logging.

### Intelligent Argument Resolution
The runtime inspects and sanitizes tool arguments before execution:
- **Search Query Normalization**: Cleans user queries, strips template artifacts, and removes restrictive site filters that degrade search recall.
- **Artifact Writer Automation**: When the planner allocates `amas_artifact_writer`, the runtime automatically injects the accumulated research findings from the blackboard into the artifact content.
- **Adaptive Context Windowing**: Truncates search results and tool responses safely (up to 4,000 characters) to deliver deep context to LLMs without overflowing model token limits.

---

## 6. The 6 Specialized Agent Roles

AMAS enforces strict role separation across 6 specialized agents (`amas/runtime/agents.py`):

| Agent Role | System Prompt Directive | Permitted Tools | Core Responsibility |
| :--- | :--- | :--- | :--- |
| **`PlanningAgent`** | "Architect and decompose objectives into minimum sequential tasks." | None (pure reasoning) | Formulates DAG, sets dependencies, enforces least-privilege scoping. |
| **`ResearchAgent`** | "Gather authentic facts from live search, encyclopedias, and market feeds." | `praison_web_search`, `official_tavily_search`, `official_financial_retriever`, `langchain_wikipedia` | Live data retrieval without fabricating facts or simulating metrics. |
| **`AnalysisAgent`** | "Perform deterministic mathematical and statistical operations." | `amas_financial_risk_calculator`, `amas_telemetry_anomaly_detector`, `praison_code_interpreter` | Computes Sharpe ratios, annualized volatility, Z-scores, and variances. |
| **`ExecutionAgent`** | "Synthesize deliverable reports and export structured documents." | `amas_artifact_writer`, `praison_file_read` | Compiles comprehensive markdown deliverables with tables and metrics. |
| **`VerificationAgent`**| "Adversarially audit claims, re-run math, and verify evidence coverage." | Independent calculation methods | Validates bounds, verifies citations, scores deliverable quality. |
| **`RecoveryAgent`** | "Diagnose failures, select healing strategies, and restore execution." | Control plane policy operations | Self-healing via provider switching, tool fallbacks, and replanning. |

---

## 7. Provider-Agnostic LLM Routing & Health Monitoring

AMAS decouples agent intelligence from model vendors (`amas/providers/`):

```
+-------------------------------------------------------------------------+
│                          LLM Provider Manager                           │
│        (Fixed Selection | Fallback Chain | Health-Aware Routing)        │
+-------------------------------------------------------------------------+
       │                   │                   │                   │
       ▼                   ▼                   ▼                   ▼
+--------------+    +--------------+    +--------------+    +--------------+
│     Groq     │    │  OpenRouter  │    │  CodeCraft   │    │    Gemini    │
│ (Ultra-Fast) │    │  (100+ LLMs) │    │  (Coding)    │    │  (1M Context)│
+--------------+    +--------------+    +--------------+    +--------------+
       │                   │                   │                   │
       +-------------------+-------------------+-------------------+
                                   │
                                   ▼
              +-------------------------------------------+
              │       Custom / Local OpenAI-Compatible    │
              │       (Ollama, vLLM, LM Studio)           │
              +-------------------------------------------+
```

### Supported Providers
- **Groq**: Ultra-high throughput inference (`openai/gpt-oss-120b`, `openai/gpt-oss-20b`, `qwen/qwen3.8-27b`).
- **OpenRouter**: Access to frontier models (`meta-llama/llama-3.3-70b-instruct`, `anthropic/claude-3.5-sonnet`, `deepseek/deepseek-chat`).
- **CodeCraft**: High-throughput code generation and structured JSON output endpoint.
- **Google Gemini**: Deep context reasoning (`gemini-2.5-flash`, `gemini-2.5-pro`).
- **Local OpenAI Compatible**: Local inference via Ollama or vLLM (`http://localhost:11434/v1`).

### Routing Modes
1. **`fixed`**: Strictly routes all calls to the user-selected provider.
2. **`fallback`**: Tries the primary provider; automatically fails over to secondary providers upon exhaustion or HTTP 429 rate limits.
3. **`automatic` (Health-Aware)**: Dynamically selects the healthiest provider based on runtime telemetry:
   - Success rate tracking per provider.
   - Exponential moving average of response latency.
   - Automatic cooldown on rate-limited providers.

---

## 8. Multi-Tier Tool Ecosystem & Policy

To avoid code sprawl and enforce software reuse, AMAS organizes all tools into a strict **5-Tier Precedence Hierarchy** (`amas/tools/`):

```
Tier 1: PraisonAI Official Ecosystem (praisonai, praisonaiagents)
   ↓
Tier 2: LangChain Community Tools (langchain_community, langchain_core)
   ↓
Tier 3: Model Context Protocol (MCP) Tools
   ↓
Tier 4: Official Provider & Service SDKs (Tavily, Yahoo Finance, Exa, Brave, Serper)
   ↓
Tier 5: AMAS Custom Tools (ONLY when justified for project-specific math/storage)
```

### Tool Catalog

| Tool ID | Source Tier | Purpose | Permissions | Justification |
| :--- | :--- | :--- | :--- | :--- |
| `praison_web_search` | **Tier 1 (PraisonAI)** | DuckDuckGo search via PraisonAI | Read-Only, Network | Native framework tool |
| `praison_file_read` | **Tier 1 (PraisonAI)** | Safe reading of workspace files | Read-Only, Workspace | Native framework tool |
| `praison_code_interpreter` | **Tier 1 (PraisonAI)** | Isolated mathematical evaluation | Sandboxed, No Net | Native framework tool |
| `langchain_wikipedia` | **Tier 2 (LangChain)** | Wikipedia encyclopedic lookups | Read-Only, Network | Community reference tool |
| `official_tavily_search` | **Tier 4 (Official SDK)** | High-precision web search with citations | Read-Only, Network | AI-optimized live search |
| `official_financial_retriever`| **Tier 4 (Official SDK)** | Historical and real-time market data | Read-Only, Network | Direct Yahoo Finance API |
| `official_exa_search` | **Tier 4 (Official SDK)** | Neural semantic web search | Read-Only, Network | High-relevance research |
| `official_brave_search` | **Tier 4 (Official SDK)** | Independent web index search | Read-Only, Network | Privacy-preserving fallback |
| `official_serper_search` | **Tier 4 (Official SDK)** | Google SERP search | Read-Only, Network | Breadth search index |
| `amas_financial_risk_calculator`| **Tier 5 (Custom)** | Sharpe ratio & volatility math | Pure Math, No IO | Deterministic quant math |
| `amas_telemetry_anomaly_detector`| **Tier 5 (Custom)** | Z-score outlier detection ($> 2.2\sigma$) | Pure Math, No IO | Zero-IO statistical engine |
| `amas_artifact_writer` | **Tier 5 (Custom)** | Formatted Markdown deliverable export | Workspace Write | Local artifact persistence |
| `web_search` | **Tier 5 (Orchestration)** | Multi-provider search with fallback | Read-Only, Network | Search failover controller |

---

## 9. Internet Search & Real-Time Web Intelligence

AMAS features a dedicated multi-provider search subsystem (`amas/tools/web_search_manager.py`):

```
                   User Query
                       │
                       ▼
           ┌───────────────────────┐
           │   WebSearchManager    │
           └───────────┬───────────┘
                       │
       ┌───────────────┼───────────────┬───────────────┐
       ▼               ▼               ▼               ▼
┌──────────────┐┌──────────────┐┌──────────────┐┌──────────────┐
│ Tavily API   ││   Exa API    ││  Brave API   ││  Serper API  │
│ (AI Answers) ││   (Neural)   ││ (Independent)││   (Google)   │
└──────┬───────┘└──────┬───────┘└──────┬───────┘└──────┬───────┘
       │ [Fail]        │ [Fail]        │ [Fail]        │ [Fail]
       └───────────────┴───────┬───────┴───────────────┘
                               ▼
                   ┌───────────────────────┐
                   │ DuckDuckGo Fallback   │
                   │ (Zero Config Needed)  │
                   └───────────────────────┘
```

- **Tavily AI Direct Answer & Citations**: Extracts synthesized summaries alongside top ranked sources, URLs, and snippets.
- **Automatic Fallover Chain**: If Tavily is unconfigured or rate-limited, requests fail over to Exa, Brave, Serper, and finally DuckDuckGo.
- **Citation Tracking**: Every search output includes structured citations (`title`, `url`, `snippet`) that are attached to the run blackboard and audited by the Verification Agent.

---

## 10. Independent Verification & Adversarial Audit Gate

To eliminate LLM self-grading bias, the Verification Auditor (`amas/verification/auditor.py`) runs objective assertions before certifying any deliverable:

1. **Independent Numerical Recalculation**:
   - For financial tasks: Extracts the raw price series from the blackboard, recalculates daily returns, annualized volatility, and Sharpe ratio from first principles, and checks that the reported values match within tolerance ($\pm 5\%$).
   - For anomaly detection: Re-computes standard deviations and Z-scores against raw sensor vectors.
2. **Mathematical Boundary Checks**:
   - Rejects unfeasible Sharpe ratios outside $[-10, 25]$.
   - Flags negative volatility or probability values $> 1.0$.
3. **Evidence & Citation Coverage**:
   - Measures the ratio of factual assertions supported by retrieved search citations.
   - Verifies URL validity and source diversity.
4. **Weighted Quality Score**:
   - Computed as: $\text{Score} = 0.40 \times \text{NumericalAccuracy} + 0.30 \times \text{EvidenceCoverage} + 0.20 \times \text{CitationCoverage} + 0.10 \times \text{Completeness}$.
   - Deliverables achieving $\ge 85\%$ receive a `VERIFIED` certification badge in the UI.

---

## 11. Self-Healing & Diagnostic Recovery Agent

When a task fails or verification rejects an output, the Recovery Agent (`amas/control_plane/recovery_agent.py`) diagnoses the root cause and selects an appropriate recovery strategy:

```
Task Fault Detected
       │
       ▼
Diagnostic Classifier ──► Identifies Fault Type:
                             ├── Rate Limit / 429 ────────► SWITCH_PROVIDER
                             ├── Search Network Error ────► SWITCH_SEARCH_PROVIDER
                             ├── Invalid Tool Arguments ──► MODIFY_ARGUMENTS
                             ├── Math Verification Fail ──► REPLAN_TASK
                             ├── Timeout / Glitch ────────► RETRY_WITH_BACKOFF
                             ├── Sensitive Operation ─────► REQUEST_HUMAN_APPROVAL
                             └── Permission / Violation ──► ABORT
```

- **Exponential Backoff**: Prevents hammering endpoints during transient outages.
- **Max Retries Bound**: Prevents infinite loops by setting a hard execution limit (default: 3 attempts).
- **Audit Logging**: Every recovery attempt is logged to the database with error classifications and rationale.

---

## 12. Security Architecture & Restricted Execution

AMAS adheres to defense-in-depth principles:

1. **Arbitrary RCE Blocked**: Insecure endpoints executing arbitrary user code over HTTP are blocked (`/api/run-python` returns HTTP 403 for arbitrary scripts).
2. **Restricted Python Evaluator**:
   - Dangerous built-ins stripped: `__import__`, `eval`, `exec`, `open`, `compile`.
   - Critical system modules blocked: `os`, `sys`, `subprocess`, `shutil`, `socket`.
   - Allowed operations: Safe mathematical evaluation (`math`, `statistics`, array operations).
3. **Workspace Path Isolation**: File reading and writing operations are restricted to authorized project subdirectories; directory traversal (`../`) is blocked.
4. **Tool Permission Boundaries**: Tools declare granular permissions (`read_only`, `workspace_bound`, `pure_math`, `requires_approval`).
5. **Human-in-the-Loop Approvals**: High-impact or destructive operations require explicit human approval via durable SQLite states (`PENDING` $\rightarrow$ `APPROVED` / `REJECTED`).
6. **Zero Secret Exposure**: API keys are never returned in REST endpoints, written to SQLite, logged in console outputs, or sent over SSE streams.

---

## 13. Persistence, SQLite Schema & Storage Layer

All workflow operations persist to SQLite (`amas/storage/amas.db`) via `amas/storage/database.py`:

```
┌────────────────────────────────────────────────────────────────────────┐
│                              AMAS DATABASE                             │
├──────────────────┬──────────────────┬──────────────────┬───────────────┤
│ runs             │ tasks            │ events           │ approvals     │
│ - run_id (PK)    │ - task_id (PK)   │ - event_id (PK)  │ - req_id (PK) │
│ - objective      │ - run_id (FK)    │ - run_id (FK)    │ - run_id (FK) │
│ - status         │ - title          │ - event_type     │ - tool_id     │
│ - provider       │ - agent          │ - payload_json   │ - status      │
│ - model          │ - status         │ - timestamp      │ - created_at  │
│ - start_time     │ - result         │                  │               │
│ - end_time       │ - duration_ms    │                  │               │
│ - metrics_json   │ - verification   │                  │               │
│ - blackboard_json│                  │                  │               │
└──────────────────┴──────────────────┴──────────────────┴───────────────┘
```

- **Tool Metrics (`tool_metrics`)**: Persists total calls, success counts, failures, and average latency per tool across application restarts.
- **Artifacts Storage (`amas/storage/artifacts/`)**: Stores full markdown deliverables, analytical reports, and synthesized summaries on disk.

---

## 14. Repository Structure

```
├── amas/                                 # Core AMAS Engine Package
│   ├── control_plane/                    # DAG orchestration & execution engine
│   │   ├── event_bus.py                  # Real-time event publisher for SSE streaming
│   │   ├── policy_manager.py             # Human approval policies & backoff calculator
│   │   ├── run_manager.py                # Master workflow execution runner & deliverable compiler
│   │   ├── task_graph.py                 # Topological DAG dependency tracker with cycle detection
│   │   └── recovery_agent.py             # Diagnostic error classifier & recovery strategies
│   ├── providers/                        # Provider-Agnostic LLM Layer
│   │   ├── base.py                       # LLMProvider interface & capability specifications
│   │   ├── gemini_provider.py            # Google Gemini native adapter
│   │   ├── manager.py                    # ProviderManager with fallback, health checks & telemetry
│   │   └── openai_compatible.py          # Unified Groq / OpenRouter / CodeCraft / Custom adapter
│   ├── runtime/                          # Agent Runtime Engine
│   │   ├── agents.py                     # 6 specialized agent role definitions
│   │   ├── memory.py                     # Scoped blackboard & accumulated task results store
│   │   ├── planner.py                    # Dynamic LLM DAG planner with anti-placeholder validation
│   │   └── praison_runtime.py            # Task execution runner, argument sanitizer & PraisonAI glue
│   ├── storage/                          # Persistent Storage & Database
│   │   ├── artifacts/                    # Generated project deliverables (e.g. india_flood_summary.md)
│   │   ├── amas.db                       # SQLite database (runs, tasks, events, metrics)
│   │   └── database.py                   # Thread-safe SQLite database manager
│   ├── tools/                            # Multi-Tier Tool Ecosystem
│   │   ├── adapters/                     # Tier 1 & Tier 2 wrappers
│   │   │   ├── langchain_adapter.py      # LangChain Wikipedia adapter
│   │   │   └── praisonai_adapter.py      # PraisonAI Web Search, File Reader, Code Interpreter
│   │   ├── custom/                       # Tier 5 custom tools
│   │   │   ├── artifact_writer.py        # Report deliverable exporter
│   │   │   ├── risk_calculator.py        # Sharpe ratio, return & volatility math
│   │   │   └── telemetry_detector.py     # Z-score outlier detector (> 2.2 sigma)
│   │   ├── official/                     # Tier 4 official SDK integrations
│   │   │   ├── tavily_search.py          # Tavily, Exa, Brave, Serper search tools
│   │   │   └── yahoo_finance.py          # Yahoo Finance real market data
│   │   ├── web_search_manager.py         # Multi-provider search failover controller
│   │   ├── base.py                       # AMASTool base, permissions, metadata
│   │   └── registry.py                   # Central discovery & execution registry with telemetry
│   ├── verification/                     # Independent Verification & Audit
│   │   └── auditor.py                    # Adversarial constraint checks with independent recalculation
│   └── cli.py                            # Unified AMAS Command-Line Interface
├── server.ts                             # Express API server with SSE endpoint & Vite dev middleware
├── src/                                  # React 19 + TypeScript Frontend
│   ├── components/
│   │   ├── AgentArchitecture.tsx         # Agent profiles & verified tool catalog
│   │   ├── EvaluationSuiteView.tsx       # Live benchmark suite view
│   │   ├── Header.tsx                    # Branding, engine badges, provider switcher
│   │   ├── MarkdownRenderer.tsx          # Custom GFM markdown renderer with formatted tables
│   │   ├── ProviderSettingsModal.tsx     # Live provider/model switcher & ping tester
│   │   ├── SubmissionHub.tsx             # Standalone code view & exports
│   │   └── WorkflowStudio.tsx            # Interactive DAG runner & deliverable viewer
│   ├── App.tsx                           # Master application state runner
│   └── types.ts                          # Shared TypeScript domain interfaces
├── autonomous_multi_agent_system.py      # Standalone CLI entrypoint
├── tests/                                # Automated Unit & Integration Tests
│   └── test_amas_suite.py                # Comprehensive test suite
├── requirements.txt                      # Python dependencies
├── .env.example                          # Environment variable configuration template
└── package.json                          # Frontend dependencies & scripts
```

---

## 15. CLI & REST API Reference

### CLI Commands

AMAS provides a CLI for headless automation, scripting, and continuous integration:

```bash
# 1. Run an autonomous workflow
python -m amas.cli run "Investigate current floods in India: deaths, relief funds, and infrastructure damage"

# 2. List registered providers and their health metrics
python -m amas.cli providers

# 3. Test connectivity and latency for a specific provider
python -m amas.cli test-provider groq

# 4. List all registered tools and their source tiers
python -m amas.cli tools

# 5. Execute a tool directly with JSON input
python -m amas.cli execute-tool official_financial_retriever '{"ticker": "AAPL", "period_days": 14}'

# 6. Run the automated evaluation suite
python -m amas.cli eval
```

### Key REST Endpoints (`server.ts`)

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/system-info` | `GET` | System health, active provider, model, and engine capabilities. |
| `/api/providers` | `GET` | List all providers, supported models, and runtime health stats. |
| `/api/providers/:id/test` | `POST` | Perform a live connection test for a provider. |
| `/api/tools` | `GET` | Tool registry catalog with sources, permissions, and metrics. |
| `/api/tools/execute` | `POST` | Execute a tool directly under permission boundaries. |
| `/api/workflow/run` | `POST` | Execute an autonomous multi-agent DAG workflow. |
| `/api/runs/:runId/events` | `GET` | Real-time Server-Sent Events (SSE) stream for live DAG updates. |
| `/api/evaluation/run` | `POST` | Run the automated benchmark test suite. |

---

## 16. Quick Start & Local Setup

### Prerequisites
- **Node.js**: v18.0.0 or higher
- **Python**: 3.10, 3.11, or 3.12

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/AmanKumar-St/AMAS-Autonomus-Multi-agent-Task-Automation-system.git
cd AMAS-Autonomus-Multi-agent-Task-Automation-system

# Install Node frontend dependencies
npm install

# Install Python backend dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Configure your preferred LLM provider and search keys:
```ini
# Primary Provider (e.g. Groq for ultra-fast inference)
GROQ_API_KEY="gsk_..."

# Optional Providers
OPENROUTER_API_KEY="sk-or-..."
CODECRAFT_API_KEY="..."
GEMINI_API_KEY="..."

# Web Search API (Tavily recommended for AI research)
TAVILY_API_KEY="tvly-..."

# Optional Search Providers
EXA_API_KEY="..."
BRAVE_SEARCH_API_KEY="..."
SERPER_API_KEY="..."
```

### 3. Launch the Application
```bash
npm run dev
```
Navigate to **`http://localhost:3000`** in your browser.

### 4. Run Automated Test Suite
```bash
python -m unittest tests/test_amas_suite.py -v
```

---

## 17. Quality Benchmarks & Evaluation Suite

AMAS features an automated evaluation benchmark (`python -m amas.cli eval`) testing 7 operational dimensions:

1. **Dynamic DAG Planning**: Asserts that task graphs are dynamically synthesized without hardcoded routing.
2. **Cycle Prevention**: Validates topological DFS sorting and cyclic graph rejection.
3. **Tool Precedence Compliance**: Confirms strict adherence to the 5-Tier Tool Hierarchy.
4. **Provider Failover**: Verifies automatic failover from rate-limited primary providers to secondary endpoints.
5. **Mathematical Verification**: Asserts that corrupted calculation outputs (e.g. Sharpe ratio 150) are rejected by the independent verification gate.
6. **Search Multi-Provider Failover**: Validates fallback from primary search SDKs to alternative engines.
7. **Sandbox Security Boundaries**: Confirms that unauthorized builtins and system calls are blocked.

---

## License

This project is licensed under the **MIT License**. See the `LICENSE` file for details.
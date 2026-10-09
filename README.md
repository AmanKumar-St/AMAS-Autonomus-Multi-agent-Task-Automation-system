# AMAS — Autonomous Multi-Agent Automation System

[![PraisonAI](https://img.shields.io/badge/PraisonAI-1.7.11-blue.svg)](https://praison.ai)
[![Provider Agnostic](https://img.shields.io/badge/LLM-Provider--Agnostic-purple.svg)](https://github.com)
[![TypeScript](https://img.shields.io/badge/TypeScript-React%2019-3178C6.svg)](https://www.typescriptlang.org)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-yellow.svg)](https://python.org)

An autonomous multi-agent task automation platform with dynamic LLM-generated DAG execution, a strict multi-tier tool selection policy, shared blackboard memory, independent verification gates, and provider-agnostic LLM routing.

---

## Table of Contents

1. [Executive Overview](#1-executive-overview)
2. [Key Architectural Features](#2-key-architectural-features)
3. [Provider-Agnostic LLM Architecture](#3-provider-agnostic-llm-architecture)
4. [Tool Selection & Integration Policy](#4-tool-selection--integration-policy)
5. [Multi-Agent System Architecture](#5-multi-agent-system-architecture)
6. [Security & Sandbox Architecture](#6-security--sandbox-architecture)
7. [Repository Structure](#7-repository-structure)
8. [CLI & REST API Reference](#8-cli--rest-api-reference)
9. [Quick Start & Local Setup](#9-quick-start--local-setup)
10. [Evaluation & Quality Benchmarks](#10-evaluation--quality-benchmarks)

---

## 1. Executive Overview

**AMAS (Autonomous Multi-Agent Automation System)** transforms standard prompt-and-response AI into an autonomous execution engine. Rather than acting as a monolithic conversational bot that fabricates facts or hallucinates calculations, AMAS:

1. **Accepts High-Level Natural Language Goals**: From multi-source crisis response to quantitative risk analysis.
2. **Dynamically Synthesizes an Execution DAG**: Generates a Directed Acyclic Graph (DAG) with exact dependency ordering and least-privilege tool access based on the query, without brittle keyword `if/else` routers.
3. **Executes via Agent Runtime**: Orchestrates specialized agents (`Planner`, `Researcher`, `Analyst`, `Executor`, `Verifier`, `Recovery`) with PraisonAI integration where available.
4. **Enforces Tool Ecosystem Precedence**: Prioritizes native PraisonAI tools and LangChain community tools before falling back to official SDKs or custom calculations.
5. **Shares Context via Structured Blackboard**: Eliminates the "telephone game" by writing intermediate tables, prices, and facts to a typed blackboard.
6. **Self-Heals on Transient Glitches**: Applies structured recovery strategies (retry with backoff, provider/tool switching, argument modification, replanning) beyond simple retries.
7. **Independently Audits Deliverables**: Evaluates results against mathematical bounds, evidence coverage, citation validity, and numerical accuracy before certifying the final deliverable.

---

## 2. Key Architectural Features

| Challenge in Standard LLM Apps | How AMAS Solves It |
| :--- | :--- |
| **Monolithic Hallucination** | **Strict Separation of Concerns**: Agent roles isolate research, analysis, and execution. Computations are delegated to deterministic code tools rather than token probability guessing. |
| **Vendor Lock-in** | **Provider-Agnostic Engine**: Unified provider layer supporting Groq, OpenRouter, CodeCraft, Google Gemini, and local OpenAI-compatible endpoints (Ollama, vLLM, LM Studio) with fallback and health-aware routing. |
| **Synthetic / Fake Data** | **Authentic Grounding**: Live tools pull authentic market data and verified web sources. When live retrieval fails, outputs honestly report unavailability rather than fabricating data. |
| **Brittle Hardcoded Routers** | **Dynamic LLM-Generated DAGs**: The Planning Agent compiles high-level objectives into topological dependency graphs at runtime with cycle detection. |
| **Tool Sprawl & Random Implementations** | **Strict Tool Hierarchy**: Enforces PraisonAI tools $\rightarrow$ LangChain tools $\rightarrow$ MCP $\rightarrow$ Official SDKs $\rightarrow$ AMAS Custom (strictly justified). |
| **Remote Code Execution Vulnerabilities** | **Restricted Python Execution**: Arbitrary remote code execution via HTTP is blocked; sandboxed Python evaluator restricts dangerous builtins (`__import__`, `os`, `sys`, `subprocess`, `eval`). Not a zero-trust sandbox — honestly described as restricted execution. |

---

## 3. Provider-Agnostic LLM Architecture

AMAS decouples agent intelligence from model providers. The runtime automatically adapts prompts, tool calling conventions, and retry logic across providers.

```
+-------------------------------------------------------------------------+
|                          LLM Provider Manager                           |
|      (Fixed Selection | Fallback Chain | Health-Aware Routing)           |
+-------------------------------------------------------------------------+
       |                   |                   |                   |
       v                   v                   v                   v
+--------------+    +--------------+    +--------------+    +--------------+
|     Groq     |    |  OpenRouter  |    |  CodeCraft   |    |    Gemini    |
| (Ultra-Fast) |    |  (100+ LLMs) |    |  (Coding)    |    |  (1M Context)|
+--------------+    +--------------+    +--------------+    +--------------+
       |                   |                   |                   |
       +-------------------+-------------------+-------------------+
                                   |
                                   v
              +-------------------------------------------+
              |       Custom / Local OpenAI-Compatible    |
              |       (Ollama, vLLM, LM Studio)           |
              +-------------------------------------------+
```

### Supported Providers

- **Groq**: Ultra-low latency inference (`openai/gpt-oss-120b`, `openai/gpt-oss-20b`, `qwen/qwen3.8-27b`).
- **OpenRouter**: Access to frontier models (`meta-llama/llama-3.3-70b-instruct`, `anthropic/claude-3.5-sonnet`, `deepseek/deepseek-chat`).
- **CodeCraft**: High-throughput programming and code synthesis endpoint.
- **Google Gemini**: Deep context reasoning (`gemini-2.5-flash`, `gemini-2.5-pro`).
- **Custom / Local**: Local inference via Ollama or vLLM (`http://localhost:11434/v1`).

### Fallback Policies

- **`fixed`**: Uses the chosen provider exclusively and raises on hard failures.
- **`fallback`**: Tries primary provider; falls back to secondary provider upon exhaustion or rate limiting.
- **`automatic`**: Dynamically prioritizes healthy providers based on success rate and latency.

### Health-Aware Routing

In `automatic` mode, the ProviderManager tracks per-provider health metrics (success rate, average latency, rate-limit state) and selects the healthiest available provider for each request. Health data persists across restarts.

---

## 4. Tool Selection & Integration Policy

To avoid redundant custom scripts, AMAS implements a strict 5-tier tool source hierarchy:

```
Tier 1: PraisonAI Official Ecosystem (praisonai, praisonaiagents)
   ↓
Tier 2: LangChain Community Tools (langchain_community, langchain_core)
   ↓
Tier 3: Model Context Protocol (MCP) Tools
   ↓
Tier 4: Official Provider & Service SDKs (e.g. Yahoo Finance, Tavily, Exa, Brave, Serper)
   ↓
Tier 5: AMAS Custom Tools (ONLY when justified for project-specific math/storage)
```

### Registered Tools in AMAS

| Tool ID | Source Tier | Purpose | Permissions |
| :--- | :--- | :--- | :--- |
| `praison_web_search` | **Tier 1 (PraisonAI)** | Live internet research via DuckDuckGo | Read-Only, Network |
| `praison_file_read` | **Tier 1 (PraisonAI)** | Safe reading of approved project workspace files | Read-Only, Workspace |
| `praison_code_interpreter` | **Tier 1 (PraisonAI)** | Isolated mathematical evaluation & data transformation | Sandboxed, No Net |
| `langchain_wikipedia` | **Tier 2 (LangChain)** | Authoritative encyclopedic lookups & reference facts | Read-Only, Network |
| `official_tavily_search` | **Tier 4 (Official SDK)** | High-quality live web search with citations via Tavily API | Read-Only, Network |
| `official_exa_search` | **Tier 4 (Official SDK)** | Neural web search via Exa API | Read-Only, Network |
| `official_brave_search` | **Tier 4 (Official SDK)** | Privacy-focused web search via Brave API | Read-Only, Network |
| `official_serper_search` | **Tier 4 (Official SDK)** | Google search results via Serper API | Read-Only, Network |
| `ddgs_fallback_search` | **Tier 6 (Fallback)** | Zero-config DuckDuckGo fallback when no API keys available | Read-Only, Network |
| `official_financial_retriever` | **Tier 4 (Official SDK)** | Real-time equity prices and trade volumes via Yahoo Finance API | Read-Only, Network |
| `amas_financial_risk_calculator` | **Tier 5 (Custom)** | Deterministic Sharpe ratio, volatility & return calculations | Pure Math, No IO |
| `amas_telemetry_anomaly_detector` | **Tier 5 (Custom)** | Z-score statistical outlier detection (> $2.2\sigma$) | Pure Math, No IO |
| `amas_artifact_writer` | **Tier 5 (Custom)** | Formatted Markdown deliverable generation & export | Workspace Write |
| `web_search` | **Tier 5 (Custom Orchestration)** | Unified multi-provider search with automatic fallback | Read-Only, Network |

*Custom tools require explicit architectural justification recorded in tool metadata.*

---

## 5. Multi-Agent System Architecture

```
                                +-------------------------+
                                |    Natural Prompt /     |
                                |    Objective Directives |
                                +------------+------------+
                                             |
                                             v
                                +-------------------------+
                                |     Planning Agent      |
                                |  (Dynamic DAG Builder)  |
                                +------------+------------+
                                             |
                          Topological Execution Coordinator
                                             |
         +-----------------------------------+-----------------------------------+
         |                                   |                                   |
         v                                   v                                   v
+-------------------+               +-------------------+               +-------------------+
|  Research Agent   |               |  Analysis Agent   |               |  Execution Agent  |
| (Web & Knowledge) |               | (Metrics & Stats) |               | (Code & Actions)  |
+---------+---------+               +---------+---------+               +---------+---------+
         \                                   |                                   /
          \                                  |                                  /
           +---------------------------------+---------------------------------+
                                             |
                                             v
                                +-------------------------+
                                |    Shared Blackboard    |
                                | (Scoped State & Tables) |
                                +------------+------------+
                                             |
                                             v
                                +-------------------------+
                                |   Verification Auditor  |
                                |  (Independent Gate)     |
                                +------------+------------+
                                      /             \
                            [FAILED] /               \ [APPROVED]
                                    v                 v
                         +-------------------+   +-------------------------+
                         |  Recovery Agent   |   | Verified Final Output   |
                         | (Strategy-Based)  |   | (Artifact & Summary)    |
                         +-------------------+   +-------------------------+
```

### The 6 Specialized Agent Roles

1. **Planning Agent (`PlanningAgent`)**: Formulates the multi-step DAG, assigns agent specializations, and allocates least-privilege tool sets. Records `planning_mode` (llm, repaired_llm, fallback).
2. **Research Agent (`ResearchAgent`)**: Queries external sources, live financial markets, Wikipedia, or web search without hallucination.
3. **Analysis Agent (`AnalysisAgent`)**: Evaluates raw data, calculates statistical distributions, and detects variance anomalies.
4. **Execution Agent (`ExecutionAgent`)**: Runs sandboxed formulas, executes data processing steps, and generates deliverable documents.
5. **Verification Agent (`VerificationAgent`)**: Independent quality gate. Checks mathematical bounds (with independent recalculation), inspects citations, validates evidence coverage, and flags ungrounded claims.
6. **Recovery Agent (`RecoveryAgent`)**: Diagnoses execution faults, classifies error types, and selects recovery strategies (retry, switch provider/tool, modify arguments, simplify request, replan, request approval, abort).

### Dynamic DAG Planning (No Hardcoded Routing)

AMAS replaces hardcoded `if "finance" in prompt` scripts with an LLM-driven DAG planner (`amas/runtime/planner.py`). Given any high-level objective, the planner emits structured JSON specifying:
- Sequential and parallel task nodes
- Dependencies (`depends_on: ["task_1"]`)
- Required agent role
- Required tool whitelist
- Input argument bindings from blackboard memory

**DAG Validation**: The TaskGraph (`amas/control_plane/task_graph.py`) validates unique task IDs, dependency existence, and performs cycle detection using DFS before execution.

**Planner Fallback**: If LLM output is unparseable, a baseline 3-task decomposition is used with `planning_mode: "fallback"` recorded in metadata. The UI can distinguish autonomous planning from fallback execution.

### Blackboard Shared Memory Pattern

Agents read and write to a structured, scoped memory store (`amas/runtime/memory.py`):
```python
# Shared Blackboard State
{
    "ticker": "AAPL",
    "period_days": 30,
    "prices": [257.5, 260.1, 258.9, 262.4, ...],
    "computed_metrics": {
        "sharpe_ratio": 3.98,
        "annualized_volatility": 0.174,
        "annualized_return": 0.692
    },
    "verification_verdict": {
        "status": "VERIFIED",
        "score": 0.94,
        "evidence_coverage": 0.92,
        "citation_coverage": 1.0,
        "numerical_accuracy": 1.0,
        "checks_passed": [
            "Sharpe ratio independently verified: 3.98",
            "Annualized volatility independently verified: 17.4%",
            "Evidence grounded: 7 sources retrieved",
            "Citations present: 7 references"
        ]
    }
}
```

### Independent Verification Gate

The Verification Auditor (`amas/verification/auditor.py`) runs objective assertions before any task can be marked `COMPLETED`:
- **Output Completeness**: Ensures minimum substantive length and structured formatting.
- **Financial Boundary Check**: Rejects Sharpe ratios outside $[-10, 25]$ or negative volatility.
- **Independent Numerical Recalculation**: Recomputes Sharpe, volatility, returns, and anomaly Z-scores from raw data; compares against reported values within tolerance.
- **Evidence Coverage**: Measures fraction of claims backed by retrieved sources.
- **Citation Coverage**: Verifies that output claims have corresponding source citations.
- **Realistic Scoring**: Weighted score (40% numerical accuracy, 30% evidence coverage, 20% citation coverage, 10% other checks) — no hardcoded 100% values.

### Recovery Strategies

The Recovery Agent (`amas/control_plane/recovery_agent.py`) classifies errors and selects strategies:
- `RETRY_WITH_BACKOFF` — transient network issues
- `SWITCH_PROVIDER` — provider failure or rate limiting
- `SWITCH_SEARCH_PROVIDER` — search API failure
- `SWITCH_TOOL` — tool unavailable
- `MODIFY_ARGUMENTS` — invalid input parameters
- `SIMPLIFY_REQUEST` — reduce scope
- `REPLAN_TASK` — verification failure
- `REQUEST_HUMAN_APPROVAL` — permission required
- `ABORT` — security violation or exhausted retries

---

## 6. Security & Sandbox Architecture

1. **Arbitrary RCE Blocked**: Insecure endpoints executing unvalidated user scripts over HTTP are blocked (`/api/run-python` returns 403 for arbitrary scripts).
2. **Restricted Python Interpreter**: Restricted execution environment (NOT a zero-trust sandbox):
    - Builtins stripped: `__import__`, `eval`, `exec`, `open`, `compile` deleted.
    - Modules blocked: `os`, `sys`, `subprocess`, `shutil`, `socket` blocked.
    - Allowed primitives: `math`, `statistics`, `json`, array manipulations.
    - Honestly described as "Restricted Python Execution" — no container/OS isolation.
3. **Workspace Isolation**: File read/write tools are strictly bound to authorized project subdirectories; path traversals (`../`) are rejected.
4. **Tool Permission Boundaries**: Tools require explicit flags (`read_only`, `requires_approval`, `network_required`).
5. **Human Approval Workflow**: Durable approval state persisted to SQLite with `PENDING` → `APPROVED`/`REJECTED` transitions.
6. **No Secret Exposure**: API keys never exposed to frontend, logs, database, or SSE streams.

---

## 7. Repository Structure

```
├── amas/                                 # Core AMAS Engine Package
│   ├── control_plane/                    # DAG orchestration & execution engine
│   │   ├── event_bus.py                  # Real-time event publisher for UI streaming (SSE)
│   │   ├── policy_manager.py             # Human approval policies & backoff calculator
│   │   ├── run_manager.py                # End-to-end master workflow runner
│   │   ├── task_graph.py                 # Topological DAG dependency tracker with cycle detection
│   │   └── recovery_agent.py             # Structured error classification & recovery strategies
│   ├── providers/                        # Provider-Agnostic LLM Layer
│   │   ├── base.py                       # LLMProvider base & capability specs
│   │   ├── gemini_provider.py            # Google Gemini adapter
│   │   ├── manager.py                    # ProviderManager with fallback, health checks & metrics
│   │   └── openai_compatible.py          # Unified Groq / OpenRouter / CodeCraft / Custom adapter
│   ├── runtime/                          # Agent Runtime
│   │   ├── agents.py                     # 6 specialized agent role definitions
│   │   ├── memory.py                     # Scoped blackboard & session memory
│   │   ├── planner.py                    # Dynamic LLM DAG planner with fallback tracking
│   │   └── praison_runtime.py            # Task execution runner & PraisonAI glue
│   ├── storage/                          # Persistent storage & SQLite schema
│   │   ├── artifacts/                    # Generated project reports & deliverables
│   │   ├── amas.db                       # Runs, tasks, events, approvals, tool calls, tool metrics
│   │   └── database.py                   # SQLite database manager
│   ├── tools/                            # Multi-tier tool architecture
│   │   ├── adapters/                     # Tier 1 & Tier 2 wrappers
│   │   │   ├── langchain_adapter.py      # LangChain Wikipedia adapter
│   │   │   └── praisonai_adapter.py      # PraisonAI Web Search, File Reader, Code Interpreter
│   │   ├── custom/                       # Tier 5 justified tools
│   │   │   ├── artifact_writer.py        # Report exporter
│   │   │   ├── risk_calculator.py        # Sharpe ratio & portfolio math
│   │   │   └── telemetry_detector.py     # Z-score outlier detector
│   │   ├── official/                     # Tier 4 official SDK tools
│   │   │   ├── tavily_search.py          # Tavily, Exa, Brave, Serper search tools
│   │   │   └── yahoo_finance.py          # Yahoo Finance real market data
│   │   ├── web_search_manager.py         # Unified multi-provider search with fallback
│   │   ├── base.py                       # AMASTool, permissions, metadata
│   │   └── registry.py                   # Central discovery & execution registry with DB metrics
│   ├── verification/                     # Independent Verification & Audit
│   │   └── auditor.py                    # Adversarial constraint checks with independent recalculation
│   └── cli.py                            # Unified AMAS Command-Line Interface
├── server.ts                             # Express API server with SSE endpoint & Vite dev middleware
├── src/                                  # React 19 + TypeScript Frontend
│   ├── components/
│   │   ├── AgentArchitecture.tsx         # Agent profiles & verified tool catalog
│   │   ├── EvaluationSuiteView.tsx       # Live benchmark suite (empty state until run)
│   │   ├── Header.tsx                    # Branding, engine badges, provider switcher
│   │   ├── ProviderSettingsModal.tsx     # Live provider/model switcher & ping tester
│   │   ├── SubmissionHub.tsx             # Standalone code view & exports
│   │   └── WorkflowStudio.tsx            # Interactive DAG runner & deliverable viewer (no hardcoded fallbacks)
│   ├── App.tsx                           # Master application state runner (no auto-execution on load)
│   └── types.ts                          # Shared TypeScript domain interfaces
├── autonomous_multi_agent_system.py      # Legacy CLI wrapper (delegates to amas runtime)
├── tests/                                # Automated Unit & Integration Tests
│   └── test_amas_suite.py                # Comprehensive unit tests
├── requirements.txt                      # Python dependencies
├── .env.example                          # Environment variable template
├── .gitignore                            # Ignore cache, build, env, DB files
└── package.json                          # Dependencies & scripts
```

---

## 8. CLI & REST API Reference

### CLI Commands

AMAS provides a command-line interface for headless automation, testing, and evaluation:

```bash
# 1. Run an autonomous workflow
python -m amas.cli run "Perform 30-day volatility and Sharpe ratio analysis for NVDA"

# 2. List registered providers and their health
python -m amas.cli providers

# 3. Test provider connectivity
python -m amas.cli test-provider groq

# 4. List registered tools and source tiers
python -m amas.cli tools

# 5. Execute a tool directly with JSON input
python -m amas.cli execute-tool official_financial_retriever '{"ticker": "AAPL", "period_days": 14}'

# 6. Run the automated evaluation suite
python -m amas.cli eval
```

### Key REST Endpoints (`server.ts`)

- `GET /api/system-info` — System status, Python version, SQLite health.
- `GET /api/providers` — Active providers, models, latency metrics, capabilities, **health metrics**.
- `POST /api/providers/test` — Ping and validate an API key/endpoint.
- `GET /api/tools` — Tool registry catalog with sources, permissions, and **persisted metrics**.
- `POST /api/tools/execute` — Execute a tool with permission boundaries and approval checks.
- `POST /api/workflow/run` — Trigger an autonomous multi-agent workflow DAG.
- `GET /api/runs/:runId/events` — **Server-Sent Events (SSE) stream** for real-time workflow updates.
- `POST /api/runs/:runId/events` — Broadcast event to SSE subscribers.
- `GET /api/evaluation/run` — Run the automated evaluation benchmark suite.

---

## 9. Quick Start & Local Setup

### Prerequisites
- Node.js 18+ & npm
- Python 3.10+ (tested on Python 3.10, 3.11, 3.12)

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/AmanKumar-St/AMAS-Autonomus-Multi-agent-Task-Automation-system.git
cd AMAS-Autonomus-Multi-agent-Task-Automation-system

npm install
pip install -r requirements.txt
```

### 2. Configure API Keys
Copy the example environment file and configure your preferred provider:
```bash
cp .env.example .env
```
Edit `.env`:
```ini
# Primary Provider (e.g., Groq)
GROQ_API_KEY="gsk_..."

# Optional Providers
OPENROUTER_API_KEY="sk-or-..."
CODECRAFT_API_KEY="..."
GEMINI_API_KEY="..."

# REQUIRED for live web search
TAVILY_API_KEY="tvly-..."

# Optional Search Providers
EXA_API_KEY="..."
BRAVE_SEARCH_API_KEY="..."
SERPER_API_KEY="..."
```
*(Note: AMAS runs with local models or in degraded mode if API keys are not provided. Live web search requires at least one search API key.)*

### 3. Launch the Application
```bash
npm run dev
```
Open **[http://localhost:3000](http://localhost:3000)** in your browser.

### 4. Run Automated Tests
```bash
python -m unittest tests/test_amas_suite.py -v
```

---

## 10. Evaluation & Quality Benchmarks

AMAS includes an evaluation suite testing the full lifecycle across:
- **Dynamic DAG Planning**: Validates non-hardcoded task decomposition and cycle detection.
- **Tool Hierarchy Compliance**: Enforces PraisonAI $\rightarrow$ LangChain $\rightarrow$ Official SDK precedence.
- **Provider Switching**: Tests fallbacks across Groq, OpenRouter, and Gemini.
- **Recovery Strategies**: Verifies structured recovery (not just retry) for different error types.
- **Independent Verification**: Confirms mathematically unfeasible outputs (e.g. Sharpe ratio 150) are rejected with independent recalculation.
- **Sandbox Security**: Validates that attempted RCE and unauthorized imports are trapped.
- **No Fabrication**: Confirms that unavailable live data is honestly reported as unavailable.

```bash
# Run evaluation via CLI
python -m amas.cli eval
```

---

## Known Limitations

- **Restricted Python Execution** is not a zero-trust sandbox — it uses builtin/module filtering only. For production, consider subprocess/container isolation.
- **PraisonAI Integration** uses available Agent/Task APIs; full Team/Flow orchestration depends on installed PraisonAI version.
- **Real-time SSE** uses in-memory subscribers; not suitable for multi-instance deployments without Redis backend.
- **Automatic Provider Routing** uses success rate and latency heuristics; not a full ML-based router.
- **Human Approval** is durable in SQLite but requires frontend polling/SSE for real-time UX.
- **No Fabrication Policy** means live data unavailability results in explicit "unavailable" responses rather than synthesized content.

---

## License

This project is licensed under the MIT License.
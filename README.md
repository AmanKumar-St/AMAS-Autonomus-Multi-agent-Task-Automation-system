# AMAS — Autonomous Multi-Agent Automation System

[![PraisonAI](https://img.shields.io/badge/PraisonAI-4.7.13-blue.svg)](https://praison.ai)
[![PraisonAI Agents](https://img.shields.io/badge/PraisonAI--Agents-1.7.11-green.svg)](https://praison.ai)
[![Provider Agnostic](https://img.shields.io/badge/LLM-Provider--Agnostic-purple.svg)](https://github.com)
[![TypeScript](https://img.shields.io/badge/TypeScript-React%2019-3178C6.svg)](https://www.typescriptlang.org)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.14-yellow.svg)](https://python.org)

An enterprise-grade, provider-agnostic autonomous multi-agent task automation platform powered by **PraisonAI / PraisonAI Agents**, dynamic LLM-generated DAG execution, a strict multi-tier tool selection policy, shared blackboard memory, and adversarial verification gates.

---

## Table of Contents

1. [Executive Overview](#1-executive-overview)
2. [Key Architectural Innovations](#2-key-architectural-innovations)
3. [Provider-Agnostic LLM Architecture](#3-provider-agnostic-llm-architecture)
4. [Official Tool Selection & Integration Policy](#4-official-tool-selection--integration-policy)
5. [Multi-Agent System Architecture](#5-multi-agent-system-architecture)
   - [The 6 Specialized Agent Roles](#the-6-specialized-agent-roles)
   - [Dynamic DAG Planning (No Hardcoded Routing)](#dynamic-dag-planning-no-hardcoded-routing)
   - [Blackboard Shared Memory Pattern](#blackboard-shared-memory-pattern)
   - [Adversarial Verification Gate](#adversarial-verification-gate)
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
3. **Executes via PraisonAI Agents**: Orchestrates specialized autonomous agents (`Planner`, `Researcher`, `Analyst`, `Executor`, `Verifier`, `Recovery`).
4. **Enforces Tool Ecosystem Precedence**: Prioritizes native PraisonAI tools and LangChain community tools before falling back to official SDKs or custom calculations.
5. **Shares Context via Structured Blackboard**: Eliminates the "telephone game" by writing intermediate tables, prices, and facts to a typed blackboard.
6. **Self-Heals on Transient Glitches**: Applies exponential backoff retries and parameter corrections automatically.
7. **Adversarially Audits Deliverables**: Evaluates results against mathematical, consistency, and grounding constraints before certifying the final deliverable.

---

## 2. Key Architectural Innovations

| Challenge in Standard LLM Apps | How AMAS Solves It |
| :--- | :--- |
| **Monolithic Hallucination** | **Strict Separation of Concerns**: Agent roles isolate research, analysis, and execution. Computations are delegated to deterministic code tools rather than token probability guessing. |
| **Vendor Lock-in** | **Provider-Agnostic Engine**: Unified provider layer supporting Groq, OpenRouter, CodeCraft, Google Gemini, and local OpenAI-compatible endpoints (Ollama, vLLM, LM Studio) with live switching and fallback policies. |
| **Synthetic / Fake Data** | **Authentic Grounding**: Live tools pull authentic market data and verified web sources. When running in offline or simulation mode, outputs are explicitly marked with `source_type = "synthetic"`. |
| **Brittle Hardcoded Routers** | **Dynamic LLM-Generated DAGs**: The Planning Agent compiles high-level objectives into topological dependency graphs at runtime. |
| **Tool Sprawl & Random Implementations** | **Strict Tool Hierarchy**: Enforces PraisonAI tools $\rightarrow$ LangChain tools $\rightarrow$ MCP $\rightarrow$ Official SDKs $\rightarrow$ AMAS Custom (strictly justified). |
| **Remote Code Execution Vulnerabilities** | **Zero-Trust Sandbox**: Arbitrary remote code execution via HTTP is blocked; sandboxed Python evaluator restricts dangerous builtins (`__import__`, `os`, `sys`, `subprocess`, `eval`). |

---

## 3. Provider-Agnostic LLM Architecture

AMAS decouples agent intelligence from model providers. The runtime automatically adapts prompts, tool calling conventions, and retry logic across providers.

```
+-------------------------------------------------------------------------+
|                          LLM Provider Manager                           |
|      (Fixed Selection | Fallback Chain | Automatic Latency Routing)      |
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
             |       (Ollama, vLLM, LM Studio, vLLM)     |
             +-------------------------------------------+
```

### Supported Providers

- **Groq**: Ultra-low latency inference (`openai/gpt-oss-120b`, `openai/gpt-oss-20b`, `qwen/qwen3.8-27b`). Auto-nudge recovery handles OSS tool-syntax nuances.
- **OpenRouter**: Access to top frontier models (`meta-llama/llama-3.3-70b-instruct`, `anthropic/claude-3.5-sonnet`, `deepseek/deepseek-chat`).
- **CodeCraft**: High-throughput programming and code synthesis endpoint.
- **Google Gemini**: Deep context reasoning (`gemini-2.5-flash`, `gemini-2.5-pro`).
- **Custom / Local**: Local inference via Ollama or vLLM (`http://localhost:11434/v1`).

### Fallback Policies
- **`fixed`**: Uses the chosen provider exclusively and raises on hard failures.
- **`fallback`**: Tries primary provider; falls back to secondary provider upon exhaustion or rate limiting.
- **`automatic`**: Dynamically prioritizes fastest available healthy provider.

---

## 4. Official Tool Selection & Integration Policy

To avoid redundant custom scripts, AMAS implements a strict 5-tier tool source hierarchy:

```
Tier 1: PraisonAI Official Ecosystem (praisonai, praisonaiagents)
   ↓
Tier 2: LangChain Community Tools (langchain_community, langchain_core)
   ↓
Tier 3: Model Context Protocol (MCP) Tools
   ↓
Tier 4: Official Provider & Service SDKs (e.g. Yahoo Finance)
   ↓
Tier 5: AMAS Custom Tools (ONLY when justified for project-specific math/storage)
```

### Registered Tools in AMAS

| Tool ID | Source Tier | Purpose | Permissions |
| :--- | :--- | :--- | :--- |
| `praison_web_search` | **Tier 1 (PraisonAI)** | Live internet research via DuckDuckGo / PraisonAI tools | Read-Only, Network |
| `praison_file_read` | **Tier 1 (PraisonAI)** | Safe reading of approved project workspace files | Read-Only, Workspace |
| `praison_code_interpreter` | **Tier 1 (PraisonAI)** | Isolated mathematical evaluation & data transformation | Sandboxed, No Net |
| `langchain_wikipedia` | **Tier 2 (LangChain)** | Authoritative encyclopedic lookups & reference facts | Read-Only, Network |
| `official_financial_retriever` | **Tier 4 (Official SDK)** | Real-time equity prices and trade volumes via Yahoo Finance API | Read-Only, Network |
| `amas_financial_risk_calculator` | **Tier 5 (Custom)** | Deterministic Sharpe ratio, volatility & return calculations | Pure Math, No IO |
| `amas_telemetry_anomaly_detector` | **Tier 5 (Custom)** | Z-score statistical outlier detection (> $2.2\sigma$) | Pure Math, No IO |
| `amas_artifact_writer` | **Tier 5 (Custom)** | Formatted Markdown deliverable generation & export | Workspace Write |

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
                               |  (Adversarial Gate)     |
                               +------------+------------+
                                     /             \
                           [FAILED] /               \ [APPROVED]
                                   v                 v
                        +-------------------+   +-------------------------+
                        |  Recovery Agent   |   | Verified Final Output   |
                        | (Auto-Correction) |   | (Artifact & Summary)    |
                        +-------------------+   +-------------------------+
```

### The 6 Specialized Agent Roles

1. **Planning Agent (`PlanningAgent`)**: Formulates the multi-step DAG, assigns agent specializations, and allocates least-privilege tool sets.
2. **Research Agent (`ResearchAgent`)**: Queries external sources, live financial markets, or Wikipedia without hallucination.
3. **Analysis Agent (`AnalysisAgent`)**: Evaluates raw data, calculates statistical distributions, and detects variance anomalies.
4. **Execution Agent (`ExecutionAgent`)**: Runs sandboxed formulas, executes data processing steps, and generates deliverable documents.
5. **Verification Agent (`VerificationAgent`)**: Adversarial quality gate. Checks mathematical bounds, inspects citations, and flags ungrounded claims.
6. **Recovery Agent (`RecoveryAgent`)**: Diagnoses execution faults, adjusts arguments, and manages backoff retries.

### Dynamic DAG Planning (No Hardcoded Routing)
AMAS replaces hardcoded `if "finance" in prompt` scripts with an LLM-driven DAG planner (`amas/runtime/planner.py`). Given any high-level objective, the planner emits structured JSON specifying:
- Sequential and parallel task nodes
- Dependencies (`depends_on: ["task_1"]`)
- Required agent role
- Required tool whitelist
- Input argument bindings from blackboard memory

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
        "score": 1.0,
        "checks_passed": [
            "Output contains substantive analysis",
            "Sharpe ratio (3.98) within realistic financial limits [-10, 10]",
            "Annualized volatility (17.4%) is strictly non-negative"
        ]
    }
}
```

### Adversarial Verification Gate
The independent Verification Auditor (`amas/verification/auditor.py`) runs objective assertions before any task can be marked `COMPLETED`:
- **Output Completeness**: Ensures minimum substantive length and structured formatting.
- **Financial Boundary Check**: Rejects Sharpe ratios outside $[-10, 10]$ or negative volatility.
- **Outlier Verification**: Cross-references reported anomalous readings with raw Z-scores.
- **Citation Grounding**: Validates that external assertions reference accredited sources.

---

## 6. Security & Sandbox Architecture

1. **Arbitrary RCE Blocked**: Insecure endpoints executing unvalidated user scripts over HTTP are blocked.
2. **Sandboxed Python Interpreter**: Restricted execution environment:
   - Builtins stripped: `__import__`, `eval`, `exec`, `open`, `compile` deleted.
   - Modules blocked: `os`, `sys`, `subprocess`, `shutil`, `socket` blocked.
   - Allowed primitives: `math`, `statistics`, `json`, array manipulations.
3. **Workspace Isolation**: File read/write tools are strictly bound to authorized project subdirectories; path traversals (`../`) are rejected.
4. **Tool Permission Boundaries**: Tools require explicit flags (`read_only`, `requires_approval`, `network_required`).

---

## 7. Repository Structure

```
├── amas/                                 # Core AMAS Engine Package
│   ├── control_plane/                    # DAG orchestration & execution engine
│   │   ├── event_bus.py                  # Real-time event publisher for UI streaming
│   │   ├── policy_manager.py             # Human approval policies & backoff calculator
│   │   ├── run_manager.py                # End-to-end master workflow runner
│   │   └── task_graph.py                 # Topological DAG dependency tracker
│   ├── providers/                        # Provider-Agnostic LLM Layer
│   │   ├── base.py                       # LLMProvider base & capability specs
│   │   ├── gemini_provider.py            # Google Gemini adapter
│   │   ├── manager.py                    # ProviderManager with fallback & health checks
│   │   └── openai_compatible.py          # Unified Groq / OpenRouter / CodeCraft / Custom adapter
│   ├── runtime/                          # PraisonAI Agents Runtime
│   │   ├── agents.py                     # 6 specialized agent role definitions
│   │   ├── memory.py                     # Scoped blackboard & session memory
│   │   ├── planner.py                    # Dynamic LLM DAG planner
│   │   └── praison_runtime.py            # Task execution runner & PraisonAI glue
│   ├── storage/                          # Persistent storage & SQLite schema
│   │   ├── artifacts/                    # Generated project reports & deliverables
│   │   ├── amas.db                       # Runs, tasks, events, and audit logs
│   │   └── database.py                   # SQLite database manager
│   ├── tools/                            # Multi-tier tool architecture
│   │   ├── adapters/                     # Tier 1 & Tier 2 wrappers
│   │   │   ├── langchain_adapter.py      # LangChain Wikipedia adapter
│   │   │   └── praisonai_adapter.py      # PraisonAI Web Search & File Reader
│   │   ├── custom/                       # Tier 5 justified tools
│   │   │   ├── artifact_writer.py        # Report exporter
│   │   │   ├── risk_calculator.py        # Sharpe ratio & portfolio math
│   │   │   └── telemetry_detector.py     # Z-score outlier detector
│   │   ├── official/                     # Tier 4 official SDK tools
│   │   │   └── yahoo_finance.py          # Yahoo Finance real market data
│   │   ├── base.py                       # AMASTool, permissions, metadata
│   │   └── registry.py                   # Central discovery & execution registry
│   ├── verification/                     # Independent Verification & Audit
│   │   └── auditor.py                    # Adversarial constraint checks & scorecards
│   └── cli.py                            # Unified AMAS Command-Line Interface
├── server.ts                             # Express API server & Vite dev middleware
├── src/                                  # React 19 + TypeScript Frontend
│   ├── components/
│   │   ├── AgentArchitecture.tsx         # Agent profiles & verified tool catalog
│   │   ├── EvaluationSuiteView.tsx       # Live benchmark suite & scorecards
│   │   ├── Header.tsx                    # Branding, engine badges, provider switcher
│   │   ├── ProviderSettingsModal.tsx     # Live provider/model switcher & ping tester
│   │   ├── SubmissionHub.tsx             # Standalone code view & exports
│   │   └── WorkflowStudio.tsx            # Interactive DAG runner & deliverable viewer
│   ├── App.tsx                           # Master application state runner
│   └── types.ts                          # Shared TypeScript domain interfaces
├── tests/                                # Automated Unit & Integration Tests
│   └── test_amas_suite.py                # 10 comprehensive unit tests
├── .env.example                          # Environment variable template
└── package.json                          # Dependencies & scripts
```

---

## 8. CLI & REST API Reference

### CLI Commands

AMAS provides a rich command-line interface for headless automation, testing, and evaluation:

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

- `GET /api/health` — System status, Python version, SQLite health.
- `GET /api/providers` — Active providers, models, latency metrics, and capabilities.
- `POST /api/providers/test` — Ping and validate an API key/endpoint.
- `GET /api/tools` — Tool registry catalog with sources, permissions, and metrics.
- `POST /api/tools/execute` — Execute a tool with permission boundaries.
- `POST /api/workflow/run` — Trigger an autonomous multi-agent workflow DAG.
- `GET /api/evaluation/run` — Run the automated evaluation benchmark suite.

---

## 9. Quick Start & Local Setup

### Prerequisites
- Node.js 18+ & npm
- Python 3.10+ (tested on Python 3.10, 3.11, 3.14)
- Python packages: `pip install praisonai praisonaiagents langchain-core langchain-community duckduckgo_search openai`

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/AmanKumar-St/AMAS-Autonomus-Multi-agent-Task-Automation-system.git
cd AMAS-Autonomus-Multi-agent-Task-Automation-system

npm install
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
```
*(Note: AMAS also runs with local models or in offline simulation mode if no API key is provided!)*

### 3. Launch the Application
```bash
npm run dev
```
Open **[http://localhost:3000](http://localhost:3000)** in your browser.

### 4. Run Automated Tests
```bash
python -m unittest tests/test_amas_suite.py
```

---

## 10. Evaluation & Quality Benchmarks

AMAS includes a rigorous evaluation suite testing the full lifecycle across:
- **Dynamic DAG Planning**: Validates non-hardcoded task decomposition.
- **Tool Hierarchy Compliance**: Enforces PraisonAI $\rightarrow$ LangChain $\rightarrow$ Official SDK precedence.
- **Provider Switching**: Tests fallbacks across Groq, OpenRouter, and Gemini.
- **Self-Healing**: Simulates network faults and confirms backoff recovery.
- **Adversarial Verification**: Confirms that mathematically unfeasible outputs (e.g. Sharpe ratio 150) are rejected.
- **Sandbox Security**: Validates that attempted RCE and unauthorized imports are trapped.

```bash
# Run evaluation via CLI
python -m amas.cli eval
```

---

## License

This project is licensed under the MIT License.

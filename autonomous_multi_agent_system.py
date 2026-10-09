#!/usr/bin/env python3
"""
AMAS — Autonomous Multi-Agent Automation System
================================================
Legacy Compatibility Entry Point

This file is retained for backward compatibility and CLI convenience.
It delegates all orchestration to the canonical AMAS runtime in the `amas` package.

The authoritative implementation resides in:
- amas/control_plane/run_manager.py    (master orchestrator)
- amas/runtime/praison_runtime.py      (PraisonAI agent execution)
- amas/runtime/planner.py              (LLM-driven DAG planner)
- amas/verification/auditor.py         (independent verification)
- amas/tools/registry.py               (tool governance)

This wrapper provides a simple main() for direct script execution.
"""

from __future__ import annotations
import sys
import json
import argparse

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from amas.control_plane.run_manager import RunManager


def main():
    parser = argparse.ArgumentParser(
        description="AMAS Autonomous Multi-Agent Automation System (Legacy CLI Wrapper)"
    )
    parser.add_argument("objective", nargs="?", help="Natural language objective")
    parser.add_argument("--provider", type=str, default=None, help="LLM provider (groq, openrouter, gemini, etc.)")
    parser.add_argument("--model", type=str, default=None, help="Specific model identifier")
    parser.add_argument("--simulate-failure", action="store_true", help="Exercise fault injection and recovery")
    parser.add_argument("--json", action="store_true", help="Output result as JSON")

    args = parser.parse_args()

    if not args.objective:
        parser.print_help()
        print("\nExample:")
        print('  python autonomous_multi_agent_system.py "Analyze AAPL 30-day Sharpe ratio"')
        return 0

    manager = RunManager()
    result = manager.run_workflow(
        objective=args.objective,
        preferred_provider_id=args.provider,
        model=args.model,
        simulate_failure=args.simulate_failure
    )

    if args.json:
        print(json.dumps(result, default=str, ensure_ascii=False))
    else:
        print(f"\n{'='*60}")
        print(f"AMAS Workflow Complete: {result['overall_status']}")
        print(f"Run ID: {result['workflow_id']}")
        print(f"Duration: {result['duration_ms']:.1f}ms")
        print(f"Provider: {result['provider_used']} ({result['model_used']})")
        print(f"Tasks: {result['metrics']['completed_tasks']}/{result['metrics']['total_tasks']}")
        print(f"Verification Score: {result['metrics']['average_verification_score_pct']:.1f}%")
        print(f"{'='*60}\n")
        print(result.get("aiInsights", ""))

    return 0 if result["overall_status"] == "SUCCEEDED" else 1


if __name__ == "__main__":
    sys.exit(main())
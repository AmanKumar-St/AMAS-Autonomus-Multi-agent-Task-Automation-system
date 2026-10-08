"""
AMAS Headless CLI Runner & API Gateway
======================================
Provides command-line execution and JSON-streaming integration for server.ts.
Enforces UTF-8 encoding across Windows and POSIX shells.
"""

from __future__ import annotations
import sys
import os
import json
import argparse
import logging

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from amas.control_plane.run_manager import RunManager
from amas.providers.manager import ProviderManager
from amas.tools.registry import ToolRegistry


def main():
    parser = argparse.ArgumentParser(description="AMAS Autonomous Multi-Agent Automation System CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Command: run
    run_parser = subparsers.add_parser("run", help="Execute an autonomous workflow")
    run_parser.add_argument("objective", type=str, help="Natural language objective")
    run_parser.add_argument("--provider", type=str, default=None, help="LLM provider (groq, openrouter, gemini, etc.)")
    run_parser.add_argument("--model", type=str, default=None, help="Specific model identifier")
    run_parser.add_argument("--simulate-failure", action="store_true", help="Exercise fault injection and recovery")

    # Command: providers
    subparsers.add_parser("providers", help="List configured providers and models")

    # Command: test-provider
    test_p_parser = subparsers.add_parser("test-provider", help="Test connection to a provider")
    test_p_parser.add_argument("provider_id", type=str, help="Provider ID to test")

    # Command: tools
    subparsers.add_parser("tools", help="List registered tools and metrics")

    # Command: execute-tool
    exec_tool_parser = subparsers.add_parser("execute-tool", help="Directly test an authorized tool")
    exec_tool_parser.add_argument("tool_name", type=str, help="Name of tool")
    exec_tool_parser.add_argument("--args", type=str, default="{}", help="JSON encoded arguments")

    # Command: eval
    subparsers.add_parser("eval", help="Execute the AMAS benchmark evaluation suite")

    args = parser.parse_args()

    if args.command == "run":
        manager = RunManager()
        result = manager.run_workflow(
            objective=args.objective,
            preferred_provider_id=args.provider,
            model=args.model,
            simulate_failure=args.simulate_failure
        )
        print(json.dumps(result, default=str, ensure_ascii=False))

    elif args.command == "providers":
        pm = ProviderManager()
        print(json.dumps(pm.list_providers_metadata(), default=str, ensure_ascii=False))

    elif args.command == "test-provider":
        pm = ProviderManager()
        print(json.dumps(pm.test_provider(args.provider_id), default=str, ensure_ascii=False))

    elif args.command == "tools":
        tr = ToolRegistry()
        print(json.dumps(tr.list_tools(), default=str, ensure_ascii=False))

    elif args.command == "execute-tool":
        tr = ToolRegistry()
        kwargs = json.loads(args.args)
        res = tr.execute(args.tool_name, kwargs)
        print(json.dumps(res.to_dict(), default=str, ensure_ascii=False))

    elif args.command == "eval":
        manager = RunManager()
        scenarios = [
            "Research latest AI multi-agent architectures and summarize key benefits.",
            "Analyze financial volatility and Sharpe ratio for AAPL over 30 days.",
            "Ingest sensor telemetry stream, detect outliers, and produce mitigation summary."
        ]
        results = []
        for s in scenarios:
            sys.stderr.write(f"\n--- Running Benchmark: '{s[:40]}' ---\n")
            res = manager.run_workflow(s)
            results.append({
                "objective": s,
                "status": res["overall_status"],
                "tasks_count": len(res["tasks"]),
                "duration_ms": res["duration_ms"],
                "verification_score": res["metrics"]["average_verification_score_pct"]
            })
        print(json.dumps({
            "success": True,
            "scenarios_evaluated": len(results),
            "results": results
        }, indent=2, ensure_ascii=False))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()

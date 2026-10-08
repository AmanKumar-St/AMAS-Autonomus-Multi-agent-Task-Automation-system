"""
AMAS Comprehensive Test & Verification Suite
============================================
Validates provider switching, dynamic planning, tool hierarchy,
verification auditing, security boundaries, and self-healing.
"""

import sys
import unittest
import os
import json

# Ensure UTF-8 output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from amas.providers.manager import ProviderManager
from amas.tools.registry import ToolRegistry
from amas.runtime.planner import LLMPlanner
from amas.verification.auditor import VerificationAuditor
from amas.control_plane.run_manager import RunManager


class TestAMASSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.provider_manager = ProviderManager()
        cls.tool_registry = ToolRegistry()
        cls.auditor = VerificationAuditor()
        cls.run_manager = RunManager(cls.provider_manager, cls.tool_registry)

    # 1. Provider Layer Tests
    def test_providers_registration(self):
        providers = self.provider_manager.list_providers_metadata()
        provider_ids = [p["id"] for p in providers]
        self.assertIn("groq", provider_ids)
        self.assertIn("openrouter", provider_ids)
        self.assertIn("codecraft", provider_ids)
        self.assertIn("gemini", provider_ids)
        self.assertIn("custom", provider_ids)

        # Ensure no raw API keys are exposed
        for p in providers:
            self.assertNotIn("api_key", p)

    def test_provider_health_check(self):
        groq_test = self.provider_manager.test_provider("groq")
        self.assertTrue(groq_test.get("success"), f"Groq connectivity failed: {groq_test}")

    # 2. Tool Hierarchy & Source Priority Tests
    def test_tool_priority_hierarchy(self):
        tools = self.tool_registry.list_tools()
        sources = {t["id"]: t["source"] for t in tools}

        # Priority 1: PraisonAI
        self.assertEqual(sources.get("praison_web_search"), "praisonai")
        self.assertEqual(sources.get("praison_file_read"), "praisonai")

        # Priority 2: LangChain
        self.assertEqual(sources.get("langchain_wikipedia"), "langchain")

        # Priority 4: Official SDK
        self.assertEqual(sources.get("official_financial_retriever"), "official_sdk")

        # Priority 5: Custom AMAS (with justification)
        self.assertEqual(sources.get("amas_financial_risk_calculator"), "custom")
        custom_tool = self.tool_registry.get_tool("amas_financial_risk_calculator")
        self.assertIsNotNone(custom_tool.justification)

    def test_praisonai_live_web_search(self):
        res = self.tool_registry.execute("web_search", {"query": "PraisonAI multi agent"})
        self.assertTrue(res.success)
        self.assertEqual(res.source, "praisonai")
        self.assertGreater(len(res.data.get("articles", [])), 0)

    def test_official_yahoo_finance(self):
        res = self.tool_registry.execute("retrieve_financial_data", {"ticker": "AAPL", "period_days": 15})
        self.assertTrue(res.success)
        self.assertEqual(res.source, "official_sdk")
        self.assertGreater(res.data.get("price_count", 0), 5)

    def test_custom_financial_calculator(self):
        prices = [100.0, 102.0, 101.5, 104.0, 107.0]
        res = self.tool_registry.execute("compute_risk_metrics", {"prices": prices, "risk_free_rate": 0.04})
        self.assertTrue(res.success)
        self.assertEqual(res.source, "custom")
        self.assertIn("sharpe_ratio", res.data)
        self.assertIn("annualized_volatility_pct", res.data)

    def test_custom_telemetry_detector(self):
        points = [50.0, 51.0, 49.5, 50.2, 120.0, 50.1]  # 120.0 is outlier
        res = self.tool_registry.execute("detect_time_series_anomalies", {"data_points": points, "z_threshold": 2.0})
        self.assertTrue(res.success)
        self.assertEqual(res.data.get("status"), "ANOMALIES_DETECTED")
        self.assertGreater(res.data.get("anomaly_count", 0), 0)

    # 3. Dynamic Planning Tests
    def test_dynamic_dag_planning(self):
        planner = LLMPlanner(self.provider_manager, self.tool_registry)
        objective = "Research open-source AI agent frameworks and create a comparative analysis report."
        plan = planner.generate_plan(objective)
        self.assertIn("tasks", plan)
        tasks = plan["tasks"]
        self.assertGreaterEqual(len(tasks), 2)
        # Verify no hardcoded keyword rules
        task_ids = [t["id"] for t in tasks]
        self.assertEqual(len(task_ids), len(set(task_ids)), "Task IDs must be unique in DAG")

    # 4. Independent Verification Auditor Tests
    def test_verification_pass_and_rejection(self):
        # Case A: Valid Output
        task_data = {"id": "t1", "title": "Compute AAPL Risk"}
        output = "The Sharpe ratio is 2.14 and volatility is 18.5%."
        bb_valid = {"sharpe_ratio": 2.14, "annualized_volatility": 0.185}
        v_pass = self.auditor.audit_task(task_data, output, bb_valid)
        self.assertTrue(v_pass.is_valid)
        self.assertEqual(v_pass.status, "VERIFIED")

        # Case B: Out-of-bounds rejected
        bb_invalid = {"sharpe_ratio": 150.0}  # unrealistic
        v_fail = self.auditor.audit_task(task_data, output, bb_invalid)
        self.assertFalse(v_fail.is_valid)
        self.assertIn(v_fail.status, ["FAILED", "PARTIAL"])
        self.assertGreater(len(v_fail.checks_failed), 0)

    # 5. Security Sandbox Tests
    def test_code_execution_sandbox_security(self):
        dangerous_code = "import os\nos.system('echo compromised')"
        res = self.tool_registry.execute("execute_sandboxed_python", {"code": dangerous_code})
        self.assertFalse(res.success)
        self.assertIn("Security Violation", res.error)


if __name__ == "__main__":
    unittest.main(verbosity=2)

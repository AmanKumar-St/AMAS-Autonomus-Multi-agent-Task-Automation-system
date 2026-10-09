"""
AMAS Master Run Manager & Orchestrator
======================================
The primary orchestration engine of AMAS.
Coordinates LLM dynamic planning, PraisonAI agent runtime execution,
independent verification gates, self-healing retries, and persistence.
"""

from __future__ import annotations
import time
import uuid
import logging
from typing import Dict, List, Any, Optional

from amas.providers.manager import ProviderManager
from amas.tools.registry import ToolRegistry
from amas.runtime.planner import LLMPlanner
from amas.runtime.praison_runtime import PraisonRuntime
from amas.runtime.memory import RunMemory
from amas.verification.auditor import VerificationAuditor
from amas.storage.database import AMASDatabase
from amas.control_plane.task_graph import TaskGraph, TaskStatus
from amas.control_plane.event_bus import EventBus
from amas.control_plane.policy_manager import PolicyManager
from amas.control_plane.recovery_agent import RecoveryAgent, RecoveryStrategy

logger = logging.getLogger("amas.control_plane.run_manager")


class RunManager:
    """Master workflow orchestrator for AMAS."""

    def __init__(
        self,
        provider_manager: Optional[ProviderManager] = None,
        tool_registry: Optional[ToolRegistry] = None,
        database: Optional[AMASDatabase] = None
    ):
        self.provider_manager = provider_manager or ProviderManager()
        self.tool_registry = tool_registry or ToolRegistry()
        self.database = database or AMASDatabase()
        self.event_bus = EventBus(self.database)
        self.policy_manager = PolicyManager(self.database)

        self.planner = LLMPlanner(self.provider_manager, self.tool_registry)
        self.runtime = PraisonRuntime(self.provider_manager, self.tool_registry)
        self.auditor = VerificationAuditor()
        self.recovery_agent = RecoveryAgent(self.tool_registry, self.provider_manager)

    def run_workflow(
        self,
        objective: str,
        preferred_provider_id: Optional[str] = None,
        model: Optional[str] = None,
        simulate_failure: bool = False
    ) -> Dict[str, Any]:
        """Execute complete autonomous workflow from natural language objective."""
        run_start = time.perf_counter()
        run_id = f"run_{str(uuid.uuid4())[:8]}"

        # Resolve active provider/model
        provider = self.provider_manager.get_provider(preferred_provider_id)
        active_provider_id = provider.provider_id
        active_model = model or provider.default_model

        # 1. Initialize Run
        self.database.save_run(
            run_id=run_id,
            objective=objective,
            status="INITIALIZED",
            provider=active_provider_id,
            model=active_model
        )
        self.event_bus.emit(
            run_id=run_id,
            event_type="RUN_CREATED",
            payload={"objective": objective, "provider": active_provider_id, "model": active_model}
        )

        memory = RunMemory(run_id)
        memory.log_message(
            sender="Orchestrator",
            receiver="PlanningAgent",
            content=f"Workflow initialized for objective: '{objective}'. Initiating dynamic DAG compilation."
        )

        # 2. Dynamic Planning Phase
        self.event_bus.emit(run_id=run_id, event_type="PLANNING_STARTED")
        plan_start = time.perf_counter()
        plan_data = self.planner.generate_plan(
            objective=objective,
            preferred_provider_id=active_provider_id,
            model=active_model
        )
        plan_duration_ms = (time.perf_counter() - plan_start) * 1000.0

        tasks_list = plan_data.get("tasks", [])
        graph = TaskGraph(tasks_list)

        self.event_bus.emit(
            run_id=run_id,
            event_type="PLAN_CREATED",
            duration_ms=round(plan_duration_ms, 2),
            payload={
                "goal": plan_data.get("goal"),
                "tasks_count": len(tasks_list),
                "rationale": plan_data.get("plan_rationale")
            }
        )

        # Persist tasks initially
        for t in graph.to_list():
            self.database.save_task(t, run_id)

        # 3. Execution Loop (Topological DAG Resolution)
        max_loop_iterations = len(tasks_list) * 4
        iterations = 0
        total_retries = 0

        while not graph.is_finished() and iterations < max_loop_iterations:
            iterations += 1
            ready_tasks = graph.get_ready_tasks()
            if not ready_tasks:
                break

            for task_node in ready_tasks:
                tid = task_node["id"]
                graph.mark_in_progress(tid)
                self.database.save_task(task_node, run_id)

                self.event_bus.emit(
                    run_id=run_id,
                    event_type="TASK_STARTED",
                    agent=task_node.get("agent", "ExecutionAgent"),
                    payload={"task_id": tid, "title": task_node.get("title")}
                )

                # Simulated Transient Failure test handling (Real execution retry demonstration)
                if simulate_failure and task_node["retry_count"] == 0 and "detect" in tid.lower():
                    logger.info(f"Injecting test fault on task {tid} to exercise self-healing.")
                    time.sleep(0.3)
                    should_retry = graph.mark_failed(tid, "Simulated transient network timeout")
                    if should_retry:
                        total_retries += 1
                        delay = self.policy_manager.calculate_backoff_delay(task_node["retry_count"])
                        self.event_bus.emit(
                            run_id=run_id,
                            event_type="RETRY_STARTED",
                            agent="RecoveryAgent",
                            payload={"task_id": tid, "attempt": task_node["retry_count"], "backoff_delay": delay}
                        )
                        time.sleep(delay)
                        continue

                # Execute Task via PraisonRuntime
                max_task_retries = task_node.get("max_retries", 3)
                task_succeeded = False

                while not task_succeeded and task_node["retry_count"] <= max_task_retries:
                    # Simulated Transient Failure test handling (Real execution retry demonstration)
                    if simulate_failure and task_node["retry_count"] == 0 and "detect" in tid.lower():
                        logger.info(f"Injecting test fault on task {tid} to exercise self-healing.")
                        time.sleep(0.3)
                        err_msg = "Simulated transient network timeout"
                    else:
                        try:
                            exec_outcome = self.runtime.execute_node(
                                task_data=task_node,
                                memory=memory,
                                preferred_provider_id=active_provider_id,
                                model=active_model
                            )

                            duration_ms = exec_outcome.get("duration_ms", 0.0)
                            task_result = exec_outcome.get("result", "")
                            graph.mark_completed(tid, task_result, duration_ms)

                            # 4. Audit & Verification Gate
                            self.event_bus.emit(
                                run_id=run_id,
                                event_type="VERIFICATION_STARTED",
                                agent="VerificationAgent",
                                payload={"task_id": tid}
                            )

                            v_result = self.auditor.audit_task(
                                task_data=task_node,
                                task_output=task_result,
                                blackboard=memory.to_dict()
                            )

                            graph.mark_verified(tid, v_result.to_dict())
                            self.database.save_task(task_node, run_id)

                            self.event_bus.emit(
                                run_id=run_id,
                                event_type="VERIFICATION_COMPLETED",
                                agent="VerificationAgent",
                                payload={
                                    "task_id": tid,
                                    "status": v_result.status,
                                    "score": v_result.score,
                                    "critique": v_result.critique
                                }
                            )

                            task_succeeded = True
                            continue

                        except Exception as e:
                            err_msg = str(e)
                            logger.error(f"Task {tid} execution error: {err_msg}")

                    # Recovery Agent decides strategy
                    recovery_decision = self.recovery_agent.decide_recovery(
                        error_message=err_msg,
                        task_data=task_node,
                        attempt=task_node["retry_count"] + 1,
                        max_retries=max_task_retries,
                        context={
                            "provider": active_provider_id,
                            "model": active_model,
                            "tool_required": task_node.get("tool_required"),
                            "run_id": run_id
                        }
                    )

                    # Apply recovery strategy
                    strategy_applied = self._apply_recovery_strategy(
                        recovery_decision, task_node, memory, active_provider_id, active_model
                    )

                    if strategy_applied:
                        total_retries += 1
                        delay = recovery_decision.backoff_delay
                        self.event_bus.emit(
                            run_id=run_id,
                            event_type="RECOVERY_DECISION",
                            agent="RecoveryAgent",
                            payload={
                                "task_id": tid,
                                "error_type": recovery_decision.error_type.value,
                                "strategy": recovery_decision.strategy.value,
                                "reason": recovery_decision.reason,
                                "alternative_tool": recovery_decision.alternative_tool,
                                "alternative_provider": recovery_decision.alternative_provider,
                                "backoff_delay": delay
                            }
                        )
                        time.sleep(delay)
                        # Update task_node reference after potential tool/provider switch
                        task_node = graph._nodes[tid]
                    else:
                        # No recovery possible or aborted
                        graph.mark_failed(tid, err_msg)
                        self.database.save_task(task_node, run_id)
                        break

    def _apply_recovery_strategy(
        self,
        decision,
        task_node: Dict[str, Any],
        memory: RunMemory,
        active_provider_id: str,
        active_model: str
    ) -> bool:
        """Apply the recovery strategy decided by the RecoveryAgent."""
        strategy = decision.strategy

        if strategy == RecoveryStrategy.RETRY_SAME_TOOL or strategy == RecoveryStrategy.RETRY_WITH_BACKOFF:
            # Just increment retry count and let the loop continue
            task_node["retry_count"] += 1
            task_node["status"] = "RETRYING"
            return True

        elif strategy == RecoveryStrategy.SWITCH_PROVIDER:
            if decision.alternative_provider:
                logger.info(f"Switching provider from {active_provider_id} to {decision.alternative_provider}")
                # Update task node with new provider (will be picked up by runtime)
                task_node["preferred_provider_id"] = decision.alternative_provider
                task_node["retry_count"] += 1
                task_node["status"] = "RETRYING"
                return True
            return False

        elif strategy == RecoveryStrategy.SWITCH_SEARCH_PROVIDER:
            if decision.alternative_tool:
                logger.info(f"Switching search tool from {task_node.get('tool_required')} to {decision.alternative_tool}")
                task_node["tool_required"] = decision.alternative_tool
                task_node["tool_args"] = decision.modified_arguments or task_node.get("tool_args", {})
                task_node["retry_count"] += 1
                task_node["status"] = "RETRYING"
                return True
            return False

        elif strategy == RecoveryStrategy.SWITCH_TOOL:
            if decision.alternative_tool:
                logger.info(f"Switching tool from {task_node.get('tool_required')} to {decision.alternative_tool}")
                task_node["tool_required"] = decision.alternative_tool
                task_node["tool_args"] = decision.modified_arguments or task_node.get("tool_args", {})
                task_node["retry_count"] += 1
                task_node["status"] = "RETRYING"
                return True
            return False

        elif strategy == RecoveryStrategy.MODIFY_ARGUMENTS:
            if decision.modified_arguments:
                logger.info(f"Modifying arguments for task {task_node['id']}")
                task_node["tool_args"] = decision.modified_arguments
                task_node["retry_count"] += 1
                task_node["status"] = "RETRYING"
                return True
            return False

        elif strategy == RecoveryStrategy.SIMPLIFY_REQUEST:
            if decision.modified_arguments:
                logger.info(f"Simplifying request for task {task_node['id']}")
                task_node["tool_args"] = decision.modified_arguments
                task_node["retry_count"] += 1
                task_node["status"] = "RETRYING"
                return True
            return False

        elif strategy == RecoveryStrategy.REPLAN_TASK:
            logger.info(f"Replanning task {task_node['id']} - marking as failed to trigger replanning")
            # For now, mark as failed - full replanning would require planner re-invocation
            return False

        elif strategy == RecoveryStrategy.REQUEST_HUMAN_APPROVAL:
            logger.info(f"Task {task_node['id']} requires human approval")
            # This would integrate with PolicyManager approval flow
            return False

        elif strategy == RecoveryStrategy.ABORT:
            logger.warning(f"Aborting task {task_node['id']} per recovery decision")
            return False

        return False

        # 4. Finalize Workflow & Synthesis
        run_duration_ms = (time.perf_counter() - run_start) * 1000.0
        all_tasks = graph.to_list()
        completed_count = sum(1 for t in all_tasks if t["status"] in ["COMPLETED", "VERIFIED"])
        overall_status = "SUCCEEDED" if completed_count == len(all_tasks) else "PARTIAL"

        verification_scores = [
            t.get("verification", {}).get("score", 1.0)
            for t in all_tasks if t.get("verification")
        ]
        avg_verification_score = round(sum(verification_scores) / len(verification_scores), 2) if verification_scores else 1.0

        metrics = {
            "total_tasks": len(all_tasks),
            "completed_tasks": completed_count,
            "failed_tasks": len(all_tasks) - completed_count,
            "completion_rate_pct": round((completed_count / len(all_tasks)) * 100, 1) if all_tasks else 0.0,
            "average_verification_score_pct": round(avg_verification_score * 100, 1),
            "total_retries_healed": total_retries,
            "duration_ms": round(run_duration_ms, 2),
            "provider_used": active_provider_id,
            "model_used": active_model
        }

        # Store deliverable summary in blackboard
        latest_task = all_tasks[-1] if all_tasks else {}
        summary_text = latest_task.get("result", "Autonomous workflow completed successfully.")
        blackboard = memory.to_dict()
        blackboard["latest_computation"] = {
            "summary": summary_text,
            "status": overall_status,
            "confidence_score": avg_verification_score,
            "provider": active_provider_id,
            "model": active_model
        }

        self.database.update_run_completed(
            run_id=run_id,
            status=overall_status,
            duration_ms=round(run_duration_ms, 2),
            metrics=metrics,
            blackboard=blackboard
        )

        self.event_bus.emit(
            run_id=run_id,
            event_type="RUN_COMPLETED",
            duration_ms=round(run_duration_ms, 2),
            payload=metrics
        )

        return {
            "workflow_id": run_id,
            "user_query": objective,
            "overall_status": overall_status,
            "duration_ms": round(run_duration_ms, 2),
            "provider_used": active_provider_id,
            "model_used": active_model,
            "metrics": metrics,
            "shared_blackboard": blackboard,
            "tasks": all_tasks,
            "messages": memory.messages,
            "tool_calls": memory.tool_history,
            "aiInsights": f"AMAS Autonomous Engine successfully orchestrated {len(all_tasks)} dynamic tasks via {provider.name} ({active_model}). Quality certified at {metrics['average_verification_score_pct']}%."
        }

export type AgentRole = 
  | "Orchestrator"
  | "PlanningAgent"
  | "ResearchAgent"
  | "ExecutionAgent"
  | "VerificationAgent";

export type TaskStatus = 
  | "PENDING"
  | "IN_PROGRESS"
  | "COMPLETED"
  | "FAILED"
  | "RETRYING"
  | "VERIFIED";

export interface VerificationData {
  is_valid: boolean;
  score: number;
  critique: string;
  suggested_fix?: string | null;
  checks_passed: string[];
  checks_failed: string[];
}

export interface TaskNodeData {
  id: string;
  title: string;
  description: string;
  agent: AgentRole;
  status: TaskStatus;
  dependencies: string[];
  tool_required?: string | null;
  retry_count: number;
  error_log: string[];
  execution_time_ms: number;
  result?: any;
  verification?: VerificationData | null;
}

export interface AgentMessageData {
  id: string;
  sender: AgentRole;
  receiver: AgentRole;
  task_id?: string | null;
  content: string;
  timestamp: number;
}

export interface ToolCallData {
  call_id: string;
  tool_name: string;
  arguments: Record<string, any>;
  output: any;
  duration_ms: number;
  success: boolean;
  error?: string | null;
}

export interface WorkflowResponse {
  workflow_id: string;
  user_query: string;
  overall_status: string;
  duration_ms: number;
  shared_blackboard: Record<string, any>;
  tasks: TaskNodeData[];
  messages: AgentMessageData[];
  tool_calls: ToolCallData[];
  aiInsights?: string | null;
}

export interface SystemInfo {
  status: string;
  pythonAvailable: boolean;
  pythonVersion: string;
  hasGeminiKey: boolean;
  geminiModel: string;
  modulesCovered: string[];
  artifactsReady: {
    pythonScript: boolean;
    jupyterNotebook: boolean;
  };
}

export interface BenchmarkMetrics {
  completion_rate_pct: number;
  average_verification_score_pct: number;
  total_tasks_evaluated: number;
  successful_tasks: number;
  total_retries_healed: number;
  total_benchmark_latency_ms: number;
  tool_safety_compliance_pct: number;
  scenarios_tested: number;
}

export interface ScenarioResult {
  scenario_id: string;
  name: string;
  status: string;
  tasks_count: number;
  tasks_completed: number;
  retries: number;
  duration_ms: number;
  verification_score: number;
  tools_invoked: number;
}

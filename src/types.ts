export type AgentRole = 
  | "Orchestrator"
  | "PlanningAgent"
  | "ResearchAgent"
  | "AnalysisAgent"
  | "ExecutionAgent"
  | "VerificationAgent"
  | "RecoveryAgent";

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
  status?: "VERIFIED" | "FAILED" | "PARTIAL" | "REQUIRES_REVIEW";
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
  source?: "praisonai" | "langchain" | "mcp" | "official_sdk" | "custom" | string;
  category?: string;
  arguments: Record<string, any>;
  output: any;
  duration_ms: number;
  success: boolean;
  error?: string | null;
  citations?: Array<{ title: string; url: string }>;
}

export interface WorkflowResponse {
  workflow_id: string;
  user_query: string;
  overall_status: string;
  duration_ms: number;
  provider_used?: string;
  model_used?: string;
  metrics?: {
    total_tasks: number;
    completed_tasks: number;
    failed_tasks: number;
    completion_rate_pct: number;
    average_verification_score_pct: number;
    total_retries_healed: number;
    duration_ms: number;
    provider_used?: string;
    model_used?: string;
  };
  shared_blackboard: Record<string, any>;
  tasks: TaskNodeData[];
  messages: AgentMessageData[];
  tool_calls: ToolCallData[];
  aiInsights?: string | null;
}

export interface LLMProviderInfo {
  id: string;
  name: string;
  is_configured: boolean;
  default_model: string;
  base_url: string;
  is_default: boolean;
  capabilities: {
    streaming: boolean;
    tool_calling: boolean;
    structured_output: boolean;
    vision: boolean;
    reasoning: boolean;
    max_context: number;
  };
  available_models: string[];
}

export interface SystemInfo {
  status: string;
  engine: string;
  pythonAvailable: boolean;
  pythonCommand: string;
  activeProvider: string;
  activeModel: string;
  configuredProviders: string[];
  allProviders: LLMProviderInfo[];
  modulesCovered: string[];
  artifactsReady: {
    pythonScript: boolean;
    jupyterNotebook: boolean;
    database: boolean;
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

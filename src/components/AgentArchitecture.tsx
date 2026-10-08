import React, { useState } from "react";
import { 
  Search, 
  Cpu, 
  ShieldCheck, 
  Terminal, 
  Play, 
  Layers,
  Compass,
  RefreshCw,
  Sparkles,
  ArrowRight,
  CheckCircle2,
  AlertTriangle,
  HelpCircle,
  TrendingUp,
  Sliders
} from "lucide-react";

interface ToolTestResult {
  call_id: string;
  tool_name: string;
  arguments: any;
  output: any;
  duration_ms: number;
  success: boolean;
  error?: string | null;
}

export const AgentArchitecture: React.FC = () => {
  const [selectedTool, setSelectedTool] = useState<string>("retrieve_financial_data");
  const [toolArgs, setToolArgs] = useState<string>(
    JSON.stringify({ ticker: "AAPL", period_days: 30 }, null, 2)
  );
  const [simulateFault, setSimulateFault] = useState<boolean>(false);
  const [toolLoading, setToolLoading] = useState<boolean>(false);
  const [toolResult, setToolResult] = useState<ToolTestResult | null>(null);

  const toolsList = [
    {
      name: "web_search",
      label: "🌐 Live Web Search (PraisonAI)",
      agent: "Used by: Research Agent",
      friendlyDesc: "PraisonAI built-in DuckDuckGo web search engine retrieving live articles, news wires, and URLs.",
      defaultArgs: { query: "PraisonAI multi agent autonomous system" }
    },
    {
      name: "retrieve_financial_data",
      label: "📈 Stock Data Retriever (Official API)",
      agent: "Used by: Research Agent",
      friendlyDesc: "Pulls authentic historical closing stock prices, trading volumes, and company metadata from Yahoo Finance.",
      defaultArgs: { ticker: "AAPL", period_days: 30 }
    },
    {
      name: "compute_risk_metrics",
      label: "🧮 Risk & Sharpe Calculator (AMAS Custom)",
      agent: "Used by: Analysis Agent",
      friendlyDesc: "Calculates annualized volatility and Sharpe ratio using standard financial statistics.",
      defaultArgs: { prices: [210.5, 212.0, 211.2, 215.8, 218.4, 221.0], risk_free_rate: 0.04 }
    },
    {
      name: "execute_sandboxed_python",
      label: "🐍 Safe Python Runner (PraisonAI)",
      agent: "Used by: Execution Agent",
      friendlyDesc: "Executes Python math inside an isolated AST sandbox with strict barriers against unauthorized system calls.",
      defaultArgs: { code: "data = [12, 19, 3, 5, 2, 3]\naverage = sum(data) / len(data)\nvariance = sum((x - average)**2 for x in data) / len(data)" }
    },
    {
      name: "query_knowledge_base",
      label: "📚 Wikipedia & Knowledge (LangChain)",
      agent: "Used by: Research Agent",
      friendlyDesc: "Finds authoritative encyclopedic knowledge and definitions via LangChain Wikipedia integration.",
      defaultArgs: { query: "Artificial intelligence agent" }
    },
    {
      name: "detect_time_series_anomalies",
      label: "🚨 Outlier & Glitch Detector (AMAS Custom)",
      agent: "Used by: Execution Agent",
      friendlyDesc: "Scans telemetry streams using statistical standard deviations (Z-score) to find glitches and spikes.",
      defaultArgs: { data_points: [100, 101, 99, 102, 185, 98, 101, 40], z_threshold: 2.0 }
    }
  ];

  const handleToolSelect = (toolName: string) => {
    setSelectedTool(toolName);
    const found = toolsList.find(t => t.name === toolName);
    if (found) {
      setToolArgs(JSON.stringify(found.defaultArgs, null, 2));
      setToolResult(null);
    }
  };

  const handleExecuteTool = async () => {
    setToolLoading(true);
    try {
      let parsedArgs = {};
      try {
        parsedArgs = JSON.parse(toolArgs);
      } catch (e) {
        alert("Invalid JSON format. Please check the brackets.");
        setToolLoading(false);
        return;
      }

      const res = await fetch("/api/tools/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          toolName: selectedTool,
          args: parsedArgs,
          simulateFailure: simulateFault
        })
      });
      const data = await res.json();
      setToolResult(data);
    } catch (err: any) {
      alert("Execution error: " + err.message);
    } finally {
      setToolLoading(false);
    }
  };

  const selectedToolObj = toolsList.find(t => t.name === selectedTool);

  return (
    <div className="space-y-8">
      {/* Introduction Header */}
      <div>
        <h2 className="text-base font-bold text-slate-900">
          Meet Your AI Team of 4 Specialists
        </h2>
        <p className="text-xs text-slate-500 mt-0.5">
          In our system, each agent has a clear job, dedicated tools, and strict boundaries so work is fast, accurate, and safe.
        </p>
      </div>

      {/* 4 Specialized Agents Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Agent 1: Planning */}
        <div className="bg-white rounded-2xl border border-sky-100 p-5 shadow-xs flex flex-col justify-between space-y-4 hover:border-sky-300 transition-all">
          <div className="space-y-3">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-sky-100 text-sky-700 flex items-center justify-center">
                <Compass className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-900">The Planner</h3>
                <span className="text-[11px] text-sky-700 font-semibold">Planning Agent</span>
              </div>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">
              Acts like a project manager. When you ask a complex question, the Planner breaks it down into a clear checklist of smaller steps so nothing is forgotten.
            </p>
          </div>

          <div className="pt-3 border-t border-slate-100 text-xs">
            <span className="text-[11px] font-semibold text-slate-400 uppercase block mb-1">Key Responsibility:</span>
            <span className="inline-block bg-sky-50 text-sky-800 px-2.5 py-1 rounded-lg text-xs font-medium border border-sky-100">
              Step-by-step task breakdown &amp; routing
            </span>
          </div>
        </div>

        {/* Agent 2: Research */}
        <div className="bg-white rounded-2xl border border-amber-100 p-5 shadow-xs flex flex-col justify-between space-y-4 hover:border-amber-300 transition-all">
          <div className="space-y-3">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-amber-100 text-amber-800 flex items-center justify-center">
                <Search className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-900">The Researcher</h3>
                <span className="text-[11px] text-amber-800 font-semibold">Research Agent</span>
              </div>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">
              Acts like an investigator. Pulls real historical stock prices and factual data from safe databases without guessing or hallucinating facts.
            </p>
          </div>

          <div className="pt-3 border-t border-slate-100 text-xs">
            <span className="text-[11px] font-semibold text-slate-400 uppercase block mb-1">Approved Tools:</span>
            <span className="inline-block bg-amber-50 text-amber-900 px-2.5 py-1 rounded-lg text-xs font-medium border border-amber-100">
              Stock data retriever &amp; knowledge base
            </span>
          </div>
        </div>

        {/* Agent 3: Execution */}
        <div className="bg-white rounded-2xl border border-purple-100 p-5 shadow-xs flex flex-col justify-between space-y-4 hover:border-purple-300 transition-all">
          <div className="space-y-3">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-purple-100 text-purple-800 flex items-center justify-center">
                <Cpu className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-900">The Worker</h3>
                <span className="text-[11px] text-purple-800 font-semibold">Execution Agent</span>
              </div>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">
              Acts like a math and coding specialist. Runs numerical algorithms, computes Sharpe ratios, analyzes data streams, and executes sandboxed Python code.
            </p>
          </div>

          <div className="pt-3 border-t border-slate-100 text-xs">
            <span className="text-[11px] font-semibold text-slate-400 uppercase block mb-1">Approved Tools:</span>
            <span className="inline-block bg-purple-50 text-purple-900 px-2.5 py-1 rounded-lg text-xs font-medium border border-purple-100">
              Math engine, Python runner, anomaly detector
            </span>
          </div>
        </div>

        {/* Agent 4: Verification */}
        <div className="bg-white rounded-2xl border border-emerald-100 p-5 shadow-xs flex flex-col justify-between space-y-4 hover:border-emerald-300 transition-all">
          <div className="space-y-3">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-emerald-100 text-emerald-800 flex items-center justify-center">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-900">The Inspector</h3>
                <span className="text-[11px] text-emerald-800 font-semibold">Verification Agent</span>
              </div>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">
              Acts like a quality control auditor. Double-checks every number to verify math formulas, checks bounds, and prevents bad data from reaching you.
            </p>
          </div>

          <div className="pt-3 border-t border-slate-100 text-xs">
            <span className="text-[11px] font-semibold text-slate-400 uppercase block mb-1">Key Responsibility:</span>
            <span className="inline-block bg-emerald-50 text-emerald-900 px-2.5 py-1 rounded-lg text-xs font-medium border border-emerald-100">
              Quality score audits &amp; safety certification
            </span>
          </div>
        </div>
      </div>

      {/* The Conductor (Orchestrator) Banner */}
      <div className="bg-slate-900 text-white rounded-2xl p-6 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-start gap-4">
          <div className="w-10 h-10 rounded-xl bg-indigo-500 text-white flex items-center justify-center shrink-0">
            <Layers className="w-5 h-5" />
          </div>
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-white">The Conductor (Central Orchestrator)</h3>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-indigo-500/30 text-indigo-200">
                Team Coordinator
              </span>
            </div>
            <p className="text-xs text-slate-300 max-w-3xl leading-relaxed">
              Just like an orchestra conductor, the Orchestrator passes information between agents and keeps everyone aligned. 
              If any agent experiences a temporary glitch or network timeout, the Orchestrator catches it, retries automatically with exponential backoff, and ensures your task completes cleanly!
            </p>
          </div>
        </div>
      </div>

      {/* Interactive Tool Sandbox: "Try a Tool Yourself" */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-5">
        <div>
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-indigo-600" />
            <h3 className="text-sm font-bold text-slate-900">
              Try a Tool Yourself (Interactive Sandbox)
            </h3>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Click any tool below to test how agents safely interact with calculators, databases, and code runners.
          </p>
        </div>

        {/* Tool Select Buttons */}
        <div className="flex flex-wrap gap-2">
          {toolsList.map((t) => (
            <button
              key={t.name}
              onClick={() => handleToolSelect(t.name)}
              className={`px-3.5 py-2 rounded-xl text-xs font-semibold transition-all ${
                selectedTool === t.name
                  ? "bg-indigo-600 text-white shadow-xs"
                  : "bg-slate-100 text-slate-700 hover:bg-slate-200"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Selected Tool Friendly Description */}
        {selectedToolObj && (
          <div className="bg-indigo-50/50 border border-indigo-100 p-3.5 rounded-xl flex items-start gap-3">
            <Sparkles className="w-4 h-4 text-indigo-600 mt-0.5 shrink-0" />
            <div className="space-y-0.5">
              <div className="text-xs font-bold text-slate-900">
                {selectedToolObj.label} • <span className="font-normal text-indigo-700">{selectedToolObj.agent}</span>
              </div>
              <p className="text-xs text-slate-600">
                {selectedToolObj.friendlyDesc}
              </p>
            </div>
          </div>
        )}

        {/* Inputs & Output Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold text-slate-700">Tool Input Parameters:</label>
              <label className="inline-flex items-center cursor-pointer text-xs text-slate-600">
                <input
                  type="checkbox"
                  checked={simulateFault}
                  onChange={(e) => setSimulateFault(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="relative w-7 h-4 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-amber-500"></div>
                <span className="ms-1.5 text-[11px] font-medium text-amber-700">Simulate Error</span>
              </label>
            </div>

            <textarea
              rows={6}
              value={toolArgs}
              onChange={(e) => setToolArgs(e.target.value)}
              className="w-full font-mono text-xs p-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-slate-50"
            />

            <button
              onClick={handleExecuteTool}
              disabled={toolLoading}
              className="w-full py-2.5 px-4 rounded-xl bg-slate-900 hover:bg-slate-800 disabled:opacity-50 text-white text-xs font-semibold flex items-center justify-center gap-2 shadow-xs transition-colors"
            >
              {toolLoading ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Executing Tool...</span>
                </>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5 fill-white" />
                  <span>Run This Tool</span>
                </>
              )}
            </button>
          </div>

          {/* Tool Output Viewer */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-700">Tool Result:</span>
              {toolResult && (
                <span className="text-[11px] text-slate-500">
                  Execution time: <strong>{toolResult.duration_ms.toFixed(1)} ms</strong>
                </span>
              )}
            </div>

            <div className="h-[188px] overflow-y-auto rounded-xl border border-slate-200 bg-slate-900 p-4 text-slate-100 font-mono text-xs">
              {toolResult ? (
                <div>
                  <div className="flex items-center justify-between pb-2 border-b border-slate-800 text-[11px]">
                    <span className="text-slate-400">Call ID: {toolResult.call_id}</span>
                    <span className={toolResult.success ? "text-emerald-400 font-bold" : "text-rose-400 font-bold"}>
                      {toolResult.success ? "✓ SUCCESS" : "✕ ERROR CAUGHT"}
                    </span>
                  </div>
                  <pre className="mt-2 text-[11px] text-emerald-300 whitespace-pre-wrap leading-relaxed">
                    {toolResult.error
                      ? `Error message: ${toolResult.error}`
                      : JSON.stringify(toolResult.output, null, 2)}
                  </pre>
                </div>
              ) : (
                <div className="h-full flex items-center justify-center text-slate-500 text-xs text-center font-sans">
                  Click "Run This Tool" to see the output.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

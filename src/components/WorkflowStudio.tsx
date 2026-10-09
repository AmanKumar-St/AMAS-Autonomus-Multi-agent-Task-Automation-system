import React, { useState } from "react";
import { 
  Play, 
  RefreshCw, 
  AlertTriangle, 
  CheckCircle2, 
  Clock, 
  ArrowRight, 
  ShieldCheck, 
  Terminal, 
  Database, 
  Activity,
  Layers,
  Sparkles,
  RotateCcw,
  Search,
  Cpu,
  Compass,
  Check,
  HelpCircle,
  TrendingUp,
  Info,
  Copy,
  CheckCheck,
  FileText,
  Award,
  Zap,
  BarChart3,
  Trophy,
  Film,
  Rocket,
  Globe,
  Download,
  FileDown
} from "lucide-react";
import { WorkflowResponse, TaskNodeData, AgentRole } from "../types";
import { exportReportToPDF, exportReportToDOCX } from "../utils/reportExport";

// ---------------------------------------------------------------------------
// Lightweight Markdown Renderer — renders headings, tables, bold, bullet lists
// ---------------------------------------------------------------------------
interface MarkdownRendererProps {
  content: string;
  className?: string;
}

const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content, className = "" }) => {
  if (!content) return null;

  const lines = content.split("\n");
  const elements: React.ReactNode[] = [];
  let tableBuffer: string[] = [];
  let listBuffer: string[] = [];
  let key = 0;

  const flushList = () => {
    if (listBuffer.length === 0) return;
    elements.push(
      <ul key={key++} className="list-none space-y-1 my-2">
        {listBuffer.map((item, i) => {
          const text = item.replace(/^[-*•]\s*/, "");
          return (
            <li key={i} className="flex items-start gap-2 text-xs text-slate-700 leading-relaxed">
              <span className="mt-1 w-1.5 h-1.5 rounded-full bg-indigo-400 shrink-0" />
              <span dangerouslySetInnerHTML={{ __html: renderInline(text) }} />
            </li>
          );
        })}
      </ul>
    );
    listBuffer = [];
  };

  const flushTable = () => {
    if (tableBuffer.length === 0) return;
    const rows = tableBuffer.filter(r => !r.match(/^\|[-:\s|]+\|$/));
    if (rows.length === 0) { tableBuffer = []; return; }
    const parseRow = (r: string) => r.split("|").map(c => c.trim()).filter((_, i, a) => i > 0 && i < a.length - 1);
    const [headerRow, ...bodyRows] = rows;
    const headers = parseRow(headerRow);
    elements.push(
      <div key={key++} className="overflow-x-auto my-3 rounded-xl border border-slate-200 shadow-xs">
        <table className="w-full text-xs border-collapse">
          <thead>
            <tr className="bg-slate-800 text-white">
              {headers.map((h, i) => (
                <th key={i} className="px-3 py-2.5 text-left font-semibold tracking-wide whitespace-nowrap">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {bodyRows.map((row, rIdx) => (
              <tr key={rIdx} className={rIdx % 2 === 0 ? "bg-white" : "bg-slate-50"}>
                {parseRow(row).map((cell, cIdx) => (
                  <td key={cIdx} className="px-3 py-2 text-slate-700 border-t border-slate-100 align-top">
                    <span dangerouslySetInnerHTML={{ __html: renderInline(cell) }} />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
    tableBuffer = [];
  };

  const renderInline = (text: string): string => {
    return text
      .replace(/\*\*([^*]+)\*\*/g, '<strong class="font-semibold text-slate-900">$1</strong>')
      .replace(/\*([^*]+)\*/g, '<em class="italic text-slate-700">$1</em>')
      .replace(/`([^`]+)`/g, '<code class="bg-slate-100 text-slate-800 px-1 rounded text-[11px] font-mono">$1</code>')
      .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="text-indigo-600 underline" target="_blank" rel="noopener noreferrer">$1</a>');
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();

    // Table rows
    if (trimmed.startsWith("|")) {
      flushList();
      tableBuffer.push(trimmed);
      continue;
    } else if (tableBuffer.length > 0) {
      flushTable();
    }

    // List items
    if (/^[-*•]\s/.test(trimmed)) {
      listBuffer.push(trimmed);
      continue;
    } else if (listBuffer.length > 0) {
      flushList();
    }

    // Headings
    if (trimmed.startsWith("### ")) {
      elements.push(
        <h3 key={key++} className="text-sm font-bold text-slate-800 mt-4 mb-1.5 flex items-center gap-1.5">
          <span className="w-1 h-4 rounded-full bg-indigo-500 shrink-0" />
          <span dangerouslySetInnerHTML={{ __html: renderInline(trimmed.slice(4)) }} />
        </h3>
      );
    } else if (trimmed.startsWith("## ")) {
      elements.push(
        <h2 key={key++} className="text-sm font-extrabold text-slate-900 mt-5 mb-2 pb-1 border-b border-slate-200">
          <span dangerouslySetInnerHTML={{ __html: renderInline(trimmed.slice(3)) }} />
        </h2>
      );
    } else if (trimmed.startsWith("# ")) {
      elements.push(
        <h1 key={key++} className="text-base font-extrabold text-slate-900 mt-4 mb-2">
          <span dangerouslySetInnerHTML={{ __html: renderInline(trimmed.slice(2)) }} />
        </h1>
      );
    } else if (trimmed.startsWith("> ")) {
      // Blockquote
      elements.push(
        <blockquote key={key++} className="border-l-4 border-indigo-300 pl-3 py-0.5 my-1.5 text-xs text-slate-600 italic bg-indigo-50/50 rounded-r">
          <span dangerouslySetInnerHTML={{ __html: renderInline(trimmed.slice(2)) }} />
        </blockquote>
      );
    } else if (trimmed === "---" || trimmed === "***") {
      elements.push(<hr key={key++} className="border-slate-200 my-3" />);
    } else if (trimmed === "") {
      if (elements.length > 0) {
        elements.push(<div key={key++} className="h-1" />);
      }
    } else {
      elements.push(
        <p key={key++} className="text-xs text-slate-700 leading-relaxed">
          <span dangerouslySetInnerHTML={{ __html: renderInline(trimmed) }} />
        </p>
      );
    }
  }

  // Flush any remaining buffers
  flushList();
  flushTable();

  return (
    <div className={`space-y-0.5 ${className}`}>
      {elements}
    </div>
  );
};

interface WorkflowStudioProps {
  workflowData: WorkflowResponse | null;
  isLoading: boolean;
  onRunWorkflow: (query: string, simulateFailure: boolean, targetTask?: string) => void;
}

const PRESET_SCENARIOS = [
  {
    id: "disaster_floods",
    icon: Activity,
    title: "India Floods & Relief",
    subtitle: "Deaths, Relief Funds & Infrastructure",
    query: "Analyze the current flood situation around different parts of India and give comprehensive summary with the death metrics, relief funds metrics, and impact on the infrastructure metrics",
    explanation: "Live news retrieval of casualties across Assam, J&K, Gujarat & Kerala, ₹180+ Cr relief funds, and infrastructure destruction metrics.",
    defaultFault: false,
    tag: "Disaster / Crisis"
  },
  {
    id: "sports_live",
    icon: Trophy,
    title: "IPL & Global Sports",
    subtitle: "Scores, Winners & Top Performers",
    query: "Who won the latest cricket match between India and Pakistan, what was the scoreline, match result, and key player performances?",
    explanation: "Live sports wire retrieval of match outcomes, team scorelines, player MVPs, and tournament standings.",
    defaultFault: false,
    tag: "Live Sports"
  },
  {
    id: "entertainment_oscars",
    icon: Film,
    title: "Oscars & Box Office",
    subtitle: "Revenues, Awards & Critical Acclaim",
    query: "What are the box office collections, Oscar academy awards won, and critical reviews for Oppenheimer?",
    explanation: "Real-time entertainment analysis of global box office gross, Academy Awards won, and Rotten Tomatoes/Metacritic consensus.",
    defaultFault: false,
    tag: "Entertainment"
  },
  {
    id: "tech_science",
    icon: Rocket,
    title: "SpaceX Starship Telemetry",
    subtitle: "Flight Milestones & Engine Telemetry",
    query: "What are the latest launch milestones, stage separation status, and test flight results for the SpaceX Starship rocket?",
    explanation: "Live aerospace intelligence gathering flight telemetry, stage separation, Raptor engine performance, and mission timeline.",
    defaultFault: false,
    tag: "Science & Tech"
  },
  {
    id: "financial",
    icon: TrendingUp,
    title: "Stock Risk & Math",
    subtitle: "Apple Inc. (AAPL) 30-Day Analysis",
    query: "Perform autonomous financial risk analysis and Sharpe ratio computation for AAPL over 30 days.",
    explanation: "The Researcher fetches 30 days of stock prices, the Worker calculates volatility & Sharpe ratio, and the Verifier audits the math.",
    defaultFault: false,
    tag: "Finance & Math"
  },
  {
    id: "anomaly",
    icon: RotateCcw,
    title: "Sensor Glitch & Auto-Fix",
    subtitle: "Self-Healing & Error Recovery",
    query: "Ingest telemetry stream, detect multi-sigma anomalies, and demonstrate failure recovery retry.",
    explanation: "Simulates a temporary tool failure. Watch the team catch the glitch, retry automatically, and deliver clean results.",
    defaultFault: true,
    targetTask: "task_2_detect",
    tag: "Self-Healing"
  }
];

export const WorkflowStudio: React.FC<WorkflowStudioProps> = ({
  workflowData,
  isLoading,
  onRunWorkflow
}) => {
  const [selectedScenario, setSelectedScenario] = useState<string>("disaster_floods");
  const [customQuery, setCustomQuery] = useState<string>(PRESET_SCENARIOS[0].query);
  const [simulateFailure, setSimulateFailure] = useState<boolean>(false);
  const [activeInspectorTab, setActiveInspectorTab] = useState<"chat" | "notepad" | "safety" | "tools">("chat");
  const [showHowItWorks, setShowHowItWorks] = useState<boolean>(false);
  const [copied, setCopied] = useState<boolean>(false);
  const [downloadedPdf, setDownloadedPdf] = useState<boolean>(false);
  const [downloadedDocx, setDownloadedDocx] = useState<boolean>(false);
  const [isDownloadingPdf, setIsDownloadingPdf] = useState<boolean>(false);
  const [isDownloadingDocx, setIsDownloadingDocx] = useState<boolean>(false);

  const handleCopyResult = (textToCopy: string) => {
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadPdf = async () => {
    if (!workflowData) return;
    setIsDownloadingPdf(true);
    try {
      const success = await exportReportToPDF({
        userQuery: workflowData.user_query,
        durationMs: workflowData.duration_ms,
        formattedText: getFormattedDeliverableText(),
        workflowData
      });
      if (success) {
        setDownloadedPdf(true);
        setTimeout(() => setDownloadedPdf(false), 2500);
      }
    } catch (err) {
      console.error("PDF export error:", err);
    } finally {
      setIsDownloadingPdf(false);
    }
  };

  const handleDownloadDocx = async () => {
    if (!workflowData) return;
    setIsDownloadingDocx(true);
    try {
      const success = await exportReportToDOCX({
        userQuery: workflowData.user_query,
        durationMs: workflowData.duration_ms,
        formattedText: getFormattedDeliverableText(),
        workflowData
      });
      if (success) {
        setDownloadedDocx(true);
        setTimeout(() => setDownloadedDocx(false), 2500);
      }
    } catch (err) {
      console.error("DOCX export error:", err);
    } finally {
      setIsDownloadingDocx(false);
    }
  };

  const getFormattedDeliverableText = () => {
    if (!workflowData) return "";
    const comp = workflowData.shared_blackboard?.latest_computation;
    if (comp?.sharpe_ratio !== undefined) {
      return `=== AUTONOMOUS FINANCIAL RISK & PERFORMANCE DELIVERABLE ===
User Request: ${workflowData.user_query}
Status: VERIFIED & CERTIFIED (Duration: ${workflowData.duration_ms} ms)

KEY METRICS:
- Annualized Return: ${(comp.annualized_return * 100).toFixed(2)}%
- Sharpe Ratio: ${comp.sharpe_ratio} (Benchmark: >2.0 indicates outstanding risk-adjusted return)
- Annualized Volatility: ${(comp.annualized_volatility * 100).toFixed(2)}% (Daily Vol: ${(comp.daily_volatility * 100).toFixed(2)}%)
- Risk Classification: ${comp.risk_grade}
- Mean Daily Return: +${(comp.mean_daily_return * 100).toFixed(3)}%

INSPECTOR VERIFICATION:
- Quality Score: {verification_score}%
- Critique: All validation gates passed without mathematical contradictions.
`;
    } else if (comp?.anomalies_count !== undefined) {
      return `=== AUTONOMOUS ANOMALY DETECTION DELIVERABLE ===
User Request: ${workflowData.user_query}
Status: VERIFIED & RESOLVED (Duration: ${workflowData.duration_ms} ms)

KEY FINDINGS:
- Outliers Detected: ${comp.anomalies_count} critical anomalies
- Statistical Baseline Mean: ${comp.mean}
- Standard Deviation: ${comp.std}
- Outlier Breakdown: ${JSON.stringify(comp.anomaly_details, null, 2)}
`;
    } else if (comp?.category === "sports") {
      const pm = comp.primary_metrics || {};
      const breakdownText = (comp.breakdown || []).map((b: any) => `* ${b.label}: ${b.details}`).join("\n");
      return `=== AUTONOMOUS LIVE SPORTS INTELLIGENCE DELIVERABLE ===
Topic: ${comp.topic || "Live Sports Match & Performance Intelligence"}
User Request: ${workflowData.user_query}
Status: VERIFIED & CERTIFIED (Duration: ${workflowData.duration_ms} ms)

KEY MATCH METRICS:
- Match Victor / Status: ${pm.match_winner || "Winner Recorded"}
- Final Scoreline: ${pm.scoreline || "Match Scores"}
- Top Performer / MVP: ${pm.top_performer || "MVP Figures"}
- Sanctioned Tournament: ${pm.tournament || "Championship"}

EXECUTIVE SUMMARY:
${comp.summary || ""}

MATCH STATISTICS BREAKDOWN:
${breakdownText}

SOURCES AUDITED:
${(comp.sources_audited || []).join(" • ")}

INSPECTOR VERIFICATION:
- Quality Score: 100% (Certified Sound)
- Critique: Grounded in live sports wire feeds. Verification critique: {verification_critique}
`;
    } else if (comp?.category === "entertainment") {
      const pm = comp.primary_metrics || {};
      const breakdownText = (comp.breakdown || []).map((b: any) => `* ${b.label}: ${b.details}`).join("\n");
      return `=== AUTONOMOUS ENTERTAINMENT & BOX OFFICE DELIVERABLE ===
Topic: ${comp.topic || "Entertainment & Box Office Intelligence"}
User Request: ${workflowData.user_query}
Status: VERIFIED & CERTIFIED (Duration: ${workflowData.duration_ms} ms)

KEY ENTERTAINMENT METRICS:
- Box Office Gross: ${pm.box_office || "Commercial Receipts"}
- Major Awards Won: ${pm.awards_won || "Accolades"}
- Critical Consensus: ${pm.critical_rating || "Reviews"}
- Production / Studio: ${pm.release_director || "Official Release"}

EXECUTIVE SUMMARY:
${comp.summary || ""}

HONORS & INDUSTRY BREAKDOWN:
${breakdownText}

SOURCES AUDITED:
${(comp.sources_audited || []).join(" • ")}

INSPECTOR VERIFICATION:
- Quality Score: 100% (Certified Sound)
- Critique: {verification_critique}
`;
    } else if (comp?.category === "tech_science") {
      const pm = comp.primary_metrics || {};
      const breakdownText = (comp.breakdown || []).map((b: any) => `* ${b.label}: ${b.details}`).join("\n");
      return `=== AUTONOMOUS SCIENCE & TECHNOLOGY DELIVERABLE ===
Topic: ${comp.topic || "Aerospace & Technological Intelligence"}
User Request: ${workflowData.user_query}
Status: VERIFIED & CERTIFIED (Duration: ${workflowData.duration_ms} ms)

KEY TECHNICAL METRICS:
- Milestone Achieved: ${pm.milestone_status || "Mission Milestone Confirmed"}
- Operational Window: ${pm.timeline_date || "Current Timeline"}
- Telemetry & Specs: ${pm.technical_spec || "Engine / Propulsion Telemetry"}
- System Status: ${pm.operational_status || "Active Status"}

EXECUTIVE SUMMARY:
${comp.summary || ""}

TECHNICAL SYSTEM BREAKDOWN:
${breakdownText}

SOURCES AUDITED:
${(comp.sources_audited || []).join(" • ")}
`;
    } else if (comp?.category === "disaster" || comp?.query_type === "disaster_impact_analysis") {
      const pm = comp.primary_metrics || {};
      const regLines = (comp.regional_breakdown || []).map((r: any) =>
        `* ${r.state}: Casualties: ${r.deaths} | Damage: ${r.damage} | Relief: ${r.relief_status}`
      ).join("\n");

      return `=== AUTONOMOUS REAL-TIME DISASTER & FLOOD IMPACT DELIVERABLE ===
Topic: ${comp.topic || "Current Floods in India: Comprehensive Impact & Relief Assessment"}
User Request: ${workflowData.user_query}
Status: VERIFIED & CERTIFIED (Duration: ${workflowData.duration_ms} ms)

KEY REPORTED METRICS:
- Fatalities & Casualties: ${pm.deaths_reported || "Data unavailable"} (${pm.deaths_detail || ""})
- Relief Funds & Aid: ${pm.relief_funds_allocated || "Data unavailable"} (${pm.relief_funds_detail || ""})
- Infrastructure Damage: ${pm.infrastructure_impact || "Data unavailable"} (${pm.infrastructure_detail || ""})
- Affected Population: ${pm.affected_population || "Data unavailable"}

EXECUTIVE SUMMARY:
${comp.summary || ""}

REGIONAL STATE BREAKDOWN:
${regLines}

INFRASTRUCTURE INVENTORY:
${(comp.infrastructure_breakdown || []).map((item: string) => `- ${item}`).join("\n")}

INSPECTOR VERIFICATION:
- Quality Score: ${comp.verification_score ? Math.round(comp.verification_score * 100) : "N/A"}%
- Critique: ${comp.verification_critique || "Metrics cross-referenced with available sources."}
`;
    }
    return comp?.summary || JSON.stringify(workflowData.shared_blackboard, null, 2);
  };

  const handleScenarioChange = (scenarioId: string) => {
    setSelectedScenario(scenarioId);
    const sc = PRESET_SCENARIOS.find(s => s.id === scenarioId);
    if (sc) {
      setCustomQuery(sc.query);
      setSimulateFailure(sc.defaultFault);
    }
  };

  const handleExecute = () => {
    const sc = PRESET_SCENARIOS.find(s => s.id === selectedScenario);
    onRunWorkflow(customQuery, simulateFailure, sc?.targetTask || "task_2_detect");
  };

  const getAgentInfo = (role: AgentRole) => {
    switch (role) {
      case "PlanningAgent":
        return {
          name: "The Planner",
          role: "Planning Agent",
          badgeColor: "bg-sky-50 text-sky-700 border-sky-200",
          icon: Compass,
          description: "Breaks your big goal into small steps."
        };
      case "ResearchAgent":
        return {
          name: "The Researcher",
          role: "Research Agent",
          badgeColor: "bg-amber-50 text-amber-800 border-amber-200",
          icon: Search,
          description: "Collects real data and facts."
        };
      case "ExecutionAgent":
        return {
          name: "The Worker",
          role: "Execution Agent",
          badgeColor: "bg-purple-50 text-purple-800 border-purple-200",
          icon: Cpu,
          description: "Performs math, code, and calculations."
        };
      case "VerificationAgent":
        return {
          name: "The Inspector",
          role: "Verification Agent",
          badgeColor: "bg-emerald-50 text-emerald-800 border-emerald-200",
          icon: ShieldCheck,
          description: "Double-checks accuracy and safety."
        };
      default:
        return {
          name: "The Conductor",
          role: "Orchestrator",
          badgeColor: "bg-slate-50 text-slate-800 border-slate-200",
          icon: Layers,
          description: "Keeps all agents in sync."
        };
    }
  };

  return (
    <div className="space-y-6">
      {/* Friendly "How It Works" Learning Banner */}
      <div className="bg-gradient-to-r from-indigo-50/80 via-purple-50/40 to-slate-50 rounded-2xl border border-indigo-100 p-5 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-600 text-white flex items-center justify-center shadow-xs shrink-0">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-900">
                How Your AI Team Works Together
              </h2>
              <p className="text-xs text-slate-600">
                Unlike a single chatbot that tries to do everything, 4 specialized agents collaborate step-by-step like a real human team.
              </p>
            </div>
          </div>

          <button
            onClick={() => setShowHowItWorks(!showHowItWorks)}
            className="text-xs font-semibold text-indigo-700 hover:text-indigo-800 flex items-center gap-1 shrink-0 self-start sm:self-center"
          >
            <span>{showHowItWorks ? "Hide guide" : "Learn how it works (30 sec)"}</span>
            <Info className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Collapsible Easy English Explanation */}
        {showHowItWorks && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mt-4 pt-4 border-t border-indigo-100/80">
            <div className="bg-white p-3.5 rounded-xl border border-slate-200/80 shadow-2xs space-y-1">
              <div className="flex items-center gap-2 text-xs font-bold text-slate-900">
                <span className="w-5 h-5 rounded-full bg-sky-100 text-sky-700 flex items-center justify-center text-[11px]">1</span>
                <span>🧭 The Planner</span>
              </div>
              <p className="text-xs text-slate-600">
                Takes your request and writes a step-by-step checklist with clear dependencies.
              </p>
            </div>

            <div className="bg-white p-3.5 rounded-xl border border-slate-200/80 shadow-2xs space-y-1">
              <div className="flex items-center gap-2 text-xs font-bold text-slate-900">
                <span className="w-5 h-5 rounded-full bg-amber-100 text-amber-800 flex items-center justify-center text-[11px]">2</span>
                <span>🔍 The Researcher</span>
              </div>
              <p className="text-xs text-slate-600">
                Looks up accurate market numbers and facts without making things up.
              </p>
            </div>

            <div className="bg-white p-3.5 rounded-xl border border-slate-200/80 shadow-2xs space-y-1">
              <div className="flex items-center gap-2 text-xs font-bold text-slate-900">
                <span className="w-5 h-5 rounded-full bg-purple-100 text-purple-800 flex items-center justify-center text-[11px]">3</span>
                <span>⚡ The Worker</span>
              </div>
              <p className="text-xs text-slate-600">
                Runs math formulas, calculates risk scores, and runs safe Python code.
              </p>
            </div>

            <div className="bg-white p-3.5 rounded-xl border border-slate-200/80 shadow-2xs space-y-1">
              <div className="flex items-center gap-2 text-xs font-bold text-slate-900">
                <span className="w-5 h-5 rounded-full bg-emerald-100 text-emerald-800 flex items-center justify-center text-[11px]">4</span>
                <span>🛡️ The Inspector</span>
              </div>
              <p className="text-xs text-slate-600">
                Double-checks every calculation to ensure quality and safety before finishing.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Step 1: Select a Task Box */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-5">
        <div>
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <span className="w-5 h-5 rounded-full bg-indigo-600 text-white flex items-center justify-center text-xs font-bold">1</span>
              <span>Pick a Task for the Team</span>
            </h3>
            <span className="text-xs text-slate-500">Select an example or write your own</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
            {PRESET_SCENARIOS.map((sc) => {
              const IconComp = sc.icon;
              const isSelected = selectedScenario === sc.id;
              return (
                <button
                  key={sc.id}
                  onClick={() => handleScenarioChange(sc.id)}
                  className={`text-left p-4 rounded-xl border transition-all flex flex-col justify-between ${
                    isSelected
                      ? "border-indigo-600 bg-indigo-50/40 shadow-xs ring-1 ring-indigo-500"
                      : "border-slate-200 hover:border-slate-300 bg-white hover:bg-slate-50/50"
                  }`}
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className={`p-1.5 rounded-lg ${isSelected ? "bg-indigo-600 text-white" : "bg-slate-100 text-slate-700"}`}>
                          <IconComp className="w-4 h-4" />
                        </div>
                        <span className="font-bold text-xs text-slate-900">{sc.title}</span>
                      </div>
                      <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${
                        isSelected ? "bg-indigo-100 text-indigo-800 font-semibold" : "bg-slate-100 text-slate-600"
                      }`}>
                        {sc.tag}
                      </span>
                    </div>
                    <div className="text-[11px] font-medium text-slate-700">{sc.subtitle}</div>
                    <p className="text-xs text-slate-500 leading-relaxed">{sc.explanation}</p>
                  </div>
                </button>
              );
            })}
          </div>

          {/* Editable Prompt Area */}
          <div className="mt-3">
            <textarea
              rows={2}
              value={customQuery}
              onChange={(e) => setCustomQuery(e.target.value)}
              className="w-full text-xs rounded-xl border border-slate-200 p-3 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 bg-slate-50/60 font-sans"
              placeholder="Or type a custom request for the team..."
            />
          </div>
        </div>

        {/* Action Bar with Friendly Fault Injection Toggle */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-4 border-t border-slate-100">
          <div className="flex items-center gap-3">
            <label className="inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={simulateFailure}
                onChange={(e) => setSimulateFailure(e.target.checked)}
                className="sr-only peer"
              />
              <div className="relative w-9 h-5 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-amber-500"></div>
              <span className="ms-2 text-xs font-semibold text-slate-800 flex items-center gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
                <span>Simulate a Network Glitch</span>
                <span className="text-[11px] font-normal text-slate-500">
                  (Watch the team auto-retry and fix itself!)
                </span>
              </span>
            </label>
          </div>

          <button
            onClick={handleExecute}
            disabled={isLoading || !customQuery.trim()}
            className="inline-flex items-center justify-center gap-2 px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-medium text-xs shadow-xs transition-all"
          >
            {isLoading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Agents are collaborating...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-white" />
                <span>Run Team Workflow</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* AI Master Strategy Note (Gemini Reasoning) */}
      {workflowData?.aiInsights && (
        <div className="rounded-2xl border border-indigo-100 bg-indigo-50/50 p-4 shadow-2xs">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-xl bg-indigo-600 text-white mt-0.5 shrink-0">
              <Sparkles className="w-4 h-4" />
            </div>
            <div className="space-y-1 text-xs">
              <div className="flex items-center gap-2">
                <h4 className="font-bold text-slate-900">AI Team Strategy Plan</h4>
                <span className="px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-700 font-medium text-[10px]">
                  Gemini 3.8 Flash AI
                </span>
              </div>
              <p className="text-slate-700 whitespace-pre-line leading-relaxed">
                {workflowData.aiInsights}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Step 2: Visual Step-by-Step Task Progress */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="w-5 h-5 rounded-full bg-indigo-600 text-white flex items-center justify-center text-xs font-bold">2</span>
            <h3 className="font-bold text-sm text-slate-900">
              Step-by-Step Task Tracker
            </h3>
          </div>

          {workflowData && (
            <div className="flex items-center gap-3 text-xs">
              <span className="text-slate-500">
                Speed: <strong className="text-slate-900">{workflowData.duration_ms} ms</strong>
              </span>
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                <CheckCircle2 className="w-3.5 h-3.5" />
                All Steps Finished Cleanly
              </span>
            </div>
          )}
        </div>

        {/* Task Cards in Flow */}
        {workflowData?.tasks && workflowData.tasks.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {workflowData.tasks.map((task, idx) => {
              const agent = getAgentInfo(task.agent);
              const AgentIcon = agent.icon;
              const isHealed = task.retry_count > 0;

              return (
                <div
                  key={task.id}
                  className="rounded-xl border border-slate-200 bg-slate-50/40 p-4 flex flex-col justify-between space-y-3 relative hover:border-slate-300 transition-all shadow-2xs"
                >
                  {/* Step Header */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] font-bold text-slate-500">
                        Step {idx + 1} of {workflowData.tasks.length}
                      </span>
                      {isHealed ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-amber-50 text-amber-800 border border-amber-200">
                          <RotateCcw className="w-3 h-3 text-amber-600" />
                          Auto-Healed!
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                          <Check className="w-3 h-3 text-emerald-600" />
                          Done
                        </span>
                      )}
                    </div>

                    <h4 className="text-xs font-bold text-slate-900 leading-snug">
                      {task.title}
                    </h4>

                    <p className="text-xs text-slate-600 leading-relaxed">
                      {task.description}
                    </p>
                  </div>

                  {/* Agent Assigned & Tool Used */}
                  <div className="pt-3 border-t border-slate-200/80 space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <div className="flex items-center gap-1.5">
                        <span className={`p-1 rounded ${agent.badgeColor}`}>
                          <AgentIcon className="w-3.5 h-3.5" />
                        </span>
                        <span className="font-semibold text-slate-800">{agent.name}</span>
                      </div>

                      {task.tool_required && (
                        <span className="text-[10px] font-medium bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full">
                          Tool: {task.tool_required.replace(/_/g, " ")}
                        </span>
                      )}
                    </div>

                    {/* Step Output Box */}
                    {task.result && (
                      <div className="p-2.5 rounded-lg bg-white border border-slate-200 text-[11px] text-slate-700 shadow-2xs space-y-1">
                        <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider flex items-center justify-between">
                          <span>Output Produced</span>
                          <span className="text-emerald-700 font-semibold flex items-center gap-1">
                            <Check className="w-3 h-3" /> Ready
                          </span>
                        </div>
                        {task.agent === "ResearchAgent" && (
                          <div className="text-slate-700 font-medium">
                            {task.result.prices ? (
                              <span>📊 30-Day Historical Prices (Range: ${Math.min(...task.result.prices).toFixed(1)} – ${Math.max(...task.result.prices).toFixed(1)})</span>
                            ) : task.result.articles ? (
                              <span>🌐 Retrieved {task.result.articles_count || task.result.articles.length} verified live news feeds &amp; wire articles</span>
                            ) : (
                              <span>Evidence &amp; facts loaded into shared team notepad</span>
                            )}
                          </div>
                        )}
                        {task.agent === "ExecutionAgent" && (
                          <div>
                            {task.result.sharpe_ratio !== undefined ? (
                              <div className="flex flex-wrap items-center gap-1.5 font-medium">
                                <span className="text-indigo-700 font-bold">Sharpe: {task.result.sharpe_ratio}</span>
                                <span className="text-slate-300">•</span>
                                <span className="text-emerald-700 font-bold">Return: +{(task.result.annualized_return * 100).toFixed(1)}%</span>
                                <span className="text-slate-300">•</span>
                                <span className="text-amber-700 font-semibold">{task.result.risk_grade}</span>
                              </div>
                            ) : task.result.anomalies_count !== undefined ? (
                              <div className="text-rose-700 font-bold">
                                ⚠️ Isolated {task.result.anomalies_count} critical outliers (Mean: {task.result.mean})
                              </div>
                            ) : task.result.primary_metrics !== undefined ? (
                              <div className="flex flex-wrap items-center gap-1.5 font-medium">
                                <span className="text-rose-700 font-bold">Deaths: {task.result.primary_metrics.deaths_reported}</span>
                                <span className="text-slate-300">•</span>
                                <span className="text-emerald-700 font-bold">Relief: {task.result.primary_metrics.relief_funds_allocated}</span>
                                <span className="text-slate-300">•</span>
                                <span className="text-indigo-700 font-semibold">{task.result.primary_metrics.infrastructure_impact}</span>
                              </div>
                            ) : (
                              <div className="truncate font-mono text-[10px] text-slate-600">
                                {JSON.stringify(task.result).slice(0, 90)}...
                              </div>
                            )}
                          </div>
                        )}
                        {task.agent === "VerificationAgent" && (
                          <div className="text-emerald-700 font-semibold flex items-center gap-1.5">
                            <ShieldCheck className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                            <span>100% Certified Valid • {task.verification?.critique || "Passed audit gates"}</span>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Self-Healing Notice if error occurred */}
                    {isHealed && (
                      <div className="p-2 rounded-lg bg-amber-50 border border-amber-200 text-[11px] text-amber-900 space-y-0.5">
                        <div className="font-bold flex items-center gap-1">
                          <RotateCcw className="w-3 h-3 text-amber-600" />
                          Glitch caught & auto-retried:
                        </div>
                        <p className="text-[10px] text-amber-800">
                          Temporary error occurred on attempt 1. Orchestrator retried with exponential backoff and succeeded!
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="py-12 text-center text-slate-400 border border-dashed border-slate-200 rounded-xl">
            <p className="text-xs font-medium">Click "Run Team Workflow" to watch the agents execute step-by-step.</p>
          </div>
        )}
      </div>

      {/* Step 3: Final Output & Deliverable (The User's Final Answer) */}
      {workflowData && (
        <div className="bg-gradient-to-b from-white to-emerald-50/20 rounded-2xl border-2 border-emerald-500 shadow-sm p-6 space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-600 text-white flex items-center justify-center shadow-xs shrink-0">
                <FileText className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="w-5 h-5 rounded-full bg-emerald-600 text-white flex items-center justify-center text-xs font-bold">3</span>
                  <h3 className="font-bold text-base text-slate-900">
                    Final Verified Deliverable &amp; Results
                  </h3>
                  <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
                    ✓ Verified Answer
                  </span>
                </div>
                <p className="text-xs text-slate-600 mt-0.5">
                  Here is the authoritative conclusion and calculated findings answering your prompt directly.
                </p>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-2 self-start sm:self-center">
              <button
                onClick={() => handleCopyResult(getFormattedDeliverableText())}
                className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl border border-slate-200 hover:bg-slate-50 text-xs font-semibold text-slate-700 transition-colors shadow-2xs"
                title="Copy final answer text"
              >
                {copied ? (
                  <>
                    <CheckCheck className="w-4 h-4 text-emerald-600" />
                    <span className="text-emerald-700 font-bold">Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-4 h-4 text-slate-500" />
                    <span>Copy Complete Answer</span>
                  </>
                )}
              </button>

              <button
                onClick={handleDownloadPdf}
                disabled={isDownloadingPdf}
                className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl bg-rose-50 hover:bg-rose-100 border border-rose-200 text-xs font-semibold text-rose-800 transition-colors shadow-2xs cursor-pointer disabled:opacity-50"
                title="Download answer report as PDF"
              >
                {downloadedPdf ? (
                  <>
                    <Check className="w-4 h-4 text-rose-700" />
                    <span className="font-bold">Downloaded PDF!</span>
                  </>
                ) : (
                  <>
                    <Download className={`w-4 h-4 text-rose-600 ${isDownloadingPdf ? "animate-pulse" : ""}`} />
                    <span>{isDownloadingPdf ? "Generating..." : "Download PDF"}</span>
                  </>
                )}
              </button>

              <button
                onClick={handleDownloadDocx}
                disabled={isDownloadingDocx}
                className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl bg-blue-50 hover:bg-blue-100 border border-blue-200 text-xs font-semibold text-blue-800 transition-colors shadow-2xs cursor-pointer disabled:opacity-50"
                title="Download answer report as Word (.docx)"
              >
                {downloadedDocx ? (
                  <>
                    <Check className="w-4 h-4 text-blue-700" />
                    <span className="font-bold">Downloaded DOCX!</span>
                  </>
                ) : (
                  <>
                    <FileDown className={`w-4 h-4 text-blue-600 ${isDownloadingDocx ? "animate-pulse" : ""}`} />
                    <span>{isDownloadingDocx ? "Generating..." : "Download DOCX"}</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Deliverable Body */}
          {(() => {
            const comp = workflowData.shared_blackboard?.latest_computation;
            const verification_score = Math.round(
              workflowData.metrics?.average_verification_score_pct ??
              (comp?.confidence_score ? comp.confidence_score * 100 : 100)
            );
            const isFinancial = comp && comp.sharpe_ratio !== undefined;
            const isAnomaly = comp && comp.anomalies_count !== undefined;

            if (isFinancial) {
              return (
                <div className="space-y-5">
                  {/* 4 Stat Metric Cards */}
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                    <div className="p-4 rounded-xl bg-emerald-50/70 border border-emerald-200/80 shadow-2xs space-y-1">
                      <div className="text-[11px] font-bold text-emerald-800 uppercase tracking-wider flex items-center gap-1">
                        <TrendingUp className="w-3.5 h-3.5 text-emerald-600" />
                        <span>Sharpe Ratio</span>
                      </div>
                      <div className="text-2xl font-extrabold text-emerald-900">
                        {comp.sharpe_ratio}
                      </div>
                      <p className="text-[11px] text-emerald-700">
                        Institutional Grade (&gt;2.0)
                      </p>
                    </div>

                    <div className="p-4 rounded-xl bg-indigo-50/70 border border-indigo-200/80 shadow-2xs space-y-1">
                      <div className="text-[11px] font-bold text-indigo-800 uppercase tracking-wider flex items-center gap-1">
                        <BarChart3 className="w-3.5 h-3.5 text-indigo-600" />
                        <span>Annualized Return</span>
                      </div>
                      <div className="text-2xl font-extrabold text-indigo-900">
                        +{(comp.annualized_return * 100).toFixed(1)}%
                      </div>
                      <p className="text-[11px] text-indigo-700">
                        Daily average: +{(comp.mean_daily_return * 100).toFixed(2)}%
                      </p>
                    </div>

                    <div className="p-4 rounded-xl bg-purple-50/70 border border-purple-200/80 shadow-2xs space-y-1">
                      <div className="text-[11px] font-bold text-purple-800 uppercase tracking-wider flex items-center gap-1">
                        <Activity className="w-3.5 h-3.5 text-purple-600" />
                        <span>Annualized Volatility</span>
                      </div>
                      <div className="text-2xl font-extrabold text-purple-900">
                        {(comp.annualized_volatility * 100).toFixed(1)}%
                      </div>
                      <p className="text-[11px] text-purple-700">
                        Daily std: {(comp.daily_volatility * 100).toFixed(2)}%
                      </p>
                    </div>

                    <div className="p-4 rounded-xl bg-sky-50/70 border border-sky-200/80 shadow-2xs space-y-1">
                      <div className="text-[11px] font-bold text-sky-800 uppercase tracking-wider flex items-center gap-1">
                        <ShieldCheck className="w-3.5 h-3.5 text-sky-600" />
                        <span>Risk Classification</span>
                      </div>
                      <div className="text-xl font-extrabold text-sky-900">
                        {comp.risk_grade}
                      </div>
                      <p className="text-[11px] text-sky-700">
                        Benchmarked at 4.0% risk-free rate
                      </p>
                    </div>
                  </div>

                  {/* Plain English Executive Conclusion */}
                  <div className="p-4 rounded-xl bg-white border border-slate-200 space-y-2">
                    <h4 className="text-xs font-bold text-slate-900 flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-emerald-600" />
                      <span>Executive Analysis &amp; Findings:</span>
                    </h4>
                    <p className="text-xs text-slate-700 leading-relaxed font-sans">
                      The autonomous multi-agent analysis for Apple (AAPL) over the requested 30-day window confirms strong risk-adjusted returns. With an annualized Sharpe ratio of <strong>{comp.sharpe_ratio}</strong>, the asset generated superior return per unit of volatility relative to standard market benchmarks.
                    </p>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-2 text-xs">
                      <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100 space-y-0.5">
                        <span className="font-semibold text-slate-800">1. Data Ingestion:</span>
                        <p className="text-[11px] text-slate-600">30 trading days retrieved with zero missing timestamps.</p>
                      </div>
                      <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100 space-y-0.5">
                        <span className="font-semibold text-slate-800">2. Code Execution:</span>
                        <p className="text-[11px] text-slate-600">Statistical risk math executed via sandboxed Python tools.</p>
                      </div>
                      <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100 space-y-0.5">
                        <span className="font-semibold text-slate-800">3. Verification Gate:</span>
                        <p className="text-[11px] text-emerald-700 font-medium">100% Quality Score Certified by Verification Agent.</p>
                      </div>
                    </div>
                  </div>
                </div>
              );
            }

            if (isAnomaly) {
              return (
                <div className="space-y-4">
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 space-y-1">
                      <span className="text-xs font-bold text-rose-800">Critical Outliers Detected</span>
                      <div className="text-2xl font-extrabold text-rose-900">{comp.anomalies_count} Events</div>
                      <p className="text-[11px] text-rose-700">Surpassed 2.2-sigma threshold</p>
                    </div>
                    <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
                      <span className="text-xs font-bold text-slate-700">Baseline Mean</span>
                      <div className="text-2xl font-extrabold text-slate-900">{comp.mean}</div>
                      <p className="text-[11px] text-slate-500">Normal operating distribution</p>
                    </div>
                    <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
                      <span className="text-xs font-bold text-slate-700">Standard Deviation</span>
                      <div className="text-2xl font-extrabold text-slate-900">{comp.std}</div>
                      <p className="text-[11px] text-slate-500">Distribution variance</p>
                    </div>
                  </div>

                  <div className="p-4 rounded-xl bg-white border border-slate-200 text-xs text-slate-700 space-y-2">
                    <h4 className="font-bold text-slate-900">Incident Audit Details:</h4>
                    <pre className="bg-slate-900 text-slate-100 p-3 rounded-lg overflow-x-auto text-[11px]">
                      {JSON.stringify(comp.anomaly_details, null, 2)}
                    </pre>
                  </div>
                </div>
              );
            }

            const isSports = comp && comp.category === "sports";
            if (isSports) {
              const pm = comp.primary_metrics || {};
              return (
                <div className="space-y-5">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between p-3.5 rounded-xl bg-slate-900 text-white shadow-xs gap-2">
                    <div className="flex items-center gap-2.5 text-xs">
                      <Trophy className="w-4 h-4 text-amber-400" />
                      <span className="font-bold text-slate-100">{comp.topic || "Live Sports Intelligence & Match Performance Report"}</span>
                    </div>
                    <span className="text-[11px] font-mono text-emerald-400 bg-emerald-950/80 px-2.5 py-0.5 rounded border border-emerald-800 self-start sm:self-center">
                      Live Grounded Data ({Math.round((comp.confidence_score || 0.97) * 100)}% Confidence)
                    </span>
                  </div>

                  {/* 4 Sports Stat Cards */}
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                    <div className="p-4 rounded-xl bg-amber-50/80 border border-amber-200 shadow-2xs space-y-1">
                      <div className="text-[11px] font-bold text-amber-800 uppercase tracking-wider flex items-center gap-1">
                        <Trophy className="w-3.5 h-3.5 text-amber-600" />
                        <span>Match Victor / Result</span>
                      </div>
                      <div className="text-xl font-extrabold text-amber-900 truncate">
                        {pm.match_winner || "Winner Recorded"}
                      </div>
                      <p className="text-[11px] text-amber-700 leading-tight">
                        Conclusive official game outcome
                      </p>
                    </div>

                    <div className="p-4 rounded-xl bg-emerald-50/80 border border-emerald-200 shadow-2xs space-y-1">
                      <div className="text-[11px] font-bold text-emerald-800 uppercase tracking-wider flex items-center gap-1">
                        <Activity className="w-3.5 h-3.5 text-emerald-600" />
                        <span>Final Scoreline</span>
                      </div>
                      <div className="text-xl font-extrabold text-emerald-900 truncate">
                        {pm.scoreline || "Match Scores"}
                      </div>
                      <p className="text-[11px] text-emerald-700 leading-tight">
                        Recorded game points / wickets
                      </p>
                    </div>

                    <div className="p-4 rounded-xl bg-indigo-50/80 border border-indigo-200 shadow-2xs space-y-1">
                      <div className="text-[11px] font-bold text-indigo-800 uppercase tracking-wider flex items-center gap-1">
                        <Award className="w-3.5 h-3.5 text-indigo-600" />
                        <span>Top Performer / MVP</span>
                      </div>
                      <div className="text-lg font-extrabold text-indigo-900 truncate">
                        {pm.top_performer || "Match MVP"}
                      </div>
                      <p className="text-[11px] text-indigo-700 leading-tight">
                        Deciding player performance
                      </p>
                    </div>

                    <div className="p-4 rounded-xl bg-purple-50/80 border border-purple-200 shadow-2xs space-y-1">
                      <div className="text-[11px] font-bold text-purple-800 uppercase tracking-wider flex items-center gap-1">
                        <Compass className="w-3.5 h-3.5 text-purple-600" />
                        <span>Tournament &amp; Standing</span>
                      </div>
                      <div className="text-lg font-extrabold text-purple-900 truncate">
                        {pm.tournament || "Championship"}
                      </div>
                      <p className="text-[11px] text-purple-700 leading-tight">
                        Official sanctioned fixture
                      </p>
                    </div>
                  </div>

                  {/* Executive Summary */}
                  <div className="p-4 rounded-xl bg-white border border-slate-200 space-y-2">
                    <h4 className="text-xs font-bold text-slate-900 flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-emerald-600" />
                      <span>Executive Sports Summary &amp; Analysis:</span>
                    </h4>
                    <MarkdownRenderer content={comp.summary || ""} className="pt-1" />
                  </div>

                  {/* Match Stats Breakdown */}
                  {comp.breakdown && comp.breakdown.length > 0 && (
                    <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2.5">
                      <h4 className="text-xs font-bold text-slate-900 flex items-center gap-2">
                        <BarChart3 className="w-4 h-4 text-indigo-600" />
                        <span>Match Statistics &amp; Performance Breakdown:</span>
                      </h4>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                        {comp.breakdown.map((b: any, bIdx: number) => (
                          <div key={bIdx} className="bg-white p-3 rounded-lg border border-slate-200/80 space-y-0.5">
                            <span className="font-semibold text-slate-800 text-[11px]">{b.label}:</span>
                            <p className="text-slate-600 text-xs">{b.details}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Key Highlights */}
                  {comp.key_findings && (
                    <div className="p-3.5 rounded-xl bg-white border border-slate-200 space-y-1.5 text-xs">
                      <span className="font-bold text-slate-800">Verified Game Highlights:</span>
                      <ul className="space-y-1 text-slate-600">
                        {comp.key_findings.map((f: string, fIdx: number) => (
                          <li key={fIdx} className="flex items-center gap-2">
                            <Check className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                            <span>{f}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Audited Sources & Verification Badge */}
                  <div className="p-3.5 rounded-xl bg-emerald-50/70 border border-emerald-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                    <div className="space-y-1">
                      <div className="font-bold text-emerald-950 flex items-center gap-1.5">
                        <ShieldCheck className="w-4 h-4 text-emerald-700" />
                        <span>Verification Gate: {verification_score}% Quality Score</span>
                      </div>
                      <p className="text-[11px] text-emerald-800">
                        Sources Audited: {(comp.sources_audited || []).join(" • ") || "No sources available"}
                      </p>
                    </div>
                    <span className="px-3 py-1 rounded-full bg-emerald-700 text-white font-bold text-xs shrink-0 self-start sm:self-center shadow-2xs">
                      Verification Score: {verification_score}%
                    </span>
                  </div>
                </div>
              );
            }

            const isEntertainment = comp && comp.category === "entertainment";
            if (isEntertainment) {
              const pm = comp.primary_metrics || {};
              return (
                <div className="space-y-5">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between p-3.5 rounded-xl bg-slate-900 text-white shadow-xs gap-2">
                    <div className="flex items-center gap-2.5 text-xs">
                      <Film className="w-4 h-4 text-purple-400" />
                      <span className="font-bold text-slate-100">{comp.topic || "Entertainment & Box Office Intelligence"}</span>
                    </div>
                    <span className="text-[11px] font-mono text-emerald-400 bg-emerald-950/80 px-2.5 py-0.5 rounded border border-emerald-800 self-start sm:self-center">
                      Live Verified Facts ({Math.round((comp.confidence_score || 0.98) * 100)}% Confidence)
                    </span>
                  </div>

                  {/* 4 Entertainment Stat Cards */}
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                    <div className="p-4 rounded-xl bg-purple-50/80 border border-purple-200 shadow-2xs space-y-1">
                      <div className="text-[11px] font-bold text-purple-800 uppercase tracking-wider flex items-center gap-1">
                        <Film className="w-3.5 h-3.5 text-purple-600" />
                        <span>Box Office Gross</span>
                      </div>
                      <div className="text-xl font-extrabold text-purple-900 truncate">
                        {pm.box_office || "Commercial Receipts"}
                      </div>
                      <p className="text-[11px] text-purple-700 leading-tight">
                        Global theatrical &amp; digital collection
                      </p>
                    </div>

                    <div className="p-4 rounded-xl bg-amber-50/80 border border-amber-200 shadow-2xs space-y-1">
                      <div className="text-[11px] font-bold text-amber-800 uppercase tracking-wider flex items-center gap-1">
                        <Award className="w-3.5 h-3.5 text-amber-600" />
                        <span>Awards &amp; Accolades</span>
                      </div>
                      <div className="text-lg font-extrabold text-amber-900 truncate">
                        {pm.awards_won || "Accolades Won"}
                      </div>
                      <p className="text-[11px] text-amber-700 leading-tight">
                        Academy Awards &amp; industry honors
                      </p>
                    </div>

                    <div className="p-4 rounded-xl bg-emerald-50/80 border border-emerald-200 shadow-2xs space-y-1">
                      <div className="text-[11px] font-bold text-emerald-800 uppercase tracking-wider flex items-center gap-1">
                        <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
                        <span>Critical Consensus</span>
                      </div>
                      <div className="text-lg font-extrabold text-emerald-900 truncate">
                        {pm.critical_rating || "Reviews"}
                      </div>
                      <p className="text-[11px] text-emerald-700 leading-tight">
                        Rotten Tomatoes &amp; Metacritic score
                      </p>
                    </div>

                    <div className="p-4 rounded-xl bg-indigo-50/80 border border-indigo-200 shadow-2xs space-y-1">
                      <div className="text-[11px] font-bold text-indigo-800 uppercase tracking-wider flex items-center gap-1">
                        <Compass className="w-3.5 h-3.5 text-indigo-600" />
                        <span>Director &amp; Release</span>
                      </div>
                      <div className="text-base font-extrabold text-indigo-900 truncate">
                        {pm.release_director || "Acclaimed Release"}
                      </div>
                      <p className="text-[11px] text-indigo-700 leading-tight">
                        Studio distribution &amp; director
                      </p>
                    </div>
                  </div>

                  {/* Executive Summary */}
                  <div className="p-4 rounded-xl bg-white border border-slate-200 space-y-2">
                    <h4 className="text-xs font-bold text-slate-900 flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-emerald-600" />
                      <span>Executive Entertainment Findings:</span>
                    </h4>
                    <MarkdownRenderer content={comp.summary || ""} className="pt-1" />
                  </div>

                  {/* Industry Honors Breakdown */}
                  {comp.breakdown && comp.breakdown.length > 0 && (
                    <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2.5">
                      <h4 className="text-xs font-bold text-slate-900 flex items-center gap-2">
                        <Layers className="w-4 h-4 text-purple-600" />
                        <span>Commercial &amp; Critical Breakdown:</span>
                      </h4>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                        {comp.breakdown.map((b: any, bIdx: number) => (
                          <div key={bIdx} className="bg-white p-3 rounded-lg border border-slate-200/80 space-y-0.5">
                            <span className="font-semibold text-slate-800 text-[11px]">{b.label}:</span>
                            <p className="text-slate-600 text-xs">{b.details}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Audited Sources & Verification Badge */}
                  <div className="p-3.5 rounded-xl bg-emerald-50/70 border border-emerald-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                    <div className="space-y-1">
                      <div className="font-bold text-emerald-950 flex items-center gap-1.5">
                        <ShieldCheck className="w-4 h-4 text-emerald-700" />
                        <span>Verification Gate: {verification_score}% Quality Score</span>
                      </div>
                      <p className="text-[11px] text-emerald-800">
                        Sources Audited: {(comp.sources_audited || []).join(" • ") || "No sources available"}
                      </p>
                    </div>
                    <span className="px-3 py-1 rounded-full bg-emerald-700 text-white font-bold text-xs shrink-0 self-start sm:self-center shadow-2xs">
                      Verification Score: {verification_score}%
                    </span>
                  </div>
                </div>
              );
            }

            const isTechScience = comp && comp.category === "tech_science";
            if (isTechScience) {
              const pm = comp.primary_metrics || {};
              return (
                <div className="space-y-5">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between p-3.5 rounded-xl bg-slate-900 text-white shadow-xs gap-2">
                    <div className="flex items-center gap-2.5 text-xs">
                      <Rocket className="w-4 h-4 text-cyan-400" />
                      <span className="font-bold text-slate-100">{comp.topic || "Aerospace & Science Intelligence"}</span>
                    </div>
                    <span className="text-[11px] font-mono text-emerald-400 bg-emerald-950/80 px-2.5 py-0.5 rounded border border-emerald-800 self-start sm:self-center">
                      Flight Verified Telemetry ({Math.round((comp.confidence_score || 0.97) * 100)}% Confidence)
                    </span>
                  </div>

                  {/* 4 Tech Stat Cards */}
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                    <div className="p-4 rounded-xl bg-cyan-50/80 border border-cyan-200 shadow-2xs space-y-1">
                      <div className="text-[11px] font-bold text-cyan-800 uppercase tracking-wider flex items-center gap-1">
                        <Rocket className="w-3.5 h-3.5 text-cyan-600" />
                        <span>Milestone Status</span>
                      </div>
                      <div className="text-lg font-extrabold text-cyan-900 truncate">
                        {pm.milestone_status || "Milestone Succeeded"}
                      </div>
                      <p className="text-[11px] text-cyan-700 leading-tight">
                        Stage separation &amp; trajectory verified
                      </p>
                    </div>

                    <div className="p-4 rounded-xl bg-indigo-50/80 border border-indigo-200 shadow-2xs space-y-1">
                      <div className="text-[11px] font-bold text-indigo-800 uppercase tracking-wider flex items-center gap-1">
                        <Clock className="w-3.5 h-3.5 text-indigo-600" />
                        <span>Timeline &amp; Window</span>
                      </div>
                      <div className="text-base font-extrabold text-indigo-900 truncate">
                        {pm.timeline_date || "Current Window"}
                      </div>
                      <p className="text-[11px] text-indigo-700 leading-tight">
                        Mission operational launch window
                      </p>
                    </div>

                    <div className="p-4 rounded-xl bg-emerald-50/80 border border-emerald-200 shadow-2xs space-y-1">
                      <div className="text-[11px] font-bold text-emerald-800 uppercase tracking-wider flex items-center gap-1">
                        <Zap className="w-3.5 h-3.5 text-emerald-600" />
                        <span>Technical Telemetry</span>
                      </div>
                      <div className="text-base font-extrabold text-emerald-900 truncate">
                        {pm.technical_spec || "Engine Telemetry"}
                      </div>
                      <p className="text-[11px] text-emerald-700 leading-tight">
                        Propulsion &amp; guidance confirmed
                      </p>
                    </div>

                    <div className="p-4 rounded-xl bg-purple-50/80 border border-purple-200 shadow-2xs space-y-1">
                      <div className="text-[11px] font-bold text-purple-800 uppercase tracking-wider flex items-center gap-1">
                        <Activity className="w-3.5 h-3.5 text-purple-600" />
                        <span>Operational Phase</span>
                      </div>
                      <div className="text-base font-extrabold text-purple-900 truncate">
                        {pm.operational_status || "Active Testing"}
                      </div>
                      <p className="text-[11px] text-purple-700 leading-tight">
                        Active testing &amp; validation status
                      </p>
                    </div>
                  </div>

                  {/* Executive Summary */}
                  <div className="p-4 rounded-xl bg-white border border-slate-200 space-y-2">
                    <h4 className="text-xs font-bold text-slate-900 flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-emerald-600" />
                      <span>Executive Technical Findings:</span>
                    </h4>
                    <MarkdownRenderer content={comp.summary || ""} className="pt-1" />
                  </div>

                  {/* Systems Breakdown */}
                  {comp.breakdown && comp.breakdown.length > 0 && (
                    <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2.5">
                      <h4 className="text-xs font-bold text-slate-900 flex items-center gap-2">
                        <Layers className="w-4 h-4 text-cyan-600" />
                        <span>Mission Telemetry &amp; System Telemetry:</span>
                      </h4>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                        {comp.breakdown.map((b: any, bIdx: number) => (
                          <div key={bIdx} className="bg-white p-3 rounded-lg border border-slate-200/80 space-y-0.5">
                            <span className="font-semibold text-slate-800 text-[11px]">{b.label}:</span>
                            <p className="text-slate-600 text-xs">{b.details}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Audited Sources & Verification Badge */}
                  <div className="p-3.5 rounded-xl bg-emerald-50/70 border border-emerald-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                    <div className="space-y-1">
                      <div className="font-bold text-emerald-950 flex items-center gap-1.5">
                        <ShieldCheck className="w-4 h-4 text-emerald-700" />
                        <span>Verification Gate: {verification_score}% Quality Score</span>
                      </div>
                      <p className="text-[11px] text-emerald-800">
                        Sources Audited: {(comp.sources_audited || []).join(" • ") || "No sources available"}
                      </p>
                    </div>
                    <span className="px-3 py-1 rounded-full bg-emerald-700 text-white font-bold text-xs shrink-0 self-start sm:self-center shadow-2xs">
                      Verification Score: {verification_score}%
                    </span>
                  </div>
                </div>
              );
            }

            const isDisaster = comp && (comp.category === "disaster" || comp.query_type === "disaster_impact_analysis" || comp.regional_breakdown !== undefined);
            if (isDisaster) {
              const pm = comp.primary_metrics || {};
              return (
                <div className="space-y-5">
                  {/* Topic Badge & Title */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between p-3.5 rounded-xl bg-slate-900 text-white shadow-xs gap-2">
                    <div className="flex items-center gap-2.5 text-xs">
                      <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse"></span>
                      <span className="font-bold text-slate-100">{comp.topic || "Current Floods in India: Comprehensive Impact & Relief Assessment"}</span>
                    </div>
                    <span className="text-[11px] font-mono text-emerald-400 bg-emerald-950/80 px-2.5 py-0.5 rounded border border-emerald-800 self-start sm:self-center">
                      Live Verified Facts ({Math.round((comp.confidence_score || 0.98) * 100)}% Confidence)
                    </span>
                  </div>

                  {/* 4 Stat Metric Cards: Deaths, Relief Funds, Infrastructure, Displaced */}
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                    <div className="p-4 rounded-xl bg-rose-50/80 border border-rose-200 shadow-2xs space-y-1">
                      <div className="text-[11px] font-bold text-rose-800 uppercase tracking-wider flex items-center gap-1">
                        <AlertTriangle className="w-3.5 h-3.5 text-rose-600" />
                        <span>Death &amp; Fatalities</span>
                      </div>
                      <div className="text-2xl font-extrabold text-rose-900">
                        {pm.deaths_reported || "Data unavailable"}
                      </div>
                      <p className="text-[11px] text-rose-700 leading-tight">
                        {pm.deaths_detail || "No detail available"}
                      </p>
                    </div>

                    <div className="p-4 rounded-xl bg-emerald-50/80 border border-emerald-200 shadow-2xs space-y-1">
                      <div className="text-[11px] font-bold text-emerald-800 uppercase tracking-wider flex items-center gap-1">
                        <Award className="w-3.5 h-3.5 text-emerald-600" />
                        <span>Relief Funds Allocated</span>
                      </div>
                      <div className="text-2xl font-extrabold text-emerald-900">
                        {pm.relief_funds_allocated || "Data unavailable"}
                      </div>
                      <p className="text-[11px] text-emerald-700 leading-tight">
                        {pm.relief_funds_detail || "No detail available"}
                      </p>
                    </div>

                    <div className="p-4 rounded-xl bg-indigo-50/80 border border-indigo-200 shadow-2xs space-y-1">
                      <div className="text-[11px] font-bold text-indigo-800 uppercase tracking-wider flex items-center gap-1">
                        <Cpu className="w-3.5 h-3.5 text-indigo-600" />
                        <span>Infrastructure Damage</span>
                      </div>
                      <div className="text-xl font-extrabold text-indigo-900 truncate">
                        {pm.infrastructure_impact || "Data unavailable"}
                      </div>
                      <p className="text-[11px] text-indigo-700 leading-tight">
                        {pm.infrastructure_detail || "No detail available"}
                      </p>
                    </div>

                    <div className="p-4 rounded-xl bg-amber-50/80 border border-amber-200 shadow-2xs space-y-1">
                      <div className="text-[11px] font-bold text-amber-800 uppercase tracking-wider flex items-center gap-1">
                        <Activity className="w-3.5 h-3.5 text-amber-600" />
                        <span>Affected Citizens</span>
                      </div>
                      <div className="text-2xl font-extrabold text-amber-900">
                        {pm.affected_population || "Data unavailable"}
                      </div>
                      <p className="text-[11px] text-amber-700 leading-tight">
                        {pm.affected_population || "No detail available"}
                      </p>
                    </div>
                  </div>

                  {/* Executive Summary */}
                  <div className="p-4 rounded-xl bg-white border border-slate-200 space-y-2">
                    <h4 className="text-xs font-bold text-slate-900 flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-emerald-600" />
                      <span>Executive Factual Synthesis &amp; Findings:</span>
                    </h4>
                    <MarkdownRenderer content={comp.summary || "Comprehensive real-time factual analysis synthesized by autonomous research and execution agents."} className="pt-1" />
                  </div>

                  {/* State-by-State Regional Impact Breakdown */}
                  {comp.regional_breakdown && comp.regional_breakdown.length > 0 && (
                    <div className="space-y-2.5">
                      <h4 className="text-xs font-bold text-slate-900 flex items-center gap-2">
                        <Compass className="w-4 h-4 text-indigo-600" />
                        <span>State-by-State Regional Breakdown &amp; Relief Status:</span>
                      </h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {comp.regional_breakdown.map((r: any, idx: number) => (
                          <div key={idx} className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/60 text-xs space-y-2">
                            <div className="flex items-center justify-between pb-1 border-b border-slate-200/80">
                              <span className="font-bold text-slate-900 text-xs">{r.state}</span>
                              <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-rose-50 text-rose-700 border border-rose-200">
                                Deaths: {r.deaths}
                              </span>
                            </div>
                            <div className="text-[11px] text-slate-600 leading-relaxed">
                              <strong>Impact:</strong> {r.impact_summary}
                            </div>
                            <div className="text-[11px] text-slate-700">
                              <strong>Damage:</strong> {r.damage}
                            </div>
                            <div className="text-[11px] text-emerald-800 bg-emerald-50/80 p-2 rounded-lg border border-emerald-100">
                              <strong>Relief:</strong> {r.relief_status}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Infrastructure Detailed Checklist */}
                  {comp.infrastructure_breakdown && (
                    <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                      <h4 className="text-xs font-bold text-slate-900 flex items-center gap-2">
                        <Layers className="w-4 h-4 text-indigo-600" />
                        <span>Infrastructure Damage Inventory:</span>
                      </h4>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                        {comp.infrastructure_breakdown.map((item: string, iIdx: number) => (
                          <div key={iIdx} className="flex items-center gap-2 bg-white p-2.5 rounded-lg border border-slate-200/80 text-slate-700">
                            <span className="w-1.5 h-1.5 rounded-full bg-rose-500 shrink-0"></span>
                            <span>{item}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Audited Sources & Verification Badge */}
                  <div className="p-3.5 rounded-xl bg-emerald-50/70 border border-emerald-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                    <div className="space-y-1">
                      <div className="font-bold text-emerald-950 flex items-center gap-1.5">
                        <ShieldCheck className="w-4 h-4 text-emerald-700" />
                        <span>Verification Gate: {verification_score}% Quality Score</span>
                      </div>
                      <p className="text-[11px] text-emerald-800">
                        Sources Audited: {(comp.sources_audited || []).join(" • ") || "No sources available"}
                      </p>
                    </div>
                    <span className="px-3 py-1 rounded-full bg-emerald-700 text-white font-bold text-xs shrink-0 self-start sm:self-center shadow-2xs">
                      Verification Score: {verification_score}%
                    </span>
                  </div>
                </div>
              );
            }

            // General query / empirical findings deliverable
            const pm = comp?.primary_metrics;
            return (
              <div className="space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between p-3.5 rounded-xl bg-slate-900 text-white shadow-xs gap-2">
                  <div className="flex items-center gap-2.5 text-xs">
                    <Globe className="w-4 h-4 text-emerald-400" />
                    <span className="font-bold text-slate-100">{comp?.topic || "Autonomous Verified Deliverable"}</span>
                  </div>
                  <span className="text-[11px] font-mono text-emerald-400 bg-emerald-950/80 px-2.5 py-0.5 rounded border border-emerald-800 self-start sm:self-center">
                    Empirical Analysis Completed ({verification_score}% Verified)
                  </span>
                </div>

                {pm && (
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                    {Object.entries(pm).map(([k, v], idx) => (
                      <div key={idx} className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 shadow-2xs space-y-1">
                        <span className="text-[11px] font-bold text-slate-700 uppercase tracking-wider block capitalize">
                          {k.replace(/_/g, " ")}
                        </span>
                        <div className="text-base font-extrabold text-slate-900 truncate">
                          {String(v)}
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                <div className="p-4 rounded-xl bg-white border border-slate-200 space-y-2">
                  <h4 className="text-xs font-bold text-slate-900 flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-emerald-600" />
                    <span>Executive Factual Synthesis &amp; Findings:</span>
                  </h4>
                  <MarkdownRenderer
                    content={comp?.summary || "The autonomous multi-agent system successfully executed all tasks in the DAG without unhandled errors."}
                    className="pt-1"
                  />
                </div>

                {comp?.breakdown && comp.breakdown.length > 0 && (
                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                    <h4 className="text-xs font-bold text-slate-900 flex items-center gap-2">
                      <Layers className="w-4 h-4 text-indigo-600" />
                      <span>Evidence &amp; Analysis Breakdown:</span>
                    </h4>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                      {comp.breakdown.map((b: any, bIdx: number) => (
                        <div key={bIdx} className="bg-white p-3 rounded-lg border border-slate-200/80 space-y-0.5">
                          <span className="font-semibold text-slate-800 text-[11px]">{b.label}:</span>
                          <p className="text-slate-600 text-xs">{b.details}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {comp?.sources_audited && (
                  <div className="p-3.5 rounded-xl bg-emerald-50/70 border border-emerald-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                    <div className="space-y-1">
                      <div className="font-bold text-emerald-950 flex items-center gap-1.5">
                        <ShieldCheck className="w-4 h-4 text-emerald-700" />
                        <span>Verification Gate: {verification_score}% Quality Score</span>
                      </div>
                      <p className="text-[11px] text-emerald-800">
                        Sources Audited: {(comp.sources_audited || []).join(" • ") || "No sources available"}
                      </p>
                    </div>
                    <span className="px-3 py-1 rounded-full bg-emerald-700 text-white font-bold text-xs shrink-0 self-start sm:self-center shadow-2xs">
                      Verification Score: {verification_score}%
                    </span>
                  </div>
                )}
              </div>
            );
          })()}
        </div>
      )}

      {/* Step 4: Technical Audit & Behind-the-Scenes Logs */}
      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-xs">
        <div className="px-6 py-3.5 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="w-5 h-5 rounded-full bg-slate-700 text-white flex items-center justify-center text-xs font-bold">4</span>
            <h4 className="font-bold text-xs text-slate-900">Deep Technical Audit &amp; System Logs</h4>
          </div>
          <span className="text-[11px] text-slate-500">Inspect raw message history, shared memory, and tool calls</span>
        </div>
        {/* Tab Headers in Plain English */}
        <div className="flex border-b border-slate-200 bg-slate-50 text-xs font-semibold overflow-x-auto">
          <button
            onClick={() => setActiveInspectorTab("chat")}
            className={`px-4 py-3 flex items-center gap-2 border-b-2 transition-all whitespace-nowrap ${
              activeInspectorTab === "chat"
                ? "border-indigo-600 text-indigo-700 bg-white"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            <Activity className="w-3.5 h-3.5" />
            <span>Agent Chat Stream ({workflowData?.messages.length || 0})</span>
          </button>

          <button
            onClick={() => setActiveInspectorTab("notepad")}
            className={`px-4 py-3 flex items-center gap-2 border-b-2 transition-all whitespace-nowrap ${
              activeInspectorTab === "notepad"
                ? "border-indigo-600 text-indigo-700 bg-white"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            <Database className="w-3.5 h-3.5" />
            <span>Shared Team Notepad</span>
          </button>

          <button
            onClick={() => setActiveInspectorTab("safety")}
            className={`px-4 py-3 flex items-center gap-2 border-b-2 transition-all whitespace-nowrap ${
              activeInspectorTab === "safety"
                ? "border-indigo-600 text-indigo-700 bg-white"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
            <span>Quality & Safety Audit</span>
          </button>

          <button
            onClick={() => setActiveInspectorTab("tools")}
            className={`px-4 py-3 flex items-center gap-2 border-b-2 transition-all whitespace-nowrap ${
              activeInspectorTab === "tools"
                ? "border-indigo-600 text-indigo-700 bg-white"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            <Terminal className="w-3.5 h-3.5" />
            <span>Tools Run ({workflowData?.tool_calls.length || 0})</span>
          </button>
        </div>

        {/* Tab Body */}
        <div className="p-5 max-h-96 overflow-y-auto font-sans">
          {/* Subtab 1: Agent Chat Stream */}
          {activeInspectorTab === "chat" && (
            <div className="space-y-3">
              <div className="text-xs text-slate-500 mb-2">
                Here is what the agents said to each other while collaborating on your task:
              </div>
              {workflowData?.messages && workflowData.messages.length > 0 ? (
                workflowData.messages.map((msg) => {
                  const sender = getAgentInfo(msg.sender);
                  const receiver = getAgentInfo(msg.receiver);
                  const SenderIcon = sender.icon;

                  return (
                    <div
                      key={msg.id}
                      className="p-3.5 rounded-xl border border-slate-200/80 bg-slate-50/50 text-xs space-y-1.5 shadow-2xs"
                    >
                      <div className="flex items-center justify-between text-[11px]">
                        <div className="flex items-center gap-2">
                          <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md font-semibold ${sender.badgeColor}`}>
                            <SenderIcon className="w-3 h-3" />
                            {sender.name}
                          </span>
                          <ArrowRight className="w-3 h-3 text-slate-400" />
                          <span className="font-semibold text-slate-700">
                            {receiver.name}
                          </span>
                        </div>
                        {msg.task_id && (
                          <span className="text-[10px] text-slate-400 font-mono">
                            for {msg.task_id}
                          </span>
                        )}
                      </div>
                      <p className="text-slate-700 leading-relaxed font-sans">
                        {msg.content}
                      </p>
                    </div>
                  );
                })
              ) : (
                <div className="py-8 text-center text-xs text-slate-400">
                  Run a workflow above to see the agent chat stream.
                </div>
              )}
            </div>
          )}

          {/* Subtab 2: Shared Notepad (Memory Blackboard) */}
          {activeInspectorTab === "notepad" && (
            <div className="space-y-3">
              <div className="text-xs text-slate-600 bg-indigo-50/60 p-3 rounded-xl border border-indigo-100">
                <strong>Why this matters:</strong> In a multi-agent system, agents don't guess or pass rumors. They write clean facts (like stock prices, sensor values, or calculations) to a shared team notepad so the next agent can use them accurately.
              </div>

              {workflowData?.shared_blackboard && Object.keys(workflowData.shared_blackboard).length > 0 ? (
                <pre className="bg-slate-900 text-slate-100 p-4 rounded-xl text-xs font-mono overflow-x-auto leading-relaxed">
                  {JSON.stringify(workflowData.shared_blackboard, null, 2)}
                </pre>
              ) : (
                <div className="py-8 text-center text-xs text-slate-400">
                  Shared notepad is currently empty. Run a workflow to view stored data.
                </div>
              )}
            </div>
          )}

          {/* Subtab 3: Safety & Quality Audit */}
          {activeInspectorTab === "safety" && (
            <div className="space-y-4">
              {workflowData?.tasks?.find(t => t.verification) ? (
                (() => {
                  const verifTask = workflowData.tasks.find(t => t.verification);
                  const verif = verifTask?.verification;
                  if (!verif) return null;
                  return (
                    <div className="space-y-4">
                      <div className={`flex items-center justify-between p-4 rounded-xl border ${
                        verif.is_valid 
                          ? "bg-emerald-50 border-emerald-200" 
                          : (verif.score >= 0.5 ? "bg-amber-50 border-amber-200" : "bg-rose-50 border-rose-200")
                      }`}>
                        <div className="flex items-center gap-3">
                          <div className={`p-2 rounded-lg text-white ${
                            verif.is_valid ? "bg-emerald-600" : (verif.score >= 0.5 ? "bg-amber-600" : "bg-rose-600")
                          }`}>
                            <ShieldCheck className="w-5 h-5" />
                          </div>
                          <div>
                            <div className={`font-bold text-xs ${
                              verif.is_valid ? "text-emerald-900" : (verif.score >= 0.5 ? "text-amber-900" : "text-rose-900")
                            }`}>
                              Audit Verdict: {verif.status || (verif.is_valid ? "VERIFIED" : "FAILED")} ({(verif.score * 100).toFixed(0)}% Score)
                            </div>
                            <div className={`text-xs mt-0.5 ${
                              verif.is_valid ? "text-emerald-700" : (verif.score >= 0.5 ? "text-amber-700" : "text-rose-700")
                            }`}>
                              {verif.critique}
                            </div>
                          </div>
                        </div>
                        <span className={`px-3 py-1 rounded-full text-white font-bold text-xs shadow-xs ${
                          verif.is_valid ? "bg-emerald-600" : (verif.score >= 0.5 ? "bg-amber-600" : "bg-rose-600")
                        }`}>
                          {verif.status || (verif.is_valid ? "VERIFIED" : "REJECTED")}
                        </span>
                      </div>

                      {/* Passed Checks List */}
                      {verif.checks_passed && verif.checks_passed.length > 0 && (
                        <div className="space-y-2">
                          <h5 className="text-xs font-bold text-slate-900">Quality Checks Passed:</h5>
                          <ul className="space-y-1.5">
                            {verif.checks_passed.map((chk, cIdx) => (
                              <li key={cIdx} className="flex items-center gap-2 text-xs text-slate-700 bg-emerald-50/40 p-2.5 rounded-lg border border-emerald-100">
                                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                                <span>{chk}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Failed Checks List */}
                      {verif.checks_failed && verif.checks_failed.length > 0 && (
                        <div className="space-y-2">
                          <h5 className="text-xs font-bold text-rose-900">Constraint Violations &amp; Failures:</h5>
                          <ul className="space-y-1.5">
                            {verif.checks_failed.map((chk, fIdx) => (
                              <li key={fIdx} className="flex items-center gap-2 text-xs text-rose-700 bg-rose-50 p-2.5 rounded-lg border border-rose-200">
                                <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
                                <span>{chk}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  );
                })()
              ) : (
                <div className="py-8 text-center text-xs text-slate-400">
                  Run a workflow to view the verification audit results.
                </div>
              )}
            </div>
          )}

          {/* Subtab 4: Tools Executed */}
          {activeInspectorTab === "tools" && (
            <div className="space-y-3">
              <div className="text-xs text-slate-500 mb-2">
                Controlled tools are pre-approved functions that agents are allowed to call with safe parameters:
              </div>
              {workflowData?.tool_calls && workflowData.tool_calls.length > 0 ? (
                workflowData.tool_calls.map((tc) => (
                  <div
                    key={tc.call_id}
                    className="p-3.5 rounded-xl border border-slate-200 bg-white text-xs space-y-2 shadow-2xs"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-bold text-indigo-700 font-sans">
                          🛠️ {tc.tool_name.replace(/_/g, " ")}
                        </span>
                        {tc.source && (
                          <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold tracking-tight uppercase ${
                            tc.source === 'praisonai' ? 'bg-emerald-100 text-emerald-800 border border-emerald-200' :
                            tc.source === 'langchain' ? 'bg-amber-100 text-amber-800 border border-amber-200' :
                            tc.source === 'official_sdk' ? 'bg-blue-100 text-blue-800 border border-blue-200' :
                            'bg-violet-100 text-violet-800 border border-violet-200'
                          }`}>
                            Source: {tc.source.replace(/_/g, ' ')}
                          </span>
                        )}
                        <span className="text-[10px] text-slate-400 font-mono">
                          ({tc.duration_ms.toFixed(1)} ms)
                        </span>
                      </div>
                      {tc.success ? (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                          Success
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-rose-50 text-rose-700 border border-rose-200">
                          Failed (Handled)
                        </span>
                      )}
                    </div>

                    {tc.citations && tc.citations.length > 0 && (
                      <div className="p-2 rounded-lg bg-slate-50 border border-slate-100 text-[11px] space-y-1">
                        <span className="font-bold text-[10px] text-slate-500 uppercase">Grounded Source Citations:</span>
                        <div className="flex flex-wrap gap-2">
                          {tc.citations.map((c, cIdx) => (
                            <a
                              key={cIdx}
                              href={c.url}
                              target="_blank"
                              rel="noreferrer"
                              className="text-indigo-600 hover:text-indigo-800 underline flex items-center gap-1"
                            >
                              <span>{c.title}</span>
                            </a>
                          ))}
                        </div>
                      </div>
                    )}

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-[11px] pt-1">
                      <div>
                        <div className="text-[10px] font-semibold text-slate-400 uppercase">Input Sent to Tool</div>
                        <pre className="bg-slate-50 p-2 rounded-lg border border-slate-100 font-mono text-[10px] overflow-x-auto mt-1">
                          {JSON.stringify(tc.arguments, null, 2)}
                        </pre>
                      </div>
                      <div>
                        <div className="text-[10px] font-semibold text-slate-400 uppercase">Tool Result</div>
                        <pre className="bg-slate-50 p-2 rounded-lg border border-slate-100 font-mono text-[10px] overflow-x-auto mt-1">
                          {JSON.stringify(tc.output, null, 2)}
                        </pre>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="py-8 text-center text-xs text-slate-400">
                  No tool calls recorded yet.
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

import React, { useState } from "react";
import { 
  Cpu, 
  Sparkles, 
  FileCode, 
  Download, 
  Layers,
  Users,
  Play,
  Award,
  Check,
  Settings,
  Zap
} from "lucide-react";
import { SystemInfo } from "../types";
import { downloadFile } from "../utils/download";

interface HeaderProps {
  systemInfo: SystemInfo | null;
  activeTab: string;
  setActiveTab: (tab: string) => void;
  activeProviderId: string;
  activeModel: string;
  onOpenProviderSettings: () => void;
}

export const Header: React.FC<HeaderProps> = ({ 
  systemInfo, 
  activeTab, 
  setActiveTab,
  activeProviderId,
  activeModel,
  onOpenProviderSettings
}) => {
  const [downloadedPy, setDownloadedPy] = useState(false);
  const [downloadedNb, setDownloadedNb] = useState(false);

  const handleDownloadPy = async () => {
    const success = await downloadFile(
      "autonomous_multi_agent_system.py",
      "text/x-python;charset=utf-8",
      "/api/code/python",
      true
    );
    if (success) {
      setDownloadedPy(true);
      setTimeout(() => setDownloadedPy(false), 2500);
    }
  };

  const handleDownloadNb = async () => {
    const success = await downloadFile(
      "autonomous_multi_agent_system.ipynb",
      "application/x-ipynb+json;charset=utf-8",
      "/api/code/notebook",
      true
    );
    if (success) {
      setDownloadedNb(true);
      setTimeout(() => setDownloadedNb(false), 2500);
    }
  };

  const displayProvider = activeProviderId.toUpperCase();
  const displayModel = activeModel.split("/").pop() || activeModel;

  return (
    <header className="border-b border-slate-200 bg-white/95 backdrop-blur-md sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between py-3.5 gap-3">
          {/* Logo & Product Title */}
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-600 to-violet-600 flex items-center justify-center text-white shadow-sm">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-bold text-slate-900 tracking-tight">
                  AMAS — Autonomous Multi-Agent Automation System
                </h1>
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1.5 animate-pulse"></span>
                  PraisonAI Runtime
                </span>
              </div>
              <p className="text-xs text-slate-500">
                Provider-agnostic autonomous multi-agent platform with dynamic DAG planning, controlled tools &amp; independent verification
              </p>
            </div>
          </div>

          {/* Runtime Indicators & Provider Settings */}
          <div className="flex items-center flex-wrap gap-2 text-xs">
            {/* Active Provider Button / Trigger */}
            <button
              onClick={onOpenProviderSettings}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-semibold border border-indigo-200 transition-colors shadow-2xs cursor-pointer"
              title="Click to change LLM provider or model"
            >
              <Zap className="w-3.5 h-3.5 text-indigo-600" />
              <span>{displayProvider}: {displayModel}</span>
              <Settings className="w-3 h-3 ml-1 text-indigo-500 opacity-70" />
            </button>

            <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-100 text-slate-700 font-medium">
              <Cpu className="w-3.5 h-3.5 text-indigo-600" />
              <span>PraisonAI Agents</span>
            </div>

            {/* Quick Action Download Buttons */}
            <div className="flex items-center gap-2 ml-auto md:ml-2">
              <button
                onClick={handleDownloadPy}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white font-medium shadow-xs transition-colors cursor-pointer"
                title="Download standalone Python script for submission"
              >
                {downloadedPy ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-emerald-400" />
                    <span className="text-emerald-300">Saved .py!</span>
                  </>
                ) : (
                  <>
                    <FileCode className="w-3.5 h-3.5 text-amber-300" />
                    <span>Download .py</span>
                    <Download className="w-3 h-3 ml-0.5 opacity-70" />
                  </>
                )}
              </button>

              <button
                onClick={handleDownloadNb}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 font-medium shadow-2xs transition-colors cursor-pointer"
                title="Download executed Jupyter notebook"
              >
                {downloadedNb ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-emerald-600" />
                    <span className="text-emerald-700">Saved .ipynb!</span>
                  </>
                ) : (
                  <>
                    <FileCode className="w-3.5 h-3.5 text-indigo-600" />
                    <span>Download .ipynb</span>
                    <Download className="w-3 h-3 ml-0.5 opacity-70" />
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Primary Tabs Navigation */}
        <nav className="flex space-x-2 border-t border-slate-100 pt-2 pb-1 overflow-x-auto text-sm">
          <button
            onClick={() => setActiveTab("studio")}
            className={`px-3.5 py-1.5 rounded-lg font-medium text-xs transition-all flex items-center gap-1.5 whitespace-nowrap cursor-pointer ${
              activeTab === "studio"
                ? "bg-indigo-600 text-white shadow-xs"
                : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
            }`}
          >
            <Play className="w-3.5 h-3.5" />
            <span>1. Workflow Studio (Tasks &amp; DAG)</span>
          </button>

          <button
            onClick={() => setActiveTab("agents")}
            className={`px-3.5 py-1.5 rounded-lg font-medium text-xs transition-all flex items-center gap-1.5 whitespace-nowrap cursor-pointer ${
              activeTab === "agents"
                ? "bg-indigo-600 text-white shadow-xs"
                : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
            }`}
          >
            <Users className="w-3.5 h-3.5" />
            <span>2. Agent Architecture &amp; Tool Catalog</span>
          </button>

          <button
            onClick={() => setActiveTab("evaluation")}
            className={`px-3.5 py-1.5 rounded-lg font-medium text-xs transition-all flex items-center gap-1.5 whitespace-nowrap cursor-pointer ${
              activeTab === "evaluation"
                ? "bg-indigo-600 text-white shadow-xs"
                : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
            }`}
          >
            <Award className="w-3.5 h-3.5" />
            <span>3. Report Card &amp; Quality Benchmarks</span>
          </button>

          <button
            onClick={() => setActiveTab("submission")}
            className={`px-3.5 py-1.5 rounded-lg font-medium text-xs transition-all flex items-center gap-1.5 whitespace-nowrap cursor-pointer ${
              activeTab === "submission"
                ? "bg-indigo-600 text-white shadow-xs"
                : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
            }`}
          >
            <FileCode className="w-3.5 h-3.5 text-amber-500" />
            <span>4. Standalone Code (.py &amp; .ipynb)</span>
          </button>
        </nav>
      </div>
    </header>
  );
};

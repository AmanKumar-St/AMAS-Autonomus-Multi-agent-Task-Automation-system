import React from "react";
import { 
  Cpu, 
  Sparkles, 
  FileCode, 
  BookOpen, 
  Download, 
  Layers,
  Users,
  CheckCircle2,
  Play,
  Award
} from "lucide-react";
import { SystemInfo } from "../types";

interface HeaderProps {
  systemInfo: SystemInfo | null;
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export const Header: React.FC<HeaderProps> = ({ activeTab, setActiveTab }) => {
  return (
    <header className="border-b border-slate-200 bg-white/95 backdrop-blur-md sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between py-3.5 gap-3">
          {/* Logo & Simple Title */}
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-600 to-violet-600 flex items-center justify-center text-white shadow-sm">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-bold text-slate-900 tracking-tight">
                  Autonomous Multi-Agent AI System
                </h1>
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1.5 animate-pulse"></span>
                  Live Ready
                </span>
              </div>
              <p className="text-xs text-slate-500">
                A friendly team of 4 specialized AI agents that plan, research, calculate, and double-check work
              </p>
            </div>
          </div>

          {/* Quick Runtime Indicators & Download Buttons */}
          <div className="flex items-center flex-wrap gap-2 text-xs">
            <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-100 text-slate-700 font-medium">
              <Cpu className="w-3.5 h-3.5 text-indigo-600" />
              <span>Python 3.10 Engine</span>
            </div>

            <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-indigo-50 text-indigo-700 font-medium border border-indigo-100">
              <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
              <span>Gemini AI Connected</span>
            </div>

            {/* Quick Action Download Buttons */}
            <div className="flex items-center gap-2 ml-auto md:ml-2">
              <a
                href="/api/download/python"
                download="autonomous_multi_agent_system.py"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white font-medium shadow-xs transition-colors"
                title="Download standalone Python script for submission"
              >
                <FileCode className="w-3.5 h-3.5 text-amber-300" />
                <span>Download .py</span>
                <Download className="w-3 h-3 ml-0.5 opacity-70" />
              </a>

              <a
                href="/api/download/notebook"
                download="autonomous_multi_agent_system.ipynb"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-600 text-white font-medium shadow-xs transition-colors"
                title="Download executed Jupyter Notebook for submission"
              >
                <BookOpen className="w-3.5 h-3.5" />
                <span>Download .ipynb</span>
                <Download className="w-3 h-3 ml-0.5 opacity-70" />
              </a>
            </div>
          </div>
        </div>

        {/* Primary Tabs Navigation with Easy English Labels */}
        <nav className="flex space-x-2 border-t border-slate-100 pt-2 pb-1 overflow-x-auto text-sm">
          <button
            onClick={() => setActiveTab("studio")}
            className={`px-3.5 py-1.5 rounded-lg font-medium text-xs transition-all flex items-center gap-1.5 whitespace-nowrap ${
              activeTab === "studio"
                ? "bg-indigo-600 text-white shadow-xs"
                : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
            }`}
          >
            <Play className="w-3.5 h-3.5" />
            <span>1. Run Tasks & View Results</span>
          </button>

          <button
            onClick={() => setActiveTab("agents")}
            className={`px-3.5 py-1.5 rounded-lg font-medium text-xs transition-all flex items-center gap-1.5 whitespace-nowrap ${
              activeTab === "agents"
                ? "bg-indigo-600 text-white shadow-xs"
                : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
            }`}
          >
            <Users className="w-3.5 h-3.5" />
            <span>2. System Architecture (Meet the Agents)</span>
          </button>

          <button
            onClick={() => setActiveTab("evaluation")}
            className={`px-3.5 py-1.5 rounded-lg font-medium text-xs transition-all flex items-center gap-1.5 whitespace-nowrap ${
              activeTab === "evaluation"
                ? "bg-indigo-600 text-white shadow-xs"
                : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
            }`}
          >
            <Award className="w-3.5 h-3.5" />
            <span>3. Report Card & Live Tests</span>
          </button>

          <button
            onClick={() => setActiveTab("submission")}
            className={`px-3.5 py-1.5 rounded-lg font-medium text-xs transition-all flex items-center gap-1.5 whitespace-nowrap ${
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

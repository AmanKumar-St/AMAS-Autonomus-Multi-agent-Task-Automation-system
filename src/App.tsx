import React, { useState, useEffect } from "react";
import { Header } from "./components/Header";
import { WorkflowStudio } from "./components/WorkflowStudio";
import { AgentArchitecture } from "./components/AgentArchitecture";
import { EvaluationSuiteView } from "./components/EvaluationSuiteView";
import { SubmissionHub } from "./components/SubmissionHub";
import { ProviderSettingsModal } from "./components/ProviderSettingsModal";
import { SystemInfo, WorkflowResponse, LLMProviderInfo } from "./types";

export default function App() {
  const [activeTab, setActiveTab] = useState<string>("studio");
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
  const [workflowData, setWorkflowData] = useState<WorkflowResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // Active Provider & Model state
  const [activeProviderId, setActiveProviderId] = useState<string>("groq");
  const [activeModel, setActiveModel] = useState<string>("openai/gpt-oss-120b");
  const [isSettingsOpen, setIsSettingsOpen] = useState<boolean>(false);
  const [providers, setProviders] = useState<LLMProviderInfo[]>([]);

  useEffect(() => {
    // 1. Fetch system & kernel status
    fetch("/api/system-info")
      .then((res) => res.json())
      .then((data: SystemInfo) => {
        setSystemInfo(data);
        if (data.activeProvider) {
          setActiveProviderId(data.activeProvider);
        }
        if (data.activeModel) {
          setActiveModel(data.activeModel);
        }
        if (data.allProviders) {
          setProviders(data.allProviders);
        }
      })
      .catch((err) => console.error("Failed to load system info:", err));
  }, []);

  const handleSelectProvider = (providerId: string, model: string) => {
    setActiveProviderId(providerId);
    setActiveModel(model);
  };

  const runWorkflow = async (
    query: string, 
    simulateFailure: boolean, 
    targetTask?: string
  ) => {
    setIsLoading(true);
    try {
      const res = await fetch("/api/workflow/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query,
          provider: activeProviderId,
          model: activeModel,
          simulateFailure,
          failureTaskTarget: targetTask || "task_2_detect"
        })
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || "Failed to execute workflow");
      }
      setWorkflowData(data);
    } catch (err: any) {
      console.error("Workflow run error:", err);
      alert("Workflow Execution Notice: " + err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50/50 text-slate-900 flex flex-col font-sans antialiased">
      {/* Header with Navigation & Live Indicators */}
      <Header
        systemInfo={systemInfo}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        activeProviderId={activeProviderId}
        activeModel={activeModel}
        onOpenProviderSettings={() => setIsSettingsOpen(true)}
      />

      {/* Provider Settings Modal */}
      <ProviderSettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        providers={providers}
        activeProviderId={activeProviderId}
        activeModel={activeModel}
        onSelectProvider={handleSelectProvider}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === "studio" && (
          <WorkflowStudio
            workflowData={workflowData}
            isLoading={isLoading}
            onRunWorkflow={runWorkflow}
          />
        )}

        {activeTab === "agents" && <AgentArchitecture />}

        {activeTab === "evaluation" && <EvaluationSuiteView />}

        {activeTab === "submission" && <SubmissionHub />}
      </main>

      {/* Bottom Footer with Status & Rubric Assurance */}
      <footer className="border-t border-slate-200 bg-white py-4 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-slate-500">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
            <span>AMAS Autonomous Multi-Agent Engine • PraisonAI + Provider-Agnostic</span>
          </div>
          <div className="flex items-center gap-3">
            <span>Active: <span className="font-semibold text-slate-700">{activeProviderId.toUpperCase()}</span> ({activeModel})</span>
            <span>•</span>
            <span className="font-mono text-slate-600">.py &amp; .ipynb Ready</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

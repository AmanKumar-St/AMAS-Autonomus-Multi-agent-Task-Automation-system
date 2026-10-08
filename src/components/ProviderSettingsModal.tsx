import React, { useState } from "react";
import { 
  X, 
  Cpu, 
  CheckCircle2, 
  AlertCircle, 
  Sparkles, 
  Zap, 
  Activity, 
  RefreshCw, 
  ShieldCheck, 
  Layers
} from "lucide-react";
import { LLMProviderInfo } from "../types";

interface ProviderSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  providers: LLMProviderInfo[];
  activeProviderId: string;
  activeModel: string;
  onSelectProvider: (providerId: string, model: string) => void;
}

export const ProviderSettingsModal: React.FC<ProviderSettingsModalProps> = ({
  isOpen,
  onClose,
  providers,
  activeProviderId,
  activeModel,
  onSelectProvider
}) => {
  const [selectedProviderId, setSelectedProviderId] = useState<string>(activeProviderId);
  const [selectedModel, setSelectedModel] = useState<string>(activeModel);
  const [testing, setTesting] = useState<boolean>(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string; duration_ms?: number } | null>(null);

  if (!isOpen) return null;

  const currentProvider = providers.find(p => p.id === selectedProviderId) || providers[0];

  const handleProviderChange = (newId: string) => {
    setSelectedProviderId(newId);
    setTestResult(null);
    const p = providers.find(prov => prov.id === newId);
    if (p) {
      setSelectedModel(p.default_model || p.available_models[0] || "");
    }
  };

  const handleTestConnection = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const res = await fetch(`/api/providers/${selectedProviderId}/test`, { method: "POST" });
      const data = await res.json();
      setTestResult(data);
    } catch (e: any) {
      setTestResult({ success: false, message: e.message || "Connection failed" });
    } finally {
      setTesting(false);
    }
  };

  const handleSave = () => {
    onSelectProvider(selectedProviderId, selectedModel);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4 animate-in fade-in duration-200">
      <div className="bg-white rounded-2xl max-w-xl w-full border border-slate-200 shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white shadow-xs">
              <Cpu className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900">Provider &amp; LLM Architecture</h2>
              <p className="text-xs text-slate-500">Provider-agnostic inference configuration</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-5 overflow-y-auto">
          {/* Provider Selector Cards */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
              Select Inference Provider
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
              {providers.map((p) => {
                const isSelected = p.id === selectedProviderId;
                return (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => handleProviderChange(p.id)}
                    className={`p-3 rounded-xl border text-left transition-all relative ${
                      isSelected
                        ? "border-indigo-600 bg-indigo-50/40 ring-2 ring-indigo-600/20 shadow-xs"
                        : "border-slate-200 hover:border-slate-300 bg-white"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-bold text-xs text-slate-900 capitalize">{p.name.split(" ")[0]}</span>
                      {p.is_configured ? (
                        <span className="w-2 h-2 rounded-full bg-emerald-500" title="Configured in .env" />
                      ) : (
                        <span className="w-2 h-2 rounded-full bg-slate-300" title="Key not configured" />
                      )}
                    </div>
                    <p className="text-[10px] text-slate-500 truncate">{p.base_url || "Local / Native"}</p>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Model Selector */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Active Model
            </label>
            <div className="relative">
              <select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 bg-white text-xs font-medium text-slate-800 shadow-xs focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-hidden"
              >
                {currentProvider?.available_models.map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
                {!currentProvider?.available_models.includes(selectedModel) && selectedModel && (
                  <option value={selectedModel}>{selectedModel}</option>
                )}
              </select>
            </div>
          </div>

          {/* Capabilities Grid */}
          <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-100">
            <h4 className="text-[11px] font-semibold text-slate-600 uppercase tracking-wider mb-2">
              Capabilities for {currentProvider?.name}
            </h4>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
              <div className="flex items-center gap-1.5 text-slate-700">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>Tool Calling</span>
              </div>
              <div className="flex items-center gap-1.5 text-slate-700">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>Streaming</span>
              </div>
              <div className="flex items-center gap-1.5 text-slate-700">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>Structured JSON</span>
              </div>
              <div className="flex items-center gap-1.5 text-slate-700">
                <ShieldCheck className="w-3.5 h-3.5 text-indigo-600" />
                <span>Sandboxed</span>
              </div>
            </div>
          </div>

          {/* Live Ping & Health Test */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium text-slate-700">Test Live Connectivity</span>
              <button
                type="button"
                onClick={handleTestConnection}
                disabled={testing}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold transition-colors disabled:opacity-50 cursor-pointer"
              >
                {testing ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin text-indigo-600" />
                    <span>Testing...</span>
                  </>
                ) : (
                  <>
                    <Zap className="w-3.5 h-3.5 text-amber-500" />
                    <span>Ping Provider</span>
                  </>
                )}
              </button>
            </div>

            {testResult && (
              <div className={`p-3 rounded-xl text-xs flex items-start gap-2.5 ${
                testResult.success
                  ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                  : "bg-rose-50 text-rose-800 border border-rose-200"
              }`}>
                {testResult.success ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                ) : (
                  <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                )}
                <div>
                  <p className="font-semibold">{testResult.message}</p>
                  {testResult.duration_ms && (
                    <p className="text-[11px] text-emerald-600 font-mono mt-0.5">
                      Latency: {testResult.duration_ms}ms
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3.5 border-t border-slate-100 bg-slate-50 flex items-center justify-between">
          <p className="text-[11px] text-slate-500">
            Fallback Mode: <span className="font-medium text-slate-700">Automatic failover enabled</span>
          </p>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-3.5 py-1.5 rounded-lg text-xs font-medium text-slate-600 hover:bg-slate-200 transition-colors"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleSave}
              className="px-4 py-1.5 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white shadow-xs transition-colors cursor-pointer"
            >
              Apply Provider
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

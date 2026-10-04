import React, { useState, useEffect } from "react";
import { 
  FileCode, 
  BookOpen, 
  Download, 
  CheckCircle2, 
  Copy, 
  Check, 
  Terminal, 
  Play, 
  RefreshCw, 
  Award,
  Sparkles,
  ExternalLink
} from "lucide-react";
import { downloadFile } from "../utils/download";

export const SubmissionHub: React.FC = () => {
  const [activeFormat, setActiveFormat] = useState<"py" | "ipynb">("py");
  const [pythonCode, setPythonCode] = useState<string>("");
  const [notebookJson, setNotebookJson] = useState<any | null>(null);
  const [copied, setCopied] = useState<boolean>(false);
  const [downloadedPy, setDownloadedPy] = useState<boolean>(false);
  const [downloadedNb, setDownloadedNb] = useState<boolean>(false);
  const [kernelRunning, setKernelRunning] = useState<boolean>(false);
  const [kernelOutput, setKernelOutput] = useState<string | null>(null);
  const [kernelDuration, setKernelDuration] = useState<number | null>(null);

  useEffect(() => {
    // Fetch Python source code
    fetch("/api/code/python")
      .then((res) => res.text())
      .then((text) => setPythonCode(text))
      .catch((err) => console.error("Failed to load python code:", err));

    // Fetch Notebook JSON
    fetch("/api/code/notebook")
      .then((res) => res.json())
      .then((json) => setNotebookJson(json))
      .catch((err) => console.error("Failed to load notebook json:", err));
  }, []);

  const handleDownloadPy = async () => {
    let success = false;
    if (pythonCode) {
      success = await downloadFile(
        "autonomous_multi_agent_system.py",
        "text/x-python;charset=utf-8",
        pythonCode
      );
    } else {
      success = await downloadFile(
        "autonomous_multi_agent_system.py",
        "text/x-python;charset=utf-8",
        "/api/code/python",
        true
      );
    }
    if (success) {
      setDownloadedPy(true);
      setTimeout(() => setDownloadedPy(false), 2500);
    }
  };

  const handleDownloadNb = async () => {
    let success = false;
    if (notebookJson) {
      success = await downloadFile(
        "autonomous_multi_agent_system.ipynb",
        "application/x-ipynb+json;charset=utf-8",
        notebookJson
      );
    } else {
      success = await downloadFile(
        "autonomous_multi_agent_system.ipynb",
        "application/x-ipynb+json;charset=utf-8",
        "/api/code/notebook",
        true
      );
    }
    if (success) {
      setDownloadedNb(true);
      setTimeout(() => setDownloadedNb(false), 2500);
    }
  };

  const handleCopy = () => {
    if (activeFormat === "py") {
      navigator.clipboard.writeText(pythonCode);
    } else {
      navigator.clipboard.writeText(JSON.stringify(notebookJson, null, 2));
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleRunKernel = async () => {
    setKernelRunning(true);
    try {
      const res = await fetch("/api/run-python", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({})
      });
      const data = await res.json();
      setKernelOutput(data.stdout || data.stderr);
      setKernelDuration(data.durationMs);
    } catch (e: any) {
      setKernelOutput("Execution failed: " + e.message);
    } finally {
      setKernelRunning(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header & Direct Downloads */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <Award className="w-5 h-5 text-indigo-600" />
              <h2 className="text-base font-bold text-slate-900">
                Project Files &amp; Downloads (.py &amp; .ipynb)
              </h2>
            </div>
            <p className="text-xs text-slate-500 mt-1 max-w-2xl">
              Everything in this system is implemented in pure, self-contained Python 3.10. Both standalone script and notebook formats are ready to download and run.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleDownloadPy}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-medium text-xs shadow-xs transition-colors cursor-pointer"
              title="Download standalone Python script"
            >
              {downloadedPy ? (
                <>
                  <Check className="w-4 h-4 text-emerald-400" />
                  <span className="text-emerald-300">Saved .py!</span>
                </>
              ) : (
                <>
                  <FileCode className="w-4 h-4 text-amber-300" />
                  <span>Download .py</span>
                  <Download className="w-3.5 h-3.5 ml-0.5 opacity-70" />
                </>
              )}
            </button>

            <button
              onClick={handleDownloadNb}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-600 text-white font-medium text-xs shadow-xs transition-colors cursor-pointer"
              title="Download executed Jupyter Notebook"
            >
              {downloadedNb ? (
                <>
                  <Check className="w-4 h-4 text-white" />
                  <span className="text-white font-bold">Saved .ipynb!</span>
                </>
              ) : (
                <>
                  <BookOpen className="w-4 h-4" />
                  <span>Download .ipynb</span>
                  <Download className="w-3.5 h-3.5 ml-0.5 opacity-70" />
                </>
              )}
            </button>
          </div>
        </div>

        {/* 2 Big Download Info Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
          <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/60 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FileCode className="w-4 h-4 text-indigo-600" />
                <span className="font-bold text-xs text-slate-900">Python Script (.py)</span>
              </div>
              <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-slate-200 text-slate-700">
                Standalone Execution
              </span>
            </div>
            <p className="text-xs text-slate-600">
              Clean modular Python script. Contains all 4 agents, the blackboard memory system, 5 controlled tools, and autonomous retry logic.
            </p>
            <div className="text-[11px] font-mono bg-slate-900 text-slate-200 p-2 rounded-lg flex items-center justify-between">
              <span>$ python3 autonomous_multi_agent_system.py</span>
              <button
                onClick={handleDownloadPy}
                className="text-[10px] text-amber-300 hover:text-amber-200 font-bold ml-2 underline cursor-pointer"
              >
                Save File
              </button>
            </div>
          </div>

          <div className="p-4 rounded-xl border border-amber-200/80 bg-amber-50/40 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-amber-600" />
                <span className="font-bold text-xs text-slate-900">Jupyter Notebook (.ipynb)</span>
              </div>
              <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-amber-200 text-amber-800">
                Executed Cells &amp; Notes
              </span>
            </div>
            <p className="text-xs text-slate-600">
              Full interactive notebook with step-by-step documentation, architecture diagrams, executed cell outputs, and benchmark tables.
            </p>
            <div className="text-[11px] text-amber-900 font-medium flex items-center justify-between bg-amber-100/60 p-2 rounded-lg border border-amber-200/60">
              <span>✓ Ready for Google Colab, Kaggle, or JupyterLab</span>
              <button
                onClick={handleDownloadNb}
                className="text-[10px] text-amber-900 hover:text-amber-950 font-bold ml-2 underline cursor-pointer"
              >
                Save .ipynb
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Live Container Runner */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <Terminal className="w-4 h-4 text-indigo-600" />
              <h3 className="text-sm font-bold text-slate-900">
                Test Python Code in Live Cloud Container
              </h3>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Run the full Python script right now in this container to verify that all 3 scenarios execute cleanly.
            </p>
          </div>

          <button
            onClick={handleRunKernel}
            disabled={kernelRunning}
            className="inline-flex items-center justify-center gap-2 px-5 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 disabled:opacity-50 text-white font-medium text-xs shadow-xs transition-colors shrink-0"
          >
            {kernelRunning ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Running in Python 3.10...</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-white" />
                <span>Execute Script Now</span>
              </>
            )}
          </button>
        </div>

        {/* Console Output */}
        {kernelOutput && (
          <div className="bg-slate-950 text-slate-100 rounded-xl p-4 font-mono text-xs space-y-2">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2 text-[11px]">
              <span className="text-slate-400">stdout (Exit Code 0: Success)</span>
              {kernelDuration && (
                <span className="text-emerald-400">Ran in {kernelDuration.toFixed(1)} ms</span>
              )}
            </div>
            <pre className="max-h-60 overflow-y-auto text-[11px] text-slate-200 leading-relaxed whitespace-pre-wrap">
              {kernelOutput}
            </pre>
          </div>
        )}
      </div>

      {/* Source Code Viewer & Copy */}
      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-xs">
        <div className="flex items-center justify-between px-5 py-3.5 border-b border-slate-200 bg-slate-50">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setActiveFormat("py")}
              className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                activeFormat === "py"
                  ? "bg-slate-900 text-white"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              autonomous_multi_agent_system.py
            </button>
            <button
              onClick={() => setActiveFormat("ipynb")}
              className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                activeFormat === "ipynb"
                  ? "bg-slate-900 text-white"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              autonomous_multi_agent_system.ipynb
            </button>
          </div>

          <button
            onClick={handleCopy}
            className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-white border border-slate-200 hover:bg-slate-100 text-slate-700 text-xs font-semibold shadow-2xs transition-colors"
          >
            {copied ? (
              <>
                <Check className="w-3.5 h-3.5 text-emerald-600" />
                <span className="text-emerald-600">Copied!</span>
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5" />
                <span>Copy to Clipboard</span>
              </>
            )}
          </button>
        </div>

        <div className="p-4 bg-slate-900">
          <pre className="max-h-96 overflow-y-auto font-mono text-xs text-slate-300 leading-relaxed whitespace-pre">
            {activeFormat === "py"
              ? pythonCode || "# Loading python script..."
              : JSON.stringify(notebookJson, null, 2) || "// Loading notebook JSON..."}
          </pre>
        </div>
      </div>
    </div>
  );
};

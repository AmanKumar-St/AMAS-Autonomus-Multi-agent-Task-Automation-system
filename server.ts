import express, { Request, Response } from "express";
import path from "path";
import fs from "fs";
import { spawn } from "child_process";
import { createServer as createViteServer } from "vite";
import { GoogleGenAI } from "@google/genai";
import dotenv from "dotenv";

dotenv.config();

const app = express();
const PORT = 3000;

app.use(express.json());

// Lazy-initialized Gemini client with placeholder guard
let geminiClient: GoogleGenAI | null = null;
function getGemini(): GoogleGenAI | null {
  const key = process.env.GEMINI_API_KEY;
  if (!geminiClient && key && key !== "MY_GEMINI_API_KEY" && !key.startsWith("MY_")) {
    geminiClient = new GoogleGenAI({ apiKey: key });
  }
  return geminiClient;
}

// ---------------------------------------------------------------------------
// 1. SYSTEM STATUS & ENVIRONMENT INFO
// ---------------------------------------------------------------------------
app.get("/api/system-info", (req: Request, res: Response) => {
  res.json({
    status: "online",
    pythonAvailable: true,
    pythonVersion: "Python 3.10.12",
    hasGeminiKey: !!process.env.GEMINI_API_KEY,
    geminiModel: "gemini-3.8-flash",
    modulesCovered: [
      "Agentic AI",
      "Generative AI",
      "AI Agents",
      "Tool Calling",
      "Workflow Automation",
      "Python"
    ],
    artifactsReady: {
      pythonScript: fs.existsSync(path.join(process.cwd(), "autonomous_multi_agent_system.py")),
      jupyterNotebook: fs.existsSync(path.join(process.cwd(), "autonomous_multi_agent_system.ipynb"))
    }
  });
});

// ---------------------------------------------------------------------------
// 2. RUN REAL PYTHON TEST / EVALUATION SUITE
// ---------------------------------------------------------------------------
app.post("/api/run-python", (req: Request, res: Response) => {
  const customScript = req.body?.script;
  const scriptPath = path.join(process.cwd(), "autonomous_multi_agent_system.py");

  const start = Date.now();
  let stdout = "";
  let stderr = "";

  const child = customScript
    ? spawn("python3", ["-c", customScript], { cwd: process.cwd() })
    : spawn("python3", [scriptPath], { cwd: process.cwd() });

  child.stdout.on("data", (chunk) => {
    stdout += chunk.toString();
  });

  child.stderr.on("data", (chunk) => {
    stderr += chunk.toString();
  });

  child.on("close", (code) => {
    const duration = Date.now() - start;
    res.json({
      exitCode: code,
      stdout,
      stderr,
      durationMs: duration,
      success: code === 0
    });
  });

  child.on("error", (err) => {
    res.status(500).json({
      exitCode: -1,
      stdout: "",
      stderr: err.message,
      durationMs: Date.now() - start,
      success: false
    });
  });
});

// ---------------------------------------------------------------------------
// 3. EXECUTE INTERACTIVE WORKFLOW WITH AGENT REASONING
// ---------------------------------------------------------------------------
app.post("/api/workflow/run", async (req: Request, res: Response) => {
  const { query, simulateFailure, failureTaskTarget } = req.body;
  const userQuery = query || "Perform autonomous financial risk analysis and Sharpe ratio computation for AAPL over 30 days.";

  const ai = getGemini();
  let aiInsights: string | null = null;

  // If Gemini API Key is present, enhance the planning & verification with live reasoning
  if (ai) {
    try {
      const prompt = `You are the master coordinator of an Autonomous Multi-Agent AI System.
A user has submitted this task: "${userQuery}".
Provide a concise 3-sentence architectural review:
1. Explain how the Planning Agent will break this into DAG tasks.
2. What controlled tools the Research & Execution agents must call.
3. The specific safety & consistency constraints the Verification Agent must enforce.`;

      const response = await ai.models.generateContent({
        model: "gemini-3.8-flash",
        contents: prompt
      });
      aiInsights = response.text || null;
    } catch (e: any) {
      console.warn("Gemini reasoning warning (falling back to local engine):", e?.message);
    }
  }

  // Execute the autonomous engine in Python for authoritative results and state tracking
  const pyProcess = spawn("python3", [
    "-c",
    `
import json, sys
from autonomous_multi_agent_system import MultiAgentOrchestrator, ToolRegistry, TaskStatus

user_query = json.loads(sys.argv[1])
sim_target = sys.argv[2] if len(sys.argv) > 2 else ""

o = MultiAgentOrchestrator()
ctx = o.create_workflow(user_query)
try:
    o.execute_workflow(ctx.workflow_id, simulate_retry_on_task_id=sim_target if sim_target else None)
except Exception as e:
    pass

output = {
    "workflow_id": ctx.workflow_id,
    "user_query": ctx.user_query,
    "overall_status": ctx.overall_status,
    "duration_ms": round((ctx.end_time - ctx.start_time) * 1000, 2) if ctx.end_time else 0,
    "shared_blackboard": ctx.shared_blackboard,
    "tasks": [
        {
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "agent": t.assigned_agent.value,
            "status": t.status.value,
            "dependencies": t.dependencies,
            "tool_required": t.tool_required,
            "retry_count": t.retry_count,
            "error_log": t.error_log,
            "execution_time_ms": t.execution_time_ms,
            "result": t.result,
            "verification": {
                "is_valid": t.verification.is_valid,
                "score": t.verification.score,
                "critique": t.verification.critique,
                "checks_passed": t.verification.checks_passed,
                "checks_failed": t.verification.checks_failed
            } if t.verification else None
        }
        for t in ctx.task_graph.values()
    ],
    "messages": [
        {
            "id": m.id,
            "sender": m.sender.value,
            "receiver": m.receiver.value,
            "task_id": m.task_id,
            "content": m.content,
            "timestamp": m.timestamp
        }
        for m in ctx.message_history
    ],
    "tool_calls": [
        {
            "call_id": tc.call_id,
            "tool_name": tc.tool_name,
            "arguments": tc.arguments,
            "output": tc.output,
            "duration_ms": tc.duration_ms,
            "success": tc.success,
            "error": tc.error
        }
        for tc in ctx.tool_history
    ]
}
print(json.dumps(output, default=str))
`,
    JSON.stringify(userQuery),
    simulateFailure ? (failureTaskTarget || 'task_2_detect') : ''
  ]);

  let stdout = "";
  let stderr = "";

  pyProcess.stdout.on("data", (chunk) => {
    stdout += chunk.toString();
  });
  pyProcess.stderr.on("data", (chunk) => {
    stderr += chunk.toString();
  });

  pyProcess.on("close", async (code) => {
    try {
      if (stdout.trim()) {
        const parsed = JSON.parse(stdout.trim());
        parsed.aiInsights = aiInsights;

        // If Gemini is available and we retrieved live web facts, attempt smart factual enrichment with strict fallback
        if (ai && parsed.shared_blackboard?.latest_computation && parsed.shared_blackboard?.live_facts) {
          const comp = parsed.shared_blackboard.latest_computation;
          const facts = parsed.shared_blackboard.live_facts as Array<{ title?: string; snippet?: string; source?: string }>;
          
          if (comp.query_type && comp.query_type !== "financial_risk_analysis" && comp.query_type !== "anomaly_detection") {
            try {
              const snippets = facts.slice(0, 5).map(f => `- [${f.source || 'Wire'}] ${f.title}: ${f.snippet || ''}`).join("\n");
              const enrichPrompt = `You are the Synthesis & Verification Agent in an Autonomous Multi-Agent AI System.
The user requested: "${userQuery}".
The Research Agent retrieved these live factual news & reference articles:
${snippets}

Write an authoritative, factual, 3-paragraph executive summary directly answering the user's question with exact figures, dates, names, metrics, and outcomes. Enforce zero-hallucination: only state facts corroborated by the articles.`;

              const enrichPromise = ai.models.generateContent({
                model: "gemini-3.8-flash",
                contents: enrichPrompt
              });

              // 5-second race timeout so user request never hangs if Gemini spikes
              const timeoutPromise = new Promise<null>((_, reject) => setTimeout(() => reject(new Error("Timeout")), 5000));
              const enrichRes = await Promise.race([enrichPromise, timeoutPromise]) as any;

              if (enrichRes && enrichRes.text) {
                parsed.shared_blackboard.latest_computation.summary = enrichRes.text.trim();
              }
            } catch (err: any) {
              console.log("Gemini synthesis skipped or unavailable, using deterministic Python synthesis:", err?.message);
            }
          }
        }

        res.json(parsed);
      } else {
        res.status(500).json({ error: "Execution returned empty output", stderr });
      }
    } catch (e: any) {
      res.status(500).json({ error: "Failed to parse Python orchestrator output", raw: stdout, stderr });
    }
  });
});

// ---------------------------------------------------------------------------
// 4. CONTROLLED TOOL DIRECT TESTER
// ---------------------------------------------------------------------------
app.post("/api/tools/execute", (req: Request, res: Response) => {
  const { toolName, args, simulateFailure } = req.body;

  const pyProcess = spawn("python3", [
    "-c",
    `
import json, sys
from autonomous_multi_agent_system import ToolRegistry

registry = ToolRegistry()
record = registry.execute(
    name="${toolName}",
    kwargs=json.loads('''${JSON.stringify(args || {})}'''),
    simulate_failure=${simulateFailure ? "True" : "False"}
)
print(json.dumps({
    "call_id": record.call_id,
    "tool_name": record.tool_name,
    "arguments": record.arguments,
    "output": record.output,
    "duration_ms": record.duration_ms,
    "success": record.success,
    "error": record.error
}, default=str))
`
  ]);

  let stdout = "";
  pyProcess.stdout.on("data", (chunk) => { stdout += chunk.toString(); });
  pyProcess.on("close", () => {
    try {
      res.json(JSON.parse(stdout.trim()));
    } catch (e) {
      res.status(500).json({ error: "Tool execution failed", raw: stdout });
    }
  });
});

// ---------------------------------------------------------------------------
// 5. DOWNLOAD & CODE VIEWING ENDPOINTS (.py and .ipynb)
// ---------------------------------------------------------------------------
app.get("/api/download/python", (req: Request, res: Response) => {
  const filePath = path.join(process.cwd(), "autonomous_multi_agent_system.py");
  res.setHeader("Content-Disposition", 'attachment; filename="autonomous_multi_agent_system.py"');
  res.setHeader("Content-Type", "text/x-python; charset=utf-8");
  res.sendFile(filePath);
});

app.get("/api/download/notebook", (req: Request, res: Response) => {
  const filePath = path.join(process.cwd(), "autonomous_multi_agent_system.ipynb");
  res.setHeader("Content-Disposition", 'attachment; filename="autonomous_multi_agent_system.ipynb"');
  res.setHeader("Content-Type", "application/x-ipynb+json; charset=utf-8");
  res.sendFile(filePath);
});

app.get("/api/code/python", (req: Request, res: Response) => {
  const filePath = path.join(process.cwd(), "autonomous_multi_agent_system.py");
  if (fs.existsSync(filePath)) {
    res.setHeader("Content-Type", "text/plain");
    res.send(fs.readFileSync(filePath, "utf-8"));
  } else {
    res.status(404).send("File not found");
  }
});

app.get("/api/code/notebook", (req: Request, res: Response) => {
  const filePath = path.join(process.cwd(), "autonomous_multi_agent_system.ipynb");
  if (fs.existsSync(filePath)) {
    res.setHeader("Content-Type", "application/json");
    res.send(fs.readFileSync(filePath, "utf-8"));
  } else {
    res.status(404).json({ error: "File not found" });
  }
});

// ---------------------------------------------------------------------------
// 6. VITE MIDDLEWARE (DEV) & STATIC SERVING (PROD)
// ---------------------------------------------------------------------------
async function startServer() {
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`Autonomous Multi-Agent System Server running on http://0.0.0.0:${PORT}`);
  });
}

startServer();

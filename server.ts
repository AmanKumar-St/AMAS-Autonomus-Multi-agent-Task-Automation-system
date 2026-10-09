import express, { Request, Response } from "express";
import path from "path";
import fs from "fs";
import { spawn } from "child_process";
import { createServer as createViteServer } from "vite";
import dotenv from "dotenv";

dotenv.config();

const app = express();
const PORT = parseInt(process.env.PORT || "3000", 10);

// Cross-platform Python launcher
const PYTHON_CMD = process.env.PYTHON_PATH || (process.platform === "win32" ? "python" : "python3");

app.use(express.json());

// Helper to spawn Python commands safely with UTF-8
function runPythonCommand(args: string[]): Promise<{ stdout: string; stderr: string; exitCode: number }> {
  return new Promise((resolve, reject) => {
    let stdout = "";
    let stderr = "";
    const child = spawn(PYTHON_CMD, args, {
      cwd: process.cwd(),
      env: { ...process.env, PYTHONIOENCODING: "utf-8" }
    });

    child.stdout.on("data", (chunk) => {
      stdout += chunk.toString("utf-8");
    });

    child.stderr.on("data", (chunk) => {
      stderr += chunk.toString("utf-8");
    });

    child.on("close", (code) => {
      resolve({ stdout: stdout.trim(), stderr: stderr.trim(), exitCode: code ?? 0 });
    });

    child.on("error", (err) => {
      reject(err);
    });
  });
}

// In-memory event subscribers for SSE
const sseSubscribers: Map<string, Set<Response>> = new Map();

function addSSESubscriber(runId: string, res: Response) {
  if (!sseSubscribers.has(runId)) {
    sseSubscribers.set(runId, new Set());
  }
  sseSubscribers.get(runId)!.add(res);
}

function removeSSESubscriber(runId: string, res: Response) {
  sseSubscribers.get(runId)?.delete(res);
}

function broadcastSSE(runId: string, event: any) {
  const subscribers = sseSubscribers.get(runId);
  if (subscribers) {
    const data = `data: ${JSON.stringify(event)}\n\n`;
    for (const res of subscribers) {
      try {
        res.write(data);
      } catch (e) {
        // Client disconnected
        removeSSESubscriber(runId, res);
      }
    }
  }
}

// ---------------------------------------------------------------------------
// 1. SYSTEM STATUS & ENVIRONMENT INFO
// ---------------------------------------------------------------------------
app.get("/api/system-info", async (req: Request, res: Response) => {
  try {
    const { stdout } = await runPythonCommand(["-m", "amas.cli", "providers"]);
    const providers = JSON.parse(stdout || "[]");
    const activeProvider = providers.find((p: any) => p.is_default) || providers.find((p: any) => p.is_configured) || providers[0];

    res.json({
      status: "online",
      engine: "AMAS PraisonAI Runtime v2.0",
      pythonAvailable: true,
      pythonCommand: PYTHON_CMD,
      activeProvider: activeProvider?.id || "groq",
      activeModel: activeProvider?.default_model || "openai/gpt-oss-120b",
      configuredProviders: providers.filter((p: any) => p.is_configured).map((p: any) => p.id),
      allProviders: providers,
      modulesCovered: [
        "Agentic AI",
        "PraisonAI Agents",
        "Provider-Agnostic LLM",
        "Dynamic Task DAG",
        "Tool Calling",
        "Independent Verification",
        "Self-Healing Retries"
      ],
      artifactsReady: {
        pythonScript: fs.existsSync(path.join(process.cwd(), "autonomous_multi_agent_system.py")),
        jupyterNotebook: fs.existsSync(path.join(process.cwd(), "autonomous_multi_agent_system.ipynb")),
        database: fs.existsSync(path.join(process.cwd(), "amas", "storage", "amas.db"))
      }
    });
  } catch (err: any) {
    res.json({
      status: "degraded",
      engine: "AMAS Control Plane",
      pythonAvailable: false,
      error: err.message,
      allProviders: []
    });
  }
});

// ---------------------------------------------------------------------------
// 2. PROVIDER MANAGEMENT ENDPOINTS (No secrets exposed)
// ---------------------------------------------------------------------------
app.get("/api/providers", async (req: Request, res: Response) => {
  try {
    const { stdout } = await runPythonCommand(["-m", "amas.cli", "providers"]);
    res.json(JSON.parse(stdout || "[]"));
  } catch (err: any) {
    res.status(500).json({ error: "Failed to list providers", details: err.message });
  }
});

app.post("/api/providers/:id/test", async (req: Request, res: Response) => {
  const providerId = req.params.id;
  try {
    const { stdout } = await runPythonCommand(["-m", "amas.cli", "test-provider", providerId]);
    res.json(JSON.parse(stdout || "{}"));
  } catch (err: any) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// ---------------------------------------------------------------------------
// 3. EXECUTE AUTONOMOUS WORKFLOW (Primary AMAS Engine)
// ---------------------------------------------------------------------------
app.post(["/api/workflow/run", "/api/runs"], async (req: Request, res: Response) => {
  const { query, provider, model, simulateFailure } = req.body;
  const userQuery = query || "Analyze the risk profile and Sharpe ratio of AAPL over 30 days.";

  const cliArgs = ["-m", "amas.cli", "run", userQuery];
  if (provider) {
    cliArgs.push("--provider", provider);
  }
  if (model) {
    cliArgs.push("--model", model);
  }
  if (simulateFailure) {
    cliArgs.push("--simulate-failure");
  }

  try {
    const { stdout, stderr, exitCode } = await runPythonCommand(cliArgs);
    if (exitCode !== 0 && !stdout) {
      return res.status(500).json({ error: "Workflow execution failed", stderr });
    }

    try {
      const parsed = JSON.parse(stdout);
      res.json(parsed);
    } catch (parseErr) {
      res.status(500).json({ error: "Failed to parse orchestrator output", raw: stdout, stderr });
    }
  } catch (err: any) {
    res.status(500).json({ error: "Internal execution error", details: err.message });
  }
});

// ---------------------------------------------------------------------------
// 4. CONTROLLED TOOL DIRECT TESTER & DISCOVERY
// ---------------------------------------------------------------------------
app.get("/api/tools", async (req: Request, res: Response) => {
  try {
    const { stdout } = await runPythonCommand(["-m", "amas.cli", "tools"]);
    res.json(JSON.parse(stdout || "[]"));
  } catch (err: any) {
    res.status(500).json({ error: "Failed to list tools", details: err.message });
  }
});

app.post("/api/tools/execute", async (req: Request, res: Response) => {
  const { toolName, args } = req.body;
  const jsonArgs = JSON.stringify(args || {});

  try {
    const { stdout } = await runPythonCommand([
      "-m", "amas.cli", "execute-tool", toolName, "--args", jsonArgs
    ]);
    res.json(JSON.parse(stdout || "{}"));
  } catch (err: any) {
    res.status(500).json({ error: "Tool execution failed", details: err.message });
  }
});

// ---------------------------------------------------------------------------
// 5. SECURITY HARDENING: BENCHMARKS & EVALUATION ONLY (Arbitrary code BLOCKED)
// ---------------------------------------------------------------------------
app.post(["/api/run-python", "/api/evaluation/run"], async (req: Request, res: Response) => {
  // CRITICAL SECURITY FIX: Block arbitrary code execution
  if (req.body?.script) {
    return res.status(403).json({
      success: false,
      error: "Security Policy Violation: Arbitrary remote code execution is disabled. All tasks must execute through authorized AMAS tools."
    });
  }

  const start = Date.now();
  try {
    const { stdout, stderr, exitCode } = await runPythonCommand(["-m", "amas.cli", "eval"]);
    const duration = Date.now() - start;
    res.json({
      exitCode,
      stdout,
      stderr,
      durationMs: duration,
      success: exitCode === 0
    });
  } catch (err: any) {
    res.status(500).json({
      exitCode: -1,
      stdout: "",
      stderr: err.message,
      durationMs: Date.now() - start,
      success: false
    });
  }
});

// ---------------------------------------------------------------------------
// 6. DOWNLOAD & ARTIFACT MANAGEMENT
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
    res.setHeader("Content-Type", "text/plain; charset=utf-8");
    res.send(fs.readFileSync(filePath, "utf-8"));
  } else {
    res.status(404).send("File not found");
  }
});

app.get("/api/code/notebook", (req: Request, res: Response) => {
  const filePath = path.join(process.cwd(), "autonomous_multi_agent_system.ipynb");
  if (fs.existsSync(filePath)) {
    res.setHeader("Content-Type", "application/json; charset=utf-8");
    res.send(fs.readFileSync(filePath, "utf-8"));
  } else {
    res.status(404).json({ error: "File not found" });
  }
});

app.get("/api/artifacts/:filename", (req: Request, res: Response) => {
  const safeFilename = path.basename(req.params.filename);
  const filePath = path.join(process.cwd(), "amas", "storage", "artifacts", safeFilename);
  if (fs.existsSync(filePath)) {
    res.sendFile(filePath);
  } else {
    res.status(404).json({ error: "Artifact not found" });
  }
});

// ---------------------------------------------------------------------------
// 7. REAL-TIME EVENT STREAM (SSE)
// ---------------------------------------------------------------------------
app.get("/api/runs/:runId/events", (req: Request, res: Response) => {
  const runId = req.params.runId;

  // Set SSE headers
  res.setHeader("Content-Type", "text/event-stream");
  res.setHeader("Cache-Control", "no-cache");
  res.setHeader("Connection", "keep-alive");
  res.flushHeaders();

  // Send initial connection event
  res.write(`data: ${JSON.stringify({ type: "connected", runId })}\n\n`);

  // Add subscriber
  addSSESubscriber(runId, res);

  // Handle client disconnect
  req.on("close", () => {
    removeSSESubscriber(runId, res);
  });
});

// Endpoint to manually broadcast events (for testing or external triggers)
app.post("/api/runs/:runId/events", (req: Request, res: Response) => {
  const runId = req.params.runId;
  const event = req.body;
  broadcastSSE(runId, event);
  res.json({ success: true });
});

// ---------------------------------------------------------------------------
// 8. VITE MIDDLEWARE (DEV) & STATIC SERVING (PROD)
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
    console.log(`AMAS Autonomous Multi-Agent Server running on http://localhost:${PORT}`);
  });
}

startServer();

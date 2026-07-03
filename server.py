"""
SOC Dashboard API Server
Thin FastAPI wrapper around the existing OrchestratorCoordinator.
Run: python server.py  →  http://localhost:8000
"""

import os
import sys
import json
import asyncio
import uvicorn
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Ensure project root is on sys.path so "from src.…" imports work
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

if "GOOGLE_API_KEY" in os.environ and "GEMINI_API_KEY" not in os.environ:
    os.environ["GEMINI_API_KEY"] = os.environ["GOOGLE_API_KEY"]

from src.agents.orchestrator.agent import OrchestratorCoordinator

app = FastAPI(title="Security Triage Fleet — SOC Dashboard")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Single orchestrator instance shared across requests
orchestrator = OrchestratorCoordinator()

# ── Serve the dashboard ──────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    html_path = PROJECT_ROOT / "dashboard.html"
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


# ── Run a full simulation ────────────────────────────────────────────
@app.post("/api/simulate")
async def run_simulation(request: Request):
    """
    Accepts a JSON body with a 'prompt' field (the target context).
    Runs the 3-phase pipeline and returns the simulation report.
    """
    try:
        body = await request.json()
        prompt = body.get("prompt", "")
        if not prompt:
            return JSONResponse(
                status_code=400,
                content={"error": "Missing 'prompt' field in request body."}
            )

        result_json = await orchestrator.invoke(prompt)
        return JSONResponse(content=json.loads(result_json))

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "type": type(e).__name__}
        )


# ── HITL Approve / Deny ──────────────────────────────────────────────
@app.post("/api/approve")
async def approve_hitl(request: Request):
    """
    Re-runs the simulation with 'approve' in the prompt so the orchestrator
    triggers the Green Team remediation phase.
    """
    try:
        body = await request.json()
        original_prompt = body.get("prompt", "")
        approved = body.get("approved", False)

        if approved:
            prompt_with_approval = f"{original_prompt}\napprove"
        else:
            # Deny — return current state without remediation
            return JSONResponse(content={
                "simulation_outcome": "DENIED",
                "message": "HITL approval denied. Simulation halted at Phase 2."
            })

        result_json = await orchestrator.invoke(prompt_with_approval)
        return JSONResponse(content=json.loads(result_json))

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "type": type(e).__name__}
        )


if __name__ == "__main__":
    print("╔══════════════════════════════════════════════╗")
    print("║  Security Triage Fleet — SOC Dashboard       ║")
    print("║  http://localhost:8000                        ║")
    print("╚══════════════════════════════════════════════╝")
    uvicorn.run(app, host="0.0.0.0", port=8000)

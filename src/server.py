"""
🌐 DEMO WEB UI — Day 03 Chatbot vs ReAct Agent
Chạy: python src/server.py   rồi mở http://127.0.0.1:8080
"""

import os
import sys
import time
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from app import load_test_cases, run_react_agent, save_waterfall_trace
from mcp_server import MCPAcademicServer
from memory import ConversationMemory
from prompts import CHATBOT_BASELINE_PROMPT
from providers import get_llm_provider

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND = os.path.join(ROOT, "frontend")

provider = get_llm_provider()
mcp_server = MCPAcademicServer()
memory = ConversationMemory()

app = FastAPI(title="VinUni Day 03 — ReAct Agent Demo", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=FRONTEND), name="static")


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    mode: Literal["react", "chatbot"] = "react"


@app.get("/")
def index():
    return FileResponse(os.path.join(FRONTEND, "index.html"))


@app.get("/api/status")
def status():
    return {
        "provider": provider.__class__.__name__,
        "model": getattr(provider, "model_name", None),
        "base_url": getattr(provider, "base_url", None),
        "mcp_server": mcp_server.server_name,
        "mcp_version": mcp_server.version,
        "tool_count": len(mcp_server.list_tools()),
        "memory_backend": memory.backend,
        "machine_id": memory.machine_id,
        "old_prompts": len(memory.get_recent(limit=10)),
        "is_mock": provider.__class__.__name__ == "MockOfflineProvider",
    }


@app.get("/api/tools")
def tools():
    return {"tools": mcp_server.list_tools()}


@app.get("/api/tests")
def tests():
    return {"tests": load_test_cases()}


@app.get("/api/memory")
def memory_view():
    return {
        "backend": memory.backend,
        "machine_id": memory.machine_id,
        "limit": memory.limit,
        "prompts": memory.get_recent(limit=10),
    }


@app.post("/api/chat")
def chat(req: ChatRequest):
    query = req.message.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Câu hỏi trống.")

    if req.mode == "chatbot":
        started = time.time()
        output = provider.generate(query, system_prompt=CHATBOT_BASELINE_PROMPT)
        latency_ms = round((time.time() - started) * 1000, 2)
        traces = [{
            "step": 1,
            "query": query,
            "action_type": "FINAL_ANSWER",
            "thought": "Chatbot Cấp 2 — sinh văn bản, không gọi Tool / MCP.",
            "output": output,
            "latency_ms": latency_ms,
        }]
        save_waterfall_trace(traces)
        return {
            "mode": "chatbot",
            "query": query,
            "final_answer": output,
            "traces": traces,
            "used_tools": [],
            "memory": {
                "backend": memory.backend,
                "old_prompts": len(memory.get_recent(limit=10)),
            },
        }

    traces = run_react_agent(query, provider, mcp_server, memory=memory)
    save_waterfall_trace(traces)
    final_answer = ""
    used_tools = []
    for event in traces:
        if event.get("action_type") == "TOOL_EXECUTION" and event.get("tool_name"):
            used_tools.append(event["tool_name"])
        if event.get("action_type") == "FINAL_ANSWER":
            final_answer = event.get("output") or final_answer
    return {
        "mode": "react",
        "query": query,
        "final_answer": final_answer,
        "traces": traces,
        "used_tools": used_tools,
        "memory": {
            "backend": memory.backend,
            "machine_id": memory.machine_id,
            "old_prompts": len(memory.get_recent(limit=10)),
        },
    }


if __name__ == "__main__":
    import uvicorn

    print("==========================================================")
    print("🏫 VINUNI DAY 03 — DEMO UI  http://127.0.0.1:8080")
    print(f"🔌 Provider: {provider.__class__.__name__}")
    print(f"🌐 MCP: {mcp_server.server_name} | tools={len(mcp_server.list_tools())}")
    print(f"🧠 Memory: {memory.backend}")
    print("==========================================================")
    uvicorn.run(app, host="127.0.0.1", port=8080, log_level="info")

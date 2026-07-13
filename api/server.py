import asyncio
import json
import os
import subprocess
import threading
import uuid
from datetime import datetime
from pathlib import Path
from queue import Queue, Empty
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.schemas import RunRequest

app = FastAPI(title="Coding Agent Web UI")

BASE_DIR = Path(__file__).resolve().parent.parent

env_path = BASE_DIR / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())

LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

active_runs: dict[str, dict] = {}
run_history: list[dict] = []


def load_run_history():
    global run_history
    run_history = []
    if LOGS_DIR.exists():
        for d in sorted(LOGS_DIR.iterdir(), key=os.path.getmtime, reverse=True):
            if d.is_dir():
                transcript = d / "transcript.json"
                run_history.append({
                    "run_id": d.name,
                    "status": "completed",
                    "task": "",
                    "created_at": d.name.replace("run_", ""),
                    "log_path": str(transcript),
                })
                if transcript.exists():
                    try:
                        data = json.loads(open(transcript))
                        if data:
                            run_history[-1]["task"] = data[0].get("content", "") if len(data) > 0 else ""
                    except Exception:
                        pass


load_run_history()


def _run_agent_in_thread(run_id: str, task: str, max_steps: int,
                          repo_dir: Optional[str], test_cmd: Optional[str],
                          lint_cmd: Optional[str], queue: Queue):
    env = os.environ.copy()
    if repo_dir:
        env["TARGET_REPO_DIR"] = os.path.abspath(repo_dir)
    if test_cmd:
        env["TEST_CMD"] = test_cmd
    if lint_cmd:
        env["LINT_CMD"] = lint_cmd

    cmd = ["python", str(BASE_DIR / "main.py"), "--task", task, "--max-steps", str(max_steps)]

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
        text=True,
        bufsize=1,
    )

    for line in iter(proc.stdout.readline, ""):
        queue.put({"type": "stdout", "data": line})
    proc.wait()

    result = proc.returncode

    transcript_file = None
    log_dir = None
    for d in sorted(LOGS_DIR.iterdir(), key=os.path.getmtime, reverse=True):
        if d.is_dir() and d.name.startswith("run_"):
            tf = d / "transcript.json"
            if tf.exists():
                transcript_file = str(tf)
                log_dir = d.name
                break

    queue.put({
        "type": "done",
        "data": {
            "returncode": result,
            "log_dir": log_dir,
            "transcript_file": transcript_file,
        },
    })
    queue.put(None)


@app.post("/api/runs")
async def start_run(req: RunRequest):
    run_id = uuid.uuid4().hex[:12]
    queue: Queue = Queue()
    timestamp = datetime.now().isoformat()

    active_runs[run_id] = {
        "status": "running",
        "task": req.task,
        "created_at": timestamp,
        "queue": queue,
        "max_steps": req.max_steps,
        "repo_dir": req.repo_dir,
        "test_cmd": req.test_cmd,
        "lint_cmd": req.lint_cmd,
    }

    thread = threading.Thread(
        target=_run_agent_in_thread,
        args=(run_id, req.task, req.max_steps, req.repo_dir, req.test_cmd, req.lint_cmd, queue),
        daemon=True,
    )
    thread.start()

    return {"run_id": run_id, "status": "started", "created_at": timestamp}


@app.get("/api/runs")
async def list_runs():
    active_list = []
    for rid, info in active_runs.items():
        active_list.append({
            "run_id": rid,
            "status": info["status"],
            "task": info["task"][:80],
            "created_at": info["created_at"],
        })
    return {"runs": active_list + run_history[:50]}


@app.get("/api/runs/{run_id}")
async def get_run(run_id: str):
    if run_id in active_runs:
        info = active_runs[run_id]
        return {
            "run_id": run_id,
            "status": info["status"],
            "task": info["task"],
            "created_at": info["created_at"],
            "output": None,
        }

    for d in LOGS_DIR.iterdir():
        if d.name == f"run_{run_id}" or d.name == run_id:
            transcript = d / "transcript.json"
            if transcript.exists():
                data = json.loads(open(transcript))
                return {
                    "run_id": d.name,
                    "status": "completed",
                    "transcript": data,
                }

    raise HTTPException(status_code=404, detail="Run not found")


@app.get("/api/runs/{run_id}/transcript")
async def get_transcript(run_id: str):
    for d in LOGS_DIR.iterdir():
        if d.name == run_id or d.name == f"run_{run_id}":
            transcript = d / "transcript.json"
            if transcript.exists():
                return FileResponse(str(transcript), media_type="application/json")
    raise HTTPException(status_code=404, detail="Transcript not found")


@app.websocket("/api/ws/{run_id}")
async def websocket_endpoint(websocket: WebSocket, run_id: str):
    await websocket.accept()

    if run_id not in active_runs:
        await websocket.send_json({"type": "error", "data": "Run not found or already completed"})
        await websocket.close()
        return

    run_info = active_runs[run_id]
    queue: Queue = run_info["queue"]

    try:
        while True:
            try:
                item = queue.get(timeout=0.1)
            except Empty:
                try:
                    await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(None, queue.get, True, 0.1),
                        timeout=0.5,
                    )
                    item = queue.get_nowait()
                except Exception:
                    try:
                        await websocket.send_json({"type": "ping"})
                    except Exception:
                        break
                    continue

            if item is None:
                run_info["status"] = "completed"
                await websocket.send_json({"type": "done"})
                break

            await websocket.send_json(item)

            if item.get("type") == "done":
                run_info["status"] = "completed"
                break

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "data": str(e)})
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


frontend_dir = BASE_DIR / "frontend" / "dist"
static_dir = BASE_DIR / "static"

if frontend_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dir / "assets")), name="assets")
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
elif static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

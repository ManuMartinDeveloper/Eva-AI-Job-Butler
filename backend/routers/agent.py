# backend/routers/agent.py
import os
import sys
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

import json
from fastapi.responses import FileResponse

# --- Setup Paths ---
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
sys.path.append(_PROJECT_ROOT)

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
SESSION_PATH = os.path.join(WORKSPACE_ROOT, "outputs", "agent_session.json")
SCREENSHOT_PATH = os.path.join(WORKSPACE_ROOT, "outputs", "agent_screenshot.png")

from core.db import SessionLocal, AgentLog
from core.agent import agent

router = APIRouter()

# Dependency to get db session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic schemas
class AgentLogSchema(BaseModel):
    id: int
    action: str
    details: str
    timestamp: str
    status: str

    class Config:
        orm_mode = True

class AgentStatusResponse(BaseModel):
    is_running: bool
    status_text: str
    next_tasks: List[dict]

@router.get("/status", response_model=AgentStatusResponse)
def get_status():
    status_text = "🟢 Running" if agent.is_running else "🔴 Stopped"
    
    # Extract upcoming jobs from scheduler
    next_tasks = []
    if agent.is_running:
        for job in agent.scheduler.get_jobs():
            next_tasks.append({
                "id": job.id,
                "next_run_time": job.next_run_time.strftime('%Y-%m-%d %H:%M:%S') if job.next_run_time else "None"
            })
    else:
        # Mock what will be scheduled
        next_tasks = [
            {"id": "scout_jobs", "next_run_time": "When started (every 4h)"},
            {"id": "pr_brainstorm", "next_run_time": "When started (every 12h)"}
        ]
            
    return {
        "is_running": agent.is_running,
        "status_text": status_text,
        "next_tasks": next_tasks
    }

@router.post("/start")
def start_agent():
    if agent.is_running:
        return {"message": "Agent is already running"}
    
    try:
        agent.start()
        return {"message": "Agent successfully started in the background."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start agent: {e}")

@router.post("/stop")
def stop_agent():
    if not agent.is_running:
        return {"message": "Agent is not running"}
    
    try:
        agent.stop()
        return {"message": "Agent successfully stopped."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop agent: {e}")

@router.post("/evaluate")
def trigger_evaluate(background_tasks: BackgroundTasks):
    try:
        background_tasks.add_task(agent.task_evaluate_jobs)
        return {"message": "Job evaluation process started in the background."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start evaluation: {e}")

@router.get("/logs", response_model=List[AgentLogSchema])
def get_logs(db: Session = Depends(get_db)):
    logs = db.query(AgentLog).order_by(AgentLog.timestamp.desc()).limit(50).all()
    
    serialized_logs = []
    for log in logs:
        serialized_logs.append({
            "id": log.id,
            "action": log.action,
            "details": log.details,
            "timestamp": log.timestamp.strftime('%Y-%m-%d %H:%M:%S') if log.timestamp else "",
            "status": log.status
        })
        
    return serialized_logs

class AgentCommandRequest(BaseModel):
    command: str

@router.get("/session")
def get_agent_session():
    if not os.path.exists(SESSION_PATH):
        return {"status": "idle", "logs": []}
    try:
        with open(SESSION_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read agent session: {e}")

@router.get("/screenshot")
def get_agent_screenshot():
    if not os.path.exists(SCREENSHOT_PATH):
        raise HTTPException(status_code=404, detail="Screenshot not found")
    return FileResponse(SCREENSHOT_PATH)

@router.post("/session/command")
def post_agent_command(req: AgentCommandRequest):
    if req.command not in ["approve", "abort"]:
        raise HTTPException(status_code=400, detail="Invalid command. Must be 'approve' or 'abort'")
        
    if not os.path.exists(SESSION_PATH):
        raise HTTPException(status_code=404, detail="No active agent session found to command")
        
    try:
        with open(SESSION_PATH, "r") as f:
            session_data = json.load(f)
        
        session_data["command"] = req.command
        
        with open(SESSION_PATH, "w") as f:
            json.dump(session_data, f, indent=2)
            
        return {"status": "success", "message": f"Command '{req.command}' registered."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write command: {e}")

@router.delete("/session")
def delete_agent_session():
    if os.path.exists(SESSION_PATH):
        try:
            os.remove(SESSION_PATH)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete session: {e}")
    if os.path.exists(SCREENSHOT_PATH):
        try:
            os.remove(SCREENSHOT_PATH)
        except Exception as e:
            pass
    return {"status": "success", "message": "Agent session cache cleared successfully."}

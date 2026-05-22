# backend/routers/jobs.py
import os
import sys
import subprocess
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

# --- Setup Paths ---
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
sys.path.append(_PROJECT_ROOT)

from core.db import SessionLocal, Job, Application, AgentLog, ProfileFact
from backend.auth import get_current_user, User

router = APIRouter()

# Dependency to get db session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic schemas
class JobSchema(BaseModel):
    id: int
    title: str
    company: str
    location: Optional[str] = None
    description: Optional[str] = None
    url: str
    date_posted: Optional[str] = None
    salary: Optional[str] = None
    site: Optional[str] = None
    email: Optional[str] = None
    scouted_at: str
    is_applied: bool
    fit_score: int
    fit_reasoning: Optional[str] = None

    class Config:
        orm_mode = True

class ScoutRequest(BaseModel):
    search_term: str = "AI Engineer"
    location: str = "Bengaluru"
    limit: int = 20

class ApplyResponse(BaseModel):
    status: str
    message: str

class ApplyRequest(BaseModel):
    provider: Optional[str] = "gemini"
    model: Optional[str] = None

def run_scout_task(search_term: str, location: str, limit: int, user_id: int):
    # This function is now imported from core.tasks. Leaving a wrapper just in case.
    from core.tasks import run_scout_task as task_impl
    task_impl(search_term, location, limit, user_id)

def run_apply_task(job_url: str, provider: str = "gemini", model: Optional[str] = None, user_id: Optional[int] = None):
    # This function is now imported from core.tasks. Leaving a wrapper just in case.
    from core.tasks import run_apply_task as task_impl
    task_impl(job_url, provider, model, user_id, False)

from core.tasks import trigger_scout_jobs, trigger_auto_apply

@router.get("/", response_model=List[JobSchema])
def list_jobs(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    jobs = db.query(Job).filter(Job.user_id == current_user.id).order_by(Job.scouted_at.desc()).all()
    # Serialize date
    result = []
    for j in jobs:
        result.append({
            "id": j.id,
            "title": j.title,
            "company": j.company,
            "location": j.location,
            "description": j.description,
            "url": j.url,
            "date_posted": j.date_posted,
            "salary": j.salary,
            "site": j.site,
            "email": j.email,
            "scouted_at": j.scouted_at.strftime('%Y-%m-%d %H:%M:%S') if j.scouted_at else "",
            "is_applied": j.is_applied,
            "fit_score": j.fit_score or 0,
            "fit_reasoning": j.fit_reasoning
        })
    return result

@router.get("/{job_id}", response_model=JobSchema)
def get_job(job_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    j = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
    if not j:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "id": j.id,
        "title": j.title,
        "company": j.company,
        "location": j.location,
        "description": j.description,
        "url": j.url,
        "date_posted": j.date_posted,
        "salary": j.salary,
        "site": j.site,
        "email": j.email,
        "scouted_at": j.scouted_at.strftime('%Y-%m-%d %H:%M:%S') if j.scouted_at else "",
        "is_applied": j.is_applied,
        "fit_score": j.fit_score or 0,
        "fit_reasoning": j.fit_reasoning
    }

@router.post("/{job_id}/evaluate", response_model=JobSchema)
def evaluate_single_job(job_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # 1. Fetch job
    j = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
    if not j:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # 2. Run evaluation
    from core.profile_memory_resume_phase2 import get_llm, get_qdrant_client, get_rag_context, parse_json_output
    qdrant_client = get_qdrant_client()
    
    # We can log this to AgentLog
    from core.agent import agent
    agent.log_action("Thought", f"Manual assessment started for '{j.title}' at '{j.company}'...", "Running", user_id=current_user.id)
    
    context = get_rag_context(j.title, j.description or "", qdrant_client, current_user.id)
    if not context.strip():
        db_facts = db.query(ProfileFact).filter(ProfileFact.user_id == current_user.id).all()
        if db_facts:
            context = "## Candidate Profile Facts:\n" + "\n".join([f"- [{f.category}] {f.fact}" for f in db_facts])
        else:
            context = "No profile facts found."
    
    prompt = f"""
You are Eva, the autonomous Agentic AI Job Butler. Your goal is to analyze if the candidate is a good match for the job description.
Perform a step-by-step reasoning cycle (Thought -> Action -> Observation -> Decision) and output a JSON response.

CANDIDATE PROFILE CONTEXT (RAG):
---
{context}
---

JOB DETAILS:
Job Title: {j.title}
Company: {j.company}
Location: {j.location}
Job Description:
---
{j.description}
---

**INSTRUCTIONS:**
1. Perform an in-depth match assessment. Identify required skills, frameworks, and years of experience.
2. Formulate your reasoning using the ReAct (Thought/Action/Observation) paradigm:
   - THOUGHT: Analyze the job description and candidate facts. Identify alignment and discrepancies.
   - ACTION/OBSERVATION: Compare the specific skills/experiences needed with what the candidate has.
   - DECISION: Determine the final fit score (0 to 100), gap analysis, and tailored recommendations.
3. Output a VALID JSON object with the following schema:
{{
  "thought_process": "Detailed thoughts of your requirements vs skills analysis.",
  "gap_analysis": "Identify specific skills, tools, or experience gaps.",
  "fit_score": 85, // integer 0-100
  "fit_reasoning": "A concise 2-3 sentence summary explaining the fit score and key reasons, to be displayed directly on the UI dashboard.",
  "recommendations": "Actionable advice on what projects/skills to emphasize or add to the resume for this role.",
  "should_auto_apply": true
}}
Do NOT output any markdown tags or text outside of the JSON object.
"""
    try:
        # Default to gemini for manual evaluation
        llm = get_llm(provider="gemini")
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, 'content') else str(response)
        parsed_json = parse_json_output(content)
        
        if parsed_json:
            fit_score = int(parsed_json.get("fit_score", 0))
            fit_reasoning = parsed_json.get("fit_reasoning", "")
            thought = parsed_json.get("thought_process", "")
            gaps = parsed_json.get("gap_analysis", "")
            recs = parsed_json.get("recommendations", "")
            
            full_reasoning = f"Score: {fit_score}%\n\nGap Analysis:\n{gaps}\n\nRecommendations:\n{recs}\n\nReasoning:\n{fit_reasoning}"
            
            j.fit_score = fit_score
            j.fit_reasoning = full_reasoning
            db.commit()
            db.refresh(j)
            
            agent.log_action("Thought", f"[Manual: {j.title}] {thought[:100]}...", "Success", user_id=current_user.id)
            agent.log_action("Decision", f"Job '{j.title}' rated {fit_score}%", "Success", user_id=current_user.id)
        else:
            agent.log_action("Scout", f"Failed to parse agent reasoning JSON for job {j.id}.", "Failed", user_id=current_user.id)
            raise HTTPException(status_code=500, detail="Failed to parse agent reasoning.")
    except Exception as e:
        agent.log_action("Scout", f"Error during manual evaluation of job {j.id}: {str(e)}", "Failed", user_id=current_user.id)
        raise HTTPException(status_code=500, detail=str(e))
        
    return {
        "id": j.id,
        "title": j.title,
        "company": j.company,
        "location": j.location,
        "description": j.description,
        "url": j.url,
        "date_posted": j.date_posted,
        "salary": j.salary,
        "site": j.site,
        "email": j.email,
        "scouted_at": j.scouted_at.strftime('%Y-%m-%d %H:%M:%S') if j.scouted_at else "",
        "is_applied": j.is_applied,
        "fit_score": j.fit_score or 0,
        "fit_reasoning": j.fit_reasoning
    }

@router.post("/scout")
def trigger_scout(req: ScoutRequest, background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user)):
    trigger_scout_jobs(req.search_term, req.location, req.limit, current_user.id, background_tasks)
    return {"message": "Job scout task started in the background."}

@router.post("/{job_id}/apply", response_model=ApplyResponse)
def trigger_apply(job_id: int, req: ApplyRequest = ApplyRequest(), background_tasks: BackgroundTasks = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    j = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
    if not j:
        raise HTTPException(status_code=404, detail="Job not found")
    
    trigger_auto_apply(j.url, current_user.id, req.provider, req.model, background_tasks)
    
    # Mark job as applied
    j.is_applied = True
    # Create or update Application object
    app_record = db.query(Application).filter_by(job_id=j.id).first()
    if not app_record:
        app_record = Application(job_id=j.id, status="Applied")
        db.add(app_record)
    else:
        app_record.status = "Applied"
    db.commit()
    
    return {"status": "success", "message": f"Assisted application launched in browser for {j.title} at {j.company}."}


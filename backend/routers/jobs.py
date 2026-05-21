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

from core.db import SessionLocal, Job, Application, AgentLog

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

def run_scout_task(search_term: str, location: str, limit: int):
    """Run the job scout scraper script in a subprocess and log the action."""
    db = SessionLocal()
    log = AgentLog(action="Scout", details=f"Manual scout started for '{search_term}' in '{location}'", status="Running")
    db.add(log)
    db.commit()
    db.refresh(log)
    
    try:
        # Run scraper script as a subprocess
        process = subprocess.run(
            [sys.executable, "scrapers/job_scout.py", "--search", search_term, "--location", location, "--limit", str(limit)],
            cwd=_PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        
        # Check for database synchronization from CSV
        from scrapers.job_scout import fetch_and_save_jobs
        # Re-import and run sync since we are already in-process or we just sync files
        # The script scrapers/job_scout.py updates job_seeker.db.
        # Now let's sync new jobs into agent_brain.db (Job model)
        # We can implement a sync helper to copy from job_seeker.db to agent_brain.db
        import sqlite3
        seeker_db_path = os.path.join(_PROJECT_ROOT, 'data', 'job_seeker.db')
        if os.path.exists(seeker_db_path):
            conn = sqlite3.connect(seeker_db_path)
            c = conn.cursor()
            c.execute("SELECT title, company, location, description, url, date_posted, salary, site, email FROM jobs ORDER BY id DESC LIMIT ?", (limit * 2,))
            scraped_jobs = c.fetchall()
            conn.close()
            
            new_count = 0
            for row in scraped_jobs:
                title, company, loc, desc, url, date_posted, salary, site, email = row
                exists = db.query(Job).filter_by(url=url).first()
                if not exists:
                    new_job = Job(
                        title=title,
                        company=company,
                        location=loc,
                        description=desc,
                        url=url,
                        date_posted=date_posted,
                        salary=salary,
                        site=site,
                        email=email
                    )
                    db.add(new_job)
                    new_count += 1
            db.commit()
            log.details = f"Scout complete. Found {new_count} new jobs."
            log.status = "Success"
        else:
            log.details = "Scout completed but job_seeker.db was not found."
            log.status = "Failed"
            
    except Exception as e:
        log.details = f"Scout failed: {str(e)}"
        log.status = "Failed"
    finally:
        db.commit()
        db.close()

def run_apply_task(job_url: str, provider: str = "gemini", model: Optional[str] = None):
    """Launches the headful Playwright form filler in the background."""
    # Delete old session/screenshot files to prevent frontend displaying stale data
    session_path = os.path.join(_PROJECT_ROOT, "outputs", "agent_session.json")
    screenshot_path = os.path.join(_PROJECT_ROOT, "outputs", "agent_screenshot.png")
    
    if os.path.exists(session_path):
        try:
            os.remove(session_path)
        except Exception as e:
            print(f"Could not remove old session file: {e}")
            
    if os.path.exists(screenshot_path):
        try:
            os.remove(screenshot_path)
        except Exception as e:
            print(f"Could not remove old screenshot: {e}")
            
    try:
        cmd = [sys.executable, "core/auto_apply.py", "--url", job_url, "--provider", provider]
        if model:
            cmd.extend(["--model", model])
            
        subprocess.Popen(
            cmd,
            cwd=_PROJECT_ROOT
        )
    except Exception as e:
        print(f"Error launching auto apply: {e}")

@router.get("/", response_model=List[JobSchema])
def list_jobs(db: Session = Depends(get_db)):
    jobs = db.query(Job).order_by(Job.scouted_at.desc()).all()
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
def get_job(job_id: int, db: Session = Depends(get_db)):
    j = db.query(Job).filter(Job.id == job_id).first()
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
def evaluate_single_job(job_id: int, db: Session = Depends(get_db)):
    # 1. Fetch job
    j = db.query(Job).filter(Job.id == job_id).first()
    if not j:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # 2. Run evaluation
    from core.profile_memory_resume_phase2 import get_llm, get_chroma_client, get_rag_context, parse_json_output
    chroma_client = get_chroma_client()
    
    # We can log this to AgentLog
    from core.agent import agent
    agent.log_action("Thought", f"Manual assessment started for '{j.title}' at '{j.company}'...", "Running")
    
    context = get_rag_context(j.title, j.description or "", chroma_client)
    if not context.strip():
        from core.db import ProfileFact
        db_facts = db.query(ProfileFact).all()
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
            
            agent.log_action("Thought", f"[Manual: {j.title}] {thought[:100]}...", "Success")
            agent.log_action("Decision", f"Job '{j.title}' rated {fit_score}%", "Success")
        else:
            agent.log_action("Scout", f"Failed to parse agent reasoning JSON for job {j.id}.", "Failed")
            raise HTTPException(status_code=500, detail="Failed to parse agent reasoning.")
    except Exception as e:
        agent.log_action("Scout", f"Error during manual evaluation of job {j.id}: {str(e)}", "Failed")
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
def trigger_scout(req: ScoutRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_scout_task, req.search_term, req.location, req.limit)
    return {"message": "Job scout task started in the background."}

@router.post("/{job_id}/apply", response_model=ApplyResponse)
def trigger_apply(job_id: int, req: ApplyRequest = ApplyRequest(), background_tasks: BackgroundTasks = None, db: Session = Depends(get_db)):
    j = db.query(Job).filter(Job.id == job_id).first()
    if not j:
        raise HTTPException(status_code=404, detail="Job not found")
    
    background_tasks.add_task(run_apply_task, j.url, req.provider, req.model)
    
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
    
    return {"status": "success", "message": f"Assisted application launched in local browser for {j.title} at {j.company}."}


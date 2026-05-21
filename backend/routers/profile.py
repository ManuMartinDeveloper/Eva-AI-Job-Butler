# backend/routers/profile.py
import os
import sys
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

# --- Setup Paths ---
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
sys.path.append(_PROJECT_ROOT)

from core.db import SessionLocal, ProfileFact, AgentLog
from core.ingest import ingest_profile, read_profile

router = APIRouter()

# Dependency to get db session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic schemas
class FactSchema(BaseModel):
    id: int
    category: Optional[str] = None
    fact: str
    source: Optional[str] = None
    confidence: int
    created_at: str

    class Config:
        orm_mode = True

class NewFactRequest(BaseModel):
    category: str = "Skills"
    fact: str
    source: str = "Manual Input"

class ProfileDetailsResponse(BaseModel):
    name: str
    email: str
    phone: str
    website: str
    skills: List[str]
    experience: List[dict]
    education: List[dict]
    github_username: str
    facts: List[FactSchema]

def run_ingestion_task():
    """Trigger the ingest pipeline (embed text facts + github repos)."""
    db = SessionLocal()
    log = AgentLog(action="Ingest", details="Profile RAG Ingestion Pipeline started", status="Running")
    db.add(log)
    db.commit()
    db.refresh(log)
    
    try:
        ingest_profile()
        log.details = "Profile RAG Ingestion Pipeline completed successfully."
        log.status = "Success"
    except Exception as e:
        log.details = f"Profile Ingestion failed: {str(e)}"
        log.status = "Failed"
    finally:
        db.commit()
        db.close()

@router.get("/", response_model=ProfileDetailsResponse)
def get_profile(db: Session = Depends(get_db)):
    # Read the profile from SQLite (seeded from core/ingest.py)
    profile_info = read_profile()
    if not profile_info:
        # Import default profile structure if table is empty
        from core.ingest import user_profile
        profile_info = user_profile
    
    # Read facts from the agent_brain DB (e.g. extracted from chats or custom input)
    db_facts = db.query(ProfileFact).order_by(ProfileFact.created_at.desc()).all()
    serialized_facts = []
    for fact in db_facts:
        serialized_facts.append({
            "id": fact.id,
            "category": fact.category,
            "fact": fact.fact,
            "source": fact.source,
            "confidence": fact.confidence or 100,
            "created_at": fact.created_at.strftime('%Y-%m-%d %H:%M:%S') if fact.created_at else ""
        })

    return {
        "name": profile_info.get("name", ""),
        "email": profile_info.get("email", ""),
        "phone": profile_info.get("phone", ""),
        "website": profile_info.get("website", ""),
        "skills": profile_info.get("skills", []),
        "experience": profile_info.get("experience", []),
        "education": profile_info.get("education", []),
        "github_username": profile_info.get("github_username", ""),
        "facts": serialized_facts
    }

@router.post("/ingest")
def trigger_ingest(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_ingestion_task)
    return {"message": "Profile embedding and sync pipeline started in background."}

@router.post("/fact", response_model=FactSchema)
def add_fact(req: NewFactRequest, db: Session = Depends(get_db)):
    if not req.fact.strip():
        raise HTTPException(status_code=400, detail="Fact text cannot be empty")
        
    fact_obj = ProfileFact(
        category=req.category,
        fact=req.fact,
        source=req.source,
        confidence=100
    )
    db.add(fact_obj)
    db.commit()
    db.refresh(fact_obj)
    
    return {
        "id": fact_obj.id,
        "category": fact_obj.category,
        "fact": fact_obj.fact,
        "source": fact_obj.source,
        "confidence": fact_obj.confidence,
        "created_at": fact_obj.created_at.strftime('%Y-%m-%d %H:%M:%S')
    }

@router.delete("/fact/{fact_id}")
def delete_fact(fact_id: int, db: Session = Depends(get_db)):
    fact = db.query(ProfileFact).filter(ProfileFact.id == fact_id).first()
    if not fact:
        raise HTTPException(status_code=404, detail="Fact not found")
        
    db.delete(fact)
    db.commit()
    return {"message": f"Fact #{fact_id} successfully deleted."}

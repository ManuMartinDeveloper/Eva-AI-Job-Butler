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

import json
from core.db import SessionLocal, ProfileFact, AgentLog, UserProfile
from backend.auth import get_current_user, User
from core.ingest import ingest_profile

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
    projects: List[dict]
    github_username: str
    facts: List[FactSchema]

def run_ingestion_task(user_id: int):
    """Trigger the ingest pipeline (embed text facts + github repos)."""
    db = SessionLocal()
    log = AgentLog(user_id=user_id, action="Ingest", details="Profile RAG Ingestion Pipeline started", status="Running")
    db.add(log)
    db.commit()
    db.refresh(log)
    
    try:
        ingest_profile(user_id=user_id)
        log.details = "Profile RAG Ingestion Pipeline completed successfully."
        log.status = "Success"
    except Exception as e:
        log.details = f"Profile Ingestion failed: {str(e)}"
        log.status = "Failed"
    finally:
        db.commit()
        db.close()

@router.get("/", response_model=ProfileDetailsResponse)
def get_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Read the profile from DB
    profile_info = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    
    # Defaults if not initialized yet
    skills_list = []
    experience_list = []
    education_list = []
    name = ""
    email = current_user.email
    phone = ""
    website = ""
    github_username = ""
    
    if profile_info:
        name = profile_info.name or ""
        email = profile_info.email or current_user.email
        phone = profile_info.phone or ""
        website = profile_info.website or ""
        github_username = profile_info.github_username or ""
        try:
            skills_list = json.loads(profile_info.skills) if profile_info.skills else []
        except Exception:
            skills_list = []
        try:
            experience_list = json.loads(profile_info.experience) if profile_info.experience else []
        except Exception:
            experience_list = []
        try:
            education_list = json.loads(profile_info.education) if profile_info.education else []
        except Exception:
            education_list = []
        try:
            projects_list = json.loads(profile_info.projects) if profile_info.projects else []
        except Exception:
            projects_list = []
            
    # Read facts from the agent_brain DB
    db_facts = db.query(ProfileFact).filter(ProfileFact.user_id == current_user.id).order_by(ProfileFact.created_at.desc()).all()
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
        "name": name,
        "email": email,
        "phone": phone,
        "website": website,
        "skills": skills_list,
        "experience": experience_list,
        "education": education_list,
        "projects": projects_list,
        "github_username": github_username,
        "facts": serialized_facts
    }

class ProfileUpdateSchema(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    skills: Optional[List[str]] = None
    experience: Optional[List[dict]] = None
    education: Optional[List[dict]] = None
    projects: Optional[List[dict]] = None
    github_username: Optional[str] = None

@router.put("/", response_model=ProfileDetailsResponse)
def update_profile(req: ProfileUpdateSchema, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
    
    if req.name is not None: profile.name = req.name
    if req.email is not None: profile.email = req.email
    if req.phone is not None: profile.phone = req.phone
    if req.website is not None: profile.website = req.website
    if req.skills is not None: profile.skills = json.dumps(req.skills)
    if req.experience is not None: profile.experience = json.dumps(req.experience)
    if req.education is not None: profile.education = json.dumps(req.education)
    if req.projects is not None: profile.projects = json.dumps(req.projects)
    if req.github_username is not None: profile.github_username = req.github_username
    
    db.commit()
    db.refresh(profile)
    
    return get_profile(current_user=current_user, db=db)

@router.post("/ingest")
def trigger_ingest(background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user)):
    background_tasks.add_task(run_ingestion_task, current_user.id)
    return {"message": "Profile embedding and sync pipeline started in background."}

@router.post("/fact", response_model=FactSchema)
def add_fact(req: NewFactRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not req.fact.strip():
        raise HTTPException(status_code=400, detail="Fact text cannot be empty")
        
    fact_obj = ProfileFact(
        user_id=current_user.id,
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
def delete_fact(fact_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    fact = db.query(ProfileFact).filter(ProfileFact.id == fact_id, ProfileFact.user_id == current_user.id).first()
    if not fact:
        raise HTTPException(status_code=404, detail="Fact not found")
        
    db.delete(fact)
    db.commit()
    return {"message": f"Fact #{fact_id} successfully deleted."}

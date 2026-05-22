# backend/routers/chat.py
import os
import sys
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from pydantic import BaseModel

# --- Setup Paths ---
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
sys.path.append(_PROJECT_ROOT)

from core.db import SessionLocal, ProfileFact, UserProfile
from backend.auth import get_current_user, User
from core.profile_memory_resume_phase2 import get_llm, parse_json_output

router = APIRouter()

# Dependency to get db session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic schemas
class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage]
    provider: Optional[str] = "gemini"
    model_name: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str
    extracted_facts: List[str]

@router.post("/message", response_model=ChatResponse)
def handle_chat_message(req: ChatRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
        
    try:
        llm = get_llm(req.provider, req.model_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM initialization failed: {e}")

    # Fetch profile to get user name dynamically
    profile_info = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    user_name = "Candidate"
    if profile_info and profile_info.name:
        user_name = profile_info.name
    elif current_user.email:
        user_name = current_user.email.split("@")[0]

    # 1. Generate Eva's Chat Reply
    history_formatted = ""
    for msg in req.history:
        role_label = user_name if msg.role == "user" else "Eva (Butler)"
        history_formatted += f"{role_label}: {msg.content}\n"
    
    chat_prompt = f"""
    You are Eva, the personal AI Job Butler for {user_name}. Your goal is to interview {user_name} to learn more about their background, skills, and projects so you can write stellar, tailored resumes for them.
    
    Conversation History:
    {history_formatted}
    {user_name}: {req.message}
    
    Instructions:
    - Respond in an engaging, professional, and friendly butler-like tone.
    - Keep your response brief (1-3 sentences) and conversational.
    - Ask exactly one specific follow-up question to dig deeper into any skills, achievements, or project details.
    
    Eva (Butler):
    """
    
    try:
        chat_reply = llm.invoke(chat_prompt)
        reply_text = chat_reply.content if hasattr(chat_reply, 'content') else str(chat_reply)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate AI response: {e}")

    # 2. Extract Facts in Parallel (Background or Synchronous fast prompt)
    # Ask the LLM to extract key skills or facts from the user's latest response in JSON format.
    extraction_prompt = f"""
    Analyze the following user response from {user_name} during a career interview.
    Identify any new professional facts, skills, experiences, or project details that were explicitly stated.
    
    User Response: "{req.message}"
    
    Output a VALID JSON object containing a list of extracted facts:
    {{
        "facts": [
            "Fact 1 (e.g. 'Has experience building chatbots using LangChain')",
            "Fact 2 (e.g. 'Proficient with PyTorch for model training')"
        ]
    }}
    If no professional facts can be extracted, return an empty list. Do NOT include any explanations outside the JSON object.
    """
    
    extracted_facts = []
    try:
        extraction_res = llm.invoke(extraction_prompt)
        ext_text = extraction_res.content if hasattr(extraction_res, 'content') else str(extraction_res)
        parsed_ext = parse_json_output(ext_text)
        if parsed_ext and "facts" in parsed_ext:
            extracted_facts = parsed_ext["facts"]
            
            # Save extracted facts to database
            for fact_text in extracted_facts:
                # Deduplicate or skip empty
                if not fact_text.strip():
                    continue
                new_fact = ProfileFact(
                    user_id=current_user.id,
                    category="Interview",
                    fact=fact_text.strip(),
                    source="Interview Chat",
                    confidence=95
                )
                db.add(new_fact)
            db.commit()
    except Exception as e:
        print(f"Fact extraction failed: {e}")
        # Non-fatal error, do not fail the chat response

    # If extraction did not find anything structural, we still save the raw response as a basic fact
    # just like the phase1 app did, to ensure no data is lost.
    if not extracted_facts:
        new_fact = ProfileFact(
            user_id=current_user.id,
            category="Interview",
            fact=req.message.strip(),
            source="Interview Chat (Raw)",
            confidence=80
        )
        db.add(new_fact)
        db.commit()

    return {
        "reply": reply_text.strip(),
        "extracted_facts": extracted_facts
    }

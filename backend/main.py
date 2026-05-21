# backend/main.py
import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# --- Setup Paths ---
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
sys.path.append(_PROJECT_ROOT)

from core.db import init_db
from backend.routers import jobs, profile, generate, agent, chat

app = FastAPI(
    title="Eva AI Job Butler API",
    description="Backend API for Eva AI Job Butler Web & Android Applications",
    version="1.0.0"
)

# Configure CORS
# Allow all local origins (React dev server, local network IPs, and Android emulator loopbacks)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize SQLite database tables
@app.on_event("startup")
def startup_event():
    init_db()

# Include routers
app.include_router(jobs.router, prefix="/api/jobs", tags=["Jobs"])
app.include_router(profile.router, prefix="/api/profile", tags=["Profile"])
app.include_router(generate.router, prefix="/api/generate", tags=["Document Generator"])
app.include_router(agent.router, prefix="/api/agent", tags=["Autonomous Agent"])
app.include_router(chat.router, prefix="/api/chat", tags=["Interview Chat"])

@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "Eva AI Job Butler API is running.",
        "docs_url": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)

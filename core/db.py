from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
import os

# --- Setup ---
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
DB_PATH = os.path.join(_PROJECT_ROOT, 'data', 'agent_brain.db')
DATABASE_URL = f"sqlite:///{DB_PATH}"

Base = declarative_base()

# --- Models ---

class Job(Base):
    __tablename__ = 'jobs'
    
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    location = Column(String)
    description = Column(Text)
    url = Column(String, unique=True, nullable=False)
    date_posted = Column(String)
    salary = Column(String)
    site = Column(String)
    email = Column(String)
    
    # Metadata
    scouted_at = Column(DateTime, default=datetime.now)
    is_applied = Column(Boolean, default=False)
    fit_score = Column(Integer, default=0) # 0-100 score from AI
    fit_reasoning = Column(Text)
    
    # Relationships
    application = relationship("Application", back_populates="job", uselist=False)

class Application(Base):
    __tablename__ = 'applications'
    
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey('jobs.id'))
    
    status = Column(String, default="Applied") # Applied, Interview, Rejected, Offer
    applied_at = Column(DateTime, default=datetime.now)
    resume_path = Column(String)
    cover_letter_path = Column(String)
    notes = Column(Text)
    
    job = relationship("Job", back_populates="application")

class ProfileFact(Base):
    __tablename__ = 'profile_facts'
    
    id = Column(Integer, primary_key=True)
    category = Column(String) # Skills, Experience, Preference, Personal
    fact = Column(Text, nullable=False)
    source = Column(String) # Resume, Interview, LinkedIn
    confidence = Column(Integer, default=100)
    created_at = Column(DateTime, default=datetime.now)

class AgentLog(Base):
    __tablename__ = 'agent_logs'
    
    id = Column(Integer, primary_key=True)
    action = Column(String) # Scout, Apply, PR_Post
    details = Column(Text)
    timestamp = Column(DateTime, default=datetime.now)
    status = Column(String) # Success, Failed

# --- Engine & Session ---
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    Base.metadata.create_all(bind=engine)
    print(f"Database initialized at {DB_PATH}")

if __name__ == "__main__":
    init_db()

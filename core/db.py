from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
import os

# --- Setup ---
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
DB_PATH = os.path.join(_PROJECT_ROOT, 'data', 'agent_brain.db')

# Use Railway/Postgres URL if provided, otherwise fallback to local SQLite
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DB_PATH}")

# Fix postgresql:// vs postgres:// for SQLAlchemy
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

Base = declarative_base()

# --- Models ---

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    
    jobs = relationship("Job", back_populates="user")
    facts = relationship("ProfileFact", back_populates="user")
    profile = relationship("UserProfile", back_populates="user", uselist=False)

class UserProfile(Base):
    __tablename__ = 'user_profiles'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True, nullable=False)
    
    name = Column(String)
    email = Column(String)
    phone = Column(String)
    website = Column(String)
    skills = Column(Text) # JSON string array
    experience = Column(Text) # JSON string array of dicts
    education = Column(Text) # JSON string array of dicts
    projects = Column(Text) # JSON string array of dicts
    github_username = Column(String)
    
    user = relationship("User", back_populates="profile")

class Job(Base):
    __tablename__ = 'jobs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    location = Column(String)
    description = Column(Text)
    url = Column(String, nullable=False) # Removed unique=True to allow multiple users to save the same job
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
    user = relationship("User", back_populates="jobs")
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
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    category = Column(String) # Skills, Experience, Preference, Personal
    fact = Column(Text, nullable=False)
    source = Column(String) # Resume, Interview, LinkedIn
    confidence = Column(Integer, default=100)
    created_at = Column(DateTime, default=datetime.now)
    
    user = relationship("User", back_populates="facts")

class AgentLog(Base):
    __tablename__ = 'agent_logs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    action = Column(String) # Scout, Apply, PR_Post
    details = Column(Text)
    timestamp = Column(DateTime, default=datetime.now)
    status = Column(String) # Success, Failed

# --- Engine & Session ---
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    if "sqlite" in DATABASE_URL:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    Base.metadata.create_all(bind=engine)
    print(f"Database initialized.")

if __name__ == "__main__":
    init_db()

# core/ingest.py
import os
import sys
import json
import logging
import uuid
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from github import Github, GithubException

# --- Setup Paths ---
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
sys.path.append(_PROJECT_ROOT)

from core.db import SessionLocal, UserProfile, User, ProfileFact
from core.profile_memory_resume_phase2 import get_qdrant_client, ensure_collection

# Load environment variables
load_dotenv(os.path.join(_PROJECT_ROOT, '.env'))

# Define skill categories for metadata
TECHNICAL_SKILLS = [
    "Artificial Intelligence (AI)", "Machine Learning", "Scikit-learn",
    "Analytics and Visualization", "Power BI", "Excel", "DAX",
    "Python (Pandas, Matplotlib)", "Natural Language Processing (NLP)",
    "Chatbot Development", "Computer Vision", "DialogFlow",
    "Python (Programming Language)", "Large Language Model (LLM)",
    "Langchain", "Data Cleaning", "EDA", "Statistical Analysis"
]
SOFT_SKILLS = [
    "Leadership", "Adaptability", "Problem Solving",
    "Communication", "Time Management", "Collaboration",
    "Teaching", "Training"
]

# Configure logging for errors
logging.basicConfig(filename="rag_pipeline.log", level=logging.ERROR, format="%(asctime)s - %(message)s")

# --- Embedder Initialization ---
def get_embedder():
    print("Loading embedder model...")
    return SentenceTransformer('all-MiniLM-L6-v2', device="cpu")

embedder = get_embedder()

# Fallback seed data for User 1 or when profile is completely empty
SEED_PROFILE = {
    "name": "Manu Martin",
    "email": "manu.reshma.martin@gmail.com",
    "phone": "+91 8746 960082",
    "website": "https://manumartin.streamlit.app",
    "skills": [
        "Artificial Intelligence (AI)", "Machine Learning", "Scikit-learn",
        "Analytics and Visualization", "Power BI", "Excel", "DAX",
        "Python (Pandas, Matplotlib)", "Natural Language Processing (NLP)",
        "Chatbot Development", "Computer Vision", "DialogFlow",
        "Python (Programming Language)", "Large Language Model (LLM)",
        "Langchain", "Leadership", "Adaptability", "Problem Solving",
        "Communication", "Time Management", "Collaboration", "Data Cleaning",
        "EDA", "Statistical Analysis", "Teaching", "Training"
    ],
    "experience": [
        {"role": "Conversation Designer Intern", "year": 2025, "duration": 4, "company": "Comportement Software Private Limited"},
        {"role": "Freelancer", "year": 2025, "duration": 6, "company": ""}
    ],
    "education": [
        {"degree": "BSc in Computer Science Mathematic and Electronics", "year": 2023, "college": "Christ University, Bengaluru"},
        {"degree": "MSc in Artificial Intelligence and Machine Learning", "year": 2025, "college": "Christ University, Bengaluru"}
    ],
    "projects": [],
    "github_username": "ManuMartinDeveloper"
}

def fetch_github_projects(username):
    """
    Fetches public repositories for a given GitHub username.
    """
    if not username or not username.strip():
        return []
    try:
        github_token = os.getenv("GITHUB_TOKEN")
        g = Github(github_token) if github_token else Github()
        user = g.get_user(username)
        repos = user.get_repos()
        projects = []
        print(f"Found {repos.totalCount} repositories for github user '{username}'.")
        for repo in repos:
            homepage = repo.homepage or ""
            description = repo.description or ""
            if description.strip():
                projects.append({"name": repo.name, "description": description, "homepage": homepage})
            
        if not projects:
            print("No valid GitHub projects with descriptions found.")
            return []
        return projects
    except GithubException as e:
        print(f"GitHub API error for user '{username}': {e}.")
        logging.error(f"GitHub API error: {e}")
        return []
    except Exception as e:
        print(f"Error fetching GitHub projects: {e}")
        logging.error(f"Error fetching GitHub projects: {e}")
        return []

def get_or_create_user_profile(session, user_id):
    """
    Gets user profile from DB or creates a seed one if empty/not found.
    """
    profile = session.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        user = session.query(User).filter(User.id == user_id).first()
        email = user.email if user else ""
        profile = UserProfile(
            user_id=user_id,
            name=SEED_PROFILE["name"],
            email=email or SEED_PROFILE["email"],
            phone=SEED_PROFILE["phone"],
            website=SEED_PROFILE["website"],
            skills=json.dumps(SEED_PROFILE["skills"]),
            experience=json.dumps(SEED_PROFILE["experience"]),
            education=json.dumps(SEED_PROFILE["education"]),
            projects=json.dumps(SEED_PROFILE["projects"]),
            github_username=SEED_PROFILE["github_username"]
        )
        session.add(profile)
        session.commit()
        session.refresh(profile)
        print(f"Created seed profile for user_id={user_id}")
    return profile

def create_or_update_embeddings(user_id):
    """
    Reads user profile from DB and updates Qdrant vector DB.
    """
    session = SessionLocal()
    try:
        profile = session.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if not profile:
            print(f"No profile found for user_id={user_id}. Cannot update embeddings.")
            return False

        skills = json.loads(profile.skills) if profile.skills else []
        experience = json.loads(profile.experience) if profile.experience else []
        education = json.loads(profile.education) if profile.education else []
        projects = json.loads(profile.projects) if profile.projects else []

        # Prepare collections of facts
        collections_data = {
            "personal": [
                {"content": f"NAME: {profile.name or ''}", "id_str": "name", "metadata": {"category": "personal"}},
                {"content": f"EMAIL: {profile.email or ''}", "id_str": "email", "metadata": {"category": "personal"}},
                {"content": f"PHONE: {profile.phone or ''}", "id_str": "phone", "metadata": {"category": "personal"}},
                {"content": f"WEBSITE: {profile.website or ''}", "id_str": "website", "metadata": {"category": "personal"}},
                {"content": f"GITHUB_USERNAME: {profile.github_username or ''}", "id_str": "github_username", "metadata": {"category": "personal"}}
            ],
            "skills": [
                {
                    "content": f"SKILL: {skill}", "id_str": f"skill_{i}",
                    "metadata": {"category": "technical" if skill in TECHNICAL_SKILLS else "soft"}
                } for i, skill in enumerate(skills)
            ],
            "experience": [
                {
                    "content": f"EXPERIENCE: {exp.get('role', '')} at {exp.get('company', '')} ({exp.get('year', '')}, {exp.get('duration', '')} months)", 
                    "id_str": f"experience_{i}",
                    "metadata": {"year": str(exp.get('year', '')), "duration": exp.get('duration', 0), "company": exp.get('company', '')}
                } for i, exp in enumerate(experience)
            ],
            "education": [
                {
                    "content": f"EDUCATION: {edu.get('degree', '')} ({edu.get('year', '')}, {edu.get('college', '')})", 
                    "id_str": f"education_{i}",
                    "metadata": {"year": str(edu.get('year', '')), "college": edu.get('college', '')}
                } for i, edu in enumerate(education)
            ],
            "projects": [
                {
                    "content": f"PROJECT: {pro.get('name', '')}: {pro.get('description', '')}", 
                    "id_str": f"project_{i}",
                    "metadata": {"source": "github", "homepage": pro.get('homepage', '')}
                } for i, pro in enumerate(projects)
            ]
        }

        # Initialize Qdrant Client
        client = get_qdrant_client()
        ensure_collection(client, "eva_profile_facts", 384)

        from qdrant_client.http import models as rest_models

        # Delete existing points for this user to avoid duplicate or stale entries
        client.delete(
            collection_name="eva_profile_facts",
            points_selector=rest_models.Filter(
                must=[
                    rest_models.FieldCondition(
                        key="user_id",
                        match=rest_models.MatchValue(value=user_id)
                    )
                ]
            )
        )
        print(f"Cleared existing points for user_id={user_id} in Qdrant.")

        points = []
        for category_name, items in collections_data.items():
            if not items:
                continue
            
            # Embed content
            contents = [item["content"] for item in items]
            embeddings = embedder.encode(contents, device="cpu", normalize_embeddings=True)
            
            for idx, item in enumerate(items):
                point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"user_{user_id}_{category_name}_{item['id_str']}"))
                points.append(
                    rest_models.PointStruct(
                        id=point_id,
                        vector=embeddings[idx].tolist(),
                        payload={
                            "user_id": user_id,
                            "category": category_name,
                            "content": item["content"],
                            "metadata": item["metadata"]
                        }
                    )
                )

        if points:
            client.upsert(
                collection_name="eva_profile_facts",
                points=points
            )
            print(f"Upserted {len(points)} facts to Qdrant collection 'eva_profile_facts' for user_id={user_id}.")
        return True
    except Exception as e:
        print(f"Failed to process and upload embeddings to Qdrant: {e}")
        logging.error(f"Failed to process and upload embeddings to Qdrant: {e}")
        return False
    finally:
        session.close()

def ingest_profile(user_id):
    """
    Main ingestion pipeline per user: fetches Github repos, updates UserProfile in database, and generates Qdrant embeddings.
    """
    print(f"--- RAG Ingestion Pipeline Started for user_id={user_id} ---")
    session = SessionLocal()
    try:
        # Step 1: Get or Create profile
        profile = get_or_create_user_profile(session, user_id)
        
        # Step 2: Fetch and merge GitHub projects if username is present
        if profile.github_username:
            print(f"\nFetching GitHub projects for '{profile.github_username}'...")
            gh_projects = fetch_github_projects(profile.github_username)
            if gh_projects:
                # Merge or replace existing projects
                profile.projects = json.dumps(gh_projects)
                session.commit()
                print(f"Updated GitHub projects in database.")
        
        # Step 3: Embed profile details into Qdrant
        print("\nCreating and uploading Qdrant vector embeddings...")
        if create_or_update_embeddings(user_id):
            print(f"\n--- RAG Pipeline Completed Successfully for user_id={user_id} ---")
        else:
            print(f"\n--- Ingestion failed during embeddings creation ---")
            raise Exception("Embeddings creation failed.")
    finally:
        session.close()

if __name__ == "__main__":
    # Test script locally for user_id=1
    print("Testing ingestion for user_id=1")
    ingest_profile(1)


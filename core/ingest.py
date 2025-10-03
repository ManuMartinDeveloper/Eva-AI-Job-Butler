import os
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
DB_PATH = os.path.join(_PROJECT_ROOT, 'data', 'job_seeker.db')
CHROMA_PATH = os.path.join(_PROJECT_ROOT, 'data', 'chroma_data')

import json
import logging
import os
import sqlite3
import chromadb
from github import Github, GithubException
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import streamlit as st # Import Streamlit

# Load environment variables
load_dotenv() 

# --- User Profile Data (Initial State) ---
# This is the "seed" data for your profile. It will be updated with live data from GitHub.
user_profile = {
    "name": "Manu Martin",
    "email": "manu.reshma.martin@gmail.com",
    "phone": '+91 8746 960082',
    'website': 'https://manumartin.streamlit.app',
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
    "projects": [], # This will be populated from GitHub
    "github_username": "ManuMartinDeveloper"
}

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

# --- Variable Initializations ---
@st.cache_resource
def get_embedder():
    print("Loading embedder model...")
    return SentenceTransformer('all-MiniLM-L6-v2', device="cpu")
embedder = get_embedder()

# --- Function Definitions ---

def fetch_github_projects(username):
    """
    Fetches public repositories for a given GitHub username.
    """
    try:
        github_token = os.getenv("GITHUB_TOKEN")
        print(f"{github_token} is the token")
        # if not github_token:
        #     raise ValueError("GITHUB_TOKEN is required in .env for GitHub API access.")
        g = Github(github_token) if github_token else Github()
        user = g.get_user()
        repos = user.get_repos()
        projects = []
        print(f"Found {repos.totalCount} repositories for user '{username}'.")
        for repo in repos:
            homepage = repo.homepage
            description = repo.description or "No description"
            if description.strip():
                projects.append({"name": repo.name, "description": description, "homepage": homepage})
            
        if not projects:
            print("No valid GitHub projects with descriptions found. Using fallback projects.")
            return [{"name": "fallback-project", "description": "Customer churn prediction model"}]
        return projects
    except GithubException as e:
        print(f"GitHub API error: {e}. Check username or token.")
        logging.error(f"GitHub API error: {e}")
        return [{"name": "fallback-project", "description": "Customer churn prediction model"}]
    except Exception as e:
        print(f"Error fetching GitHub projects: {e}")
        logging.error(f"Error fetching GitHub projects: {e}")
        return [{"name": "fallback-project", "description": "Customer churn prediction model"}]

def validate_profile(profile):
    """
    Validates the structure and content of the user profile dictionary.
    """
    try:
        if not all([profile['name'], profile['phone'], profile['email'], profile['website'], profile['skills'], profile['github_username']]):
            raise ValueError("Name, email, phone, website, skills, or GitHub username is empty")
        # Add more validation for other fields as needed
        return True
    except Exception as e:
        print(f"Validation error: {e}")
        logging.error(f"Validation error: {e}")
        return False

def init_db():
    """
    Initializes the SQLite database and creates the profile table.
    """
    try:
        print(f"Initializing database at {DB_PATH}")
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS profile (
            name TEXT, email TEXT, phone TEXT, website TEXT, skills TEXT, experience TEXT, education TEXT, projects TEXT, github_username TEXT
        )''')
        conn.commit()
        conn.close()
        print("Database 'job_seeker.db' initialized successfully.")
        return True
    except Exception as e:
        print(f"Failed to initialize database: {e}")
        logging.error(f"Failed to initialize database: {e}")
        return False

def save_profile(profile_data):
    """
    Saves the user profile data to the SQLite database.
    """
    if not validate_profile(profile_data):
        print("Stopping due to validation failure.")
        return False
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM profile")
        c.execute("INSERT INTO profile (name, email, phone, website, skills, experience, education, projects, github_username) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                  (profile_data['name'], profile_data['email'], profile_data['phone'], profile_data['website'], json.dumps(profile_data['skills']),
                   json.dumps(profile_data['experience']), json.dumps(profile_data['education']), 
                   json.dumps(profile_data['projects']), profile_data['github_username']))
        conn.commit()
        conn.close()
        print("Profile saved to SQLite successfully.")
        return True
    except Exception as e:
        print(f"Failed to save profile to SQLite: {e}")
        logging.error(f"Failed to save profile to SQLite: {e}")
        return False

def read_profile():
    """
    Reads the user profile from the SQLite database.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM profile")
        profile_data = c.fetchone()
        conn.close()
        if profile_data:
            profile = {
                "name": profile_data[0],
                "email": profile_data[1],
                "phone": profile_data[2],
                'website': profile_data[3],
                "skills": json.loads(profile_data[4]),
                "experience": json.loads(profile_data[5]),
                "education": json.loads(profile_data[6]),
                "projects": json.loads(profile_data[7]),
                "github_username": profile_data[8]
            }
            return profile
        return None
    except Exception as e:
        print(f"Error reading profile from SQLite: {e}")
        logging.error(f"Error reading profile from SQLite: {e}")
        return None

def create_or_update_embeddings():
    """
    Reads the profile from SQLite and creates/updates a ChromaDB vector database.
    """
    profile = read_profile()
    if not profile:
        print("Stopping due to profile reading failure.")
        logging.error("Stopping due to profile reading failure.")
        return False

    # Initialize embedding model
    try:
        
        if embedder: print("Embedding model all-MiniLM-L6-v2 loaded successfully.")
    except Exception as e:
        print(f"Failed to load embedding model: {e}")
        logging.error(f"Failed to load embedding model: {e}")
        return False

    # Prepare data for ChromaDB
    collections_data = {
        "personal": [
            {"content": f"NAME: {profile['name']}", "id": "name_1", "metadata": {"category": "personal"}},
            {"content": f"EMAIL: {profile['email']}", "id": "email_1", "metadata": {"category": "personal"}},
            {"content": f"PHONE: {profile['phone']}", "id": "phone_!", "metadata": {"category": "personal"}},
            {"content": f"WEBSITE: {profile['website']}", "id": "website_1", "metadata": {"category": "personal"}},
            {"content": f"GITHUB_USERNAME: {profile['github_username']}", "id": "github_username_1", "metadata": {"category": "personal"}}
        ],
        "skills": [
            {
                "content": f"SKILL: {skill}", "id": f"skill_{i+1}",
                "metadata": {"category": "technical" if skill in TECHNICAL_SKILLS else "soft"}
            } for i, skill in enumerate(profile['skills'])
        ],
        "experience": [
            {
                "content": f"EXPERIENCE: {exp['role']} at {exp['company']} ({exp['year']}, {exp['duration']} months)", "id": f"experience_{i+1}",
                "metadata": {"year": str(exp['year']), "duration": exp['duration'], "company": exp['company']}
            } for i, exp in enumerate(profile['experience'])
        ],
        "education": [
            {
                "content": f"EDUCATION: {edu['degree']} ({edu['year']}, {edu['college']})", "id": f"education_{i+1}",
                "metadata": {"year": str(edu['year']), "college": edu['college']}
            } for i, edu in enumerate(profile['education'])
        ],
        "projects": [
            {
                "content": f"PROJECT: {pro['name']}: {pro['description']}", "id": f"project_{i+1}",
                "metadata": {"source": "github"}
            } for i, pro in enumerate(profile['projects'])
        ]
    }

    # Initialize Chroma and process collections
    try:
        print(f"ChromaDB path: {CHROMA_PATH}")
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        for coll_name, items in collections_data.items():
            if not items:
                print(f"Warning: No items to add to collection '{coll_name}'.")
                continue
            collection = client.get_or_create_collection(coll_name, metadata={"hnsw:space": "cosine"})
            contents = [item["content"] for item in items]
            ids = [item["id"] for item in items]
            metadatas = [item["metadata"] for item in items]
            embeddings = embedder.encode(contents, device="cpu", normalize_embeddings=True)
            collection.upsert(
                documents=contents,
                embeddings=embeddings.tolist(),
                metadatas=metadatas,
                ids=ids
            )
            print(f"Upserted {len(items)} items to collection '{coll_name}'. Total items: {collection.count()}")
        print("\nAll collections processed successfully.")
        return True
    except Exception as e:
        print(f"Failed to initialize Chroma or process collections: {e}")
        logging.error(f"Failed to initialize Chroma or process collections: {e}")
        return False

def ingest_profile():
    """
    Main function to run the ingestion pipeline: fetch GitHub projects, save profile to SQLite, and create/update embeddings.
    """
    print("--- RAG Pipeline Started ---")
    print(DB_PATH)

    # Step 1: Initialize the database
    if not init_db():
        print("Database initialization failed. Exiting.")
        exit(1)

    # Step 2: Fetch projects and update user profile
    print("\nFetching GitHub projects...")
    user_profile['projects'] = fetch_github_projects(user_profile['github_username'])
    print("GitHub projects fetched and updated in profile.")
    
    # Step 3: Save the complete profile to SQLite
    print("\nSaving complete profile to SQLite...")
    if not save_profile(user_profile):
        print("Profile saving failed. Exiting.")
        exit(1)

    # Step 4: Create embeddings from the saved profile
    print("\nCreating vector embeddings in ChromaDB...")
    if not create_or_update_embeddings():
        print("Embedding creation failed. Exiting.")
        exit(1)
        
    print("\n--- RAG Pipeline Completed Successfully ---")
    print("Your data is now stored in 'job_seeker.db' and the vector database in the 'chroma_data/' directory.")



# --- Main Execution Block ---
if __name__ == "__main__":
    print("--- RAG Pipeline Started ---")

    # Step 1: Initialize the database
    if not init_db():
        print("Database initialization failed. Exiting.")
        exit(1)

    # Step 2: Fetch projects and update user profile
    print("\nFetching GitHub projects...")
    user_profile['projects'] = fetch_github_projects(user_profile['github_username'])
    print("GitHub projects fetched and updated in profile.")
    
    # Step 3: Save the complete profile to SQLite
    print("\nSaving complete profile to SQLite...")
    if not save_profile(user_profile):
        print("Profile saving failed. Exiting.")
        exit(1)

    # Step 4: Create embeddings from the saved profile
    print("\nCreating vector embeddings in ChromaDB...")
    if not create_or_update_embeddings():
        print("Embedding creation failed. Exiting.")
        exit(1)
        
    print("\n--- RAG Pipeline Completed Successfully ---")
    print("Your data is now stored in 'job_seeker.db' and the vector database in the 'chroma_data/' directory.")


# core/profile_memory.py
import streamlit as st # Import Streamlit
from langchain_ollama import OllamaLLM
from sentence_transformers import SentenceTransformer
import chromadb
import os

# --- Setup paths (no changes here) ---
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
DB_PATH = os.path.join(_PROJECT_ROOT, 'data', 'job_seeker.db')
CHROMA_PATH = os.path.join(_PROJECT_ROOT, 'data', 'chroma_data')

# --- Cached Functions to Load Models ---
# This decorator tells Streamlit to run this function only once.
@st.cache_resource
def get_embedder():
    print("Loading embedder model...")
    return SentenceTransformer('all-MiniLM-L6-v2', device="cpu")

@st.cache_resource
def get_llm():
    print("Loading LLM model...")
    return OllamaLLM(model="phi4-mini")

@st.cache_resource
def get_chroma_client():
    print("Initializing ChromaDB client...")
    return chromadb.PersistentClient(path=CHROMA_PATH)

def ingest_and_embed(clear_existing=False):
    from .ingest import ingest_profile
    ingest_profile()


# Global setup
embedder = SentenceTransformer('all-MiniLM-L6-v2', device="cpu")
llm = OllamaLLM(model="phi4-mini")
print(f"Chroma_path in query_rag: {CHROMA_PATH}")
client = chromadb.PersistentClient(path=CHROMA_PATH)

def ingest_and_embed(clear_existing=False):
    from .ingest import ingest_profile
    ingest_profile()

def query_rag(job_title, job_desc="", doc_type="cover_letter"):
    llm = get_llm()
    client = get_chroma_client()

    # --- 1. Intelligent, Context-Aware Query Generation ---
    query_map = {
        "skills": f"What are my most relevant skills for a '{job_title}' role?",
        "experience": f"Which of my past jobs are most relevant to these responsibilities: {job_desc}?",
        "projects": f"Which of my projects best showcase skills for this job: {job_desc}?"
    }

    context = ""
    for coll_name, query in query_map.items():
        try:
            collection = client.get_collection(coll_name)
            results = collection.query(query_texts=[query], n_results=5)
            if results and results.get('documents'):
                context += f"Relevant {coll_name}:\n- " + "\n- ".join(results['documents'][0]) + "\n\n"
        except Exception as e:
            print(f"Error querying '{coll_name}': {e}")

    # --- 2. Advanced Prompt Engineering with a Persona ---
    persona_prompt = "Act as an expert career coach and professional resume writer for Manu Martin. Your tone is confident, professional, and achievement-oriented. Only use the information provided in the USER PROFILE and JOB DESCRIPTION to generate responses."
    
    prompt_template = {
        "cover_letter": f"""{persona_prompt}
        Based ONLY on the user profile below, write a compelling 3-paragraph cover letter for '{job_title}'. Keep it under 200 words. Highlight the most relevant project or experience and connect it to a key requirement in the job description.
        USER PROFILE:
        ---
        {context}
        ---
        JOB DESCRIPTION:
        ---
        {job_desc}
        ---
        """,
        "resume": f"""{persona_prompt}
        Based ONLY on the user profile below, generate a tailored 'Professional Summary' (2 sentences), a 'Key Skills' section (6 bullet points), a 'Key Projects' section (5 most relavent projects with small description about each project), 'Education' section with all the education backgroud with the year of completion (You shall not alter the education and course informations, Do not halucinate this information), 'Experience' section incluse the professional Jobs done for a resume targeted at the job of '{job_title}'.
        USER PROFILE:
        ---
        {context}
        ---
        """
    }
    
    prompt = prompt_template.get(doc_type.lower(), prompt_template["resume"])
    return llm.invoke(prompt)
# core/profile_memory.py
from langchain_ollama import OllamaLLM
from sentence_transformers import SentenceTransformer
import chromadb

# Setup paths
import os
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
DB_PATH = os.path.join(_PROJECT_ROOT, 'data', 'job_seeker.db')
CHROMA_PATH = os.path.join(_PROJECT_ROOT, 'data', 'chroma_data')


# Global setup
embedder = SentenceTransformer('all-MiniLM-L6-v2', device="cpu")
llm = OllamaLLM(model="phi4-mini")
print(f"Chroma_path in query_rag: {CHROMA_PATH}")
client = chromadb.PersistentClient(path=CHROMA_PATH)

def ingest_and_embed(clear_existing=False):
    from .ingest import ingest_profile
    ingest_profile()

def query_rag(query, job_desc="", doc_type="cover_letter"):
    collections = ["personal","skills", "experience", "education", "projects"]
    context = ""
    for coll_name in collections:
        try:
            collection = client.get_collection(coll_name)
            results = collection.query(query_texts=[query], n_results=3)
            context += "\n".join(results['documents'][0]) if results['documents'] else ""
        except Exception as e:
            print(f"Error querying {coll_name}: {e}")
    if not context:
        return "No relevant profile data found. Please re-ingest your profile."
    
    # Enhanced prompt for tailoring
    prompt_template = {
        "cover_letter": f"""Generate a professional cover letter (150-200 words) for {job_desc}.
        Use this user profile: {context}. Highlight 2-3 relevant skills/experiences, personalize with a value-first approach (e.g., 'I can enhance your AI team with...'), and include a CTA (e.g., 'Available for a 15-min call'). 
        Format: [Date]\n[Recruiter Name, Company]\n[Dear ...]\n[Body]\n[Sign-off: Manu Martin]""",
        "resume": f"""Generate a concise resume section (100-150 words) tailored for {job_desc}.
        Use this user profile: {context}. Include a summary (1-2 sentences), key skills (3-5), and relevant experience (2-3 items). Format as plain text with headings: Summary, Skills, Experience."""
    }
    prompt = prompt_template.get(doc_type.lower(), prompt_template["cover_letter"])
    return llm.invoke(prompt)
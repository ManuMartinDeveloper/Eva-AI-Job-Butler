# core/profile_memory.py
# Handles profile ingestion, embedding, and RAG querying
# Setup paths
import os
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
DB_PATH = os.path.join(_PROJECT_ROOT, 'data', 'job_seeker.db')
CHROMA_PATH = os.path.join(_PROJECT_ROOT, 'data', 'chroma_data')

from langchain_ollama import OllamaLLM
from sentence_transformers import SentenceTransformer
import chromadb
from .ingest import ingest_profile  # Assuming ingestion.py holds your code

# Global setup
embedder = SentenceTransformer('all-MiniLM-L6-v2', device="cpu")
# llm = OllamaLLM(model="phi3.5")  # Ensure 'ollama pull phi3.5' is run
llm = OllamaLLM(model="phi4-mini")

def ingest_and_embed(clear_existing=False):
    # Run your ingestion pipeline
    ingest_profile()  # Update with GitHub projects, save to SQLite, embed in ChromaDB
    # Note: Your code already handles this; just call it here

def query_rag(query, job_desc=""):
    print(f"Chroma_path in query_rag: {CHROMA_PATH}")
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collections = ["personal","skills", "experience", "education", "projects"]
    context = ""
    print("Collection count:", len(collections))

    for coll_name in collections:
        collection = client.get_collection(coll_name)
        results = collection.query(query_texts=[query], n_results=3)
        context += "\n".join(results['documents'][0])
    # prompt = f"Using this user profile: {context}\nTailor a response for: {job_desc}\n{query}. Complete the task never leanving out details from the profile."
    prompt = f"Using this user profile: {context}\n{query}, Answer {job_desc}."
    return llm.invoke(prompt)
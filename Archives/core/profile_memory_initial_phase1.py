# core/profile_memory.py
# Handles profile ingestion, embedding, and RAG querying
# Setup paths
import os
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
DB_PATH = os.path.join(_PROJECT_ROOT, 'data', 'job_seeker.db')
CHROMA_PATH = os.path.join(_PROJECT_ROOT, 'data', 'chroma_data')

from langchain_ollama import OllamaLLM
import streamlit as st
from sentence_transformers import SentenceTransformer
import chromadb
from .ingest import ingest_profile  # Assuming ingestion.py holds your code

# Global setup
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

embedder = get_embedder()
llm = get_llm()
client = get_chroma_client()
print(f"Chroma_path in profile_memory: {CHROMA_PATH}")


def ingest_and_embed(clear_existing=False):
    from .ingest import ingest_profile
    ingest_profile()

# def ingest_and_embed(clear_existing=False):
    # Run your ingestion pipeline
    # ingest_profile()  # Update with GitHub projects, save to SQLite, embed in ChromaDB
    # Note: Your code already handles this; just call it here

def query_rag(query, job_desc=""):
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
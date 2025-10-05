# core/profile_memory_resume_phase2.py

import streamlit as st
import chromadb
from langchain_ollama.llms import OllamaLLM
import os
import re

# --- Setup Paths ---
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
CHROMA_PATH = os.path.join(_PROJECT_ROOT, 'data', 'chroma_data')

# --- Cached Resource Loading ---
@st.cache_resource
def get_llm():
    print("Loading LLM model...")
    return OllamaLLM(model="phi4-mini") # No 'format="json"' needed

@st.cache_resource
def get_chroma_client():
    print("Initializing ChromaDB client...")
    return chromadb.PersistentClient(path=CHROMA_PATH)

# --- The Main Generation Function ---

def generate_document_and_reasoning(job_title: str, job_desc: str, doc_type: str = "resume") -> dict:
    """
    A direct RAG function that generates both the document text and the AI's reasoning.
    """
    llm = get_llm()
    client = get_chroma_client()

    # 1. Intelligent RAG Context Retrieval
    query_map = {
        "skills": f"Relevant skills for a '{job_title}' role?",
        "experience": f"Past job experiences relevant to: {job_desc}?",
        "projects": f"Projects that showcase skills for this job: {job_desc}?"
    }
    context = ""
    for coll_name, query in query_map.items():
        try:
            collection = client.get_collection(coll_name)
            results = collection.query(query_texts=[query], n_results=3)
            if results and results.get('documents'):
                context += f"## Relevant {coll_name}:\n" + "\n".join(results['documents'][0]) + "\n\n"
        except Exception as e:
            print(f"Error querying collection '{coll_name}': {e}")
    
    if not context:
        return {"document": "Error: No profile data found.", "reasoning": "Failed to retrieve context from ChromaDB."}

    # 2. Direct Instruction Prompting for Structured Text
    persona_prompt = "Act as an expert career coach for Manu Martin. Your tone is professional and achievement-oriented."
    
    resume_prompt = f"""{persona_prompt}
    Based ONLY on the user profile below, generate the content for a resume targeted at the job of '{job_title}'.

    You MUST GENERATE the following sections, each with a bolded title (e.g., **Professional Summary**):
    1. **Professional Summary**
    2. **Key Skills**
    3. **Relevant Experience**
    4. **Key Projects**

    Do NOT include an 'Education' section.


    USER PROFILE:
    ---
    {context}
    ---
    JOB DESCRIPTION:
    ---
    {job_desc}
    ---

    After generating the resume sections, add a final section titled **Reasoning** and explain, in 2-3 sentences, why you chose the specific skills and projects for this job.
    """
    
    # (You can create a similar high-quality prompt for "cover_letter")
    
    prompt = resume_prompt # Use the resume prompt for this example
    
    print("--- [AI Core] Generating document text and reasoning... ---")
    raw_response = llm.invoke(prompt)
    
    # 3. Parse the output
    document = raw_response
    reasoning = "No reasoning was generated."
    
    if "**Reasoning**" in raw_response:
        parts = raw_response.split("**Reasoning**")
        document = parts[0].strip()
        reasoning = parts[1].strip()
    elif "### Reasoning" in raw_response:
        parts = raw_response.split("### Reasoning")
        document = parts[0].strip()
        reasoning = parts[1].strip()
    elif "###Reasoning" in raw_response:
        parts = raw_response.split("###Reasoning")
        document = parts[0].strip()
        reasoning = parts[1].strip()
        
    return {"document": document, "reasoning": reasoning}
import chromadb
import json
import re
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama.llms import OllamaLLM
from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv

# --- Setup Paths ---
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
CHROMA_PATH = os.path.join(_PROJECT_ROOT, 'data', 'chroma_data')

load_dotenv(os.path.join(_PROJECT_ROOT, '.env'))

# --- LLM Factory ---
def get_llm(provider="gemini", model_name=None, temperature=0.7):
    """
    Factory function to get the LLM instance based on provider.
    """
    print(f"Initializing LLM: Provider={provider}, Model={model_name}")
    
    if provider == "gemini":
        if not os.getenv("GOOGLE_API_KEY"):
            raise ValueError("GOOGLE_API_KEY not found in .env file.")
        model = model_name if model_name else "gemini-2.0-flash-lite"
        return ChatGoogleGenerativeAI(model=model, temperature=temperature)
        
    elif provider == "ollama":
        model = model_name if model_name else "phi4" # Default to a capable local model
        return OllamaLLM(model=model, temperature=temperature)
        
    elif provider == "groq":
        if not os.getenv("GROQ_API_KEY"):
            raise ValueError("GROQ_API_KEY not found in .env file.")
        model = model_name if model_name else "llama3-70b-8192"
        return ChatGroq(model_name=model, temperature=temperature)
    
    else:
        raise ValueError(f"Unknown provider: {provider}")


def get_chroma_client():
    print("Initializing ChromaDB client...")
    return chromadb.PersistentClient(path=CHROMA_PATH)

def parse_json_output(text):
    """
    Robustly extracts and parses JSON from a string, handling markdown code blocks.
    """
    try:
        # 1. Try direct parsing
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2. Extract from markdown code blocks ```json ... ```
    match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
            
    # 3. Extract from simple code blocks ``` ... ```
    match = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    print(f"Failed to parse JSON. Raw output:\n{text}")
    return None

def get_rag_context(job_title: str, job_desc: str, client) -> str:
    """
    Queries ChromaDB to retrieve relevant context.
    """
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
    return context

# --- Main Generation Functions ---

def ingest_and_embed(clear_existing=False):
    from .ingest import ingest_profile
    ingest_profile()

def generate_resume_and_reasoning(job_title: str, job_desc: str, provider="gemini", model_name=None) -> dict:
    """
    Generates resume content in JSON format using RAG.
    """
    llm = get_llm(provider, model_name)
    client = get_chroma_client()
    context = get_rag_context(job_title, job_desc, client)
    
    if not context:
        return {"document": {}, "reasoning": "Failed to retrieve context from ChromaDB."}

    prompt = f"""
    Act as an expert career coach. Based on the USER PROFILE and JOB DESCRIPTION below, generate a JSON object for a resume.
    
    USER PROFILE:
    ---
    {context}
    ---
    JOB DESCRIPTION:
    ---
    {job_desc}
    ---

    **INSTRUCTIONS:**
    1. Analyze the profile and select the most relevant skills, experience, and projects for the job.
    2. Output a VALID JSON object with the following structure:
    {{
        "summary": "A strong 3-4 sentence professional summary tailored to the job.",
        "skills": "A list of key technical and soft skills, separated by commas or bullets.",
        "experience": "Detailed bullet points of relevant work experience. Use action verbs.",
        "projects": "Descriptions of key projects that demonstrate required skills.",
        "reasoning": "Brief explanation (2-3 sentences) of why you chose these specific details."
    }}
    3. Do NOT include any text outside the JSON object.
    """
    
    print("--- [AI Core] Generating resume (JSON)... ---")
    raw_response = llm.invoke(prompt)
    content = raw_response.content if hasattr(raw_response, 'content') else str(raw_response)
    parsed_json = parse_json_output(content)
    
    if parsed_json:
        return {
            "document": {
                "summary": parsed_json.get("summary", ""),
                "skills": parsed_json.get("skills", ""),
                "experience": parsed_json.get("experience", ""),
                "projects": parsed_json.get("projects", "")
            },
            "reasoning": parsed_json.get("reasoning", "")
        }
    else:
        return {
            "document": {
                "summary": "Error parsing AI response.",
                "skills": "",
                "experience": "",
                "projects": ""
            },
            "reasoning": "The AI did not return valid JSON."
        }

def generate_coverletter_and_reasoning(job_title: str, job_desc: str, provider="gemini", model_name=None) -> dict:
    """
    Generates a cover letter in JSON format using RAG.
    """
    llm = get_llm(provider, model_name)
    client = get_chroma_client()
    context = get_rag_context(job_title, job_desc, client)
    
    if not context:
        return {"document": "Failed to retrieve context from ChromaDB.", "reasoning": "Failed to retrieve context."}

    prompt = f"""
    Act as an expert career coach. Write a compelling cover letter for the role of '{job_title}'.
    
    USER PROFILE:
    ---
    {context}
    ---
    JOB DESCRIPTION:
    ---
    {job_desc}
    ---

    **INSTRUCTIONS:**
    1. Output a VALID JSON object with the following structure:
    {{
        "cover_letter_content": "The full text of the cover letter (3 paragraphs). Use \\n for line breaks.",
        "reasoning": "Brief explanation of the strategy used."
    }}
    2. Do NOT include any text outside the JSON object.
    """
    
    print("--- [AI Core] Generating cover letter (JSON)... ---")
    raw_response = llm.invoke(prompt)
    content = raw_response.content if hasattr(raw_response, 'content') else str(raw_response)
    parsed_json = parse_json_output(content)
    
    if parsed_json:
        return {
            "document": parsed_json.get("cover_letter_content", ""), 
            "reasoning": parsed_json.get("reasoning", "")
        }
    else:
        return {
            "document": "Error parsing AI response.", 
            "reasoning": "The AI did not return valid JSON."
        }
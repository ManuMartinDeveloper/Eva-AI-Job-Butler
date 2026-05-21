import os
import sys

# --- Setup Paths ---
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
sys.path.append(_PROJECT_ROOT)

from core.profile_memory_resume_phase2 import get_llm

def generate_linkedin_post(topic="AI Trends"):
    """
    Generates a LinkedIn post based on a topic and Manu's profile.
    """
    llm = get_llm()
    prompt = f"""
    Act as a professional career coach and personal branding expert for Manu Martin, an AI Engineer.
    Write a LinkedIn post about "{topic}".
    
    **Style Guide:**
    - Professional yet engaging.
    - Use 1-2 relevant hashtags.
    - Keep it under 200 words.
    - Highlight Manu's expertise in AI/ML.
    
    **Content:**
    """
    response = llm.invoke(prompt)
    return response.content

def generate_outreach_message(recipient_name, company, role):
    """
    Generates a cold outreach message for a recruiter.
    """
    llm = get_llm()
    prompt = f"""
    Write a short, professional LinkedIn connection request message (max 300 chars) to {recipient_name}, a recruiter at {company}.
    Manu Martin is interested in the {role} position.
    
    **Key Points:**
    - Mention interest in {company}.
    - Mention relevant AI experience.
    - Polite call to action.
    """
    response = llm.invoke(prompt)
    return response.content

if __name__ == "__main__":
    print("--- Testing PR Agent ---")
    print("\n[LinkedIn Post]")
    print(generate_linkedin_post("The future of Autonomous Agents"))
    
    print("\n[Outreach Message]")
    print(generate_outreach_message("Sarah", "Google", "Senior AI Engineer"))

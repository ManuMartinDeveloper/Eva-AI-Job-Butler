# core/cold_mailer.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import os
import sqlite3
from email.mime.text import MIMEText
from core.profile_memory_initial_phase1 import query_rag
from datetime import datetime, timedelta
import base64


import os
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
DB_PATH = os.path.join(_PROJECT_ROOT, 'data', 'job_seeker.db')
CHROMA_PATH = os.path.join(_PROJECT_ROOT, 'data', 'chroma_data')


SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def get_gmail_service():
    creds = None
    if os.path.exists('token.json'):
        with open('token.json', 'r') as token:
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

def create_message(sender, to, subject, message_text):
    """Create a message for an email."""
    message = MIMEText(message_text)
    message["to"] = to
    message["from"] = sender
    message["subject"] = subject
    # Encode the message in base64url format
    return {"raw": base64.urlsafe_b64encode(message.as_bytes()).decode()}

def send_cold_email(recipient, job_title, job_desc=""):
    service = get_gmail_service()
    profile_intro = query_rag(" Generate a professional intro for a job application", job_desc)
    # message = f"Subject: Application for {job_title}\n\n{profile_intro}\n\nPlease find my details at https://manumartin.streamlit.app.\nBest,\nManu Martin\n+91 8746 960082"
    # raw_message = base64.urlsafe_b64encode(message.encode()).decode()
    # message = {'raw': raw_message}
    # print("Prepared message:", message)
    message = create_message("me", recipient, f"Application for {job_title}", f"{profile_intro}\n\nPlease find my details at https://manumartin.streamlit.app.\n+91 8746 960082")
    try:
        sent = service.users().messages().send(userId="me", body=message).execute()
        print(f"Email sent, ID: {sent['id']}")
        return sent['id']
    except Exception as e:
        print(f"Error sending email: {e}")
        return None

def log_followup(email_id, follow_up_date):
    conn = sqlite3.connect("job_seeker.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS followups 
                (email_id TEXT PRIMARY KEY, follow_up_date TEXT, status TEXT)''')
    c.execute("INSERT OR REPLACE INTO followups (email_id, follow_up_date, status) VALUES (?, ?, ?)",
              (email_id, follow_up_date, "Sent"))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    des = '''Support Engineer – AI Automation (Homeowners Insurance)
Location: InfoPark, Cochin, India
Job Type: Full-Time
Reports To: Director of AI Operations / Support Automation Lead

Job Summary
We are looking for a proactive and technically adept Support Engineer to join our AI Enablement team at InfoPark, Cochin. This role sits at the critical junction of AI technology and customer support operations, focusing on the homeowners insurance domain. You’ll help train and deploy AI models to automate support tasks, optimize intelligent tools for underwriting and claims workflows, and improve customer and agent interactions across digital channels—while continuing to support existing manual tasks.

Key Responsibilities
· AI Model Training & Data Curation
· Prepare, label, and validate underwriting and claims support data and documents to train models for tasks related to underwriting and claims workflows and responding to insured inquiries.
· Support Workflow Automation
Partner with AI engineers to build and refine automation for routine tasks such as document verification, claims intake, estimate reviews, and chat-based interactions.
· Performance Monitoring & Feedback
Continuously evaluate AI performance in production, identify gaps, and provide actionable feedback to enhance model accuracy and usability.
· Cross-Functional Collaboration
Serve as a key liaison between the AI development team and customer support teams, ensuring tools meet operational requirements and frontline needs.
· Training & Enablement
Onboard support staff on AI-driven tools and gather user feedback to guide tool enhancements.
· System Maintenance & Troubleshooting
Monitor system reliability, escalate technical issues, and support the stability of AI tools across platforms.
· Documentation & Standards
Maintain internal documentation for data labeling standards, model training processes, and tool usage protocols and develop requirements documents for tool enhancements.

Required Qualifications
· 2+ years in technical support, customer support, or insurance operations (preferably in homeowners insurance)
· Familiarity with insurance workflows—especially policy servicing and claims handling
· Basic understanding of AI/ML concepts, especially Natural Language Processing (NLP)
· Strong analytical and troubleshooting skills
· Experience with support platforms like Zendesk, HubSpot or Salesforce
· Excellent interpersonal and communication skills

Preferred Qualifications
· Experience labeling or training datasets for AI/chatbot models
· Exposure to tools like chatGPT, Gemini, Copilot, etc.
· Knowledge of data privacy practices and compliance standards in the insurance sector
· Basic proficiency in Python or SQL for data handling

Why Join Us
· Play a central role in transforming the insurance industry with AI
· Collaborate with global, cross-functional teams at the cutting edge of support automation
· Work from a modern, innovation-driven environment at InfoPark, Cochin
· Enjoy a flexible, inclusive work culture with growth opportunities in AI and insurance technology
If this opportunity aligns with your career goals, kindly share your updated resume with us at hr@inerg.com'''
    email_id = send_cold_email("manu.reshma.martin@gmail.com", "AIML Engineer", des)
    if email_id:
        log_followup(email_id, (datetime.now() + timedelta(days=7)).isoformat())
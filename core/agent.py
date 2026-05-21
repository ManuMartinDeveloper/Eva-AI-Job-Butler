import time
import threading
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import sys
import os

# --- Setup Paths ---
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
sys.path.append(_PROJECT_ROOT)

from core.db import SessionLocal, AgentLog, Job, init_db

class EvaAgent:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.is_running = False
        init_db() # Ensure DB exists
        
    def start(self):
        if not self.is_running:
            print("🤖 Eva Agent Starting...")
            self.scheduler.add_job(self.task_scout_jobs, 'interval', hours=4, id='scout_jobs')
            self.scheduler.add_job(self.task_pr_brainstorm, 'interval', hours=12, id='pr_brainstorm')
            self.scheduler.start()
            self.is_running = True
            self.log_action("System", "Agent Started", "Success")
            
    def stop(self):
        if self.is_running:
            print("🛑 Eva Agent Stopping...")
            self.scheduler.shutdown()
            self.is_running = False
            self.log_action("System", "Agent Stopped", "Success")

    def log_action(self, action, details, status="Success"):
        session = SessionLocal()
        try:
            log = AgentLog(action=action, details=details, status=status)
            session.add(log)
            session.commit()
            print(f"[{datetime.now().strftime('%H:%M')}] {action}: {details}")
        except Exception as e:
            print(f"Error logging action: {e}")
        finally:
            session.close()

    # --- Tasks ---
    
    def task_scout_jobs(self):
        """
        Runs the job scout script and imports results to the main DB.
        """
        self.log_action("Scout", "Starting scheduled job scout...", "Running")
        try:
            # Import here to avoid circular imports or early init
            from scrapers.job_scout import fetch_and_save_jobs
            
            # Run the scout
            jobs_df = fetch_and_save_jobs(results_wanted=20)
            
            if not jobs_df.empty:
                # Sync with main DB
                session = SessionLocal()
                new_count = 0
                for _, row in jobs_df.iterrows():
                    # Check if exists
                    exists = session.query(Job).filter_by(url=row['job_url']).first()
                    if not exists:
                        new_job = Job(
                            title=row['title'],
                            company=row['company'],
                            location=row['location'],
                            description=row['description'],
                            url=row['job_url'],
                            date_posted=str(row['date_posted']),
                            salary=str(row['salary_source']),
                            site=row['site'],
                            email=str(row['emails'])
                        )
                        session.add(new_job)
                        new_count += 1
                session.commit()
                session.close()
                self.log_action("Scout", f"Scout complete. Found {new_count} new jobs.", "Success")
                
                # Automatically trigger evaluation for new jobs
                self.task_evaluate_jobs()
            else:
                self.log_action("Scout", "Scout complete. No jobs found.", "Success")
                
        except Exception as e:
            self.log_action("Scout", f"Scout failed: {str(e)}", "Failed")

    def task_evaluate_jobs(self, provider="gemini", model_name=None):
        """
        Autonomous Agentic AI Reasoning Loop to evaluate unscored jobs using ReAct pattern.
        """
        self.log_action("Scout", "Autonomous Job Evaluation Cycle Started", "Running")
        session = SessionLocal()
        try:
            # Find jobs that are unscored or have fit_score = 0
            jobs = session.query(Job).filter((Job.fit_score == 0) | (Job.fit_score == None)).all()
            if not jobs:
                self.log_action("Scout", "No unscored jobs found for evaluation.", "Success")
                return

            self.log_action("Scout", f"Found {len(jobs)} unscored jobs to evaluate.", "Running")
            
            from core.profile_memory_resume_phase2 import get_llm, get_chroma_client, get_rag_context, parse_json_output
            chroma_client = get_chroma_client()
            
            for job in jobs:
                self.log_action("Thought", f"Analyzing requirements for '{job.title}' at '{job.company}'...", "Running")
                time.sleep(0.5) # Slight pacing
                
                # Fetch RAG context
                self.log_action("Action", f"Querying profile vector memory for '{job.title}' skills...", "Running")
                context = get_rag_context(job.title, job.description or "", chroma_client)
                
                if not context.strip():
                    self.log_action("Observation", "No relevant facts found in vector database. Checking SQL database facts...", "Running")
                    from core.db import ProfileFact
                    db_facts = session.query(ProfileFact).all()
                    if db_facts:
                        context = "## Candidate Profile Facts:\n" + "\n".join([f"- [{f.category}] {f.fact}" for f in db_facts])
                    else:
                        context = "No profile facts or resume data found. Please upload a profile or resume."
                else:
                    self.log_action("Observation", f"Retrieved matching profile context. Querying LLM for fit assessment...", "Running")
                
                # Build agentic reasoning prompt
                prompt = f"""
You are Eva, the autonomous Agentic AI Job Butler. Your goal is to analyze if the candidate is a good match for the job description.
Perform a step-by-step reasoning cycle (Thought -> Action -> Observation -> Decision) and output a JSON response.

CANDIDATE PROFILE CONTEXT (RAG):
---
{context}
---

JOB DETAILS:
Job Title: {job.title}
Company: {job.company}
Location: {job.location}
Job Description:
---
{job.description}
---

**INSTRUCTIONS:**
1. Perform an in-depth match assessment. Identify required skills, frameworks, and years of experience.
2. Formulate your reasoning using the ReAct (Thought/Action/Observation) paradigm:
   - THOUGHT: Analyze the job description and candidate facts. Identify alignment and discrepancies.
   - ACTION/OBSERVATION: Compare the specific skills/experiences needed with what the candidate has.
   - DECISION: Determine the final fit score (0 to 100), gap analysis, and tailored recommendations.
3. Output a VALID JSON object with the following schema:
{{
  "thought_process": "Detailed thoughts of your requirements vs skills analysis.",
  "gap_analysis": "Identify specific skills, tools, or experience gaps.",
  "fit_score": 85, // integer 0-100
  "fit_reasoning": "A concise 2-3 sentence summary explaining the fit score and key reasons, to be displayed directly on the UI dashboard.",
  "recommendations": "Actionable advice on what projects/skills to emphasize or add to the resume for this role.",
  "should_auto_apply": true // set to true only if fit_score >= 80 and candidate is a strong fit
}}
Do NOT output any markdown tags or text outside of the JSON object.
"""
                try:
                    llm = get_llm(provider=provider, model_name=model_name)
                    response = llm.invoke(prompt)
                    content = response.content if hasattr(response, 'content') else str(response)
                    parsed_json = parse_json_output(content)
                    
                    if parsed_json:
                        fit_score = int(parsed_json.get("fit_score", 0))
                        fit_reasoning = parsed_json.get("fit_reasoning", "")
                        thought = parsed_json.get("thought_process", "")
                        gaps = parsed_json.get("gap_analysis", "")
                        recs = parsed_json.get("recommendations", "")
                        should_apply = parsed_json.get("should_auto_apply", False)
                        
                        # Format reasoning content with structured metadata
                        full_reasoning = f"Score: {fit_score}%\n\nGap Analysis:\n{gaps}\n\nRecommendations:\n{recs}\n\nReasoning:\n{fit_reasoning}"
                        
                        # Update database
                        job.fit_score = fit_score
                        job.fit_reasoning = full_reasoning
                        session.add(job)
                        session.commit()
                        
                        # Log thought logs for terminal
                        self.log_action("Thought", f"[{job.title}] {thought[:100]}...", "Success")
                        self.log_action("Observation", f"Gaps: {gaps[:100]}", "Success")
                        self.log_action("Decision", f"Job '{job.title}' rated {fit_score}%. Should auto-apply: {should_apply}", "Success")
                        
                        # Automatically trigger auto-apply if eligible
                        if should_apply:
                            self.log_action("Apply", f"Automatic auto-apply triggered for {job.title} at {job.company}!", "Success")
                            from backend.routers.jobs import run_apply_task
                            run_apply_task(job.url)
                    else:
                        self.log_action("Scout", f"Failed to parse agent reasoning JSON for job {job.id}.", "Failed")
                except Exception as eval_err:
                    self.log_action("Scout", f"Error during evaluation of job {job.id}: {str(eval_err)}", "Failed")
            
            self.log_action("Scout", "Autonomous Evaluation Cycle Completed successfully.", "Success")
        except Exception as e:
            self.log_action("Scout", f"Evaluation failed: {str(e)}", "Failed")
        finally:
            session.close()

    def task_pr_brainstorm(self):
        """
        Placeholder for PR task.
        """
        self.log_action("PR", "Brainstorming LinkedIn content...", "Pending")
        # TODO: Implement PR Agent logic here

# Singleton instance
agent = EvaAgent()

if __name__ == "__main__":
    # Test run
    agent.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        agent.stop()

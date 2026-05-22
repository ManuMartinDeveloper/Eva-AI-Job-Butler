# core/tasks.py
import os
import sys
import subprocess
from typing import Optional
import dramatiq
from dramatiq.brokers.redis import RedisBroker

# --- Setup Paths ---
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
sys.path.append(_PROJECT_ROOT)

from core.db import SessionLocal, AgentLog, Job, Application

REDIS_URL = os.environ.get("REDIS_URL")
USE_QUEUE = False

if REDIS_URL:
    try:
        broker = RedisBroker(url=REDIS_URL)
        dramatiq.set_broker(broker)
        USE_QUEUE = True
        print(f"Queue configured using Redis broker at {REDIS_URL}")
    except Exception as e:
        print(f"Failed to configure Redis broker: {e}. Falling back to direct execution.")

def run_scout_task(search_term: str, location: str, limit: int, user_id: int):
    """Run the job scout scraper script in a subprocess and log the action."""
    db = SessionLocal()
    log = AgentLog(user_id=user_id, action="Scout", details=f"Manual scout started for '{search_term}' in '{location}'", status="Running")
    db.add(log)
    db.commit()
    db.refresh(log)
    
    try:
        # Run scraper script as a subprocess
        process = subprocess.run(
            [sys.executable, "scrapers/job_scout.py", "--search", search_term, "--location", location, "--limit", str(limit)],
            cwd=_PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        
        # Check for database synchronization from CSV
        import sqlite3
        seeker_db_path = os.path.join(_PROJECT_ROOT, 'data', 'job_seeker.db')
        if os.path.exists(seeker_db_path):
            conn = sqlite3.connect(seeker_db_path)
            c = conn.cursor()
            c.execute("SELECT title, company, location, description, url, date_posted, salary, site, email FROM jobs ORDER BY id DESC LIMIT ?", (limit * 2,))
            scraped_jobs = c.fetchall()
            conn.close()
            
            new_count = 0
            for row in scraped_jobs:
                title, company, loc, desc, url, date_posted, salary, site, email = row
                exists = db.query(Job).filter_by(url=url, user_id=user_id).first()
                if not exists:
                    new_job = Job(
                        user_id=user_id,
                        title=title,
                        company=company,
                        location=loc,
                        description=desc,
                        url=url,
                        date_posted=date_posted,
                        salary=salary,
                        site=site,
                        email=email
                    )
                    db.add(new_job)
                    new_count += 1
            db.commit()
            log.details = f"Scout complete. Found {new_count} new jobs."
            log.status = "Success"
            
            # Trigger evaluation for the newly scouted jobs for this user
            from core.agent import agent
            agent.task_evaluate_jobs(user_id=user_id)
        else:
            log.details = "Scout completed but job_seeker.db was not found."
            log.status = "Failed"
            
    except Exception as e:
        log.details = f"Scout failed: {str(e)}"
        log.status = "Failed"
    finally:
        db.commit()
        db.close()

def run_apply_task(job_url: str, provider: str = "gemini", model: Optional[str] = None, user_id: Optional[int] = None, wait_for_completion: bool = False):
    """Launches the Playwright form filler in the background or synchronously."""
    if not user_id:
        print("Error: user_id is required to run auto_apply task.")
        return
        
    # Delete old session/screenshot files under user directory to prevent frontend displaying stale data
    user_output_dir = os.path.join(_PROJECT_ROOT, "outputs", str(user_id))
    session_path = os.path.join(user_output_dir, "agent_session.json")
    screenshot_path = os.path.join(user_output_dir, "agent_screenshot.png")
    
    if os.path.exists(session_path):
        try:
            os.remove(session_path)
        except Exception as e:
            print(f"Could not remove old session file for user {user_id}: {e}")
            
    if os.path.exists(screenshot_path):
        try:
            os.remove(screenshot_path)
        except Exception as e:
            print(f"Could not remove old screenshot for user {user_id}: {e}")
            
    try:
        cmd = [
            sys.executable, 
            "core/auto_apply.py", 
            "--url", job_url, 
            "--user-id", str(user_id), 
            "--provider", provider
        ]
        if model:
            cmd.extend(["--model", model])
            
        if wait_for_completion:
            process = subprocess.run(
                cmd,
                cwd=_PROJECT_ROOT,
                capture_output=True,
                text=True
            )
            if process.returncode != 0:
                print(f"Auto apply subprocess failed for user {user_id} with returncode {process.returncode}")
                print(f"Stderr: {process.stderr}")
                raise Exception(f"Playwright solver failed: {process.stderr}")
        else:
            subprocess.Popen(
                cmd,
                cwd=_PROJECT_ROOT
            )
    except Exception as e:
        print(f"Error launching auto apply for user {user_id}: {e}")
        if wait_for_completion:
            raise e

@dramatiq.actor(max_retries=1)
def scout_jobs_task(search_term: str, location: str, limit: int, user_id: int):
    run_scout_task(search_term, location, limit, user_id)

@dramatiq.actor(max_retries=0)
def auto_apply_task(job_url: str, user_id: int, provider: str, model: Optional[str] = None):
    run_apply_task(job_url, provider, model, user_id, wait_for_completion=True)

def trigger_scout_jobs(search_term: str, location: str, limit: int, user_id: int, background_tasks=None):
    if USE_QUEUE:
        scout_jobs_task.send(search_term, location, limit, user_id)
        print(f"Scout task queued via Dramatiq for user {user_id}")
    else:
        if background_tasks:
            background_tasks.add_task(run_scout_task, search_term, location, limit, user_id)
            print(f"Scout task added to FastAPI background_tasks for user {user_id}")
        else:
            import threading
            t = threading.Thread(target=run_scout_task, args=(search_term, location, limit, user_id))
            t.daemon = True
            t.start()
            print(f"Scout task started in local thread for user {user_id}")

def trigger_auto_apply(job_url: str, user_id: int, provider: str = "gemini", model: Optional[str] = None, background_tasks=None):
    if USE_QUEUE:
        auto_apply_task.send(job_url, user_id, provider, model)
        print(f"Auto-apply task queued via Dramatiq for user {user_id}")
    else:
        if background_tasks:
            background_tasks.add_task(run_apply_task, job_url, provider, model, user_id, False)
            print(f"Auto-apply task added to FastAPI background_tasks for user {user_id}")
        else:
            import threading
            t = threading.Thread(target=run_apply_task, args=(job_url, provider, model, user_id, False))
            t.daemon = True
            t.start()
            print(f"Auto-apply task started in local thread for user {user_id}")

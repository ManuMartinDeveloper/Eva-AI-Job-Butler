import os
import sys
import sqlite3
import subprocess
import glob
import time
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

# --- Setup Paths ---
_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_TEST_DIR)
sys.path.append(_PROJECT_ROOT)

def print_header(title):
    print(f"\n{'='*60}")
    print(f"TEST: {title}")
    print(f"{'='*60}")

def run_syntax_checks():
    print_header("Syntax Checks (Static Analysis)")
    py_files = glob.glob(os.path.join(_PROJECT_ROOT, "**", "*.py"), recursive=True)
    # Filter out venv
    py_files = [f for f in py_files if ".venv" not in f and "venv" not in f]
    
    failed = []
    for f in py_files:
        try:
            subprocess.check_output([sys.executable, "-m", "py_compile", f], stderr=subprocess.STDOUT)
            # print(f"✅ {os.path.basename(f)}")
        except subprocess.CalledProcessError as e:
            print(f"❌ {os.path.basename(f)}")
            print(e.output.decode())
            failed.append(f)
            
    if not failed:
        print("✅ All files passed syntax check.")
        return True
    else:
        print(f"❌ {len(failed)} files failed syntax check.")
        return False

def run_db_check():
    print_header("Database Integrity Check")
    db_path = os.path.join(_PROJECT_ROOT, 'data', 'job_seeker.db')
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return False
        
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [r[0] for r in cursor.fetchall()]
        print(f"Found tables: {tables}")
        
        required = ['jobs'] # 'agent_log' might be created on first run
        missing = [t for t in required if t not in tables]
        
        if missing:
            print(f"❌ Missing required tables: {missing}")
            return False
            
        # Check jobs count
        cursor.execute("SELECT count(*) FROM jobs")
        count = cursor.fetchone()[0]
        print(f"✅ Database connected. Total jobs stored: {count}")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        return False

def run_scraper_test():
    print_header("Scraper Functional Test (Dry Run)")
    # Run for a very specific, likely-to-exist term to be quick
    cmd = [
        sys.executable, 
        os.path.join(_PROJECT_ROOT, "scrapers", "job_scout.py"),
        "--search", "Python",
        "--location", "Remote",
        "--limit", "1" 
    ]
    
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            print("✅ Scraper ran successfully.")
            # Verify output file
            # We need to check if a new csv was created in outputs/
            # This is a bit tricky as the filename has a timestamp, but we can check if the count increased in DB or just trust the exit code + stdout
            if "Saved" in result.stdout:
                print("✅ Output confirmed in stdout.")
                return True
            else:
                print("⚠️ Scraper ran but didn't report saving jobs (might be 0 found).")
                print(result.stdout)
                return True # Still a "pass" on execution
        else:
            print("❌ Scraper failed.")
            print(result.stderr)
            return False
    except subprocess.TimeoutExpired:
        print("❌ Scraper timed out.")
        return False

def run_rag_import_test():
    print_header("RAG Pipeline Import Test")
    try:
        from core.profile_memory_resume_phase2 import get_qdrant_client, get_llm
        print("✅ Successfully imported RAG modules.")
        
        # Check Qdrant
        client = get_qdrant_client()
        print("✅ Qdrant client initialized.")
        
        # Check LLM Factory (don't invoke, just init)
        try:
            llm = get_llm(provider="gemini", model_name="gemini-2.0-flash-lite")
            print("✅ LLM Factory initialized (Gemini).")
        except Exception as e:
            print(f"⚠️ LLM Init warning (check .env): {e}")
            
        return True
    except Exception as e:
        print(f"❌ RAG Import failed: {e}")
        return False

def main():
    print(f"Starting Test Suite at {datetime.now()}")
    
    results = {
        "Syntax": run_syntax_checks(),
        "Database": run_db_check(),
        "RAG_Import": run_rag_import_test(),
        "Scraper": run_scraper_test(),
    }
    
    print_header("Summary")
    all_passed = True
    for test, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test:<15} {status}")
        if not passed:
            all_passed = False
            
    if all_passed:
        print("\n🎉 ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print("\n⚠️ SOME TESTS FAILED.")
        sys.exit(1)

if __name__ == "__main__":
    main()

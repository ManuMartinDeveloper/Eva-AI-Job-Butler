
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from scrapers.job_scout import fetch_and_save_jobs

print("--- Starting Scraping Reproduction ---")
try:
    jobs = fetch_and_save_jobs(search_term="Python Developer", location="Bengaluru", results_wanted=5)
    print(f"--- Scraping Complete ---")
    print(f"Jobs Found: {len(jobs)}")
    if not jobs.empty:
        print(jobs[['title', 'company', 'site']].head())
    else:
        print("No jobs returned.")
except Exception as e:
    print(f"--- Scraping Failed ---")
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

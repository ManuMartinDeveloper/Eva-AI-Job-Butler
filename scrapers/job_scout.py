#scrapers/job_scout.py

import os
import sqlite3
import csv
import pandas as pd
from jobspy import scrape_jobs
from datetime import datetime

# --- Configuration ---
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
OUTPUT_PATH = os.path.join(_PROJECT_ROOT, 'data', 'jobs_details')

def fetch_and_save_jobs(search_term="AIML Engineer", location="Bengaluru", results_wanted=50, hours_old=48):
    """
    Fetches jobs using JobSpy, saves to SQLite and CSV, dedupes by title + company.
    """
    jobs = scrape_jobs(
        site_name=["indeed", "linkedin", "glassdoor", "google"],  # Add "naukri", "zip_recruiter" for India focus
        search_term=search_term,
        location=location,
        results_wanted=results_wanted,
        hours_old=hours_old,
        country_indeed="India",  # For Indeed geo
        # proxies=["http://proxy1:port", "http://proxy2:port"]  # If needed
    )
    if jobs.empty:
        print("No jobs found—try broader terms.")
        return pd.DataFrame()
    
    # Dedupe by title + company
    jobs_deduped = jobs.drop_duplicates(subset=["title", "company"])
    
    # Save to CSV
    filename = f"job_leads_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    os.makedirs(OUTPUT_PATH, exist_ok=True)  # Ensure directory exists
    jobs_deduped.to_csv(os.path.join(OUTPUT_PATH, filename), quoting=csv.QUOTE_NONNUMERIC, escapechar="\\", index=False)
    print(f"Saved {len(jobs_deduped)} unique jobs to {filename}")

    # Store in SQLite
    conn = sqlite3.connect(os.path.join(_PROJECT_ROOT, 'data', 'job_seeker.db'))
    c = conn.cursor()
    
    # Create jobs table if not exists (with url as unique constraint)
    c.execute('''CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        company TEXT,
        location TEXT,
        description TEXT,
        url TEXT UNIQUE,
        date_posted TEXT,
        salary TEXT,
        site TEXT,
        email TEXT,
        scrape_date TEXT,
        UNIQUE(url)
    )''')
    
    # Prepare data for insertion (handle NaN/None)
    jobs_deduped = jobs_deduped.fillna('N/A')  # Replace NaN with 'N/A'
    data = [
        (
            row['title'], row['company'], row['location'], row['description'],
            row['job_url'], row['date_posted'], row['salary_source'], row['site'], row['emails'],
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        for row in jobs_deduped.to_dict('records')
    ]
    
    # Insert or ignore duplicates (based on url)
    c.executemany('INSERT OR IGNORE INTO jobs (title, company, location, description, url, date_posted, salary, site, email, scrape_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', data)
    conn.commit()
    conn.close()
    
    print(f"Stored/updated {len(data)} jobs in SQLite.")
    return jobs_deduped

if __name__ == "__main__":
    df = fetch_and_save_jobs()
    print(df.head())  # Preview
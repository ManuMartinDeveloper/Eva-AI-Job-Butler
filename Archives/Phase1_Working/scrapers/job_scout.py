#scrapers/job_scout.py

#run the initial_login.py to save the session data before running this script
import os
import sqlite3
import csv
import pandas as pd
import argparse
import time
from jobspy import scrape_jobs
from datetime import datetime
from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeoutError
# from playwright_stealth import stealth_sync
from dotenv import load_dotenv


load_dotenv()

# --- Configuration ---
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
OUTPUT_PATH = os.path.join(_PROJECT_ROOT, 'data', 'jobs_details')
SESSION_DATA_PATH = os.path.join(_PROJECT_ROOT, "data", "playwright_session")



LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")

# --- Deep Scraping with Playwright ---
# def get_full_job_description(job_url: str) -> str:
#     """
#     Visits a job URL using Playwright and scrapes the full job description text.
#     NOTE: This requires custom selectors for each job site (LinkedIn, Indeed, etc.).
#     """
#     print(f"Performing deep scrape for URL: {job_url}")
#     description = "Could not retrieve full description."
    
#     with sync_playwright() as p:
#         context = p.chromium.launch_persistent_context(
#             user_data_dir=SESSION_DATA_PATH,
#             headless=False # Can now run in the background
#         )
#         page = context.new_page()
#         print('launched with existing session data')
#         try:
#             page.goto(job_url, timeout=600000000)
            
#             # --- This is the part you MUST customize for each job site ---
#             if "linkedin.com" in job_url:
#                 # page.goto(job_url, timeout=60000)
#                 show_more_button = page.locator("button[aria-label='Click to see more description']")
#                 if show_more_button:
#                     show_more_button.click()
                
#                 # The selector for the main description content on LinkedIn
#                 description_locator = page.locator("div.jobs-description__content.jobs-description-content.jobs-description__content--condensed")
                
#                 description = description_locator.inner_text()
            
#             elif "indeed.com" in job_url:
#                 # The selector for the job description on Indeed
#                 description_locator = page.locator("div#jobDescriptionText")
#                 description = description_locator.inner_text()
            
#             elif "glassdoor.com" in job_url:
#                 show_more_button = page.locator("button[aria-label='Show more, visually expand the content']")
#                 if show_more_button:
#                     show_more_button.click()

#                 # The selector for the job description on Glassdoor
#                 description_locator = page.locator("div.JobDetails_jobDescription__uW_fK.JobDetails_showHidden__C_FOA")
#                 description = description_locator.inner_text()
        # except PlaywrightTimeoutError:
        #     print(f"Timeout while trying to load {job_url}")
        # except Exception as e:
        #     print(f"An error occurred during deep scrape: {e}")
        # finally:
        #     context.close()
                
        # return description


#             # Add more 'elif' blocks for other sites like Glassdoor, Naukri, etc.
def get_full_job_description_connected(page, job_url: str) -> str:
    """Uses an EXISTING page to scrape a URL."""
    try:
        page.goto(job_url, timeout=60000)
        time.sleep(3)
        # --- (Your site-specific selectors for LinkedIn, Indeed, etc. go here) ---
        if "linkedin.com" in job_url:
            show_more_button = page.locator("button[aria-label='Click to see more description']")
            if show_more_button:
                show_more_button.click()
            
            # The selector for the main description content on LinkedIn
            description_locator = page.locator("div.jobs-description__content.jobs-description-content.jobs-description__content--condensed")
            
            description = description_locator.inner_text()        # ... add other sites
            return description
        elif 'glassdoor' in job_url:
            description_locator = page.locator("div.JobDetails_jobDescription__uW_fK.JobDetails_blurDescription__vN7nh")
            description = description_locator.inner_text()
            # apply_on_employer_site = page.locator("button[aria-label='Apply on employer site']")
            # if show_more_button:
            #     show_more_button.click()
            if not description:
                description_locator = page.locator("div.JobDetails_jobDescription__uW_fK.JobDetails_showHidden__C_FOA")
                description = description_locator.inner_text()
        else:
            return f"Site not supported for deep scraping. URL: {job_url}"
    except Exception as e:
        print(f"Error scraping {job_url}: {e}")
        return "Could not retrieve full description."



# --- Job Scraping and Storage ---

def fetch_and_save_jobs(search_term="AIML Engineer", location="Bengaluru", results_wanted=50, hours_old=48):
    """
    Fetches jobs using JobSpy, saves to SQLite and CSV, dedupes by title + company.
    """
    jobs = scrape_jobs(
        site_name=["indeed", "linkedin", "google"],  # Add "naukri", "glassdoor", "zip_recruiter" for India focus
        search_term=search_term,
        location=location,
        results_wanted=results_wanted,
        hours_old=hours_old,
        country_indeed="United Arab Emirates",  # For Indeed geo
        # proxies=["http://proxy1:port", "http://proxy2:port"]  # If needed
    )
    if jobs.empty:
        print("No jobs found—try broader terms.")
        return pd.DataFrame()
    
    # Dedupe by title + company
    jobs_deduped = jobs.drop_duplicates(subset=["title", "company"]).reset_index()


    # --- 2. Perform deep scrape using a connected browser ---
    descriptions = []
    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]
            page = context.new_page()

            for index, row in jobs_deduped.iterrows():
                desc = get_full_job_description_connected(page, row['job_url'])
                descriptions.append(desc)

            page.close()
            jobs_deduped['description'] = descriptions
        except Exception as e:
            print(f"CRITICAL ERROR: Could not connect to browser. Is it running with the debug port? Error: {e}")
            # Still return the partial data from jobspy
            return jobs_deduped

    # Deep scrape job descriptions
    # jobs_deduped['description'] = jobs_deduped.apply(
    #     lambda row: get_full_job_description_connected(row['job_url']) if pd.isna(row.get('description')) or len(row.get('description', '')) < 100 else row['description'],
    #     axis=1
    # )

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
    parser = argparse.ArgumentParser(description="Scrape job listings.")
    parser.add_argument("--search", type=str, default="AI Engineer", help="Job search term")
    parser.add_argument("--location", type=str, default="Bengaluru", help="Job location")
    args = parser.parse_args()
    
    print(f"--- Running job scout manually for {args.search} in {args.location} ---")
    fetch_and_save_jobs(search_term=args.search, location=args.location, results_wanted=20)
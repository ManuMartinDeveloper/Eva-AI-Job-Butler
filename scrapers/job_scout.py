# scrapers/job_scout.py
import os
import sqlite3
import csv
import pandas as pd
import argparse
import time
from jobspy import scrape_jobs
from datetime import datetime
from playwright.sync_api import sync_playwright

# --- Setup Paths ---
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
OUTPUT_PATH = os.path.join(_PROJECT_ROOT, 'outputs')

def get_full_job_description_connected(page, url):
    """
    Navigates to the job URL using Playwright and extracts the full description.
    Handles 'Show More' buttons to ensure complete text is captured.
    """
    try:
        print(f"Navigating to {url}...")
        page.goto(url, timeout=60000)
        time.sleep(3) # Wait for initial load

        # --- Handle "Show More" buttons ---
        show_more_selectors = [
            "button[aria-label='Show more, visually expands previously read content.']", # LinkedIn
            ".show-more-less-html__button", # LinkedIn public
            "#job-details-show-more", # Generic
            "button:has-text('Show more')",
            "button:has-text('See more')",
            "[class*='show-more']",
            "[class*='read-more']"
        ]

        for selector in show_more_selectors:
            try:
                if page.locator(selector).first.is_visible():
                    print(f"Clicking 'Show More' using selector: {selector}")
                    page.locator(selector).first.click()
                    time.sleep(1)
                    break 
            except Exception:
                continue

        # --- Extract Text ---
        description_selectors = [
            ".job-view-layout", # LinkedIn
            ".job-description",
            "#job-description",
            "[class*='description']",
            "article"
        ]
        
        content = ""
        for selector in description_selectors:
             if page.locator(selector).first.is_visible():
                 content = page.locator(selector).first.inner_text()
                 break
        
        if not content:
            content = page.inner_text("body")

        return content

    except Exception as e:
        print(f"Failed to get description for {url}: {e}")
        return "N/A"

def fetch_and_save_jobs(search_term="AI Engineer", location="Bengaluru", results_wanted=20):
    print(f"Scraping jobs for: {search_term} in {location}")
    
    # 1. Initial Search using JobSpy
    try:
        jobs = scrape_jobs(
            site_name=["linkedin", "indeed", "glassdoor"],
            search_term=search_term,
            location=location,
            results_wanted=results_wanted,
            country_indeed='india' # Fixed country code
        )
    except Exception as e:
        print(f"Error during initial scrape: {e}")
        return pd.DataFrame()

    if jobs.empty:
        print("No jobs found—try broader terms.")
        return pd.DataFrame()
    
    # Deduplicate
    jobs_deduped = jobs.drop_duplicates(subset=["title", "company"]).reset_index(drop=True)

    # 2. Deep Scrape for Descriptions
    # We use a real browser session (headless or connected) to maintain "human identity"
    descriptions = []
    with sync_playwright() as p:
        browser = None
        try:
            # Try connecting to an existing debug browser first
            print("Attempting to connect to existing browser on port 9222...")
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            print("Connected to existing browser.")
        except Exception:
            # Fallback to launching a new headless browser
            print("Could not connect to existing browser. Launching new headless browser...")
            browser = p.chromium.launch(headless=True)
        
        if browser:
            try:
                context = browser.contexts[0] if browser.contexts else browser.new_context()
                page = context.new_page()

                for index, row in jobs_deduped.iterrows():
                    desc = get_full_job_description_connected(page, row['job_url'])
                    descriptions.append(desc)

                page.close()
                if len(descriptions) == len(jobs_deduped):
                     jobs_deduped['description'] = descriptions
            except Exception as e:
                 print(f"Error during deep scraping session: {e}")
            finally:
                if browser.is_connected():
                    browser.close()
        else:
            print("Skipping deep scrape due to browser failure.")

    # 3. Save to CSV
    filename = f"job_leads_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    os.makedirs(OUTPUT_PATH, exist_ok=True)
    jobs_deduped.to_csv(os.path.join(OUTPUT_PATH, filename), quoting=csv.QUOTE_NONNUMERIC, escapechar="\\", index=False)
    print(f"Saved {len(jobs_deduped)} unique jobs to {filename}")

    # 4. Store in SQLite
    conn = sqlite3.connect(os.path.join(_PROJECT_ROOT, 'data', 'job_seeker.db'))
    c = conn.cursor()
    
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
        scrape_date TEXT
    )''')
    
    jobs_deduped = jobs_deduped.fillna('N/A')
    data = [
        (
            row['title'], row['company'], row['location'], row['description'],
            row['job_url'], row['date_posted'], row['salary_source'], row['site'], row['emails'],
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        for row in jobs_deduped.to_dict('records')
    ]
    
    c.executemany('INSERT OR IGNORE INTO jobs (title, company, location, description, url, date_posted, salary, site, email, scrape_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', data)
    conn.commit()
    conn.close()
    
    print(f"Stored/updated {len(data)} jobs in SQLite.")
    return jobs_deduped

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape job listings.")
    parser.add_argument("--search", type=str, default="AI Engineer", help="Job search term")
    parser.add_argument("--location", type=str, default="Bengaluru", help="Job location")
    parser.add_argument("--limit", type=int, default=20, help="Number of jobs to scrape")
    args = parser.parse_args()
    
    print(f"--- Running job scout manually for {args.search} in {args.location} (Limit: {args.limit}) ---")
    fetch_and_save_jobs(search_term=args.search, location=args.location, results_wanted=args.limit)
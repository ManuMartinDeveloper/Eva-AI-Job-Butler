# core/setup_sessions.py

import os
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
from playwright_stealth import stealth_sync  # Correct import


load_dotenv()

# --- Configuration ---
# This is the folder where your logged-in session will be saved
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
SESSION_DATA_PATH = os.path.join(_PROJECT_ROOT, "data", "playwright_session")

# --- Get Credentials from .env ---
LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")
# Add other credentials here, e.g., NAUKRI_EMAIL, NAUKRI_PASSWORD

def main():
    """
    Launches a browser, logs into all required sites, and saves the session.
    """
    with sync_playwright() as p:
        # This is the key: launch_persistent_context()
        # It tells Playwright to use and save data to the specified directory.
        context = p.chromium.launch_persistent_context(
            user_data_dir=SESSION_DATA_PATH,
            headless=False, # Must be False to handle logins manually
            slow_mo=500
        )
        page_linkedin = context.new_page()

        # --- Login to LinkedIn ---
        print("Please log in to LinkedIn...")
        stealth_sync(page_linkedin)
        page_linkedin.goto("https://www.linkedin.com/login")
        # The script will try to auto-fill, but you should manually complete the login
        # to handle any CAPTCHAs or 2-Factor Authentication.
        
        # --- Login to Naukri (Example) ---
        # page_naukri = context.new_page() # Use a new tab
        # print("Please log in to Naukri.com...")
        # page_naukri.goto("https://www.naukri.com/nlogin/login")
         
        # # --- Add more login pages as needed ---
        # print("Please login to Glassdoor...")
        # page_glassdoor = context.new_page() # Use a new tab
        # page_glassdoor.goto("https://www.glassdoor.co.in/Community/index.htm")

        # print("Please login to Indeed...")
        # page_indeed = context.new_page() # Use a new tab
        # page_indeed.goto("https://in.indeed.com/")


    # This is for futher Automation of login if needed     
        # page.fill("input#username", LINKEDIN_EMAIL)
        # page.fill("input#password", LINKEDIN_PASSWORD)
        # page.click("button[type='submit']")
        # page.wait_for_url("**/feed/**", timeout=60000)
        # print("Login successful.")
        
        print("\n----------------------------------------------------------------")
        print("All login pages are open. Please complete any necessary logins,")
        print("including CAPTCHAs or 2FA prompts.")
        input("Press Enter here after you have successfully logged in to all sites...")
        print("----------------------------------------------------------------\n")

        # Once you press Enter, the session is saved automatically.
        context.close()
        print("Browser session saved successfully!")

if __name__ == "__main__":
    main()
# core/connect_and_scrape.py

from playwright.sync_api import sync_playwright

def main():
    """
    Connects to an existing browser instance and performs tasks.
    """
    with sync_playwright() as p:
        try:
            # This is the key: connect_over_cdp
            # It connects to the browser you opened manually
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0] # Use the default browser context
            page = context.new_page()

            print("Successfully connected to the existing browser.")
            print("Browser is already logged in.")

            # Now you can perform any scraping task
            # For example, go to LinkedIn jobs
            page.goto("https://www.linkedin.com/jobs/", timeout=60000)
            print("Navigated to LinkedIn jobs successfully.")
            
            # (Your scraping logic would go here)
            
            input("\n>>> Scraping tasks finished. Press Enter to close the script...")

        except Exception as e:
            print(f"Failed to connect to browser. Is it running with the remote debugging port?")
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
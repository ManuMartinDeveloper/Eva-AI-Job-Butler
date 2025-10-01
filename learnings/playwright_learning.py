import asyncio
from playwright.async_api import async_playwright
import time

async def main():
    async with async_playwright() as p:
        # Launch the browser. headless=False means you'll see the browser window.
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # Go to the website
        await page.goto("http://quotes.toscrape.com")

        # Create a locator for all the quote elements on the page
        # A locator is a recipe for finding elements, not the elements themselves.
        quote_locators = page.locator("div.quote")

        # Loop through each quote found by the locator and extract its text
        all_quotes = await quote_locators.all()
        for quote_locator in all_quotes:
            text = await quote_locator.locator(".text").text_content()
            author = await quote_locator.locator(".author").text_content()
            print(f"'{text}' by {author}")

        time.sleep(500)  # Pause to see the results in the browser
        # Close the browser
        await browser.close()

# This is the standard way to run an async main function
if __name__ == "__main__":
    asyncio.run(main())
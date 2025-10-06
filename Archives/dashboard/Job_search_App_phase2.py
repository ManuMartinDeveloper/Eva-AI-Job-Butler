# import asyncio
# import nest_asyncio
# nest_asyncio.apply()

# import sys
# import os
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# import pandas as pd
# import streamlit as st
# from scrapers.job_scout import fetch_and_save_jobs


# st.title("AI Job Butler Dashboard")

# if st.button("Fetch Latest Jobs"):
#     jobs = fetch_and_save_jobs()  # Initial ingest
#     if not jobs.empty:
#         st.dataframe(jobs)
#     st.success("Searched Jobs")

# dashboard/Job_search_App_phase2.py

# --- (Add these imports at the top) ---
import streamlit as st
import subprocess
import sys

st.title("AI Job Butler Dashboard")

# --- UI for Job Search ---
search_term = st.text_input("Job Title to Search", "AI Engineer")
location = st.text_input("Location", "Bengaluru")

if st.button("Fetch Latest Jobs"):
    # --- THIS IS THE NEW, CORRECTED LOGIC ---
    st.info("Starting the job scout... This may take a moment.")
    
    # We will display the live output from the scraper script
    with st.expander("Show Scraper Log"):
        # Use subprocess.Popen to run the script as a separate process
        process = subprocess.Popen(
            [sys.executable, "scrapers/job_scout.py", "--search", search_term, "--location", location],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8'
        )
        
        # Display the output in real-time
        log_container = st.empty()
        log_text = ""
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                log_text += output
                log_container.code(log_text)
    
    st.success("Job search process complete! The latest jobs have been saved to the database.")
    # You might want to add a button to refresh the view of the database here


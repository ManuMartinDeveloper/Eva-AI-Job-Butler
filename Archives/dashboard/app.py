import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import streamlit as st
from core.profile_memory_initial_phase1 import ingest_and_embed, query_rag
from scrapers.job_scout import fetch_and_save_jobs

st.title("AI Job Butler Dashboard")

if st.button("Ingest Profile"):
    ingest_and_embed(clear_existing=True)  # Initial ingest
    st.success("Profile ingested and embedded!")

job_desc = st.text_area("Paste Job Description")
if st.button("Generate Tailored Response"):
    if job_desc:
        response = query_rag("Answer to the questions asked", job_desc)
        st.text_area("Tailored Output", response, height=300)
    else:
        st.write("Please enter a job description.")


if st.button("Fetch Latest Jobs"):
    jobs = fetch_and_save_jobs()  # Initial ingest
    if not jobs.empty:
        st.dataframe(jobs)
    st.success("Searched Jobs")

st.write("Note: Ensure 'ollama pull phi3.5' is run and GitHub token is in .env.")
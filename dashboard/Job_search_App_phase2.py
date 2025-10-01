import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import streamlit as st
from scrapers.job_scout import fetch_and_save_jobs


st.title("AI Job Butler Dashboard")

if st.button("Fetch Latest Jobs"):
    jobs = fetch_and_save_jobs()  # Initial ingest
    if not jobs.empty:
        st.dataframe(jobs)
    st.success("Searched Jobs")



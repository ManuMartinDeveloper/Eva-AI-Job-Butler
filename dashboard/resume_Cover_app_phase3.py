import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import pandas as pd
import sqlite3
from scrapers.job_scout import fetch_and_save_jobs
from core.profile_memory_resume_phase2 import query_rag, ingest_and_embed
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime

st.title("AI Job Butler Dashboard")

if st.button("Ingest Profile"):
    ingest_and_embed(clear_existing=True)
    st.success("Profile ingested and embedded!")

# st.subheader("Job Scout with JobSpy")
# search_term = st.text_input("Job Title (e.g., AIML Engineer)")
# location = st.text_input("Location (e.g., Bengaluru)")
# results_wanted = st.slider("Max Results", 5, 50, 20)

# selected_job = None
doc_type = "resume"
# selected_job = pd.DataFrame()
# response = ""

# if st.button("Search Jobs"):
# with st.spinner("Scraping jobs..."):
#         jobs_df = fetch_and_save_jobs(search_term, location, results_wanted)
#         if not jobs_df.empty:
#             st.dataframe(jobs_df)
#             conn = sqlite3.connect("data/job_seeker.db")
#             sql_jobs = pd.read_sql_query("SELECT * FROM jobs ORDER BY scrape_date DESC LIMIT 20", conn)
#             conn.close()
#             st.subheader("Recent Jobs from DB")
#             st.dataframe(sql_jobs)

#             selected_idx = st.selectbox("Select Job to Tailor", range(len(jobs_df)))
#             selected_job = jobs_df.iloc[selected_idx]
#             doc_type = st.selectbox("Document Type", ["cover_letter", "resume"])
job_desc = st.text_area("Paste Job Description", height=200)

if st.button("Tailor Document"):
    # job_desc = selected_job.get('description', selected_job.get('title', ''))    
    response = query_rag(f"Generate tailored {doc_type}", job_desc, doc_type)
    st.text_area("Tailored Output", response, height=300)

# PDF Export
if st.button("Export to PDF"):
    output_path = f"tailored_{doc_type}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    c = canvas.Canvas(output_path, pagesize=letter)
    print(response)
    c.drawString(100, 750, response)
    c.save()
    st.success(f"PDF saved as {output_path}")
    st.download_button("Download PDF", open(output_path, "rb").read(), file_name=output_path)
    #         else:
    #             st.warning("No jobs found. Try different terms.")
    # else:
    #     st.write("Enter search term and location.")

# ... Cold Email section (unchanged for now) ...
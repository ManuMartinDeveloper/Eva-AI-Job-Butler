import streamlit as st
import os
import subprocess
import sys
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder

# --- Setup Paths ---
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
JOBS_DIR = os.path.join(_PROJECT_ROOT, "data", "jobs_details")

st.set_page_config(
    page_title="Eva - AI Job Butler",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🤖 Eva - AI Job Butler")
st.markdown("""
**Welcome to your personal AI Job Search Assistant.**
Eva helps you find jobs, tailor your resume, and write compelling cover letters using advanced AI.
""")

# --- Helper Functions ---
def get_latest_csv_file(path):
    """Finds the most recently created CSV file in a directory."""
    if not os.path.exists(path):
        return None, []
    
    csv_files = [f for f in os.listdir(path) if f.endswith('.csv')]
    if not csv_files:
        return None, []
        
    full_paths = [os.path.join(path, f) for f in csv_files]
    latest_file = max(full_paths, key=os.path.getctime)
    
    return latest_file, sorted(csv_files, reverse=True)

# --- Job Scout Section ---
st.header("🕵️ Job Scout")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Search Parameters")
    search_term = st.text_input("Job Title", "AI Engineer")
    location = st.text_input("Location", "Bengaluru")
    
    if st.button("🚀 Start Job Scout", use_container_width=True):
        st.info(f"Scouting for '{search_term}' jobs in '{location}'...")
        
        # Run the scraper script
        with st.expander("View Scraper Logs", expanded=True):
            process = subprocess.Popen(
                [sys.executable, "scrapers/job_scout.py", "--search", search_term, "--location", location],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                cwd=_PROJECT_ROOT # Ensure it runs from project root
            )
            
            log_container = st.empty()
            log_text = ""
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    log_text += output
                    log_container.code(log_text)
        
        st.success("Scouting complete! Check the results below.")
        st.rerun()

with col2:
    st.subheader("Latest Job Leads")
    latest_csv, all_csvs = get_latest_csv_file(JOBS_DIR)

    if not latest_csv:
        st.warning("No job data found. Run the Job Scout to find some leads!")
    else:
        selected_csv_name = st.selectbox("Select Job List", options=all_csvs, index=all_csvs.index(os.path.basename(latest_csv)))
        jobs_df = pd.read_csv(os.path.join(JOBS_DIR, selected_csv_name))
        
        # Display with AgGrid
        gb = GridOptionsBuilder.from_dataframe(jobs_df[['title', 'company', 'location', 'date_posted', 'job_url']])
        gb.configure_selection('single', use_checkbox=False)
        gb.configure_grid_options(domLayout='normal')
        gridOptions = gb.build()

        grid_response = AgGrid(
            jobs_df,
            gridOptions=gridOptions,
            height=400,
            width='100%',
            fit_columns_on_grid_load=True,
            theme='streamlit'
        )
        
        selected_rows = grid_response['selected_rows']
        if selected_rows is not None and not selected_rows.empty:
            selected_job = selected_rows.to_dict('records')[0]
            st.session_state.selected_job = selected_job
            st.success(f"Selected: {selected_job.get('title')} at {selected_job.get('company')}")
            st.info("Go to the 'Document Generator' page to create your application!")

st.markdown("---")
st.markdown("### 📚 Quick Guide")
# --- Agent Stats ---
from core.db import SessionLocal, Job, Application
from datetime import datetime, timedelta

session = SessionLocal()
today = datetime.now().date()
jobs_today = session.query(Job).filter(Job.scouted_at >= today).count()
total_jobs = session.query(Job).count()
apps_sent = session.query(Application).count()
session.close()

st.markdown("### 📊 Agent Activity")
col1, col2, col3 = st.columns(3)
col1.metric("Jobs Found Today", jobs_today, f"Total: {total_jobs}")
col2.metric("Applications Sent", apps_sent)
col3.metric("Agent Status", "Ready", "Waiting for Command")

st.divider()

st.markdown("""
### 🚀 Quick Start
1.  **Scout Jobs**: Go to **Job Scout** below or enable the **Autonomous Agent** in Settings.
2.  **Manage Profile**: Update your resume in **Profile Manager**.
3.  **Generate Documents**: Create tailored resumes in **Document Generator**.
""")
st.markdown("""
1.  **Job Scout**: Use this page to find new job listings.
2.  **Profile Manager**: Go here to update your skills and experience (ingest your resume).
3.  **Document Generator**: Select a job here, then go to the Generator to create your Resume and Cover Letter.
4.  **Settings**: Configure your AI models and API keys.
""")


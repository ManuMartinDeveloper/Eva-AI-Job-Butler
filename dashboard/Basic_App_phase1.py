# dashboard/Basic_App_phase1.py
""" This app is the basic version. Here the data Ingestion and the retrieval of the tailored response is done.
    The app uses Streamlit for the UI and integrates with the core functions for embedding and querying.
    Instructions:
    1. Ensure you have run `ollama pull phi4-mini` to have the model available locally.
    2. Make sure your GitHub token is set in the .env file for accessing private repositories if needed.
    3. Run this script using Streamlit: `streamlit run dashboard/Basic_App_phase1.py`
    4. Use the "Ingest Profile" button to load and embed your profile data. create an vector database.
    5. Test the  
"""

# --- setting up the path ---
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- Impoting the libraries ---
import streamlit as st
from core.profile_memory_initial_phase1 import ingest_and_embed, query_rag

# --- Streamlit App ---
st.title("AI Job Butler Dashboard")
if st.button("Ingest Profile"):
    ingest_and_embed(clear_existing=True)  # Initial ingest
    st.success("Profile ingested and embedded!")

job_desc = st.text_area("Ask any question from the profile and shall try to answer it from the chromaDB", height=200)
if st.button("Test Rag"):
    if job_desc:
        response = query_rag("Answer to the questions asked", job_desc)
        st.text_area("Tailored Output", response, height=300)
    else:
        st.write("Please enter a job description.")


st.write("Note: Ensure 'ollama pull phi3.5' is run and GitHub token is in .env.")
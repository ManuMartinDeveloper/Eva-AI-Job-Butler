import streamlit as st
import os
import sys

# --- Setup Paths ---
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
sys.path.append(_PROJECT_ROOT) # Ensure core modules can be imported

from core.profile_memory_resume_phase2 import ingest_and_embed

st.set_page_config(page_title="Profile Manager - Eva", page_icon="👤")

st.title("👤 Profile Manager")
st.markdown("""
**Manage your "Profile Memory".** 
This is the knowledge base Eva uses to write about you. Update this whenever you have a new resume or want to refresh your skills.
""")

st.info("Currently, Eva ingests data from `core/ingest.py`. Please make sure your data is updated there.")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Ingest Profile")
    st.markdown("Click the button below to process your resume and store it in the vector database.")
    
    if st.button("🔄 Ingest & Update Memory", use_container_width=True):
        with st.spinner("Ingesting profile data... This may take a minute."):
            try:
                ingest_and_embed(clear_existing=True)
                st.success("Profile successfully ingested! Eva now knows your latest details.")
            except Exception as e:
                st.error(f"Error during ingestion: {e}")

with col2:
    st.subheader("View Memory Stats")
    # Placeholder for future feature: showing stats about the vector store
    st.markdown("""
    *Vector Store Status:*
    - **Status**: Active 🟢
    - **Provider**: ChromaDB
    - **Embeddings**: Local (Sentence Transformers)
    """)

st.markdown("---")

# --- Interview Mode ---
st.subheader("🎤 Interview Mode")
st.markdown("Chat with Eva to fill in the gaps in your profile. She will ask you questions to learn more about you.")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hi Manu! I want to learn more about you. What is your biggest professional achievement so far?"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input("Answer Eva..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    
    # Simple logic for now - in future, use LLM to generate next question and extract facts
    from core.db import SessionLocal, ProfileFact
    session = SessionLocal()
    new_fact = ProfileFact(category="Interview", fact=prompt, source="User Chat")
    session.add(new_fact)
    session.commit()
    session.close()
    
    response = "Thanks! I've noted that down. Tell me about your ideal work environment?"
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.chat_message("assistant").write(response)

st.markdown("---")
st.markdown("### 💡 Tip")
st.markdown("If Eva is hallucinating or missing details about your recent work, try re-ingesting your profile here.")

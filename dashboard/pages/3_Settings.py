import streamlit as st
import os
from dotenv import load_dotenv

# --- Setup ---
load_dotenv()

st.set_page_config(page_title="Settings - Eva", page_icon="⚙️")

st.title("⚙️ Settings")
st.markdown("Configure your AI Job Butler.")

# --- Model Selection ---
st.header("🧠 AI Model Configuration")

# Initialize session state for settings if not present
if 'llm_provider' not in st.session_state:
    st.session_state.llm_provider = "gemini"
if 'llm_model' not in st.session_state:
    st.session_state.llm_model = "gemini-2.0-flash-lite"

col1, col2 = st.columns(2)

with col1:
    provider = st.selectbox(
        "Select AI Provider",
        options=["gemini", "ollama", "groq"],
        index=["gemini", "ollama", "groq"].index(st.session_state.llm_provider)
    )
    st.session_state.llm_provider = provider

with col2:
    model_name = ""
    if provider == "gemini":
        model_name = st.text_input("Model Name", value=st.session_state.llm_model if st.session_state.llm_provider == "gemini" else "gemini-2.0-flash-lite")
        st.caption("Recommended: `gemini-2.0-flash-lite`, `gemini-1.5-pro`")
    elif provider == "ollama":
        model_name = st.text_input("Model Name", value=st.session_state.llm_model if st.session_state.llm_provider == "ollama" else "phi4")
        st.caption("Ensure you have pulled this model via `ollama pull <model>`")
    elif provider == "groq":
        model_name = st.text_input("Model Name", value=st.session_state.llm_model if st.session_state.llm_provider == "groq" else "llama3-70b-8192")
        st.caption("Recommended: `llama3-70b-8192`, `mixtral-8x7b-32768`")
    
    st.session_state.llm_model = model_name

st.success(f"Current Configuration: **{provider.upper()}** using **{model_name}**")

# --- API Keys Status ---
st.header("🔑 API Keys Status")
st.markdown("These are loaded from your `.env` file.")

keys = {
    "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY"),
    "GROQ_API_KEY": os.getenv("GROQ_API_KEY"),
}

for key, value in keys.items():
    if value:
        st.markdown(f"- **{key}**: ✅ Loaded")
    else:
        st.markdown(f"- **{key}**: ❌ Not Found")

st.info("To update keys, please edit the `.env` file in the project root directory.")

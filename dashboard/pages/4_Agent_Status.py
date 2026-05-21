import streamlit as st
import pandas as pd
import os
import sys
import time

# --- Setup Paths ---
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
sys.path.append(_PROJECT_ROOT)

from core.db import SessionLocal, AgentLog, Job
from core.agent import agent

st.set_page_config(page_title="Agent Status - Eva", page_icon="🤖", layout="wide")

st.title("🤖 Autonomous Agent Status")

# --- Control Panel ---
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Control")
    if st.button("▶️ Start Agent", use_container_width=True):
        if not agent.is_running:
            agent.start()
            st.success("Agent started in background!")
        else:
            st.warning("Agent is already running.")

    if st.button("⏹️ Stop Agent", use_container_width=True):
        if agent.is_running:
            agent.stop()
            st.error("Agent stopped.")
        else:
            st.warning("Agent is not running.")

with col2:
    st.subheader("Status")
    status = "🟢 Running" if agent.is_running else "🔴 Stopped"
    st.markdown(f"**Current State:** {status}")
    
    # Next scheduled tasks (Mockup for now, real scheduler inspection is complex in Streamlit reload)
    if agent.is_running:
        st.markdown("**Next Tasks:**")
        st.markdown("- `scout_jobs`: In ~4 hours")
        st.markdown("- `pr_brainstorm`: In ~12 hours")

with col3:
    st.subheader("Quick Actions")
    if st.button("🕵️ Force Run Scout", use_container_width=True):
        with st.spinner("Running manual scout..."):
            agent.task_scout_jobs()
            st.success("Scout complete!")

# --- Activity Log ---
st.markdown("---")
st.subheader("📜 Activity Log")

session = SessionLocal()
logs = session.query(AgentLog).order_by(AgentLog.timestamp.desc()).limit(50).all()
session.close()

if logs:
    data = [{
        "Time": log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        "Action": log.action,
        "Details": log.details,
        "Status": log.status
    } for log in logs]
    
    st.dataframe(pd.DataFrame(data), use_container_width=True)
else:
    st.info("No logs found. Start the agent to see activity.")

# Auto-refresh
if agent.is_running:
    time.sleep(5)
    st.rerun()

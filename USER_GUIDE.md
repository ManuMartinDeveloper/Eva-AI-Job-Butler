# 🤖 Eva AI Job Butler - User Guide

Welcome to your new autonomous job search assistant! This guide will help you navigate the features of Eva AI Job Butler.

## 🚀 Quick Start

1.  **Start the Dashboard**:
    Open your terminal and run:
    ```bash
    .venv/bin/streamlit run dashboard/Home.py
    ```
    Then open `http://localhost:8501` in your browser.

---

## 🧭 Features Overview

### 1. 🏠 Home: Job Scout
*   **What it does**: Finds job listings relevant to you.
*   **How to use**:
    1.  Enter a **Job Title** (e.g., "AI Engineer") and **Location** (e.g., "Remote").
    2.  Click **"🔍 Scout Jobs"**.
    3.  Eva will scrape job boards (LinkedIn, Indeed, etc.) and display a list of opportunities.
    4.  **Action**: Select jobs you like to save them to your database.

### 2. 👤 Profile Manager: "Know Me"
*   **What it does**: This is Eva's brain. It stores your resume and professional facts.
*   **How to use**:
    *   **Upload Resume**: Paste your resume text to update the base memory.
    *   **Interview Mode**: Chat with Eva! She will ask you questions to dig deeper into your experience (e.g., "Tell me more about that Python project"). This helps her write better cover letters later.

### 3. 📝 Document Generator
*   **What it does**: Writes tailored Resumes and Cover Letters.
*   **How to use**:
    1.  Select a **Job** you scouted earlier.
    2.  Choose your **AI Model** (e.g., `gemini-2.0-flash-lite`).
    3.  Click **"Generate Resume"** or **"Generate Cover Letter"**.
    4.  **Review**: Read the AI's reasoning and the generated text.
    5.  **Download**: Click "Download DOCX" to get a formatted file ready to send.

### 4. ⚙️ Settings
*   **What it does**: Configure the AI brains.
*   **How to use**:
    *   **Provider**: Switch between Google Gemini (recommended), Ollama (local), or Groq (fast).
    *   **Model**: The default is now `gemini-2.0-flash-lite` for the best balance of speed and quality.

### 5. 🕵️ Agent Status (Autonomous Mode)
*   **What it does**: Controls the background agent that works while you sleep.
*   **How to use**:
    *   **Start Agent**: Click the "▶️ Start Agent" button. Eva will wake up and run scheduled tasks (like scouting for jobs every 4 hours).
    *   **Logs**: View the "Activity Log" to see what Eva has been doing.

### 6. 📢 PR Agent (Bonus)
*   **What it does**: Drafts LinkedIn posts and networking messages.
*   **How to use**:
    *   Currently, this runs as a script: `python core/pr_agent.py`.
    *   *Coming Soon*: Full integration into the dashboard!

---

## 💡 Pro Tips
*   **Keep your Profile Updated**: The more you chat with Eva in "Interview Mode", the better your resumes will be.
*   **Check the Logs**: If something seems quiet, check the **Agent Status** page to ensure the background scheduler is running.

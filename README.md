# 🤖 Eva AI Job Butler

Welcome to your new autonomous job search assistant! Eva AI Job Butler helps you scout for job listings, tailor your resume, generate cover letters, and auto-apply using Playwright. It operates with a FastAPI backend and a React/Vite frontend.

## 🚀 Quick Start

### 1. Start the Backend API
The backend requires Python 3.10+ and uses FastAPI.

```bash
# Install dependencies
pip install -r requirements.txt

# Start the FastAPI server
python backend/main.py &
```
The API will run at `http://localhost:8000`.

### 2. Start the Frontend
The frontend is built with React and Vite.

```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev &
```
The UI will be accessible at `http://localhost:5173`.

---

## 🧭 Features Overview

### 1. 🏠 Job Scout
*   **What it does**: Finds job listings relevant to you.
*   **How to use**:
    1.  Enter a **Job Title** (e.g., "AI Engineer") and **Location** (e.g., "Remote").
    2.  Click **"Launch Scout"**.
    3.  Eva will scrape job boards and display a list of opportunities.
    4.  **Action**: Select jobs you like to view details and start applying.

### 2. 👤 Profile Manager: "Know Me"
*   **What it does**: This is Eva's brain. It stores your professional facts and seeds a RAG vector store.
*   **How to use**:
    *   **Sync Profile & Embed**: Extract data from your GitHub and provided resume data into ChromaDB.
    *   **Interview Mode**: Chat with Eva! She will ask you questions to dig deeper into your experience. This helps her write better cover letters later.
    *   **Manage Facts**: Add or delete specific skills and experiences manually.

### 3. 📝 Document Tailor
*   **What it does**: Writes tailored Resumes and Cover Letters.
*   **How to use**:
    1.  Select a **Job** you scouted earlier.
    2.  Ensure the Job Title and Description are populated.
    3.  Click **"Tailor Resume & Cover Letter"**.
    4.  **Review**: Read the AI's reasoning and the generated text.
    5.  **Download**: Click "Compile & Download" to get formatted `.docx` files ready to send.

### 4. ⚙️ Settings
*   **What it does**: Configure the AI brains.
*   **How to use**:
    *   **Provider**: Switch between Google Gemini (recommended), Ollama (local), or Groq (fast).
    *   **Model**: The default is `gemini-2.0-flash-lite` for the best balance of speed and quality.

### 5. 🕵️ Agent Control
*   **What it does**: Controls the background agent that works autonomously, and the Cybernetic Agent Cockpit.
*   **How to use**:
    *   **Start/Stop Agent**: The background scheduler wakes up periodically to scout for jobs.
    *   **Cybernetic Agent Cockpit**: When using "Assisted Apply", you can watch Eva's thought process (ReAct Stream) and view a live screenshot of the Playwright browser automating the application process.

### 6. 📢 PR Agent (Bonus)
*   **What it does**: Drafts LinkedIn posts and networking messages.
*   **How to use**:
    *   Currently, this runs as a script: `python core/pr_agent.py`.
    *   *Coming Soon*: Full integration into the dashboard!

---

## 💡 Pro Tips
*   **Keep your Profile Updated**: The more you chat with Eva in "Interview Mode" or add facts, the better your tailored documents will be.
*   **Check the Cockpit Logs**: Monitor the live activity log or agent stream to see exactly what Eva is doing while applying.

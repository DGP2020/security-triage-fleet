# Security Triage Fleet

Welcome to the **Security Triage Fleet** project! This repository contains a multi-agent SOC (Security Operations Center) dashboard powered by the Google Agent Development Kit (ADK) and Gemini. 

The project orchestrates multiple specialized AI agents (Red Team, Blue Team, Green Team) to triage, analyze, and remediate security threats. It features a FastAPI backend and a web-based dashboard for interactive simulation and Human-In-The-Loop (HITL) approval.

---

## 🚀 Setup Instructions

You can run this project either using **Docker** (recommended) or **Locally via Python**. 

### Prerequisites
Before you begin, you will need:
1. A **Google API Key** for Gemini models.
2. **Docker** installed (if using the Docker method).
3. **Python 3.11+** installed (if using the local method).

---
Demo requires a free Google AI Studio API key.
Get one free at aistudio.google.com — no credit card needed.
Takes 30 seconds to set up.

### Option 1: Hugging face space(Recommended)

Visit (https://huggingface.co/spaces/DanielGP12/security-triage-fleet) to see the live version

### Option 2: Running Locally with Python

If you prefer to run the project directly on your machine, follow these steps:

**1. Create a virtual environment:**
```bash
python -m venv agent-env
```

**2. Activate the virtual environment:**
- **Windows:**
  ```powershell
  agent-env\Scripts\activate
  ```
- **macOS / Linux:**
  ```bash
  source agent-env/bin/activate
  ```

**3. Install dependencies:**
```bash
pip install -r requirements.txt
```

**4. Configure Environment Variables:**
Create a `.env` file in the root directory of the project and add your API key:
```env
GOOGLE_API_KEY=your_google_api_key_here
```
*(Note: The server will automatically map this to `GEMINI_API_KEY` if required by underlying libraries).*

**5. Start the Server:**
Run the FastAPI server using `uvicorn`:
```bash
uvicorn server:app --host 0.0.0.0 --port 8000
```
*(Alternatively, you can run `python server.py` which will also start the server on port 8000).*

**6. Access the Dashboard:**
Open your web browser and navigate to:  
[http://localhost:8000](http://localhost:8000)

---

## 🛠️ Technology Stack
* **Agent Framework:** Google ADK (Agent Development Kit), Google GenAI SDK
* **Backend:** FastAPI, Uvicorn, Pydantic
* **Frontend:** Vanilla HTML/JS/CSS Dashboard
* **Containerization:** Docker (Python 3.11-slim)



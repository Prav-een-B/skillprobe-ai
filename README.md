# SkillProbe AI - Skill Assessment Agent

## Overview
SkillProbe AI is an AI-powered conversational skill assessment and learning plan generation agent built for the **Catalyst Hackathon by Deccan AI**. 

It takes a Job Description and a Candidate's Resume, conversationally assesses their real proficiency on each required skill, identifies gaps, and generates a personalised learning plan focused on adjacent skills.

### Features
1. **Smart Resume Parsing:** Extracts and matches skills between JD and Resume.
2. **Adaptive Conversational Assessment:** A dynamic chat interface where the AI (powered by Groq / Llama-3.3-70b) asks questions tailored to the candidate's experience and adapts difficulty based on their answers.
3. **Gap Analysis Dashboard:** Visualizes proficiency scores across required skills.
4. **Personalised Learning Plan:** Generates actionable learning roadmaps with curated resources, time estimates, and adjacent skill mapping, instantly downloadable as a professional PDF.

## Tech Stack
- **Backend:** Python, FastAPI
- **Frontend:** Vanilla HTML, CSS (Aurora Noir theme), JS
- **AI Model:** Groq (Llama-3.3-70b-versatile via OpenAI SDK)
- **PDF Generation:** PyMuPDF (parsing), fpdf2 (exporting)

## Setup Instructions

### 1. Prerequisites
- Python 3.9+
- A Groq API Key (Get a free one at [console.groq.com](https://console.groq.com))

### 2. Installation
```bash
git clone <your-repo-url>
cd skill-assessment-agent

# Create a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration
Rename `.env.example` to `.env` and add your Groq API key:
```env
OPENAI_API_KEY=gsk_your_groq_api_key_here
```

### 4. Running the Application
```bash
python main.py
```
Open your browser and navigate to: `http://localhost:8000`

## Demo Video
*(Add your demo video link here)*

## Project Structure
- `main.py`: FastAPI entry point
- `app/`: Backend logic (routes, AI services, prompts)
- `static/`: Frontend assets (CSS, JS)
- `templates/`: HTML views
- `sample_data/`: Example JDs and Resumes for testing

## Author
Praveen B

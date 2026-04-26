# Architecture & Logic

## High-Level Architecture
SkillProbe AI is built as a monolithic application using FastAPI. It serves both the REST API endpoints and the frontend static files.

1. **Frontend:** A single-page application built with plain HTML, CSS, and JS. It communicates with the backend via fetch requests.
2. **Backend:** FastAPI handles routing, validation (Pydantic), and session state management.
3. **AI Layer:** Interacts with the Google Gemini API to parse text, generate questions, evaluate answers, and create learning plans.

## Assessment Logic

### 1. Skill Extraction
The system sends the JD and Resume to Gemini. It extracts a list of required skills, categorises them by importance (Critical, Important, Nice-to-have), and matches them against the candidate's claimed skills.

### 2. Adaptive Questioning
- **Initial Difficulty:** If a skill is found in the resume, the first question is `medium` difficulty. If not, it's `easy`.
- **Adaptation:** After each answer, the AI evaluates the response on a 1-5 scale.
  - Score >= 4 -> Next question is `hard`.
  - Score <= 2 -> Next question is `easy`.
  - Score == 3 -> Next question is `medium`.
- **Termination:** The system asks a maximum of 2 questions per skill to respect the candidate's time. If the first score is <= 1, it skips the second question entirely.

### 3. Scoring Rubric
- **1 (Novice):** Cannot explain the concept.
- **2 (Beginner):** Textbook knowledge, no practical experience.
- **3 (Intermediate):** Can solve standard problems.
- **4 (Advanced):** Deep understanding, handles edge cases.
- **5 (Expert):** Can architect solutions, teach others.

The final score for a skill is a weighted average of the questions asked, giving slightly more weight to the harder follow-up questions.

### 4. Learning Plan Generation
The final step takes the skill scores and generates a personalised roadmap. It focuses heavily on **adjacent skills** (e.g., if a candidate knows Django but the job needs FastAPI, the learning plan will leverage their existing ORM and routing knowledge to teach FastAPI faster).

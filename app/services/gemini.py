"""
Google Gemini API wrapper with retry logic and JSON mode.
"""

import json
import time
import google.generativeai as genai
from app.config import settings


def get_model():
    """Initialise and return the Gemini generative model."""
    genai.configure(api_key=settings.GEMINI_API_KEY)
    return genai.GenerativeModel(settings.GEMINI_MODEL)


async def call_gemini(prompt: str, max_retries: int = 3) -> str:
    """
    Send a prompt to Gemini and return the text response.
    Includes exponential backoff for rate-limit errors.
    """
    model = get_model()
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "quota" in error_msg.lower():
                wait = 2 ** (attempt + 1)
                print(f"⏳ Rate limited, waiting {wait}s before retry...")
                time.sleep(wait)
            else:
                raise e
    raise Exception("Max retries exceeded for Gemini API call")


async def call_gemini_json(prompt: str, max_retries: int = 3) -> dict:
    """
    Send a prompt to Gemini and parse the response as JSON.
    Automatically strips markdown code fences if present.
    """
    if getattr(settings, "MOCK_MODE", False):
        import asyncio
        await asyncio.sleep(1.5)  # Simulate network delay
        if "extract and analyse the skills" in prompt:
            return {
                "required_skills": [
                    {"name": "Python", "importance": "critical", "category": "backend"},
                    {"name": "HTML", "importance": "important", "category": "frontend"}
                ],
                "candidate_skills": [
                    {"name": "HTML", "claimed_experience": "Weekend bootcamp", "context": "Can make simple forms"}
                ],
                "initial_gaps": [
                    {"skill": "Python", "status": "missing", "adjacent_to": []}
                ]
            }
        elif "Generate ONE assessment question" in prompt:
            if "HTML" in prompt:
                q = "What's the difference between a `<div>` and a `<span>` in HTML?"
                c = "Block vs inline elements."
            else:
                q = "How do you define a function in Python?"
                c = "Using the def keyword."
            return {
                "question": q,
                "what_good_answer_covers": c
            }
        elif "Evaluate the answer and return a JSON" in prompt:
            return {
                "score": 4,
                "level": "advanced",
                "feedback": "Great answer! You covered the core concepts nicely.",
                "strengths": ["Clear understanding", "Good examples"],
                "weaknesses": []
            }
        elif "personalised learning plan" in prompt:
            return {
                "overall_readiness_score": 85,
                "summary": "You have a strong foundation in HTML but need to learn Python.",
                "strengths": ["HTML basics"],
                "critical_gaps": ["Python"],
                "learning_items": [
                    {
                        "skill_name": "Python",
                        "current_level": "novice",
                        "target_level": "intermediate",
                        "priority": "high",
                        "why_important": "It is critical for the developer role.",
                        "resources": [
                            {"title": "Python Official Docs", "url": "https://docs.python.org/3/", "type": "documentation", "estimated_hours": 10}
                        ],
                        "estimated_weeks": 2,
                        "prerequisites_you_have": ["HTML"],
                        "milestones": ["Write your first script"]
                    }
                ],
                "total_estimated_weeks": 2
            }

    raw = await call_gemini(prompt, max_retries)

    # Strip markdown code fences
    cleaned = raw.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Try to find JSON object in the response
        start = cleaned.find("{")
        end = cleaned.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(cleaned[start:end])
        # Try JSON array
        start = cleaned.find("[")
        end = cleaned.rfind("]") + 1
        if start != -1 and end > start:
            return json.loads(cleaned[start:end])
        raise ValueError(f"Could not parse Gemini response as JSON: {raw[:200]}")

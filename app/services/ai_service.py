"""
OpenAI API wrapper with JSON mode and Mock fallback.
"""

import json
import asyncio
from openai import AsyncOpenAI
from app.config import settings

client = None
if settings.GROQ_API_KEY:
    client = AsyncOpenAI(
        api_key=settings.GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1"
    )

async def call_ai_json(prompt: str, max_retries: int = 3) -> dict:
    """
    Call Groq and parse the response as JSON.
    Automatically returns mock data if API key is missing.
    """
    if not client:
        await asyncio.sleep(1.5)  # Simulate network delay
        if "extract and analyse the skills" in prompt:
            return {
                "required_skills": [
                    {"name": "Python", "importance": "critical", "category": "backend"},
                    {"name": "FastAPI", "importance": "important", "category": "backend"}
                ],
                "candidate_skills": [
                    {"name": "Python", "claimed_experience": "3 years", "context": "Built APIs"}
                ],
                "initial_gaps": [
                    {"skill": "FastAPI", "status": "missing", "adjacent_to": ["Python"]}
                ]
            }
        elif "Generate ONE assessment question" in prompt:
            return {
                "question": "How do you define an asynchronous function in Python, and why might you use it over a standard function in a web framework like FastAPI?",
                "what_good_answer_covers": "Using async def, non-blocking I/O, event loops."
            }
        elif "Evaluate the answer and return a JSON" in prompt:
            return {
                "score": 4,
                "level": "advanced",
                "feedback": "Great answer! You correctly identified the async keyword and explained its benefit for I/O operations.",
                "strengths": ["Clear understanding of concurrency", "Good practical context"],
                "weaknesses": []
            }
        elif "personalised learning plan" in prompt:
            return {
                "overall_readiness_score": 85,
                "summary": "You have a strong foundation in Python but need to focus on modern web frameworks like FastAPI.",
                "strengths": ["Python fundamentals"],
                "critical_gaps": ["FastAPI"],
                "learning_items": [
                    {
                        "skill_name": "FastAPI",
                        "current_level": "novice",
                        "target_level": "intermediate",
                        "priority": "high",
                        "why_important": "It is critical for the backend role.",
                        "resources": [
                            {"title": "FastAPI Official Docs", "url": "https://fastapi.tiangolo.com/", "type": "documentation", "estimated_hours": 10}
                        ],
                        "estimated_weeks": 2,
                        "prerequisites_you_have": ["Python"],
                        "milestones": ["Build a simple CRUD API"]
                    }
                ],
                "total_estimated_weeks": 2
            }
        return {"error": "Mock fallback reached without a matched prompt."}

    for attempt in range(max_retries):
        try:
            response = await client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant. Output must be valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
            )
            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from OpenAI")
            return json.loads(content)
        except Exception as e:
            print(f"OpenAI API Error (attempt {attempt+1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                raise ValueError(f"Failed to call OpenAI API: {e}")
            await asyncio.sleep(2 ** attempt)

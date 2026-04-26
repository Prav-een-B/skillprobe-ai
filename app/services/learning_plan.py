"""
Learning Plan Generator — creates personalised study plans using Gemini.
"""

from app.services.ai_service import call_ai_json
from app.services.assessment import get_session
from app.prompts.templates import GENERATE_PLAN_PROMPT
from app.models import (
    LearningPlan,
    LearningItem,
    LearningResource,
)


async def generate_learning_plan(session_id: str) -> LearningPlan:
    """Generate a personalised learning plan from assessment results."""
    session = get_session(session_id)
    if not session:
        raise ValueError("Session not found")

    if not session.is_complete:
        raise ValueError("Assessment is not yet complete")

    # Format skill results for the prompt
    skill_results_text = ""
    for sr in session.skill_scores:
        skill_results_text += (
            f"- {sr.skill_name}: Score {sr.final_score}/5 "
            f"(Level: {sr.level.value}, Importance: {sr.importance.value})\n"
        )

    prompt = GENERATE_PLAN_PROMPT.format(
        skill_results=skill_results_text,
        jd_summary=session.jd_text[:1500],  # Truncate if very long
        resume_summary=session.resume_text[:1500],
    )

    data = await call_ai_json(prompt)

    # Parse learning items
    learning_items = []
    for item_data in data.get("learning_items", []):
        resources = [
            LearningResource(**r) for r in item_data.get("resources", [])
        ]
        item = LearningItem(
            skill_name=item_data.get("skill_name", ""),
            current_level=item_data.get("current_level", ""),
            target_level=item_data.get("target_level", ""),
            priority=item_data.get("priority", "medium"),
            why_important=item_data.get("why_important", ""),
            resources=resources,
            estimated_weeks=item_data.get("estimated_weeks", 0),
            prerequisites_you_have=item_data.get("prerequisites_you_have", []),
            milestones=item_data.get("milestones", []),
        )
        learning_items.append(item)

    plan = LearningPlan(
        overall_readiness_score=data.get("overall_readiness_score", 0),
        summary=data.get("summary", ""),
        strengths=data.get("strengths", []),
        critical_gaps=data.get("critical_gaps", []),
        learning_items=learning_items,
        total_estimated_weeks=data.get("total_estimated_weeks", 0),
    )

    return plan

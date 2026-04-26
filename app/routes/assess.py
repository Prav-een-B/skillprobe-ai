"""
Assessment routes — start assessment, submit answers, check progress.
"""

from fastapi import APIRouter, HTTPException
from app.services.assessment import generate_question, evaluate_answer, get_session
from app.models import (
    SubmitAnswerRequest,
    SubmitAnswerResponse,
    StartAssessmentResponse,
)

router = APIRouter()


@router.post("/assess/start", response_model=StartAssessmentResponse)
async def start_assessment(session_id: str):
    """Start the assessment — returns the first question."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found. Please upload resume and JD first.")

    if session.is_complete:
        raise HTTPException(400, "Assessment already completed for this session.")

    question = await generate_question(session_id)
    if not question:
        raise HTTPException(500, "Could not generate assessment question.")

    return StartAssessmentResponse(
        session_id=session_id,
        question=question,
        total_skills=len(session.skills_to_assess),
        current_skill_number=session.current_skill_index + 1,
    )


@router.post("/assess/answer", response_model=SubmitAnswerResponse)
async def submit_answer(request: SubmitAnswerRequest):
    """Submit an answer and get evaluation + next question."""
    session = get_session(request.session_id)
    if not session:
        raise HTTPException(404, "Session not found.")

    if session.is_complete:
        raise HTTPException(400, "Assessment already completed.")

    if not request.answer.strip():
        raise HTTPException(400, "Please provide an answer.")

    try:
        evaluation, is_skill_complete, is_assessment_complete, skill_result = (
            await evaluate_answer(request.session_id, request.answer)
        )
    except Exception as e:
        raise HTTPException(500, f"Error evaluating answer: {str(e)}")

    # Generate next question if assessment isn't complete
    next_question = None
    if not is_assessment_complete:
        try:
            next_question = await generate_question(request.session_id)
        except Exception as e:
            raise HTTPException(500, f"Error generating next question: {str(e)}")

    session = get_session(request.session_id)  # Refresh

    return SubmitAnswerResponse(
        evaluation=evaluation,
        next_question=next_question,
        is_skill_complete=is_skill_complete,
        is_assessment_complete=is_assessment_complete,
        current_skill_number=min(
            session.current_skill_index + 1, len(session.skills_to_assess)
        ),
        total_skills=len(session.skills_to_assess),
        skill_result=skill_result,
    )


@router.get("/assess/{session_id}")
async def get_assessment_status(session_id: str):
    """Get current assessment progress and status."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found.")

    return {
        "session_id": session_id,
        "is_complete": session.is_complete,
        "total_skills": len(session.skills_to_assess),
        "skills_assessed": len(session.skill_scores),
        "current_skill_index": session.current_skill_index,
        "skill_scores": [s.model_dump() for s in session.skill_scores],
    }

"""
Assessment Engine — adaptive conversational skill assessment using Gemini.
Manages session state, generates questions, and evaluates answers.
"""

import uuid
import json
import os
from pydantic import TypeAdapter
from app.services.ai_service import call_ai_json
from app.prompts.templates import GENERATE_QUESTION_PROMPT, EVALUATE_ANSWER_PROMPT
from app.models import (
    AssessmentSession,
    AssessmentQuestion,
    AnswerEvaluation,
    SkillAssessmentResult,
    SkillExtractionResult,
    ProficiencyLevel,
)

# ── Persistent session store ─────────
SESSIONS_FILE = "sessions.json"
sessions: dict[str, AssessmentSession] = {}

def load_sessions():
    global sessions
    if os.path.exists(SESSIONS_FILE):
        try:
            with open(SESSIONS_FILE, "r") as f:
                data = json.load(f)
                sessions = {k: AssessmentSession.model_validate(v) for k, v in data.items()}
        except Exception:
            sessions = {}

def save_sessions():
    try:
        with open(SESSIONS_FILE, "w") as f:
            data = {k: v.model_dump(mode="json") for k, v in sessions.items()}
            json.dump(data, f)
    except Exception:
        pass

load_sessions()


def create_session(
    jd_text: str,
    resume_text: str,
    extraction_result: SkillExtractionResult,
) -> AssessmentSession:
    """Create a new assessment session."""
    session_id = str(uuid.uuid4())[:8]

    # Sort skills: critical first, then important, then nice-to-have
    priority_order = {"critical": 0, "important": 1, "nice-to-have": 2}
    sorted_skills = sorted(
        extraction_result.required_skills,
        key=lambda s: priority_order.get(s.importance, 2),
    )

    session = AssessmentSession(
        session_id=session_id,
        jd_text=jd_text,
        resume_text=resume_text,
        extraction_result=extraction_result,
        skills_to_assess=sorted_skills,
    )
    sessions[session_id] = session
    save_sessions()
    return session


def get_session(session_id: str) -> AssessmentSession | None:
    """Retrieve an existing session."""
    return sessions.get(session_id)


def _get_resume_context(session: AssessmentSession, skill_name: str) -> str:
    """Get relevant context about a skill from the candidate's resume."""
    if session.extraction_result:
        for cs in session.extraction_result.candidate_skills:
            if cs.name.lower() == skill_name.lower():
                return f"{cs.name}: {cs.claimed_experience}. {cs.context}"
    return "No specific mention of this skill in the resume."


def _get_jd_context(session: AssessmentSession, skill_name: str) -> str:
    """Get relevant context about a skill from the JD."""
    if session.extraction_result:
        for rs in session.extraction_result.required_skills:
            if rs.name.lower() == skill_name.lower():
                return f"{rs.name} (importance: {rs.importance}, category: {rs.category})"
    return skill_name


def _get_previous_qa(session: AssessmentSession) -> str:
    """Get previous Q&A for the current skill for context."""
    current_skill = session.skills_to_assess[session.current_skill_index]
    relevant = [
        h for h in session.conversation_history
        if h.get("skill") == current_skill.name
    ]
    if not relevant:
        return "This is the first question for this skill."

    parts = []
    for h in relevant:
        parts.append(f"Q: {h['question']}\nA: {h['answer']}\nScore: {h['score']}/5")
    return "Previous Q&A for this skill:\n" + "\n---\n".join(parts)


def _determine_initial_difficulty(session: AssessmentSession, skill_name: str) -> str:
    """Determine starting difficulty based on whether skill is in resume."""
    if session.extraction_result:
        candidate_skill_names = [
            cs.name.lower() for cs in session.extraction_result.candidate_skills
        ]
        if skill_name.lower() in candidate_skill_names:
            return "medium"
    return "easy"


async def generate_question(session_id: str) -> AssessmentQuestion | None:
    """Generate the next assessment question for the current skill."""
    session = get_session(session_id)
    if not session or session.is_complete:
        return None

    current_skill = session.skills_to_assess[session.current_skill_index]
    skill_name = current_skill.name

    # Determine difficulty
    if session.current_question_number == 0:
        session.current_difficulty = _determine_initial_difficulty(session, skill_name)
    # else: difficulty is set by the evaluation of the previous answer

    total_questions = 2  # Default 2 questions per skill

    prompt = GENERATE_QUESTION_PROMPT.format(
        skill_name=skill_name,
        resume_context=_get_resume_context(session, skill_name),
        jd_context=_get_jd_context(session, skill_name),
        difficulty=session.current_difficulty,
        question_number=session.current_question_number + 1,
        total_questions=total_questions,
        previous_qa=_get_previous_qa(session),
    )

    data = await call_ai_json(prompt)

    question = AssessmentQuestion(
        skill_name=skill_name,
        question=data["question"],
        difficulty=session.current_difficulty,
        question_number=session.current_question_number + 1,
        total_questions_for_skill=total_questions,
    )

    # Store the good answer reference in conversation history metadata
    session.last_question = question
    session.conversation_history.append({
        "skill": skill_name,
        "question": data["question"],
        "good_answer_covers": data.get("what_good_answer_covers", ""),
        "difficulty": session.current_difficulty,
        "answer": None,
        "score": None,
    })

    sessions[session_id] = session
    save_sessions()
    return question


async def evaluate_answer(session_id: str, answer: str) -> tuple[AnswerEvaluation, bool, bool, SkillAssessmentResult | None]:
    """
    Evaluate the candidate's answer.
    Returns: (evaluation, is_skill_complete, is_assessment_complete, skill_result_if_complete)
    """
    session = get_session(session_id)
    if not session:
        raise ValueError("Session not found")

    current_skill = session.skills_to_assess[session.current_skill_index]
    skill_name = current_skill.name

    # Get the last conversation entry (has the question info)
    last_entry = session.conversation_history[-1]

    prompt = EVALUATE_ANSWER_PROMPT.format(
        skill_name=skill_name,
        difficulty=last_entry["difficulty"],
        question=last_entry["question"],
        answer=answer,
        good_answer_covers=last_entry.get("good_answer_covers", ""),
    )

    data = await call_ai_json(prompt)
    evaluation = AnswerEvaluation(**data)

    # Update conversation history
    last_entry["answer"] = answer
    last_entry["score"] = evaluation.score
    session.conversation_history[-1] = last_entry

    session.current_question_number += 1

    # Adaptive difficulty
    if evaluation.score >= 4:
        session.current_difficulty = "hard"
    elif evaluation.score <= 2:
        session.current_difficulty = "easy"
    else:
        session.current_difficulty = "medium"

    # Check if we should ask another question for this skill
    max_questions = 2
    is_skill_complete = False
    skill_result = None

    if session.current_question_number >= max_questions:
        is_skill_complete = True
    elif evaluation.score <= 1:
        # Very low score — no point asking harder questions
        is_skill_complete = True

    if is_skill_complete:
        # Calculate final score for this skill
        skill_scores = [
            h["score"]
            for h in session.conversation_history
            if h.get("skill") == skill_name and h.get("score") is not None
        ]
        # Weight harder questions more
        if len(skill_scores) >= 2:
            final_score = skill_scores[0] * 0.4 + skill_scores[1] * 0.6
        else:
            final_score = skill_scores[0] if skill_scores else 0

        level = _score_to_level(final_score)

        skill_result = SkillAssessmentResult(
            skill_name=skill_name,
            importance=current_skill.importance,
            final_score=round(final_score, 1),
            level=level,
            questions_asked=session.current_question_number,
        )
        session.skill_scores.append(skill_result)

        # Move to next skill
        session.current_skill_index += 1
        session.current_question_number = 0

    is_assessment_complete = session.current_skill_index >= len(session.skills_to_assess)
    session.is_complete = is_assessment_complete

    sessions[session_id] = session
    save_sessions()
    return evaluation, is_skill_complete, is_assessment_complete, skill_result


def _score_to_level(score: float) -> ProficiencyLevel:
    """Convert numeric score to proficiency level."""
    if score >= 4.5:
        return ProficiencyLevel.EXPERT
    elif score >= 3.5:
        return ProficiencyLevel.ADVANCED
    elif score >= 2.5:
        return ProficiencyLevel.INTERMEDIATE
    elif score >= 1.5:
        return ProficiencyLevel.BEGINNER
    else:
        return ProficiencyLevel.NOVICE

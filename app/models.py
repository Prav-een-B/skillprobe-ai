"""
Pydantic models for request / response validation and session state.
"""

from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


# ── Enums ────────────────────────────────────────────────────

class SkillImportance(str, Enum):
    CRITICAL = "critical"
    IMPORTANT = "important"
    NICE_TO_HAVE = "nice-to-have"


class ProficiencyLevel(str, Enum):
    NOVICE = "novice"
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


# ── Skill Models ─────────────────────────────────────────────

class RequiredSkill(BaseModel):
    name: str
    importance: str = "important"  # relaxed from Enum
    category: str = ""


class CandidateSkill(BaseModel):
    name: str
    claimed_experience: str = ""
    context: str = ""


class SkillGap(BaseModel):
    skill: str
    status: str = "missing"  # relaxed from Enum
    adjacent_to: list[str] = []


class SkillExtractionResult(BaseModel):
    required_skills: list[RequiredSkill] = []
    candidate_skills: list[CandidateSkill] = []
    initial_gaps: list[SkillGap] = []


# ── Assessment Models ────────────────────────────────────────

class AssessmentQuestion(BaseModel):
    skill_name: str
    question: str
    difficulty: str  # "easy", "medium", "hard"
    question_number: int
    total_questions_for_skill: int


class AnswerEvaluation(BaseModel):
    score: int = Field(ge=1, le=5)
    level: ProficiencyLevel
    feedback: str
    strengths: list[str] = []
    weaknesses: list[str] = []


class SkillAssessmentResult(BaseModel):
    skill_name: str
    importance: SkillImportance
    final_score: float
    level: ProficiencyLevel
    questions_asked: int
    details: str = ""


class AssessmentSession(BaseModel):
    session_id: str
    jd_text: str = ""
    resume_text: str = ""
    extraction_result: Optional[SkillExtractionResult] = None
    current_skill_index: int = 0
    current_question_number: int = 0
    skills_to_assess: list[RequiredSkill] = []
    conversation_history: list[dict] = []
    skill_scores: list[SkillAssessmentResult] = []
    current_difficulty: str = "medium"
    is_complete: bool = False
    last_question: Optional[AssessmentQuestion] = None


# ── Learning Plan Models ─────────────────────────────────────

class LearningResource(BaseModel):
    title: str
    url: str
    type: str  # "course", "documentation", "tutorial", "video", "book"
    estimated_hours: float = 0


class LearningItem(BaseModel):
    skill_name: str
    current_level: str
    target_level: str
    priority: str  # "high", "medium", "low"
    why_important: str
    resources: list[LearningResource] = []
    estimated_weeks: float = 0
    prerequisites_you_have: list[str] = []
    milestones: list[str] = []


class LearningPlan(BaseModel):
    overall_readiness_score: float  # 0–100
    summary: str
    strengths: list[str] = []
    critical_gaps: list[str] = []
    learning_items: list[LearningItem] = []
    total_estimated_weeks: float = 0


# ── API Request / Response Models ────────────────────────────

class UploadResponse(BaseModel):
    session_id: str
    extraction_result: SkillExtractionResult
    skills_to_assess_count: int


class StartAssessmentResponse(BaseModel):
    session_id: str
    question: AssessmentQuestion
    total_skills: int
    current_skill_number: int


class SubmitAnswerRequest(BaseModel):
    session_id: str
    answer: str


class SubmitAnswerResponse(BaseModel):
    evaluation: AnswerEvaluation
    next_question: Optional[AssessmentQuestion] = None
    is_skill_complete: bool = False
    is_assessment_complete: bool = False
    current_skill_number: int = 0
    total_skills: int = 0
    skill_result: Optional[SkillAssessmentResult] = None


class GeneratePlanRequest(BaseModel):
    session_id: str


class GeneratePlanResponse(BaseModel):
    session_id: str
    plan: LearningPlan

"""
Skill Extractor — uses Gemini to extract and match skills from JD + Resume.
"""

from app.services.ai_service import call_ai_json
from app.prompts.templates import EXTRACT_SKILLS_PROMPT
from app.models import SkillExtractionResult, RequiredSkill, CandidateSkill, SkillGap


async def extract_skills(jd_text: str, resume_text: str) -> SkillExtractionResult:
    """
    Extract required skills from JD, candidate skills from resume,
    and identify initial gaps.
    """
    prompt = EXTRACT_SKILLS_PROMPT.format(
        jd_text=jd_text,
        resume_text=resume_text,
    )

    try:
        data = await call_ai_json(prompt)
    except Exception as e:
        print(f"Gemini API Error: {e}")
        raise ValueError(f"Failed to call Gemini API: {str(e)}")
        
    try:
        required_skills = [
            RequiredSkill(**s) for s in data.get("required_skills", [])
        ]
        candidate_skills = [
            CandidateSkill(**s) for s in data.get("candidate_skills", [])
        ]
        initial_gaps = [
            SkillGap(**g) for g in data.get("initial_gaps", [])
        ]

        return SkillExtractionResult(
            required_skills=required_skills,
            candidate_skills=candidate_skills,
            initial_gaps=initial_gaps,
        )
    except Exception as e:
        print("====== JSON DECODE OR VALIDATION ERROR ======")
        print(f"Error: {e}")
        print(f"Raw Data: {data}")
        print("=============================================")
        raise ValueError(f"Data validation failed: {str(e)}")

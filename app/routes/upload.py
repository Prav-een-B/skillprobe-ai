"""
Upload route — handles resume PDF + JD text upload, extracts skills.
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.services.resume_parser import extract_text_from_pdf, clean_text
from app.services.skill_extractor import extract_skills
from app.services.assessment import create_session
from app.models import UploadResponse

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_resume_and_jd(
    jd_text: str = Form(...),
    resume_file: UploadFile | None = File(None),
    resume_text: str = Form(""),
):
    """
    Upload a resume (PDF or plain text) and Job Description.
    Returns extracted skills and a session ID for assessment.
    """
    # Parse resume
    if resume_file and resume_file.filename:
        if not resume_file.filename.lower().endswith(".pdf"):
            raise HTTPException(400, "Only PDF files are supported for resume upload.")
        pdf_bytes = await resume_file.read()
        if len(pdf_bytes) > 10 * 1024 * 1024:
            raise HTTPException(400, "File too large. Maximum 10 MB.")
        parsed_resume = extract_text_from_pdf(pdf_bytes)
    elif resume_text.strip():
        parsed_resume = clean_text(resume_text)
    else:
        raise HTTPException(400, "Please provide a resume (PDF upload or paste text).")

    jd_cleaned = clean_text(jd_text)
    if len(jd_cleaned) < 50:
        raise HTTPException(400, "Job description seems too short. Please provide more details.")

    # Extract skills using AI
    try:
        extraction_result = await extract_skills(jd_cleaned, parsed_resume)
    except Exception as e:
        raise HTTPException(500, f"Error analysing documents: {str(e)}")

    # Create assessment session
    session = create_session(jd_cleaned, parsed_resume, extraction_result)

    return UploadResponse(
        session_id=session.session_id,
        extraction_result=extraction_result,
        skills_to_assess_count=len(session.skills_to_assess),
    )

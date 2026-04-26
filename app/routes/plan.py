"""
Learning Plan routes — generate and retrieve personalised learning plans.
"""

from fastapi import APIRouter, HTTPException
from app.services.learning_plan import generate_learning_plan
from app.services.assessment import get_session
from app.models import GeneratePlanRequest, GeneratePlanResponse

router = APIRouter()

# Cache generated plans
_plan_cache: dict[str, dict] = {}


@router.post("/plan/generate", response_model=GeneratePlanResponse)
async def generate_plan(request: GeneratePlanRequest):
    """Generate a personalised learning plan from assessment results."""
    session = get_session(request.session_id)
    if not session:
        raise HTTPException(404, "Session not found.")

    if not session.is_complete:
        raise HTTPException(400, "Assessment must be completed before generating a plan.")

    # Check cache
    if request.session_id in _plan_cache:
        return GeneratePlanResponse(
            session_id=request.session_id,
            plan=_plan_cache[request.session_id],
        )

    try:
        plan = await generate_learning_plan(request.session_id)
    except Exception as e:
        raise HTTPException(500, f"Error generating learning plan: {str(e)}")

    _plan_cache[request.session_id] = plan

    return GeneratePlanResponse(
        session_id=request.session_id,
        plan=plan,
    )


@router.get("/plan/{session_id}")
async def get_plan(session_id: str):
    """Get a previously generated learning plan."""
    if session_id not in _plan_cache:
        raise HTTPException(404, "No learning plan found. Generate one first.")

    return {
        "session_id": session_id,
        "plan": _plan_cache[session_id],
    }

from fastapi.responses import StreamingResponse
import io
from fpdf import FPDF

@router.get("/plan/export-pdf/{session_id}")
async def export_plan_pdf(session_id: str):
    if session_id not in _plan_cache:
        raise HTTPException(404, "Learning plan not found")
    
    # plan is already a LearningPlan object
    plan = _plan_cache[session_id]

    try:
        class PDF(FPDF):
            def header(self):
                self.set_font('helvetica', 'B', 15)
                self.cell(0, 10, 'SkillProbe AI - Personalised Learning Plan', new_x="LMARGIN", new_y="NEXT", align='C')
                self.ln(5)

            def footer(self):
                self.set_y(-15)
                self.set_font('helvetica', 'I', 8)
                self.cell(0, 10, f'Page {self.page_no()}', new_x="LMARGIN", new_y="NEXT", align='C')

        pdf = PDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        pdf.set_font("helvetica", 'B', 14)
        pdf.cell(0, 10, f"Overall Readiness Score: {plan.overall_readiness_score}%", new_x="LMARGIN", new_y="NEXT")
        
        pdf.set_font("helvetica", '', 11)
        pdf.multi_cell(0, 8, plan.summary, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(5)
        
        pdf.set_font("helvetica", 'B', 12)
        pdf.cell(0, 8, "Strengths", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("helvetica", '', 11)
        for s in plan.strengths:
            pdf.multi_cell(0, 6, f"- {s}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(5)
        
        pdf.set_font("helvetica", 'B', 12)
        pdf.cell(0, 8, "Critical Gaps", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("helvetica", '', 11)
        for g in plan.critical_gaps:
            pdf.multi_cell(0, 6, f"- {g}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(5)
        
        pdf.set_font("helvetica", 'B', 14)
        pdf.cell(0, 10, "Learning Timeline", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        
        for item in plan.learning_items:
            pdf.set_font("helvetica", 'B', 12)
            pdf.cell(0, 8, f"{item.skill_name} ({item.priority.upper()} Priority)", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("helvetica", '', 10)
            pdf.cell(0, 6, f"Progression: {item.current_level} -> {item.target_level} | Est: {item.estimated_weeks} weeks", new_x="LMARGIN", new_y="NEXT")
            pdf.multi_cell(0, 6, f"Why important: {item.why_important}", new_x="LMARGIN", new_y="NEXT")
            if item.prerequisites_you_have:
                pdf.multi_cell(0, 6, f"Prerequisites you have: {', '.join(item.prerequisites_you_have)}", new_x="LMARGIN", new_y="NEXT")
            
            pdf.ln(2)
            pdf.set_font("helvetica", 'I', 10)
            pdf.cell(0, 6, "Resources:", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("helvetica", '', 10)
            for r in item.resources:
                pdf.multi_cell(0, 6, f"- {r.title} ({r.type}, {r.estimated_hours}h) : {r.url}", new_x="LMARGIN", new_y="NEXT")
            
            pdf.ln(5)
            
        pdf_bytes = bytes(pdf.output())
        
        return StreamingResponse(
            io.BytesIO(pdf_bytes), 
            media_type="application/pdf", 
            headers={"Content-Disposition": "attachment; filename=learning_plan.pdf"}
        )
    except Exception as e:
        import traceback
        return StreamingResponse(
            io.BytesIO(f"PDF Generation Error:\n{traceback.format_exc()}".encode('utf-8')), 
            media_type="text/plain"
        )

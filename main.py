"""
SkillProbe AI — AI-Powered Skill Assessment & Personalised Learning Plan Agent
Entry point for the FastAPI application.
"""

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from pathlib import Path

from app.config import settings
from app.routes import upload, assess, plan

# ── App Setup ────────────────────────────────────────────────
app = FastAPI(
    title="SkillProbe AI",
    description="AI-Powered Skill Assessment & Personalised Learning Plan Agent",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static Files & Templates ────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# ── API Routes ───────────────────────────────────────────────
app.include_router(upload.router, prefix="/api", tags=["Upload"])
app.include_router(assess.router, prefix="/api", tags=["Assessment"])
app.include_router(plan.router, prefix="/api", tags=["Learning Plan"])


# ── Serve Frontend ───────────────────────────────────────────
@app.get("/")
async def serve_frontend(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


# ── Run ──────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n✨ SkillProbe AI starting...")
    print(f"🌐 Open http://localhost:8000 in your browser\n")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

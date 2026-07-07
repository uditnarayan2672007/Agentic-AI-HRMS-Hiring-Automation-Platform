"""
Resume Router — Upload PDF resumes, trigger AI parsing, semantic ranking
"""
import os
import uuid
import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import Applicant, ApplicantStatus
from app.schemas import (
    ApplicantOut, ApplicantStatusUpdate, JobDescriptionRequest,
    ResumeUploadResponse,
)
from app.agents.resume_agent import process_resume, rank_candidates_by_job
from app.agents.onboarding_agent import trigger_onboarding
from app.routers.auth import get_current_user
from app.models import User

router = APIRouter(prefix="/resumes", tags=["Resume Intelligence Agent"])

UPLOAD_DIR = Path(settings.UPLOAD_DIR)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_EXT = {".pdf"}
MAX_SIZE_MB = 10


@router.post("/upload", response_model=ResumeUploadResponse, status_code=201)
async def upload_resume(
    file: UploadFile = File(..., description="Candidate resume PDF"),
    job_title: str = Form(default="General Position"),
    job_description: str = Form(default=""),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """
    Upload a candidate's resume PDF.
    Pipeline: PyMuPDF extraction → OpenAI JSON parsing → Vector embedding → DB storage
    """
    # Validate file type
    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXT:
        raise HTTPException(400, f"Only PDF files are accepted. Got: {suffix}")

    # Check file size
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > MAX_SIZE_MB:
        raise HTTPException(413, f"File too large ({size_mb:.1f}MB). Max: {MAX_SIZE_MB}MB")

    # Save to disk
    file_id  = uuid.uuid4().hex
    save_dir = UPLOAD_DIR / file_id
    save_dir.mkdir(parents=True, exist_ok=True)
    save_path = str(save_dir / f"resume{suffix}")

    with open(save_path, "wb") as f:
        f.write(content)

    # Run the full AI pipeline
    try:
        applicant = await process_resume(
            db              = db,
            pdf_path        = save_path,
            job_title       = job_title,
            job_description = job_description,
        )
    except Exception as e:
        # Clean up on failure
        shutil.rmtree(save_dir, ignore_errors=True)
        raise HTTPException(500, f"Resume processing failed: {str(e)}")

    return ResumeUploadResponse(
        applicant_id   = applicant.id,
        full_name      = applicant.full_name,
        email          = applicant.email,
        extracted_json = applicant.resume_json or {},
        similarity_score = applicant.similarity_score,
        message        = "Resume processed and stored successfully",
    )


@router.post("/rank", summary="Rank candidates against a job description")
async def rank_candidates(
    payload: JobDescriptionRequest,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """
    Embed the job description and return top-k candidates ranked by
    vector cosine similarity from the pgvector store.
    """
    results = await rank_candidates_by_job(
        db              = db,
        job_description = payload.job_description,
        top_k           = payload.top_k,
    )
    return {
        "job_description_preview": payload.job_description[:200] + "...",
        "total_matches": len(results),
        "candidates": results,
    }


@router.get("/applicants", response_model=list[ApplicantOut])
async def list_applicants(
    status_filter: str = None,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """List all applicants, optionally filtered by status."""
    stmt = select(Applicant)
    if status_filter:
        try:
            s = ApplicantStatus(status_filter)
            stmt = stmt.where(Applicant.status == s)
        except ValueError:
            raise HTTPException(400, f"Invalid status: {status_filter}")
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/applicants/{applicant_id}", response_model=ApplicantOut)
async def get_applicant(
    applicant_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Get a specific applicant's full profile."""
    result = await db.execute(select(Applicant).where(Applicant.id == applicant_id))
    applicant = result.scalar_one_or_none()
    if not applicant:
        raise HTTPException(404, "Applicant not found")
    return applicant


@router.patch("/applicants/{applicant_id}/status")
async def update_applicant_status(
    applicant_id: uuid.UUID,
    payload: ApplicantStatusUpdate,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """
    Update applicant status.
    When set to ONBOARDING, automatically triggers the Onboarding Agent
    (generates NDA + Offer Letter + tasks).
    """
    result = await db.execute(select(Applicant).where(Applicant.id == applicant_id))
    applicant = result.scalar_one_or_none()
    if not applicant:
        raise HTTPException(404, "Applicant not found")

    old_status = applicant.status
    applicant.status = payload.status

    onboarding_triggered = False
    tasks = []

    # Auto-trigger onboarding agent
    if payload.status == ApplicantStatus.ONBOARDING and old_status != ApplicantStatus.ONBOARDING:
        tasks = await trigger_onboarding(db=db, applicant=applicant)
        onboarding_triggered = True

    return {
        "applicant_id": str(applicant_id),
        "old_status": old_status.value,
        "new_status": payload.status.value,
        "onboarding_triggered": onboarding_triggered,
        "tasks_created": len(tasks),
        "message": "Onboarding documents generated!" if onboarding_triggered else "Status updated",
    }

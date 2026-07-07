"""
Onboarding Router — Manage onboarding tasks and retrieve generated documents
"""
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Applicant, OnboardingTask, ApplicantStatus
from app.schemas import OnboardingTaskOut, OnboardingTriggerRequest
from app.agents.onboarding_agent import trigger_onboarding
from app.routers.auth import get_current_user
from app.models import User

router = APIRouter(prefix="/onboarding", tags=["Employee Onboarding Agent"])


@router.post("/trigger", status_code=201)
async def manual_trigger_onboarding(
    payload: OnboardingTriggerRequest,
    department: str = "Engineering",
    base_salary: float = 50000.0,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """
    Manually trigger the onboarding agent for a specific applicant.
    Generates NDA + Offer Letter PDFs and creates task checklist.
    """
    result = await db.execute(
        select(Applicant).where(Applicant.id == payload.applicant_id)
    )
    applicant = result.scalar_one_or_none()
    if not applicant:
        raise HTTPException(404, "Applicant not found")

    tasks = await trigger_onboarding(
        db           = db,
        applicant    = applicant,
        department   = department,
        base_salary  = base_salary,
    )

    # Update status
    applicant.status = ApplicantStatus.ONBOARDING

    return {
        "applicant_id":  str(applicant.id),
        "candidate_name": applicant.full_name,
        "tasks_created": len(tasks),
        "task_names":    [t.task_name for t in tasks],
        "documents": {
            "nda":          tasks[1].nda_path if len(tasks) > 1 else None,
            "offer_letter": tasks[2].offer_letter_path if len(tasks) > 2 else None,
        },
        "message": "Onboarding successfully triggered",
    }


@router.get("/tasks/{applicant_id}", response_model=list[OnboardingTaskOut])
async def get_onboarding_tasks(
    applicant_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Get all onboarding tasks for an applicant."""
    result = await db.execute(
        select(OnboardingTask).where(OnboardingTask.applicant_id == applicant_id)
    )
    tasks = result.scalars().all()
    if not tasks:
        raise HTTPException(404, "No onboarding tasks found for this applicant")
    return tasks


@router.patch("/tasks/{task_id}/complete")
async def mark_task_complete(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Mark an onboarding task as completed."""
    from datetime import datetime, timezone
    result = await db.execute(
        select(OnboardingTask).where(OnboardingTask.id == task_id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(404, "Task not found")

    task.is_completed = True
    task.completed_at = datetime.now(timezone.utc)

    return {
        "task_id":    str(task_id),
        "task_name":  task.task_name,
        "completed":  True,
        "completed_at": task.completed_at.isoformat(),
    }


@router.get("/document/nda/{applicant_id}")
async def download_nda(
    applicant_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Download the generated NDA PDF for an applicant."""
    result = await db.execute(
        select(OnboardingTask).where(
            OnboardingTask.applicant_id == applicant_id,
            OnboardingTask.nda_path != None,  # noqa: E711
        )
    )
    task = result.scalar_one_or_none()
    if not task or not task.nda_path:
        raise HTTPException(404, "NDA not found. Trigger onboarding first.")

    if not Path(task.nda_path).exists():
        raise HTTPException(404, "NDA file not found on disk")

    return FileResponse(
        path       = task.nda_path,
        filename   = "NDA.pdf",
        media_type = "application/pdf",
    )


@router.get("/document/offer-letter/{applicant_id}")
async def download_offer_letter(
    applicant_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Download the generated Offer Letter PDF for an applicant."""
    result = await db.execute(
        select(OnboardingTask).where(
            OnboardingTask.applicant_id == applicant_id,
            OnboardingTask.offer_letter_path != None,  # noqa: E711
        )
    )
    task = result.scalar_one_or_none()
    if not task or not task.offer_letter_path:
        raise HTTPException(404, "Offer Letter not found. Trigger onboarding first.")

    if not Path(task.offer_letter_path).exists():
        raise HTTPException(404, "Offer Letter file not found on disk")

    return FileResponse(
        path       = task.offer_letter_path,
        filename   = "Offer_Letter.pdf",
        media_type = "application/pdf",
    )

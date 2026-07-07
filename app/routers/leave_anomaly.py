"""
Leave & Anomaly Router — Leave requests, approvals, forecasting, and anomaly dashboard
"""
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import LeaveRecord, PayrollAnomaly, AnomalyStatus
from app.schemas import (
    LeaveRequest, LeaveApprovalRequest, LeaveRecordOut,
    LeaveForecast, AnomalyOut, AnomalyReviewRequest, AnomalyScanResult,
)
from app.agents.leave_anomaly_agent import (
    submit_leave_request, approve_leave,
    get_leave_forecast, scan_for_anomalies, review_anomaly,
)
from app.routers.auth import get_current_user
from app.models import User

# Two routers with distinct prefixes
leave_router   = APIRouter(prefix="/leave",     tags=["Leave Management Agent"])
anomaly_router = APIRouter(prefix="/anomalies", tags=["Payroll Anomaly Detection"])


# ════════════════════════════ LEAVE MANAGEMENT ════════════════════════════════

@leave_router.post("/request", response_model=LeaveRecordOut, status_code=201)
async def request_leave(
    payload: LeaveRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Submit a leave request. Validates balance and business days."""
    result = await submit_leave_request(
        db          = db,
        employee_id = payload.employee_id,
        leave_type  = payload.leave_type,
        start_date  = payload.start_date,
        end_date    = payload.end_date,
        reason      = payload.reason or "",
    )
    if not result["success"]:
        raise HTTPException(400, result["error"])
    return result["leave"]


@leave_router.post("/approve")
async def approve_leave_request(
    payload: LeaveApprovalRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Approve or reject a leave request.
    Records approval timestamp — critical for anomaly detection.
    """
    result = await approve_leave(
        db          = db,
        leave_id    = payload.leave_id,
        approver_id = payload.approved_by,
        approve     = payload.approve,
    )
    if not result["success"]:
        raise HTTPException(400, result["error"])

    return {
        "leave_id":    str(payload.leave_id),
        "status":      result["status"],
        "approved_by": str(payload.approved_by),
        "message":     f"Leave {result['status']} successfully",
    }


@leave_router.get("/history/{employee_id}", response_model=list[LeaveRecordOut])
async def leave_history(
    employee_id: uuid.UUID,
    year: int = Query(default=date.today().year),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Get full leave history for an employee for the given year."""
    from sqlalchemy import extract, and_
    result = await db.execute(
        select(LeaveRecord).where(
            and_(
                LeaveRecord.employee_id == employee_id,
                extract("year", LeaveRecord.start_date) == year,
            )
        ).order_by(LeaveRecord.start_date.desc())
    )
    return result.scalars().all()


@leave_router.get("/pending", response_model=list[LeaveRecordOut])
async def pending_leaves(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Get all pending leave requests (for manager dashboard)."""
    from app.models import LeaveStatus
    result = await db.execute(
        select(LeaveRecord)
        .where(LeaveRecord.status == LeaveStatus.PENDING)
        .order_by(LeaveRecord.created_at.asc())
    )
    return result.scalars().all()


@leave_router.get("/forecast/{employee_id}", response_model=LeaveForecast)
async def leave_forecast(
    employee_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Analyse leave trends and forecast potential shortfall by end of year.
    Returns trend: 'increasing' | 'stable' | 'decreasing'
    """
    result = await get_leave_forecast(db=db, employee_id=employee_id)
    if "error" in result:
        raise HTTPException(404, result["error"])
    return result


# ═══════════════════════ ANOMALY DETECTION ════════════════════════════════════

@anomaly_router.post("/scan", response_model=AnomalyScanResult)
async def trigger_anomaly_scan(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Manually trigger the Agentic Anomaly Detection scan.
    Checks all employees for:
    - Approved leaves with missing approval timestamps (UNAPPROVED_LEAVE_DEDUCTION)
    - Unexplained leave balance drops (ABRUPT_BALANCE_DROP)
    Writes PayrollAnomaly records for Swarnajit's dashboard.
    """
    result = await scan_for_anomalies(db=db)
    return AnomalyScanResult(
        scan_timestamp  = result["scan_timestamp"],
        total_checked   = result["total_checked"],
        anomalies_found = result["anomalies_found"],
        new_flags       = result["new_flags"],
        anomalies       = result["anomalies"],
    )


@anomaly_router.get("", response_model=list[AnomalyOut])
async def list_anomalies(
    status_filter: str = Query(default=None, description="Filter: open/reviewed/resolved"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    List all flagged payroll anomalies.
    Feeds Swarnajit's HR Admin Dashboard anomaly panel.
    """
    stmt = select(PayrollAnomaly).order_by(PayrollAnomaly.flagged_at.desc())
    if status_filter:
        try:
            s = AnomalyStatus(status_filter)
            stmt = stmt.where(PayrollAnomaly.status == s)
        except ValueError:
            raise HTTPException(400, f"Invalid status: {status_filter}")
    result = await db.execute(stmt)
    return result.scalars().all()


@anomaly_router.get("/dashboard-summary")
async def anomaly_dashboard_summary(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Aggregate anomaly stats for the HR dashboard widget.
    Returns counts by status and type for quick visual indicators.
    """
    from sqlalchemy import func
    result = await db.execute(
        select(
            PayrollAnomaly.anomaly_type,
            PayrollAnomaly.status,
            func.count(PayrollAnomaly.id).label("count"),
        ).group_by(PayrollAnomaly.anomaly_type, PayrollAnomaly.status)
    )
    rows = result.fetchall()

    by_type   = {}
    by_status = {}
    total     = 0

    for anomaly_type, status, count in rows:
        by_type[anomaly_type]    = by_type.get(anomaly_type, 0) + count
        by_status[status.value]  = by_status.get(status.value, 0) + count
        total += count

    return {
        "total_anomalies": total,
        "by_status":       by_status,
        "by_type":         by_type,
        "open_count":      by_status.get("open", 0),
        "critical_alert":  by_status.get("open", 0) > 0,
    }


@anomaly_router.patch("/{anomaly_id}/review")
async def review_anomaly_endpoint(
    anomaly_id: uuid.UUID,
    payload: AnomalyReviewRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Mark an anomaly as reviewed or resolved with an audit note."""
    anomaly = await review_anomaly(
        db              = db,
        anomaly_id      = anomaly_id,
        reviewer_id     = payload.reviewer_id,
        resolution_note = payload.resolution_note,
        new_status      = payload.new_status,
    )
    if not anomaly:
        raise HTTPException(404, "Anomaly not found")

    return {
        "anomaly_id":      str(anomaly_id),
        "new_status":      anomaly.status.value,
        "reviewed_at":     anomaly.reviewed_at.isoformat(),
        "resolution_note": anomaly.resolution_note,
    }

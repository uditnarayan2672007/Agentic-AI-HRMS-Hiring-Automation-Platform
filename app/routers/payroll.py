"""
Payroll Router — Endpoints for salary calculation, payroll runs, and history
"""
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Employee, PayrollRecord
from app.schemas import (
    PayrollRunRequest, PayrollRecordOut, PayrollSummary,
    EmployeeCreate, EmployeeUpdate, EmployeeOut,
)
from app.agents.payroll_agent import (
    run_payroll_bulk, calculate_net_salary, process_employee_payroll
)
from app.routers.auth import get_current_user
from app.models import User

router = APIRouter(prefix="/payroll", tags=["Payroll Agent"])


# ── Employee CRUD (needed for payroll) ───────────────────────────────────────

@router.post("/employees", response_model=EmployeeOut, status_code=201)
async def create_employee(
    payload: EmployeeCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Create an employee profile (after hiring)."""
    employee = Employee(**payload.model_dump())
    db.add(employee)
    await db.flush()
    return employee


@router.get("/employees", response_model=list[EmployeeOut])
async def list_employees(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Employee))
    return result.scalars().all()


@router.get("/employees/{employee_id}", response_model=EmployeeOut)
async def get_employee(
    employee_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    emp = result.scalar_one_or_none()
    if not emp:
        raise HTTPException(404, "Employee not found")
    return emp


@router.patch("/employees/{employee_id}", response_model=EmployeeOut)
async def update_employee(
    employee_id: uuid.UUID,
    payload: EmployeeUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    emp = result.scalar_one_or_none()
    if not emp:
        raise HTTPException(404, "Employee not found")

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(emp, field, value)
    await db.flush()
    return emp


# ── Payroll Calculation & Run ─────────────────────────────────────────────────

@router.post("/calculate", summary="Preview salary calculation without saving")
async def preview_calculation(
    base_salary: float = Query(..., gt=0, description="Monthly base salary"),
    incentives: float = Query(default=0.0, ge=0),
    tax_rate: float = Query(default=0.20, ge=0, le=1),
    unpaid_leaves: int = Query(default=0, ge=0),
    working_days: int = Query(default=22, ge=1, le=31),
    _: User = Depends(get_current_user),
):
    """
    Pure calculation endpoint — returns full salary breakdown.
    Net = Base + Incentives - Tax - (Unpaid Leaves × Daily Rate)
    No database write.
    """
    breakdown = calculate_net_salary(
        base_salary   = base_salary,
        incentives    = incentives,
        tax_rate      = tax_rate,
        unpaid_leaves = unpaid_leaves,
        working_days  = working_days,
    )
    return {
        "formula": "Net = Base + Incentives - Tax Deductions - (Unpaid Leaves × Daily Rate)",
        "breakdown": breakdown,
        "period": "Preview only — not saved",
    }


@router.post("/run", response_model=PayrollSummary)
async def run_payroll(
    payload: PayrollRunRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Execute payroll for one or all employees for a given month.
    Idempotent — safe to re-run.
    """
    result = await run_payroll_bulk(
        db           = db,
        year         = payload.year,
        month        = payload.month,
        working_days = payload.working_days,
        employee_id  = payload.employee_id,
    )

    if not result["records"]:
        raise HTTPException(404, "No employees found to process")

    return PayrollSummary(
        total_employees = result["total_employees"],
        total_gross     = result["total_gross"],
        total_deductions= result["total_deductions"],
        total_net       = result["total_net"],
        period          = result["period"],
        records         = result["records"],
    )


@router.get("/history/{employee_id}", response_model=list[PayrollRecordOut])
async def payroll_history(
    employee_id: uuid.UUID,
    limit: int = Query(default=12, ge=1, le=60),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Get payroll history for an employee (most recent first)."""
    result = await db.execute(
        select(PayrollRecord)
        .where(PayrollRecord.employee_id == employee_id)
        .order_by(PayrollRecord.period_year.desc(), PayrollRecord.period_month.desc())
        .limit(limit)
    )
    records = result.scalars().all()
    if not records:
        raise HTTPException(404, "No payroll records found")
    return records


@router.get("/dashboard/summary")
async def payroll_dashboard_summary(
    year: int = Query(default=date.today().year),
    month: int = Query(default=date.today().month, ge=1, le=12),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Dashboard summary for the given month —
    total headcount, gross, deductions, net, top earners.
    """
    result = await db.execute(
        select(PayrollRecord).where(
            and_(
                PayrollRecord.period_year  == year,
                PayrollRecord.period_month == month,
                PayrollRecord.is_processed == True,   # noqa: E712
            )
        )
    )
    records = result.scalars().all()

    if not records:
        return {
            "period": f"{year}-{month:02d}",
            "message": "No payroll records for this period",
        }

    total_gross = sum(r.base_salary + r.incentives for r in records)
    total_net   = sum(r.net_salary for r in records)
    total_tax   = sum(r.tax_deductions for r in records)
    total_leave_ded = sum(r.leave_deduction for r in records)

    sorted_records = sorted(records, key=lambda r: r.net_salary, reverse=True)

    return {
        "period":           f"{year}-{month:02d}",
        "headcount":        len(records),
        "total_gross":      round(total_gross, 2),
        "total_net":        round(total_net, 2),
        "total_tax":        round(total_tax, 2),
        "total_leave_ded":  round(total_leave_ded, 2),
        "avg_net_salary":   round(total_net / len(records), 2),
        "top_5_earners": [
            {
                "employee_id": str(r.employee_id),
                "net_salary":  r.net_salary,
            }
            for r in sorted_records[:5]
        ],
    }

"""
╔══════════════════════════════════════════════════════════════════════════════╗
║          AGENT 4 — Payroll Automation Agent                                 ║
║                                                                              ║
║  Formula:                                                                    ║
║  Net Salary = Base + Incentives - Tax Deductions - (Unpaid Leaves × Daily Rate)
║                                                                              ║
║  Features:                                                                   ║
║  • Per-employee or bulk monthly payroll calculation                         ║
║  • Configurable working days, tax bracket, incentives                       ║
║  • Idempotent — safe to re-run (upserts existing record)                    ║
║  • APScheduler cron job for auto-run on the last working day of each month  ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
import uuid
from datetime import datetime, date, timezone
from typing import Optional, List

from loguru import logger
from sqlalchemy import select, and_, extract
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Employee, LeaveRecord, PayrollRecord, LeaveType, LeaveStatus


# ─────────────────────────────────────────────────────────────────────────────
# CORE CALCULATION
# ─────────────────────────────────────────────────────────────────────────────

def calculate_net_salary(
    base_salary: float,
    incentives: float,
    tax_rate: float,
    unpaid_leaves: int,
    working_days: int = 22,
) -> dict:
    """
    Net Salary = Base + Incentives - Tax Deductions - (Unpaid Leaves × Daily Rate)

    Returns a breakdown dict with every intermediate value for full transparency.
    """
    if working_days <= 0:
        working_days = settings.DEFAULT_WORKING_DAYS

    daily_rate = base_salary / working_days
    gross = base_salary + incentives
    tax_deductions = gross * tax_rate
    leave_deduction = unpaid_leaves * daily_rate
    net_salary = gross - tax_deductions - leave_deduction

    return {
        "base_salary":    round(base_salary,    2),
        "incentives":     round(incentives,     2),
        "gross":          round(gross,           2),
        "tax_rate":       round(tax_rate,        4),
        "tax_deductions": round(tax_deductions,  2),
        "daily_rate":     round(daily_rate,      2),
        "unpaid_leaves":  unpaid_leaves,
        "leave_deduction":round(leave_deduction, 2),
        "net_salary":     round(max(net_salary, 0.0), 2),   # floor at 0
    }


# ─────────────────────────────────────────────────────────────────────────────
# UNPAID LEAVE COUNTER
# ─────────────────────────────────────────────────────────────────────────────

async def count_unpaid_leaves(
    db: AsyncSession,
    employee_id: uuid.UUID,
    year: int,
    month: int,
) -> int:
    """
    Count approved UNPAID leave days for an employee in a given month.
    Only counts leaves that overlap with the target month.
    """
    # Fetch all approved unpaid leaves for this employee
    stmt = select(LeaveRecord).where(
        and_(
            LeaveRecord.employee_id == employee_id,
            LeaveRecord.leave_type == LeaveType.UNPAID,
            LeaveRecord.status == LeaveStatus.APPROVED,
        )
    )
    result = await db.execute(stmt)
    all_unpaid = result.scalars().all()

    # Count only days that fall within target month
    month_start = date(year, month, 1)
    # Last day of month
    if month == 12:
        month_end = date(year + 1, 1, 1)
    else:
        month_end = date(year, month + 1, 1)

    total_days = 0
    for leave in all_unpaid:
        # Find overlap between leave period and target month
        overlap_start = max(leave.start_date, month_start)
        overlap_end   = min(leave.end_date, month_end)
        if overlap_start < overlap_end:
            total_days += (overlap_end - overlap_start).days

    return total_days


# ─────────────────────────────────────────────────────────────────────────────
# SINGLE EMPLOYEE PAYROLL
# ─────────────────────────────────────────────────────────────────────────────

async def process_employee_payroll(
    db: AsyncSession,
    employee: Employee,
    year: int,
    month: int,
    working_days: int = 22,
    notes: str = "",
) -> PayrollRecord:
    """
    Calculate and persist a PayrollRecord for one employee for the given period.
    Idempotent: updates the existing record if it exists.
    """
    # Check for existing record this period
    stmt = select(PayrollRecord).where(
        and_(
            PayrollRecord.employee_id == employee.id,
            PayrollRecord.period_year  == year,
            PayrollRecord.period_month == month,
        )
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    # Count unpaid leaves for this month
    unpaid_count = await count_unpaid_leaves(db, employee.id, year, month)

    # Compute
    breakdown = calculate_net_salary(
        base_salary  = employee.base_salary,
        incentives   = employee.incentives,
        tax_rate     = employee.tax_rate,
        unpaid_leaves= unpaid_count,
        working_days = working_days,
    )

    if existing:
        # Update in place (re-run scenario)
        existing.base_salary     = breakdown["base_salary"]
        existing.incentives      = breakdown["incentives"]
        existing.tax_deductions  = breakdown["tax_deductions"]
        existing.unpaid_leaves   = breakdown["unpaid_leaves"]
        existing.daily_rate      = breakdown["daily_rate"]
        existing.leave_deduction = breakdown["leave_deduction"]
        existing.net_salary      = breakdown["net_salary"]
        existing.is_processed    = True
        existing.processed_at    = datetime.now(timezone.utc)
        existing.notes           = notes or existing.notes
        record = existing
    else:
        record = PayrollRecord(
            employee_id    = employee.id,
            period_year    = year,
            period_month   = month,
            base_salary    = breakdown["base_salary"],
            incentives     = breakdown["incentives"],
            tax_deductions = breakdown["tax_deductions"],
            unpaid_leaves  = breakdown["unpaid_leaves"],
            daily_rate     = breakdown["daily_rate"],
            leave_deduction= breakdown["leave_deduction"],
            net_salary     = breakdown["net_salary"],
            is_processed   = True,
            processed_at   = datetime.now(timezone.utc),
            notes          = notes,
        )
        db.add(record)

    await db.flush()
    logger.info(
        f"💰 Payroll | Emp: {employee.employee_code} | "
        f"{year}-{month:02d} | "
        f"Base: ₹{breakdown['base_salary']:,.0f} | "
        f"Net: ₹{breakdown['net_salary']:,.0f} | "
        f"Unpaid: {unpaid_count}d"
    )
    return record


# ─────────────────────────────────────────────────────────────────────────────
# BULK PAYROLL RUN
# ─────────────────────────────────────────────────────────────────────────────

async def run_payroll_bulk(
    db: AsyncSession,
    year: int,
    month: int,
    working_days: int = 22,
    employee_id: Optional[uuid.UUID] = None,
) -> dict:
    """
    Run payroll for all employees (or a specific one).
    Returns a summary dict for the API response.
    """
    # Fetch employees
    if employee_id:
        stmt = select(Employee).where(Employee.id == employee_id)
    else:
        stmt = select(Employee)

    result = await db.execute(stmt)
    employees = result.scalars().all()

    if not employees:
        return {
            "period": f"{year}-{month:02d}",
            "total_employees": 0,
            "total_gross": 0,
            "total_net": 0,
            "records": [],
        }

    records = []
    total_gross = 0.0
    total_net   = 0.0
    total_deductions = 0.0

    for emp in employees:
        record = await process_employee_payroll(
            db           = db,
            employee     = emp,
            year         = year,
            month        = month,
            working_days = working_days,
        )
        records.append(record)
        total_gross      += record.base_salary + record.incentives
        total_net        += record.net_salary
        total_deductions += record.tax_deductions + record.leave_deduction

    logger.info(
        f"✅ Bulk payroll complete — {len(records)} employees | "
        f"Total Net: ₹{total_net:,.2f}"
    )

    return {
        "period": f"{year}-{month:02d}",
        "total_employees": len(records),
        "total_gross": round(total_gross, 2),
        "total_deductions": round(total_deductions, 2),
        "total_net": round(total_net, 2),
        "records": records,
    }


# ─────────────────────────────────────────────────────────────────────────────
# CRON JOB HANDLER (called by APScheduler)
# ─────────────────────────────────────────────────────────────────────────────

async def scheduled_payroll_job():
    """
    APScheduler async job — runs automatically on the 28th of every month.
    Creates its own DB session independently.
    """
    from app.database import AsyncSessionLocal
    now = datetime.now(timezone.utc)
    logger.info(f"🕐 Scheduled payroll job triggered — {now.strftime('%Y-%m-%d %H:%M UTC')}")

    async with AsyncSessionLocal() as db:
        try:
            result = await run_payroll_bulk(
                db           = db,
                year         = now.year,
                month        = now.month,
                working_days = settings.DEFAULT_WORKING_DAYS,
            )
            await db.commit()
            logger.info(
                f"✅ Scheduled payroll done — "
                f"{result['total_employees']} employees, "
                f"Net: ₹{result['total_net']:,.2f}"
            )
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Scheduled payroll failed: {e}")

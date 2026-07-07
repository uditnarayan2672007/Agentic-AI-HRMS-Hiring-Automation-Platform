"""
APScheduler — Background Cron Jobs for Payroll & Anomaly Detection

Jobs:
  • Payroll Run    — Every month on the 28th at 02:00 UTC
  • Anomaly Scan   — Every day at 06:00 UTC
  • Leave Forecast — Every Monday at 07:00 UTC (logs warnings)
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

scheduler = AsyncIOScheduler(timezone="UTC")


def setup_scheduler():
    """Register all cron jobs on the APScheduler instance."""

    # ── Job 1: Monthly Payroll Run (28th of every month at 02:00 UTC) ────────
    scheduler.add_job(
        func            = _payroll_job,
        trigger         = CronTrigger(day=28, hour=2, minute=0),
        id              = "monthly_payroll",
        name            = "Monthly Payroll Calculation",
        replace_existing= True,
        max_instances   = 1,
        misfire_grace_time = 3600,
    )
    logger.info("📅 Cron: Monthly Payroll → every 28th at 02:00 UTC")

    # ── Job 2: Daily Anomaly Scan (every day at 06:00 UTC) ────────────────────
    scheduler.add_job(
        func            = _anomaly_scan_job,
        trigger         = CronTrigger(hour=6, minute=0),
        id              = "daily_anomaly_scan",
        name            = "Daily Payroll Anomaly Detection",
        replace_existing= True,
        max_instances   = 1,
        misfire_grace_time = 1800,
    )
    logger.info("📅 Cron: Anomaly Scan → every day at 06:00 UTC")

    # ── Job 3: Weekly Leave Forecast Analysis (every Monday at 07:00 UTC) ─────
    scheduler.add_job(
        func            = _leave_forecast_job,
        trigger         = CronTrigger(day_of_week="mon", hour=7, minute=0),
        id              = "weekly_leave_forecast",
        name            = "Weekly Leave Forecast Analysis",
        replace_existing= True,
        max_instances   = 1,
    )
    logger.info("📅 Cron: Leave Forecast → every Monday at 07:00 UTC")

    return scheduler


# ── Async Job Handlers ────────────────────────────────────────────────────────

async def _payroll_job():
    """Wrapper for the payroll agent's scheduled job."""
    try:
        from app.agents.payroll_agent import scheduled_payroll_job
        await scheduled_payroll_job()
    except Exception as e:
        logger.error(f"❌ Payroll cron job error: {e}")


async def _anomaly_scan_job():
    """Wrapper for the anomaly detection agent's scheduled job."""
    try:
        from app.agents.leave_anomaly_agent import scheduled_anomaly_scan
        await scheduled_anomaly_scan()
    except Exception as e:
        logger.error(f"❌ Anomaly scan cron job error: {e}")


async def _leave_forecast_job():
    """
    Weekly leave forecast — logs employees with predicted shortfall.
    In production, this would push notifications to the dashboard.
    """
    from app.database import AsyncSessionLocal
    from app.agents.leave_anomaly_agent import get_leave_forecast
    from sqlalchemy import select
    from app.models import Employee

    logger.info("📊 Weekly leave forecast analysis starting...")
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(Employee))
            employees = result.scalars().all()
            at_risk = []

            for emp in employees:
                forecast = await get_leave_forecast(db, emp.id)
                if forecast.get("predicted_shortfall"):
                    at_risk.append({
                        "employee_code":  emp.employee_code,
                        "balance":        forecast["current_balance"],
                        "trend":          forecast["trend"],
                    })

            if at_risk:
                logger.warning(
                    f"⚠️ {len(at_risk)} employees at leave shortfall risk: "
                    + ", ".join(e["employee_code"] for e in at_risk)
                )
            else:
                logger.info("✅ No employees at leave shortfall risk this week")

        except Exception as e:
            logger.error(f"❌ Leave forecast job error: {e}")

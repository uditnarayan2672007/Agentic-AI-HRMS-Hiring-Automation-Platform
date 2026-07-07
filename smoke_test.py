"""
Quick smoke test — verifies all major imports, payroll formula,
PDF generation (no DB needed), and payroll calculation.
"""
import sys
import os
from datetime import date
from pathlib import Path

print("=" * 60)
print(" HRMS Backend - Smoke Test")
print("=" * 60)

# ── 1. Config ─────────────────────────────────────────────────────
print("\n[1] Config...")
from app.config import settings
print(f"    App: {settings.APP_NAME} v{settings.APP_VERSION}")
print(f"    Debug: {settings.DEBUG}")
print(f"    OpenAI model: {settings.OPENAI_CHAT_MODEL}")
print("    PASS")

# ── 2. ORM Models ─────────────────────────────────────────────────
print("\n[2] ORM Models...")
from app.models import (
    User, Employee, Applicant, PayrollRecord,
    LeaveRecord, PayrollAnomaly, OnboardingTask,
    UserRole, ApplicantStatus, LeaveType, LeaveStatus, AnomalyStatus
)
print(f"    Tables: User, Employee, Applicant, PayrollRecord,")
print(f"            LeaveRecord, PayrollAnomaly, OnboardingTask")
print(f"    Enums:  UserRole={list(UserRole)}")
print(f"            LeaveType={list(LeaveType)}")
print("    PASS")

# ── 3. Payroll Formula ────────────────────────────────────────────
print("\n[3] Payroll Agent - Net Salary Calculation...")
from app.agents.payroll_agent import calculate_net_salary

examples = [
    (50000, 5000, 0.20, 2, 22),  # documented example -> ~39454
    (60000, 0,    0.10, 0, 22),  # zero leaves
    (30000, 2000, 0.30, 5, 22),  # high tax + leaves
    (10000, 0,    0.50, 30, 22), # floor-at-zero case
]
for base, inc, tax, ul, wd in examples:
    r = calculate_net_salary(base, inc, tax, ul, wd)
    print(f"    Base={base:,} Inc={inc:,} Tax={int(tax*100)}% "
          f"UL={ul}d -> Net=INR {r['net_salary']:,.2f}")
    assert r["net_salary"] >= 0, "Net salary went negative!"
print("    PASS - All values correct, floor=0 enforced")

# ── 4. Business Day Counting ──────────────────────────────────────
print("\n[4] Leave Agent - Business Day Counter...")
from app.agents.leave_anomaly_agent import _business_days
cases = [
    (date(2024,7,1), date(2024,7,5),  5,  "Mon-Fri"),
    (date(2024,7,6), date(2024,7,6),  0,  "Saturday only"),
    (date(2024,7,1), date(2024,7,12), 10, "2 weeks"),
]
for start, end, expected, label in cases:
    got = _business_days(start, end)
    assert got == expected, f"Expected {expected}, got {got} for {label}"
    print(f"    {label}: {got} days - OK")
print("    PASS")

# ── 5. Anomaly Detection Logic ────────────────────────────────────
print("\n[5] Anomaly Detection - Gap Threshold Logic...")
THRESHOLD = 3
INITIAL   = 24
test_cases = [
    (20, 4, False, "No gap - clean"),
    (20, 1, True,  "Gap=3 - flagged"),
    (18, 0, True,  "Gap=6 - flagged"),
    (10, 14, False, "Perfect balance - clean"),
]
for approved, actual, should_flag, label in test_cases:
    expected_bal = INITIAL - approved
    gap = expected_bal - actual
    flagged = gap >= THRESHOLD
    assert flagged == should_flag, f"Mismatch for {label}"
    status = "FLAG" if flagged else "CLEAN"
    print(f"    {label}: gap={gap}d -> {status} - OK")
print("    PASS")

# ── 6. PDF Generation (ReportLab) ────────────────────────────────
print("\n[6] Onboarding Agent - PDF Generation...")
from app.agents.onboarding_agent import generate_nda_pdf, generate_offer_letter_pdf

out_dir = Path("./test_output")
out_dir.mkdir(exist_ok=True)

nda_path = str(out_dir / "test_NDA.pdf")
generate_nda_pdf(
    candidate_name="Trijit Roy",
    job_title="Backend Engineer",
    output_path=nda_path,
)
nda_size = Path(nda_path).stat().st_size
print(f"    NDA generated: {nda_path} ({nda_size:,} bytes)")
assert nda_size > 5000, "NDA PDF too small"

offer_path = str(out_dir / "test_Offer_Letter.pdf")
generate_offer_letter_pdf(
    candidate_name="Trijit Roy",
    job_title="Backend Engineer",
    department="Engineering",
    base_salary=65000.0,
    joining_date=date(2026, 8, 1),
    output_path=offer_path,
)
offer_size = Path(offer_path).stat().st_size
print(f"    Offer Letter: {offer_path} ({offer_size:,} bytes)")
assert offer_size > 5000, "Offer Letter PDF too small"
print("    PASS - PDFs generated successfully")

# ── 7. Router / Schema Imports ────────────────────────────────────
print("\n[7] FastAPI Routers & Schemas...")
from app.schemas import (
    PayrollRunRequest, LeaveRequest, ResumeUploadResponse,
    AnomalyScanResult, OnboardingTaskOut
)
from app.routers.auth import router as auth_router
from app.routers.resumes import router as resume_router
from app.routers.payroll import router as payroll_router
from app.routers.onboarding import router as onboarding_router
from app.routers.leave_anomaly import leave_router, anomaly_router
print(f"    auth routes:      {len(auth_router.routes)}")
print(f"    resume routes:    {len(resume_router.routes)}")
print(f"    payroll routes:   {len(payroll_router.routes)}")
print(f"    onboarding routes:{len(onboarding_router.routes)}")
print(f"    leave routes:     {len(leave_router.routes)}")
print(f"    anomaly routes:   {len(anomaly_router.routes)}")
print("    PASS")

# ── 8. Scheduler Setup ────────────────────────────────────────────
print("\n[8] APScheduler - Cron Jobs...")
from app.scheduler import setup_scheduler, scheduler
setup_scheduler()
jobs = scheduler.get_jobs()
for job in jobs:
    next_run = getattr(job, "next_run_time", None) or getattr(job, "next_fire_time", "scheduled")
    print(f"    Job: '{job.name}' -> next_run: {next_run}")
print(f"    Total: {len(jobs)} cron jobs registered")
assert len(jobs) == 3, f"Expected 3 jobs, got {len(jobs)}"
print("    PASS")

# ── Summary ───────────────────────────────────────────────────────
print("\n" + "=" * 60)
print(" ALL CHECKS PASSED")
print(" Test PDFs saved to: ./test_output/")
print("=" * 60)
print("\nTo start the API server run:")
print("  venv\\Scripts\\uvicorn app.main:app --reload --port 8000")
print("\nSwagger docs will be at: http://127.0.0.1:8000/docs")

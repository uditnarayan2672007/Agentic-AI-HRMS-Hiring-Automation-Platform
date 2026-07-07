"""
Elite Coders HRMS — FastAPI Application Entry Point

Agents registered:
  • Agent 1: Resume Intelligence  (/resumes/*)
  • Agent 3: Employee Onboarding  (/onboarding/*)
  • Agent 4: Payroll Automation   (/payroll/*)
  • Agent 5: Leave Management     (/leave/*)
  • Bonus:   Anomaly Detection    (/anomalies/*)
"""
import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from app.config import settings
from app.database import init_db
from app.scheduler import scheduler, setup_scheduler
from app.routers import auth, resumes, onboarding, payroll
from app.routers.leave_anomaly import leave_router, anomaly_router



# ─────────────────────────────────────────────────────────────────────────────
# Startup / Shutdown Lifecycle
# ─────────────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager:
    - DB initialisation (creates tables, enables pgvector)
    - APScheduler startup (payroll + anomaly cron jobs)
    - Graceful shutdown
    """
    logger.info("🚀 Elite Coders HRMS API starting up...")

    # Create upload/docs directories
    os.makedirs(settings.UPLOAD_DIR,        exist_ok=True)
    os.makedirs(settings.GENERATED_DOCS_DIR, exist_ok=True)

    # Initialise DB
    try:
        await init_db()
    except Exception as e:
        logger.warning(f"⚠️ DB init skipped (no live DB): {e}")

    # Start APScheduler
    setup_scheduler()
    scheduler.start()
    logger.info("⏰ APScheduler started — cron jobs active")

    yield

    # Cleanup
    scheduler.shutdown(wait=False)
    logger.info("👋 HRMS API shutdown complete")


# ─────────────────────────────────────────────────────────────────────────────
# FastAPI App
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title       = settings.APP_NAME,
    version     = settings.APP_VERSION,
    description = """
## 🤖 Elite Coders HRMS — Agentic AI Backend (Trijit's Module)

### Agents & Pipelines
| Agent | Endpoint Prefix | Tech |
|-------|----------------|------|
| **1. Resume Intelligence** | `/resumes` | PyMuPDF + OpenAI JSON Mode + pgvector |
| **3. Onboarding** | `/onboarding` | ReportLab PDF Generation |
| **4. Payroll** | `/payroll` | Formula Engine + APScheduler Cron |
| **5. Leave** | `/leave` | Business-day calculation + Balance tracking |
| **Bonus: Anomaly Detection** | `/anomalies` | Agentic DB Scanner → Dashboard flags |

### Payroll Formula
> **Net Salary = Base + Incentives − Tax Deductions − (Unpaid Leaves × Daily Rate)**

### Anomaly Detection Cases
- `UNAPPROVED_LEAVE_DEDUCTION` — approved leave with no manager timestamp
- `ABRUPT_BALANCE_DROP` — leave balance gap > 3 days without approved leave
""",
    lifespan    = lifespan,
    docs_url    = "/docs",
    redoc_url   = "/redoc",
    openapi_url = "/openapi.json",
)


# ─────────────────────────────────────────────────────────────────────────────
# Middleware
# ─────────────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["*"],   # restrict in production
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)


@app.middleware("http")
async def request_timing_middleware(request: Request, call_next):
    """Log every request with method, path, status, and duration."""
    start = time.perf_counter()
    response = await call_next(request)
    duration = (time.perf_counter() - start) * 1000
    logger.info(
        f"{request.method} {request.url.path} → {response.status_code} "
        f"({duration:.1f}ms)"
    )
    return response


# ─────────────────────────────────────────────────────────────────────────────
# Routers
# ─────────────────────────────────────────────────────────────────────────────

API_PREFIX = "/api/v1"

app.include_router(auth.router,       prefix=API_PREFIX)
app.include_router(resumes.router,    prefix=API_PREFIX)
app.include_router(onboarding.router, prefix=API_PREFIX)
app.include_router(payroll.router,    prefix=API_PREFIX)
app.include_router(leave_router,      prefix=API_PREFIX)
app.include_router(anomaly_router,    prefix=API_PREFIX)



# ─────────────────────────────────────────────────────────────────────────────
# Root & Health Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
async def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status":  "🟢 online",
        "docs":    "/docs",
        "agents": {
            "resume_intelligence": f"{API_PREFIX}/resumes",
            "onboarding":          f"{API_PREFIX}/onboarding",
            "payroll":             f"{API_PREFIX}/payroll",
            "leave_management":    f"{API_PREFIX}/leave",
            "anomaly_detection":   f"{API_PREFIX}/anomalies",
        },
        "cron_jobs": {
            "monthly_payroll":    "Every 28th at 02:00 UTC",
            "daily_anomaly_scan": "Every day at 06:00 UTC",
            "weekly_forecast":    "Every Monday at 07:00 UTC",
        },
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Kubernetes/Docker health probe endpoint."""
    return {
        "status": "healthy",
        "scheduler_running": scheduler.running,
        "jobs": [
            {
                "id":       job.id,
                "name":     job.name,
                "next_run": str(job.next_run_time),
            }
            for job in scheduler.get_jobs()
        ],
    }


@app.get("/api/v1/payroll/formula", tags=["Payroll Agent"])
async def payroll_formula():
    """Return the payroll formula documentation."""
    return {
        "formula": "Net Salary = Base Salary + Incentives - Tax Deductions - (Unpaid Leaves × Daily Rate)",
        "components": {
            "Base Salary":     "Monthly fixed compensation",
            "Incentives":      "Performance bonuses and variable pay",
            "Tax Deductions":  "(Base + Incentives) × Tax Rate",
            "Daily Rate":      "Base Salary ÷ Working Days in Month",
            "Leave Deduction": "Unpaid Leave Days × Daily Rate",
        },
        "example": {
            "base_salary":    50000,
            "incentives":     5000,
            "tax_rate":       0.20,
            "unpaid_leaves":  2,
            "working_days":   22,
            "daily_rate":     "50000 / 22 = ₹2272.73",
            "tax":            "(50000 + 5000) × 0.20 = ₹11000",
            "leave_deduction":"2 × 2272.73 = ₹4545.45",
            "net_salary":     "55000 - 11000 - 4545.45 = ₹39454.55",
        },
    }

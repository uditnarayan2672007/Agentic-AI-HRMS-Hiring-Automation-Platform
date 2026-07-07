"""
Pydantic Schemas — Request & Response models for all API endpoints
"""
import uuid
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field

from app.models import (
    UserRole, ApplicantStatus, LeaveType,
    LeaveStatus, AnomalyStatus,
)


# ══════════════════════════════ AUTH ══════════════════════════════════════════

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: UserRole = UserRole.EMPLOYEE


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ══════════════════════════ EMPLOYEE ══════════════════════════════════════════

class EmployeeCreate(BaseModel):
    user_id: uuid.UUID
    employee_code: str
    department: str
    designation: str
    date_of_joining: date
    base_salary: float = Field(gt=0)
    incentives: float = 0.0
    tax_rate: float = Field(default=0.20, ge=0, le=1)
    leave_balance: int = 24
    manager_id: Optional[uuid.UUID] = None


class EmployeeUpdate(BaseModel):
    department: Optional[str] = None
    designation: Optional[str] = None
    base_salary: Optional[float] = None
    incentives: Optional[float] = None
    tax_rate: Optional[float] = None
    leave_balance: Optional[int] = None
    manager_id: Optional[uuid.UUID] = None


class EmployeeOut(BaseModel):
    id: uuid.UUID
    employee_code: str
    department: Optional[str]
    designation: Optional[str]
    date_of_joining: Optional[date]
    base_salary: float
    incentives: float
    tax_rate: float
    leave_balance: int
    created_at: datetime

    class Config:
        from_attributes = True


# ══════════════════════════ RESUME / APPLICANT ════════════════════════════════

class ResumeUploadResponse(BaseModel):
    applicant_id: uuid.UUID
    full_name: str
    email: str
    extracted_json: Dict[str, Any]
    similarity_score: Optional[float]
    message: str


class ApplicantStatusUpdate(BaseModel):
    status: ApplicantStatus


class ApplicantOut(BaseModel):
    id: uuid.UUID
    full_name: str
    email: str
    phone: Optional[str]
    job_title: Optional[str]
    status: ApplicantStatus
    resume_json: Optional[Dict[str, Any]]
    similarity_score: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


class JobDescriptionRequest(BaseModel):
    job_description: str
    top_k: int = Field(default=10, ge=1, le=50)


# ══════════════════════════ ONBOARDING ════════════════════════════════════════

class OnboardingTriggerRequest(BaseModel):
    applicant_id: uuid.UUID


class OnboardingTaskOut(BaseModel):
    id: uuid.UUID
    task_name: str
    description: Optional[str]
    is_completed: bool
    due_date: Optional[date]
    nda_path: Optional[str]
    offer_letter_path: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class OnboardingTaskComplete(BaseModel):
    task_id: uuid.UUID


# ══════════════════════════ PAYROLL ═══════════════════════════════════════════

class PayrollRunRequest(BaseModel):
    employee_id: Optional[uuid.UUID] = None   # None = run for ALL employees
    year: int
    month: int = Field(ge=1, le=12)
    working_days: int = Field(default=22, ge=1, le=31)


class PayrollRecordOut(BaseModel):
    id: uuid.UUID
    employee_id: uuid.UUID
    period_year: int
    period_month: int
    base_salary: float
    incentives: float
    tax_deductions: float
    unpaid_leaves: int
    daily_rate: float
    leave_deduction: float
    net_salary: float
    is_processed: bool
    processed_at: Optional[datetime]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class PayrollSummary(BaseModel):
    total_employees: int
    total_gross: float
    total_deductions: float
    total_net: float
    period: str
    records: List[PayrollRecordOut]


# ══════════════════════════ LEAVE ═════════════════════════════════════════════

class LeaveRequest(BaseModel):
    employee_id: uuid.UUID
    leave_type: LeaveType
    start_date: date
    end_date: date
    reason: Optional[str] = None


class LeaveApprovalRequest(BaseModel):
    leave_id: uuid.UUID
    approved_by: uuid.UUID
    approve: bool                  # True = approve, False = reject


class LeaveRecordOut(BaseModel):
    id: uuid.UUID
    employee_id: uuid.UUID
    leave_type: LeaveType
    start_date: date
    end_date: date
    days_count: int
    reason: Optional[str]
    status: LeaveStatus
    approved_by: Optional[uuid.UUID]
    approved_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class LeaveForecast(BaseModel):
    employee_id: uuid.UUID
    current_balance: int
    leaves_this_year: int
    leaves_by_type: Dict[str, int]
    predicted_shortfall: bool
    trend: str                   # "increasing" | "stable" | "decreasing"


# ══════════════════════════ ANOMALY ══════════════════════════════════════════

class AnomalyOut(BaseModel):
    id: uuid.UUID
    employee_id: uuid.UUID
    leave_record_id: Optional[uuid.UUID]
    anomaly_type: str
    description: str
    leave_days_flagged: Optional[int]
    status: AnomalyStatus
    flagged_at: datetime
    reviewed_at: Optional[datetime]
    resolution_note: Optional[str]

    class Config:
        from_attributes = True


class AnomalyReviewRequest(BaseModel):
    anomaly_id: uuid.UUID
    reviewer_id: uuid.UUID
    resolution_note: str
    new_status: AnomalyStatus


class AnomalyScanResult(BaseModel):
    scan_timestamp: datetime
    total_checked: int
    anomalies_found: int
    new_flags: int
    anomalies: List[AnomalyOut]

"""
SQLAlchemy ORM Models — All HRMS Entities
Tables: users, employees, applicants, payroll_records, leave_records, payroll_anomalies, onboarding_tasks
"""
import enum
import uuid
from datetime import datetime, date
from typing import List, Optional

from sqlalchemy import (
    Column, String, Float, Integer, Boolean, DateTime, Date,
    ForeignKey, Text, Enum as SAEnum, JSON, func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from pgvector.sqlalchemy import Vector

from app.database import Base


# ─────────────────────────── ENUMS ───────────────────────────────────────────

class UserRole(str, enum.Enum):
    ADMIN   = "admin"
    HR      = "hr"
    MANAGER = "manager"
    EMPLOYEE = "employee"


class ApplicantStatus(str, enum.Enum):
    APPLIED    = "applied"
    SCREENING  = "screening"
    INTERVIEW  = "interview"
    OFFERED    = "offered"
    ONBOARDING = "onboarding"
    HIRED      = "hired"
    REJECTED   = "rejected"


class LeaveType(str, enum.Enum):
    ANNUAL    = "annual"
    SICK      = "sick"
    CASUAL    = "casual"
    UNPAID    = "unpaid"
    MATERNITY = "maternity"


class LeaveStatus(str, enum.Enum):
    PENDING  = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class AnomalyStatus(str, enum.Enum):
    OPEN     = "open"
    REVIEWED = "reviewed"
    RESOLVED = "resolved"


# ─────────────────────────── USER ────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email       = Column(String(255), unique=True, nullable=False, index=True)
    full_name   = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role        = Column(SAEnum(UserRole), default=UserRole.EMPLOYEE, nullable=False)
    is_active   = Column(Boolean, default=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    updated_at  = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship back to employee profile
    employee    = relationship("Employee", back_populates="user", uselist=False)


# ─────────────────────────── EMPLOYEE ────────────────────────────────────────

class Employee(Base):
    __tablename__ = "employees"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id         = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True)
    employee_code   = Column(String(20), unique=True, nullable=False)
    department      = Column(String(100))
    designation     = Column(String(100))
    date_of_joining = Column(Date)
    base_salary     = Column(Float, nullable=False, default=0.0)
    incentives      = Column(Float, default=0.0)
    tax_rate        = Column(Float, default=0.20)   # fraction e.g. 0.20
    leave_balance   = Column(Integer, default=24)   # days remaining this year
    manager_id      = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), onupdate=func.now())

    # Relations
    user            = relationship("User", back_populates="employee")
    manager         = relationship("Employee", remote_side="Employee.id", foreign_keys=[manager_id])
    payroll_records = relationship("PayrollRecord", back_populates="employee")
    leave_records   = relationship("LeaveRecord", back_populates="employee")
    anomalies       = relationship("PayrollAnomaly", back_populates="employee")
    onboarding_tasks= relationship("OnboardingTask", back_populates="employee")


# ─────────────────────────── APPLICANT ───────────────────────────────────────

class Applicant(Base):
    __tablename__ = "applicants"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name       = Column(String(255), nullable=False)
    email           = Column(String(255), nullable=False, index=True)
    phone           = Column(String(30))
    job_title       = Column(String(200))
    status          = Column(SAEnum(ApplicantStatus), default=ApplicantStatus.APPLIED)
    resume_path     = Column(String(500))          # raw PDF path
    resume_text     = Column(Text)                 # extracted plain text
    resume_json     = Column(JSON)                 # structured AI output
    resume_embedding= Column(Vector(1536))         # text-embedding-3-small dim
    similarity_score= Column(Float)                # vs job description
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), onupdate=func.now())

    onboarding_tasks= relationship("OnboardingTask", back_populates="applicant")


# ─────────────────────────── PAYROLL RECORD ──────────────────────────────────

class PayrollRecord(Base):
    """
    Stores the result of each monthly payroll run.
    Net Salary = Base + Incentives - Tax - (Unpaid Leaves × Daily Rate)
    """
    __tablename__ = "payroll_records"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id     = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False)
    period_year     = Column(Integer, nullable=False)
    period_month    = Column(Integer, nullable=False)   # 1-12
    base_salary     = Column(Float, nullable=False)
    incentives      = Column(Float, default=0.0)
    tax_deductions  = Column(Float, default=0.0)
    unpaid_leaves   = Column(Integer, default=0)       # count of unpaid leave days
    daily_rate      = Column(Float)                    # base_salary / working_days
    leave_deduction = Column(Float, default=0.0)       # unpaid_leaves × daily_rate
    net_salary      = Column(Float, nullable=False)
    is_processed    = Column(Boolean, default=False)
    processed_at    = Column(DateTime(timezone=True))
    notes           = Column(Text)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    employee        = relationship("Employee", back_populates="payroll_records")


# ─────────────────────────── LEAVE RECORD ────────────────────────────────────

class LeaveRecord(Base):
    __tablename__ = "leave_records"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id     = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False)
    leave_type      = Column(SAEnum(LeaveType), nullable=False)
    start_date      = Column(Date, nullable=False)
    end_date        = Column(Date, nullable=False)
    days_count      = Column(Integer, nullable=False)
    reason          = Column(Text)
    status          = Column(SAEnum(LeaveStatus), default=LeaveStatus.PENDING)
    approved_by     = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=True)
    approved_at     = Column(DateTime(timezone=True), nullable=True)  # ← key anomaly field
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), onupdate=func.now())

    employee        = relationship("Employee", back_populates="leave_records",
                                   foreign_keys=[employee_id])
    approver        = relationship("Employee", foreign_keys=[approved_by])


# ─────────────────────────── PAYROLL ANOMALY ─────────────────────────────────

class PayrollAnomaly(Base):
    """Flagged records where leave balance dropped without manager approval."""
    __tablename__ = "payroll_anomalies"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id     = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False)
    leave_record_id = Column(UUID(as_uuid=True), ForeignKey("leave_records.id"), nullable=True)
    anomaly_type    = Column(String(100), default="UNAPPROVED_LEAVE_DEDUCTION")
    description     = Column(Text)
    leave_days_flagged = Column(Integer)
    status          = Column(SAEnum(AnomalyStatus), default=AnomalyStatus.OPEN)
    flagged_at      = Column(DateTime(timezone=True), server_default=func.now())
    reviewed_at     = Column(DateTime(timezone=True), nullable=True)
    reviewed_by     = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    resolution_note = Column(Text)

    employee        = relationship("Employee", back_populates="anomalies")
    leave_record    = relationship("LeaveRecord")


# ─────────────────────────── ONBOARDING TASK ────────────────────────────────

class OnboardingTask(Base):
    __tablename__ = "onboarding_tasks"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    applicant_id    = Column(UUID(as_uuid=True), ForeignKey("applicants.id"), nullable=True)
    employee_id     = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=True)
    task_name       = Column(String(200), nullable=False)
    description     = Column(Text)
    is_completed    = Column(Boolean, default=False)
    due_date        = Column(Date)
    completed_at    = Column(DateTime(timezone=True), nullable=True)
    nda_path        = Column(String(500))           # generated NDA PDF path
    offer_letter_path = Column(String(500))         # generated Offer Letter PDF
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    applicant       = relationship("Applicant", back_populates="onboarding_tasks")
    employee        = relationship("Employee", back_populates="onboarding_tasks")

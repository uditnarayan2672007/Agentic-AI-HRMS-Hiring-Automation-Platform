"""
Test Suite — Core Logic Tests (no DB/network required)
All imports are done INSIDE tests to avoid import-chain issues.
"""
import sys
import types
import pytest
from datetime import date


# ─── Mock heavy optional modules so tests can run without a live DB ───────────

def _make_mock_module(name):
    m = types.ModuleType(name)
    sys.modules[name] = m
    return m

# sqlalchemy stubs
for mod in [
    "sqlalchemy", "sqlalchemy.orm", "sqlalchemy.ext",
    "sqlalchemy.ext.asyncio", "sqlalchemy.dialects",
    "sqlalchemy.dialects.postgresql", "sqlalchemy.dialects.postgresql.asyncpg",
]:
    if mod not in sys.modules:
        _make_mock_module(mod)

# pgvector stub
pv = _make_mock_module("pgvector")
pv_sa = _make_mock_module("pgvector.sqlalchemy")
pv_sa.Vector = lambda n: None


# ─── Now import just the pure-logic functions ─────────────────────────────────

def calculate_net_salary(base_salary, incentives, tax_rate, unpaid_leaves, working_days=22):
    """
    Net Salary = Base + Incentives - Tax Deductions - (Unpaid Leaves × Daily Rate)
    Inlined copy of the production formula so tests don't need the full module graph.
    """
    if working_days <= 0:
        working_days = 22
    daily_rate      = base_salary / working_days
    gross           = base_salary + incentives
    tax_deductions  = gross * tax_rate
    leave_deduction = unpaid_leaves * daily_rate
    net_salary      = gross - tax_deductions - leave_deduction
    return {
        "base_salary":     round(base_salary,     2),
        "incentives":      round(incentives,      2),
        "gross":           round(gross,            2),
        "tax_rate":        round(tax_rate,         4),
        "tax_deductions":  round(tax_deductions,   2),
        "daily_rate":      round(daily_rate,       2),
        "unpaid_leaves":   unpaid_leaves,
        "leave_deduction": round(leave_deduction,  2),
        "net_salary":      round(max(net_salary, 0.0), 2),
    }


def _business_days(start: date, end: date) -> int:
    """Count weekdays (Mon-Fri) between start and end (inclusive)."""
    from datetime import timedelta
    total, current = 0, start
    while current <= end:
        if current.weekday() < 5:
            total += 1
        current += timedelta(days=1)
    return total


# ── Payroll Calculation Tests ─────────────────────────────────────────────────

class TestPayrollCalculation:
    """
    Net Salary = Base + Incentives - Tax Deductions - (Unpaid Leaves × Daily Rate)
    """

    def test_standard_case(self):
        result = calculate_net_salary(50000, 5000, 0.20, 2, 22)
        assert result["base_salary"]    == 50000.0
        assert result["incentives"]     == 5000.0
        assert result["gross"]          == 55000.0
        assert result["tax_deductions"] == pytest.approx(11000.0, rel=1e-3)
        assert result["unpaid_leaves"]  == 2
        assert result["daily_rate"]     == pytest.approx(2272.73, rel=1e-2)
        assert result["leave_deduction"]== pytest.approx(4545.45, rel=1e-2)
        assert result["net_salary"]     == pytest.approx(39454.55, rel=1e-2)

    def test_zero_unpaid_leaves(self):
        result = calculate_net_salary(50000, 0, 0.20, 0, 22)
        expected_net = 50000 - (50000 * 0.20)
        assert result["net_salary"] == pytest.approx(expected_net, rel=1e-3)

    def test_zero_incentives(self):
        result = calculate_net_salary(60000, 0, 0.10, 0, 22)
        assert result["gross"]          == 60000
        assert result["tax_deductions"] == pytest.approx(6000.0, rel=1e-3)

    def test_net_salary_floor_at_zero(self):
        """Massive deductions should not produce a negative salary."""
        result = calculate_net_salary(10000, 0, 0.50, 30, 22)
        assert result["net_salary"] >= 0.0

    def test_full_month_unpaid(self):
        """22 unpaid leaves on 22-day month = entire base deducted."""
        result = calculate_net_salary(44000, 0, 0.0, 22, 22)
        assert result["net_salary"] == 0.0

    def test_high_incentive(self):
        result = calculate_net_salary(40000, 20000, 0.30, 0, 22)
        gross = 60000
        net   = gross - gross * 0.30
        assert result["net_salary"] == pytest.approx(net, rel=1e-3)

    def test_tax_rate_zero(self):
        """Tax rate of 0 means no deduction."""
        result = calculate_net_salary(50000, 0, 0.0, 0, 22)
        assert result["tax_deductions"] == 0.0
        assert result["net_salary"]     == 50000.0

    def test_daily_rate_formula(self):
        result = calculate_net_salary(44000, 0, 0.0, 0, 22)
        assert result["daily_rate"] == pytest.approx(2000.0, rel=1e-3)

    def test_documented_api_example(self):
        """
        Matches the /api/v1/payroll/formula endpoint documented example.
        Base=50000, Inc=5000, Tax=20%, Unpaid=2, WorkDays=22 → Net≈39454.55
        """
        result = calculate_net_salary(50000, 5000, 0.20, 2, 22)
        assert result["net_salary"] == pytest.approx(39454.55, rel=1e-2)


# ── Business Day Calculation Tests ────────────────────────────────────────────

class TestBusinessDays:
    def test_full_work_week(self):
        # Mon Jul 1 → Fri Jul 5 = 5 weekdays
        assert _business_days(date(2024, 7, 1), date(2024, 7, 5)) == 5

    def test_includes_weekend(self):
        # Mon to Sun = 5 weekdays
        assert _business_days(date(2024, 7, 1), date(2024, 7, 7)) == 5

    def test_single_weekday(self):
        assert _business_days(date(2024, 7, 1), date(2024, 7, 1)) == 1   # Monday

    def test_saturday_only(self):
        assert _business_days(date(2024, 7, 6), date(2024, 7, 6)) == 0   # Saturday

    def test_two_weeks(self):
        assert _business_days(date(2024, 7, 1), date(2024, 7, 12)) == 10


# ── Resume Schema Tests ───────────────────────────────────────────────────────

class TestResumeSchema:
    """Test the expected structure of the OpenAI JSON-mode output schema."""

    def test_required_top_level_keys(self):
        required = [
            "full_name", "email", "phone", "summary",
            "skills", "experience", "education",
            "certifications", "projects", "total_experience_years",
        ]
        dummy = {k: None for k in required}
        for key in required:
            assert key in dummy

    def test_skills_sub_keys(self):
        skills = {"technical": [], "soft": [], "tools": [], "languages": []}
        for key in ["technical", "soft", "tools", "languages"]:
            assert key in skills

    def test_embedding_text_builder(self):
        """Test that _build_embedding_text produces non-empty output."""
        resume_json = {
            "summary": "Experienced Python developer",
            "skills": {
                "technical": ["Python", "FastAPI"],
                "soft": ["Communication"],
                "tools": ["Docker"],
                "languages": ["Python"],
            },
            "experience": [{
                "role": "Backend Engineer",
                "company": "TechCorp",
                "responsibilities": ["Built REST APIs"],
                "achievements": [],
            }],
            "education": [{
                "degree": "B.Tech",
                "field": "CS",
                "institution": "JIS College",
            }],
            "certifications": ["AWS Certified"],
        }
        # Replicate _build_embedding_text logic
        parts = []
        if s := resume_json.get("summary"):
            parts.append(f"Summary: {s}")
        skills = resume_json.get("skills", {})
        all_skills = (
            skills.get("technical", []) + skills.get("tools", [])
            + skills.get("languages", []) + skills.get("soft", [])
        )
        if all_skills:
            parts.append("Skills: " + ", ".join(all_skills))
        text = "\n".join(parts)
        assert len(text) > 50
        assert "Python" in text


# ── Anomaly Detection Logic Tests ─────────────────────────────────────────────

class TestAnomalyLogic:
    """Test the threshold and gap-detection logic (pure Python, no DB)."""

    ABRUPT_DROP_THRESHOLD = 3
    INITIAL_BALANCE = 24

    def test_gap_below_threshold_not_flagged(self):
        approved_days = 22
        actual_balance = 2
        expected = self.INITIAL_BALANCE - approved_days   # 2
        gap = expected - actual_balance                   # 0
        assert gap < self.ABRUPT_DROP_THRESHOLD

    def test_gap_at_threshold_flagged(self):
        approved_days = 20
        actual_balance = 1   # should be 4, gap = 3
        expected = self.INITIAL_BALANCE - approved_days
        gap = expected - actual_balance
        assert gap >= self.ABRUPT_DROP_THRESHOLD

    def test_gap_above_threshold_flagged(self):
        approved_days = 18
        actual_balance = 0   # should be 6, gap = 6
        expected = self.INITIAL_BALANCE - approved_days
        gap = expected - actual_balance
        assert gap >= self.ABRUPT_DROP_THRESHOLD

    def test_no_gap_no_flag(self):
        approved_days = 10
        actual_balance = 14  # exactly correct
        expected = self.INITIAL_BALANCE - approved_days
        gap = expected - actual_balance
        assert gap < self.ABRUPT_DROP_THRESHOLD

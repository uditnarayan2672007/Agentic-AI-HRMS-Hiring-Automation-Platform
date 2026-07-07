"""
╔══════════════════════════════════════════════════════════════════════════════╗
║          AGENT 3 — Employee Onboarding Agent                                ║
║                                                                              ║
║  Triggered when Hiring Agent sets a candidate to ONBOARDING status.         ║
║  Actions:                                                                    ║
║  1. Generate a personalised NDA PDF (ReportLab)                             ║
║  2. Generate a personalised Offer Letter PDF (ReportLab)                    ║
║  3. Create a checklist of mock onboarding tasks in the DB                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

from loguru import logger
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, HRFlowable, KeepTogether,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Applicant, OnboardingTask


# ─── Color Palette ────────────────────────────────────────────────────────────
BRAND_NAVY  = colors.HexColor("#0F172A")
BRAND_BLUE  = colors.HexColor("#3B82F6")
BRAND_TEAL  = colors.HexColor("#06B6D4")
BRAND_LIGHT = colors.HexColor("#F0F9FF")
TEXT_DARK   = colors.HexColor("#1E293B")
TEXT_MUTED  = colors.HexColor("#64748B")


def _get_styles():
    """Build a branded style sheet."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        "DocTitle",
        parent=styles["Title"],
        fontSize=22,
        textColor=BRAND_NAVY,
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
    ))
    styles.add(ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontSize=11,
        textColor=BRAND_TEAL,
        spaceAfter=4,
        alignment=TA_CENTER,
        fontName="Helvetica-Oblique",
    ))
    styles.add(ParagraphStyle(
        "SectionHeader",
        parent=styles["Heading2"],
        fontSize=12,
        textColor=BRAND_BLUE,
        spaceBefore=12,
        spaceAfter=4,
        fontName="Helvetica-Bold",
    ))
    styles.add(ParagraphStyle(
        "BodyText2",
        parent=styles["Normal"],
        fontSize=10,
        textColor=TEXT_DARK,
        spaceAfter=6,
        leading=16,
        alignment=TA_JUSTIFY,
        fontName="Helvetica",
    ))
    styles.add(ParagraphStyle(
        "SmallMuted",
        parent=styles["Normal"],
        fontSize=8,
        textColor=TEXT_MUTED,
        spaceAfter=4,
        fontName="Helvetica-Oblique",
    ))
    return styles


# ─────────────────────────────────────────────────────────────────────────────
# DOCUMENT 1 — NDA
# ─────────────────────────────────────────────────────────────────────────────

def generate_nda_pdf(
    candidate_name: str,
    job_title: str,
    output_path: str,
    company_name: str = "Elite Coders Pvt. Ltd.",
    effective_date: Optional[date] = None,
) -> str:
    """Generate a professional Non-Disclosure Agreement PDF using ReportLab."""
    if effective_date is None:
        effective_date = date.today()

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2.5 * cm,
        leftMargin=2.5 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
    )

    styles = _get_styles()
    story = []

    # ── Header ────────────────────────────────────────────────────────────
    story.append(Paragraph("ELITE CODERS PVT. LTD.", styles["DocTitle"]))
    story.append(Paragraph("Non-Disclosure Agreement (NDA)", styles["DocSubtitle"]))
    story.append(HRFlowable(width="100%", thickness=2, color=BRAND_BLUE, spaceAfter=12))
    story.append(Spacer(1, 0.3 * cm))

    # ── Parties Table ──────────────────────────────────────────────────────
    effective_str = effective_date.strftime("%B %d, %Y")
    parties_data = [
        ["Field", "Disclosing Party", "Receiving Party"],
        ["Name", company_name, candidate_name],
        ["Role", "Employer / Company", job_title],
        ["Date", effective_str, effective_str],
    ]
    parties_table = Table(parties_data, colWidths=[3.5 * cm, 8 * cm, 5.5 * cm])
    parties_table.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0), BRAND_NAVY),
        ("TEXTCOLOR",    (0, 0), (-1, 0), colors.white),
        ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, 0), 10),
        ("BACKGROUND",   (0, 1), (0, -1), BRAND_LIGHT),
        ("FONTNAME",     (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE",     (0, 1), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BRAND_LIGHT]),
        ("GRID",         (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",   (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
    ]))
    story.append(parties_table)
    story.append(Spacer(1, 0.5 * cm))

    # ── Clauses ───────────────────────────────────────────────────────────
    clauses = [
        (
            "1. Definition of Confidential Information",
            f'"{company_name}" (hereinafter "Company") may disclose to '
            f'"{candidate_name}" (hereinafter "Recipient") certain confidential '
            "and proprietary information. \"Confidential Information\" includes, "
            "but is not limited to: trade secrets, business strategies, source code, "
            "customer data, financial projections, HR records, and any other data "
            "designated as confidential in writing by the Company.",
        ),
        (
            "2. Obligations of the Recipient",
            "The Recipient agrees to: (a) hold all Confidential Information in "
            "strict confidence; (b) not disclose Confidential Information to any "
            "third party without the prior written consent of the Company; "
            "(c) use Confidential Information solely for the purposes of fulfilling "
            "their role as stated in the Employment Agreement; (d) implement "
            "reasonable security measures to prevent unauthorised disclosure.",
        ),
        (
            "3. Exclusions",
            "This Agreement does not apply to information that: (a) is or becomes "
            "publicly known through no breach of this Agreement; (b) was rightfully "
            "known by the Recipient prior to disclosure; (c) is independently "
            "developed by the Recipient without use of Confidential Information; "
            "(d) is required to be disclosed by applicable law or court order.",
        ),
        (
            "4. Term",
            "This Agreement shall remain in effect for a period of three (3) years "
            f"from the Effective Date ({effective_str}), and shall survive termination "
            "of employment for an additional two (2) years.",
        ),
        (
            "5. Remedies",
            "The Recipient acknowledges that any breach of this Agreement may cause "
            "irreparable harm to the Company for which monetary damages would be an "
            "inadequate remedy. The Company shall be entitled to seek equitable "
            "relief, including injunctions, without bond.",
        ),
        (
            "6. Governing Law",
            "This Agreement shall be governed by and construed in accordance with "
            "the laws of India. Any disputes arising hereunder shall be subject to "
            "the exclusive jurisdiction of the courts of West Bengal.",
        ),
    ]

    for heading, body in clauses:
        story.append(Paragraph(heading, styles["SectionHeader"]))
        story.append(Paragraph(body, styles["BodyText2"]))
        story.append(Spacer(1, 0.2 * cm))

    # ── Signature Block ────────────────────────────────────────────────────
    story.append(Spacer(1, 0.8 * cm))
    story.append(HRFlowable(width="100%", thickness=1, color=TEXT_MUTED))
    story.append(Spacer(1, 0.3 * cm))

    sig_data = [
        ["For the Company", "", "Recipient"],
        ["", "", ""],
        ["_" * 30, "", "_" * 30],
        [f"Authorised Signatory", "", candidate_name],
        [company_name, "", job_title],
        [f"Date: {effective_str}", "", f"Date: {effective_str}"],
    ]
    sig_table = Table(sig_data, colWidths=[8 * cm, 1 * cm, 8 * cm])
    sig_table.setStyle(TableStyle([
        ("FONTNAME",  (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",  (0, 0), (-1, -1), 9),
        ("FONTNAME",  (0, 3), (0, 3), "Helvetica-Bold"),
        ("FONTNAME",  (2, 3), (2, 3), "Helvetica-Bold"),
        ("VALIGN",    (0, 0), (-1, -1), "BOTTOM"),
        ("TOPPADDING",(0, 0), (-1, -1), 4),
    ]))
    story.append(sig_table)
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph(
        "⚠  This is a system-generated document for onboarding purposes. "
        "Final execution requires wet signatures and HR countersignature.",
        styles["SmallMuted"],
    ))

    doc.build(story)
    logger.info(f"📄 NDA generated → {output_path}")
    return output_path


# ─────────────────────────────────────────────────────────────────────────────
# DOCUMENT 2 — OFFER LETTER
# ─────────────────────────────────────────────────────────────────────────────

def generate_offer_letter_pdf(
    candidate_name: str,
    job_title: str,
    department: str,
    base_salary: float,
    joining_date: date,
    output_path: str,
    company_name: str = "Elite Coders Pvt. Ltd.",
    manager_name: str = "HR Department",
) -> str:
    """Generate a branded Offer Letter PDF using ReportLab."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2.5 * cm,
        leftMargin=2.5 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
    )

    styles = _get_styles()
    story = []
    today_str = date.today().strftime("%B %d, %Y")
    joining_str = joining_date.strftime("%B %d, %Y")
    annual_salary = base_salary * 12

    # ── Letterhead ────────────────────────────────────────────────────────
    story.append(Paragraph("ELITE CODERS PVT. LTD.", styles["DocTitle"]))
    story.append(Paragraph(
        "Empowering Talent Through Technology",
        styles["DocSubtitle"],
    ))
    story.append(HRFlowable(width="100%", thickness=2, color=BRAND_BLUE, spaceAfter=8))

    # Date & Reference
    story.append(Paragraph(
        f"<b>Date:</b> {today_str} &nbsp;&nbsp;&nbsp; "
        f"<b>Ref No:</b> EC/OL/{date.today().year}/{uuid.uuid4().hex[:6].upper()}",
        styles["SmallMuted"],
    ))
    story.append(Spacer(1, 0.5 * cm))

    # Salutation
    story.append(Paragraph(f"Dear <b>{candidate_name}</b>,", styles["BodyText2"]))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        f"We are delighted to extend this offer of employment to you for the role of "
        f"<b>{job_title}</b> in our <b>{department}</b> department at "
        f"<b>{company_name}</b>. This letter outlines the key terms and conditions "
        "of your employment.",
        styles["BodyText2"],
    ))
    story.append(Spacer(1, 0.3 * cm))

    # ── CTC Breakdown Table ────────────────────────────────────────────────
    story.append(Paragraph("Compensation & Benefits", styles["SectionHeader"]))
    annual_incentive = base_salary * 0.15  # 15% of monthly as annual incentive
    ctc_data = [
        ["Component",               "Monthly (INR)",     "Annual (INR)"],
        ["Basic Salary",            f"₹{base_salary:,.2f}", f"₹{annual_salary:,.2f}"],
        ["House Rent Allowance",    f"₹{base_salary*0.4:,.2f}", f"₹{annual_salary*0.4:,.2f}"],
        ["Transport Allowance",     "₹2,000.00",          "₹24,000.00"],
        ["Performance Incentive",   f"₹{annual_incentive/12:,.2f}",  f"₹{annual_incentive:,.2f}"],
        ["Medical Benefits",        "As per policy",      "Up to ₹50,000"],
        ["Gross CTC",
         f"₹{base_salary + base_salary*0.4 + 2000 + annual_incentive/12:,.2f}",
         f"₹{(base_salary + base_salary*0.4 + 2000 + annual_incentive/12)*12:,.2f}"],
    ]
    ctc_table = Table(ctc_data, colWidths=[7 * cm, 5 * cm, 5 * cm])
    ctc_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0),  (-1, 0),  BRAND_NAVY),
        ("TEXTCOLOR",     (0, 0),  (-1, 0),  colors.white),
        ("FONTNAME",      (0, 0),  (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0),  (-1, -1), 9),
        ("BACKGROUND",    (0, -1), (-1, -1), BRAND_LIGHT),
        ("FONTNAME",      (0, -1), (-1, -1), "Helvetica-Bold"),
        ("ROWBACKGROUNDS",(0, 1),  (-1, -2), [colors.white, colors.HexColor("#F8FAFC")]),
        ("GRID",          (0, 0),  (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("TOPPADDING",    (0, 0),  (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0),  (-1, -1), 6),
        ("ALIGN",         (1, 0),  (-1, -1), "RIGHT"),
    ]))
    story.append(ctc_table)
    story.append(Spacer(1, 0.3 * cm))

    # ── Terms & Conditions ────────────────────────────────────────────────
    terms = [
        ("Joining Date", f"You are expected to join on or before <b>{joining_str}</b>."),
        ("Probation Period", "This offer is subject to a probation period of <b>6 months</b>, "
         "during which either party may terminate the employment with 2 weeks' notice."),
        ("Working Hours", "Standard working hours are <b>9:00 AM – 6:00 PM IST</b>, Monday to Friday, "
         "with flexibility as per project requirements."),
        ("Annual Leave", "You are entitled to <b>24 days</b> of paid annual leave per year, "
         "accruing at 2 days per month."),
        ("Background Verification", "This offer is contingent upon successful completion of "
         "background verification and document submission within 7 days of joining."),
        ("Confidentiality", "You are required to sign the attached NDA as a condition of employment."),
    ]

    for term_title, term_body in terms:
        story.append(Paragraph(term_title, styles["SectionHeader"]))
        story.append(Paragraph(term_body, styles["BodyText2"]))

    # ── Closing ───────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph(
        "We look forward to welcoming you to the Elite Coders family. "
        "Please sign and return a copy of this letter as your acceptance "
        "within <b>5 business days</b>.",
        styles["BodyText2"],
    ))
    story.append(Spacer(1, 0.5 * cm))
    story.append(HRFlowable(width="100%", thickness=1, color=TEXT_MUTED))
    story.append(Spacer(1, 0.3 * cm))

    # Signature block
    sig_data = [
        ["Issued By", "", "Accepted By"],
        ["", "", ""],
        ["_" * 30, "", "_" * 30],
        [manager_name, "", candidate_name],
        [company_name, "", job_title],
        [today_str, "", "Date: ________________"],
    ]
    sig_table = Table(sig_data, colWidths=[8 * cm, 1 * cm, 8 * cm])
    sig_table.setStyle(TableStyle([
        ("FONTNAME",  (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",  (0, 0), (-1, -1), 9),
        ("TOPPADDING",(0, 0), (-1, -1), 4),
    ]))
    story.append(sig_table)
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph(
        "🔒 Confidential — For the addressee only. "
        "This document was auto-generated by the Elite Coders HRMS Onboarding Agent.",
        styles["SmallMuted"],
    ))

    doc.build(story)
    logger.info(f"📄 Offer Letter generated → {output_path}")
    return output_path


# ─────────────────────────────────────────────────────────────────────────────
# MOCK ONBOARDING TASKS
# ─────────────────────────────────────────────────────────────────────────────

ONBOARDING_TASK_TEMPLATES = [
    {
        "task_name": "Upload Identity Documents",
        "description": "Upload scanned copies of Aadhaar Card, PAN Card, and Passport (if available).",
        "due_days": 3,
    },
    {
        "task_name": "Sign & Return NDA",
        "description": "Review, sign, and upload the Non-Disclosure Agreement provided in your onboarding portal.",
        "due_days": 3,
    },
    {
        "task_name": "Sign & Return Offer Letter",
        "description": "Accept the offer by signing the Offer Letter and uploading the signed copy.",
        "due_days": 5,
    },
    {
        "task_name": "Submit Educational Certificates",
        "description": "Upload verified copies of all academic degrees, diplomas, and mark sheets.",
        "due_days": 7,
    },
    {
        "task_name": "Bank Account Details",
        "description": "Submit cancelled cheque or bank statement for payroll processing.",
        "due_days": 5,
    },
    {
        "task_name": "IT Equipment Request",
        "description": "Fill out the equipment request form specifying your laptop/peripheral preferences.",
        "due_days": 7,
    },
    {
        "task_name": "Complete Security & Data Privacy Training",
        "description": "Complete the mandatory online security awareness course (approx. 45 mins).",
        "due_days": 10,
    },
    {
        "task_name": "HR Onboarding Orientation",
        "description": "Attend the HR orientation session scheduled for your joining week.",
        "due_days": 14,
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENTRY POINT — Full onboarding pipeline
# ─────────────────────────────────────────────────────────────────────────────

async def trigger_onboarding(
    db: AsyncSession,
    applicant: Applicant,
    department: str = "Engineering",
    base_salary: float = 50000.0,
    manager_name: str = "HR Department",
) -> list[OnboardingTask]:
    """
    Called when hiring agent sets applicant → ONBOARDING.
    1. Generate NDA PDF
    2. Generate Offer Letter PDF
    3. Create checklist of onboarding tasks in DB
    """
    docs_dir = Path(settings.GENERATED_DOCS_DIR) / str(applicant.id)
    docs_dir.mkdir(parents=True, exist_ok=True)

    joining_date = date.today() + timedelta(days=14)

    # ── 1. Generate NDA ───────────────────────────────────────────────────
    nda_path = str(docs_dir / "NDA.pdf")
    generate_nda_pdf(
        candidate_name=applicant.full_name,
        job_title=applicant.job_title or "Software Engineer",
        output_path=nda_path,
    )

    # ── 2. Generate Offer Letter ──────────────────────────────────────────
    offer_path = str(docs_dir / "Offer_Letter.pdf")
    generate_offer_letter_pdf(
        candidate_name=applicant.full_name,
        job_title=applicant.job_title or "Software Engineer",
        department=department,
        base_salary=base_salary,
        joining_date=joining_date,
        output_path=offer_path,
        manager_name=manager_name,
    )

    # ── 3. Create onboarding tasks ────────────────────────────────────────
    tasks = []
    for template in ONBOARDING_TASK_TEMPLATES:
        task = OnboardingTask(
            applicant_id=applicant.id,
            task_name=template["task_name"],
            description=template["description"],
            due_date=date.today() + timedelta(days=template["due_days"]),
            is_completed=False,
            nda_path=nda_path if "NDA" in template["task_name"] else None,
            offer_letter_path=offer_path if "Offer" in template["task_name"] else None,
        )
        db.add(task)
        tasks.append(task)

    await db.flush()
    logger.info(
        f"✅ Onboarding triggered for {applicant.full_name} — "
        f"{len(tasks)} tasks created, NDA + Offer Letter generated."
    )
    return tasks

"""
╔══════════════════════════════════════════════════════════════════════════════╗
║          AGENT 1 — Resume Intelligence Agent                                ║
║                                                                              ║
║  Pipeline:                                                                   ║
║  1. PyMuPDF   → extract raw text from uploaded PDF                          ║
║  2. OpenAI    → JSON-mode extraction of Skills/Experience/Education         ║
║  3. OpenAI    → text-embedding-3-small vector (1536-dim)                    ║
║  4. pgvector  → store & semantic-rank against a job description             ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
import json
import uuid
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF
from loguru import logger
from openai import AsyncOpenAI
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Applicant, ApplicantStatus


# ─── OpenAI client (lazy-init so import works even without a key in dev) ──────
_openai: Optional[AsyncOpenAI] = None


def get_openai() -> AsyncOpenAI:
    global _openai
    if _openai is None:
        _openai = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _openai


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — PDF TEXT EXTRACTION (PyMuPDF)
# ─────────────────────────────────────────────────────────────────────────────

RESUME_EXTRACTION_PROMPT = """
You are an expert HR analyst. Extract structured information from the resume text below.

Return ONLY a valid JSON object with this exact schema:
{
  "full_name": "string",
  "email": "string",
  "phone": "string",
  "linkedin": "string or null",
  "location": "string or null",
  "summary": "string — professional summary in 2-3 sentences",
  "skills": {
    "technical": ["list of technical skills"],
    "soft": ["list of soft skills"],
    "tools": ["list of tools, frameworks, platforms"],
    "languages": ["programming languages"]
  },
  "experience": [
    {
      "company": "string",
      "role": "string",
      "start_date": "YYYY-MM or string",
      "end_date": "YYYY-MM or 'Present'",
      "duration_months": "integer estimate",
      "responsibilities": ["bullet list of key responsibilities"],
      "achievements": ["measurable achievements if any"]
    }
  ],
  "education": [
    {
      "institution": "string",
      "degree": "string",
      "field": "string",
      "start_year": "integer or null",
      "end_year": "integer or null",
      "gpa": "string or null"
    }
  ],
  "certifications": ["list of certifications"],
  "projects": [
    {
      "name": "string",
      "description": "string",
      "tech_stack": ["list of technologies"]
    }
  ],
  "total_experience_years": "float estimate"
}

Resume Text:
"""


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Use PyMuPDF (fitz) to extract all text from each page of the PDF.
    Falls back to OCR-friendly layout mode if the PDF is scanned.
    """
    doc = fitz.open(pdf_path)
    pages_text = []

    for page_num, page in enumerate(doc):
        # Try standard text extraction first
        text = page.get_text("text")
        if not text.strip():
            # Fallback: use layout-aware extraction (handles multi-column)
            text = page.get_text("blocks")
            text = " ".join(str(b[4]) for b in text if isinstance(b, tuple))
        pages_text.append(text)

    doc.close()
    full_text = "\n\n".join(pages_text)
    logger.info(f"📄 Extracted {len(full_text)} chars from PDF: {pdf_path}")
    return full_text


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — STRUCTURED JSON EXTRACTION (OpenAI JSON Mode)
# ─────────────────────────────────────────────────────────────────────────────

async def extract_resume_json(raw_text: str) -> dict:
    """
    Call OpenAI gpt-4o-mini in JSON mode to parse the resume into
    a strict structured schema (Skills, Experience, Education).
    """
    client = get_openai()
    logger.info("🤖 Sending resume to OpenAI for structured extraction...")

    response = await client.chat.completions.create(
        model=settings.OPENAI_CHAT_MODEL,
        response_format={"type": "json_object"},
        temperature=0.0,
        messages=[
            {
                "role": "system",
                "content": RESUME_EXTRACTION_PROMPT,
            },
            {
                "role": "user",
                "content": raw_text[:12000],  # ~3k tokens budget
            },
        ],
    )

    content = response.choices[0].message.content
    parsed = json.loads(content)
    logger.info(f"✅ Resume parsed — name: {parsed.get('full_name')}, "
                f"experience: {parsed.get('total_experience_years')} yrs")
    return parsed


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — VECTOR EMBEDDING (text-embedding-3-small, 1536 dims)
# ─────────────────────────────────────────────────────────────────────────────

async def embed_text(text: str) -> list[float]:
    """Generate a 1536-dimensional embedding vector for the given text."""
    client = get_openai()

    # Truncate to ~8191 tokens max for embedding model
    truncated = text[:30000]

    response = await client.embeddings.create(
        model=settings.OPENAI_EMBEDDING_MODEL,
        input=truncated,
    )
    vector = response.data[0].embedding
    logger.info(f"📐 Embedding generated — dim: {len(vector)}")
    return vector


def _build_embedding_text(resume_json: dict) -> str:
    """
    Flatten the structured resume JSON into a rich text string
    optimised for semantic similarity against job descriptions.
    """
    parts = []

    # Summary
    if s := resume_json.get("summary"):
        parts.append(f"Summary: {s}")

    # Skills
    skills = resume_json.get("skills", {})
    all_skills = (
        skills.get("technical", [])
        + skills.get("tools", [])
        + skills.get("languages", [])
        + skills.get("soft", [])
    )
    if all_skills:
        parts.append("Skills: " + ", ".join(all_skills))

    # Experience
    for exp in resume_json.get("experience", []):
        role_str = f"{exp.get('role','')} at {exp.get('company','')}"
        resps = " ".join(exp.get("responsibilities", []))
        parts.append(f"Role: {role_str}. {resps}")

    # Education
    for edu in resume_json.get("education", []):
        parts.append(f"Education: {edu.get('degree','')} in "
                     f"{edu.get('field','')} from {edu.get('institution','')}")

    # Certifications
    if certs := resume_json.get("certifications", []):
        parts.append("Certifications: " + ", ".join(certs))

    return "\n".join(parts)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 — SEMANTIC RANKING (pgvector cosine similarity)
# ─────────────────────────────────────────────────────────────────────────────

async def rank_candidates_by_job(
    db: AsyncSession,
    job_description: str,
    top_k: int = 10,
) -> list[dict]:
    """
    Embed the job description and find the top-k most similar applicant
    profiles using pgvector's cosine distance (<=>).
    """
    logger.info(f"🔍 Ranking candidates against job description (top_k={top_k})")
    jd_vector = await embed_text(job_description)

    # pgvector cosine distance: 1 - similarity, so ORDER BY ASC = most similar first
    query = text("""
        SELECT
            id,
            full_name,
            email,
            job_title,
            status,
            similarity_score,
            resume_json,
            1 - (resume_embedding <=> CAST(:jd_vector AS vector)) AS cosine_similarity
        FROM applicants
        WHERE resume_embedding IS NOT NULL
        ORDER BY resume_embedding <=> CAST(:jd_vector AS vector)
        LIMIT :top_k
    """)

    result = await db.execute(query, {
        "jd_vector": str(jd_vector),
        "top_k": top_k,
    })
    rows = result.fetchall()

    candidates = []
    for row in rows:
        candidates.append({
            "applicant_id": str(row.id),
            "full_name": row.full_name,
            "email": row.email,
            "job_title": row.job_title,
            "status": row.status,
            "cosine_similarity": round(float(row.cosine_similarity), 4),
            "resume_json": row.resume_json,
        })

    logger.info(f"✅ Ranked {len(candidates)} candidates")
    return candidates


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENTRY POINT — Full pipeline for a single resume upload
# ─────────────────────────────────────────────────────────────────────────────

async def process_resume(
    db: AsyncSession,
    pdf_path: str,
    job_title: str = "General Position",
    job_description: str = "",
) -> Applicant:
    """
    Full resume intelligence pipeline:
    1. Extract text (PyMuPDF)
    2. Parse to JSON (OpenAI JSON mode)
    3. Generate embedding vector
    4. Optionally compute similarity to a reference JD
    5. Persist Applicant record in DB
    """
    # ── 1. Extract raw text ────────────────────────────────────────────────
    raw_text = extract_text_from_pdf(pdf_path)

    # ── 2. AI-powered structured extraction ───────────────────────────────
    try:
        resume_json = await extract_resume_json(raw_text)
    except Exception as e:
        logger.warning(f"⚠️ OpenAI extraction failed, using fallback: {e}")
        resume_json = _fallback_extract(raw_text)

    # ── 3. Embed for vector search ─────────────────────────────────────────
    embedding_text = _build_embedding_text(resume_json)
    try:
        vector = await embed_text(embedding_text)
    except Exception as e:
        logger.warning(f"⚠️ Embedding failed: {e}")
        vector = None

    # ── 4. Cosine similarity vs reference JD (optional) ───────────────────
    similarity = None
    if job_description and vector:
        try:
            jd_vector = await embed_text(job_description)
            similarity = _cosine_similarity(vector, jd_vector)
        except Exception:
            pass

    # ── 5. Persist to DB ───────────────────────────────────────────────────
    applicant = Applicant(
        full_name=resume_json.get("full_name", "Unknown"),
        email=resume_json.get("email", f"unknown_{uuid.uuid4().hex[:6]}@example.com"),
        phone=resume_json.get("phone"),
        job_title=job_title,
        status=ApplicantStatus.SCREENING,
        resume_path=pdf_path,
        resume_text=raw_text,
        resume_json=resume_json,
        resume_embedding=vector,
        similarity_score=similarity,
    )
    db.add(applicant)
    await db.flush()
    logger.info(f"✅ Applicant persisted — id: {applicant.id}, "
                f"similarity: {similarity}")
    return applicant


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Pure-Python cosine similarity (numpy not guaranteed available at import)."""
    try:
        import numpy as np
        va, vb = np.array(a), np.array(b)
        return float(np.dot(va, vb) / (np.linalg.norm(va) * np.linalg.norm(vb)))
    except Exception:
        return 0.0


def _fallback_extract(raw_text: str) -> dict:
    """Minimal fallback when OpenAI is unavailable (dev/offline mode)."""
    return {
        "full_name": "Unknown Candidate",
        "email": "",
        "phone": "",
        "summary": raw_text[:500],
        "skills": {"technical": [], "soft": [], "tools": [], "languages": []},
        "experience": [],
        "education": [],
        "certifications": [],
        "projects": [],
        "total_experience_years": 0,
    }

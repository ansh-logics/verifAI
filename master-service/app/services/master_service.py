from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from app.config import get_settings
from core_engine.service import score_existing_analysis
from app.services.cloudinary_service import upload_resume_to_cloudinary
from app.services.downstream import (
    DEFAULT_HEADERS,
    call_coding_analyzer,
    call_marksheet_analyzer,
    call_resume_analyzer,
)

logger = logging.getLogger(__name__)


def normalize_skills(skills: list[Any] | None) -> list[str]:
    if not isinstance(skills, list):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for raw in skills:
        if not isinstance(raw, str):
            continue
        normalized = raw.strip().lower()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        out.append(normalized)
    return out


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        clean = value.strip().replace(",", ".")
        try:
            return float(clean)
        except ValueError:
            return None
    return None


def _clamp_score(value: float | None) -> float:
    if value is None:
        return 0.0
    return max(0.0, min(100.0, float(value)))


def has_candidate_basic_details(marksheet: dict[str, Any] | None) -> bool:
    if not isinstance(marksheet, dict):
        return False
    candidate = marksheet.get("candidate")
    if not isinstance(candidate, dict):
        return False

    name = str(candidate.get("name") or "").strip()
    roll_no = str(candidate.get("roll_no") or "").strip()
    enrollment_no = str(candidate.get("enrollment_no") or "").strip()
    class_name = str(candidate.get("class_name") or "").strip()

    has_identity = bool(roll_no or enrollment_no)
    return bool(name and class_name and has_identity)


def normalize_master_output(
    *,
    resume: dict[str, Any],
    coding: dict[str, Any],
    marksheet: dict[str, Any],
    github_username: str,
    leetcode_username: str,
    resume_url: str | None,
) -> dict[str, Any]:
    marksheet_cgpa = _safe_float(marksheet.get("cgpa_computed"))
    resume_cgpa = _safe_float(resume.get("cgpa"))
    final_cgpa = marksheet_cgpa if marksheet_cgpa is not None else resume_cgpa
    engine_scores = score_existing_analysis(
        resume=resume,
        coding=coding,
        marksheet=marksheet,
    )
    coding_score = _clamp_score(engine_scores["coding_score"])
    academic_score = _clamp_score(engine_scores["academic_score_percent"])
    overall_score = _clamp_score(engine_scores["final_score"])

    github_data = coding.get("github") if isinstance(coding.get("github"), dict) else {}
    leetcode_data = coding.get("leetcode") if isinstance(coding.get("leetcode"), dict) else {}
    coding_persona = str(coding.get("coding_persona") or coding.get("coding_level") or "").strip()
    cand = marksheet.get("candidate") if isinstance(marksheet.get("candidate"), dict) else {}
    roll_from_sheet = str(cand.get("roll_no") or "").strip().upper()
    profile = {
        "student": {
            "name": str(resume.get("name") or cand.get("name") or "").strip(),
            "email": str(resume.get("email") or "").strip().lower(),
            "roll_no": roll_from_sheet or None,
            "phone": str(resume.get("phone") or "").strip(),
            "branch": str(resume.get("branch") or "").strip(),
            "cgpa": final_cgpa,
            "gender": "other",
            "cgpa_verified": marksheet_cgpa is not None,
        },
        "skills": normalize_skills(resume.get("skills")),
        "coding": {
            "persona": coding_persona,
            "score": coding_score,
            "github": {**github_data, "username": github_username, "score": engine_scores["github_score"]},
            "leetcode": {**leetcode_data, "username": leetcode_username, "score": engine_scores["leetcode_score"]},
        },
        "academics": {
            "cgpa": final_cgpa,
            "verified": marksheet_cgpa is not None,
            "score": academic_score,
        },
        "overall_score": overall_score,
        "resume_data": resume,
        "academic_data": marksheet,
        "github_data": github_data,
        "leetcode_data": leetcode_data,
        "resume_url": resume_url,
    }
    return profile


async def analyze_student_profile(
    *,
    resume_file: bytes,
    resume_filename: str,
    resume_content_type: str | None,
    marksheet_file: bytes,
    marksheet_filename: str,
    marksheet_content_type: str | None,
    branch: str,
    github: str,
    leetcode: str,
) -> dict[str, Any]:
    settings = get_settings()
    logger.info("Starting profile analysis for github=%s leetcode=%s", github, leetcode)

    async with httpx.AsyncClient(headers=DEFAULT_HEADERS) as client:
        resume_task = call_resume_analyzer(
            settings=settings,
            client=client,
            file_bytes=resume_file,
            filename=resume_filename,
            content_type=resume_content_type,
        )
        coding_task = call_coding_analyzer(
            settings=settings,
            client=client,
            payload={
                "github_username": github,
                "leetcode_username": leetcode,
                "codeforces_username": None,
            },
        )
        marksheet_task = call_marksheet_analyzer(
            settings=settings,
            client=client,
            file_bytes=marksheet_file,
            filename=marksheet_filename,
            content_type=marksheet_content_type,
        )

        (resume_data, resume_error), (coding_data, coding_error), (marksheet_data, marksheet_error) = await asyncio.gather(
            resume_task,
            coding_task,
            marksheet_task,
        )

    if resume_error or resume_data is None:
        raise ValueError(f"Resume analyzer failed: {resume_error or 'unknown error'}")
    if coding_error or coding_data is None:
        raise ValueError(f"Coding analyzer failed: {coding_error or 'unknown error'}")
    if marksheet_error or marksheet_data is None:
        raise ValueError(f"Marksheet analyzer failed: {marksheet_error or 'unknown error'}")
    if not has_candidate_basic_details(marksheet_data):
        raise ValueError(
            "Invalid marksheet: basic candidate details are missing (name, class, and roll/enrollment)."
        )

    resume_data["branch"] = branch.strip()
    resume_url = await upload_resume_to_cloudinary(
        settings=settings,
        resume_bytes=resume_file,
        filename=resume_filename,
    )
    normalized = normalize_master_output(
        resume=resume_data,
        coding=coding_data,
        marksheet=marksheet_data,
        github_username=github.strip(),
        leetcode_username=leetcode.strip(),
        resume_url=resume_url,
    )
    logger.info("Completed profile analysis for email=%s", normalized["student"]["email"])
    return normalized


async def analyze_student_profile_incremental(
    *,
    existing_resume_data: dict[str, Any],
    existing_marksheet_data: dict[str, Any],
    existing_coding_data: dict[str, Any],
    resume_file: bytes | None,
    resume_filename: str | None,
    resume_content_type: str | None,
    marksheet_file: bytes | None,
    marksheet_filename: str | None,
    marksheet_content_type: str | None,
    resume_changed: bool,
    marksheet_changed: bool,
    coding_changed: bool,
    branch: str,
    github: str,
    leetcode: str,
    existing_resume_url: str | None,
) -> dict[str, Any]:
    settings = get_settings()

    resume_data = dict(existing_resume_data or {})
    marksheet_data = dict(existing_marksheet_data or {})
    coding_data = {
        "github": dict((existing_coding_data or {}).get("github") or {}),
        "leetcode": dict((existing_coding_data or {}).get("leetcode") or {}),
        "scores": {"overall_score": (existing_coding_data or {}).get("score", 0)},
        "coding_persona": (existing_coding_data or {}).get("persona", ""),
    }
    resume_url = existing_resume_url

    async with httpx.AsyncClient(headers=DEFAULT_HEADERS) as client:
        if resume_changed:
            if not resume_file or not resume_filename:
                raise ValueError("Resume file is required when resume_changed is true.")
            r_data, r_err = await call_resume_analyzer(
                settings=settings,
                client=client,
                file_bytes=resume_file,
                filename=resume_filename,
                content_type=resume_content_type,
            )
            if r_err or r_data is None:
                raise ValueError(f"Resume analyzer failed: {r_err or 'unknown error'}")
            r_data["branch"] = branch.strip()
            resume_data = r_data
            resume_url = await upload_resume_to_cloudinary(
                settings=settings,
                resume_bytes=resume_file,
                filename=resume_filename,
            )

        if marksheet_changed:
            if not marksheet_file or not marksheet_filename:
                raise ValueError("Marksheet file is required when marksheet_changed is true.")
            m_data, m_err = await call_marksheet_analyzer(
                settings=settings,
                client=client,
                file_bytes=marksheet_file,
                filename=marksheet_filename,
                content_type=marksheet_content_type,
            )
            if m_err or m_data is None:
                raise ValueError(f"Marksheet analyzer failed: {m_err or 'unknown error'}")
            if not has_candidate_basic_details(m_data):
                raise ValueError(
                    "Invalid marksheet: basic candidate details are missing (name, class, and roll/enrollment)."
                )
            marksheet_data = m_data

        if coding_changed:
            c_data, c_err = await call_coding_analyzer(
                settings=settings,
                client=client,
                payload={
                    "github_username": github,
                    "leetcode_username": leetcode,
                    "codeforces_username": None,
                },
            )
            if c_err or c_data is None:
                raise ValueError(f"Coding analyzer failed: {c_err or 'unknown error'}")
            coding_data = c_data

    if not resume_data:
        raise ValueError("No resume data available. Upload resume at least once.")
    if not marksheet_data:
        raise ValueError("No marksheet data available. Upload marksheet at least once.")

    if "branch" not in resume_data or resume_changed:
        resume_data["branch"] = branch.strip()

    return normalize_master_output(
        resume=resume_data,
        coding=coding_data,
        marksheet=marksheet_data,
        github_username=github.strip(),
        leetcode_username=leetcode.strip(),
        resume_url=resume_url,
    )

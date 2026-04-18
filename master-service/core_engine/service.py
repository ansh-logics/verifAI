from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx

from core_engine.processor import process_candidate
from core_engine.utils import as_dict, clamp, round_score


def _content_type_for(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        return "application/pdf"
    if suffix == ".docx":
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    return "application/octet-stream"


def _score_to_percent(score: float, max_score: float) -> float:
    if max_score <= 0:
        return 0.0
    return round_score(clamp((score / max_score) * 100.0))


def score_existing_analysis(
    *,
    resume: dict[str, Any] | None,
    coding: dict[str, Any] | None,
    marksheet: dict[str, Any] | None = None,
    jd: dict[str, Any] | str | None = None,
) -> dict[str, Any]:
    processed = process_candidate(
        {
            "resume": resume,
            "coding": coding,
            "marksheet": marksheet,
            "jd": jd,
        }
    )
    scores = processed["scores"]
    coding_score = _score_to_percent(scores["github_score"] + scores["leetcode_score"], 40.0)
    academic_score = _score_to_percent(scores["academic_score"], 20.0)

    return {
        "resume_score": scores["resume_score"],
        "github_score": scores["github_score"],
        "leetcode_score": scores["leetcode_score"],
        "academic_score": scores["academic_score"],
        "final_score": scores["final_score"],
        "coding_score": coding_score,
        "academic_score_percent": academic_score,
        "breakdown": scores["breakdown"],
    }


async def run_full_analysis(
    resume_id_or_file_path: str | Path | None = None,
    *,
    resume_data: dict[str, Any] | None = None,
    coding_data: dict[str, Any] | None = None,
    marksheet_data: dict[str, Any] | None = None,
    jd_data: dict[str, Any] | str | None = None,
    resume_file_bytes: bytes | None = None,
    resume_filename: str | None = None,
    resume_content_type: str | None = None,
    github_username: str | None = None,
    leetcode_username: str | None = None,
    codeforces_username: str | None = None,
    settings: Any | None = None,
) -> dict[str, Any]:
    """
    Fetch missing analyzer data when a file path/bytes is supplied, then score it.

    Existing backend callers can pass already-fetched analyzer payloads. New
    callers can pass a local file path or bytes plus usernames and this service
    will reuse master-service downstream clients.
    """
    resolved_settings = settings
    if resolved_settings is None and (resume_data is None or coding_data is None):
        from app.config import get_settings

        resolved_settings = get_settings()

    if resume_data is None:
        if resume_file_bytes is None and resume_id_or_file_path is not None:
            path = Path(resume_id_or_file_path)
            resume_file_bytes = path.read_bytes()
            resume_filename = resume_filename or path.name
        if resume_file_bytes is not None:
            from app.services.downstream import DEFAULT_HEADERS, call_resume_analyzer

            filename = resume_filename or "resume.bin"
            async with httpx.AsyncClient(headers=DEFAULT_HEADERS) as client:
                fetched_resume, resume_error = await call_resume_analyzer(
                    settings=resolved_settings,
                    client=client,
                    file_bytes=resume_file_bytes,
                    filename=filename,
                    content_type=resume_content_type or _content_type_for(filename),
                )
            if resume_error:
                raise ValueError(f"Resume analyzer failed: {resume_error}")
            resume_data = fetched_resume

    if coding_data is None and any([github_username, leetcode_username, codeforces_username]):
        from app.services.downstream import DEFAULT_HEADERS, call_coding_analyzer

        async with httpx.AsyncClient(headers=DEFAULT_HEADERS) as client:
            fetched_coding, coding_error = await call_coding_analyzer(
                settings=resolved_settings,
                client=client,
                payload={
                    "github_username": github_username,
                    "leetcode_username": leetcode_username,
                    "codeforces_username": codeforces_username,
                },
            )
        if coding_error:
            raise ValueError(f"Coding analyzer failed: {coding_error}")
        coding_data = fetched_coding

    return score_existing_analysis(
        resume=as_dict(resume_data),
        coding=as_dict(coding_data),
        marksheet=as_dict(marksheet_data),
        jd=jd_data,
    )

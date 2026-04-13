from __future__ import annotations

import asyncio
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.config import get_settings
from app.services.downstream import (
    DEFAULT_HEADERS,
    call_coding_analyzer,
    call_marksheet_analyzer,
    call_resume_analyzer,
)
from app.services.payload_builder import build_master_report

router = APIRouter()
TEMPLATES = Jinja2Templates(directory=str(Path(__file__).resolve().parents[1] / "templates"))

MAX_RESUME_BYTES = 8 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".docx"}
ALLOWED_MARKSHEET_EXTENSIONS = {".pdf"}
RESUME_FORBIDDEN_NAME_TOKENS = ("marksheet", "one view", "result")
MARKSHEET_FORBIDDEN_NAME_TOKENS = ("resume", "cv")


def _bytes_text_lower(data: bytes) -> str:
    # Best-effort text sniffing for quick role validation.
    return data.decode("utf-8", errors="ignore").lower()


def _looks_like_marksheet(data: bytes) -> bool:
    t = _bytes_text_lower(data)
    anchors = ("aktu-one-view", "student result", "sgpa", "rollno", "enrollmentno", "semester")
    return sum(1 for a in anchors if a in t) >= 2


def _looks_like_resume(data: bytes) -> bool:
    t = _bytes_text_lower(data)
    anchors = ("education", "experience", "skills", "projects", "certifications", "summary")
    return sum(1 for a in anchors if a in t) >= 2


@dataclass
class ResumeOutcome:
    data: dict[str, Any] | None
    error: str | None


@dataclass
class CodingOutcome:
    data: dict[str, Any] | None
    error: str | None
    skipped: bool


@dataclass
class MarksheetOutcome:
    data: dict[str, Any] | None
    error: str | None
    skipped: bool


@router.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return TEMPLATES.TemplateResponse(request, "index.html", {"request": request})


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/analyze-profile")
async def analyze_profile(
    file: UploadFile = File(...),
    marksheet_file: UploadFile | None = File(None),
    branch: str = Form(""),
    github_username: str = Form(""),
    leetcode_username: str = Form(""),
    codeforces_username: str = Form(""),
) -> JSONResponse:
    settings = get_settings()
    branch_stripped = branch.strip()
    if not branch_stripped:
        raise HTTPException(
            status_code=400,
            detail="Branch is required.",
        )

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Please upload PDF or DOCX.",
        )

    resume_name_lower = (file.filename or "").lower()
    if any(token in resume_name_lower for token in RESUME_FORBIDDEN_NAME_TOKENS):
        raise HTTPException(
            status_code=400,
            detail="Resume file appears to be a marksheet. Upload it in the marksheet field.",
        )

    contents = await file.read()
    if len(contents) > MAX_RESUME_BYTES:
        raise HTTPException(
            status_code=413,
            detail="Resume file is too large (max 8 MB).",
        )
    if suffix == ".pdf" and _looks_like_marksheet(contents):
        raise HTTPException(
            status_code=400,
            detail="Uploaded resume file looks like a marksheet PDF. Please upload a valid resume.",
        )

    gh = github_username.strip() or None
    lc = leetcode_username.strip() or None
    cf = codeforces_username.strip() or None
    has_coding = bool(gh or lc or cf)
    has_marksheet = marksheet_file is not None and bool((marksheet_file.filename or "").strip())
    marksheet_contents: bytes | None = None
    marksheet_filename = "marksheet.pdf"
    marksheet_content_type: str | None = None
    if has_marksheet and marksheet_file is not None:
        marksheet_name_lower = (marksheet_file.filename or "").lower()
        if any(token in marksheet_name_lower for token in MARKSHEET_FORBIDDEN_NAME_TOKENS):
            raise HTTPException(
                status_code=400,
                detail="Marksheet file name looks like a resume. Upload the resume in the resume field.",
            )
        marksheet_suffix = Path(marksheet_file.filename or "").suffix.lower()
        if marksheet_suffix not in ALLOWED_MARKSHEET_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail="Unsupported marksheet type. Please upload PDF.",
            )
        marksheet_contents = await marksheet_file.read()
        if len(marksheet_contents) > MAX_RESUME_BYTES:
            raise HTTPException(
                status_code=413,
                detail="Marksheet file is too large (max 8 MB).",
            )
        if hashlib.sha256(contents).digest() == hashlib.sha256(marksheet_contents).digest():
            raise HTTPException(
                status_code=400,
                detail="Resume and marksheet files cannot be the same file.",
            )
        if not _looks_like_marksheet(marksheet_contents):
            if _looks_like_resume(marksheet_contents):
                raise HTTPException(
                    status_code=400,
                    detail="Uploaded marksheet file looks like a resume. Please upload a valid marksheet PDF.",
                )
            raise HTTPException(
                status_code=400,
                detail="Uploaded marksheet file does not look like a valid marksheet PDF.",
            )
        marksheet_filename = marksheet_file.filename or "marksheet.pdf"
        marksheet_content_type = marksheet_file.content_type

    async def run_resume() -> ResumeOutcome:
        async with httpx.AsyncClient(headers=DEFAULT_HEADERS) as client:
            data, err = await call_resume_analyzer(
                settings=settings,
                client=client,
                file_bytes=contents,
                filename=file.filename or "resume.bin",
                content_type=file.content_type,
            )
        return ResumeOutcome(data=data, error=err)

    async def run_coding() -> CodingOutcome:
        if not has_coding:
            return CodingOutcome(
                data=None,
                error="Provide at least one platform username (GitHub, LeetCode, or Codeforces).",
                skipped=True,
            )
        payload = {
            "github_username": gh,
            "leetcode_username": lc,
            "codeforces_username": cf,
        }
        async with httpx.AsyncClient(headers=DEFAULT_HEADERS) as client:
            data, err = await call_coding_analyzer(
                settings=settings,
                client=client,
                payload=payload,
            )
        return CodingOutcome(data=data, error=err, skipped=False)

    async def run_marksheet() -> MarksheetOutcome:
        if not has_marksheet or marksheet_contents is None:
            return MarksheetOutcome(
                data=None,
                error="Marksheet not provided.",
                skipped=True,
            )
        async with httpx.AsyncClient(headers=DEFAULT_HEADERS) as client:
            data, err = await call_marksheet_analyzer(
                settings=settings,
                client=client,
                file_bytes=marksheet_contents,
                filename=marksheet_filename,
                content_type=marksheet_content_type,
            )
        return MarksheetOutcome(data=data, error=err, skipped=False)

    resume_out, coding_out, marksheet_out = await asyncio.gather(run_resume(), run_coding(), run_marksheet())

    resume_ok = resume_out.data is not None
    if coding_out.skipped:
        coding_skipped = True
        coding_ok = False
        coding_data: dict[str, Any] | None = None
        coding_error = coding_out.error
    else:
        coding_skipped = False
        coding_ok = coding_out.data is not None
        coding_data = coding_out.data
        coding_error = coding_out.error

    if marksheet_out.skipped:
        marksheet_skipped = True
        marksheet_ok = False
        marksheet_data: dict[str, Any] | None = None
        marksheet_error = marksheet_out.error
    else:
        marksheet_skipped = False
        marksheet_ok = marksheet_out.data is not None
        marksheet_data = marksheet_out.data
        marksheet_error = marksheet_out.error

    report = build_master_report(
        resume=resume_out.data,
        coding=coding_data,
        marksheet=marksheet_data,
        branch=branch_stripped,
        github_username=gh,
        leetcode_username=lc,
        codeforces_username=cf,
        resume_filename=file.filename,
        resume_ok=resume_ok,
        resume_error=resume_out.error,
        coding_ok=coding_ok,
        coding_skipped=coding_skipped,
        coding_error=coding_error,
        marksheet_ok=marksheet_ok,
        marksheet_skipped=marksheet_skipped,
        marksheet_error=marksheet_error,
    )

    resume_failed = resume_out.data is None
    coding_failed = has_coding and coding_out.data is None
    if resume_failed and coding_failed:
        return JSONResponse(
            status_code=502,
            content=report.model_dump(),
        )

    return JSONResponse(content=report.model_dump())

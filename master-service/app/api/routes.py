from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.config import get_settings
from app.models.report import MasterAnalysisReport
from app.services.downstream import DEFAULT_HEADERS, call_coding_analyzer, call_resume_analyzer

router = APIRouter()
TEMPLATES = Jinja2Templates(directory=str(Path(__file__).resolve().parents[1] / "templates"))

MAX_RESUME_BYTES = 8 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".docx"}


@dataclass
class ResumeOutcome:
    data: dict[str, Any] | None
    error: str | None


@dataclass
class CodingOutcome:
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
    github_username: str = Form(""),
    leetcode_username: str = Form(""),
    codeforces_username: str = Form(""),
) -> JSONResponse:
    settings = get_settings()
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Please upload PDF or DOCX.",
        )

    contents = await file.read()
    if len(contents) > MAX_RESUME_BYTES:
        raise HTTPException(
            status_code=413,
            detail="Resume file is too large (max 8 MB).",
        )

    gh = github_username.strip() or None
    lc = leetcode_username.strip() or None
    cf = codeforces_username.strip() or None
    has_coding = bool(gh or lc or cf)

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

    resume_out, coding_out = await asyncio.gather(run_resume(), run_coding())

    report = MasterAnalysisReport()
    report.resume_ok = resume_out.data is not None
    report.resume = resume_out.data
    report.resume_error = resume_out.error

    if coding_out.skipped:
        report.coding_skipped = True
        report.coding_ok = False
        report.coding = None
        report.coding_error = coding_out.error
    else:
        report.coding_skipped = False
        report.coding_ok = coding_out.data is not None
        report.coding = coding_out.data
        report.coding_error = coding_out.error

    resume_failed = resume_out.data is None
    coding_failed = has_coding and coding_out.data is None
    if resume_failed and coding_failed:
        return JSONResponse(
            status_code=502,
            content=report.model_dump(),
        )

    return JSONResponse(content=report.model_dump())

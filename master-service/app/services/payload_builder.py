from __future__ import annotations

import re
from typing import Any

from app.models.report import (
    AcademicsPayload,
    CodeforcesSummaryPayload,
    GitHubStatsPayload,
    LeetCodeStatsPayload,
    MasterAnalysisReport,
    ProfilePayload,
    SourcesPayload,
    StudentPayload,
)


def _normalize_skill(s: str) -> str:
    return s.strip().lower()


def normalize_resume_skills(skills: list[Any] | None) -> list[str]:
    if not skills:
        return []
    out: list[str] = []
    seen: set[str] = set()
    for item in skills:
        if not isinstance(item, str):
            continue
        n = _normalize_skill(item)
        if not n or n in seen:
            continue
        seen.add(n)
        out.append(n)
    return out


def _parse_cgpa_numeric(cgpa: str) -> float | None:
    if not cgpa or not isinstance(cgpa, str):
        return None
    m = re.search(r"(\d+(?:\.\d+)?)", cgpa.replace(",", "."))
    if not m:
        return None
    try:
        return float(m.group(1))
    except ValueError:
        return None


def _str_from_resume(resume: dict[str, Any] | None, key: str) -> str:
    if not resume:
        return ""
    v = resume.get(key)
    if v is None:
        return ""
    return str(v).strip()


def build_master_report(
    *,
    resume: dict[str, Any] | None,
    coding: dict[str, Any] | None,
    branch: str,
    github_username: str | None,
    leetcode_username: str | None,
    codeforces_username: str | None,
    marksheet: dict[str, Any] | None,
    resume_filename: str | None,
    resume_ok: bool,
    resume_error: str | None,
    coding_ok: bool,
    coding_skipped: bool,
    coding_error: str | None,
    marksheet_ok: bool,
    marksheet_skipped: bool,
    marksheet_error: str | None,
) -> MasterAnalysisReport:
    branch_clean = branch.strip()
    cgpa_str = _str_from_resume(resume, "cgpa") if resume_ok and resume else ""
    student = StudentPayload(
        name=_str_from_resume(resume, "name") if resume_ok and resume else "",
        email=_str_from_resume(resume, "email") if resume_ok and resume else "",
        phone=_str_from_resume(resume, "phone") if resume_ok and resume else "",
        cgpa=cgpa_str,
        cgpa_numeric=_parse_cgpa_numeric(cgpa_str) if cgpa_str else None,
        branch=branch_clean,
        github_username=github_username,
        leetcode_username=leetcode_username,
        codeforces_username=codeforces_username,
        roll_no="",
        enrollment_no="",
        class_name="",
        resume_url=None,
        resume_filename=resume_filename,
    )
    if marksheet_ok and marksheet:
        candidate = marksheet.get("candidate") if isinstance(marksheet.get("candidate"), dict) else {}
        student.roll_no = str(candidate.get("roll_no") or "").strip()
        student.enrollment_no = str(candidate.get("enrollment_no") or "").strip()
        student.class_name = str(candidate.get("class_name") or "").strip()
        if not student.name:
            student.name = str(candidate.get("name") or "").strip()

    academics = _build_academics(marksheet if marksheet_ok else None)
    if not student.cgpa and academics.cgpa_computed is not None:
        student.cgpa = str(academics.cgpa_computed)
        student.cgpa_numeric = float(academics.cgpa_computed)

    profile = _build_profile(resume if resume_ok else None, coding if coding_ok else None)
    sources = SourcesPayload(
        resume=resume if resume_ok else None,
        coding=coding if coding_ok else None,
        marksheet=marksheet if marksheet_ok else None,
    )

    return MasterAnalysisReport(
        student=student,
        academics=academics,
        profile=profile,
        sources=sources,
        resume_ok=resume_ok,
        resume_error=resume_error,
        coding_ok=coding_ok,
        coding_skipped=coding_skipped,
        coding_error=coding_error,
        marksheet_ok=marksheet_ok,
        marksheet_skipped=marksheet_skipped,
        marksheet_error=marksheet_error,
    )


def _build_academics(marksheet: dict[str, Any] | None) -> AcademicsPayload:
    if not marksheet:
        return AcademicsPayload()
    backlog = marksheet.get("backlog") if isinstance(marksheet.get("backlog"), dict) else {}
    codes_raw = backlog.get("active_backlog_codes")
    codes = [str(x) for x in codes_raw if isinstance(x, str)] if isinstance(codes_raw, list) else []
    return AcademicsPayload(
        cgpa_computed=marksheet.get("cgpa_computed") if isinstance(marksheet.get("cgpa_computed"), (int, float)) else None,
        last_semester_number=marksheet.get("last_semester_number")
        if isinstance(marksheet.get("last_semester_number"), int)
        else None,
        last_semester_sgpa=marksheet.get("last_semester_sgpa")
        if isinstance(marksheet.get("last_semester_sgpa"), (int, float))
        else None,
        has_active_backlog=bool(backlog.get("has_active_backlog")),
        active_backlog_codes=codes,
    )


def _build_profile(
    resume: dict[str, Any] | None,
    coding: dict[str, Any] | None,
) -> ProfilePayload:
    resume_skills: list[str] = []
    if resume:
        raw = resume.get("skills")
        if isinstance(raw, list):
            resume_skills = normalize_resume_skills(raw)

    if not coding:
        return ProfilePayload(
            resume_skills=resume_skills,
            coding_persona="",
            github_stats=GitHubStatsPayload(),
            leetcode_stats=LeetCodeStatsPayload(),
            codeforces_summary=None,
        )

    gh = coding.get("github") if isinstance(coding.get("github"), dict) else {}
    lc = coding.get("leetcode") if isinstance(coding.get("leetcode"), dict) else {}
    cf = coding.get("codeforces") if isinstance(coding.get("codeforces"), dict) else {}

    langs = gh.get("languages")
    if not isinstance(langs, list):
        langs = []
    languages = [str(x) for x in langs if isinstance(x, str)]

    github_stats = GitHubStatsPayload(
        repos=int(gh.get("repos") or 0),
        commits_30d=int(gh.get("last_30_day_commits") or 0),
        languages=languages,
    )

    leetcode_stats = LeetCodeStatsPayload(
        total_solved=int(lc.get("total_solved") or 0),
        easy=int(lc.get("easy") or 0),
        medium=int(lc.get("medium") or 0),
        hard=int(lc.get("hard") or 0),
    )

    cf_summary: CodeforcesSummaryPayload | None = None
    if any(cf.get(k) is not None for k in ("rating", "max_rating", "rank", "max_rank")):
        cf_summary = CodeforcesSummaryPayload(
            rating=cf.get("rating") if cf.get("rating") is not None else None,
            max_rating=cf.get("max_rating") if cf.get("max_rating") is not None else None,
            rank=str(cf["rank"]) if cf.get("rank") is not None else None,
            max_rank=str(cf["max_rank"]) if cf.get("max_rank") is not None else None,
        )

    raw_persona = coding.get("coding_persona")
    persona_str = str(raw_persona).strip() if raw_persona is not None else ""

    return ProfilePayload(
        resume_skills=resume_skills,
        coding_persona=persona_str,
        github_stats=github_stats,
        leetcode_stats=leetcode_stats,
        codeforces_summary=cf_summary,
    )

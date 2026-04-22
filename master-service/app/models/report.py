from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class GitHubStatsPayload(BaseModel):
    repos: int = 0
    commits_30d: int = 0
    languages: list[str] = Field(default_factory=list)


class LeetCodeStatsPayload(BaseModel):
    total_solved: int = 0
    easy: int = 0
    medium: int = 0
    hard: int = 0


class CodeforcesSummaryPayload(BaseModel):
    rating: int | None = None
    max_rating: int | None = None
    rank: str | None = None
    max_rank: str | None = None


class StudentPayload(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    cgpa: str = ""
    cgpa_numeric: float | None = None
    branch: str = ""
    github_username: str | None = None
    leetcode_username: str | None = None
    codeforces_username: str | None = None
    roll_no: str = ""
    enrollment_no: str = ""
    class_name: str = ""
    resume_url: str | None = None
    resume_filename: str | None = None


class AcademicsPayload(BaseModel):
    cgpa_computed: float | None = None
    last_semester_number: int | None = None
    last_semester_sgpa: float | None = None
    has_active_backlog: bool = False
    active_backlog_codes: list[str] = Field(default_factory=list)


class ProfilePayload(BaseModel):
    resume_skills: list[str] = Field(default_factory=list)
    coding_persona: str = ""
    github_stats: GitHubStatsPayload = Field(default_factory=GitHubStatsPayload)
    leetcode_stats: LeetCodeStatsPayload = Field(default_factory=LeetCodeStatsPayload)
    codeforces_summary: CodeforcesSummaryPayload | None = None


class SourcesPayload(BaseModel):
    resume: dict[str, Any] | None = None
    coding: dict[str, Any] | None = None
    marksheet: dict[str, Any] | None = None


class MasterAnalysisReport(BaseModel):
    report_version: int = 2
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    student: StudentPayload = Field(default_factory=StudentPayload)
    academics: AcademicsPayload = Field(default_factory=AcademicsPayload)
    profile: ProfilePayload = Field(default_factory=ProfilePayload)
    sources: SourcesPayload = Field(default_factory=SourcesPayload)

    resume_ok: bool = False
    resume_error: str | None = None

    coding_ok: bool = False
    coding_skipped: bool = False
    coding_error: str | None = None

    marksheet_ok: bool = False
    marksheet_skipped: bool = False
    marksheet_error: str | None = None

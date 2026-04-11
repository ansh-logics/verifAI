from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class MasterAnalysisReport(BaseModel):
    report_version: int = 1
    generated_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())

    resume_ok: bool = False
    resume: dict[str, Any] | None = None
    resume_error: str | None = None

    coding_ok: bool = False
    coding_skipped: bool = False
    coding: dict[str, Any] | None = None
    coding_error: str | None = None

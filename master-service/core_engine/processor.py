from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from core_engine.scoring import calculate_candidate_score
from core_engine.utils import as_dict


def process_candidate(raw_input: Mapping[str, Any] | None) -> dict[str, Any]:
    """
    Normalize analyzer outputs and calculate candidate scores.

    The existing FastAPI flow already calls resume-analyzer, coding-analyzer,
    and marksheet-analyzer. This processor accepts those raw outputs so the
    scoring layer stays independent of route code and analyzer internals.
    """
    payload = as_dict(raw_input)
    resume = as_dict(payload.get("resume") or payload.get("resume_data"))
    coding = as_dict(payload.get("coding") or payload.get("coding_data"))
    academics = as_dict(payload.get("academics") or payload.get("marksheet") or payload.get("academic_data"))
    jd = payload.get("jd") or payload.get("jd_data") or payload.get("job_description")

    github = as_dict(payload.get("github") or payload.get("github_data") or coding.get("github"))
    leetcode = as_dict(payload.get("leetcode") or payload.get("leetcode_data") or coding.get("leetcode"))

    scores = calculate_candidate_score(
        resume=resume,
        github=github,
        leetcode=leetcode,
        academics=academics,
        coding=coding,
        jd=jd,
    )

    return {
        "resume": resume,
        "github": github,
        "leetcode": leetcode,
        "academics": academics,
        "jd": jd,
        "scores": scores,
    }

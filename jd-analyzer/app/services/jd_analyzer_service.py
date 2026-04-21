from __future__ import annotations

import asyncio
import json
from typing import Any, cast

from groq import Groq

from app.config import Settings
from app.models.response_model import GenderFilter, JDAnalyzeResponse


SYSTEM_PROMPT = """You are a Job Description parser for a placement intelligence system.

Your ONLY job is to extract structured information from combined input text and return STRICT valid JSON.
The input may contain both:
1) Job description details
2) TPO candidate-selection constraints

RULES:
- Output ONLY a JSON object. No explanation, no markdown, no code fences, no extra text.
- If a field cannot be determined, use null for strings/numbers and [] for arrays.
- For accepts_freshers: true if 0 years experience required OR "freshers welcome" is mentioned.
- For min_experience_years: extract the MINIMUM number only (e.g. "2-5 years" → 2). If fresher/entry level, use 0.
- For required_skills: only hard requirements explicitly stated.
- For preferred_skills: "good to have", "plus", "bonus", or "preferred" skills.
- For key_traits: soft skills and personality traits (e.g. "team player", "self-starter").
- For role_type: one of → "full_time" | "internship" | "contract" | "part_time" | "unknown"
- Extract company_name from explicit company/organization/employer mentions when available.
- Extract pay_or_stipend from stipend/salary/CTC/compensation statements as concise text.
- Extract bond_details from service-agreement/bond/commitment clauses as concise text.
- Generate jd_summary as a concise 2-4 sentence summary of the role and constraints.
- Return canonical lowercase skill and trait tokens wherever possible.
- Extract TPO constraints when present:
  - target_student_count: numeric count requested (e.g. "give me 50 students")
  - exclude_active_backlogs: true for statements like "no back", "without backlog"
  - placement_filter: "unplaced_only" if text says not placed / unplaced only; else "placed_or_unplaced"
  - placement_exception_roll_nos: explicit roll numbers allowed as exceptions
  - min_cgpa: numeric threshold if present
  - allowed_branches: branch list if constraints mention branches
- Gender constraints:
  - "only girls", "female only", "women only", "for women" -> gender_filter="women_only"
  - "only boys", "male only", "men only", "for men" -> gender_filter="men_only"
  - no restriction / mixed / any gender -> gender_filter="all_genders"
  - any custom/non-binary-specific condition -> gender_filter="custom_text" and preserve phrase in gender_filter_raw
- Branch-family inference:
  - For phrases like "CSE related", infer allowed_branches as ["cse","it","aiml","ds"] unless explicitly contradicted.
  - Preserve original branch phrase in branch_constraint_raw when inference is used.
"""

USER_PROMPT = """Parse this combined text (JD + optional TPO constraints) and return only JSON:

<combined_input>
{jd_text}
</combined_input>

Return exactly this schema:
{{
  "company_name": "string | null",
  "pay_or_stipend": "string | null",
  "bond_details": "string | null",
  "jd_summary": "string | null",
  "job_title": "string | null",
  "role_type": "full_time | internship | contract | part_time | unknown",
  "required_skills": ["string"],
  "preferred_skills": ["string"],
  "tools_and_technologies": ["string"],
  "responsibilities": ["string"],
  "min_experience_years": "number | null",
  "accepts_freshers": "boolean",
  "key_traits": ["string"],
  "education_requirements": ["string"],
  "location": "string | null",
  "domain": "string | null",
  "duration": "string | null",
  "work_type": "string | null",
  "target_student_count": "number | null",
  "exclude_active_backlogs": "boolean",
  "placement_filter": "unplaced_only | placed_or_unplaced",
  "placement_exception_roll_nos": ["string"],
  "min_cgpa": "number | null",
  "allowed_branches": ["string"],
  "gender_filter": "women_only | men_only | all_genders | custom_text",
  "gender_filter_raw": "string | null",
  "branch_constraint_raw": "string | null",
  "branch_inference_reason": "string | null"
}}"""


class JDAnalyzerServiceError(Exception):
    """Raised when JD parsing fails."""


SKILL_SYNONYMS: dict[str, str] = {
    "ui & ux design": "ui/ux design",
    "ui and ux design": "ui/ux design",
    "ux/ui design": "ui/ux design",
    "reactjs": "react",
    "react.js": "react",
    "nodejs": "node.js",
    "node js": "node.js",
    "js": "javascript",
}

BRANCH_SYNONYMS: dict[str, str] = {
    "computer science": "cse",
    "computer science and engineering": "cse",
    "cse": "cse",
    "information technology": "it",
    "it": "it",
    "electronics and communication engineering": "ece",
    "ece": "ece",
    "electrical and electronics engineering": "eee",
    "eee": "eee",
    "mechanical engineering": "me",
    "me": "me",
    "civil engineering": "ce",
    "ce": "ce",
    "artificial intelligence and machine learning": "aiml",
    "aiml": "aiml",
    "data science": "ds",
    "ds": "ds",
}

BRANCH_FAMILY_INFERENCE: dict[str, tuple[list[str], str]] = {
    "cse related": (["cse", "it", "aiml", "ds"], "Mapped CSE-related family to core CS branches."),
    "cse-related": (["cse", "it", "aiml", "ds"], "Mapped CSE-related family to core CS branches."),
    "computer science related": (["cse", "it", "aiml", "ds"], "Mapped Computer Science related family to core CS branches."),
    "computer-science related": (["cse", "it", "aiml", "ds"], "Mapped Computer Science related family to core CS branches."),
}

GENDER_MAP: dict[str, str] = {
    "only girls": "women_only",
    "girls only": "women_only",
    "female only": "women_only",
    "women only": "women_only",
    "for women": "women_only",
    "only boys": "men_only",
    "boys only": "men_only",
    "male only": "men_only",
    "men only": "men_only",
    "for men": "men_only",
    "any gender": "all_genders",
    "mixed gender": "all_genders",
    "all genders": "all_genders",
}


def _normalize_token(value: str) -> str:
    normalized = " ".join(value.strip().lower().split())
    return SKILL_SYNONYMS.get(normalized, normalized)


def _to_string_list(value: Any, *, canonical: bool = False) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, str):
            continue
        cleaned = item.strip()
        normalized = _normalize_token(cleaned) if canonical else cleaned
        dedupe_key = normalized.lower()
        if not normalized or dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        out.append(normalized)
    return out


def _normalize_nullable_string(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    return cleaned if cleaned else None


def _normalize_roll_numbers(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, str):
            continue
        normalized = "".join(item.strip().upper().split())
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        out.append(normalized)
    return out


def _normalize_branches(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, str):
            continue
        raw = " ".join(item.strip().lower().split())
        normalized = BRANCH_SYNONYMS.get(raw, raw)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        out.append(normalized)
    return out


def _normalize_branch_phrase(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = " ".join(value.strip().lower().split())
    return cleaned if cleaned else None


def _apply_branch_inference(
    allowed_branches: list[str],
    branch_constraint_raw: str | None,
) -> tuple[list[str], str | None]:
    if not branch_constraint_raw:
        return allowed_branches, None
    inferred = BRANCH_FAMILY_INFERENCE.get(branch_constraint_raw)
    if not inferred:
        return allowed_branches, None
    inferred_branches, reason = inferred
    merged: list[str] = []
    seen: set[str] = set()
    for branch in [*allowed_branches, *inferred_branches]:
        if branch in seen:
            continue
        seen.add(branch)
        merged.append(branch)
    return merged, reason


def _normalize_gender_filter(value: Any, raw_phrase: Any) -> tuple[str, str | None]:
    filter_value = value if isinstance(value, str) else ""
    filter_clean = " ".join(filter_value.strip().lower().split())
    raw_clean = _normalize_nullable_string(raw_phrase)
    if filter_clean in {"women_only", "men_only", "all_genders", "custom_text"}:
        if filter_clean == "custom_text":
            return "custom_text", raw_clean
        return filter_clean, raw_clean if raw_clean else None

    if raw_clean:
        raw_lower = " ".join(raw_clean.lower().split())
        mapped = GENDER_MAP.get(raw_lower)
        if mapped:
            return mapped, raw_clean
        return "custom_text", raw_clean

    return "all_genders", None


def _to_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None
    return None


def _normalize_output(raw: dict[str, Any]) -> JDAnalyzeResponse:
    role_type = raw.get("role_type")
    if role_type not in {"full_time", "internship", "contract", "part_time", "unknown"}:
        role_type = "unknown"

    min_exp = _to_number(raw.get("min_experience_years"))

    accepts_freshers = bool(raw.get("accepts_freshers", False))
    if isinstance(min_exp, (int, float)) and float(min_exp) <= 0:
        accepts_freshers = True

    placement_filter = raw.get("placement_filter")
    if placement_filter not in {"unplaced_only", "placed_or_unplaced"}:
        placement_filter = "placed_or_unplaced"

    target_student_count = _to_number(raw.get("target_student_count"))
    if target_student_count is not None and target_student_count <= 0:
        target_student_count = None

    min_cgpa = _to_number(raw.get("min_cgpa"))
    if min_cgpa is not None and (min_cgpa < 0 or min_cgpa > 10):
        min_cgpa = None

    branch_constraint_raw = _normalize_branch_phrase(raw.get("branch_constraint_raw"))
    allowed_branches = _normalize_branches(raw.get("allowed_branches"))
    allowed_branches, branch_inference_reason = _apply_branch_inference(
        allowed_branches=allowed_branches,
        branch_constraint_raw=branch_constraint_raw,
    )

    gender_filter, gender_filter_raw = _normalize_gender_filter(
        raw.get("gender_filter"),
        raw.get("gender_filter_raw"),
    )

    return JDAnalyzeResponse(
        company_name=_normalize_nullable_string(raw.get("company_name")),
        pay_or_stipend=_normalize_nullable_string(raw.get("pay_or_stipend") or raw.get("stipend") or raw.get("salary") or raw.get("ctc")),
        bond_details=_normalize_nullable_string(raw.get("bond_details") or raw.get("bond") or raw.get("service_agreement")),
        jd_summary=_normalize_nullable_string(raw.get("jd_summary") or raw.get("summary")),
        job_title=_normalize_nullable_string(raw.get("job_title")),
        role_type=role_type,
        required_skills=_to_string_list(raw.get("required_skills"), canonical=True),
        preferred_skills=_to_string_list(raw.get("preferred_skills"), canonical=True),
        tools_and_technologies=_to_string_list(raw.get("tools_and_technologies"), canonical=True),
        responsibilities=_to_string_list(raw.get("responsibilities")),
        min_experience_years=min_exp,
        accepts_freshers=accepts_freshers,
        key_traits=_to_string_list(raw.get("key_traits"), canonical=True),
        education_requirements=_to_string_list(raw.get("education_requirements")),
        location=_normalize_nullable_string(raw.get("location")),
        domain=_normalize_nullable_string(raw.get("domain")),
        duration=_normalize_nullable_string(raw.get("duration")),
        work_type=_normalize_nullable_string(raw.get("work_type")),
        target_student_count=int(target_student_count) if target_student_count is not None else None,
        exclude_active_backlogs=bool(raw.get("exclude_active_backlogs", False)),
        placement_filter=placement_filter,
        placement_exception_roll_nos=_normalize_roll_numbers(raw.get("placement_exception_roll_nos")),
        min_cgpa=min_cgpa,
        allowed_branches=allowed_branches,
        gender_filter=cast(GenderFilter, gender_filter),
        gender_filter_raw=gender_filter_raw,
        branch_constraint_raw=branch_constraint_raw,
        branch_inference_reason=branch_inference_reason,
    )


class JDAnalyzerService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = Groq(api_key=settings.groq_api_key)

    async def parse_jd(self, jd_text: str) -> JDAnalyzeResponse:
        content = USER_PROMPT.format(jd_text=jd_text.strip())

        def _request() -> str:
            response = self._client.chat.completions.create(
                model=self._settings.groq_model,
                temperature=0,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": content},
                ],
            )
            raw_content = response.choices[0].message.content
            if not raw_content or not raw_content.strip():
                raise JDAnalyzerServiceError("Groq returned empty content.")
            return raw_content

        try:
            raw = await asyncio.wait_for(
                asyncio.to_thread(_request),
                timeout=self._settings.request_timeout_seconds,
            )
        except TimeoutError as exc:
            raise JDAnalyzerServiceError("JD parsing request timed out.") from exc
        except JDAnalyzerServiceError:
            raise
        except Exception as exc:
            raise JDAnalyzerServiceError(f"Groq request failed: {exc}") from exc

        clean = raw.strip().removeprefix("```json").removesuffix("```").strip()
        try:
            payload = json.loads(clean)
        except json.JSONDecodeError as exc:
            raise JDAnalyzerServiceError("Model returned non-JSON output.") from exc

        if not isinstance(payload, dict):
            raise JDAnalyzerServiceError("Model output is not a JSON object.")

        return _normalize_output(payload)

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session, joinedload

from app.database.models import RawUpload, Student
from app.schemas.student import FilterSummary, JDParsedConstraints, MatchCandidate, ScoreBreakdown

REQUIRED_WEIGHT = 50.0
PREFERRED_WEIGHT = 20.0
CGPA_WEIGHT = 20.0
BRANCH_WEIGHT = 10.0


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return False


def _normalize_skill_list(values: list[str] | None) -> set[str]:
    if not values:
        return set()
    return {v.strip().lower() for v in values if isinstance(v, str) and v.strip()}


def _latest_resume_urls(db: Session, student_ids: list[int]) -> dict[int, str]:
    if not student_ids:
        return {}
    rows = (
        db.query(RawUpload)
        .filter(RawUpload.student_id.in_(student_ids))
        .order_by(RawUpload.student_id.asc(), RawUpload.uploaded_at.desc(), RawUpload.id.desc())
        .all()
    )
    latest: dict[int, str] = {}
    for row in rows:
        if row.student_id not in latest and row.resume_url:
            latest[row.student_id] = row.resume_url
    return latest


def _parse_constraints(jd_data: dict[str, Any]) -> JDParsedConstraints:
    return JDParsedConstraints.model_validate(jd_data)


def _extract_status_flags(student: Student) -> tuple[bool, bool]:
    profile = student.profile
    if profile is None:
        return False, False
    resume_data = profile.resume_data if isinstance(profile.resume_data, dict) else {}
    academic_data = profile.academic_data if isinstance(profile.academic_data, dict) else {}
    metadata = resume_data.get("metadata") if isinstance(resume_data.get("metadata"), dict) else {}
    is_placed = _to_bool(metadata.get("is_placed"))
    has_active_backlog = _to_bool(metadata.get("has_active_backlog")) or _to_bool(academic_data.get("has_active_backlog"))
    return is_placed, has_active_backlog


def _required_score(student_skills: set[str], required: set[str]) -> float:
    if not required:
        return REQUIRED_WEIGHT
    overlap = len(student_skills.intersection(required))
    return round((overlap / len(required)) * REQUIRED_WEIGHT, 2)


def _preferred_score(student_skills: set[str], preferred: set[str]) -> float:
    if not preferred:
        return 0.0
    overlap = len(student_skills.intersection(preferred))
    return round((overlap / len(preferred)) * PREFERRED_WEIGHT, 2)


def _cgpa_score(cgpa: float | None, min_cgpa: float | None) -> float:
    if cgpa is None:
        return 0.0
    if min_cgpa is None:
        return round((max(0.0, min(cgpa, 10.0)) / 10.0) * CGPA_WEIGHT, 2)
    if cgpa <= min_cgpa:
        return 0.0
    span = max(0.1, 10.0 - min_cgpa)
    normalized = min(1.0, max(0.0, (cgpa - min_cgpa) / span))
    return round(normalized * CGPA_WEIGHT, 2)


def _branch_score(student_branch: str, allowed_branches: set[str]) -> float:
    if not allowed_branches:
        return 0.0
    return BRANCH_WEIGHT if student_branch.lower().strip() in allowed_branches else 0.0


def run_jd_matching(
    *,
    db: Session,
    jd_data: dict[str, Any],
    student_ids: list[int] | None,
    top_k: int | None,
) -> tuple[JDParsedConstraints, FilterSummary, list[MatchCandidate]]:
    constraints = _parse_constraints(jd_data)
    summary = FilterSummary()

    query = db.query(Student).options(joinedload(Student.profile))
    if student_ids:
        query = query.filter(Student.id.in_(student_ids))
    students = query.all()
    summary.total_considered = len(students)

    required_skills = _normalize_skill_list(constraints.required_skills)
    preferred_combo = _normalize_skill_list(
        (constraints.preferred_skills or []) + (constraints.tools_and_technologies or []) + (constraints.key_traits or [])
    )
    allowed_branches = _normalize_skill_list(constraints.allowed_branches)
    placement_exceptions = {r.strip().upper() for r in constraints.placement_exception_roll_nos}

    accepted: list[tuple[float, MatchCandidate]] = []
    for student in students:
        student_branch = (student.branch or "").strip().lower()
        student_gender = (student.gender or "").strip().lower()
        student_roll = (student.roll_no or "").strip().upper()
        is_placed, has_backlog = _extract_status_flags(student)

        if constraints.min_cgpa is not None and (student.cgpa is None or student.cgpa < constraints.min_cgpa):
            summary.rejected_min_cgpa += 1
            continue

        if allowed_branches and student_branch not in allowed_branches:
            summary.rejected_branch += 1
            continue

        if constraints.gender_filter == "women_only" and student_gender != "women":
            summary.rejected_gender += 1
            continue
        if constraints.gender_filter == "men_only" and student_gender != "men":
            summary.rejected_gender += 1
            continue

        if constraints.exclude_active_backlogs and has_backlog:
            summary.rejected_backlog += 1
            continue

        if constraints.placement_filter == "unplaced_only" and is_placed and student_roll not in placement_exceptions:
            summary.rejected_placement += 1
            continue

        profile = student.profile
        student_skill_list = list(profile.skills or []) if profile is not None else []
        student_skills = _normalize_skill_list(student_skill_list)

        req_score = _required_score(student_skills, required_skills)
        pref_score = _preferred_score(student_skills, preferred_combo)
        cgpa_component = _cgpa_score(student.cgpa, constraints.min_cgpa)
        branch_component = _branch_score(student_branch, allowed_branches)
        total = round(req_score + pref_score + cgpa_component + branch_component, 2)

        accepted.append(
            (
                total,
                MatchCandidate(
                    student_id=student.id,
                    email=student.email,
                    name=student.name,
                    roll_no=student.roll_no,
                    gender=student.gender,
                    branch=student.branch,
                    cgpa=student.cgpa,
                    skills=student_skill_list,
                    resume_url=None,
                    coding_persona=profile.coding_persona if profile is not None else None,
                    is_placed=is_placed,
                    has_active_backlog=has_backlog,
                    score_breakdown=ScoreBreakdown(
                        required_skills=req_score,
                        preferred_tools_traits=pref_score,
                        cgpa=cgpa_component,
                        branch_affinity=branch_component,
                        total=total,
                    ),
                ),
            )
        )

    summary.passed_filters = len(accepted)
    accepted.sort(key=lambda item: (-item[0], item[1].student_id))
    candidates = [item[1] for item in accepted]

    capped = constraints.target_student_count if constraints.target_student_count and constraints.target_student_count > 0 else None
    if top_k is not None:
        capped = min(top_k, capped) if capped is not None else top_k
    if capped is not None:
        candidates = candidates[:capped]

    resume_map = _latest_resume_urls(db, [c.student_id for c in candidates])
    for candidate in candidates:
        candidate.resume_url = resume_map.get(candidate.student_id)

    return constraints, summary, candidates

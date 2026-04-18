from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session, joinedload

from app.database.models import RawUpload, Student
from app.schemas.student import FilterSummary, JDParsedConstraints, MatchCandidate, ScoreBreakdown
from core_engine import calculate_candidate_score


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return False


def _normalize_text_set(values: list[str] | None) -> set[str]:
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

    allowed_branches = _normalize_text_set(constraints.allowed_branches)
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

        engine_scores = calculate_candidate_score(
            resume=profile.resume_data if profile and isinstance(profile.resume_data, dict) else {},
            github=profile.github_data if profile and isinstance(profile.github_data, dict) else {},
            leetcode=profile.leetcode_data if profile and isinstance(profile.leetcode_data, dict) else {},
            academics=profile.academic_data if profile and isinstance(profile.academic_data, dict) else {},
            coding={
                "github": profile.github_data if profile and isinstance(profile.github_data, dict) else {},
                "leetcode": profile.leetcode_data if profile and isinstance(profile.leetcode_data, dict) else {},
            },
            jd=jd_data,
        )
        total = float(engine_scores["final_score"])

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
                        resume=float(engine_scores["resume_score"]),
                        github=float(engine_scores["github_score"]),
                        leetcode=float(engine_scores["leetcode_score"]),
                        academics=float(engine_scores["academic_score"]),
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

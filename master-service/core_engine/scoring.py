from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from core_engine.utils import (
    as_dict,
    choose_cgpa,
    clamp,
    extract_github_tech,
    extract_jd_skills,
    extract_resume_skills,
    round_score,
    safe_float,
    safe_int,
)


def score_resume_jd_match(
    resume: Mapping[str, Any] | None,
    jd: Mapping[str, Any] | str | None = None,
) -> tuple[float, dict[str, Any]]:
    resume_skills = extract_resume_skills(resume)
    jd_skills = extract_jd_skills(jd)

    if not resume_skills:
        return 0.0, {
            "resume_skills": [],
            "jd_skills": jd_skills,
            "matched_skills": [],
            "jd_missing": not bool(jd_skills),
        }

    if not jd_skills:
        return 40.0, {
            "resume_skills": resume_skills,
            "jd_skills": [],
            "matched_skills": resume_skills,
            "jd_missing": True,
        }

    resume_set = set(resume_skills)
    matched = sorted(skill for skill in jd_skills if skill in resume_set)
    score = (len(matched) / len(jd_skills)) * 40.0
    return round_score(score), {
        "resume_skills": resume_skills,
        "jd_skills": jd_skills,
        "matched_skills": matched,
        "jd_missing": False,
    }


def score_github(
    github: Mapping[str, Any] | None,
    jd: Mapping[str, Any] | str | None = None,
    coding: Mapping[str, Any] | None = None,
) -> tuple[float, dict[str, Any]]:
    gh = as_dict(github)
    if not gh:
        return 0.0, {"repo_count": 0, "activity": 0, "tech": [], "matched_tech": []}

    repo_count = safe_int(gh.get("repos") or gh.get("repo_count"))
    activity = safe_int(
        gh.get("last_30_day_commits")
        or gh.get("recent_commit_activity")
        or gh.get("activity")
        or gh.get("commits_30d")
    )
    tech = extract_github_tech(gh, coding)
    jd_skills = extract_jd_skills(jd)

    repo_score = min(repo_count, 20) / 20.0 * 8.0
    activity_score = min(activity, 60) / 60.0 * 6.0

    if jd_skills:
        matched_tech = sorted(skill for skill in jd_skills if skill in set(tech))
        tech_score = (len(matched_tech) / len(jd_skills)) * 6.0
    else:
        matched_tech = tech
        tech_score = min(len(tech), 6) / 6.0 * 6.0

    total = repo_score + activity_score + tech_score
    return round_score(total), {
        "repo_count": repo_count,
        "repo_score": round_score(repo_score),
        "activity": activity,
        "activity_score": round_score(activity_score),
        "tech": tech,
        "matched_tech": matched_tech,
        "tech_score": round_score(tech_score),
    }


def score_leetcode(leetcode: Mapping[str, Any] | None, coding: Mapping[str, Any] | None = None) -> tuple[float, dict[str, Any]]:
    lc = as_dict(leetcode)
    if not lc:
        return 0.0, {
            "total_solved": 0,
            "medium": 0,
            "hard": 0,
            "contest_rating": None,
            "contest_count": 0,
        }

    total_solved = safe_int(lc.get("total_solved") or lc.get("problems_solved"))
    medium = safe_int(lc.get("medium"))
    hard = safe_int(lc.get("hard"))
    contest_rating = safe_float(lc.get("contest_rating"))

    root = as_dict(coding)
    intelligence = as_dict(root.get("leetcode_intelligence"))
    contest_count = safe_int(intelligence.get("contest_participation_count") or lc.get("contest_participation_count"))

    solved_score = min(total_solved, 500) / 500.0 * 10.0
    difficulty_units = medium + (hard * 2)
    difficulty_score = min(difficulty_units, 250) / 250.0 * 5.0

    if contest_rating is not None:
        contest_score = clamp((contest_rating - 1200.0) / 800.0, 0.0, 1.0) * 5.0
    else:
        contest_score = min(contest_count, 10) / 10.0 * 5.0

    total = solved_score + difficulty_score + contest_score
    return round_score(total), {
        "total_solved": total_solved,
        "solved_score": round_score(solved_score),
        "medium": medium,
        "hard": hard,
        "difficulty_score": round_score(difficulty_score),
        "contest_rating": contest_rating,
        "contest_count": contest_count,
        "contest_score": round_score(contest_score),
    }


def score_academics(*sources: Mapping[str, Any] | None) -> tuple[float, dict[str, Any]]:
    cgpa = choose_cgpa(*sources)
    if cgpa is None:
        return 0.0, {"cgpa": None}
    score = clamp(cgpa / 10.0, 0.0, 1.0) * 20.0
    return round_score(score), {"cgpa": round_score(cgpa)}


def calculate_candidate_score(
    *,
    resume: Mapping[str, Any] | None = None,
    github: Mapping[str, Any] | None = None,
    leetcode: Mapping[str, Any] | None = None,
    academics: Mapping[str, Any] | None = None,
    coding: Mapping[str, Any] | None = None,
    jd: Mapping[str, Any] | str | None = None,
) -> dict[str, Any]:
    coding_data = as_dict(coding)
    github_data = as_dict(github) or as_dict(coding_data.get("github"))
    leetcode_data = as_dict(leetcode) or as_dict(coding_data.get("leetcode"))

    resume_score, resume_breakdown = score_resume_jd_match(resume, jd)
    github_score, github_breakdown = score_github(github_data, jd, coding_data)
    leetcode_score, leetcode_breakdown = score_leetcode(leetcode_data, coding_data)
    academic_score, academic_breakdown = score_academics(academics, resume)

    final_score = round_score(resume_score + github_score + leetcode_score + academic_score)
    return {
        "resume_score": resume_score,
        "github_score": github_score,
        "leetcode_score": leetcode_score,
        "academic_score": academic_score,
        "final_score": final_score,
        "breakdown": {
            "resume": resume_breakdown,
            "github": github_breakdown,
            "leetcode": leetcode_breakdown,
            "academics": academic_breakdown,
        },
    }

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Any


TECH_ALIASES = {
    "js": "javascript",
    "javascript": "javascript",
    "ts": "typescript",
    "typescript": "typescript",
    "node": "nodejs",
    "node.js": "nodejs",
    "nodejs": "nodejs",
    "react.js": "react",
    "reactjs": "react",
    "next.js": "nextjs",
    "nextjs": "nextjs",
    "postgres": "postgresql",
    "postgresql": "postgresql",
    "mongo": "mongodb",
    "mongodb": "mongodb",
    "py": "python",
    "python": "python",
}

COMMON_TECH_TERMS = {
    "python",
    "java",
    "javascript",
    "typescript",
    "react",
    "nextjs",
    "nodejs",
    "express",
    "fastapi",
    "django",
    "flask",
    "sql",
    "postgresql",
    "mysql",
    "mongodb",
    "redis",
    "docker",
    "kubernetes",
    "aws",
    "azure",
    "gcp",
    "git",
    "github",
    "html",
    "css",
    "tailwind",
    "machine learning",
    "deep learning",
    "data structures",
    "algorithms",
}


def as_dict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        dumped = value.model_dump()
        return dumped if isinstance(dumped, dict) else {}
    if isinstance(value, Mapping):
        return dict(value)
    return {}


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(float(value), high))


def round_score(value: float) -> float:
    rounded = round(value, 2)
    return int(rounded) if rounded.is_integer() else rounded


def safe_int(value: Any, default: int = 0) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        cleaned = value.strip().replace(",", "")
        if not cleaned:
            return default
        try:
            return int(float(cleaned))
        except ValueError:
            return default
    return default


def safe_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip().replace(",", ".")
        if not text:
            return None
        percent_match = re.search(r"(\d+(?:\.\d+)?)\s*%", text)
        if percent_match:
            try:
                return float(percent_match.group(1)) / 10.0
            except ValueError:
                return None
        number_match = re.search(r"(\d+(?:\.\d+)?)", text)
        if not number_match:
            return None
        try:
            return float(number_match.group(1))
        except ValueError:
            return None
    return None


def normalize_skill(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip().lower()
    if not text:
        return ""
    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9+#.\s-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip(" -")
    return TECH_ALIASES.get(text, text)


def unique_normalized(values: Iterable[Any]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        item = normalize_skill(value)
        if not item or item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def list_from_any(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple | set):
        return list(value)
    if isinstance(value, str):
        parts = re.split(r"[,;/|]", value)
        return [part.strip() for part in parts if part.strip()]
    return []


def extract_resume_skills(resume: Mapping[str, Any] | None) -> list[str]:
    data = as_dict(resume)
    skills: list[Any] = []
    skills.extend(list_from_any(data.get("skills")))

    for project in list_from_any(data.get("projects")):
        project_data = as_dict(project)
        skills.extend(list_from_any(project_data.get("tech_stack")))
        skills.extend(list_from_any(project_data.get("technologies")))

    for experience in list_from_any(data.get("experience")):
        exp_data = as_dict(experience)
        skills.extend(list_from_any(exp_data.get("tech_stack")))

    return unique_normalized(skills)


def extract_jd_skills(jd: Mapping[str, Any] | str | None) -> list[str]:
    if jd is None:
        return []
    if isinstance(jd, str):
        lowered = normalize_skill(jd)
        found = [term for term in COMMON_TECH_TERMS if re.search(rf"\b{re.escape(term)}\b", lowered)]
        return unique_normalized(found)

    data = as_dict(jd)
    skills: list[Any] = []
    for key in (
        "required_skills",
        "preferred_skills",
        "tools_and_technologies",
        "skills",
        "technologies",
        "key_traits",
    ):
        skills.extend(list_from_any(data.get(key)))
    return unique_normalized(skills)


def extract_github_tech(github: Mapping[str, Any] | None, coding: Mapping[str, Any] | None = None) -> list[str]:
    gh = as_dict(github)
    root = as_dict(coding)
    tech: list[Any] = []
    tech.extend(list_from_any(gh.get("languages")))

    repo_sources = list_from_any(root.get("repo_analysis"))
    repo_sources.extend(list_from_any(gh.get("repositories")))
    repo_sources.extend(list_from_any(gh.get("pinned_repositories")))
    for repo in repo_sources:
        repo_data = as_dict(repo)
        if repo_data:
            tech.extend(list_from_any(repo_data.get("tech_stack")))
            tech.extend(list_from_any(repo_data.get("languages")))
            tech.append(repo_data.get("language"))
            continue
        tech.append(repo)

    return unique_normalized(tech)


def choose_cgpa(*sources: Mapping[str, Any] | None) -> float | None:
    candidate_values: list[Any] = []
    for source in sources:
        data = as_dict(source)
        candidate_values.extend(
            [
                data.get("cgpa_computed"),
                data.get("cgpa"),
                data.get("cgpa_numeric"),
                data.get("final_cgpa"),
            ]
        )
        academics = as_dict(data.get("academics"))
        candidate_values.extend([academics.get("cgpa"), academics.get("cgpa_computed")])

    for raw in candidate_values:
        value = safe_float(raw)
        if value is None:
            continue
        if value > 10 and value <= 100:
            value = value / 10.0
        if 0 <= value <= 10:
            return value
    return None

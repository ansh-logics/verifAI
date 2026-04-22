"""
Indexing system for fast resume lookup.

Builds inverted index and document store from database.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any

from search_engine.utils import tokenize, normalize_token


@dataclass
class CandidateDocument:
    """Searchable candidate document."""

    candidate_id: int
    name: str
    email: str
    branch: str
    cgpa: float | None
    skills: list[str]
    github_languages: list[str]
    github_repos: list[str]
    projects: list[str]
    coding_score: float
    overall_score: float
    searchable_text: str
    github_username: str = ""
    leetcode_username: str = ""

    # Pre-computed tokens for this candidate
    tokens: set[str] = field(default_factory=set, init=False)

    def __post_init__(self):
        """Compute tokens after initialization."""
        self.tokens = set(tokenize(self.searchable_text))


class InvertedIndex:
    """Fast lookup structure: token -> list of candidate IDs."""

    def __init__(self):
        self.index: dict[str, set[int]] = {}
        self.documents: dict[int, CandidateDocument] = {}

    def add_document(self, doc: CandidateDocument) -> None:
        """Add a document to the index."""
        self.documents[doc.candidate_id] = doc

        # Index all tokens
        for token in doc.tokens:
            normalized = normalize_token(token)
            if normalized:
                if normalized not in self.index:
                    self.index[normalized] = set()
                self.index[normalized].add(doc.candidate_id)

    def lookup(self, token: str) -> set[int]:
        """Get all candidate IDs containing this token."""
        normalized = normalize_token(token)
        return self.index.get(normalized, set())

    def lookup_multiple(self, tokens: list[str]) -> dict[str, set[int]]:
        """Lookup multiple tokens at once."""
        return {token: self.lookup(token) for token in tokens}

    def get_document(self, candidate_id: int) -> CandidateDocument | None:
        """Get a candidate document by ID."""
        return self.documents.get(candidate_id)

    def get_all_tokens(self) -> set[str]:
        """Get all indexed tokens."""
        return set(self.index.keys())

    def size(self) -> tuple[int, int]:
        """Return (num_documents, num_unique_tokens)."""
        return len(self.documents), len(self.index)


def build_searchable_text(candidate_data: dict[str, Any]) -> str:
    """
    Build searchable text from candidate data.

    Combines name, skills, github languages, projects, etc.
    """
    parts = []

    # Name (weighted by including multiple times)
    if name := candidate_data.get("name"):
        parts.append(str(name).lower())

    # Email
    if email := candidate_data.get("email"):
        parts.append(str(email).lower())

    # GitHub Username
    if github_user := candidate_data.get("github_username"):
        parts.append(str(github_user).lower())

    # LeetCode Username
    if leetcode_user := candidate_data.get("leetcode_username"):
        parts.append(str(leetcode_user).lower())

    # Skills
    if skills := candidate_data.get("skills"):
        if isinstance(skills, list):
            parts.extend(str(s).lower() for s in skills)

    # GitHub languages
    if github_data := candidate_data.get("github_data"):
        if isinstance(github_data, dict):
            if languages := github_data.get("languages"):
                if isinstance(languages, list):
                    parts.extend(str(lang).lower() for lang in languages)
            if repos := github_data.get("repositories"):
                if isinstance(repos, list):
                    for repo in repos:
                        if isinstance(repo, dict):
                            if repo_name := repo.get("name"):
                                parts.append(str(repo_name).lower())
                            if tech_stack := repo.get("tech_stack"):
                                if isinstance(tech_stack, list):
                                    parts.extend(str(t).lower() for t in tech_stack)

    # Projects from resume
    if resume_data := candidate_data.get("resume_data"):
        if isinstance(resume_data, dict):
            if projects := resume_data.get("projects"):
                if isinstance(projects, list):
                    for project in projects:
                        if isinstance(project, dict):
                            if project_name := project.get("name"):
                                parts.append(str(project_name).lower())
                            if tech_stack := project.get("tech_stack"):
                                if isinstance(tech_stack, list):
                                    parts.extend(str(t).lower() for t in tech_stack)

    # Branch
    if branch := candidate_data.get("branch"):
        parts.append(str(branch).lower())

    # Phone (normalize to digits so +91 / hyphen formatting does not affect matching)
    if phone := candidate_data.get("phone"):
        phone_text = str(phone).strip()
        if phone_text:
            digits = re.sub(r"\D", "", phone_text)
            if digits:
                parts.append(digits)
                # Add local 10-digit variant for Indian numbers (+91XXXXXXXXXX)
                if digits.startswith("91") and len(digits) >= 12:
                    parts.append(digits[-10:])

    # Combine all
    return " ".join(parts)


def create_candidate_document(
    candidate_id: int,
    student_data: dict[str, Any],
    profile_data: dict[str, Any] | None = None,
) -> CandidateDocument:
    """
    Create a candidate document from student and profile data.

    Args:
        candidate_id: Student ID
        student_data: Student model data (name, email, branch, cgpa)
        profile_data: StudentProfile data (skills, scores, github_data, etc)

    Returns:
        CandidateDocument ready for indexing
    """
    profile = profile_data or {}

    # Extract data with defaults
    name = str(student_data.get("name", "")).strip()
    email = str(student_data.get("email", "")).strip()
    branch = str(student_data.get("branch", "")).strip()
    cgpa = student_data.get("cgpa")
    if cgpa is not None:
        cgpa = float(cgpa)

    skills = profile.get("skills", [])
    if not isinstance(skills, list):
        skills = []
    skills = [str(s).lower() for s in skills]

    github_data = profile.get("github_data", {})
    if not isinstance(github_data, dict):
        github_data = {}
    
    github_username = str(github_data.get("username", "")).strip()

    github_languages = github_data.get("languages", [])
    if not isinstance(github_languages, list):
        github_languages = []
    github_languages = [str(lang).lower() for lang in github_languages]

    github_repos = []
    if repos := github_data.get("repositories"):
        if isinstance(repos, list):
            for repo in repos:
                if isinstance(repo, dict) and (repo_name := repo.get("name")):
                    github_repos.append(str(repo_name).lower())

    leetcode_data = profile.get("leetcode_data", {})
    if not isinstance(leetcode_data, dict):
        leetcode_data = {}
    
    leetcode_username = str(leetcode_data.get("username", "")).strip()

    projects = []
    if resume_data := profile.get("resume_data"):
        if isinstance(resume_data, dict):
            if proj_list := resume_data.get("projects"):
                if isinstance(proj_list, list):
                    for proj in proj_list:
                        if isinstance(proj, dict) and (proj_name := proj.get("name")):
                            projects.append(str(proj_name).lower())

    coding_score = float(profile.get("coding_score", 0.0) or 0.0)
    overall_score = float(profile.get("overall_score", 0.0) or 0.0)

    searchable_text = build_searchable_text(
        {
            "name": name,
            "email": email,
            "github_username": github_username,
            "leetcode_username": leetcode_username,
            "branch": branch,
            "skills": skills,
            "github_data": github_data,
            "resume_data": profile.get("resume_data", {}),
        }
    )

    return CandidateDocument(
        candidate_id=candidate_id,
        name=name,
        email=email,
        branch=branch,
        cgpa=cgpa,
        skills=skills,
        github_languages=github_languages,
        github_repos=github_repos,
        github_username=github_username,
        leetcode_username=leetcode_username,
        projects=projects,
        coding_score=coding_score,
        overall_score=overall_score,
        searchable_text=searchable_text,
    )

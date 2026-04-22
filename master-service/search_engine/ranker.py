"""
Ranking and scoring system for search results.

Ranks candidates by relevance based on match quality.
"""

from __future__ import annotations

from dataclasses import dataclass

from search_engine.indexer import CandidateDocument


@dataclass
class ScoredResult:
    """Ranked search result."""

    candidate_id: int
    name: str
    email: str
    branch: str
    cgpa: float | None
    match_score: float
    overall_score: float
    matched_terms: list[str]
    match_quality: str  # "exact", "fuzzy", "mixed"


class ResultRanker:
    """Ranks and scores search results."""

    def __init__(
        self,
        skill_weight: float = 2.0,
        name_weight: float = 1.5,
        identity_weight: float = 5.0,
        project_weight: float = 1.0,
        github_weight: float = 0.8,
        score_boost_factor: float = 0.1,
    ):
        """
        Initialize ranker with weights.

        Args:
            skill_weight: Weight for matches in skills field
            name_weight: Weight for matches in name field
            identity_weight: Weight for exact identity matches (email, usernames)
            project_weight: Weight for matches in projects
            github_weight: Weight for matches in github
            score_boost_factor: Factor to boost by overall_score
        """
        self.skill_weight = skill_weight
        self.name_weight = name_weight
        self.identity_weight = identity_weight
        self.project_weight = project_weight
        self.github_weight = github_weight
        self.score_boost_factor = score_boost_factor

    def calculate_match_score(
        self, doc: CandidateDocument, matched_terms: set[str], query_tokens: list[str]
    ) -> float:
        """
        Calculate match relevance score.

        Args:
            doc: Candidate document
            matched_terms: Set of matched tokens (may include fuzzy with ~prefix)
            query_tokens: Original query tokens

        Returns:
            Match score (0-100)
        """
        if not matched_terms:
            return 0.0

        score = 0.0
        query_str = " ".join(query_tokens).lower()

        # Separate exact and fuzzy matches
        exact_matches = [t for t in matched_terms if not t.startswith("~")]
        fuzzy_matches = [t[1:] for t in matched_terms if t.startswith("~")]

        # 1. PRIMARY IDENTITY BOOST (Email, GitHub, LeetCode, Full Name)
        doc_email = doc.email.lower()
        doc_github = doc.github_username.lower()
        doc_leetcode = doc.leetcode_username.lower()
        doc_name = doc.name.lower()

        # Check for full query exact matches against identity fields
        if query_str == doc_email:
            score += 100.0  # Perfect match for email
        elif query_str == doc_github or query_str == doc_leetcode:
            score += 95.0   # Extremely high for username match
        elif query_str == doc_name:
            score += 90.0   # High for exact full name

        # 2. TOKEN-BASED SCORING
        if score < 100:
            # Bonus for number of distinct query terms matched
            unique_query_matched = sum(1 for qt in query_tokens if any(qt.lower() in str(em).lower() for em in exact_matches))
            score += unique_query_matched * 5

            # Field-specific scoring for each token
            for token in exact_matches:
                token_lower = token.lower()
                
                # Identity token match (partial email or username match)
                if token_lower == doc_email or token_lower == doc_github or token_lower == doc_leetcode:
                    score += self.identity_weight * 10
                
                # Name token match
                if token_lower in doc_name:
                    score += self.name_weight * 10

                # Skills match (skills are pre-lowered in indexer)
                if any(token_lower in skill for skill in doc.skills):
                    score += self.skill_weight * 10

                # GitHub languages match
                if any(token_lower in lang for lang in doc.github_languages):
                    score += self.github_weight * 7

                # Projects match
                if any(token_lower in proj for proj in doc.projects):
                    score += self.project_weight * 6

            # Fuzzy match penalty
            for token in fuzzy_matches:
                score += 2  # Small bonus for fuzzy matches

        # 3. OVERALL SCORE BOOST
        if doc.overall_score > 0:
            score_boost = (doc.overall_score / 100.0) * self.score_boost_factor * 10
            score += score_boost

        return min(score, 100.0)  # Cap at 100

    def determine_quality(self, matched_terms: set[str]) -> str:
        """Determine match quality based on term types."""
        has_exact = any(not t.startswith("~") for t in matched_terms)
        has_fuzzy = any(t.startswith("~") for t in matched_terms)

        if has_exact and has_fuzzy:
            return "mixed"
        elif has_exact:
            return "exact"
        else:
            return "fuzzy"

    def rank_results(
        self, candidates: dict[int, CandidateDocument], matched_terms: dict[int, set[str]], query_tokens: list[str]
    ) -> list[ScoredResult]:
        """
        Rank candidates by match relevance.

        Args:
            candidates: Dict of candidate_id -> CandidateDocument
            matched_terms: Dict of candidate_id -> set of matched terms
            query_tokens: Original query tokens

        Returns:
            Sorted list of ScoredResult (best matches first)
        """
        results = []

        for candidate_id, doc in candidates.items():
            terms = matched_terms.get(candidate_id, set())
            if not terms:
                continue

            match_score = self.calculate_match_score(doc, terms, query_tokens)
            quality = self.determine_quality(terms)

            # Clean up matched terms for output (remove ~ prefix)
            display_terms = sorted(
                [t[1:] if t.startswith("~") else t for t in terms], key=lambda x: not x.startswith("~")
            )

            results.append(
                ScoredResult(
                    candidate_id=candidate_id,
                    name=doc.name,
                    email=doc.email,
                    branch=doc.branch,
                    cgpa=doc.cgpa,
                    match_score=round(match_score, 2),
                    overall_score=round(doc.overall_score, 2),
                    matched_terms=display_terms,
                    match_quality=quality,
                )
            )

        # Sort by match score (descending), then by overall score (descending)
        results.sort(key=lambda r: (-r.match_score, -r.overall_score))

        return results

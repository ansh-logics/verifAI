"""
Main search service orchestrating index, match, and rank.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
import re
from typing import Any

from search_engine.indexer import InvertedIndex, create_candidate_document
from search_engine.matcher import QueryMatcher
from search_engine.ranker import ResultRanker, ScoredResult
from search_engine.utils import tokenize

logger = logging.getLogger(__name__)


@dataclass
class SearchQuery:
    """Search query parameters."""

    q: str
    min_score: float = 0.0
    min_cgpa: float | None = None
    branch: str | None = None
    limit: int = 50


@dataclass
class SearchResult:
    """Search result response."""

    query: str
    total_results: int
    results: list[dict[str, Any]]


class SearchService:
    """Main search service."""

    def __init__(self):
        """Initialize search service."""
        self.index = InvertedIndex()
        self.matcher = QueryMatcher(self.index)
        self.ranker = ResultRanker()
        self.initialized = False

    def is_indexed(self) -> bool:
        """Check if index is populated."""
        return self.initialized

    def index_candidates(self, candidates: list[dict[str, Any]]) -> int:
        """
        Index candidates for fast search.

        Args:
            candidates: List of candidate dicts with student and profile data
                       Expected keys: id, name, email, branch, cgpa, student_id, skills, github_data, etc.

        Returns:
            Number of candidates indexed
        """
        count = 0
        try:
            for candidate in candidates:
                try:
                    # Extract student and profile data
                    candidate_id = candidate.get("id") or candidate.get("student_id")
                    if not candidate_id:
                        logger.warning("Skipping candidate with no ID")
                        continue

                    # Create document
                    doc = create_candidate_document(
                        candidate_id=candidate_id,
                        student_data={
                            "name": candidate.get("name", ""),
                            "email": candidate.get("email", ""),
                            "phone": candidate.get("phone", ""),
                            "branch": candidate.get("branch", ""),
                            "cgpa": candidate.get("cgpa"),
                        },
                        profile_data={
                            "skills": candidate.get("skills", []),
                            "github_data": candidate.get("github_data", {}),
                            "leetcode_data": candidate.get("leetcode_data", {}),
                            "resume_data": candidate.get("resume_data", {}),
                            "coding_score": candidate.get("coding_score", 0.0),
                            "overall_score": candidate.get("overall_score", 0.0),
                        },
                    )

                    self.index.add_document(doc)
                    count += 1

                except Exception as e:
                    logger.error(f"Error indexing candidate {candidate.get('id')}: {e}")
                    continue

            self.initialized = True
            num_docs, num_tokens = self.index.size()
            logger.info(f"Indexed {num_docs} candidates with {num_tokens} unique tokens")

        except Exception as e:
            logger.error(f"Error indexing candidates: {e}")

        return count

    def search(self, query: SearchQuery) -> SearchResult:
        """
        Search for candidates.

        Args:
            query: SearchQuery with search parameters

        Returns:
            SearchResult with ranked candidates
        """
        if not query.q or not query.q.strip():
            return SearchResult(query=query.q, total_results=0, results=[])

        try:
            # Tokenize and normalize query
            query_tokens = tokenize(query.q)
            digits = re.sub(r"\D", "", query.q or "")
            if digits:
                query_tokens.append(digits)
                if digits.startswith("91") and len(digits) >= 12:
                    query_tokens.append(digits[-10:])
                elif len(digits) == 10:
                    query_tokens.append(f"91{digits}")
            if not query_tokens:
                return SearchResult(query=query.q, total_results=0, results=[])

            # Find matching candidates
            matched = self.matcher.find_candidates(query_tokens, allow_fuzzy=True)
            if not matched:
                return SearchResult(query=query.q, total_results=0, results=[])

            # Get candidate documents
            candidate_ids = set(matched.keys())
            candidates = self.matcher.get_candidate_documents(candidate_ids)

            # Apply filters
            filtered = self._apply_filters(candidates, query)

            # Rank results
            ranked = self.ranker.rank_results(filtered, matched, query_tokens)

            # Limit results
            ranked = ranked[: query.limit]

            # Convert to dict format
            results = [
                {
                    "candidate_id": r.candidate_id,
                    "name": r.name,
                    "email": r.email,
                    "branch": r.branch,
                    "cgpa": r.cgpa,
                    "match_score": r.match_score,
                    "overall_score": r.overall_score,
                    "matched_terms": r.matched_terms,
                    "match_quality": r.match_quality,
                }
                for r in ranked
            ]

            return SearchResult(query=query.q, total_results=len(results), results=results)

        except Exception as e:
            logger.error(f"Error searching: {e}")
            return SearchResult(query=query.q, total_results=0, results=[])

    def _apply_filters(
        self, candidates: dict[int, Any], query: SearchQuery
    ) -> dict[int, Any]:
        """Apply additional filters to candidates."""
        filtered = {}

        for cand_id, doc in candidates.items():
            # Min score filter
            if doc.overall_score < query.min_score:
                continue

            # Min CGPA filter
            if query.min_cgpa is not None and doc.cgpa is not None:
                if doc.cgpa < query.min_cgpa:
                    continue

            # Branch filter
            if query.branch and doc.branch.lower() != query.branch.lower():
                continue

            filtered[cand_id] = doc

        return filtered

    def clear_index(self) -> None:
        """Clear the index."""
        self.index = InvertedIndex()
        self.matcher = QueryMatcher(self.index)
        self.initialized = False

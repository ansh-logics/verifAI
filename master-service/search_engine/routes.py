"""
FastAPI routes for resume search.

NEW routes - does not modify any existing routes or code.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.models import Student, StudentProfile
from app.dependencies.auth import get_optional_bearer_token
from app.config import get_settings
from app.services.auth_service import AuthService
from search_engine.service import SearchQuery, SearchService

logger = logging.getLogger(__name__)

TPO_API_KEY = os.environ.get("TPO_API_KEY", "default-insecure-tpo-key")


def verify_tpo_access(
    token: str | None = Depends(get_optional_bearer_token),
    x_tpo_api_key: str | None = Header(None),
) -> None:
    settings = get_settings()
    if token:
        auth = AuthService(settings)
        try:
            payload = auth.decode_access_token(token)
        except ValueError:
            raise HTTPException(status_code=401, detail="Invalid or expired token.") from None
        if payload.get("role") != "tpo":
            raise HTTPException(status_code=403, detail="TPO access required.")
        return
    if settings.tpo_allow_api_key_fallback and x_tpo_api_key == (settings.tpo_api_key or TPO_API_KEY):
        return
    raise HTTPException(status_code=403, detail="Invalid or missing TPO credentials")

router = APIRouter(
    prefix="/search", 
    tags=["search"],
    dependencies=[Depends(verify_tpo_access)]
)

# Global search service instance
_search_service: SearchService | None = None


def get_search_service() -> SearchService:
    """Get or initialize search service."""
    global _search_service
    if _search_service is None:
        _search_service = SearchService()
    return _search_service


def _ensure_indexed(service: SearchService, db: Session) -> None:
    """Ensure search index is populated from database."""
    if service.is_indexed():
        return

    try:
        # Query all students with their profiles using a server-side cursor to prevent memory bloat
        students = db.query(Student, StudentProfile).outerjoin(StudentProfile).yield_per(1000)

        candidates = []
        for student, profile in students:
            candidate_data = {
                "id": student.id,
                "name": student.name,
                "email": student.email,
                "branch": student.branch,
                "cgpa": student.cgpa,
                "student_id": student.id,
            }

            if profile:
                candidate_data.update(
                    {
                        "skills": profile.skills or [],
                        "github_data": profile.github_data or {},
                        "resume_data": profile.resume_data or {},
                        "coding_score": profile.coding_score or 0.0,
                        "overall_score": profile.overall_score or 0.0,
                    }
                )
            else:
                candidate_data.update(
                    {
                        "skills": [],
                        "github_data": {},
                        "resume_data": {},
                        "coding_score": 0.0,
                        "overall_score": 0.0,
                    }
                )

            candidates.append(candidate_data)

        if candidates:
            count = service.index_candidates(candidates)
            logger.info(f"Indexed {count} candidates from database")

    except Exception as e:
        logger.error(f"Error building search index: {e}")
        raise


@router.post("/index")
async def trigger_reindex(db: Session = Depends(get_db)) -> dict[str, Any]:
    """
    Manually trigger search index rebuild.

    POST /search/index
    """
    service = get_search_service()
    service.clear_index()

    try:
        _ensure_indexed(service, db)
        num_docs, num_tokens = service.index.size()
        return {
            "status": "success",
            "message": f"Indexed {num_docs} candidates",
            "candidates": num_docs,
            "tokens": num_tokens,
        }
    except Exception as e:
        logger.error(f"Reindex failed: {e}")
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")


@router.get("/status")
async def search_status() -> dict[str, Any]:
    """
    Get search service status.

    GET /search/status
    """
    service = get_search_service()
    num_docs, num_tokens = service.index.size()
    return {
        "indexed": service.is_indexed(),
        "candidates": num_docs,
        "tokens": num_tokens,
    }


@router.get("")
async def search_candidates(
    q: str = Query(..., description="Search query (e.g., 'react node', 'python ml')"),
    min_score: float = Query(0.0, ge=0.0, le=100.0, description="Minimum overall score"),
    min_cgpa: float | None = Query(None, ge=0.0, le=10.0, description="Minimum CGPA"),
    branch: str | None = Query(None, description="Filter by branch"),
    limit: int = Query(50, ge=1, le=200, description="Max results to return"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Search for candidates by skills, name, or technologies.

    GET /search?q=react+node&min_score=60&limit=20

    Query Examples:
    - /search?q=react developer
    - /search?q=node mongodb
    - /search?q=python machine learning
    - /search?q=amit (name search)
    - /search?q=raect (fuzzy matching for typos)
    - /search?q=react&min_score=70
    - /search?q=python&branch=CSE
    """
    service = get_search_service()

    # Ensure index is populated
    try:
        _ensure_indexed(service, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search indexing failed: {str(e)}")

    # Execute search
    try:
        search_query = SearchQuery(
            q=q,
            min_score=min_score,
            min_cgpa=min_cgpa,
            branch=branch,
            limit=limit,
        )

        result = service.search(search_query)

        return {
            "query": result.query,
            "total_results": result.total_results,
            "results": result.results,
        }

    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/{candidate_id}/details")
async def get_candidate_details(
    candidate_id: int, db: Session = Depends(get_db)
) -> dict[str, Any]:
    """
    Get detailed information for a candidate.

    GET /search/{candidate_id}/details
    """
    result = db.query(Student, StudentProfile).outerjoin(StudentProfile).filter(Student.id == candidate_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Candidate not found")
        
    student, profile = result

    data = {
        "id": student.id,
        "name": student.name,
        "email": student.email,
        "roll_no": student.roll_no,
        "branch": student.branch,
        "cgpa": student.cgpa,
        "gender": student.gender,
        "created_at": student.created_at.isoformat() if student.created_at else None,
    }

    if profile:
        data.update(
            {
                "skills": profile.skills or [],
                "coding_score": profile.coding_score,
                "academic_score": profile.academic_score,
                "overall_score": profile.overall_score,
                "coding_persona": profile.coding_persona,
                "github_data": profile.github_data or {},
                "leetcode_data": profile.leetcode_data or {},
                "resume_data": profile.resume_data or {},
                "academic_data": profile.academic_data or {},
            }
        )

    return data

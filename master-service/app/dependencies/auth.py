from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import get_settings
from app.services.auth_service import AuthService

_bearer = HTTPBearer(auto_error=False)


def get_optional_bearer_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> str | None:
    if credentials is None or credentials.scheme.lower() != "bearer":
        return None
    return credentials.credentials


def get_current_student_id(
    token: Annotated[str | None, Depends(get_optional_bearer_token)],
) -> int:
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    auth = AuthService(get_settings())
    try:
        payload = auth.decode_access_token(token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid or expired token.") from None
    sub = payload.get("sub")
    if sub is None:
        raise HTTPException(status_code=401, detail="Invalid token payload.")
    try:
        return int(sub)
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token subject.")


def get_optional_student_id(
    token: Annotated[str | None, Depends(get_optional_bearer_token)],
) -> int | None:
    if not token:
        return None
    auth = AuthService(get_settings())
    try:
        payload = auth.decode_access_token(token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid or expired token.") from None
    sub = payload.get("sub")
    if sub is None:
        raise HTTPException(status_code=401, detail="Invalid token payload.")
    try:
        return int(sub)
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token subject.")


def get_current_tpo_user(
    token: Annotated[str | None, Depends(get_optional_bearer_token)],
) -> str:
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    auth = AuthService(get_settings())
    try:
        payload = auth.decode_access_token(token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid or expired token.") from None
    if payload.get("role") != "tpo":
        raise HTTPException(status_code=403, detail="TPO access required.")
    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject.strip():
        raise HTTPException(status_code=401, detail="Invalid token subject.")
    return subject.strip()

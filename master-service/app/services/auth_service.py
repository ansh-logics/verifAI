from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from jwt.exceptions import PyJWTError
from passlib.context import CryptContext

from app.config import Settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, password_hash: str) -> bool:
        if not password_hash:
            return False
        return pwd_context.verify(plain_password, password_hash)

    def create_access_token(self, *, student_id: int, email: str, roll_no: str | None) -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=self.settings.auth_access_token_expire_minutes)
        payload: dict[str, Any] = {
            "sub": str(student_id),
            "email": email,
            "roll_no": roll_no,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
        }
        return jwt.encode(payload, self.settings.auth_jwt_secret, algorithm=self.settings.auth_jwt_algorithm)

    def create_tpo_access_token(self, *, username: str) -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=self.settings.tpo_access_token_expire_minutes)
        payload: dict[str, Any] = {
            "sub": username,
            "role": "tpo",
            "exp": expire,
            "iat": datetime.now(timezone.utc),
        }
        return jwt.encode(payload, self.settings.auth_jwt_secret, algorithm=self.settings.auth_jwt_algorithm)

    def decode_access_token(self, token: str) -> dict[str, Any]:
        try:
            return jwt.decode(
                token,
                self.settings.auth_jwt_secret,
                algorithms=[self.settings.auth_jwt_algorithm],
            )
        except PyJWTError as exc:
            raise ValueError("Invalid or expired token.") from exc

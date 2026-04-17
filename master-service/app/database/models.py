from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class Student(Base):
    __tablename__ = "students"
    __table_args__ = (Index("ix_students_roll_no_lookup", "roll_no"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    roll_no: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    branch: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    cgpa: Mapped[float | None] = mapped_column(Float, nullable=True)
    gender: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    cgpa_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    profile: Mapped["StudentProfile | None"] = relationship(
        back_populates="student",
        uselist=False,
        cascade="all, delete-orphan",
    )
    raw_uploads: Mapped[list["RawUpload"]] = relationship(
        back_populates="student",
        cascade="all, delete-orphan",
    )


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), unique=True, nullable=False)
    skills: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    coding_persona: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    coding_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    academic_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    github_data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    leetcode_data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    resume_data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    academic_data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    # Optional JSON mirror helps portability when ARRAY consumers are limited.
    skills_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    last_analyzed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    student: Mapped[Student] = relationship(back_populates="profile")

    __table_args__ = (
        Index("ix_student_profiles_skills_gin", "skills", postgresql_using="gin"),
    )


class RawUpload(Base):
    __tablename__ = "raw_uploads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    resume_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    marksheet_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    student: Mapped[Student] = relationship(back_populates="raw_uploads")


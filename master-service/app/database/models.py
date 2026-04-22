from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Student(Base):
    __tablename__ = "students"

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
    has_active_backlog: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
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
    placements: Mapped[list["PlacementRecord"]] = relationship(
        back_populates="student",
        cascade="all, delete-orphan",
    )
    tpo_group_memberships: Mapped[list["TpoAnalysisGroupMember"]] = relationship(
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
    # JSON mirror of skills for compatibility with consumers that don't support ARRAY well.
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

    __table_args__ = (
        Index("ix_raw_uploads_student_uploaded", "student_id", "uploaded_at", "id"),
    )


class PlacementRecord(Base):
    __tablename__ = "placement_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    offer_type: Mapped[str] = mapped_column(String(32), nullable=False)  # internship or job
    pay_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    student: Mapped[Student] = relationship(back_populates="placements")


class TpoAnalysisGroup(Base):
    __tablename__ = "tpo_analysis_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    jd_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    pay_or_stipend: Mapped[str | None] = mapped_column(String(128), nullable=True)
    duration: Mapped[str | None] = mapped_column(String(128), nullable=True)
    bond_details: Mapped[str | None] = mapped_column(Text, nullable=True)
    jd_topics: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    jd_key_points: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    interview_timezone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_by: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    members: Mapped[list["TpoAnalysisGroupMember"]] = relationship(
        back_populates="group",
        cascade="all, delete-orphan",
    )
    mail_jobs: Mapped[list["TpoMailJob"]] = relationship(
        back_populates="group",
        cascade="all, delete-orphan",
    )


class TpoAnalysisGroupMember(Base):
    __tablename__ = "tpo_analysis_group_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("tpo_analysis_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    group: Mapped[TpoAnalysisGroup] = relationship(back_populates="members")
    student: Mapped[Student] = relationship(back_populates="tpo_group_memberships")


class TpoSettings(Base):
    __tablename__ = "tpo_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tpo_username: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)

    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    institute_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    sender_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reply_to_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    default_timezone: Mapped[str | None] = mapped_column(String(64), nullable=True)

    stale_group_reminder_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    daily_queue_summary_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    placement_update_confirmation_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    tpo_password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class TpoMailJob(Base):
    __tablename__ = "tpo_mail_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("tpo_analysis_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    requested_by: Mapped[str] = mapped_column(String(128), nullable=False)
    mail_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued", index=True)
    total_recipients: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    processed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    success_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    group: Mapped[TpoAnalysisGroup] = relationship(back_populates="mail_jobs")


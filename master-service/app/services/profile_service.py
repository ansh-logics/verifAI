from __future__ import annotations

import logging
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.database.models import RawUpload, Student, StudentProfile
from app.schemas.student import (
    AcademicsData,
    AuthTokenResponse,
    CodingData,
    LoginRequest,
    RegisterRequest,
    StudentData,
    StudentProfileCreate,
    StudentProfileResponse,
    StudentProfileStoreResponse,
)
from app.services.auth_service import AuthService
from app.services.master_service import normalize_skills

logger = logging.getLogger(__name__)


class ProfileService:
    def __init__(self, db: Session, auth_service: AuthService | None = None) -> None:
        self.db = db
        self.auth_service = auth_service

    @staticmethod
    def _looks_like_email(identifier: str) -> bool:
        return "@" in identifier and "." in identifier.split("@")[-1]

    def register_student(self, payload: RegisterRequest) -> Student:
        duplicate = self.db.query(Student).filter(Student.email == payload.email).one_or_none()
        if duplicate:
            raise HTTPException(
                status_code=409,
                detail={
                    "message": "Account already exists with this email.",
                    "code": "duplicate_email",
                    "student_id": duplicate.id,
                },
            )

        if self.auth_service is None:
            raise HTTPException(status_code=500, detail="Auth service unavailable.")

        student = Student(
            name=payload.email.split("@")[0],
            email=payload.email,
            roll_no=payload.roll_no,
            password_hash=self.auth_service.hash_password(payload.password),
            phone=payload.phone,
            branch=payload.branch,
            cgpa=payload.cgpa,
            gender=payload.gender,
            cgpa_verified=True,
        )
        self.db.add(student)
        self.db.commit()
        self.db.refresh(student)
        return student

    def login_student(self, payload: LoginRequest) -> AuthTokenResponse:
        if self.auth_service is None:
            raise HTTPException(status_code=500, detail="Auth service unavailable.")

        identifier = payload.identifier.strip()
        if self._looks_like_email(identifier):
            student = self.db.query(Student).filter(Student.email == identifier.lower()).one_or_none()
        else:
            student = self.db.query(Student).filter(Student.roll_no == identifier.upper()).one_or_none()

        if student is None or not self.auth_service.verify_password(payload.password, student.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials.")

        token = self.auth_service.create_access_token(
            student_id=student.id,
            email=student.email,
            roll_no=student.roll_no,
        )
        return AuthTokenResponse(
            access_token=token,
            student_id=student.id,
            email=student.email,
            roll_no=student.roll_no,
        )

    def save_profile(
        self,
        payload: StudentProfileCreate,
        *,
        requesting_student_id: int | None = None,
    ) -> StudentProfileStoreResponse:
        student = self.db.query(Student).filter(Student.email == payload.student.email).one_or_none()
        if student is None:
            student = Student(
                name=payload.student.name,
                email=payload.student.email,
                roll_no=payload.student.roll_no,
                password_hash="",
                phone=payload.student.phone,
                branch=payload.student.branch,
                cgpa=payload.student.cgpa,
                gender=payload.student.gender,
                cgpa_verified=payload.student.cgpa_verified,
            )
            self.db.add(student)
            self.db.flush()
        else:
            if student.password_hash and requesting_student_id != student.id:
                raise HTTPException(
                    status_code=403,
                    detail="This account is registered. Log in to update your profile.",
                )
            student.name = payload.student.name
            student.phone = payload.student.phone
            student.branch = payload.student.branch
            student.cgpa = payload.student.cgpa
            student.gender = payload.student.gender
            student.cgpa_verified = payload.student.cgpa_verified
            if payload.student.roll_no:
                student.roll_no = payload.student.roll_no

        profile = self.db.query(StudentProfile).filter(StudentProfile.student_id == student.id).one_or_none()
        skills = normalize_skills(payload.skills)
        resume_data = payload.resume_data or {}
        academic_data = payload.academic_data or {}
        if profile is not None:
            existing_resume_name = (profile.resume_data or {}).get("file_name")
            existing_academic_name = (profile.academic_data or {}).get("file_name")
            if existing_resume_name and not resume_data.get("file_name"):
                resume_data = {**resume_data, "file_name": existing_resume_name}
            if existing_academic_name and not academic_data.get("file_name"):
                academic_data = {**academic_data, "file_name": existing_academic_name}
        if profile is None:
            profile = StudentProfile(
                student_id=student.id,
                skills=skills,
                skills_json=skills,
                coding_persona=payload.coding.persona,
                coding_score=payload.coding.score,
                academic_score=payload.academics.score,
                overall_score=payload.overall_score,
                github_data=payload.github_data,
                leetcode_data=payload.leetcode_data,
                resume_data=resume_data,
                academic_data=academic_data,
                last_analyzed_at=datetime.now(UTC),
            )
            self.db.add(profile)
            self.db.flush()
        else:
            profile.skills = skills
            profile.skills_json = skills
            profile.coding_persona = payload.coding.persona
            profile.coding_score = payload.coding.score
            profile.academic_score = payload.academics.score
            profile.overall_score = payload.overall_score
            profile.github_data = payload.github_data
            profile.leetcode_data = payload.leetcode_data
            profile.resume_data = resume_data
            profile.academic_data = academic_data
            profile.last_analyzed_at = datetime.now(UTC)

        if payload.resume_url or payload.marksheet_url:
            raw_upload = RawUpload(
                student_id=student.id,
                resume_url=payload.resume_url,
                marksheet_url=payload.marksheet_url,
            )
            self.db.add(raw_upload)

        self.db.commit()
        logger.info("Stored profile for student_id=%s email=%s", student.id, student.email)
        return StudentProfileStoreResponse(student_id=student.id, profile_id=profile.id)

    def get_profile(self, student_id: int) -> StudentProfileResponse:
        profile = self.db.query(StudentProfile).filter(StudentProfile.student_id == student_id).one_or_none()
        if profile is None:
            raise HTTPException(status_code=404, detail="Profile not found.")

        student = profile.student
        if student is None:
            raise HTTPException(status_code=500, detail="Profile exists without student record.")

        latest_upload = (
            self.db.query(RawUpload)
            .filter(RawUpload.student_id == student_id)
            .order_by(RawUpload.uploaded_at.desc(), RawUpload.id.desc())
            .one_or_none()
        )

        return StudentProfileResponse(
            id=profile.id,
            student_id=student.id,
            student=StudentData(
                name=student.name,
                email=student.email,
                roll_no=student.roll_no,
                phone=student.phone,
                branch=student.branch,
                cgpa=student.cgpa,
                gender=student.gender,
                cgpa_verified=student.cgpa_verified,
            ),
            skills=profile.skills or [],
            coding=CodingData(
                persona=profile.coding_persona,
                score=profile.coding_score,
                github=profile.github_data or {},
                leetcode=profile.leetcode_data or {},
            ),
            academics=AcademicsData(
                cgpa=student.cgpa,
                verified=student.cgpa_verified,
                score=profile.academic_score,
            ),
            overall_score=profile.overall_score,
            resume_url=latest_upload.resume_url if latest_upload else None,
            resume_data=profile.resume_data or {},
            academic_data=profile.academic_data or {},
            github_data=profile.github_data or {},
            leetcode_data=profile.leetcode_data or {},
            last_analyzed_at=profile.last_analyzed_at,
            created_at=student.created_at,
        )


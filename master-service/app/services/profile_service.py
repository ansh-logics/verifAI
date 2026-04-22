from __future__ import annotations

import logging
import re
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.database.models import PlacementRecord, RawUpload, Student, StudentProfile, TpoAnalysisGroup, TpoAnalysisGroupMember
from app.schemas.student import (
    AcademicsData,
    AuthTokenResponse,
    CodingData,
    LoginRequest,
    PlacementInfo,
    RegisterRequest,
    StudentData,
    StudentProfileCreate,
    StudentProfileResponse,
    StudentProfileStoreResponse,
)
from app.services.auth_service import AuthService
from app.services.master_service import normalize_skills

logger = logging.getLogger(__name__)
PHONE_REGEX = re.compile(r"^[0-9+\-\s()]{7,20}$")
ROLL_REGEX = re.compile(r"^[A-Z0-9][A-Z0-9\-_/]{2,63}$")


class ProfileService:
    def __init__(self, db: Session, auth_service: AuthService | None = None) -> None:
        self.db = db
        self.auth_service = auth_service

    @staticmethod
    def _normalize_handle(value: str | None) -> str | None:
        if value is None:
            return None
        v = value.strip().lower()
        return v or None

    @staticmethod
    def _extract_handle_from_blob(blob: dict[str, object] | None) -> str | None:
        if not isinstance(blob, dict):
            return None
        for key in ("username", "handle", "login", "user"):
            raw = blob.get(key)
            if isinstance(raw, str) and raw.strip():
                return ProfileService._normalize_handle(raw)
        return None

    @staticmethod
    def _extract_platform_handle(payload: StudentProfileCreate, platform: str) -> str | None:
        primary = payload.github_data if platform == "github" else payload.leetcode_data
        candidates: list[dict[str, object]] = []
        if isinstance(primary, dict):
            candidates.append(primary)
        coding_blob = payload.coding.github if platform == "github" else payload.coding.leetcode
        if isinstance(coding_blob, dict):
            candidates.append(coding_blob)
        for blob in candidates:
            found = ProfileService._extract_handle_from_blob(blob)
            if found:
                return found
        return None

    @staticmethod
    def _extract_github_profile_name(payload: StudentProfileCreate) -> str | None:
        candidates: list[dict[str, object]] = []
        if isinstance(payload.github_data, dict):
            candidates.append(payload.github_data)
        if isinstance(payload.coding.github, dict):
            candidates.append(payload.coding.github)
        for blob in candidates:
            for key in ("name", "full_name"):
                raw = blob.get(key)
                if isinstance(raw, str) and raw.strip():
                    return raw.strip()
        return None

    @staticmethod
    def _names_compatible(registered_name: str, external_name: str) -> bool:
        reg_tokens = {token for token in re.findall(r"[a-z0-9]+", registered_name.lower()) if len(token) >= 2}
        ext_tokens = {token for token in re.findall(r"[a-z0-9]+", external_name.lower()) if len(token) >= 2}
        if not reg_tokens or not ext_tokens:
            return True
        return bool(reg_tokens.intersection(ext_tokens))

    @staticmethod
    def _assert_github_name_matches_registered(student: Student, payload: StudentProfileCreate) -> None:
        github_name = ProfileService._extract_github_profile_name(payload)
        if not github_name:
            return
        if not ProfileService._names_compatible(student.name, github_name):
            raise HTTPException(
                status_code=400,
                detail="GitHub profile name does not match the registered account name.",
            )

    def _assert_unique_coding_handles(self, student_id: int, payload: StudentProfileCreate) -> None:
        github_handle = self._extract_platform_handle(payload, "github")
        leetcode_handle = self._extract_platform_handle(payload, "leetcode")
        if not github_handle and not leetcode_handle:
            return
        profiles = (
            self.db.query(StudentProfile)
            .filter(StudentProfile.student_id != student_id)
            .all()
        )
        for profile in profiles:
            existing_github = self._extract_handle_from_blob(profile.github_data if isinstance(profile.github_data, dict) else {})
            existing_leetcode = self._extract_handle_from_blob(profile.leetcode_data if isinstance(profile.leetcode_data, dict) else {})
            if github_handle and existing_github and github_handle == existing_github:
                raise HTTPException(
                    status_code=400,
                    detail="This GitHub account is already linked to another student profile.",
                )
            if leetcode_handle and existing_leetcode and leetcode_handle == existing_leetcode:
                raise HTTPException(
                    status_code=400,
                    detail="This LeetCode account is already linked to another student profile.",
                )

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
            name=payload.name,
            email=payload.email,
            roll_no=None,
            password_hash=self.auth_service.hash_password(payload.password),
            phone=payload.phone,
            branch="Unknown",
            cgpa=None,
            gender="other",
            cgpa_verified=False,
        )
        self.db.add(student)
        self.db.commit()
        self.db.refresh(student)
        return student

    @staticmethod
    def _extract_identity_candidates(payload: StudentProfileCreate) -> dict[str, str]:
        buckets = [payload.resume_data or {}, payload.academic_data or {}]
        key_map = {
            "name": ["name", "full_name", "candidate_name", "student_name"],
            "email": ["email", "mail"],
            "phone": ["phone", "mobile", "contact", "phone_number"],
            "roll_no": ["roll_no", "roll", "roll_number", "enrollment_no", "enrollment"],
        }
        out: dict[str, str] = {}
        for canonical, keys in key_map.items():
            for blob in buckets:
                if not isinstance(blob, dict):
                    continue
                for key in keys:
                    raw = blob.get(key)
                    if isinstance(raw, str) and raw.strip():
                        out[canonical] = raw.strip()
                        break
                if canonical in out:
                    break
        return out

    @staticmethod
    def _assert_identity_and_anomalies(student: Student, payload: StudentProfileCreate) -> None:
        submitted = payload.student
        if submitted.email.strip().lower() != student.email.strip().lower():
            raise HTTPException(status_code=400, detail="Email mismatch with registered account.")
        if submitted.name.strip().lower() != student.name.strip().lower():
            raise HTTPException(status_code=400, detail="Name mismatch with registered account.")
        if submitted.phone.strip() != student.phone.strip():
            raise HTTPException(status_code=400, detail="Phone mismatch with registered account.")
        if not submitted.roll_no:
            raise HTTPException(status_code=400, detail="roll_no is required before saving profile.")
        if not ROLL_REGEX.match(submitted.roll_no):
            raise HTTPException(status_code=400, detail="Invalid roll number format.")
        if not PHONE_REGEX.match(submitted.phone):
            raise HTTPException(status_code=400, detail="Invalid phone format.")
        if submitted.cgpa is not None and (submitted.cgpa < 0 or submitted.cgpa > 10):
            raise HTTPException(status_code=400, detail="CGPA must be between 0 and 10.")
        extracted = ProfileService._extract_identity_candidates(payload)
        if extracted.get("name") and extracted["name"].strip().lower() != student.name.strip().lower():
            raise HTTPException(status_code=400, detail="Resume/marksheet name does not match registered name.")
        if extracted.get("email") and extracted["email"].strip().lower() != student.email.strip().lower():
            raise HTTPException(status_code=400, detail="Resume/marksheet email does not match registered email.")
        if extracted.get("phone") and extracted["phone"].strip() != student.phone.strip():
            raise HTTPException(status_code=400, detail="Resume/marksheet phone does not match registered phone.")
        if extracted.get("roll_no") and submitted.roll_no and extracted["roll_no"].strip().upper() != submitted.roll_no.strip().upper():
            raise HTTPException(status_code=400, detail="Resume/marksheet roll number does not match provided roll number.")

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
            raise HTTPException(status_code=400, detail="No registered account found. Register first.")
        else:
            if student.password_hash and requesting_student_id != student.id:
                raise HTTPException(
                    status_code=403,
                    detail="This account is registered. Log in to update your profile.",
                )
            self._assert_identity_and_anomalies(student, payload)
            self._assert_github_name_matches_registered(student, payload)
            self._assert_unique_coding_handles(student.id, payload)
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

        has_file_metadata = bool((resume_data or {}).get("file_name") or (academic_data or {}).get("file_name"))
        if payload.resume_url or payload.marksheet_url or has_file_metadata:
            latest_upload = (
                self.db.query(RawUpload)
                .filter(RawUpload.student_id == student.id)
                .order_by(RawUpload.uploaded_at.desc(), RawUpload.id.desc())
                .first()
            )
            resolved_resume_url = payload.resume_url or (latest_upload.resume_url if latest_upload else None)
            resolved_marksheet_url = payload.marksheet_url or (latest_upload.marksheet_url if latest_upload else None)
            raw_upload = RawUpload(
                student_id=student.id,
                resume_url=resolved_resume_url,
                marksheet_url=resolved_marksheet_url,
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
            .first()
        )

        active_placement = (
            self.db.query(PlacementRecord)
            .filter(PlacementRecord.student_id == student_id, PlacementRecord.is_active.is_(True))
            .order_by(PlacementRecord.updated_at.desc(), PlacementRecord.id.desc())
            .first()
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
            placement=PlacementInfo(
                company_name=active_placement.company_name,
                offer_type=active_placement.offer_type,
                pay_amount=active_placement.pay_amount,
                notes=active_placement.notes,
                is_active=active_placement.is_active,
                created_at=active_placement.created_at,
                updated_at=active_placement.updated_at,
            )
            if active_placement
            else None,
        )

    def create_tpo_analysis_group(
        self,
        *,
        title: str,
        jd_summary: str | None,
        company_name: str | None,
        role_type: str | None,
        pay_or_stipend: str | None,
        duration: str | None,
        bond_details: str | None,
        jd_topics: list[str],
        jd_key_points: list[str],
        interview_timezone: str | None,
        student_ids: list[int],
        created_by: str,
    ) -> TpoAnalysisGroup:
        summary = (jd_summary or "").strip() or None
        inferred_company = (company_name or "").strip() or None
        if inferred_company is None and summary:
            lowered = summary.lower()
            for marker in ("company:", "organization:", "employer:"):
                idx = lowered.find(marker)
                if idx >= 0:
                    tail = summary[idx + len(marker) :].strip()
                    inferred_company = tail.splitlines()[0].strip(" .,-")[:255] or None
                    break
        group = TpoAnalysisGroup(
            title=title.strip(),
            jd_summary=summary,
            company_name=inferred_company,
            role_type=(role_type or "").strip() or None,
            pay_or_stipend=(pay_or_stipend or "").strip() or None,
            duration=(duration or "").strip() or None,
            bond_details=(bond_details or "").strip() or None,
            jd_topics=[topic.strip() for topic in jd_topics if isinstance(topic, str) and topic.strip()],
            jd_key_points=[point.strip() for point in jd_key_points if isinstance(point, str) and point.strip()],
            interview_timezone=(interview_timezone or "").strip() or None,
            created_by=created_by,
        )
        self.db.add(group)
        self.db.flush()
        deduped_ids = sorted({sid for sid in student_ids if sid > 0})
        for sid in deduped_ids:
            member = TpoAnalysisGroupMember(group_id=group.id, student_id=sid)
            self.db.add(member)
        self.db.commit()
        self.db.refresh(group)
        return group

    def list_tpo_analysis_groups(self) -> list[TpoAnalysisGroup]:
        return (
            self.db.query(TpoAnalysisGroup)
            .order_by(TpoAnalysisGroup.created_at.desc(), TpoAnalysisGroup.id.desc())
            .all()
        )

    def delete_tpo_analysis_group(self, group_id: int) -> None:
        group = self.db.query(TpoAnalysisGroup).filter(TpoAnalysisGroup.id == group_id).one_or_none()
        if group is None:
            raise HTTPException(status_code=404, detail="Group not found.")
        self.db.delete(group)
        self.db.commit()

    def mark_student_placement(
        self,
        *,
        student_id: int,
        group_id: int | None,
        company_name: str | None,
        offer_type: str | None,
        pay_amount: float | None,
        notes: str | None,
    ) -> PlacementRecord:
        student = self.db.query(Student).filter(Student.id == student_id).one_or_none()
        if student is None:
            raise HTTPException(status_code=404, detail="Student not found.")
        group_company_name: str | None = None
        group_role_type: str | None = None
        if group_id is not None:
            group = self.db.query(TpoAnalysisGroup).filter(TpoAnalysisGroup.id == group_id).one_or_none()
            if group is None:
                raise HTTPException(status_code=404, detail="Group not found.")
            group_company_name = (group.company_name or "").strip() or None
            group_role_type = (group.role_type or "").strip().lower() or None
            if group_company_name is None:
                raise HTTPException(status_code=400, detail="Group company is missing. Recreate group with company context.")

        resolved_company = group_company_name or ((company_name or "").strip() or None)
        if resolved_company is None:
            raise HTTPException(status_code=400, detail="company_name is required.")
        resolved_offer_type = group_role_type or ((offer_type or "").strip().lower() or None)
        if resolved_offer_type not in {"internship", "job"}:
            raise HTTPException(status_code=400, detail="offer_type must be internship or job.")

        student_record = (
            self.db.query(PlacementRecord)
            .filter(PlacementRecord.student_id == student_id, PlacementRecord.is_active.is_(True))
            .one_or_none()
        )
        if student_record is None:
            student_record = PlacementRecord(
                student_id=student_id,
                company_name=resolved_company,
                offer_type=resolved_offer_type,
                pay_amount=pay_amount,
                notes=(notes or "").strip() or None,
                is_active=True,
            )
            self.db.add(student_record)
        else:
            student_record.company_name = resolved_company
            student_record.offer_type = resolved_offer_type
            student_record.pay_amount = pay_amount
            student_record.notes = (notes or "").strip() or None
            student_record.updated_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(student_record)
        return student_record


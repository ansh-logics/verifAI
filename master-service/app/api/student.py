from __future__ import annotations

import logging
import json
import smtplib
from datetime import datetime, timezone
from pathlib import Path

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session
from starlette.datastructures import UploadFile as StarletteUploadFile

from app.config import get_settings
from app.database.database import SessionLocal, get_db
from app.database.models import (
    PlacementRecord,
    RawUpload,
    Student,
    StudentProfile,
    TpoAnalysisGroup,
    TpoMailJob,
    TpoSettings,
)
from app.dependencies.auth import get_current_student_id, get_current_tpo_user, get_optional_student_id
from app.schemas.student import (
    AuthTokenResponse,
    JDMatchRequest,
    JDMatchResponse,
    LoginRequest,
    RegisterRequest,
    RegisterResponse,
    StudentAnalyzeResponse,
    StudentProfileCreate,
    StudentProfileResponse,
    StudentProfileStoreResponse,
    PlacementMarkRequest,
    TpoAuthTokenResponse,
    TpoGroupCreateRequest,
    TpoGroupMemberInfo,
    TpoGroupResponse,
    TpoOverviewRecentPlacement,
    TpoOverviewResponse,
    TpoPasswordChangeRequest,
    TpoSettingsData,
    TpoSettingsResponse,
    TpoMailActionRequest,
    TpoMailActionResponse,
    TpoMailJobProgressResponse,
    TpoLoginRequest,
)
from app.services.auth_service import AuthService
from app.services.downstream import DEFAULT_HEADERS, call_jd_analyzer
from app.services.jd_file_parser import ALLOWED_JD_EXTENSIONS, extract_jd_text_from_file
from app.services.master_service import analyze_student_profile, analyze_student_profile_incremental
from app.services.matching_service import run_jd_matching
from app.services.profile_service import ProfileService
from app.services.mail_service import MailService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/student", tags=["student"])

ALLOWED_RESUME_EXTENSIONS = {".pdf", ".docx"}
ALLOWED_MARKSHEET_EXTENSIONS = {".pdf"}
MAX_FILE_BYTES = 8 * 1024 * 1024
def _upsert_tpo_settings_defaults(db: Session, tpo_username: str) -> TpoSettings:
    settings = db.query(TpoSettings).filter(TpoSettings.tpo_username == tpo_username).one_or_none()
    if settings is not None:
        return settings
    settings = TpoSettings(
        tpo_username=tpo_username,
        display_name=tpo_username,
        sender_name=tpo_username,
        default_timezone="Asia/Kolkata",
    )
    db.add(settings)
    db.commit()
    db.refresh(settings)
    return settings


def _validate_new_password(new_password: str) -> None:
    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters.")
    has_alpha = any(ch.isalpha() for ch in new_password)
    has_digit = any(ch.isdigit() for ch in new_password)
    if not (has_alpha and has_digit):
        raise HTTPException(status_code=400, detail="New password must include both letters and numbers.")




def _first_non_empty_str(*values: object) -> str | None:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _normalize_group_metadata(payload: TpoGroupCreateRequest) -> dict[str, str | None]:
    summary = payload.jd_summary or ""
    company_name = _first_non_empty_str(payload.company_name)
    role_type = _first_non_empty_str(payload.role_type)
    pay_or_stipend = _first_non_empty_str(payload.pay_or_stipend)
    duration = _first_non_empty_str(payload.duration)
    bond_details = _first_non_empty_str(payload.bond_details)

    if pay_or_stipend is None:
        pay_or_stipend = _first_non_empty_str(
            payload.model_extra.get("stipend") if payload.model_extra else None,
            payload.model_extra.get("salary") if payload.model_extra else None,
            payload.model_extra.get("ctc") if payload.model_extra else None,
        )
    if bond_details is None:
        bond_details = _first_non_empty_str(
            payload.model_extra.get("bond") if payload.model_extra else None,
            payload.model_extra.get("service_agreement") if payload.model_extra else None,
        )
    if duration is None:
        duration = _first_non_empty_str(
            payload.model_extra.get("internship_duration") if payload.model_extra else None,
            payload.model_extra.get("tenure") if payload.model_extra else None,
        )
    if role_type is None and summary:
        lowered = summary.lower()
        if "intern" in lowered:
            role_type = "internship"
        elif "full time" in lowered or "job" in lowered:
            role_type = "job"

    return {
        "company_name": company_name,
        "role_type": role_type,
        "pay_or_stipend": pay_or_stipend,
        "duration": duration,
        "bond_details": bond_details,
    }


def _active_placement_for_student(student: Student) -> PlacementRecord | None:
    active = [record for record in getattr(student, "placements", []) if record.is_active]
    if not active:
        return None
    active.sort(key=lambda item: (item.updated_at, item.id), reverse=True)
    return active[0]


def _require_non_empty(value: str, field_name: str) -> str:
    v = value.strip()
    if not v:
        raise HTTPException(status_code=400, detail=f"{field_name} is required.")
    return v


def _validate_resume_file(name: str) -> None:
    ext = Path(name or "").suffix.lower()
    if ext not in ALLOWED_RESUME_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Resume file must be PDF or DOCX.")


def _validate_marksheet_file(name: str) -> None:
    ext = Path(name or "").suffix.lower()
    if ext not in ALLOWED_MARKSHEET_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Marksheet file must be PDF.")


def _parse_student_ids_form(raw: str | None) -> list[int] | None:
    if raw is None or not raw.strip():
        return None

    value = raw.strip()
    try:
        parsed_json = json.loads(value)
        if isinstance(parsed_json, list):
            candidate_ids = [int(item) for item in parsed_json]
        else:
            candidate_ids = [int(value)]
    except Exception:
        candidate_ids = [int(chunk.strip()) for chunk in value.split(",") if chunk.strip()]

    deduped = sorted({sid for sid in candidate_ids if sid > 0})
    return deduped or None


def _merge_jd_sources(file_text: str | None, typed_text: str | None) -> str:
    file_part = (file_text or "").strip()
    text_part = (typed_text or "").strip()

    if file_part and text_part:
        return f"{file_part}\n\nAdditional instructions:\n{text_part}"
    if file_part:
        return file_part
    if text_part:
        return text_part
    raise HTTPException(status_code=400, detail="Provide JD text and/or a JD file.")


def _norm_text(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.strip().lower().split())


def _norm_roll(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip().upper()


def _extract_identity_from_blob(blob: dict[str, object] | None) -> dict[str, str]:
    if not isinstance(blob, dict):
        return {}
    out: dict[str, str] = {}
    for key in ("name", "full_name", "candidate_name", "student_name"):
        value = _norm_text(blob.get(key))
        if value:
            out["name"] = value
            break
    for key in ("email", "mail"):
        value = _norm_text(blob.get(key))
        if value:
            out["email"] = value
            break
    for key in ("phone", "mobile", "contact", "phone_number"):
        value = _norm_text(blob.get(key))
        if value:
            out["phone"] = value
            break
    for key in ("roll_no", "roll", "roll_number", "enrollment_no", "enrollment"):
        value = _norm_roll(blob.get(key))
        if value:
            out["roll_no"] = value
            break
    return out


def _assert_analysis_identity_matches_student(student: Student, normalized: dict[str, object]) -> None:
    resume_identity = _extract_identity_from_blob(
        normalized.get("resume_data") if isinstance(normalized.get("resume_data"), dict) else {}
    )
    marksheet_identity = _extract_identity_from_blob(
        normalized.get("academic_data") if isinstance(normalized.get("academic_data"), dict) else {}
    )
    merged: dict[str, str] = {**resume_identity, **marksheet_identity}
    expected = {
        "name": _norm_text(student.name),
        "email": _norm_text(student.email),
        "phone": _norm_text(student.phone),
        "roll_no": _norm_roll(student.roll_no),
    }
    for field, observed in merged.items():
        target = expected.get(field, "")
        if field == "roll_no" and not target:
            # Permit first-time roll submission when account has no roll yet.
            continue
        if observed and target and observed != target:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Analysis blocked: uploaded resume/marksheet identity does not match your registered account. "
                    f"Mismatch field: {field}."
                ),
            )


@router.post("/analyze", response_model=StudentAnalyzeResponse)
async def analyze_student(
    resume_file: UploadFile = File(...),
    marksheet_file: UploadFile = File(...),
    branch: str = Form(...),
    github_username: str = Form(...),
    leetcode_username: str = Form(...),
    student_id: int = Depends(get_current_student_id),
    db: Session = Depends(get_db),
) -> StudentAnalyzeResponse:
    branch_clean = _require_non_empty(branch, "branch")
    github_clean = _require_non_empty(github_username, "github_username")
    leetcode_clean = _require_non_empty(leetcode_username, "leetcode_username")

    _validate_resume_file(resume_file.filename or "")
    _validate_marksheet_file(marksheet_file.filename or "")

    resume_bytes = await resume_file.read()
    marksheet_bytes = await marksheet_file.read()
    if not resume_bytes:
        raise HTTPException(status_code=400, detail="Resume file is empty.")
    if not marksheet_bytes:
        raise HTTPException(status_code=400, detail="Marksheet file is empty.")
    if len(resume_bytes) > MAX_FILE_BYTES or len(marksheet_bytes) > MAX_FILE_BYTES:
        raise HTTPException(status_code=413, detail="File size exceeds 8 MB limit.")
    student = db.query(Student).filter(Student.id == student_id).one_or_none()
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found.")

    try:
        normalized = await analyze_student_profile(
            resume_file=resume_bytes,
            resume_filename=resume_file.filename or "resume.bin",
            resume_content_type=resume_file.content_type,
            marksheet_file=marksheet_bytes,
            marksheet_filename=marksheet_file.filename or "marksheet.pdf",
            marksheet_content_type=marksheet_file.content_type,
            branch=branch_clean,
            github=github_clean,
            leetcode=leetcode_clean,
        )
    except ValueError as exc:
        logger.exception("Analyzer failure")
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    _assert_analysis_identity_matches_student(student, normalized)

    return StudentAnalyzeResponse.model_validate(normalized)


@router.post("/analyze-incremental", response_model=StudentAnalyzeResponse)
async def analyze_student_incremental(
    branch: str = Form(...),
    github_username: str = Form(...),
    leetcode_username: str = Form(...),
    resume_changed: bool = Form(False),
    marksheet_changed: bool = Form(False),
    coding_changed: bool = Form(False),
    resume_file: UploadFile | None = File(None),
    marksheet_file: UploadFile | None = File(None),
    student_id: int = Depends(get_current_student_id),
    db: Session = Depends(get_db),
) -> StudentAnalyzeResponse:
    branch_clean = _require_non_empty(branch, "branch")
    github_clean = _require_non_empty(github_username, "github_username")
    leetcode_clean = _require_non_empty(leetcode_username, "leetcode_username")

    inferred_resume_changed = resume_changed or resume_file is not None
    inferred_marksheet_changed = marksheet_changed or marksheet_file is not None

    student = db.query(Student).filter(Student.id == student_id).one_or_none()
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found.")

    profile = db.query(StudentProfile).filter(StudentProfile.student_id == student_id).one_or_none()
    if profile is None:
        raise HTTPException(
            status_code=400,
            detail="No existing profile found for incremental analysis. Run full analyze first with both files.",
        )

    latest_upload = (
        db.query(RawUpload)
        .filter(RawUpload.student_id == student_id)
        .order_by(RawUpload.uploaded_at.desc(), RawUpload.id.desc())
        .first()
    )

    resume_bytes: bytes | None = None
    marksheet_bytes: bytes | None = None

    if inferred_resume_changed:
        if resume_file is None:
            raise HTTPException(status_code=400, detail="Resume file is required when resume_changed is true.")
        _validate_resume_file(resume_file.filename or "")
        resume_bytes = await resume_file.read()
        if not resume_bytes:
            raise HTTPException(status_code=400, detail="Resume file is empty.")
        if len(resume_bytes) > MAX_FILE_BYTES:
            raise HTTPException(status_code=413, detail="Resume file size exceeds 8 MB limit.")

    if inferred_marksheet_changed:
        if marksheet_file is None:
            raise HTTPException(status_code=400, detail="Marksheet file is required when marksheet_changed is true.")
        _validate_marksheet_file(marksheet_file.filename or "")
        marksheet_bytes = await marksheet_file.read()
        if not marksheet_bytes:
            raise HTTPException(status_code=400, detail="Marksheet file is empty.")
        if len(marksheet_bytes) > MAX_FILE_BYTES:
            raise HTTPException(status_code=413, detail="Marksheet file size exceeds 8 MB limit.")

    try:
        normalized = await analyze_student_profile_incremental(
            existing_resume_data=profile.resume_data or {},
            existing_marksheet_data=profile.academic_data or {},
            existing_coding_data={
                "github": profile.github_data or {},
                "leetcode": profile.leetcode_data or {},
                "coding_persona": profile.coding_persona,
                "coding_level": profile.coding_persona,
            },
            resume_file=resume_bytes,
            resume_filename=resume_file.filename if resume_file else None,
            resume_content_type=resume_file.content_type if resume_file else None,
            marksheet_file=marksheet_bytes,
            marksheet_filename=marksheet_file.filename if marksheet_file else None,
            marksheet_content_type=marksheet_file.content_type if marksheet_file else None,
            resume_changed=inferred_resume_changed,
            marksheet_changed=inferred_marksheet_changed,
            coding_changed=coding_changed,
            branch=branch_clean,
            github=github_clean,
            leetcode=leetcode_clean,
            existing_resume_url=latest_upload.resume_url if latest_upload else None,
        )
    except ValueError as exc:
        logger.exception("Incremental analyzer failure")
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    if inferred_resume_changed and resume_file is not None:
        normalized.setdefault("resume_data", {})["file_name"] = resume_file.filename
    else:
        existing_resume_name = (profile.resume_data or {}).get("file_name")
        if existing_resume_name:
            normalized.setdefault("resume_data", {})["file_name"] = existing_resume_name

    if inferred_marksheet_changed and marksheet_file is not None:
        normalized.setdefault("academic_data", {})["file_name"] = marksheet_file.filename
    else:
        existing_marksheet_name = (profile.academic_data or {}).get("file_name")
        if existing_marksheet_name:
            normalized.setdefault("academic_data", {})["file_name"] = existing_marksheet_name

    # Incremental analyzers may omit identity fields; backfill from registered profile.
    student_payload = normalized.setdefault("student", {})
    if not isinstance(student_payload, dict):
        student_payload = {}
        normalized["student"] = student_payload
    if not str(student_payload.get("name") or "").strip():
        student_payload["name"] = student.name
    if not str(student_payload.get("email") or "").strip():
        student_payload["email"] = student.email
    if not str(student_payload.get("phone") or "").strip():
        student_payload["phone"] = student.phone
    if not str(student_payload.get("branch") or "").strip():
        student_payload["branch"] = branch_clean
    if not student_payload.get("roll_no"):
        student_payload["roll_no"] = student.roll_no
    _assert_analysis_identity_matches_student(student, normalized)

    return StudentAnalyzeResponse.model_validate(normalized)


@router.post("/profile", response_model=StudentProfileStoreResponse)
def create_student_profile(
    payload: StudentProfileCreate,
    db: Session = Depends(get_db),
    requesting_student_id: int | None = Depends(get_optional_student_id),
) -> StudentProfileStoreResponse:
    service = ProfileService(db)
    return service.save_profile(payload, requesting_student_id=requesting_student_id)


@router.get("/profile/me", response_model=StudentProfileResponse)
def get_my_profile(
    student_id: int = Depends(get_current_student_id),
    db: Session = Depends(get_db),
) -> StudentProfileResponse:
    service = ProfileService(db)
    return service.get_profile(student_id)


@router.post("/register", response_model=RegisterResponse)
def register_student(payload: RegisterRequest, db: Session = Depends(get_db)) -> RegisterResponse:
    auth_service = AuthService(get_settings())
    service = ProfileService(db, auth_service=auth_service)
    student = service.register_student(payload)
    return RegisterResponse(
        student_id=student.id,
        message="Registration successful.",
    )


@router.post("/tpo/groups", response_model=TpoGroupResponse)
def create_tpo_group(
    payload: TpoGroupCreateRequest,
    db: Session = Depends(get_db),
    tpo_user: str = Depends(get_current_tpo_user),
) -> TpoGroupResponse:
    service = ProfileService(db)
    metadata = _normalize_group_metadata(payload)
    group = service.create_tpo_analysis_group(
        title=payload.title,
        jd_summary=payload.jd_summary,
        company_name=metadata["company_name"],
        role_type=metadata["role_type"],
        pay_or_stipend=metadata["pay_or_stipend"],
        duration=metadata["duration"],
        bond_details=metadata["bond_details"],
        jd_topics=payload.jd_topics,
        jd_key_points=payload.jd_key_points,
        interview_timezone=payload.interview_timezone,
        student_ids=payload.student_ids,
        created_by=tpo_user,
    )
    members: list[TpoGroupMemberInfo] = []
    for member in group.members:
        student = member.student
        if student is None:
            continue
        placement = _active_placement_for_student(student)
        members.append(
            TpoGroupMemberInfo(
                student_id=student.id,
                name=student.name,
                email=student.email,
                roll_no=student.roll_no,
                branch=student.branch,
                placement={
                    "company_name": placement.company_name,
                    "offer_type": placement.offer_type,
                    "pay_amount": placement.pay_amount,
                    "notes": placement.notes,
                    "is_active": placement.is_active,
                    "created_at": placement.created_at,
                    "updated_at": placement.updated_at,
                }
                if placement
                else None,
            )
        )
    return TpoGroupResponse(
        id=group.id,
        title=group.title,
        jd_summary=group.jd_summary,
        created_by=group.created_by,
        created_at=group.created_at,
        company_name=group.company_name,
        role_type=group.role_type,
        pay_or_stipend=group.pay_or_stipend,
        duration=group.duration,
        bond_details=group.bond_details,
        jd_topics=group.jd_topics or [],
        jd_key_points=group.jd_key_points or [],
        interview_timezone=group.interview_timezone,
        members=members,
    )


@router.get("/tpo/groups", response_model=list[TpoGroupResponse])
def list_tpo_groups(
    db: Session = Depends(get_db),
    _tpo_user: str = Depends(get_current_tpo_user),
) -> list[TpoGroupResponse]:
    service = ProfileService(db)
    groups = service.list_tpo_analysis_groups()
    responses: list[TpoGroupResponse] = []
    for group in groups:
        members: list[TpoGroupMemberInfo] = []
        for member in group.members:
            student = member.student
            if student is None:
                continue
            placement = _active_placement_for_student(student)
            members.append(
                TpoGroupMemberInfo(
                    student_id=student.id,
                    name=student.name,
                    email=student.email,
                    roll_no=student.roll_no,
                    branch=student.branch,
                    placement={
                        "company_name": placement.company_name,
                        "offer_type": placement.offer_type,
                        "pay_amount": placement.pay_amount,
                        "notes": placement.notes,
                        "is_active": placement.is_active,
                        "created_at": placement.created_at,
                        "updated_at": placement.updated_at,
                    }
                    if placement
                    else None,
                )
            )
        responses.append(
            TpoGroupResponse(
                id=group.id,
                title=group.title,
                jd_summary=group.jd_summary,
                created_by=group.created_by,
                created_at=group.created_at,
                company_name=group.company_name,
                role_type=group.role_type,
                pay_or_stipend=group.pay_or_stipend,
                duration=group.duration,
                bond_details=group.bond_details,
                jd_topics=group.jd_topics or [],
                jd_key_points=group.jd_key_points or [],
                interview_timezone=group.interview_timezone,
                members=members,
            )
        )
    return responses


@router.get("/tpo/overview", response_model=TpoOverviewResponse)
def get_tpo_overview(
    db: Session = Depends(get_db),
    _tpo_user: str = Depends(get_current_tpo_user),
) -> TpoOverviewResponse:
    total_students = db.query(func.count(Student.id)).scalar() or 0
    active_groups = db.query(func.count(TpoAnalysisGroup.id)).scalar() or 0

    placed_students = (
        db.query(func.count(func.distinct(PlacementRecord.student_id)))
        .filter(PlacementRecord.is_active.is_(True))
        .scalar()
        or 0
    )

    unplaced_eligible_students = (
        db.query(func.count(Student.id))
        .outerjoin(
            PlacementRecord,
            (PlacementRecord.student_id == Student.id) & (PlacementRecord.is_active.is_(True)),
        )
        .filter(PlacementRecord.id.is_(None), Student.has_active_backlog.is_(False))
        .scalar()
        or 0
    )

    recent_rows = (
        db.query(PlacementRecord, Student)
        .join(Student, Student.id == PlacementRecord.student_id)
        .filter(PlacementRecord.is_active.is_(True))
        .order_by(PlacementRecord.updated_at.desc(), PlacementRecord.id.desc())
        .limit(5)
        .all()
    )
    recent_placements = [
        TpoOverviewRecentPlacement(
            student_id=student.id,
            name=student.name,
            email=student.email,
            company_name=record.company_name,
            offer_type=record.offer_type,
            pay_amount=record.pay_amount,
            updated_at=record.updated_at,
        )
        for record, student in recent_rows
    ]

    return TpoOverviewResponse(
        total_students=total_students,
        unplaced_eligible_students=unplaced_eligible_students,
        active_groups=active_groups,
        placed_students=placed_students,
        recent_placements=recent_placements,
    )


@router.get("/tpo/settings", response_model=TpoSettingsResponse)
def get_tpo_settings(
    db: Session = Depends(get_db),
    tpo_user: str = Depends(get_current_tpo_user),
) -> TpoSettingsResponse:
    settings_row = _upsert_tpo_settings_defaults(db, tpo_user)
    return TpoSettingsResponse(
        tpo_username=settings_row.tpo_username,
        display_name=settings_row.display_name,
        contact_number=settings_row.contact_number,
        institute_name=settings_row.institute_name,
        sender_name=settings_row.sender_name,
        reply_to_email=settings_row.reply_to_email,
        default_timezone=settings_row.default_timezone,
        stale_group_reminder_enabled=settings_row.stale_group_reminder_enabled,
        daily_queue_summary_enabled=settings_row.daily_queue_summary_enabled,
        placement_update_confirmation_enabled=settings_row.placement_update_confirmation_enabled,
        created_at=settings_row.created_at,
        updated_at=settings_row.updated_at,
    )


@router.put("/tpo/settings", response_model=TpoSettingsResponse)
def update_tpo_settings(
    payload: TpoSettingsData,
    db: Session = Depends(get_db),
    tpo_user: str = Depends(get_current_tpo_user),
) -> TpoSettingsResponse:
    settings_row = _upsert_tpo_settings_defaults(db, tpo_user)
    settings_row.display_name = payload.display_name
    settings_row.contact_number = payload.contact_number
    settings_row.institute_name = payload.institute_name
    settings_row.sender_name = payload.sender_name
    settings_row.reply_to_email = payload.reply_to_email
    settings_row.default_timezone = payload.default_timezone
    settings_row.stale_group_reminder_enabled = payload.stale_group_reminder_enabled
    settings_row.daily_queue_summary_enabled = payload.daily_queue_summary_enabled
    settings_row.placement_update_confirmation_enabled = payload.placement_update_confirmation_enabled
    db.add(settings_row)
    db.commit()
    db.refresh(settings_row)
    return TpoSettingsResponse(
        tpo_username=settings_row.tpo_username,
        display_name=settings_row.display_name,
        contact_number=settings_row.contact_number,
        institute_name=settings_row.institute_name,
        sender_name=settings_row.sender_name,
        reply_to_email=settings_row.reply_to_email,
        default_timezone=settings_row.default_timezone,
        stale_group_reminder_enabled=settings_row.stale_group_reminder_enabled,
        daily_queue_summary_enabled=settings_row.daily_queue_summary_enabled,
        placement_update_confirmation_enabled=settings_row.placement_update_confirmation_enabled,
        created_at=settings_row.created_at,
        updated_at=settings_row.updated_at,
    )


@router.post("/tpo/settings/change-password", response_model=TpoMailActionResponse)
def change_tpo_password(
    payload: TpoPasswordChangeRequest,
    db: Session = Depends(get_db),
    tpo_user: str = Depends(get_current_tpo_user),
) -> TpoMailActionResponse:
    settings = get_settings()
    auth_service = AuthService(settings)
    settings_row = _upsert_tpo_settings_defaults(db, tpo_user)
    stored_hash = settings_row.tpo_password_hash
    current_matches = (
        auth_service.verify_password(payload.current_password, stored_hash)
        if stored_hash
        else payload.current_password == settings.tpo_password
    )
    if not current_matches:
        raise HTTPException(status_code=400, detail="Current password is incorrect.")
    if payload.current_password == payload.new_password:
        raise HTTPException(status_code=400, detail="New password must be different from current password.")
    _validate_new_password(payload.new_password)
    settings_row.tpo_password_hash = auth_service.hash_password(payload.new_password)
    db.add(settings_row)
    db.commit()
    return TpoMailActionResponse(message="TPO password updated successfully.")


@router.delete("/tpo/groups/{group_id}", response_model=TpoMailActionResponse)
def delete_tpo_group(
    group_id: int,
    db: Session = Depends(get_db),
    _tpo_user: str = Depends(get_current_tpo_user),
) -> TpoMailActionResponse:
    service = ProfileService(db)
    service.delete_tpo_analysis_group(group_id)
    return TpoMailActionResponse(message="Placement group deleted.")


@router.post("/tpo/placement", response_model=StudentProfileStoreResponse)
def mark_placement(
    payload: PlacementMarkRequest,
    db: Session = Depends(get_db),
    _tpo_user: str = Depends(get_current_tpo_user),
) -> StudentProfileStoreResponse:
    service = ProfileService(db)
    record = service.mark_student_placement(
        student_id=payload.student_id,
        group_id=payload.group_id,
        company_name=payload.company_name,
        offer_type=payload.offer_type,
        pay_amount=payload.pay_amount,
        notes=payload.notes,
    )
    return StudentProfileStoreResponse(
        student_id=record.student_id,
        profile_id=0,
        message="Placement status updated.",
    )


def _optional_note_block(additional_note: str | None) -> str:
    note = (additional_note or "").strip()
    if not note:
        return ""
    return f"\nAdditional Note:\n{note}\n"


def _clean_lines(values: list[str] | None, limit: int = 6) -> list[str]:
    if not values:
        return []
    out: list[str] = []
    seen: set[str] = set()
    for raw in values:
        text = str(raw or "").strip()
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(text)
        if len(out) >= limit:
            break
    return out


def _jd_context_block(group: TpoAnalysisGroup) -> str:
    topics = _clean_lines(group.jd_topics if isinstance(group.jd_topics, list) else [])
    key_points = _clean_lines(group.jd_key_points if isinstance(group.jd_key_points, list) else [])
    lines: list[str] = []
    if topics:
        lines.append("Primary Focus Areas:")
        lines.extend(f"- {topic}" for topic in topics)
    if key_points:
        if lines:
            lines.append("")
        lines.append("Important JD Points:")
        lines.extend(f"- {point}" for point in key_points)
    if not lines:
        summary = (group.jd_summary or "").strip()
        if summary:
            return f"JD Context:\n{summary[:400]}\n"
        return ""
    return "\n".join(lines) + "\n"


def _render_subject_and_body(payload: TpoMailActionRequest, student: Student, group: TpoAnalysisGroup) -> tuple[str, str]:
    company = (group.company_name or "the company").strip()
    role = (group.role_type or "job opportunity").strip()
    note_block = _optional_note_block(payload.additional_note)
    jd_block = _jd_context_block(group)

    if payload.mail_type == "shortlist_notice":
        subject = (payload.subject or f"Shortlist Update: {company} {role.title()}").strip()
        body = (
            f"Dear {student.name},\n\n"
            f"We are pleased to inform you that you have been shortlisted for the {role} role at {company}.\n\n"
            "Details:\n"
            f"- Company: {company}\n"
            f"- Role: {role}\n"
            "- Status: Shortlisted for next stage\n"
            f"{jd_block}\n"
            f"{note_block}\n"
            "Please keep checking the placement portal and your email for further updates.\n\n"
            "Best regards,\n"
            "Training and Placement Office\n"
            "VerifAI"
        ).strip()
        return subject, body

    if payload.mail_type == "prep_topics":
        topics = [topic.strip() for topic in payload.prep_topics if topic.strip()]
        if not topics:
            topics = _clean_lines(group.jd_topics if isinstance(group.jd_topics, list) else [])
        if not topics:
            raise HTTPException(status_code=400, detail="prep_topics requires at least one topic.")
        subject = (payload.subject or f"Preparation Guide: {company} {role.title()}").strip()
        topics_text = "\n".join(f"- {topic}" for topic in topics)
        body = (
            f"Dear {student.name},\n\n"
            f"As part of the upcoming selection process for {company}, please prepare the following topics for the {role} role.\n\n"
            "Preparation Topics:\n"
            f"{topics_text}\n"
            f"{jd_block}\n"
            f"{note_block}\n"
            "Please revise these topics thoroughly before the next round.\n\n"
            "Best regards,\n"
            "Training and Placement Office\n"
            "VerifAI"
        ).strip()
        return subject, body

    if payload.mail_type == "interview_schedule":
        if not payload.interview_date or not payload.interview_time_start or not payload.interview_time_end:
            raise HTTPException(
                status_code=400,
                detail="interview_schedule requires interview_date, interview_time_start, and interview_time_end.",
            )
        tz = group.interview_timezone or "local time"
        subject = (payload.subject or f"Interview Schedule: {company}").strip()
        body = (
            f"Dear {student.name},\n\n"
            "Your interview has been scheduled. Please find the details below:\n\n"
            "Interview Details:\n"
            f"- Company: {company}\n"
            f"- Role: {role}\n"
            f"- Date: {payload.interview_date}\n"
            f"- Time: {payload.interview_time_start} to {payload.interview_time_end}\n"
            f"- Timezone: {tz}\n"
            f"{jd_block}\n"
            f"{note_block}\n"
            "Please join/report on time and keep your required documents ready.\n\n"
            "Best regards,\n"
            "Training and Placement Office\n"
            "VerifAI"
        ).strip()
        return subject, body

    if payload.mail_type == "process_custom":
        if not payload.subject or not payload.body:
            raise HTTPException(status_code=400, detail="process_custom requires subject and body.")
        subject = payload.subject.strip()
        personalized_body = payload.body.strip().replace("{student_name}", student.name).replace("{company_name}", company)
        body = (
            f"Dear {student.name},\n\n"
            f"{personalized_body}\n\n"
            f"{jd_block}\n"
            f"{note_block}\n"
            "Best regards,\n"
            "Training and Placement Office\n"
            "VerifAI"
        ).strip()
        return subject, body

    raise HTTPException(status_code=400, detail="Unsupported mail type.")


def _mail_job_to_progress_response(job: TpoMailJob) -> TpoMailJobProgressResponse:
    status = job.status if job.status in {"queued", "running", "completed", "failed"} else "failed"
    progress = 0.0
    if job.total_recipients > 0:
        progress = round((job.processed_count / job.total_recipients) * 100, 2)
    return TpoMailJobProgressResponse(
        job_id=job.id,
        group_id=job.group_id,
        mail_type=job.mail_type,
        status=status,
        total_recipients=job.total_recipients,
        processed_count=job.processed_count,
        success_count=job.success_count,
        failure_count=job.failure_count,
        progress_percent=progress,
        last_error=job.last_error,
        started_at=job.started_at,
        finished_at=job.finished_at,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


def _process_bulk_mail_job(job_id: int, payload_dict: dict[str, object]) -> None:
    db = SessionLocal()
    try:
        job = db.query(TpoMailJob).filter(TpoMailJob.id == job_id).one_or_none()
        if job is None:
            return
        group = db.query(TpoAnalysisGroup).filter(TpoAnalysisGroup.id == job.group_id).one_or_none()
        if group is None:
            job.status = "failed"
            job.last_error = "Group no longer exists."
            job.finished_at = datetime.now(timezone.utc)
            job.updated_at = datetime.now(timezone.utc)
            db.add(job)
            db.commit()
            return
        payload = TpoMailActionRequest.model_validate(payload_dict)
        members = [member.student for member in group.members if member.student is not None]
        if payload.mode == "individual" and payload.student_id is not None:
            members = [student for student in members if student.id == payload.student_id]

        settings = get_settings()
        mailer = MailService(settings)
        job.status = "running"
        job.started_at = datetime.now(timezone.utc)
        job.updated_at = datetime.now(timezone.utc)
        db.add(job)
        db.commit()

        for student in members:
            try:
                subject, body = _render_subject_and_body(payload, student, group)
                mailer.send_email(to_email=student.email, subject=subject, body=body)
                job.success_count += 1
            except (HTTPException, smtplib.SMTPException, OSError, ValueError) as exc:
                job.failure_count += 1
                job.last_error = f"{student.email}: {exc}"
            finally:
                job.processed_count += 1
                job.updated_at = datetime.now(timezone.utc)
                db.add(job)
                db.commit()

        job.status = "completed" if job.failure_count == 0 else "failed"
        job.finished_at = datetime.now(timezone.utc)
        job.updated_at = datetime.now(timezone.utc)
        db.add(job)
        db.commit()
    finally:
        db.close()


@router.post("/tpo/mail", response_model=TpoMailActionResponse)
def trigger_tpo_mail_action(
    payload: TpoMailActionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    tpo_user: str = Depends(get_current_tpo_user),
) -> TpoMailActionResponse:
    group = db.query(TpoAnalysisGroup).filter(TpoAnalysisGroup.id == payload.group_id).one_or_none()
    if group is None:
        raise HTTPException(status_code=404, detail="Group not found.")

    members = [member.student for member in group.members if member.student is not None]
    if payload.mode == "individual":
        if payload.student_id is None:
            raise HTTPException(status_code=400, detail="student_id is required for individual mail mode.")
        members = [student for student in members if student.id == payload.student_id]
    if not members:
        raise HTTPException(status_code=400, detail="No recipients found.")

    if payload.mode == "bulk":
        job = TpoMailJob(
            group_id=group.id,
            requested_by=tpo_user,
            mail_type=payload.mail_type,
            status="queued",
            total_recipients=len(members),
            processed_count=0,
            success_count=0,
            failure_count=0,
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        background_tasks.add_task(_process_bulk_mail_job, job.id, payload.model_dump())
        return TpoMailActionResponse(
            message=f"Bulk mail started for {len(members)} recipient(s).",
            job_id=job.id,
            status=job.status,
            total_recipients=job.total_recipients,
            processed_count=job.processed_count,
            success_count=job.success_count,
            failure_count=job.failure_count,
        )

    settings = get_settings()
    mailer = MailService(settings)
    student = members[0]
    subject, body = _render_subject_and_body(payload, student, group)
    try:
        mailer.send_email(to_email=student.email, subject=subject, body=body)
    except (smtplib.SMTPException, OSError, ValueError) as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to send email to {student.email}. Check SMTP configuration and credentials.",
        ) from exc
    return TpoMailActionResponse(message=f"Sent {payload.mail_type} email to 1 recipient.")


@router.get("/tpo/mail/{job_id}", response_model=TpoMailJobProgressResponse)
def get_tpo_mail_job_progress(
    job_id: int,
    db: Session = Depends(get_db),
    _tpo_user: str = Depends(get_current_tpo_user),
) -> TpoMailJobProgressResponse:
    job = db.query(TpoMailJob).filter(TpoMailJob.id == job_id).one_or_none()
    if job is None:
        raise HTTPException(status_code=404, detail="Mail job not found.")
    return _mail_job_to_progress_response(job)


@router.post("/login", response_model=AuthTokenResponse)
def login_student(payload: LoginRequest, db: Session = Depends(get_db)) -> AuthTokenResponse:
    auth_service = AuthService(get_settings())
    service = ProfileService(db, auth_service=auth_service)
    return service.login_student(payload)


@router.post("/tpo/login", response_model=TpoAuthTokenResponse)
def login_tpo(payload: TpoLoginRequest) -> TpoAuthTokenResponse:
    settings = get_settings()
    from app.database.database import SessionLocal

    if payload.username != settings.tpo_username:
        raise HTTPException(status_code=401, detail="Invalid TPO credentials.")
    auth_service = AuthService(settings)
    db = SessionLocal()
    try:
        settings_row = db.query(TpoSettings).filter(TpoSettings.tpo_username == payload.username).one_or_none()
        if settings_row and settings_row.tpo_password_hash:
            password_ok = auth_service.verify_password(payload.password, settings_row.tpo_password_hash)
        else:
            password_ok = payload.password == settings.tpo_password
    finally:
        db.close()
    if not password_ok:
        raise HTTPException(status_code=401, detail="Invalid TPO credentials.")

    access_token = auth_service.create_tpo_access_token(username=settings.tpo_username)
    return TpoAuthTokenResponse(
        access_token=access_token,
        username=settings.tpo_username,
    )


@router.get("/profile/{id}", response_model=StudentProfileResponse)
def get_student_profile(id: int, db: Session = Depends(get_db)) -> StudentProfileResponse:
    service = ProfileService(db)
    return service.get_profile(id)


@router.post("/match-jd", response_model=JDMatchResponse)
async def match_students_with_jd(
    request: Request,
    db: Session = Depends(get_db),
    _tpo_user: str = Depends(get_current_tpo_user),
) -> JDMatchResponse:
    content_type = request.headers.get("content-type", "").lower()
    merged_jd_text: str
    student_ids: list[int] | None = None
    top_k: int | None = None

    if "multipart/form-data" in content_type:
        form = await request.form()
        jd_text = str(form.get("jd_text") or "").strip() or None

        jd_file = form.get("jd_file")
        file_text: str | None = None
        if isinstance(jd_file, (UploadFile, StarletteUploadFile)):
            suffix = Path(jd_file.filename or "").suffix.lower()
            if suffix not in ALLOWED_JD_EXTENSIONS:
                raise HTTPException(status_code=400, detail="JD file must be PDF or DOCX.")
            raw_file = await jd_file.read()
            if not raw_file:
                raise HTTPException(status_code=400, detail="JD file is empty.")
            if len(raw_file) > MAX_FILE_BYTES:
                raise HTTPException(status_code=413, detail="JD file size exceeds 8 MB limit.")
            try:
                file_text = extract_jd_text_from_file(raw_file, jd_file.filename or "jd_file")
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc

        merged_jd_text = _merge_jd_sources(file_text, jd_text)
        if len(merged_jd_text.strip()) < 20:
            raise HTTPException(status_code=400, detail="Merged JD content must be at least 20 characters.")

        try:
            student_ids = _parse_student_ids_form(form.get("student_ids"))  # type: ignore[arg-type]
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Invalid student_ids format.") from exc

        raw_top_k = form.get("top_k")
        if raw_top_k not in (None, ""):
            try:
                top_k = int(str(raw_top_k))
            except ValueError as exc:
                raise HTTPException(status_code=400, detail="top_k must be an integer.") from exc
            if top_k < 1 or top_k > 500:
                raise HTTPException(status_code=400, detail="top_k must be between 1 and 500.")
    else:
        try:
            payload = JDMatchRequest.model_validate(await request.json())
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Invalid JSON payload for JD matching.") from exc
        merged_jd_text = payload.jd_text
        student_ids = payload.student_ids
        top_k = payload.top_k

    settings = get_settings()
    async with httpx.AsyncClient(headers=DEFAULT_HEADERS) as client:
        jd_data, jd_error = await call_jd_analyzer(
            settings=settings,
            client=client,
            jd_text=merged_jd_text,
        )
    if jd_error or jd_data is None:
        raise HTTPException(status_code=502, detail=f"JD analyzer failed: {jd_error or 'unknown error'}")

    constraints, filters, candidates = run_jd_matching(
        db=db,
        jd_data=jd_data,
        student_ids=student_ids,
        top_k=top_k,
    )
    return JDMatchResponse(jd=constraints, filters=filters, candidates=candidates)


@router.post("/{id}/send-email")
def send_student_email(
    id: int,
    subject: str | None = Form(None),
    body: str | None = Form(None),
    db: Session = Depends(get_db)
) -> dict:
    student = db.query(Student).filter(Student.id == id).one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")
    
    from app.services.email_service import EmailService
    service = EmailService()
    success = service.send_single_email(student, subject, body)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send email.")

    return {"success": True, "message": f"Mail sent to {student.name}."}

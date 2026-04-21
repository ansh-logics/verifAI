from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

GenderType = str


def normalize_gender_value(value: str) -> GenderType:
    v = value.strip().lower().replace("-", "_").replace(" ", "_")
    if v in {"woman", "women", "female", "girl", "girls"}:
        return "women"
    if v in {"man", "men", "male", "boy", "boys"}:
        return "men"
    if v in {"other", "non_binary", "nonbinary", "nb", "prefer_not_to_say"}:
        return "other"
    raise ValueError("gender must be one of: women, men, other")


class StudentData(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: str = Field(min_length=3, max_length=255)
    roll_no: str | None = Field(default=None, min_length=1, max_length=64)
    phone: str = Field(min_length=7, max_length=32)
    branch: str = Field(min_length=1, max_length=128)
    cgpa: float | None = Field(default=None, ge=0, le=10)
    gender: GenderType = Field(default="other")
    cgpa_verified: bool = False

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        v = value.strip().lower()
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("invalid email format")
        return v

    @field_validator("name", "phone", "branch")
    @classmethod
    def trim_required(cls, value: str) -> str:
        v = value.strip()
        if not v:
            raise ValueError("field cannot be blank")
        return v

    @field_validator("roll_no")
    @classmethod
    def normalize_roll_no(cls, value: str | None) -> str | None:
        if value is None:
            return None
        v = value.strip().upper()
        if not v:
            raise ValueError("roll_no cannot be blank")
        return v

    @field_validator("gender")
    @classmethod
    def normalize_gender(cls, value: str) -> GenderType:
        return normalize_gender_value(value)


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    phone: str = Field(min_length=7, max_length=32)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        v = value.strip().lower()
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("invalid email format")
        return v

    @field_validator("name", "phone")
    @classmethod
    def normalize_required_text(cls, value: str) -> str:
        v = value.strip()
        if not v:
            raise ValueError("field cannot be blank")
        return v

class LoginRequest(BaseModel):
    identifier: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("identifier")
    @classmethod
    def normalize_identifier(cls, value: str) -> str:
        return value.strip()


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    student_id: int
    email: str
    roll_no: str | None = None


class TpoLoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        return value.strip()


class TpoAuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


class RegisterResponse(BaseModel):
    success: bool = True
    student_id: int
    message: str = "Registration successful."


class CodingData(BaseModel):
    persona: str = ""
    score: float = Field(default=0.0, ge=0, le=100)
    github: dict[str, Any] = Field(default_factory=dict)
    leetcode: dict[str, Any] = Field(default_factory=dict)


class AcademicsData(BaseModel):
    cgpa: float | None = Field(default=None, ge=0, le=10)
    verified: bool = False
    score: float = Field(default=0.0, ge=0, le=100)


class StudentAnalyzeResponse(BaseModel):
    student: StudentData
    skills: list[str] = Field(default_factory=list)
    coding: CodingData = Field(default_factory=CodingData)
    academics: AcademicsData = Field(default_factory=AcademicsData)
    overall_score: float = Field(default=0.0, ge=0, le=100)
    resume_url: str | None = None


class StudentProfileCreate(StudentAnalyzeResponse):
    resume_data: dict[str, Any] = Field(default_factory=dict)
    academic_data: dict[str, Any] = Field(default_factory=dict)
    github_data: dict[str, Any] = Field(default_factory=dict)
    leetcode_data: dict[str, Any] = Field(default_factory=dict)
    resume_url: str | None = None
    marksheet_url: str | None = None

    @field_validator("skills")
    @classmethod
    def normalize_skills(cls, value: list[str]) -> list[str]:
        out: list[str] = []
        seen: set[str] = set()
        for skill in value:
            s = skill.strip().lower()
            if not s or s in seen:
                continue
            seen.add(s)
            out.append(s)
        return out


class StudentProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    student: StudentData
    skills: list[str] = Field(default_factory=list)
    coding: CodingData
    academics: AcademicsData
    overall_score: float
    resume_url: str | None = None
    resume_data: dict[str, Any] = Field(default_factory=dict)
    academic_data: dict[str, Any] = Field(default_factory=dict)
    github_data: dict[str, Any] = Field(default_factory=dict)
    leetcode_data: dict[str, Any] = Field(default_factory=dict)
    last_analyzed_at: datetime
    created_at: datetime
    placement: "PlacementInfo | None" = None


class StudentProfileStoreResponse(BaseModel):
    success: bool = True
    student_id: int
    profile_id: int
    message: str = "Profile stored successfully."


class PlacementInfo(BaseModel):
    company_name: str
    offer_type: str
    pay_amount: float | None = None
    notes: str | None = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime


class PlacementMarkRequest(BaseModel):
    student_id: int = Field(ge=1)
    group_id: int | None = Field(default=None, ge=1)
    company_name: str | None = Field(default=None, min_length=1, max_length=255)
    offer_type: str | None = Field(default=None, min_length=1, max_length=32)
    pay_amount: float | None = None
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("company_name", "offer_type")
    @classmethod
    def normalize_non_empty(cls, value: str) -> str:
        v = value.strip()
        if not v:
            raise ValueError("field cannot be blank")
        return v

    @field_validator("group_id")
    @classmethod
    def validate_group_or_company(cls, value: int | None) -> int | None:
        return value

    @field_validator("offer_type")
    @classmethod
    def normalize_offer_type(cls, value: str | None) -> str | None:
        if value is None:
            return None
        v = value.strip().lower()
        if v not in {"internship", "job"}:
            raise ValueError("offer_type must be internship or job")
        return v


class TpoGroupCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    jd_summary: str | None = Field(default=None, max_length=5000)
    student_ids: list[int] = Field(default_factory=list)
    company_name: str | None = Field(default=None, max_length=255)
    role_type: str | None = Field(default=None, max_length=32)
    pay_or_stipend: str | None = Field(default=None, max_length=128)
    duration: str | None = Field(default=None, max_length=128)
    bond_details: str | None = Field(default=None, max_length=4000)
    interview_timezone: str | None = Field(default=None, max_length=64)


class TpoGroupMemberInfo(BaseModel):
    student_id: int
    name: str
    email: str
    roll_no: str | None = None
    branch: str
    placement: PlacementInfo | None = None


class TpoGroupResponse(BaseModel):
    id: int
    title: str
    jd_summary: str | None = None
    created_by: str
    created_at: datetime
    company_name: str | None = None
    role_type: str | None = None
    pay_or_stipend: str | None = None
    duration: str | None = None
    bond_details: str | None = None
    interview_timezone: str | None = None
    members: list[TpoGroupMemberInfo] = Field(default_factory=list)


class TpoMailActionRequest(BaseModel):
    group_id: int = Field(ge=1)
    mode: str = Field(min_length=1, max_length=16)
    mail_type: str = Field(min_length=1, max_length=64)
    subject: str | None = Field(default=None, max_length=255)
    body: str | None = Field(default=None, max_length=5000)
    student_id: int | None = Field(default=None, ge=1)
    prep_topics: list[str] = Field(default_factory=list)
    interview_date: str | None = None
    interview_time_start: str | None = None
    interview_time_end: str | None = None
    additional_note: str | None = Field(default=None, max_length=1000)

    @field_validator("mode")
    @classmethod
    def normalize_mode(cls, value: str) -> str:
        v = value.strip().lower()
        if v not in {"bulk", "individual"}:
            raise ValueError("mode must be bulk or individual")
        return v

    @field_validator("mail_type")
    @classmethod
    def normalize_mail_type(cls, value: str) -> str:
        v = value.strip().lower()
        allowed = {"shortlist_notice", "prep_topics", "interview_schedule", "process_custom"}
        if v not in allowed:
            raise ValueError("mail_type is invalid")
        return v


class TpoMailActionResponse(BaseModel):
    success: bool = True
    message: str


class JDParsedConstraints(BaseModel):
    company_name: str | None = None
    pay_or_stipend: str | None = None
    bond_details: str | None = None
    jd_summary: str | None = None
    job_title: str | None = None
    role_type: str = "unknown"
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    tools_and_technologies: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    key_traits: list[str] = Field(default_factory=list)
    min_experience_years: float | None = None
    accepts_freshers: bool = False
    education_requirements: list[str] = Field(default_factory=list)
    location: str | None = None
    domain: str | None = None
    duration: str | None = None
    work_type: str | None = None
    target_student_count: int | None = None
    exclude_active_backlogs: bool = False
    placement_filter: str = "placed_or_unplaced"
    placement_exception_roll_nos: list[str] = Field(default_factory=list)
    min_cgpa: float | None = None
    allowed_branches: list[str] = Field(default_factory=list)
    gender_filter: str = "all_genders"
    gender_filter_raw: str | None = None
    branch_constraint_raw: str | None = None
    branch_inference_reason: str | None = None


class JDMatchRequest(BaseModel):
    jd_text: str = Field(min_length=20)
    student_ids: list[int] | None = None
    top_k: int | None = Field(default=None, ge=1, le=500)

    @field_validator("jd_text")
    @classmethod
    def validate_jd_text(cls, value: str) -> str:
        v = value.strip()
        if len(v) < 20:
            raise ValueError("jd_text must contain at least 20 non-space characters")
        return v

    @field_validator("student_ids")
    @classmethod
    def validate_student_ids(cls, value: list[int] | None) -> list[int] | None:
        if value is None:
            return None
        deduped = sorted({sid for sid in value if sid > 0})
        return deduped or None


class ScoreBreakdown(BaseModel):
    resume: float = Field(default=0.0, ge=0, le=40)
    github: float = Field(default=0.0, ge=0, le=20)
    leetcode: float = Field(default=0.0, ge=0, le=20)
    academics: float = Field(default=0.0, ge=0, le=20)
    total: float = Field(default=0.0, ge=0, le=100)


class MatchCandidate(BaseModel):
    student_id: int
    email: str
    name: str
    roll_no: str | None = None
    gender: str
    branch: str
    cgpa: float | None = None
    skills: list[str] = Field(default_factory=list)
    resume_url: str | None = None
    coding_persona: str | None = None
    is_placed: bool = False
    has_active_backlog: bool = False
    score_breakdown: ScoreBreakdown


class FilterSummary(BaseModel):
    total_considered: int = 0
    passed_filters: int = 0
    rejected_min_cgpa: int = 0
    rejected_branch: int = 0
    rejected_gender: int = 0
    rejected_backlog: int = 0
    rejected_placement: int = 0


class JDMatchResponse(BaseModel):
    jd: JDParsedConstraints
    filters: FilterSummary
    candidates: list[MatchCandidate] = Field(default_factory=list)


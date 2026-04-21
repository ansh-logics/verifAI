from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


RoleType = Literal["full_time", "internship", "contract", "part_time", "unknown"]
PlacementFilter = Literal["unplaced_only", "placed_or_unplaced"]
GenderFilter = Literal["women_only", "men_only", "all_genders", "custom_text"]


class JDAnalyzeRequest(BaseModel):
    jd_text: str = Field(..., min_length=20)

    @field_validator("jd_text")
    @classmethod
    def validate_jd_text(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 20:
            raise ValueError("jd_text must be at least 20 characters long.")
        return cleaned


class JDAnalyzeResponse(BaseModel):
    company_name: str | None = None
    pay_or_stipend: str | None = None
    bond_details: str | None = None
    jd_summary: str | None = None
    job_title: str | None = None
    role_type: RoleType = "unknown"
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    min_experience_years: float | None = None
    accepts_freshers: bool = False
    key_traits: list[str] = Field(default_factory=list)
    education_requirements: list[str] = Field(default_factory=list)
    location: str | None = None
    domain: str | None = None
    tools_and_technologies: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    duration: str | None = None
    work_type: str | None = None
    target_student_count: int | None = None
    exclude_active_backlogs: bool = False
    placement_filter: PlacementFilter = "placed_or_unplaced"
    placement_exception_roll_nos: list[str] = Field(default_factory=list)
    min_cgpa: float | None = None
    allowed_branches: list[str] = Field(default_factory=list)
    gender_filter: GenderFilter = "all_genders"
    gender_filter_raw: str | None = None
    branch_constraint_raw: str | None = None
    branch_inference_reason: str | None = None


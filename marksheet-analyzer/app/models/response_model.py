from __future__ import annotations

from pydantic import BaseModel, Field


class StudentInfo(BaseModel):
    institute_code: str = ""
    institute_name: str = ""
    course_code: str = ""
    course_name: str = ""
    branch_code: str = ""
    branch_name: str = ""
    roll_no: str = ""
    enrollment_no: str = ""
    name: str = ""
    father_name: str = ""
    gender: str = ""


class SubjectEntry(BaseModel):
    code: str = ""
    name: str = ""
    type: str = ""
    internal: str = ""
    external: str = ""
    back_paper: str = ""
    grade: str = ""


class SemesterAttempt(BaseModel):
    attempt_index: int = 0
    session: str = ""
    semester_no: int = 0
    even_odd: str = ""
    result_status_session: str = ""
    result_status_semester: str = ""
    marks_obtained: int | None = None
    marks_total: int | None = None
    cop: str = ""
    sgpa_pdf: float | None = None
    declaration_date: str = ""
    subjects: list[SubjectEntry] = Field(default_factory=list)


class NormalizedSemester(BaseModel):
    semester_no: int
    all_attempts_count: int
    latest_attempt: SemesterAttempt


class AcademicsSummary(BaseModel):
    sgpa_by_semester: dict[int, float] = Field(default_factory=dict)
    cgpa_computed: float | None = None
    semesters_counted: int = 0
    missing_sgpa_semesters: list[int] = Field(default_factory=list)


class ValidationBlock(BaseModel):
    warnings: list[str] = Field(default_factory=list)
    parser_confidence: int = 0


class CandidateDetails(BaseModel):
    institute_code: str = ""
    institute_name: str = ""
    course_code: str = ""
    course_name: str = ""
    branch_code: str = ""
    branch_name: str = ""
    class_name: str = ""
    roll_no: str = ""
    enrollment_no: str = ""
    name: str = ""
    father_name: str = ""
    gender: str = ""


class BacklogSummary(BaseModel):
    has_active_backlog: bool = False
    active_backlog_codes: list[str] = Field(default_factory=list)
    active_backlog_count: int = 0


class MarksheetAnalysisResponse(BaseModel):
    candidate: CandidateDetails = Field(default_factory=CandidateDetails)
    cgpa_computed: float | None = None
    last_semester_number: int | None = None
    last_semester_sgpa: float | None = None
    backlog: BacklogSummary = Field(default_factory=BacklogSummary)
    academics_summary: AcademicsSummary = Field(default_factory=AcademicsSummary)
    validation: ValidationBlock = Field(default_factory=ValidationBlock)

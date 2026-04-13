from __future__ import annotations

import re
from datetime import datetime
from typing import Sequence

from app.models.response_model import (
    AcademicsSummary,
    BacklogSummary,
    CandidateDetails,
    MarksheetAnalysisResponse,
    NormalizedSemester,
    SemesterAttempt,
    StudentInfo,
    ValidationBlock,
)
from app.services.parser import parse_declaration_date


class MarksheetExtractor:
    def build_response(
        self,
        *,
        student: StudentInfo,
        attempts: Sequence[SemesterAttempt],
        warnings: list[str],
    ) -> MarksheetAnalysisResponse:
        normalized, summary, extra_warnings = self._normalize_and_compute(attempts)
        all_warnings = warnings + extra_warnings
        confidence = self._confidence(student, attempts, all_warnings)
        latest_semester = max(normalized, key=lambda item: item.semester_no) if normalized else None
        candidate = self._build_candidate(student)
        backlog = self._build_backlog(normalized)

        return MarksheetAnalysisResponse(
            candidate=candidate,
            cgpa_computed=summary.cgpa_computed,
            last_semester_number=latest_semester.semester_no if latest_semester else None,
            last_semester_sgpa=latest_semester.latest_attempt.sgpa_pdf if latest_semester else None,
            backlog=backlog,
            academics_summary=summary,
            validation=ValidationBlock(warnings=all_warnings, parser_confidence=confidence),
        )

    def _normalize_and_compute(
        self,
        attempts: Sequence[SemesterAttempt],
    ) -> tuple[list[NormalizedSemester], AcademicsSummary, list[str]]:
        warnings: list[str] = []
        grouped: dict[int, list[SemesterAttempt]] = {}
        for attempt in attempts:
            grouped.setdefault(attempt.semester_no, []).append(attempt)

        normalized: list[NormalizedSemester] = []
        sgpa_by_semester: dict[int, float] = {}
        missing_sgpa_semesters: list[int] = []

        for semester_no in sorted(grouped.keys()):
            choices = grouped[semester_no]
            latest = self._pick_latest_attempt(choices)
            normalized.append(
                NormalizedSemester(
                    semester_no=semester_no,
                    all_attempts_count=len(choices),
                    latest_attempt=latest,
                )
            )
            if len(choices) > 1:
                warnings.append(
                    f"Semester {semester_no} has {len(choices)} attempts; latest declaration used for CGPA."
                )

            if latest.sgpa_pdf is None:
                missing_sgpa_semesters.append(semester_no)
                warnings.append(f"Semester {semester_no} excluded from CGPA due to missing SGPA.")
            else:
                sgpa_by_semester[semester_no] = latest.sgpa_pdf

        values = list(sgpa_by_semester.values())
        cgpa = round(sum(values) / len(values), 2) if values else None

        summary = AcademicsSummary(
            sgpa_by_semester=sgpa_by_semester,
            cgpa_computed=cgpa,
            semesters_counted=len(values),
            missing_sgpa_semesters=missing_sgpa_semesters,
        )
        return normalized, summary, warnings

    def _pick_latest_attempt(self, attempts: Sequence[SemesterAttempt]) -> SemesterAttempt:
        def session_year(session: str) -> int:
            m = re.search(r"(\d{4})", session)
            return int(m.group(1)) if m else 0

        def sort_key(item: SemesterAttempt) -> tuple[int, int, int]:
            dt = parse_declaration_date(item.declaration_date)
            ts = int(dt.timestamp()) if isinstance(dt, datetime) else 0
            yr = session_year(item.session)
            return (ts, yr, item.attempt_index)

        return max(attempts, key=sort_key)

    def _confidence(
        self,
        student: StudentInfo,
        attempts: Sequence[SemesterAttempt],
        warnings: Sequence[str],
    ) -> int:
        score = 100
        if not student.roll_no:
            score -= 10
        if not student.enrollment_no:
            score -= 10
        if not student.name:
            score -= 10
        if not attempts:
            score -= 40
        missing_subject_blocks = sum(1 for a in attempts if not a.subjects)
        score -= min(20, missing_subject_blocks * 5)
        score -= min(30, len(warnings) * 3)
        return max(0, min(score, 100))

    def _build_candidate(self, student: StudentInfo) -> CandidateDetails:
        class_name = " ".join(x for x in [student.course_name, student.branch_name] if x).strip()
        return CandidateDetails(
            institute_code=student.institute_code,
            institute_name=student.institute_name,
            course_code=student.course_code,
            course_name=student.course_name,
            branch_code=student.branch_code,
            branch_name=student.branch_name,
            class_name=class_name,
            roll_no=student.roll_no,
            enrollment_no=student.enrollment_no,
            name=student.name,
            father_name=student.father_name,
            gender=student.gender,
        )

    def _build_backlog(self, normalized: Sequence[NormalizedSemester]) -> BacklogSummary:
        backlog_codes: set[str] = set()
        for sem in normalized:
            latest = sem.latest_attempt
            cop_raw = (latest.cop or "").strip()
            if not cop_raw:
                continue
            for part in re.split(r"[,/]", cop_raw):
                token = part.strip()
                if re.fullmatch(r"[A-Z]{2,}\d{3,}", token):
                    backlog_codes.add(token)
        codes = sorted(backlog_codes)
        return BacklogSummary(
            has_active_backlog=bool(codes),
            active_backlog_codes=codes,
            active_backlog_count=len(codes),
        )

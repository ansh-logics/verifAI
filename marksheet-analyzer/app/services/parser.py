from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

import fitz
import pdfplumber

from app.models.response_model import SemesterAttempt, StudentInfo, SubjectEntry


class MarksheetParsingError(Exception):
    """Raised when marksheet parsing fails."""


def _extract_text_pdf_pymupdf(file_path: Path) -> str:
    chunks: list[str] = []
    with fitz.open(file_path) as doc:
        for page in doc:
            chunks.append(page.get_text("text"))
    return "\n".join(chunks)


def _extract_text_pdf_pdfplumber(file_path: Path) -> str:
    chunks: list[str] = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            chunks.append(page.extract_text() or "")
    return "\n".join(chunks)


def extract_marksheet_text(file_path: Path) -> str:
    if file_path.suffix.lower() != ".pdf":
        raise MarksheetParsingError("Unsupported marksheet type. Please upload PDF.")

    candidates: list[tuple[str, str]] = []
    for name, parser in (("pymupdf", _extract_text_pdf_pymupdf), ("pdfplumber", _extract_text_pdf_pdfplumber)):
        try:
            text = parser(file_path)
        except Exception:
            text = ""
        if text.strip():
            candidates.append((name, text))

    if not candidates:
        raise MarksheetParsingError("Unable to extract readable text from marksheet PDF.")

    def score(text: str) -> int:
        # Prefer extraction that preserves semantic anchors and row-like subject lines.
        anchor_hits = 0
        anchor_hits += len(re.findall(r"Semester\s*:\s*\d+", text))
        anchor_hits += len(re.findall(r"Session\s*:", text))
        anchor_hits += len(re.findall(r"Result Status\s*:", text))
        anchor_hits += len(re.findall(r"SGPA\s*:", text))
        subject_rows = len(
            re.findall(r"^[A-Z]{2,}[A-Z0-9]{3,}.*(?:Theory|Practical|CA).*$", text, flags=re.M)
        )
        return (anchor_hits * 20) + (subject_rows * 3) + min(len(text) // 200, 50)

    _, best_text = max(candidates, key=lambda item: score(item[1]))
    return best_text


def _clean_line(line: str) -> str:
    line = line.replace("\t", " ")
    line = re.sub(r"\s+", " ", line).strip()
    return line


def _normalize_for_block_parsing(text: str) -> str:
    """Insert line breaks before key anchors seen in flattened PDF text."""
    normalized = text.replace("\r", "\n")
    anchors = [
        r"Session\s*:",
        r"Semester\s*:",
        r"Result Status\s*:",
        r"Date of Declaration\s*:",
        r"Code\s+Name\s+Type\s+Internal\s+External\s+Back\s+Paper\s+Grade",
        r"No Result found for the above semester\.",
    ]
    for anchor in anchors:
        normalized = re.sub(rf"\s+({anchor})", r"\n\1", normalized)
    return normalized


def _skip_noise(line: str) -> bool:
    return (
        not line
        or "One View by AKTU SDC Team" in line
        or line.startswith("about:blank")
        or re.match(r"^-- \d+ of \d+ --$", line) is not None
        or line.startswith("AKTU-One-View")
        or line.startswith("Print One")
    )


def _extract_student_info(text: str) -> StudentInfo:
    def find(pattern: str) -> str:
        m = re.search(pattern, text, flags=re.IGNORECASE)
        return m.group(1).strip() if m else ""

    institute_code = ""
    institute_name = ""
    course_code = ""
    course_name = ""
    branch_code = ""
    branch_name = ""

    # Primary layout in current AKTU PDF extraction.
    inst_simple = re.search(r"Institute Code\s*:\s*\((\d+)\s*\)\s*([^\n]+)", text, flags=re.IGNORECASE)
    if inst_simple:
        institute_code = inst_simple.group(1).strip()
        institute_name = inst_simple.group(2).strip()

    course_simple = re.search(r"Course Code[\s\S]{0,60}:\s*\((\d+)\)\s*([^:\n]+)", text, flags=re.IGNORECASE)
    if course_simple:
        course_code = course_simple.group(1).strip()
        course_name = re.sub(r"\s+", " ", course_simple.group(2)).strip()

    # In this layout, branch appears as "(153) COMPUTER SCIENCE AND ... Course Code & Branch Code &"
    branch_simple = re.search(
        r"\((\d{3})\)\s*([A-Z][A-Z\s()&\-]+?)\s*Course Code\s*&\s*Branch Code",
        text,
        flags=re.IGNORECASE,
    )
    if branch_simple:
        branch_code = branch_simple.group(1).strip()
        branch_name = re.sub(r"\s+", " ", branch_simple.group(2)).strip()
        if branch_name.endswith(" AND"):
            branch_name = branch_name[: -len(" AND")].strip()

    # Fallbacks for alternate extractions.
    if not institute_code:
        inst_m = re.search(r"Institute Code[\s\S]{0,120}?Name\s*:\s*\((\d+)\s*\)\s*([^\n]+)", text, flags=re.IGNORECASE)
        if inst_m:
            institute_code = inst_m.group(1).strip()
            institute_name = inst_m.group(2).strip()

    if not course_code:
        course_m = re.search(
            r"Course Code[\s\S]{0,120}?Name\s*:\s*\((\d+)\s*\)\s*([^\n]+)",
            text,
            flags=re.IGNORECASE,
        )
        if course_m:
            course_code = course_m.group(1).strip()
            course_name = course_m.group(2).strip()

    if not branch_code:
        branch_m = re.search(
            r"Branch Code[\s\S]{0,200}?Name\s*:\s*\((\d+)\s*\)\s*([^\n]+(?:\n[^\n:]+){0,4})",
            text,
            flags=re.IGNORECASE,
        )
        if branch_m:
            branch_code = branch_m.group(1).strip()
            raw_branch = branch_m.group(2).split("RollNo", 1)[0]
            branch_name = re.sub(r"\s+", " ", raw_branch).strip()

    roll_no = find(r"RollNo\s*:\s*([A-Z0-9]+)")
    enrollment_no = find(r"EnrollmentNo\s*:\s*([A-Z0-9]+)")

    name_match = re.search(r"\bName\s*:\s*([^\n]+?)\s+Hindi Name", text)
    name = name_match.group(1).strip() if name_match else ""

    father_name = find(r"Father's Name\s*:\s*([^\n]+?)\s+Gender")
    gender = find(r"Gender\s*:\s*([A-Z])")

    return StudentInfo(
        institute_code=institute_code,
        institute_name=institute_name,
        course_code=course_code,
        course_name=course_name,
        branch_code=branch_code,
        branch_name=branch_name,
        roll_no=roll_no,
        enrollment_no=enrollment_no,
        name=name,
        father_name=father_name,
        gender=gender,
    )


def _safe_int(token: str) -> int | None:
    if token is None:
        return None
    token = token.strip()
    if not token or token == "--":
        return None
    m = re.search(r"\d+", token)
    if not m:
        return None
    return int(m.group(0))


def _safe_float(token: str) -> float | None:
    if token is None:
        return None
    token = token.strip()
    if not token:
        return None
    try:
        return float(token)
    except ValueError:
        return None


def _parse_subject_line(line: str) -> SubjectEntry | None:
    if not re.match(r"^[A-Z]{2,}[A-Z0-9]{3,}\s+", line):
        return None

    tokens = line.split()
    if len(tokens) < 4:
        return None

    code = tokens[0]
    type_idx = -1
    for i, token in enumerate(tokens):
        if token not in {"Theory", "Practical", "CA"}:
            continue
        next_token = tokens[i + 1] if i + 1 < len(tokens) else ""
        if re.match(r"^\d+$", next_token) or next_token == "--":
            type_idx = i
            break
    if type_idx == -1:
        # Fallback to the last type token for lines where numeric token is malformed.
        for i in range(len(tokens) - 1, -1, -1):
            if tokens[i] in {"Theory", "Practical", "CA"}:
                type_idx = i
                break
    if type_idx < 2:
        return None

    name = " ".join(tokens[1:type_idx]).strip()
    subject_type = tokens[type_idx]
    tail = tokens[type_idx + 1 :]

    internal = tail[0] if len(tail) > 0 else ""
    external = tail[1] if len(tail) > 1 else ""
    back_paper = tail[2] if len(tail) > 2 else ""
    grade = tail[3] if len(tail) > 3 else ""

    return SubjectEntry(
        code=code,
        name=name,
        type=subject_type,
        internal=internal,
        external=external,
        back_paper=back_paper,
        grade=grade,
    )


def _parse_marks_pair(text: str) -> tuple[int | None, int | None]:
    m = re.search(r"Marks\s*:\s*(\d+)\s*/\s*(\d+)", text)
    if not m:
        return None, None
    return int(m.group(1)), int(m.group(2))


def parse_declaration_date(value: str) -> datetime | None:
    raw = value.strip()
    if not raw:
        return None
    for fmt in ("%d/%m/%y", "%d/%m/%Y", "%d-%m-%y", "%d-%m-%Y"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


def parse_marksheet_text(text: str) -> tuple[StudentInfo, list[SemesterAttempt], list[str]]:
    student = _extract_student_info(text)
    normalized_text = _normalize_for_block_parsing(text)
    lines = [_clean_line(x) for x in normalized_text.splitlines()]
    warnings: list[str] = []

    attempts: list[dict[str, Any]] = []
    current_session: dict[str, Any] = {
        "session": "",
        "result_status_session": "",
        "marks_obtained": None,
        "marks_total": None,
        "cop": "",
    }
    current: dict[str, Any] | None = None

    def flush() -> None:
        nonlocal current
        if current is None:
            return
        attempts.append(current)
        current = None

    for idx, line in enumerate(lines):
        if _skip_noise(line):
            continue

        if re.search(r"\bSession\s*:", line):
            flush()
            sm = re.search(r"Session\s*:\s*(.+?)(?:\s+Semesters\s*:|$)", line)
            rm = re.search(r"Result\s*:\s*([^\n]+?)(?:\s+Marks\s*:|\s+COP\s*:|$)", line)
            copm = re.search(r"COP\s*:\s*([^\n]+?)(?:\s+Audit|$)", line)
            marks_obt, marks_total = _parse_marks_pair(line)
            result_status = rm.group(1).strip() if rm else ""
            if result_status.lower().startswith("marks"):
                result_status = ""
            cop_value = copm.group(1).strip() if copm else ""
            if cop_value.lower().startswith("audit"):
                cop_value = ""
            current_session = {
                "session": sm.group(1).strip() if sm else "",
                "result_status_session": result_status,
                "marks_obtained": marks_obt,
                "marks_total": marks_total,
                "cop": cop_value,
            }
            continue

        if re.search(r"\bSemester\s*:", line):
            flush()
            sem_m = re.search(r"Semester\s*:\s*(\d+)", line)
            eo_m = re.search(r"Even/Odd\s*:\s*([A-Za-z]+)", line)
            if not sem_m:
                continue
            current = {
                "attempt_index": len(attempts),
                "session": current_session.get("session", ""),
                "semester_no": int(sem_m.group(1)),
                "even_odd": eo_m.group(1) if eo_m else "",
                "result_status_session": current_session.get("result_status_session", ""),
                "result_status_semester": "",
                "marks_obtained": current_session.get("marks_obtained"),
                "marks_total": current_session.get("marks_total"),
                "cop": current_session.get("cop", ""),
                "sgpa_pdf": None,
                "declaration_date": "",
                "subjects": [],
            }
            continue

        if current is None:
            continue

        if "Result Status" in line and "SGPA" in line:
            rs = re.search(r"Result Status\s*:\s*([^\n]+?)\s+SGPA\s*:\s*([0-9.]+)", line)
            if rs:
                current["result_status_semester"] = rs.group(1).strip()
                current["sgpa_pdf"] = _safe_float(rs.group(2))
            else:
                sg = re.search(r"SGPA\s*:\s*([0-9.]+)", line)
                if sg:
                    current["sgpa_pdf"] = _safe_float(sg.group(1))
            continue

        if line.startswith("Date of Declaration"):
            dm = re.search(r"Date of Declaration\s*:\s*(.*)$", line)
            current["declaration_date"] = dm.group(1).strip() if dm else ""
            continue

        subject = _parse_subject_line(line)
        if subject:
            current["subjects"].append(subject)
            continue

        if line.startswith("No Result found"):
            warnings.append(f"No result block encountered near line {idx + 1}.")

    flush()

    if not attempts:
        raise MarksheetParsingError("Could not parse any semester attempts from marksheet.")

    parsed_attempts = [SemesterAttempt(**a) for a in attempts]
    for a in parsed_attempts:
        if a.sgpa_pdf is None:
            warnings.append(f"Missing SGPA for semester {a.semester_no} attempt {a.attempt_index + 1}.")

    return student, parsed_attempts, warnings

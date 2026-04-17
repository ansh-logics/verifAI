from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import text

from app.database.database import SessionLocal
from app.database.models import RawUpload, Student, StudentProfile

DEMO_STUDENTS: list[dict] = [
    {
        "name": "Aarav Sharma",
        "email": "aarav.sharma.demo@verifai.dev",
        "phone": "+919910000101",
        "roll_no": "AKTU-CSE-001",
        "branch": "CSE",
        "cgpa": 9.2,
        "gender": "men",
        "skills": ["python", "django", "react", "postgresql"],
        "coding_persona": "competitive",
        "coding_score": 88.0,
        "academic_score": 91.0,
        "overall_score": 89.2,
        "has_active_backlog": False,
        "is_placed": False,
        "resume_url": "https://demo-resumes.verifai.dev/aarav-sharma.pdf",
    },
    {
        "name": "Isha Verma",
        "email": "isha.verma.demo@verifai.dev",
        "phone": "+919910000102",
        "roll_no": "AKTU-IT-014",
        "branch": "IT",
        "cgpa": 8.7,
        "gender": "women",
        "skills": ["javascript", "react", "ui/ux design", "figma"],
        "coding_persona": "frontend",
        "coding_score": 82.0,
        "academic_score": 86.0,
        "overall_score": 83.6,
        "has_active_backlog": False,
        "is_placed": True,
        "resume_url": "https://demo-resumes.verifai.dev/isha-verma.pdf",
    },
    {
        "name": "Neel Rao",
        "email": "neel.rao.demo@verifai.dev",
        "phone": "+919910000103",
        "roll_no": "AKTU-AIML-023",
        "branch": "AIML",
        "cgpa": 7.9,
        "gender": "other",
        "skills": ["python", "pytorch", "mlops", "docker"],
        "coding_persona": "ml_engineer",
        "coding_score": 79.0,
        "academic_score": 78.0,
        "overall_score": 78.6,
        "has_active_backlog": True,
        "is_placed": False,
        "resume_url": "https://demo-resumes.verifai.dev/neel-rao.pdf",
    },
    {
        "name": "Sneha Singh",
        "email": "sneha.singh.demo@verifai.dev",
        "phone": "+919910000104",
        "roll_no": "AKTU-DS-031",
        "branch": "DS",
        "cgpa": 9.5,
        "gender": "women",
        "skills": ["python", "sql", "data analysis", "power bi"],
        "coding_persona": "data_analyst",
        "coding_score": 84.0,
        "academic_score": 93.0,
        "overall_score": 87.6,
        "has_active_backlog": False,
        "is_placed": False,
        "resume_url": "https://demo-resumes.verifai.dev/sneha-singh.pdf",
    },
    {
        "name": "Rahul Yadav",
        "email": "rahul.yadav.demo@verifai.dev",
        "phone": "+919910000105",
        "roll_no": "AKTU-EE-044",
        "branch": "EEE",
        "cgpa": 6.8,
        "gender": "men",
        "skills": ["embedded c", "pcb design", "matlab"],
        "coding_persona": "core_engineering",
        "coding_score": 68.0,
        "academic_score": 70.0,
        "overall_score": 68.8,
        "has_active_backlog": True,
        "is_placed": False,
        "resume_url": "https://demo-resumes.verifai.dev/rahul-yadav.pdf",
    },
    {
        "name": "Pooja Nair",
        "email": "pooja.nair.demo@verifai.dev",
        "phone": "+919910000106",
        "roll_no": "AKTU-ME-052",
        "branch": "ME",
        "cgpa": 7.2,
        "gender": "women",
        "skills": ["autocad", "solidworks", "project management"],
        "coding_persona": "product_builder",
        "coding_score": 61.0,
        "academic_score": 74.0,
        "overall_score": 66.2,
        "has_active_backlog": False,
        "is_placed": True,
        "resume_url": "https://demo-resumes.verifai.dev/pooja-nair.pdf",
    },
]


def reset_demo_tables() -> None:
    with SessionLocal() as db:
        db.execute(text("TRUNCATE TABLE raw_uploads, student_profiles, students RESTART IDENTITY CASCADE"))
        db.commit()


def upsert_demo_students() -> None:
    now = datetime.now(UTC)
    with SessionLocal() as db:
        for entry in DEMO_STUDENTS:
            student = db.query(Student).filter(Student.email == entry["email"]).one_or_none()
            if student is None:
                student = Student(
                    name=entry["name"],
                    email=entry["email"],
                    roll_no=entry["roll_no"],
                    password_hash="",
                    phone=entry["phone"],
                    branch=entry["branch"],
                    cgpa=entry["cgpa"],
                    gender=entry["gender"],
                    cgpa_verified=True,
                )
                db.add(student)
                db.flush()
            else:
                student.name = entry["name"]
                student.roll_no = entry["roll_no"]
                student.phone = entry["phone"]
                student.branch = entry["branch"]
                student.cgpa = entry["cgpa"]
                student.gender = entry["gender"]
                student.cgpa_verified = True

            profile = db.query(StudentProfile).filter(StudentProfile.student_id == student.id).one_or_none()
            resume_data = {
                "file_name": f"{entry['roll_no'].lower()}.pdf",
                "summary": f"Demo resume for {entry['name']}",
                "metadata": {
                    "has_active_backlog": entry["has_active_backlog"],
                    "is_placed": entry["is_placed"],
                },
            }
            academic_data = {
                "cgpa_computed": entry["cgpa"],
                "has_active_backlog": entry["has_active_backlog"],
            }
            github_data = {
                "username": entry["roll_no"].lower().replace("-", "_"),
                "repos": int(entry["coding_score"] // 5),
                "languages": entry["skills"][:3],
            }
            leetcode_data = {
                "username": entry["roll_no"].lower().replace("-", ""),
                "total_solved": int(entry["coding_score"] * 3),
                "easy": int(entry["coding_score"]),
                "medium": int(entry["coding_score"] * 1.5),
                "hard": int(entry["coding_score"] * 0.4),
            }

            if profile is None:
                profile = StudentProfile(
                    student_id=student.id,
                    skills=entry["skills"],
                    skills_json=entry["skills"],
                    coding_persona=entry["coding_persona"],
                    coding_score=entry["coding_score"],
                    academic_score=entry["academic_score"],
                    overall_score=entry["overall_score"],
                    github_data=github_data,
                    leetcode_data=leetcode_data,
                    resume_data=resume_data,
                    academic_data=academic_data,
                    last_analyzed_at=now,
                )
                db.add(profile)
            else:
                profile.skills = entry["skills"]
                profile.skills_json = entry["skills"]
                profile.coding_persona = entry["coding_persona"]
                profile.coding_score = entry["coding_score"]
                profile.academic_score = entry["academic_score"]
                profile.overall_score = entry["overall_score"]
                profile.github_data = github_data
                profile.leetcode_data = leetcode_data
                profile.resume_data = resume_data
                profile.academic_data = academic_data
                profile.last_analyzed_at = now

            raw_upload = db.query(RawUpload).filter(RawUpload.student_id == student.id).one_or_none()
            if raw_upload is None:
                raw_upload = RawUpload(
                    student_id=student.id,
                    resume_url=entry["resume_url"],
                    marksheet_url=None,
                )
                db.add(raw_upload)
            else:
                raw_upload.resume_url = entry["resume_url"]
                raw_upload.marksheet_url = None
                raw_upload.uploaded_at = now

        db.commit()


if __name__ == "__main__":
    reset_demo_tables()
    upsert_demo_students()
    print(f"Seeded {len(DEMO_STUDENTS)} demo students.")

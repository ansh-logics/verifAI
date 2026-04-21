from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.api.routes import router as analyzer_router
from app.api.student import router as student_router
from search_engine.routes import router as search_router
from app.config import get_settings
from app.database.database import Base, engine
from app.logging_config import configure_logging

settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(
    title="VeriAI Master Service",
    version="1.0.0",
    description="Orchestrates resume and coding profile analyzers.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = Path(__file__).resolve().parent / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

app.include_router(analyzer_router)
app.include_router(student_router)
app.include_router(search_router)


def _apply_startup_schema_updates() -> None:
    # Keep legacy deployments working when new auth columns are introduced.
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE students ADD COLUMN IF NOT EXISTS roll_no VARCHAR(64)"))
        conn.execute(text("ALTER TABLE students ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255) DEFAULT ''"))
        conn.execute(text("ALTER TABLE students ADD COLUMN IF NOT EXISTS gender VARCHAR(16)"))
        conn.execute(text("ALTER TABLE students ADD COLUMN IF NOT EXISTS has_active_backlog BOOLEAN DEFAULT FALSE"))
        conn.execute(text("UPDATE students SET password_hash = '' WHERE password_hash IS NULL"))
        conn.execute(text("UPDATE students SET gender = 'other' WHERE gender IS NULL OR trim(gender) = ''"))
        conn.execute(text("ALTER TABLE students ALTER COLUMN password_hash SET NOT NULL"))
        conn.execute(text("ALTER TABLE students ALTER COLUMN gender SET NOT NULL"))
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ux_students_roll_no_unique ON students (roll_no)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_students_roll_no_lookup ON students (roll_no)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_students_gender ON students (gender)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_students_backlog ON students (has_active_backlog)"))

        # Keep student_profiles compatible with newer schema that mirrors skills in JSON.
        conn.execute(text("ALTER TABLE student_profiles ADD COLUMN IF NOT EXISTS skills_json JSON"))
        conn.execute(text("UPDATE student_profiles SET skills_json = to_json(skills) WHERE skills_json IS NULL"))
        conn.execute(text("ALTER TABLE student_profiles ALTER COLUMN skills_json SET DEFAULT '[]'::json"))
        conn.execute(text("ALTER TABLE student_profiles ALTER COLUMN skills_json SET NOT NULL"))
        conn.execute(text("ALTER TABLE tpo_analysis_groups ADD COLUMN IF NOT EXISTS company_name VARCHAR(255)"))
        conn.execute(text("ALTER TABLE tpo_analysis_groups ADD COLUMN IF NOT EXISTS role_type VARCHAR(32)"))
        conn.execute(text("ALTER TABLE tpo_analysis_groups ADD COLUMN IF NOT EXISTS pay_or_stipend VARCHAR(128)"))
        conn.execute(text("ALTER TABLE tpo_analysis_groups ADD COLUMN IF NOT EXISTS duration VARCHAR(128)"))
        conn.execute(text("ALTER TABLE tpo_analysis_groups ADD COLUMN IF NOT EXISTS bond_details TEXT"))
        conn.execute(text("ALTER TABLE tpo_analysis_groups ADD COLUMN IF NOT EXISTS interview_timezone VARCHAR(64)"))


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    _apply_startup_schema_updates()

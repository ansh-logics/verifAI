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

# CORS middleware MUST be added first to take precedence
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
    # Canonical student email model is single-field: students.email.
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
        conn.execute(text("DROP INDEX IF EXISTS ix_students_test_email_lookup"))
        conn.execute(text("DROP INDEX IF EXISTS ix_students_real_email_lookup"))
        conn.execute(text("DROP INDEX IF EXISTS ix_students_preferred_email_type"))
        conn.execute(text("ALTER TABLE students DROP COLUMN IF EXISTS test_email"))
        conn.execute(text("ALTER TABLE students DROP COLUMN IF EXISTS real_email"))
        conn.execute(text("ALTER TABLE students DROP COLUMN IF EXISTS preferred_email_type"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_students_gender ON students (gender)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_students_backlog ON students (has_active_backlog)"))

        # Keep student_profiles compatible with newer schema that mirrors skills in JSON.
        conn.execute(text("ALTER TABLE student_profiles ADD COLUMN IF NOT EXISTS skills_json JSON"))
        conn.execute(text("UPDATE student_profiles SET skills_json = to_json(skills) WHERE skills_json IS NULL"))
        conn.execute(text("ALTER TABLE student_profiles ALTER COLUMN skills_json SET DEFAULT '[]'::json"))
        conn.execute(text("ALTER TABLE student_profiles ALTER COLUMN skills_json SET NOT NULL"))
        conn.execute(
            text(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS ux_student_profiles_github_username
                ON student_profiles ((lower(trim(github_data->>'username'))))
                WHERE trim(coalesce(github_data->>'username', '')) <> ''
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS ux_student_profiles_leetcode_username
                ON student_profiles ((lower(trim(leetcode_data->>'username'))))
                WHERE trim(coalesce(leetcode_data->>'username', '')) <> ''
                """
            )
        )
        conn.execute(text("ALTER TABLE tpo_analysis_groups ADD COLUMN IF NOT EXISTS company_name VARCHAR(255)"))
        conn.execute(text("ALTER TABLE tpo_analysis_groups ADD COLUMN IF NOT EXISTS role_type VARCHAR(32)"))
        conn.execute(text("ALTER TABLE tpo_analysis_groups ADD COLUMN IF NOT EXISTS pay_or_stipend VARCHAR(128)"))
        conn.execute(text("ALTER TABLE tpo_analysis_groups ADD COLUMN IF NOT EXISTS duration VARCHAR(128)"))
        conn.execute(text("ALTER TABLE tpo_analysis_groups ADD COLUMN IF NOT EXISTS bond_details TEXT"))
        conn.execute(text("ALTER TABLE tpo_analysis_groups ADD COLUMN IF NOT EXISTS jd_topics JSON"))
        conn.execute(text("ALTER TABLE tpo_analysis_groups ADD COLUMN IF NOT EXISTS jd_key_points JSON"))
        conn.execute(text("UPDATE tpo_analysis_groups SET jd_topics = '[]'::json WHERE jd_topics IS NULL"))
        conn.execute(text("UPDATE tpo_analysis_groups SET jd_key_points = '[]'::json WHERE jd_key_points IS NULL"))
        conn.execute(text("ALTER TABLE tpo_analysis_groups ALTER COLUMN jd_topics SET DEFAULT '[]'::json"))
        conn.execute(text("ALTER TABLE tpo_analysis_groups ALTER COLUMN jd_key_points SET DEFAULT '[]'::json"))
        conn.execute(text("ALTER TABLE tpo_analysis_groups ALTER COLUMN jd_topics SET NOT NULL"))
        conn.execute(text("ALTER TABLE tpo_analysis_groups ALTER COLUMN jd_key_points SET NOT NULL"))
        conn.execute(text("ALTER TABLE tpo_analysis_groups ADD COLUMN IF NOT EXISTS interview_timezone VARCHAR(64)"))
        conn.execute(text("ALTER TABLE tpo_analysis_groups ADD COLUMN IF NOT EXISTS total_rounds INTEGER DEFAULT 1"))
        conn.execute(text("ALTER TABLE tpo_analysis_groups ADD COLUMN IF NOT EXISTS current_round_no INTEGER DEFAULT 1"))
        conn.execute(text("ALTER TABLE tpo_analysis_groups ADD COLUMN IF NOT EXISTS round_state VARCHAR(32) DEFAULT 'in_progress'"))
        conn.execute(text("UPDATE tpo_analysis_groups SET total_rounds = 1 WHERE total_rounds IS NULL OR total_rounds < 1"))
        conn.execute(text("UPDATE tpo_analysis_groups SET current_round_no = 1 WHERE current_round_no IS NULL OR current_round_no < 1"))
        conn.execute(
            text(
                """
                UPDATE tpo_analysis_groups
                SET round_state = 'in_progress'
                WHERE round_state IS NULL OR trim(round_state) = ''
                """
            )
        )
        conn.execute(text("ALTER TABLE tpo_analysis_groups ALTER COLUMN total_rounds SET NOT NULL"))
        conn.execute(text("ALTER TABLE tpo_analysis_groups ALTER COLUMN current_round_no SET NOT NULL"))
        conn.execute(text("ALTER TABLE tpo_analysis_groups ALTER COLUMN round_state SET NOT NULL"))
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS tpo_settings (
                    id SERIAL PRIMARY KEY,
                    tpo_username VARCHAR(128) UNIQUE NOT NULL,
                    display_name VARCHAR(255),
                    contact_number VARCHAR(32),
                    institute_name VARCHAR(255),
                    sender_name VARCHAR(255),
                    reply_to_email VARCHAR(255),
                    default_timezone VARCHAR(64),
                    stale_group_reminder_enabled BOOLEAN NOT NULL DEFAULT TRUE,
                    daily_queue_summary_enabled BOOLEAN NOT NULL DEFAULT TRUE,
                    placement_update_confirmation_enabled BOOLEAN NOT NULL DEFAULT TRUE,
                    tpo_password_hash VARCHAR(255),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
        )
        conn.execute(text("ALTER TABLE tpo_settings ADD COLUMN IF NOT EXISTS display_name VARCHAR(255)"))
        conn.execute(text("ALTER TABLE tpo_settings ADD COLUMN IF NOT EXISTS contact_number VARCHAR(32)"))
        conn.execute(text("ALTER TABLE tpo_settings ADD COLUMN IF NOT EXISTS institute_name VARCHAR(255)"))
        conn.execute(text("ALTER TABLE tpo_settings ADD COLUMN IF NOT EXISTS sender_name VARCHAR(255)"))
        conn.execute(text("ALTER TABLE tpo_settings ADD COLUMN IF NOT EXISTS reply_to_email VARCHAR(255)"))
        conn.execute(text("ALTER TABLE tpo_settings ADD COLUMN IF NOT EXISTS default_timezone VARCHAR(64)"))
        conn.execute(text("ALTER TABLE tpo_settings ADD COLUMN IF NOT EXISTS stale_group_reminder_enabled BOOLEAN DEFAULT TRUE"))
        conn.execute(text("ALTER TABLE tpo_settings ADD COLUMN IF NOT EXISTS daily_queue_summary_enabled BOOLEAN DEFAULT TRUE"))
        conn.execute(
            text("ALTER TABLE tpo_settings ADD COLUMN IF NOT EXISTS placement_update_confirmation_enabled BOOLEAN DEFAULT TRUE")
        )
        conn.execute(text("ALTER TABLE tpo_settings ADD COLUMN IF NOT EXISTS tpo_password_hash VARCHAR(255)"))
        conn.execute(text("ALTER TABLE tpo_settings ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW()"))
        conn.execute(text("ALTER TABLE tpo_settings ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW()"))
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ux_tpo_settings_username ON tpo_settings (tpo_username)"))
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS tpo_mail_jobs (
                    id SERIAL PRIMARY KEY,
                    group_id INTEGER NOT NULL REFERENCES tpo_analysis_groups(id) ON DELETE CASCADE,
                    requested_by VARCHAR(128) NOT NULL,
                    mail_type VARCHAR(64) NOT NULL,
                    status VARCHAR(32) NOT NULL DEFAULT 'queued',
                    total_recipients INTEGER NOT NULL DEFAULT 0,
                    processed_count INTEGER NOT NULL DEFAULT 0,
                    success_count INTEGER NOT NULL DEFAULT 0,
                    failure_count INTEGER NOT NULL DEFAULT 0,
                    last_error TEXT,
                    started_at TIMESTAMPTZ,
                    finished_at TIMESTAMPTZ,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
        )
        conn.execute(
            text(
                "ALTER TABLE tpo_mail_jobs ADD COLUMN IF NOT EXISTS group_id INTEGER REFERENCES tpo_analysis_groups(id) ON DELETE CASCADE"
            )
        )
        conn.execute(text("ALTER TABLE tpo_mail_jobs ADD COLUMN IF NOT EXISTS requested_by VARCHAR(128)"))
        conn.execute(text("ALTER TABLE tpo_mail_jobs ADD COLUMN IF NOT EXISTS mail_type VARCHAR(64)"))
        conn.execute(text("ALTER TABLE tpo_mail_jobs ADD COLUMN IF NOT EXISTS round_no INTEGER"))
        conn.execute(text("ALTER TABLE tpo_mail_jobs ADD COLUMN IF NOT EXISTS outcome VARCHAR(32)"))
        conn.execute(text("ALTER TABLE tpo_mail_jobs ADD COLUMN IF NOT EXISTS status VARCHAR(32) DEFAULT 'queued'"))
        conn.execute(text("ALTER TABLE tpo_mail_jobs ADD COLUMN IF NOT EXISTS total_recipients INTEGER DEFAULT 0"))
        conn.execute(text("ALTER TABLE tpo_mail_jobs ADD COLUMN IF NOT EXISTS processed_count INTEGER DEFAULT 0"))
        conn.execute(text("ALTER TABLE tpo_mail_jobs ADD COLUMN IF NOT EXISTS success_count INTEGER DEFAULT 0"))
        conn.execute(text("ALTER TABLE tpo_mail_jobs ADD COLUMN IF NOT EXISTS failure_count INTEGER DEFAULT 0"))
        conn.execute(text("ALTER TABLE tpo_mail_jobs ADD COLUMN IF NOT EXISTS last_error TEXT"))
        conn.execute(text("ALTER TABLE tpo_mail_jobs ADD COLUMN IF NOT EXISTS started_at TIMESTAMPTZ"))
        conn.execute(text("ALTER TABLE tpo_mail_jobs ADD COLUMN IF NOT EXISTS finished_at TIMESTAMPTZ"))
        conn.execute(text("ALTER TABLE tpo_mail_jobs ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW()"))
        conn.execute(text("ALTER TABLE tpo_mail_jobs ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW()"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_tpo_mail_jobs_group_id ON tpo_mail_jobs (group_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_tpo_mail_jobs_status ON tpo_mail_jobs (status)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_tpo_mail_jobs_round_no ON tpo_mail_jobs (round_no)"))
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS tpo_group_rounds (
                    id SERIAL PRIMARY KEY,
                    group_id INTEGER NOT NULL REFERENCES tpo_analysis_groups(id) ON DELETE CASCADE,
                    round_no INTEGER NOT NULL,
                    status VARCHAR(32) NOT NULL DEFAULT 'in_progress',
                    finalized_at TIMESTAMPTZ,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_tpo_group_rounds_group_id ON tpo_group_rounds (group_id)"))
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ux_tpo_group_round_unique ON tpo_group_rounds (group_id, round_no)"))
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS tpo_group_round_members (
                    id SERIAL PRIMARY KEY,
                    round_id INTEGER NOT NULL REFERENCES tpo_group_rounds(id) ON DELETE CASCADE,
                    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
                    status VARCHAR(32) NOT NULL DEFAULT 'pending',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_tpo_group_round_members_round_id ON tpo_group_round_members (round_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_tpo_group_round_members_student_id ON tpo_group_round_members (student_id)"))
        conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS ux_tpo_group_round_member_unique ON tpo_group_round_members (round_id, student_id)"
            )
        )


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    _apply_startup_schema_updates()

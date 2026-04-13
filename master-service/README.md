# Master service (orchestrator)

Calls **resume-analyzer**, **coding-analyzer**, and optional **marksheet-analyzer** in parallel, merging JSON into one report aligned with the TPO ingestion shape described in [`docs/TPO_MATCHING_AND_JD_PLAN.md`](../docs/TPO_MATCHING_AND_JD_PLAN.md). Serves a small HTML UI at `/`.

## Run with Docker Compose (repo root)

```bash
docker compose -f docker-compose.dev.yml up -d
```

- Master UI: http://localhost:18082  
- Coding analyzer: http://localhost:18080  
- Resume analyzer: http://localhost:18081  
- Marksheet analyzer: http://localhost:18083  

## Run locally (uvicorn)

1. Start the analyzers (Docker or local) and set URLs in `.env` (see `.env.example`).
2. Install and run:

```bash
cd master-service
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Form UI |
| GET | `/health` | Liveness |
| POST | `/analyze-profile` | `multipart/form-data`: `file` (PDF/DOCX), optional `marksheet_file` (PDF), **`branch`** (required), optional `github_username`, `leetcode_username`, `codeforces_username` |

Returns JSON with **`report_version`: 2**, **`generated_at`**, normalized **`student`**, **`academics`** (from marksheet when provided), and **`profile`**, raw downstream payloads under **`sources`**, and status fields **`resume_ok`**, **`resume_error`**, **`coding_ok`**, **`coding_skipped`**, **`coding_error`**, **`marksheet_ok`**, **`marksheet_skipped`**, **`marksheet_error`**. HTTP **502** only if both resume and coding fail; **200** for partial success. **400** if `branch` is missing or whitespace-only.

### Response shape (summary)

- **`student`**: Identity and placement fields for a future `students` row: `name`, `email`, `phone`, `cgpa`, optional **`cgpa_numeric`** (parsed when possible), **`branch`** (from the form), platform usernames, **`resume_url`** (always `null` until object storage exists), **`resume_filename`**.
- **`academics`**: Marksheet summary fields when a marksheet is uploaded: `cgpa_computed`, `last_semester_number`, `last_semester_sgpa`, `has_active_backlog`, `active_backlog_codes`.
- **`profile`**: Normalized aggregates for a future `student_profiles` row: **`resume_skills`** (trimmed, lowercased, deduplicated), **`coding_persona`**, **`github_stats`** (`repos`, `commits_30d`, `languages`), **`leetcode_stats`** (`total_solved`, `easy`, `medium`, `hard`), optional **`codeforces_summary`**.
- **`sources`**: Raw JSON from resume-analyzer, coding-analyzer, and marksheet-analyzer when each call succeeded (`resume` / `coding` / `marksheet` may be `null` if that side failed or was skipped).

### Example (partial success: resume OK, coding skipped)

```json
{
  "report_version": 2,
  "generated_at": "2026-04-12T12:00:00+00:00",
  "student": {
    "name": "Ada Lovelace",
    "email": "ada@example.edu",
    "phone": "",
    "cgpa": "8.5",
    "cgpa_numeric": 8.5,
    "branch": "CSE",
    "github_username": null,
    "leetcode_username": null,
    "codeforces_username": null,
    "resume_url": null,
    "resume_filename": "resume.pdf",
    "roll_no": "",
    "enrollment_no": "",
    "class_name": ""
  },
  "academics": {
    "cgpa_computed": null,
    "last_semester_number": null,
    "last_semester_sgpa": null,
    "has_active_backlog": false,
    "active_backlog_codes": []
  },
  "profile": {
    "resume_skills": ["python", "sql"],
    "coding_persona": "",
    "github_stats": { "repos": 0, "commits_30d": 0, "languages": [] },
    "leetcode_stats": { "total_solved": 0, "easy": 0, "medium": 0, "hard": 0 },
    "codeforces_summary": null
  },
  "sources": {
    "resume": { },
    "coding": null,
    "marksheet": null
  },
  "resume_ok": true,
  "resume_error": null,
  "coding_ok": false,
  "coding_skipped": true,
  "coding_error": "Provide at least one platform username (GitHub, LeetCode, or Codeforces).",
  "marksheet_ok": false,
  "marksheet_skipped": true,
  "marksheet_error": "Marksheet not provided."
}
```

## Environment

| Variable | Default (Docker network) |
|----------|---------------------------|
| `RESUME_ANALYZER_BASE_URL` | `http://resume-analyzer-dev:8080` |
| `CODING_ANALYZER_BASE_URL` | `http://coding-analyzer-dev:8080` |
| `MARKSHEET_ANALYZER_BASE_URL` | `http://marksheet-analyzer-dev:8080` |
| `RESUME_HTTP_TIMEOUT_S` | `120` |
| `CODING_HTTP_TIMEOUT_S` | `180` |
| `MARKSHEET_HTTP_TIMEOUT_S` | `120` |

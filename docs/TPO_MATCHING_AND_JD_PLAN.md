# TPO matching: JD parser, database, and ranking (future work)

**Status:** Design reference only — not implemented in the repo yet. The live stack today is `resume-analyzer`, `coding-analyzer`, and `master-service` (orchestrator).

Use this document when implementing the TPO flow: paste a JD, parse with an LLM, persist students/profiles in PostgreSQL, rank candidates, and return results.

---

## Part 1: JD parser (LLM-based)

### Sample input (TPO pastes)

```
We are hiring a Full Stack Developer for our startup.

Requirements:
- 2+ years of experience in React and Node.js
- Strong knowledge of MongoDB and PostgreSQL
- Experience with RESTful APIs
- Good problem-solving skills

Preferred:
- Knowledge of Docker and Kubernetes
- Experience with AWS/Azure
- TypeScript proficiency

Freshers with strong project portfolios may also apply.
```

### Sample output (structured JSON)

```json
{
  "role_type": "Full Stack Developer",
  "required_skills": ["React", "Node.js", "MongoDB", "PostgreSQL", "RESTful APIs"],
  "preferred_skills": ["Docker", "Kubernetes", "AWS", "Azure", "TypeScript"],
  "min_experience_years": 2,
  "accepts_freshers": true,
  "key_traits": ["problem-solving"],
  "parsed_at": "2026-04-11T10:30:00Z"
}
```

### Implementation sketch

- **Service:** New module e.g. `app/services/jd_parser.py` with a `JDParser` class.
- **Client:** OpenAI-compatible API (e.g. NVIDIA `https://integrate.api.nvidia.com/v1`) with **`NVIDIA_API_KEY` (or generic `LLM_API_KEY`) from environment only** — never commit keys.
- **Endpoint:** `POST /jd/parse` with body `{ "jd_text": "..." }`.
- **Response model:** `role_type`, `required_skills`, `preferred_skills`, `min_experience_years`, `accepts_freshers`, `key_traits`, `parsed_at` (use timezone-aware UTC, e.g. `datetime.now(UTC).isoformat().replace("+00:00", "Z")`).
- **Robustness:** Strip markdown fences from model output; `json.loads`; on failure fall back to a small rule-based parser and set e.g. `fallback_used: true`.

Prompt rules (summary):

- Return **only** valid JSON matching the schema (no markdown).
- Technical skills only in skill lists; map “freshers may apply” → `accepts_freshers: true`.
- No experience stated → `min_experience_years: 0`.
- Concise skill names (“React” not “React.js framework”).

---

## Part 2: Database schema + ranking (PostgreSQL)

### Tables (SQL)

- **`students`** — identity, email, cgpa, branch, platform usernames, `resume_url`, timestamps.
- **`student_profiles`** — one row per student: GitHub / LeetCode / Codeforces aggregates, `coding_persona`, `resume_skills`, optional `JSONB` blobs, `last_analyzed_at`.
- **`tpo_users`** — TPO auth (hashed passwords).
- **`search_logs`** — optional analytics: `jd_text`, `jd_parsed_json`, `results_count`, `searched_at`.

Indexes: GIN on `github_languages`, `resume_skills`; btree on `student_id`, `coding_persona` as in the original design.

### SQLAlchemy

- `app/database/models.py` — `Student`, `StudentProfile`, `TPOUser` mapped to the tables above.
- `app/database/database.py` — engine, session, `get_db` for FastAPI `Depends`.

### Ranking engine

- **`StudentRanker`** in e.g. `app/services/ranking_engine.py`.
- **Weights:** required_skills 40, preferred_skills 15, github_activity 20, problem_solving 15, persona_match 10.
- **Flow:** join `Student` + `StudentProfile`, optional filters (`min_cgpa`, `branch`), optional overlap pre-filter on required skills vs `github_languages` / `resume_skills`, score each row, sort descending.
- **Persona match:** map `role_type` keywords (full stack, backend, frontend) to scores per `coding_persona` (aligned with `coding-analyzer` personas: e.g. Balanced Engineer, Project Builder).

### TPO search endpoint

- **`POST /tpo/search`** — body: `jd_text`, optional `min_cgpa`, `branch`, `limit`.
- Steps: parse JD → `rank_students` → return `jd_parsed`, `total_candidates`, `ranked_students` (top N).

### Sample API response shape

```json
{
  "jd_parsed": {
    "role_type": "Full Stack Developer",
    "required_skills": ["React", "Node.js", "MongoDB"],
    "preferred_skills": ["Docker", "TypeScript"],
    "min_experience_years": 2,
    "accepts_freshers": true
  },
  "total_candidates": 45,
  "ranked_students": [
    {
      "student_id": 12,
      "name": "Ansh Bhatt",
      "email": "ansh@example.com",
      "cgpa": 8.2,
      "branch": "CSE",
      "github_username": "ansh-logics",
      "total_score": 87.5,
      "breakdown": {
        "required_skills": 40.0,
        "preferred_skills": 10.0,
        "github_activity": 18.5,
        "problem_solving": 11.0,
        "persona_match": 8.0
      },
      "coding_persona": "Project Builder",
      "github_stats": {
        "repos": 73,
        "commits_30d": 15,
        "languages": ["TypeScript", "JavaScript", "Python"]
      },
      "leetcode_stats": {
        "total_solved": 48,
        "easy": 38,
        "medium": 10,
        "hard": 0
      }
    }
  ]
}
```

---

## Integration notes (when building)

1. **Data pipeline:** Populate `student_profiles` from outputs of `resume-analyzer` and `coding-analyzer` (or from `master-service` combined report) on a schedule or on upload.
2. **Skill normalization:** JD skills (“Node.js”) vs resume/GitHub strings need the same normalization rules as in `_score_required_skills` (lowercase, strip dots, etc.).
3. **New service vs monolith:** Either a dedicated `tpo-api` service or an app module under a shared backend — keep consistent with existing microservice boundaries.

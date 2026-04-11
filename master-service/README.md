# Master service (orchestrator)

Calls **resume-analyzer** and **coding-analyzer** in parallel, merges JSON into one report. Serves a small HTML UI at `/`.

## Run with Docker Compose (repo root)

```bash
docker compose -f docker-compose.dev.yml up -d
```

- Master UI: http://localhost:18082  
- Coding analyzer: http://localhost:18080  
- Resume analyzer: http://localhost:18081  

## Run locally (uvicorn)

1. Start the two analyzers (Docker or local) and set URLs in `.env` (see `.env.example`).
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
| POST | `/analyze-profile` | `multipart/form-data`: `file` (PDF/DOCX), optional `github_username`, `leetcode_username`, `codeforces_username` |

Returns JSON with `resume_ok`, `resume`, `resume_error`, `coding_ok`, `coding_skipped`, `coding`, `coding_error`. HTTP **502** only if both downstream calls fail; **200** for partial success.

## Environment

| Variable | Default (Docker network) |
|----------|---------------------------|
| `RESUME_ANALYZER_BASE_URL` | `http://resume-analyzer-dev:8080` |
| `CODING_ANALYZER_BASE_URL` | `http://coding-analyzer-dev:8080` |
| `RESUME_HTTP_TIMEOUT_S` | `120` |
| `CODING_HTTP_TIMEOUT_S` | `180` |

# VeriAI Marksheet Analyzer (FastAPI)

Standalone marksheet parser microservice for AKTU One View PDFs. It extracts candidate details and returns only placement-relevant fields: CGPA, latest semester SGPA, and active backlog status.

## Features

- FastAPI microservice with `/`, `/health`, and `/analyze-marksheet`
- PDF text extraction via PyMuPDF and pdfplumber fallback strategy
- AKTU One View state-machine parser for sessions and semesters
- Latest-attempt semester normalization for CGPA computation
- Validation warnings and parser confidence score

## Project Structure

```text
marksheet-analyzer/
├── app/
│   ├── main.py
│   ├── api/
│   │   └── routes.py
│   ├── services/
│   │   ├── parser.py
│   │   └── extractor.py
│   ├── models/
│   │   └── response_model.py
│   ├── templates/
│   │   └── index.html
│   └── static/
├── tests/
│   └── test_parser.py
├── uploads/
├── requirements.txt
├── Dockerfile.dev
└── Dockerfile.prod
```

## Setup

```bash
cd marksheet-analyzer
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

## API

### POST `/analyze-marksheet`

Accepts `multipart/form-data` with field `file` (PDF only).

Response example:

```json
{
  "candidate": {
    "class_name": "B.TECH COMPUTER SCIENCE",
    "roll_no": "2302301530010",
    "enrollment_no": "230230153017216",
    "name": "ANSH BHATT"
  },
  "cgpa_computed": 5.5,
  "last_semester_number": 5,
  "last_semester_sgpa": 6.74,
  "backlog": {
    "has_active_backlog": true,
    "active_backlog_codes": ["BAS103"],
    "active_backlog_count": 1
  },
  "validation": {
    "warnings": [],
    "parser_confidence": 92
  }
}
```

## Notes

- SGPA is always read from marksheet text and treated as authoritative.
- CGPA is computed as the mean of latest-attempt semester SGPAs.
- Backlog detection is based on COP codes present in latest attempts per semester.
- If declaration date is missing, fallback ordering uses session year and document order.

## Synthetic Dataset Generator

Use this to generate paired synthetic PDFs for bulk testing:
- one resume PDF
- one AKTU-like One View marksheet PDF
- one JSONL manifest row per student

### Generate 500 paired documents (default)

```bash
python scripts/generate_bulk_documents.py --out-dir generated_docs
```

### Generate with explicit count and deterministic seed

```bash
python scripts/generate_bulk_documents.py --count 500 --seed 42 --out-dir generated_docs
```

Output structure:

```text
generated_docs/
├── resumes/
├── marksheets/
└── metadata/
    └── students.jsonl
```

### Validate generated dataset

This performs:
- manifest + file existence checks
- parser smoke test on a sample of generated marksheets

```bash
python scripts/validate_generated_documents.py --dataset-dir generated_docs --sample-size 25 --seed 7
```

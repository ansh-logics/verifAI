from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.models.response_model import MarksheetAnalysisResponse
from app.services.extractor import MarksheetExtractor
from app.services.parser import MarksheetParsingError, extract_marksheet_text, parse_marksheet_text

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parents[2]
UPLOAD_DIR = BASE_DIR.parent / "uploads"
TEMPLATES = Jinja2Templates(directory=str(Path(__file__).resolve().parents[1] / "templates"))
ALLOWED_EXTENSIONS = {".pdf"}
MAX_FILE_SIZE_BYTES = 8 * 1024 * 1024

extractor = MarksheetExtractor()


@router.get("/", response_class=HTMLResponse)
async def upload_page(request: Request) -> HTMLResponse:
    return TEMPLATES.TemplateResponse(request, "index.html", {"request": request})


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/analyze-marksheet", response_model=MarksheetAnalysisResponse)
async def analyze_marksheet(file: UploadFile = File(...)) -> MarksheetAnalysisResponse:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported file type. Please upload PDF marksheet.")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = f"{uuid4().hex}{suffix}"
    file_path = UPLOAD_DIR / safe_name

    try:
        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=413,
                detail="Uploaded file is too large. Please upload a file smaller than 8 MB.",
            )

        file_path.write_bytes(contents)
        text = extract_marksheet_text(file_path)
        student, attempts, warnings = parse_marksheet_text(text)

        if not any(item.sgpa_pdf is not None for item in attempts):
            raise HTTPException(
                status_code=422,
                detail="Unable to compute CGPA because SGPA values are missing in parsed semesters.",
            )

        return extractor.build_response(student=student, attempts=attempts, warnings=warnings)
    except MarksheetParsingError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Marksheet analysis failed: {exc}") from exc
    finally:
        try:
            file_path.unlink(missing_ok=True)
        except Exception:
            pass

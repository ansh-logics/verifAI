from __future__ import annotations

from typing import Any

import httpx

from app.config import Settings

DEFAULT_HEADERS = {
    "User-Agent": "VeriAI-Master-Service/1.0",
    "Accept": "application/json",
}


def _error_from_httpx(exc: Exception) -> str:
    if isinstance(exc, httpx.TimeoutException):
        return "Request timed out."
    if isinstance(exc, httpx.ConnectError):
        return "Could not connect to the service."
    return f"Request failed: {exc}"


async def call_resume_analyzer(
    *,
    settings: Settings,
    client: httpx.AsyncClient,
    file_bytes: bytes,
    filename: str,
    content_type: str | None,
) -> tuple[dict[str, Any] | None, str | None]:
    url = f"{settings.resume_base}/analyze-resume"
    files = {"file": (filename or "resume.bin", file_bytes, content_type or "application/octet-stream")}
    try:
        response = await client.post(
            url,
            files=files,
            timeout=settings.resume_http_timeout_s,
        )
        response.raise_for_status()
        return response.json(), None
    except httpx.HTTPStatusError as exc:
        detail = _http_error_detail(exc.response)
        return None, f"Resume analyzer returned {exc.response.status_code}: {detail}"
    except Exception as exc:
        return None, _error_from_httpx(exc)


def _http_error_detail(response: httpx.Response) -> str:
    try:
        body = response.json()
        if isinstance(body, dict) and "detail" in body:
            d = body["detail"]
            if isinstance(d, str):
                return d
            return str(d)
    except Exception:
        pass
    text = response.text
    return text[:500] if text else "Unknown error"


async def call_coding_analyzer(
    *,
    settings: Settings,
    client: httpx.AsyncClient,
    payload: dict[str, Any],
) -> tuple[dict[str, Any] | None, str | None]:
    url = f"{settings.coding_base}/analyze-coding-profile"
    try:
        response = await client.post(
            url,
            json=payload,
            timeout=settings.coding_http_timeout_s,
        )
        response.raise_for_status()
        return response.json(), None
    except httpx.HTTPStatusError as exc:
        detail = _http_error_detail(exc.response)
        return None, f"Coding analyzer returned {exc.response.status_code}: {detail}"
    except Exception as exc:
        return None, _error_from_httpx(exc)


async def call_marksheet_analyzer(
    *,
    settings: Settings,
    client: httpx.AsyncClient,
    file_bytes: bytes,
    filename: str,
    content_type: str | None,
) -> tuple[dict[str, Any] | None, str | None]:
    url = f"{settings.marksheet_base}/analyze-marksheet"
    files = {"file": (filename or "marksheet.pdf", file_bytes, content_type or "application/pdf")}
    try:
        response = await client.post(
            url,
            files=files,
            timeout=settings.marksheet_http_timeout_s,
        )
        response.raise_for_status()
        return response.json(), None
    except httpx.HTTPStatusError as exc:
        detail = _http_error_detail(exc.response)
        return None, f"Marksheet analyzer returned {exc.response.status_code}: {detail}"
    except Exception as exc:
        return None, _error_from_httpx(exc)

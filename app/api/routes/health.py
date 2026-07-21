"""Health and readiness endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.dependencies import get_gemini_service, get_ocr_service, get_translation_service
from app.core.config import get_settings
from app.models.responses import HealthResponse, ReadyResponse

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="healthy")


@router.get("/ready", response_model=ReadyResponse)
async def ready() -> ReadyResponse:
    settings = get_settings()

    if settings.extraction_provider == "legacy":
        ocr_service = get_ocr_service()
        translation_service = get_translation_service()
        ocr_available = ocr_service.is_available()
        translation_available = translation_service.is_available()
        status = "ready" if ocr_available and translation_available else "degraded"
        details = {"extractionProvider": "legacy", "ocr": ocr_available, "translation": translation_available}
        return ReadyResponse(
            status=status,
            ocr_available=ocr_available,
            translation_available=translation_available,
            details=details,
        )

    gemini_service = get_gemini_service()
    gemini_available = gemini_service.is_available()
    status = "ready" if gemini_available else "degraded"
    details = {"extractionProvider": "gemini", "geminiConfigured": gemini_available}
    return ReadyResponse(
        status=status,
        ocr_available=gemini_available,
        translation_available=gemini_available,
        details=details,
    )

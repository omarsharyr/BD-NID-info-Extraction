"""FastAPI dependency providers."""

from __future__ import annotations

from functools import lru_cache

from app.core.config import get_settings
from app.services.ai_extraction_service import AIExtractionService
from app.services.extraction_service import ExtractionService
from app.services.gemini_service import GeminiNIDExtractionService
from app.services.image_service import ImageService
from app.services.ocr_service import HybridOCRService, OCRService
from app.services.parser_service import ParserService
from app.services.translation_service import TranslationService, build_translation_service


@lru_cache(maxsize=1)
def get_image_service() -> ImageService:
    return ImageService(get_settings())


@lru_cache(maxsize=1)
def get_ocr_service() -> OCRService:
    return HybridOCRService(get_settings())


@lru_cache(maxsize=1)
def get_translation_service() -> TranslationService:
    return build_translation_service(get_settings())


@lru_cache(maxsize=1)
def get_parser_service() -> ParserService:
    return ParserService()


@lru_cache(maxsize=1)
def get_gemini_service() -> GeminiNIDExtractionService:
    return GeminiNIDExtractionService(settings=get_settings())


@lru_cache(maxsize=1)
def get_extraction_service():
    """Return the active extraction pipeline based on EXTRACTION_PROVIDER.

    - "gemini" (default): single AI call reads + translates both card images.
    - "legacy": original OCR (PaddleOCR/Tesseract) + regex parser + local translation.
    """
    settings = get_settings()
    if settings.extraction_provider == "legacy":
        return ExtractionService(
            settings=settings,
            image_service=get_image_service(),
            ocr_service=get_ocr_service(),
            parser_service=get_parser_service(),
            translation_service=get_translation_service(),
        )
    return AIExtractionService(
        settings=settings,
        image_service=get_image_service(),
        gemini_service=get_gemini_service(),
    )


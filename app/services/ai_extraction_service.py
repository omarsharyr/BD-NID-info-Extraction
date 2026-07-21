"""Orchestrates image validation + single-pass Gemini extraction/translation.

This is the replacement for ExtractionService's OCR -> parser -> translation
pipeline. Image validation (format/size/corruption checks) is still performed
by ImageService so all existing error-handling requirements keep working;
everything after that (reading + translating the card) is delegated to
Gemini in a single call.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from fastapi import UploadFile

from app.core.config import Settings
from app.core.exceptions import (
    MissingBackImageError,
    MissingFrontImageError,
    NoNidInformationFoundError,
)
from app.models.responses import ExtractionData, ExtractionResponse
from app.services.gemini_service import GeminiNIDExtractionService
from app.services.image_service import ImageService

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class AIExtractionService:
    settings: Settings
    image_service: ImageService
    gemini_service: GeminiNIDExtractionService

    async def extract(self, front_image: UploadFile | None, back_image: UploadFile | None) -> ExtractionResponse:
        if front_image is None:
            raise MissingFrontImageError()
        if back_image is None:
            raise MissingBackImageError()

        # Reuses existing validation: unsupported type, empty file, corrupted
        # image, and too-small-to-process checks all still raise their usual
        # NIDExtractorError subclasses here.
        front_prepared = self.image_service.load_image(front_image, "front")
        back_prepared = self.image_service.load_image(back_image, "back")

        front_bytes = front_prepared.original_bytes
        back_bytes = back_prepared.original_bytes
        front_mime = front_image.content_type or "image/jpeg"
        back_mime = back_image.content_type or "image/jpeg"

        payload = self.gemini_service.extract(front_bytes, front_mime, back_bytes, back_mime)

        if not payload.front_readable and not payload.back_readable:
            raise NoNidInformationFoundError()

        if not payload.has_any_field():
            raise NoNidInformationFoundError()

        for warning in payload.warnings:
            logger.warning("gemini_extraction_warning=%s", warning)

        data = ExtractionData(
            name=payload.name,
            father_name=payload.father_name,
            mother_name=payload.mother_name,
            date_of_birth=payload.date_of_birth,
            nid_number=payload.nid_number,
            present_address=payload.present_address,
            permanent_address=payload.permanent_address,
        )
        return ExtractionResponse(**data.model_dump())

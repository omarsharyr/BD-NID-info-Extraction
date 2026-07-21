"""Orchestrates validation, OCR, parsing, translation, and response assembly."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from fastapi import UploadFile

from app.core.config import Settings
from app.core.exceptions import (
    CorruptedImageError,
    EmptyFileError,
    ImageTooBlurryError,
    ImageTooSmallError,
    MissingBackImageError,
    MissingFrontImageError,
    NoNidInformationFoundError,
    OCRProcessingError,
    UnsupportedFileTypeError,
)
from app.models.internal import OCRResult, ParsedDocument, PreparedImage
from app.models.responses import ExtractionData, ExtractionResponse
from app.services.image_service import ImageService
from app.services.ocr_service import OCRService
from app.services.parser_service import ParserService
from app.services.translation_service import TranslationService

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ExtractionService:
    settings: Settings
    image_service: ImageService
    ocr_service: OCRService
    parser_service: ParserService
    translation_service: TranslationService

    async def extract(self, front_image: UploadFile | None, back_image: UploadFile | None) -> ExtractionResponse:
        if front_image is None:
            raise MissingFrontImageError()
        if back_image is None:
            raise MissingBackImageError()

        prepared_images = self._prepare_images(front_image, back_image)
        front_prepared = prepared_images["front"]
        back_prepared = prepared_images["back"]

        front_ocr = self._run_ocr(front_prepared)
        back_ocr = self._run_ocr(back_prepared)

        parsed = self.parser_service.parse(front_ocr, back_ocr)
        if not any(field.value for field in parsed.fields.values()):
            raise NoNidInformationFoundError()

        translated_data = self._translate(parsed)
        return ExtractionResponse(**translated_data.model_dump())

    def _prepare_images(self, front_image: UploadFile, back_image: UploadFile) -> dict[str, PreparedImage]:
        try:
            front_prepared = self.image_service.load_image(front_image, "front")
        except ImageTooSmallError:
            raise
        except EmptyFileError:
            raise
        except UnsupportedFileTypeError:
            raise
        except CorruptedImageError:
            raise

        try:
            back_prepared = self.image_service.load_image(back_image, "back")
        except ImageTooSmallError:
            raise
        except EmptyFileError:
            raise
        except UnsupportedFileTypeError:
            raise
        except CorruptedImageError:
            raise

        if not front_prepared.quality.readable and not back_prepared.quality.readable:
            raise ImageTooBlurryError()
        return {"front": front_prepared, "back": back_prepared}

    def _run_ocr(self, prepared_image: PreparedImage) -> OCRResult:
        try:
            result = self.ocr_service.extract_text(prepared_image.image, side=prepared_image.side, variants=prepared_image.variants)
        except OCRProcessingError:
            raise
        except Exception as exc:
            raise OCRProcessingError() from exc
        if not result.text.strip():
            logger.warning("No readable OCR text extracted for side=%s", prepared_image.side)
        return result

    def _translate(self, parsed: ParsedDocument) -> ExtractionData:
        translated_values: dict[str, str | None] = {}

        field_map = {
            "name": ("name", self.translation_service.translate_person_name),
            "fatherName": ("fatherName", self.translation_service.translate_person_name),
            "motherName": ("motherName", self.translation_service.translate_person_name),
            "presentAddress": ("presentAddress", self.translation_service.translate_address),
            "permanentAddress": ("permanentAddress", self.translation_service.translate_address),
            "dateOfBirth": ("dateOfBirth", lambda text: text),
            "nidNumber": ("nidNumber", lambda text: text),
        }

        for response_key, (parsed_key, translator) in field_map.items():
            field_value = parsed.fields.get(parsed_key)
            if field_value is None or field_value.value is None:
                translated_values[response_key] = None
                continue
            translated = translator(field_value.value)
            translated_values[response_key] = translated or field_value.value

        data = ExtractionData(
            name=translated_values["name"],
            father_name=translated_values["fatherName"],
            mother_name=translated_values["motherName"],
            date_of_birth=translated_values["dateOfBirth"],
            nid_number=translated_values["nidNumber"],
            present_address=translated_values["presentAddress"],
            permanent_address=translated_values["permanentAddress"],
        )
        return data

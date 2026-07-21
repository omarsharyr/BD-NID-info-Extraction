"""Hybrid English and Bengali OCR implementation."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Mapping

import cv2
import numpy as np

from app.core.config import Settings
from app.core.exceptions import OCRProcessingError
from app.models.internal import OCRLine, OCRResult
from app.utils.text_normalizer import normalize_unicode_text

logger = logging.getLogger(__name__)


class OCRService(ABC):
    @abstractmethod
    def extract_text(
        self,
        image: np.ndarray,
        *,
        side: str,
        variants: Mapping[str, np.ndarray] | None = None,
    ) -> OCRResult:
        raise NotImplementedError

    @abstractmethod
    def is_available(self) -> bool:
        raise NotImplementedError


class PaddleOCRService(OCRService):
    """Run PaddleOCR once per uploaded card side and normalize its output."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._ocr = None
        self._initialization_error: Exception | None = None
        try:
            from paddleocr import PaddleOCR

            self._ocr = PaddleOCR(
                use_angle_cls=settings.paddle_use_angle_cls,
                lang=settings.paddle_ocr_language,
                show_log=settings.enable_debug,
            )
        except Exception as exc:  # pragma: no cover - environment/model specific
            self._initialization_error = exc
            logger.exception("Failed to initialize PaddleOCR")

    def is_available(self) -> bool:
        return self._ocr is not None

    def extract_text(
        self,
        image: np.ndarray,
        *,
        side: str,
        variants: Mapping[str, np.ndarray] | None = None,
    ) -> OCRResult:
        if self._ocr is None:
            message = "PaddleOCR is not available in this environment."
            if self._initialization_error:
                message = f"{message} {self._initialization_error}"
            raise OCRProcessingError(message)

        try:
            raw_result = self._ocr.ocr(image, cls=self.settings.paddle_use_angle_cls)
        except Exception as exc:
            logger.exception("PaddleOCR inference failed side=%s", side)
            raise OCRProcessingError(f"PaddleOCR failed for {side} image.") from exc

        detected = raw_result[0] if raw_result and raw_result[0] else []
        ordered = sorted(detected, key=self._reading_order)
        lines: list[OCRLine] = []
        confidences: list[float] = []
        for index, item in enumerate(ordered, start=1):
            if not item or len(item) < 2 or not item[1]:
                continue
            text = normalize_unicode_text(str(item[1][0]))
            if not text:
                continue
            confidence = float(item[1][1]) * 100.0
            confidences.append(confidence)
            lines.append(
                OCRLine(
                    text=text,
                    confidence=confidence,
                    side=side,
                    variant="paddleocr",
                    line_number=index,
                )
            )

        text = "\n".join(line.text for line in lines)
        average_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        return OCRResult(
            side=side,
            text=text,
            lines=lines,
            average_confidence=average_confidence,
            variant_scores={"paddleocr": average_confidence},
            readable=bool(text),
        )

    @staticmethod
    def _reading_order(item: object) -> tuple[float, float]:
        try:
            box = item[0]  # type: ignore[index]
            return min(float(point[1]) for point in box), min(float(point[0]) for point in box)
        except (TypeError, ValueError, IndexError):
            return float("inf"), float("inf")


class HybridOCRService(OCRService):
    """Combine PaddleOCR English recognition with focused Bengali OCR."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.paddle = PaddleOCRService(settings)
        self._pytesseract = None
        try:
            import pytesseract

            if settings.tesseract_cmd:
                pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd
            self._pytesseract = pytesseract
        except Exception:
            logger.exception("Failed to initialize Bengali OCR")

    def is_available(self) -> bool:
        if not self.paddle.is_available() or self._pytesseract is None:
            return False
        try:
            languages = self._pytesseract.get_languages(config="")
            return "ben" in languages
        except Exception:
            return False

    def extract_text(
        self,
        image: np.ndarray,
        *,
        side: str,
        variants: Mapping[str, np.ndarray] | None = None,
    ) -> OCRResult:
        english = self.paddle.extract_text(image, side=side)
        bengali_lines = self._extract_bengali_regions(side, variants or {})
        lines = [*english.lines, *bengali_lines]
        confidences = [line.confidence for line in lines if line.confidence > 0]
        text = "\n".join(line.text for line in lines)
        average = sum(confidences) / len(confidences) if confidences else 0.0
        return OCRResult(
            side=side,
            text=text,
            lines=lines,
            average_confidence=average,
            variant_scores={"paddleocr_en": english.average_confidence, "tesseract_ben": self._average(bengali_lines)},
            readable=bool(text),
        )

    def _extract_bengali_regions(self, side: str, variants: Mapping[str, np.ndarray]) -> list[OCRLine]:
        if self._pytesseract is None:
            raise OCRProcessingError("Bengali OCR is not available in this environment.")
        region_names = ("front_identity",) if side == "front" else ("back_address",)
        lines: list[OCRLine] = []
        seen: set[str] = set()
        for region_name in region_names:
            region = variants.get(region_name)
            if region is None:
                continue
            for psm in (6, 11):
                for line in self._tesseract_lines(region, side, region_name, psm):
                    key = line.text.casefold()
                    if key not in seen:
                        seen.add(key)
                        lines.append(line)
        return lines

    def _tesseract_lines(self, image: np.ndarray, side: str, region_name: str, psm: int) -> list[OCRLine]:
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        data = self._pytesseract.image_to_data(
            rgb,
            lang="ben",
            config=f"--oem 1 --psm {psm}",
            output_type=self._pytesseract.Output.DICT,
        )
        grouped: dict[tuple[int, int, int], list[tuple[int, str, float]]] = {}
        for index, raw_text in enumerate(data["text"]):
            text = normalize_unicode_text(str(raw_text))
            if not text:
                continue
            confidence = max(0.0, float(data["conf"][index]))
            key = (int(data["block_num"][index]), int(data["par_num"][index]), int(data["line_num"][index]))
            grouped.setdefault(key, []).append((int(data["word_num"][index]), text, confidence))
        result: list[OCRLine] = []
        for number, (_, words) in enumerate(sorted(grouped.items()), start=1):
            ordered = sorted(words)
            text = " ".join(word for _, word, _ in ordered)
            scores = [score for _, _, score in ordered if score > 0]
            confidence = sum(scores) / len(scores) if scores else 0.0
            result.append(OCRLine(text, confidence, side, f"{region_name}_ben_psm{psm}", number))
        return result

    @staticmethod
    def _average(lines: list[OCRLine]) -> float:
        values = [line.confidence for line in lines if line.confidence > 0]
        return sum(values) / len(values) if values else 0.0

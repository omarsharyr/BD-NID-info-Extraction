"""Image validation and preprocessing pipeline."""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass

import cv2
import numpy as np
from fastapi import UploadFile
from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.config import Settings
from app.core.exceptions import CorruptedImageError, EmptyFileError, ImageTooSmallError, UnsupportedFileTypeError
from app.models.internal import ImageQualityReport, PreparedImage

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/jpg", "image/png", "application/octet-stream"}


@dataclass(slots=True)
class ImageService:
    settings: Settings

    def _validate_metadata(self, upload: UploadFile, side: str) -> None:
        if not upload.filename:
            raise UnsupportedFileTypeError()
        extension = upload.filename.lower().rsplit(".", 1)[-1]
        if f".{extension}" not in ALLOWED_EXTENSIONS:
            raise UnsupportedFileTypeError()
        if upload.content_type and upload.content_type.lower() not in ALLOWED_CONTENT_TYPES:
            raise UnsupportedFileTypeError()
        logger.debug("validated_upload_metadata side=%s filename=%s", side, upload.filename)

    def load_image(self, upload: UploadFile, side: str) -> PreparedImage:
        self._validate_metadata(upload, side)
        file_bytes = upload.file.read()
        if not file_bytes:
            raise EmptyFileError()
        if len(file_bytes) > self.settings.max_upload_size_mb * 1024 * 1024:
            raise UnsupportedFileTypeError()

        try:
            image = Image.open(io.BytesIO(file_bytes))
            image = ImageOps.exif_transpose(image)
            image.verify()
            reopened = Image.open(io.BytesIO(file_bytes))
            reopened = ImageOps.exif_transpose(reopened).convert("RGB")
        except (UnidentifiedImageError, OSError, ValueError):
            raise CorruptedImageError() from None

        image_array = cv2.cvtColor(np.array(reopened), cv2.COLOR_RGB2BGR)
        quality = self.analyze_quality(image_array, len(file_bytes), side)
        if quality.width < self.settings.min_image_width or quality.height < self.settings.min_image_height:
            raise ImageTooSmallError()
        variants = self.build_preprocessing_variants(image_array, side=side)
        return PreparedImage(side=side, original_bytes=file_bytes, image=image_array, quality=quality, variants=variants)

    def analyze_quality(self, image: np.ndarray, file_size_bytes: int, side: str) -> ImageQualityReport:
        height, width = image.shape[:2]
        grayscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blur_score = float(cv2.Laplacian(grayscale, cv2.CV_64F).var())
        brightness = float(grayscale.mean())
        contrast = float(grayscale.std())
        warnings: list[str] = []
        if width < self.settings.min_image_width or height < self.settings.min_image_height:
            warnings.append(f"{side} image dimensions are below the recommended minimum.")
        if blur_score < self.settings.blur_threshold:
            warnings.append(f"{side} image appears blurry.")
        if brightness < 45 or brightness > 215:
            warnings.append(f"{side} image has unusual brightness.")
        if contrast < 18:
            warnings.append(f"{side} image has low contrast.")

        readable = width >= 320 and height >= 200 and blur_score >= self.settings.blur_threshold * 0.45
        confidence = min(1.0, max(0.0, (blur_score / max(self.settings.blur_threshold, 1.0)) * 0.45 + (contrast / 80.0) * 0.35 + 0.2))
        return ImageQualityReport(
            side=side,
            width=width,
            height=height,
            file_size_bytes=file_size_bytes,
            blur_score=blur_score,
            brightness=brightness,
            contrast=contrast,
            warnings=warnings,
            confidence=confidence,
            readable=readable,
        )

    def build_preprocessing_variants(self, image: np.ndarray, side: str | None = None) -> dict[str, np.ndarray]:
        variants: dict[str, np.ndarray] = {"original": image.copy()}
        grayscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(grayscale)
        variants["clahe"] = cv2.cvtColor(clahe, cv2.COLOR_GRAY2BGR)

        denoised = cv2.bilateralFilter(grayscale, 9, 75, 75)
        adaptive = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 11)
        variants["threshold"] = cv2.cvtColor(adaptive, cv2.COLOR_GRAY2BGR)

        blur = cv2.GaussianBlur(image, (0, 0), 2.0)
        sharpened = cv2.addWeighted(image, 1.45, blur, -0.45, 0)
        variants["sharpened"] = sharpened

        warped = self._perspective_correction(image)
        if warped is not None:
            variants["perspective"] = warped
        variants.update(self._build_layout_regions(warped if warped is not None else image, side))
        return variants

    def _build_layout_regions(self, image: np.ndarray, side: str | None) -> dict[str, np.ndarray]:
        """Create enlarged OCR regions for common legacy Bangladesh NID layouts."""
        if side not in {"front", "back"}:
            return {}
        height, width = image.shape[:2]

        def crop(name: str, x1: float, y1: float, x2: float, y2: float, scale: float = 2.0) -> tuple[str, np.ndarray]:
            region = image[int(height * y1) : int(height * y2), int(width * x1) : int(width * x2)]
            enlarged = cv2.resize(region, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
            return name, enlarged

        if side == "front":
            return dict(
                [
                    crop("front_identity", 0.30, 0.20, 0.80, 0.79),
                    crop("front_numbers", 0.30, 0.70, 0.78, 0.98, 2.4),
                ]
            )
        return dict(
            [
                crop("back_address", 0.035, 0.20, 0.78, 0.52),
                crop("back_mrz", 0.035, 0.56, 0.98, 0.98, 2.4),
            ]
        )

    def _perspective_correction(self, image: np.ndarray) -> np.ndarray | None:
        grayscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(grayscale, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:8]
        for contour in contours:
            perimeter = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
            if len(approx) == 4:
                return self._warp_document(image, approx.reshape(4, 2))
        return None

    def _warp_document(self, image: np.ndarray, points: np.ndarray) -> np.ndarray:
        rect = self._order_points(points.astype("float32"))
        (top_left, top_right, bottom_right, bottom_left) = rect
        width_a = np.linalg.norm(bottom_right - bottom_left)
        width_b = np.linalg.norm(top_right - top_left)
        max_width = int(max(width_a, width_b))

        height_a = np.linalg.norm(top_right - bottom_right)
        height_b = np.linalg.norm(top_left - bottom_left)
        max_height = int(max(height_a, height_b))

        destination = np.array(
            [[0, 0], [max_width - 1, 0], [max_width - 1, max_height - 1], [0, max_height - 1]], dtype="float32"
        )
        transform = cv2.getPerspectiveTransform(rect, destination)
        return cv2.warpPerspective(image, transform, (max_width, max_height))

    def _order_points(self, points: np.ndarray) -> np.ndarray:
        rect = np.zeros((4, 2), dtype="float32")
        sums = points.sum(axis=1)
        rect[0] = points[np.argmin(sums)]
        rect[2] = points[np.argmax(sums)]
        diffs = np.diff(points, axis=1)
        rect[1] = points[np.argmin(diffs)]
        rect[3] = points[np.argmax(diffs)]
        return rect

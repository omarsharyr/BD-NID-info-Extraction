"""Application specific exceptions and error codes."""

from __future__ import annotations


class NIDExtractorError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, details: dict | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details


class MissingFrontImageError(NIDExtractorError):
    def __init__(self) -> None:
        super().__init__("MISSING_FRONT_IMAGE", "The front-side NID image is required.")


class MissingBackImageError(NIDExtractorError):
    def __init__(self) -> None:
        super().__init__("MISSING_BACK_IMAGE", "The back-side NID image is required.")


class UnsupportedFileTypeError(NIDExtractorError):
    def __init__(self) -> None:
        super().__init__("UNSUPPORTED_FILE_TYPE", "Only JPG, JPEG, and PNG files are supported.")


class EmptyFileError(NIDExtractorError):
    def __init__(self) -> None:
        super().__init__("EMPTY_FILE", "The uploaded file is empty.")


class CorruptedImageError(NIDExtractorError):
    def __init__(self) -> None:
        super().__init__("CORRUPTED_IMAGE", "The uploaded file is not a valid readable image.")


class ImageTooSmallError(NIDExtractorError):
    def __init__(self) -> None:
        super().__init__("IMAGE_TOO_SMALL", "The uploaded image is too small to process reliably.")


class ImageTooBlurryError(NIDExtractorError):
    def __init__(self) -> None:
        super().__init__("IMAGE_TOO_BLURRY", "The uploaded image appears too blurry.")


class OCRProcessingError(NIDExtractorError):
    def __init__(self, message: str = "OCR processing failed.") -> None:
        super().__init__("OCR_PROCESSING_FAILED", message, status_code=500)


class AIProviderNotConfiguredError(NIDExtractorError):
    def __init__(self) -> None:
        super().__init__(
            "AI_PROVIDER_NOT_CONFIGURED",
            "GEMINI_API_KEY is not configured on the server.",
            status_code=500,
        )


class AIExtractionError(NIDExtractorError):
    def __init__(self, message: str = "AI-based extraction failed.") -> None:
        super().__init__("AI_EXTRACTION_FAILED", message, status_code=502)


class NoNidInformationFoundError(NIDExtractorError):
    def __init__(self) -> None:
        super().__init__("NO_NID_INFORMATION_FOUND", "No Bangladesh NID information could be extracted.", status_code=422)


class InternalServerError(NIDExtractorError):
    def __init__(self) -> None:
        super().__init__("INTERNAL_SERVER_ERROR", "An internal server error occurred.", status_code=500)

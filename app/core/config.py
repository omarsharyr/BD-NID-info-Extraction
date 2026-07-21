"""Application settings loaded from environment variables."""

from __future__ import annotations

import tempfile
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "AI-Powered Bangladesh National ID Information Extraction System"
    app_version: str = "1.0.0"
    app_environment: str = Field(default="development", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    max_upload_size_mb: int = Field(default=8, alias="MAX_UPLOAD_SIZE_MB")
    min_image_width: int = Field(default=700, alias="MIN_IMAGE_WIDTH")
    min_image_height: int = Field(default=450, alias="MIN_IMAGE_HEIGHT")
    blur_threshold: float = Field(default=140.0, alias="BLUR_THRESHOLD")
    ocr_confidence_threshold: float = Field(default=55.0, alias="OCR_CONFIDENCE_THRESHOLD")
    temp_dir: str = Field(default_factory=tempfile.gettempdir, alias="TEMP_DIR")
    translation_provider: str = Field(default="local", alias="TRANSLATION_PROVIDER")
    translation_api_url: str | None = Field(default=None, alias="TRANSLATION_API_URL")
    translation_api_key: str | None = Field(default=None, alias="TRANSLATION_API_KEY")
    enable_debug: bool = Field(default=False, alias="ENABLE_DEBUG")
    paddle_ocr_language: str = Field(default="en", alias="PADDLE_OCR_LANGUAGE")
    paddle_use_angle_cls: bool = Field(default=True, alias="PADDLE_USE_ANGLE_CLS")
    tesseract_cmd: str | None = Field(default=None, alias="TESSERACT_CMD")

    # AI-based extraction (Gemini). extraction_provider selects the pipeline:
    #   "gemini" -> single-pass vision+translation via Gemini (default, recommended)
    #   "legacy" -> original OCR (PaddleOCR/Tesseract) + regex parser + local translation
    extraction_provider: str = Field(default="gemini", alias="EXTRACTION_PROVIDER")
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-flash-latest", alias="GEMINI_MODEL")
    gemini_timeout_seconds: float = Field(default=45.0, alias="GEMINI_TIMEOUT_SECONDS")
    gemini_max_retries: int = Field(default=2, alias="GEMINI_MAX_RETRIES")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

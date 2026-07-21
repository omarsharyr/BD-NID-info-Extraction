"""Public API response schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


def to_camel(value: str) -> str:
    first, *rest = value.split("_")
    return first + "".join(part.capitalize() for part in rest)


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")


class ExtractionData(CamelModel):
    name: str | None = None
    father_name: str | None = Field(default=None)
    mother_name: str | None = Field(default=None)
    date_of_birth: str | None = Field(default=None)
    nid_number: str | None = Field(default=None)
    present_address: str | None = Field(default=None)
    permanent_address: str | None = Field(default=None)


class ExtractionResponse(ExtractionData):
    """Flat public extraction response required by the API contract."""


class ErrorPayload(CamelModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class ErrorResponse(CamelModel):
    success: bool = False
    error: ErrorPayload


class HealthResponse(CamelModel):
    status: str = "healthy"


class ReadyResponse(CamelModel):
    status: str
    ocr_available: bool
    translation_available: bool
    details: dict[str, Any] | None = None


class RootResponse(CamelModel):
    project_name: str
    version: str
    docs_url: str
    redoc_url: str
    openapi_url: str

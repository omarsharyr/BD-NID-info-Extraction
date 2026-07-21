"""Unit tests for GeminiNIDExtractionService.

The real google-genai SDK is mocked out via sys.modules so these tests run
without network access or a real API key.
"""

from __future__ import annotations

import json
import sys
import types as pytypes
from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest

from app.core.config import Settings
from app.core.exceptions import AIExtractionError, AIProviderNotConfiguredError, NoNidInformationFoundError


def _install_fake_genai(monkeypatch, response_text: str | None, raise_exc: Exception | None = None):
    """Install a fake `google.genai` package into sys.modules."""

    fake_genai_module = pytypes.ModuleType("google.genai")
    fake_types_module = pytypes.ModuleType("google.genai.types")

    class FakePart:
        @staticmethod
        def from_bytes(data: bytes, mime_type: str):
            return {"data": data, "mime_type": mime_type}

    class FakeGenerateContentConfig:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    fake_types_module.Part = FakePart
    fake_types_module.GenerateContentConfig = FakeGenerateContentConfig

    fake_response = MagicMock()
    fake_response.text = response_text
    fake_response.prompt_feedback = None

    fake_models = MagicMock()
    if raise_exc is not None:
        fake_models.generate_content.side_effect = raise_exc
    else:
        fake_models.generate_content.return_value = fake_response

    fake_client_instance = MagicMock()
    fake_client_instance.models = fake_models

    class FakeClient:
        def __init__(self, api_key: str):
            self.api_key = api_key
            self.models = fake_models

    fake_genai_module.Client = FakeClient

    fake_google_module = pytypes.ModuleType("google")
    fake_google_module.genai = fake_genai_module

    monkeypatch.setitem(sys.modules, "google", fake_google_module)
    monkeypatch.setitem(sys.modules, "google.genai", fake_genai_module)
    monkeypatch.setitem(sys.modules, "google.genai.types", fake_types_module)

    return fake_models


def _settings(**overrides) -> Settings:
    base = {
        "extraction_provider": "gemini",
        "gemini_api_key": "fake-key",
        "gemini_max_retries": 0,
    }
    base.update(overrides)
    return Settings(**base)


def test_raises_when_no_api_key_configured():
    from app.services.gemini_service import GeminiNIDExtractionService

    service = GeminiNIDExtractionService(settings=_settings(gemini_api_key=None))
    assert service.is_available() is False
    with pytest.raises(AIProviderNotConfiguredError):
        service._get_client()


def test_successful_extraction_parses_payload(monkeypatch):
    from app.services.gemini_service import GeminiNIDExtractionService

    payload = {
        "name": "Md. Rahim",
        "fatherName": "Abdul Karim",
        "motherName": "Amena Begum",
        "dateOfBirth": "1998-01-15",
        "nidNumber": "1234567890123",
        "presentAddress": "Dhaka, Bangladesh",
        "permanentAddress": "Cumilla, Bangladesh",
        "frontReadable": True,
        "backReadable": True,
        "warnings": [],
    }
    _install_fake_genai(monkeypatch, json.dumps(payload))

    service = GeminiNIDExtractionService(settings=_settings())
    result = service.extract(b"front-bytes", "image/jpeg", b"back-bytes", "image/png")

    assert result.name == "Md. Rahim"
    assert result.nid_number == "1234567890123"
    assert result.has_any_field() is True


def test_partial_extraction_leaves_missing_fields_null(monkeypatch):
    from app.services.gemini_service import GeminiNIDExtractionService

    payload = {
        "name": "Md. Rahim",
        "fatherName": None,
        "motherName": None,
        "dateOfBirth": None,
        "nidNumber": "1234567890123",
        "presentAddress": None,
        "permanentAddress": None,
        "frontReadable": True,
        "backReadable": False,
        "warnings": ["Back image was too blurry to read the address fields."],
    }
    _install_fake_genai(monkeypatch, json.dumps(payload))

    service = GeminiNIDExtractionService(settings=_settings())
    result = service.extract(b"front-bytes", "image/jpeg", b"back-bytes", "image/png")

    assert result.name == "Md. Rahim"
    assert result.father_name is None
    assert result.back_readable is False
    assert result.has_any_field() is True


def test_malformed_json_raises_ai_extraction_error(monkeypatch):
    from app.services.gemini_service import GeminiNIDExtractionService

    _install_fake_genai(monkeypatch, "not json at all")

    service = GeminiNIDExtractionService(settings=_settings())
    with pytest.raises(AIExtractionError):
        service.extract(b"front-bytes", "image/jpeg", b"back-bytes", "image/png")


def test_empty_response_raises_ai_extraction_error(monkeypatch):
    from app.services.gemini_service import GeminiNIDExtractionService

    _install_fake_genai(monkeypatch, None)

    service = GeminiNIDExtractionService(settings=_settings())
    with pytest.raises(AIExtractionError):
        service.extract(b"front-bytes", "image/jpeg", b"back-bytes", "image/png")


def test_api_failure_raises_ai_extraction_error(monkeypatch):
    from app.services.gemini_service import GeminiNIDExtractionService

    _install_fake_genai(monkeypatch, None, raise_exc=RuntimeError("network unreachable"))

    service = GeminiNIDExtractionService(settings=_settings())
    with pytest.raises(AIExtractionError):
        service.extract(b"front-bytes", "image/jpeg", b"back-bytes", "image/png")

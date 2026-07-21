from __future__ import annotations

from app.api.dependencies import get_extraction_service, get_image_service
from app.core.config import get_settings
from app.main import app
from app.services.ai_extraction_service import AIExtractionService
from app.services.gemini_service import GeminiNIDPayload


class FakeGeminiService:
    def __init__(self, payload: GeminiNIDPayload) -> None:
        self._payload = payload

    def is_available(self) -> bool:
        return True

    def extract(self, front_bytes, front_mime, back_bytes, back_mime) -> GeminiNIDPayload:
        return self._payload


def _override_with_payload(payload: GeminiNIDPayload):
    app.dependency_overrides[get_extraction_service] = lambda: AIExtractionService(
        settings=get_settings(),
        image_service=get_image_service(),
        gemini_service=FakeGeminiService(payload),
    )


def test_extract_endpoint_gemini_success(client) -> None:
    payload = GeminiNIDPayload(
        name="Md. Rahim",
        fatherName="Abdul Karim",
        motherName="Amena Begum",
        dateOfBirth="1998-01-15",
        nidNumber="1234567890123",
        presentAddress="Dhaka, Bangladesh",
        permanentAddress="Cumilla, Bangladesh",
        frontReadable=True,
        backReadable=True,
        warnings=[],
    )
    _override_with_payload(payload)
    try:
        from tests.conftest import create_test_image

        front = create_test_image(text="front")
        back = create_test_image(text="back")
        response = client.post(
            "/api/v1/nid/extract",
            files={
                "front_image": ("front.png", front, "image/png"),
                "back_image": ("back.png", back, "image/png"),
            },
        )
        assert response.status_code == 200
        payload_json = response.json()
        assert payload_json["name"] == "Md. Rahim"
        assert payload_json["nidNumber"] == "1234567890123"
        assert payload_json["presentAddress"] == "Dhaka, Bangladesh"
    finally:
        app.dependency_overrides.pop(get_extraction_service, None)


def test_extract_endpoint_gemini_partial_extraction(client) -> None:
    payload = GeminiNIDPayload(
        name="Md. Rahim",
        fatherName=None,
        motherName=None,
        dateOfBirth=None,
        nidNumber="1234567890123",
        presentAddress=None,
        permanentAddress=None,
        frontReadable=True,
        backReadable=False,
        warnings=["Back image was too blurry to read."],
    )
    _override_with_payload(payload)
    try:
        from tests.conftest import create_test_image

        front = create_test_image(text="front")
        back = create_test_image(text="back")
        response = client.post(
            "/api/v1/nid/extract",
            files={
                "front_image": ("front.png", front, "image/png"),
                "back_image": ("back.png", back, "image/png"),
            },
        )
        assert response.status_code == 200
        payload_json = response.json()
        assert payload_json["name"] == "Md. Rahim"
        assert payload_json["fatherName"] is None
        assert payload_json["presentAddress"] is None
    finally:
        app.dependency_overrides.pop(get_extraction_service, None)


def test_extract_endpoint_gemini_unreadable_images_returns_422(client) -> None:
    payload = GeminiNIDPayload(
        name=None,
        fatherName=None,
        motherName=None,
        dateOfBirth=None,
        nidNumber=None,
        presentAddress=None,
        permanentAddress=None,
        frontReadable=False,
        backReadable=False,
        warnings=["Front image unreadable.", "Back image unreadable."],
    )
    _override_with_payload(payload)
    try:
        from tests.conftest import create_test_image

        front = create_test_image(text="front")
        back = create_test_image(text="back")
        response = client.post(
            "/api/v1/nid/extract",
            files={
                "front_image": ("front.png", front, "image/png"),
                "back_image": ("back.png", back, "image/png"),
            },
        )
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "NO_NID_INFORMATION_FOUND"
    finally:
        app.dependency_overrides.pop(get_extraction_service, None)


def test_extract_endpoint_missing_back_image_returns_error(client) -> None:
    app.dependency_overrides.pop(get_extraction_service, None)
    from tests.conftest import create_test_image

    front = create_test_image(text="front")
    response = client.post(
        "/api/v1/nid/extract",
        files={"front_image": ("front.png", front, "image/png")},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "MISSING_BACK_IMAGE"

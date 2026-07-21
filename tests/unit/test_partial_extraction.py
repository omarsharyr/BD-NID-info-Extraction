from app.api.dependencies import get_extraction_service, get_image_service, get_parser_service, get_translation_service
from app.core.config import get_settings
from app.main import app
from app.models.internal import OCRLine, OCRResult
from app.services.extraction_service import ExtractionService


class PartialOCRService:
    def is_available(self) -> bool:
        return True

    def extract_text(self, image, *, side: str, variants=None):
        if side == "front":
            return OCRResult(
                side="front",
                text="Name: মোঃ রহিম\nDate of Birth: 15/01/1998",
                lines=[
                    OCRLine(text="Name: মোঃ রহিম", confidence=91.0, side="front", variant="original", line_number=1),
                    OCRLine(text="Date of Birth: 15/01/1998", confidence=92.0, side="front", variant="original", line_number=2),
                ],
                average_confidence=91.5,
            )
        return OCRResult(side="back", text="", lines=[], average_confidence=10.0)


def test_partial_extraction_returns_null_fields(client) -> None:
    app.dependency_overrides[get_extraction_service] = lambda: ExtractionService(
        settings=get_settings(),
        image_service=get_image_service(),
        ocr_service=PartialOCRService(),
        parser_service=get_parser_service(),
        translation_service=get_translation_service(),
    )
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
        payload = response.json()
        assert payload["fatherName"] is None
        assert payload["presentAddress"] is None
        assert payload["name"] is not None
    finally:
        app.dependency_overrides.clear()

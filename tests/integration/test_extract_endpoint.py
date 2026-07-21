from __future__ import annotations

from app.api.dependencies import get_extraction_service, get_image_service, get_parser_service, get_translation_service
from app.core.config import get_settings
from app.main import app
from app.models.internal import OCRLine, OCRResult
from app.services.extraction_service import ExtractionService


class FakeOCRService:
    def is_available(self) -> bool:
        return True

    def extract_text(self, image, *, side: str, variants=None):
        if side == "front":
            return OCRResult(
                side="front",
                text="Name: মোঃ রহিম\nFather's Name: আব্দুল করিম\nMother's Name: আমেনা বেগম\nDate of Birth: 15/01/1998\nNID No 1234 5678 9012 3",
                lines=[
                    OCRLine(text="Name: মোঃ রহিম", confidence=94.0, side="front", variant="original", line_number=1),
                    OCRLine(text="Father's Name: আব্দুল করিম", confidence=92.0, side="front", variant="original", line_number=2),
                    OCRLine(text="Mother's Name: আমেনা বেগম", confidence=91.0, side="front", variant="original", line_number=3),
                    OCRLine(text="Date of Birth: 15/01/1998", confidence=96.0, side="front", variant="original", line_number=4),
                    OCRLine(text="NID No 1234 5678 9012 3", confidence=97.0, side="front", variant="original", line_number=5),
                ],
                average_confidence=94.0,
            )
        return OCRResult(
            side="back",
            text="Present Address: ঢাকা, বাংলাদেশ\nPermanent Address: কুমিল্লা, বাংলাদেশ",
            lines=[
                OCRLine(text="Present Address: ঢাকা, বাংলাদেশ", confidence=90.0, side="back", variant="original", line_number=1),
                OCRLine(text="Permanent Address: কুমিল্লা, বাংলাদেশ", confidence=90.0, side="back", variant="original", line_number=2),
            ],
            average_confidence=90.0,
        )


def test_extract_endpoint_integration(client) -> None:
    app.dependency_overrides[get_extraction_service] = lambda: ExtractionService(
        settings=get_settings(),
        image_service=get_image_service(),
        ocr_service=FakeOCRService(),
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
        assert payload["dateOfBirth"] == "1998-01-15"
        assert payload["nidNumber"] == "1234567890123"
        assert payload["presentAddress"] is not None
        assert set(payload) == {"name", "fatherName", "motherName", "dateOfBirth", "nidNumber", "presentAddress", "permanentAddress"}
    finally:
        app.dependency_overrides.clear()

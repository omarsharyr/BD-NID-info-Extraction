from app.api.dependencies import get_extraction_service
from app.core.exceptions import OCRProcessingError
from app.main import app


class BrokenExtractionService:
    async def extract(self, front_image, back_image):
        raise OCRProcessingError()


def test_ocr_failure_returns_expected_error(client) -> None:
    app.dependency_overrides[get_extraction_service] = lambda: BrokenExtractionService()
    try:
        response = client.post(
            "/api/v1/nid/extract",
            files={"front_image": ("front.png", b"123", "image/png"), "back_image": ("back.png", b"123", "image/png")},
        )
        assert response.status_code == 500
        assert response.json()["error"]["code"] == "OCR_PROCESSING_FAILED"
    finally:
        app.dependency_overrides.clear()

from io import BytesIO

from app.api.dependencies import get_extraction_service
from app.main import app


def test_unsupported_file_type_returns_error(client) -> None:
    response = client.post(
        "/api/v1/nid/extract",
        files={
            "front_image": ("front.txt", b"plain text", "text/plain"),
            "back_image": ("back.png", b"123", "image/png"),
        },
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "UNSUPPORTED_FILE_TYPE"


def test_corrupted_image_returns_error(client) -> None:
    response = client.post(
        "/api/v1/nid/extract",
        files={
            "front_image": ("front.png", b"not-an-image", "image/png"),
            "back_image": ("back.png", b"not-an-image", "image/png"),
        },
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "CORRUPTED_IMAGE"

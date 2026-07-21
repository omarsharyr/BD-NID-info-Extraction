from io import BytesIO

from PIL import Image


def test_too_small_image_rejected(client) -> None:
    image = Image.new("RGB", (20, 20), color="white")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    response = client.post(
        "/api/v1/nid/extract",
        files={
            "front_image": ("front.png", buffer.getvalue(), "image/png"),
            "back_image": ("back.png", buffer.getvalue(), "image/png"),
        },
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "IMAGE_TOO_SMALL"

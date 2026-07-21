def test_missing_back_image_returns_custom_error(client) -> None:
    response = client.post(
        "/api/v1/nid/extract",
        files={"front_image": ("front.png", b"123", "image/png")},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "MISSING_BACK_IMAGE"

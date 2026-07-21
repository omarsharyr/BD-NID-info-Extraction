from app.main import app


def test_landing_page_renders_focused_extraction_experience(client) -> None:
    response = client.get("/")
    assert response.status_code == 200
    body = response.text
    assert "Two images in." in body
    assert "front_image" in body
    assert "back_image" in body
    assert "/api/v1/nid/extract" in body
    assert "Evaluator ready" not in body
    assert "docker compose up --build" not in body
    assert "Swagger UI" not in body
    assert "Pricing" not in body
    assert "Testimonials" not in body
    assert "__APP_NAME__" not in body

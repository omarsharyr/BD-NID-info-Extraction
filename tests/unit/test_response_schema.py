from app.models.responses import ExtractionResponse


def test_response_schema_is_flat_and_uses_camel_case() -> None:
    response = ExtractionResponse(name="Md. Rahim", date_of_birth="1998-01-15", nid_number="1234567890123")
    payload = response.model_dump(by_alias=True)

    assert payload == {
        "name": "Md. Rahim",
        "fatherName": None,
        "motherName": None,
        "dateOfBirth": "1998-01-15",
        "nidNumber": "1234567890123",
        "presentAddress": None,
        "permanentAddress": None,
    }

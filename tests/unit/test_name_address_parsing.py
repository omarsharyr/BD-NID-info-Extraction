from app.models.internal import OCRLine, OCRResult
from app.services.parser_service import ParserService


def _result(side: str, texts: list[str]) -> OCRResult:
    return OCRResult(
        side=side,
        text="\n".join(texts),
        lines=[
            OCRLine(text=text, confidence=92.0, side=side, variant="original", line_number=index)
            for index, text in enumerate(texts, start=1)
        ],
        average_confidence=92.0,
    )


def test_extract_name_and_same_line_address_fields() -> None:
    parser = ParserService()
    front = _result(
        "front",
        [
            "Name: \u09ae\u09cb\u0983 \u09b0\u09b9\u09bf\u09ae",
            "Father's Name: \u0986\u09ac\u09cd\u09a6\u09c1\u09b2 \u0995\u09b0\u09bf\u09ae",
            "Date of Birth: 15/01/1998",
        ],
    )
    back = _result(
        "back",
        [
            "Present Address: \u09a2\u09be\u0995\u09be",
            "Permanent Address: \u0995\u09c1\u09ae\u09bf\u09b2\u09cd\u09b2\u09be",
        ],
    )

    parsed = parser.parse(front, back)

    assert parsed.fields["dateOfBirth"].value == "1998-01-15"
    assert parsed.fields["name"].value == "\u09ae\u09cb\u0983 \u09b0\u09b9\u09bf\u09ae"
    assert parsed.fields["presentAddress"].value == "\u09a2\u09be\u0995\u09be"
    assert parsed.fields["permanentAddress"].value == "\u0995\u09c1\u09ae\u09bf\u09b2\u09cd\u09b2\u09be"


def test_extracts_values_from_bengali_labels() -> None:
    parser = ParserService()
    front = _result(
        "front",
        [
            "\u09a8\u09be\u09ae: \u09ae\u09cb\u0983 \u09b0\u09b9\u09bf\u09ae",
            "\u09aa\u09bf\u09a4\u09be\u09b0 \u09a8\u09be\u09ae: \u0986\u09ac\u09cd\u09a6\u09c1\u09b2 \u0995\u09b0\u09bf\u09ae",
            "\u09ae\u09be\u09a4\u09be\u09b0 \u09a8\u09be\u09ae: \u0986\u09ae\u09c7\u09a8\u09be \u09ac\u09c7\u0997\u09ae",
        ],
    )

    parsed = parser.parse(front, _result("back", []))

    assert parsed.fields["name"].value == "\u09ae\u09cb\u0983 \u09b0\u09b9\u09bf\u09ae"
    assert parsed.fields["fatherName"].value == "\u0986\u09ac\u09cd\u09a6\u09c1\u09b2 \u0995\u09b0\u09bf\u09ae"
    assert parsed.fields["motherName"].value == "\u0986\u09ae\u09c7\u09a8\u09be \u09ac\u09c7\u0997\u09ae"

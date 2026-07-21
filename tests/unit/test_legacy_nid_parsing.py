from app.models.internal import OCRLine, OCRResult
from app.services.parser_service import ParserService


def _ocr(side: str, texts: list[str]) -> OCRResult:
    return OCRResult(
        side=side,
        text="\n".join(texts),
        lines=[
            OCRLine(text=text, confidence=88.0, side=side, variant="original", line_number=index)
            for index, text in enumerate(texts, 1)
        ],
        average_confidence=88.0,
    )


def test_legacy_card_recovers_identity_from_labels_and_mrz() -> None:
    front = _ocr(
        "front",
        [
            "Government of the People's Republic of Bangladesh",
            "Name",
            "S. M. ARIFUL ISLAM",
            "\u09aa\u09bf\u09a4\u09be",
            "\u098f\u09b8. \u098f\u09ae \u0986\u09ac\u09a6\u09c1\u09b2 \u099c\u09be\u09b2\u09be\u09b2",
            "\u09ae\u09be\u09a4\u09be",
            "\u0989\u09ae\u09cd\u09ae\u09c7 \u0995\u09c1\u09b2\u09b8\u09c1\u09ae",
            "Date of Birth 05 Feb 1976",
        ],
    )
    back = _ocr(
        "back",
        [
            "\u09a0\u09bf\u0995\u09be\u09a8\u09be: \u09ac\u09be\u09b8\u09be/\u09b9\u09cb\u09b2\u09cd\u09a1\u09bf\u0982: \u0995-\u09e9/\u09e7, \u0997\u09cd\u09b0\u09be\u09ae/\u09b0\u09be\u09b8\u09cd\u09a4\u09be: \u09b8\u09cb\u09ac\u09be\u09b9\u09be\u09a8\u09ac\u09be\u0997",
            "Blood Group:     Place of Birth: NARAIL",
            "I<BGD867322807<10<<<<<<<<<<<<<<<",
            "7602056M3111219BGD<<<<<<<<<<<<2",
            "ISLAM<<S<M<ARIFUL<<<<<<<<<<<<<<",
        ],
    )

    parsed = ParserService().parse(front, back)

    assert parsed.fields["name"].value == "S. M. Ariful Islam"
    assert parsed.fields["fatherName"].value == "\u098f\u09b8. \u098f\u09ae \u0986\u09ac\u09a6\u09c1\u09b2 \u099c\u09be\u09b2\u09be\u09b2"
    assert parsed.fields["motherName"].value == "\u0989\u09ae\u09cd\u09ae\u09c7 \u0995\u09c1\u09b2\u09b8\u09c1\u09ae"
    assert parsed.fields["dateOfBirth"].value == "1976-02-05"
    assert parsed.fields["nidNumber"].value == "8673228071"
    assert "\u09b8\u09cb\u09ac\u09be\u09b9\u09be\u09a8\u09ac\u09be\u0997" in parsed.fields["presentAddress"].value
    assert parsed.fields["permanentAddress"].value == parsed.fields["presentAddress"].value


def test_header_is_not_used_as_name() -> None:
    parsed = ParserService().parse(
        _ocr("front", ["Government of the People's Republic of Bangladesh", "05 Feb 1976"]),
        _ocr("back", []),
    )
    assert parsed.fields["name"].value is None


def test_mrz_with_single_fillers_recovers_name_and_ten_digit_nid() -> None:
    parsed = ParserService().parse(
        _ocr("front", ["Name", "S.M.ARIFULISLAM", "Father"]),
        _ocr("back", ["I<BGD867322807<10<<<<<<<<", "ISLAM<S<M<ARIFUL<<<<<<<<"]),
    )

    assert parsed.fields["name"].value == "S. M. Ariful Islam"
    assert parsed.fields["nidNumber"].value == "8673228071"
    assert parsed.fields["fatherName"].value is None

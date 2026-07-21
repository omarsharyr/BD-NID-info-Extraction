from app.services.parser_service import ParserService


def test_label_matching_detects_bengali_father_label() -> None:
    parser = ParserService()
    assert parser._looks_like_label("পিতার নাম")


def test_label_matching_detects_english_present_address() -> None:
    parser = ParserService()
    assert parser._looks_like_label("Present Address")

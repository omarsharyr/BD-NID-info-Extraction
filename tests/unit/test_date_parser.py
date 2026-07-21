from app.utils.date_parser import extract_birth_date, normalize_date_text


def test_normalize_date_text_iso() -> None:
    assert normalize_date_text("1998-01-15") == "1998-01-15"


def test_normalize_date_text_slash_format() -> None:
    assert normalize_date_text("15/01/1998") == "1998-01-15"


def test_extract_birth_date_bengali_digits() -> None:
    assert extract_birth_date("১৯৯৮/০১/১৫") == "1998-01-15"

from app.utils.bengali_digits import normalize_bengali_digits


def test_normalize_bengali_digits() -> None:
    assert normalize_bengali_digits("১৯৯৮-০১-১৫") == "1998-01-15"


def test_normalize_bengali_digits_mixed_text() -> None:
    assert normalize_bengali_digits("NID ১২৩৪৫") == "NID 12345"

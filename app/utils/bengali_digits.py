"""Bengali numeral conversion utilities."""

from __future__ import annotations

_BN_TO_EN = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")


def normalize_bengali_digits(text: str) -> str:
    return text.translate(_BN_TO_EN)


def contains_bengali_digits(text: str) -> bool:
    return any(character in "০১২৩৪৫৬৭৮৯" for character in text)

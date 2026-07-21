"""Text normalization helpers for OCR output."""

from __future__ import annotations

import re
import unicodedata

from app.utils.bengali_digits import normalize_bengali_digits

_ZERO_WIDTH_RE = re.compile(r"[\u200b\u200c\u200d\ufeff]")
_WHITESPACE_RE = re.compile(r"\s+")


def normalize_unicode_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text)
    normalized = _ZERO_WIDTH_RE.sub("", normalized)
    normalized = normalized.replace("\r", "\n")
    normalized = normalize_bengali_digits(normalized)
    normalized = normalized.replace("।", ".")
    normalized = normalized.replace("’", "'").replace("`", "'")
    normalized = normalized.replace("“", '"').replace("”", '"')
    normalized = normalized.replace("—", "-")
    normalized = _WHITESPACE_RE.sub(" ", normalized)
    return normalized.strip()


def normalize_for_matching(text: str) -> str:
    normalized = normalize_unicode_text(text).lower()
    normalized = re.sub(r"[^\w\u0980-\u09ff]+", " ", normalized)
    return _WHITESPACE_RE.sub(" ", normalized).strip()


def split_ocr_lines(text: str) -> list[str]:
    lines = []
    for raw_line in text.splitlines():
        cleaned = normalize_unicode_text(raw_line)
        if cleaned:
            lines.append(cleaned)
    return lines


def strip_label_prefix(text: str, label: str) -> str:
    normalized_text = normalize_for_matching(text)
    normalized_label = normalize_for_matching(label)
    if normalized_text.startswith(normalized_label):
        return text[len(label) :].lstrip(" :-ঃ\t")
    return text

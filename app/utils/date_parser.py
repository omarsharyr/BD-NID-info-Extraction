"""Date normalization utilities."""

from __future__ import annotations

import re
from datetime import date, datetime

from app.utils.text_normalizer import normalize_unicode_text

MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
    "জানুয়ারি": 1,
    "জানুয়ারি": 1,
    "ফেব্রুয়ারি": 2,
    "ফেব্রুয়ারি": 2,
    "মার্চ": 3,
    "এপ্রিল": 4,
    "মে": 5,
    "জুন": 6,
    "জুলাই": 7,
    "আগস্ট": 8,
    "সেপ্টেম্বর": 9,
    "অক্টোবর": 10,
    "নভেম্বর": 11,
    "ডিসেম্বর": 12,
}

DATE_PATTERNS = [
    re.compile(r"\b(?P<day>\d{1,2})[./-](?P<month>\d{1,2})[./-](?P<year>\d{2,4})\b"),
    re.compile(r"\b(?P<year>\d{4})[./-](?P<month>\d{1,2})[./-](?P<day>\d{1,2})\b"),
    re.compile(r"\b(?P<day>\d{1,2})\s+(?P<month>[A-Za-z\u0980-\u09ff]+)\s+(?P<year>\d{4})\b"),
]


def _build_date(year: int, month: int, day: int) -> str | None:
    try:
        return date(year, month, day).isoformat()
    except ValueError:
        return None


def normalize_date_text(text: str) -> str | None:
    cleaned = normalize_unicode_text(text)
    cleaned = cleaned.replace(",", " ")
    for pattern in DATE_PATTERNS:
        match = pattern.search(cleaned)
        if not match:
            continue
        groups = match.groupdict()
        day = int(groups["day"])
        month_value = groups["month"].lower()
        year = int(groups["year"])
        if len(groups["year"]) == 2:
            year += 2000 if year < 50 else 1900
        if month_value.isdigit():
            month = int(month_value)
        else:
            month = MONTHS.get(month_value)
            if month is None:
                month = MONTHS.get(month_value.title())
        if month is None:
            continue
        normalized = _build_date(year, month, day)
        if normalized:
            return normalized
    return None


def extract_birth_date(text: str) -> str | None:
    return normalize_date_text(text)


def is_valid_iso_date(value: str | None) -> bool:
    if not value:
        return False
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False

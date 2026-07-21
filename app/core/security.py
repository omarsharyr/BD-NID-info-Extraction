"""Security helpers for file handling and sensitive data masking."""

from __future__ import annotations

import os
import re
import uuid

_SAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9_.-]+")


def safe_filename(original_name: str | None, prefix: str) -> str:
    extension = ""
    if original_name and "." in original_name:
        extension = os.path.splitext(original_name)[1].lower()
    cleaned_prefix = _SAFE_FILENAME_RE.sub("_", prefix.strip().lower())
    return f"{cleaned_prefix}_{uuid.uuid4().hex}{extension}"


def mask_nid_number(value: str | None) -> str | None:
    if not value:
        return None
    digits = re.sub(r"\D", "", value)
    if len(digits) <= 4:
        return "*" * len(digits)
    return f"{digits[:2]}{'*' * (len(digits) - 4)}{digits[-2:]}"

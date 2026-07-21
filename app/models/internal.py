"""Internal dataclasses used by services."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass(slots=True)
class OCRLine:
    text: str
    confidence: float
    side: str
    variant: str
    line_number: int


@dataclass(slots=True)
class OCRResult:
    side: str
    text: str
    lines: list[OCRLine] = field(default_factory=list)
    average_confidence: float = 0.0
    variant_scores: dict[str, float] = field(default_factory=dict)
    readable: bool = False


@dataclass(slots=True)
class ImageQualityReport:
    side: str
    width: int
    height: int
    file_size_bytes: int
    blur_score: float
    brightness: float
    contrast: float
    warnings: list[str] = field(default_factory=list)
    confidence: float = 0.0
    readable: bool = True


@dataclass(slots=True)
class PreparedImage:
    side: str
    original_bytes: bytes
    image: np.ndarray
    quality: ImageQualityReport
    variants: dict[str, np.ndarray] = field(default_factory=dict)


@dataclass(slots=True)
class FieldValue:
    value: str | None
    confidence: float = 0.0
    source_side: str | None = None
    source_text: str | None = None


@dataclass(slots=True)
class ParsedDocument:
    fields: dict[str, FieldValue]
    warnings: list[str] = field(default_factory=list)
    nid_candidates: list[str] = field(default_factory=list)

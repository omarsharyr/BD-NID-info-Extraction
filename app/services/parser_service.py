"""OCR text parsing and field extraction logic."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from app.constants.nid_labels import FIELD_LABELS
from app.models.internal import FieldValue, OCRLine, OCRResult, ParsedDocument
from app.utils.date_parser import extract_birth_date
from app.utils.fuzzy_matching import best_match, similarity
from app.utils.text_normalizer import normalize_for_matching, normalize_unicode_text, strip_label_prefix

logger = logging.getLogger(__name__)

_NID_CANDIDATE_RE = re.compile(r"(?<!\d)(?:\d[\s-]?){9,16}\d(?!\d)")
_MRZ_ID_RE = re.compile(r"[I1][<\s]*B[G6]D[<\s]*([0-9O]{9})<([0-9O])", re.IGNORECASE)
_MRZ_BIRTH_RE = re.compile(r"(?<!\d)(\d{6})\d?[MF<]", re.IGNORECASE)
_HEADER_TERMS = {
    "government", "people", "republic", "bangladesh", "national", "identity", "card",
    "গণপ্রজাতন্ত্রী", "বাংলাদেশ", "সরকার", "জাতীয়", "পরিচয়পত্র",
}


@dataclass(slots=True)
class ParserService:
    def parse(self, front_result: OCRResult, back_result: OCRResult) -> ParsedDocument:
        lines = [*front_result.lines, *back_result.lines]
        grouped_fields: dict[str, FieldValue] = {}
        warnings: list[str] = []
        mrz_fields = self._extract_mrz_fields(back_result)

        grouped_fields["name"] = self._extract_simple_field(lines, "name", front_preferred=True)
        grouped_fields["fatherName"] = self._extract_simple_field(lines, "fatherName", front_preferred=True)
        grouped_fields["motherName"] = self._extract_simple_field(lines, "motherName", front_preferred=True)
        grouped_fields["dateOfBirth"] = self._extract_date_of_birth(lines, front_result)
        grouped_fields["nidNumber"] = self._extract_nid_number(lines)
        grouped_fields["presentAddress"] = self._extract_address(lines, "presentAddress", preferred_side="back")
        grouped_fields["permanentAddress"] = self._extract_address(lines, "permanentAddress", preferred_side="back")

        for field_name in ("name", "nidNumber"):
            if field_name in mrz_fields:
                grouped_fields[field_name] = mrz_fields[field_name]
        if not grouped_fields["dateOfBirth"].value and "dateOfBirth" in mrz_fields:
            grouped_fields["dateOfBirth"] = mrz_fields["dateOfBirth"]

        if not grouped_fields["presentAddress"].value and not grouped_fields["permanentAddress"].value:
            legacy_address = self._extract_legacy_address(lines)
            if legacy_address.value:
                grouped_fields["presentAddress"] = legacy_address
                grouped_fields["permanentAddress"] = FieldValue(
                    value=legacy_address.value,
                    confidence=legacy_address.confidence,
                    source_side=legacy_address.source_side,
                    source_text=legacy_address.source_text,
                )
                warnings.append("This NID contains one address block; it was returned for both address fields.")

        if not grouped_fields["name"].value:
            warnings.append("Full name could not be extracted.")
        if not grouped_fields["fatherName"].value:
            warnings.append("Father's name could not be extracted.")
        if not grouped_fields["motherName"].value:
            warnings.append("Mother's name could not be extracted.")
        if not grouped_fields["dateOfBirth"].value:
            warnings.append("Date of birth could not be extracted.")
        if not grouped_fields["nidNumber"].value:
            warnings.append("NID number could not be extracted.")
        if not grouped_fields["presentAddress"].value:
            warnings.append("Present address could not be extracted.")
        if not grouped_fields["permanentAddress"].value:
            warnings.append("Permanent address could not be extracted.")

        return ParsedDocument(fields=grouped_fields, warnings=warnings)

    def _extract_simple_field(self, lines: list[OCRLine], field_name: str, front_preferred: bool = False) -> FieldValue:
        aliases = FIELD_LABELS[field_name]
        candidates: list[FieldValue] = []
        for index, line in enumerate(lines):
            matched_alias, score = self._match_label(line.text, aliases, threshold=0.65)
            if not matched_alias:
                continue
            remainder = self._extract_value_from_line(line.text, matched_alias)
            if remainder:
                candidates.append(FieldValue(value=remainder, confidence=self._confidence_from_match(line, score), source_side=line.side, source_text=line.text))
                continue
            next_value = self._collect_following_value(lines, index + 1, source_side=line.side)
            if next_value:
                candidates.append(FieldValue(value=next_value, confidence=self._confidence_from_match(line, score) * 0.95, source_side=line.side, source_text=line.text))
        candidates = [
            candidate
            for candidate in candidates
            if candidate.value
            and not self._is_header_text(candidate.value)
            and self._is_plausible_person_value(candidate.value)
            and candidate.confidence >= 0.5
        ]
        if candidates:
            return max(candidates, key=lambda candidate: candidate.confidence)
        if field_name == "name" and front_preferred:
            fallback = self._find_first_non_label_line(lines, preferred_side="front")
            if fallback:
                return fallback
        return FieldValue(value=None)

    def _extract_date_of_birth(self, lines: list[OCRLine], front_result: OCRResult) -> FieldValue:
        aliases = FIELD_LABELS["dateOfBirth"]
        for index, line in enumerate(lines):
            matched_alias, _ = self._match_label(line.text, aliases, threshold=0.68)
            if not matched_alias:
                continue
            candidate_text = self._extract_value_from_line(line.text, matched_alias) or self._collect_following_value(
                lines, index + 1, allow_multiple=False, source_side=line.side
            )
            parsed = extract_birth_date(candidate_text or line.text)
            if parsed:
                return FieldValue(value=parsed, confidence=self._confidence_from_match(line, 0.9), source_side=line.side, source_text=line.text)
        parsed = extract_birth_date(front_result.text)
        if parsed:
            return FieldValue(value=parsed, confidence=max(0.6, front_result.average_confidence / 100.0), source_side=front_result.side, source_text=front_result.text)
        return FieldValue(value=None)

    def _extract_nid_number(self, lines: list[OCRLine]) -> FieldValue:
        candidates: list[tuple[str, float, str, str]] = []
        for line in lines:
            normalized = normalize_unicode_text(line.text)
            raw_candidates = list(_NID_CANDIDATE_RE.finditer(normalized))
            _, label_score = self._match_label(normalized, FIELD_LABELS["nidNumber"], threshold=0.0)
            for match in raw_candidates:
                if label_score < 0.55:
                    continue
                candidate = re.sub(r"[\s-]", "", match.group(0))
                if len(candidate) not in {10, 13, 17}:
                    continue
                confidence = self._nid_candidate_confidence(candidate, line.confidence, label_score)
                candidates.append((candidate, confidence, line.side, line.text))

        if not candidates:
            return FieldValue(value=None)

        candidates.sort(key=lambda item: (item[1], len(item[0])), reverse=True)
        selected = candidates[0]
        return FieldValue(value=selected[0], confidence=min(1.0, selected[1]), source_side=selected[2], source_text=selected[3])

    def _extract_address(self, lines: list[OCRLine], field_name: str, preferred_side: str) -> FieldValue:
        aliases = FIELD_LABELS[field_name]
        for index, line in enumerate(lines):
            if line.side != preferred_side:
                continue
            matched_alias, score = self._match_label(line.text, aliases, threshold=0.62)
            if not matched_alias:
                continue
            remainder = self._extract_value_from_line(line.text, matched_alias)
            if remainder:
                return FieldValue(value=remainder, confidence=self._confidence_from_match(line, score), source_side=line.side, source_text=line.text)
            value_lines = self._collect_address_lines(lines, index + 1, line.side)
            value = self._normalize_address_block(value_lines)
            if value:
                return FieldValue(value=value, confidence=self._confidence_from_match(line, score), source_side=line.side, source_text=line.text)
        return FieldValue(value=None)

    def _extract_value_from_line(self, line_text: str, label: str) -> str | None:
        normalized_line = normalize_unicode_text(line_text)
        normalized_label = normalize_unicode_text(label)
        matching_line = normalize_for_matching(normalized_line)
        matching_label = normalize_for_matching(normalized_label)
        if matching_label in matching_line:
            if ":" in normalized_line:
                remainder = normalized_line.split(":", 1)[1]
            elif "-" in normalized_line:
                remainder = normalized_line.split("-", 1)[1]
            elif "|" in normalized_line:
                remainder = normalized_line.split("|", 1)[1]
            else:
                remainder = strip_label_prefix(normalized_line, normalized_label)
            remainder = re.sub(r"^[\s:-|,;]+", "", remainder)
            return remainder or None
        return None

    def _collect_following_value(
        self,
        lines: list[OCRLine],
        start_index: int,
        allow_multiple: bool = True,
        source_side: str | None = None,
    ) -> str | None:
        collected: list[str] = []
        for line in lines[start_index : start_index + (4 if allow_multiple else 1)]:
            if source_side and line.side != source_side:
                break
            if self._looks_like_label(line.text):
                break
            collected.append(line.text)
            if not allow_multiple:
                break
        value = " ".join(collected).strip()
        return value or None

    def _is_plausible_person_value(self, text: str) -> bool:
        if any(character.isdigit() for character in text):
            return False
        letters = re.findall(r"[A-Za-z\u0980-\u09ff]", text)
        return len(letters) >= 3

    def _collect_address_lines(self, lines: list[OCRLine], start_index: int, side: str) -> list[str]:
        collected: list[str] = []
        for line in lines[start_index:]:
            if line.side != side:
                continue
            if self._is_address_boundary(line.text):
                break
            if self._looks_like_label(line.text) and collected:
                break
            if self._looks_like_label(line.text) and not collected:
                continue
            cleaned = normalize_unicode_text(line.text)
            if cleaned:
                collected.append(cleaned)
            if len(collected) >= 6:
                break
        return collected

    def _is_address_boundary(self, text: str) -> bool:
        normalized = normalize_for_matching(text)
        return any(
            marker in normalized
            for marker in ("blood group", "place of birth", "issue date", "date of issue")
        ) or bool(re.match(r"^[I1][<\s]*BGD", normalized, re.IGNORECASE))

    def _normalize_address_block(self, lines: list[str]) -> str | None:
        if not lines:
            return None
        joined = ", ".join(part for part in lines if part)
        joined = re.sub(r"\s*,\s*", ", ", joined)
        joined = re.sub(r"\s+", " ", joined).strip(" ,")
        return joined or None

    def _find_first_non_label_line(self, lines: list[OCRLine], preferred_side: str) -> FieldValue | None:
        candidates: list[tuple[float, OCRLine, str]] = []
        for line in lines:
            if line.side != preferred_side:
                continue
            if self._looks_like_label(line.text):
                continue
            cleaned = normalize_unicode_text(line.text)
            if not cleaned or self._is_header_text(cleaned) or any(character.isdigit() for character in cleaned):
                continue
            words = re.findall(r"[A-Za-z\u0980-\u09ff]+", cleaned)
            if not 2 <= len(words) <= 6:
                continue
            uppercase_bonus = 0.15 if any(character.isalpha() for character in cleaned) and cleaned.upper() == cleaned else 0.0
            candidates.append((line.confidence / 100.0 + uppercase_bonus, line, cleaned))
        if not candidates:
            return None
        _, line, cleaned = max(candidates, key=lambda item: item[0])
        return FieldValue(value=cleaned, confidence=max(0.55, line.confidence / 100.0), source_side=line.side, source_text=line.text)

    def _is_header_text(self, text: str) -> bool:
        normalized = normalize_for_matching(text)
        words = set(normalized.split())
        return bool(words & _HEADER_TERMS)

    def _extract_legacy_address(self, lines: list[OCRLine]) -> FieldValue:
        aliases = ["address", "ঠিকানা"]
        for index, line in enumerate(lines):
            if line.side != "back":
                continue
            matched_alias, score = self._match_label(line.text, aliases, threshold=0.62)
            if not matched_alias:
                continue
            parts: list[str] = []
            remainder = self._extract_value_from_line(line.text, matched_alias)
            if remainder:
                parts.append(remainder)
            parts.extend(self._collect_address_lines(lines, index + 1, "back"))
            value = self._normalize_address_block(parts)
            if value:
                return FieldValue(value=value, confidence=self._confidence_from_match(line, score), source_side="back", source_text=line.text)
        return FieldValue(value=None)

    def _extract_mrz_fields(self, back_result: OCRResult) -> dict[str, FieldValue]:
        compact_lines = [re.sub(r"\s+", "", normalize_unicode_text(line.text)).upper() for line in back_result.lines]
        fields: dict[str, FieldValue] = {}
        for raw_line, compact in zip(back_result.lines, compact_lines):
            id_match = _MRZ_ID_RE.search(compact)
            if id_match:
                nid_number = id_match.group(1).replace("O", "0")
                nid_number += id_match.group(2).replace("O", "0")
                fields["nidNumber"] = FieldValue(nid_number, max(0.7, raw_line.confidence / 100.0), "back", raw_line.text)
            birth_match = _MRZ_BIRTH_RE.search(compact)
            if birth_match:
                value = birth_match.group(1)
                year = int(value[:2])
                year += 1900 if year >= 30 else 2000
                parsed = extract_birth_date(f"{year:04d}-{value[2:4]}-{value[4:6]}")
                if parsed:
                    fields["dateOfBirth"] = FieldValue(parsed, max(0.68, raw_line.confidence / 100.0), "back", raw_line.text)
            if "<" in compact and re.fullmatch(r"[A-Z<]{5,}", compact):
                name_tokens = [part for part in compact.strip("<").split("<") if part]
                surname, given_parts = name_tokens[0], name_tokens[1:]
                name_parts = given_parts + [surname]
                if len(name_parts) >= 2 and not any(part in {"BGD", "IDBGD"} for part in name_parts):
                    name = " ".join(part.title() if len(part) > 1 else f"{part}." for part in name_parts)
                    fields["name"] = FieldValue(name, max(0.72, raw_line.confidence / 100.0), "back", raw_line.text)
        return fields

    def _looks_like_label(self, text: str) -> bool:
        return any(self._match_label(text, aliases, threshold=0.68)[0] for aliases in FIELD_LABELS.values())

    def _match_label(self, text: str, aliases: list[str], threshold: float = 0.72) -> tuple[str | None, float]:
        """Match labels at the start of an OCR line without penalizing its value."""
        normalized_text = normalize_for_matching(text)
        winner: str | None = None
        winner_score = 0.0
        for alias in aliases:
            normalized_alias = normalize_for_matching(alias)
            if not normalized_alias:
                continue
            if normalized_text == normalized_alias:
                score = 1.0
            elif normalized_text.startswith(normalized_alias + " "):
                score = 0.98
            elif 0 <= normalized_text.find(normalized_alias) <= 3:
                score = 0.9
            else:
                prefix = normalized_text[: max(len(normalized_alias) + 4, 12)]
                score = similarity(prefix, normalized_alias)
            if score > winner_score:
                winner, winner_score = alias, score
        return (winner, winner_score) if winner_score >= threshold else (None, winner_score)

    def _label_score(self, text: str, aliases: list[str]) -> float:
        return max((similarity(text, alias) for alias in aliases), default=0.0)

    def _confidence_from_match(self, line: OCRLine, score: float) -> float:
        confidence = max(0.0, min(1.0, (line.confidence / 100.0) * 0.7 + score * 0.3))
        return confidence

    def _nid_candidate_confidence(self, candidate: str, ocr_confidence: float, label_score: float) -> float:
        length_score = {10: 0.72, 13: 0.9, 17: 0.95}.get(len(candidate), 0.6)
        base = (ocr_confidence / 100.0) * 0.45 + label_score * 0.35 + length_score * 0.2
        return min(1.0, base)

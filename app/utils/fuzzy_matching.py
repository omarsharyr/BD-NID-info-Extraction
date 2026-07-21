"""Lightweight fuzzy matching helpers used during label detection."""

from __future__ import annotations

from difflib import SequenceMatcher

from app.utils.text_normalizer import normalize_for_matching


def similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, normalize_for_matching(left), normalize_for_matching(right)).ratio()


def best_match(text: str, choices: list[str], threshold: float = 0.72) -> tuple[str | None, float]:
    winner: str | None = None
    winner_score = 0.0
    for choice in choices:
        score = similarity(text, choice)
        if score > winner_score:
            winner = choice
            winner_score = score
    if winner_score < threshold:
        return None, winner_score
    return winner, winner_score

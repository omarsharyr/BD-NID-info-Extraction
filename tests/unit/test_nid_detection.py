from app.models.internal import OCRLine
from app.services.parser_service import ParserService


def test_extract_nid_number_prefers_labeled_candidate() -> None:
    parser = ParserService()
    lines = [
        OCRLine(text="NID No 1234 5678 9012 3", confidence=92.0, side="front", variant="original", line_number=1),
        OCRLine(text="Other text", confidence=55.0, side="front", variant="original", line_number=2),
    ]
    result = parser._extract_nid_number(lines)
    assert result.value == "1234567890123"

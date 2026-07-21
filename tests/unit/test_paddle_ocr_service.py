from __future__ import annotations

import sys
from types import SimpleNamespace

import numpy as np

from app.core.config import Settings
from app.services.ocr_service import PaddleOCRService


class FakePaddleOCR:
    initialization: dict[str, object] = {}

    def __init__(self, **kwargs) -> None:
        self.__class__.initialization = kwargs

    def ocr(self, image, cls=True):
        assert image.shape == (100, 200, 3)
        assert cls is True
        return [[
            [[[10, 40], [90, 40], [90, 60], [10, 60]], ("NID No. 8673228071", 0.97)],
            [[[10, 10], [90, 10], [90, 30], [10, 30]], ("Name: S. M. Ariful Islam", 0.99)],
        ]]


def test_paddle_ocr_adapter_orders_and_normalizes_results(monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "paddleocr", SimpleNamespace(PaddleOCR=FakePaddleOCR))
    service = PaddleOCRService(Settings())

    result = service.extract_text(np.zeros((100, 200, 3), dtype=np.uint8), side="front")

    assert FakePaddleOCR.initialization["use_angle_cls"] is True
    assert FakePaddleOCR.initialization["lang"] == "en"
    assert [line.text for line in result.lines] == ["Name: S. M. Ariful Islam", "NID No. 8673228071"]
    assert result.average_confidence == 98.0
    assert result.readable is True

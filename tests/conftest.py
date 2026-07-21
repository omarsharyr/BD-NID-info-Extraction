from __future__ import annotations

import os
import sys
from pathlib import Path
from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# The existing test suite in this repo was written against the legacy
# OCR (PaddleOCR/Tesseract) + parser + translation pipeline. The app now
# defaults EXTRACTION_PROVIDER to "gemini", so pin tests to "legacy" unless
# a test explicitly overrides it (see tests/unit/test_gemini_extraction_service.py
# and tests/integration/test_extract_endpoint_gemini.py for the AI path).
os.environ.setdefault("EXTRACTION_PROVIDER", "legacy")

from app.main import app


def create_test_image(width: int = 1200, height: int = 800, text: str = "Bangladesh NID") -> bytes:
    image = Image.new("RGB", (width, height), color="white")
    drawer = ImageDraw.Draw(image)
    drawer.rectangle((20, 20, width - 20, height - 20), outline="black", width=6)
    drawer.line((20, height // 2, width - 20, height // 2), fill="black", width=4)
    drawer.line((width // 2, 20, width // 2, height - 20), fill="black", width=4)
    drawer.text((40, 40), text, fill="black")
    drawer.text((40, 110), "Name: Md. Rahim", fill="black")
    drawer.text((40, 180), "NID No: 1234 5678 9012 3", fill="black")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-ben \
        libgl1 \
        libglib2.0-0 \
        libgomp1 \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

COPY app ./app
COPY README.md ARCHITECTURE.md AI_USAGE.md .env.example pytest.ini ./

RUN useradd --create-home --shell /bin/bash appuser \
    && mkdir -p /tmp/nid-extractor \
    && chown -R appuser:appuser /app /tmp/nid-extractor

USER appuser

# Cache PaddleOCR models in the image so the optional legacy OCR path
# (EXTRACTION_PROVIDER=legacy) doesn't need network access at runtime.
# Default provider is now Gemini, so this is best-effort and never fails the build.
RUN python -c "from paddleocr import PaddleOCR; PaddleOCR(use_angle_cls=True, lang='en', show_log=False)" \
    || echo "PaddleOCR model pre-cache skipped; legacy OCR provider will download models on first use."

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health').read()"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

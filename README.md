# AI-Powered Bangladesh National ID Information Extraction System

Production-oriented FastAPI service that accepts the front and back images of a Bangladesh National ID card and returns structured JSON. As of this version, extraction is powered end-to-end by **Google Gemini** (multimodal, model configurable via `GEMINI_MODEL`): Gemini reads both card images directly and returns the already-translated (Bengali → English) fields in one call — no OCR engine required. The original OCR (PaddleOCR + Tesseract) + regex parser + local translation pipeline is still included and can be selected as a fallback.

## 0. Quick Start (Gemini, default)

1. Get a Gemini API key from https://aistudio.google.com/apikey.
2. Choose **one** of the following ways to provide it — the app reads `GEMINI_API_KEY` from the container's environment, not from any file baked into the image:

   **Option A — `docker run` (simplest, no files needed):**
   ```bash
   docker build -t bangladesh-nid-extractor .
   docker run -p 8000:8000 -e GEMINI_API_KEY=your-key-here bangladesh-nid-extractor
   ```

   **Option B — `docker compose up`:**
   ```bash
   cp .env.example .env
   # then edit .env and set: GEMINI_API_KEY=your-key-here
   docker compose up --build
   ```
   `docker-compose.yml` loads `.env` (not `.env.example`) at runtime, so the key must be set there. If `/api/v1/nid/extract` returns `AI_PROVIDER_NOT_CONFIGURED`, it means `.env` is missing, wasn't edited, or the container simply never received the variable — check with `docker compose config` to confirm the value is being picked up.
3. Open http://localhost:8000/docs and try `POST /api/v1/nid/extract` with `front_image` and `back_image`.

### Provider selection

The `EXTRACTION_PROVIDER` environment variable controls which pipeline handles requests:

| Value (default: `gemini`) | Behavior |
|---|---|
| `gemini` | Single AI call (Gemini, model set by `GEMINI_MODEL`) reads and translates both images. Requires `GEMINI_API_KEY`. |
| `legacy` | Original PaddleOCR/Tesseract OCR → regex parser → local transliteration pipeline. No API key needed. |

Relevant env vars (see `.env.example`):

```
EXTRACTION_PROVIDER=gemini
GEMINI_API_KEY=
GEMINI_MODEL=gemini-flash-latest
GEMINI_TIMEOUT_SECONDS=45
GEMINI_MAX_RETRIES=2
```

> **Note on model names:** `gemini-2.5-flash` was cut off for new API keys/projects mid-2026 as Google phases it out (existing keys keep working until the full shutdown date; new keys get a `404`). `gemini-flash-latest` is an alias that always points at Google's current stable Flash model, so it avoids this problem going forward. If you want to pin an explicit version instead of the auto-updating alias, use `gemini-3.5-flash` (current GA as of mid-2026). Check https://ai.google.dev/gemini-api/docs/models for the current list if you hit another `404`.

`GET /ready` reports which provider is active and whether it's configured correctly (`geminiConfigured` for the AI path, `ocr`/`translation` availability for the legacy path).

### Why Gemini instead of OCR

Bangla NID cards mix Bengali and English text, embossed/holographic elements, and non-standard layouts, which made traditional OCR + regex parsing brittle (missed fields, mis-segmented lines, transliteration that lost meaning). Gemini reads the image directly and produces meaning-preserving English translations in a single pass, which is both simpler to maintain and more accurate in practice. The OCR path remains in the codebase (`app/services/ocr_service.py`, `parser_service.py`, `translation_service.py`) behind `EXTRACTION_PROVIDER=legacy` for offline/no-API-key use.

---

The remainder of this document (below) describes the full system, including the legacy OCR pipeline architecture, which remains available via `EXTRACTION_PROVIDER=legacy`.

## 1. Project Overview

The service extracts the following fields from uploaded NID images:

- Full name
- Father's name
- Mother's name
- Date of birth
- NID number
- Present address
- Permanent address

By default it uses **Google Gemini** as a single multimodal extraction+translation step (`EXTRACTION_PROVIDER=gemini`, requires `GEMINI_API_KEY`). A fully local, offline pipeline (PaddleOCR + Tesseract OCR → regex parser → local transliteration, no API key or internet access needed) is also included and can be selected with `EXTRACTION_PROVIDER=legacy`.

The root URL serves a lightweight landing page with quick links to Swagger UI, ReDoc, health checks, readiness checks, and the upload endpoint.

## 2. Problem Statement

Bangladesh National ID cards contain critical identity information often printed in mixed Bengali and English, on non-standard layouts. This project validates uploaded front/back images, reads all visible text, translates the Bengali identity/address fields into natural English, normalizes digits and dates, and returns the required fields as flat JSON — regardless of which extraction backend is active.

## 3. Features

- Exactly two image uploads: `front_image` and `back_image`
- JPG, JPEG, and PNG support
- Image validation for corruption, size, blur, and readability
- Meaning-preserving Bengali → English translation (not literal/word-by-word)
- Two selectable extraction backends: Gemini (default, AI-based) or legacy local OCR
- Flat structured JSON with null fields for partial extraction, and meaningful error responses
- Health and readiness endpoints (provider-aware)
- Swagger UI and ReDoc
- Automated tests for both backends
- Docker and Docker Compose support

## 4. Technology Stack

- Python 3.11
- FastAPI, Uvicorn, Pydantic
- **Gemini backend (default):** `google-genai` SDK calling a Gemini multimodal model (`GEMINI_MODEL`, default `gemini-flash-latest`)
- **Legacy backend (optional, `EXTRACTION_PROVIDER=legacy`):** OpenCV + Pillow for preprocessing, PaddleOCR for English/MRZ, Tesseract (`ben` language pack) for Bengali OCR, plus a local regex parser and transliteration table
- pytest
- Docker, Docker Compose

## 5. Architecture Overview

Two extraction pipelines share the same validation layer and the same public response contract:

**Gemini pipeline (default):**
- `ImageService` validates uploads (format, size, corruption) and reads the raw bytes
- `GeminiNIDExtractionService` sends both images to Gemini in one call with a JSON response schema, asking it to read and translate the card directly
- `AIExtractionService` orchestrates the two steps above and maps Gemini's output onto the public `ExtractionResponse` model

**Legacy pipeline (`EXTRACTION_PROVIDER=legacy`):**
- `ImageService` validates uploads and builds preprocessing variants
- `HybridOCRService` combines PaddleOCR English/MRZ recognition with Tesseract Bengali OCR
- `ParserService` identifies labels and fields from the OCR text
- `LocalTranslationService` transliterates Bengali values into English
- `ExtractionService` orchestrates OCR → parsing → translation and builds the response

`app/api/dependencies.py` selects which pipeline handles each request based on `EXTRACTION_PROVIDER`. See `ARCHITECTURE.md` for the full request flow of both.

## 6. AI/OCR Engine and Language Support

- **Gemini (default):** a single multimodal call reads both images directly — no separate OCR step. Gemini is prompted to read Bengali and English text, normalize Bengali digits/dates, and translate identity/address fields into natural English, returning `null` for anything illegible rather than guessing.
- **Legacy OCR (fallback):** PaddleOCR's English model handles English fields and MRZ-like data, while Tesseract's Bengali (`ben`) model reads focused identity/address regions. Both outputs are normalized into one line model for parsing.

`GET /ready` reports the active provider and whether it's correctly configured (`geminiConfigured` for the Gemini path; `ocr`/`translation` availability for the legacy path) without changing the API contract either way.

## 7. Image Preprocessing Pipeline

Every upload — regardless of backend — goes through the same validation: file-type/size checks, corruption detection, and a minimum-resolution check.

For the **legacy** backend specifically, `ImageService` additionally builds several preprocessing variants before OCR: EXIF orientation correction, grayscale conversion, CLAHE contrast enhancement, noise reduction, adaptive thresholding, sharpening, and optional perspective correction. The OCR service evaluates multiple variants and chooses the strongest result. The **Gemini** backend does not need this step — it reads the original image directly.

## 8. Field-Parsing Approach

- **Gemini backend:** there is no separate parsing step. Gemini is given a strict JSON schema (name, father's name, mother's name, date of birth, NID number, present/permanent address, plus readability flags) and is instructed which fields typically appear on which side, how to normalize dates/digits, and to return `null` instead of inventing a value.
- **Legacy backend:** parsing combines label aliases in Bengali and English, fuzzy matching for OCR spelling noise, line-order analysis, regexes for NID numbers and dates, and address-block aggregation across consecutive lines. Front-side text is preferred for identity details, while address fields are preferred from the back side.

## 9. Translation Approach

- **Gemini backend:** translation happens in the same call as extraction. The prompt explicitly asks for meaning-preserving, natural English rather than a literal word-for-word conversion, with standard English spellings for Bangladeshi names and places.
- **Legacy backend:** a local translation layer normalizes Bengali Unicode, converts Bengali numerals to English digits, expands common prefixes (e.g. `মোঃ` → `Md.`), and transliterates common names/places using a local fallback table. For uncertain conversions it returns the original text rather than inventing an English equivalent.

## 10. Error-Handling Approach

The API returns a consistent JSON error shape (`{"success": false, "error": {"code", "message", "details"}}`) for cases such as:

- Missing front or back image
- Unsupported file type / empty upload / corrupted image / too-small image
- No NID information could be extracted from either image
- Gemini backend: missing `GEMINI_API_KEY`, or the Gemini request itself failing (network, quota, bad response)
- Legacy backend: OCR processing failure

See the full table of codes in [§20](#20-example-error-responses) below. Stack traces and internal details are not exposed in responses.

## 11. Privacy and Security Measures

- Uploaded images are not permanently stored by default
- NID numbers and personal details are not written to logs in full
- Upload size is limited; MIME type and image content are validated; filenames are not trusted
- `GEMINI_API_KEY` is read from environment variables only — never logged, never baked into the Docker image, never committed (`.env` is gitignored)
- Production responses stay sanitized; only `EXTRACTION_PROVIDER`, readiness booleans, and error codes are exposed via `/ready`

## 12. Local Installation Instructions

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

For the default Gemini backend, set `GEMINI_API_KEY` in your shell or a local `.env` before running `uvicorn app.main:app --reload`. For the legacy backend, the first PaddleOCR initialization downloads its model files. Docker is the more reproducible option either way — see below.

## 13. Docker Build Instructions

```bash
docker build -t bangladesh-nid-extractor .
```

## 14. Docker Run Instructions

```bash
docker run -p 8000:8000 -e GEMINI_API_KEY=your-key-here bangladesh-nid-extractor
```

`GEMINI_API_KEY` must be passed as a runtime environment variable — it is never baked into the image. To use the offline legacy pipeline instead (no key needed):

```bash
docker run -p 8000:8000 -e EXTRACTION_PROVIDER=legacy bangladesh-nid-extractor
```

## 15. Docker Compose Instructions

```bash
cp .env.example .env
# edit .env and set: GEMINI_API_KEY=your-key-here
docker compose up --build
```

`docker-compose.yml` loads environment variables from `.env` (not `.env.example`) at runtime, so the real key must be set there. If `/api/v1/nid/extract` returns `AI_PROVIDER_NOT_CONFIGURED`, run `docker compose config` to confirm the container actually received the variable.


## 16. API Endpoints

- `GET /`
- `GET /health`
- `GET /ready`
- `POST /api/v1/nid/extract`
- `GET /docs`
- `GET /redoc`
- `GET /openapi.json`

## 17. Request Example Using cURL

```bash
curl -X POST "http://localhost:8000/api/v1/nid/extract" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "front_image=@sample_data/nid_front.png" \
  -F "back_image=@sample_data/nid_back.png"
```

## 18. Example Success Response

```json
{
  "name": "Md. Rahim",
  "fatherName": "Abdul Karim",
  "motherName": "Amena Begum",
  "dateOfBirth": "1998-01-15",
  "nidNumber": "1234567890123",
  "presentAddress": "Dhaka, Bangladesh",
  "permanentAddress": "Cumilla, Bangladesh"
}
```

## 19. Example Partial-Extraction Response

```json
{
  "name": "Md. Rahim",
  "fatherName": null,
  "motherName": null,
  "dateOfBirth": "1998-01-15",
  "nidNumber": "1234567890",
  "presentAddress": null,
  "permanentAddress": null
}
```

## 20. Example Error Responses

```json
{
  "success": false,
  "error": {
    "code": "MISSING_BACK_IMAGE",
    "message": "The back-side NID image is required.",
    "details": null
  }
}
```

```json
{
  "success": false,
  "error": {
    "code": "UNSUPPORTED_FILE_TYPE",
    "message": "Only JPG, JPEG, and PNG files are supported.",
    "details": null
  }
}
```

### Full Error Code Reference

| Code | Meaning | HTTP |
|---|---|---|
| `MISSING_FRONT_IMAGE` | `front_image` was not provided | 400 |
| `MISSING_BACK_IMAGE` | `back_image` was not provided | 400 |
| `UNSUPPORTED_FILE_TYPE` | File isn't JPG/JPEG/PNG, or exceeds the size limit | 400 |
| `EMPTY_FILE` | Uploaded file has no content | 400 |
| `CORRUPTED_IMAGE` | File can't be decoded as a valid image | 400 |
| `IMAGE_TOO_SMALL` | Image is below the minimum resolution | 400 |
| `IMAGE_TOO_BLURRY` | Image is too blurry to process (legacy backend) | 400 |
| `NO_NID_INFORMATION_FOUND` | No fields could be extracted from either image | 422 |
| `AI_PROVIDER_NOT_CONFIGURED` | `GEMINI_API_KEY` is missing on the server (Gemini backend) | 500 |
| `AI_EXTRACTION_FAILED` | The Gemini request failed — network, quota, or an invalid response (Gemini backend) | 502 |
| `OCR_PROCESSING_FAILED` | The OCR pipeline failed (legacy backend only) | 500 |
| `INTERNAL_SERVER_ERROR` | Unexpected server error | 500 |

## 21. Swagger Documentation URL

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 22. Test Instructions

```bash
pytest
```

Tests cover both backends: Gemini extraction/translation (mocked SDK, no network or API key needed), the endpoint with a mocked Gemini dependency, and — for the legacy backend — Bengali numeral conversion, date normalization, label matching, parsing, translation, and OCR failure handling.

## 23. Project Structure

```text
nid-extractor/
├── app/
├── tests/
├── sample_data/
├── scripts/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── README.md
├── ARCHITECTURE.md
├── AI_USAGE.md
└── .env.example
```

## 24. Configuration Variables

See `.env.example` for the complete list.

**Provider selection**
- `EXTRACTION_PROVIDER` — `gemini` (default) or `legacy`

**Gemini backend**
- `GEMINI_API_KEY`
- `GEMINI_MODEL`
- `GEMINI_TIMEOUT_SECONDS`
- `GEMINI_MAX_RETRIES`

**Legacy OCR backend**
- `PADDLE_OCR_LANGUAGE`
- `PADDLE_USE_ANGLE_CLS`
- `TESSERACT_CMD`
- `OCR_CONFIDENCE_THRESHOLD`
- `TRANSLATION_PROVIDER`
- `TRANSLATION_API_URL`
- `TRANSLATION_API_KEY`

**Shared**
- `APP_ENV`
- `LOG_LEVEL`
- `MAX_UPLOAD_SIZE_MB`
- `MIN_IMAGE_WIDTH`
- `MIN_IMAGE_HEIGHT`
- `BLUR_THRESHOLD`
- `TEMP_DIR`
- `ENABLE_DEBUG`

## 25. Known Limitations

- Gemini backend depends on an external API — network issues, rate limits, or the occasional `503` (Google's servers under high demand) can cause a request to fail; the client should retry
- The API key must be kept out of source control and rotated if ever exposed
- OCR quality (legacy backend) depends on camera quality, glare, blur, cropping, and perspective distortion
- Old or damaged cards may not parse cleanly under either backend
- Different NID layouts can reduce field accuracy
- Bengali transliteration/translation is inherently ambiguous for some proper nouns

## 26. Future Improvements

- Surface Gemini's per-field `warnings` (currently only logged) in the API response so clients know *why* a field came back null
- Configurable confidence/uncertainty signal for the Gemini backend
- Stronger legacy OCR layout models and transliteration dictionary coverage
- Additional field extraction for card issue date and gender if required

## 27. AI Usage Summary

This repository was built with AI assistance (GitHub Copilot for the original scaffold, and Claude for migrating extraction to Gemini and for review/documentation) and manually reviewed and corrected in the workspace throughout. See `AI_USAGE.md` for the full disclosure.

## 28. Interview Demonstration Guide

1. Start the app with Docker: `docker compose up --build` (after `cp .env.example .env` and setting `GEMINI_API_KEY`)
2. Open Swagger UI at `http://localhost:8000/docs`, or use the landing page at `http://localhost:8000/`
3. Upload valid front and back card images through `POST /api/v1/nid/extract`
4. Show the extracted JSON response and point out `null` handling for unreadable fields
5. Demonstrate meaning-preserving translation, e.g. a Bengali name/address coming back as natural English rather than a literal transliteration
6. Demonstrate missing-image handling by omitting `back_image`
7. Demonstrate unsupported-file handling by uploading a `.txt` file
8. Demonstrate partial-extraction handling (e.g. a partially unreadable back image) and show the fields that came back `null`
9. Explain the architecture from upload to response assembly (§5)
10. Explain why the project moved from OCR+regex to a single Gemini call (§1, §8, §9) — mention OCR's brittleness with mixed Bengali/English layouts as the motivation
11. Explain the fallback legacy OCR pipeline and when `EXTRACTION_PROVIDER=legacy` would be used
12. Explain error handling and the full error-code table (§20)
13. Explain privacy/security measures, especially how the API key is handled (§11)
14. Explain containerization: Dockerfile, docker-compose, non-root runtime, and how `GEMINI_API_KEY` reaches the container
15. Run the test suite with `pytest` and walk through what's covered for each backend

## 29. Troubleshooting

- `AI_PROVIDER_NOT_CONFIGURED` — `GEMINI_API_KEY` isn't reaching the container. With Compose, confirm you copied `.env.example` to `.env` and set the key there (not `.env.example`), then check with `docker compose config`. With `docker run`, confirm `-e GEMINI_API_KEY=...` is on the command itself.
- `AI_EXTRACTION_FAILED` with a `403 PERMISSION_DENIED` — the underlying Google Cloud project/key is invalid, suspended, or not enabled for the Generative Language API. Verify the key at https://aistudio.google.com/apikey.
- `AI_EXTRACTION_FAILED` with a `404 NOT_FOUND` mentioning a specific model — that model name has been deprecated or cut off for new API keys. Use `GEMINI_MODEL=gemini-flash-latest` (an alias Google keeps pointed at its current stable Flash model) or check https://ai.google.dev/gemini-api/docs/models for the current list.
- `AI_EXTRACTION_FAILED` with a `503 UNAVAILABLE` — transient overload on Google's side; retry after a short delay, or raise `GEMINI_MAX_RETRIES`.
- If `/ready` reports the legacy OCR unavailable (only relevant when `EXTRACTION_PROVIDER=legacy`), inspect startup logs and confirm PaddleOCR models and the Tesseract `ben` language pack are available.
- If Docker build is slow, the (optional) legacy OCR packages are being installed inside the image; this doesn't block the default Gemini path from working.
- If uploads fail, confirm the request is `multipart/form-data` with both files present.

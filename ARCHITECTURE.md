# Architecture

The application supports two extraction backends behind the same route, same
validation layer, and same public response contract. `EXTRACTION_PROVIDER`
(env var) picks which one handles a request; `app/api/dependencies.py` wires
up the corresponding pipeline.

## Request Flow — Gemini backend (default, `EXTRACTION_PROVIDER=gemini`)

```text
Client
  ↓
FastAPI upload endpoint
  ↓
File and image validation (format, size, corruption)
  ↓
Single Gemini call: both images + a JSON response schema
  (Gemini reads Bengali + English text and translates
   identity/address fields to natural English in the same pass)
  ↓
Map Gemini's JSON onto the public response model
  ↓
Structured JSON response
```

## Request Flow — Legacy OCR backend (`EXTRACTION_PROVIDER=legacy`)

```text
Client
  ↓
FastAPI upload endpoint
  ↓
File and image validation
  ↓
Image-quality analysis (blur, size)
  ↓
Image preprocessing (multiple variants)
  ↓
Bengali and English OCR (Tesseract + PaddleOCR)
  ↓
Text normalization
  ↓
Label and field detection (regex + fuzzy matching)
  ↓
Date and NID-number normalization
  ↓
Name and address translation/transliteration (local)
  ↓
Structured JSON response
```

## Component Responsibilities

### FastAPI Layer

The API layer only handles HTTP concerns: routing, multipart form parsing,
dependency injection, and error serialization. It is identical for both
backends — `POST /api/v1/nid/extract` calls whichever extraction service
`get_extraction_service()` returns for the configured provider.

### Image Service

Shared by both backends. Validates file type, decodes the image safely,
checks for corruption and minimum size. For the legacy backend it also
builds multiple preprocessing variants (EXIF correction, CLAHE contrast,
denoising, adaptive thresholding, sharpening, optional perspective
correction) so OCR concerns stay isolated from validation.

### Gemini Service (`app/services/gemini_service.py`)

Wraps the `google-genai` SDK. Sends both images plus a structured JSON
schema and a prompt describing exactly what to extract and how to
translate it, with retry/backoff on transient failures and clear
exceptions (`AIProviderNotConfiguredError`, `AIExtractionError`) for
everything else — missing key, malformed response, API errors.

### AI Extraction Service (`app/services/ai_extraction_service.py`)

Orchestrates the Gemini path: validate images via `ImageService`, call
`GeminiNIDExtractionService`, map the result onto `ExtractionResponse`,
and raise `NoNidInformationFoundError` if nothing could be read at all.

### OCR / Parser / Translation Services (legacy path)

- `HybridOCRService` combines PaddleOCR English/MRZ recognition with
  Tesseract Bengali OCR into one line model.
- `ParserService` consumes OCR lines and identifies field values using
  label aliases, fuzzy matching, regexes, and line order.
- `LocalTranslationService` converts Bengali personal names and
  addresses to English with a local fallback table.
- `ExtractionService` orchestrates OCR → parsing → translation and
  builds the final public response.

## Why Two Backends

OCR + regex parsing was the original approach but proved brittle on real
NID photos: mixed Bengali/English layouts, holographic/embossed elements,
and non-standard card variants led to missed fields and literal (rather
than meaning-preserving) transliteration. Gemini reads the image directly
and translates in the same pass, which is simpler to maintain and more
accurate in practice — so it's now the default. The OCR pipeline is kept
available (`EXTRACTION_PROVIDER=legacy`) for fully offline / no-API-key use.

## Replaceability

- Swap extraction backends entirely via `EXTRACTION_PROVIDER`, no code
  changes required
- Replace the Gemini model via `GEMINI_MODEL` (e.g. to pin an explicit
  version instead of the `gemini-flash-latest` alias)
- Replace the legacy OCR service by implementing the `OCRService`
  interface, or the translation service by implementing the
  `TranslationService` interface
- Extend the legacy parser with new labels or more card layouts

## Why the Separation Matters

Bangladesh NID extraction is a noisy problem regardless of backend.
Keeping validation, extraction, and response-mapping as separate,
testable units means either pipeline can be improved, swapped, or
disabled without touching the API contract or the other pipeline.

# AI Usage Documentation

## AI Tools Used

- **GitHub Copilot** (GPT-5.4 mini model) — original project scaffold: the legacy OCR pipeline, FastAPI structure, tests, Docker setup, and initial documentation.
- **Claude (Anthropic)** — migrated extraction from OCR to a single Gemini-based call, fixed the resulting Docker/Compose/model-name issues found during real testing, added a landing-page UI with a live status/error-code reference, and rewrote this documentation set for consistency with the final architecture.

## Purpose of the Tooling

- Generate the initial project structure and legacy OCR/parser/translation pipeline (Copilot)
- Replace OCR-based extraction with a single Gemini multimodal call that reads and translates both card images directly, keeping the legacy pipeline available as a fallback (Claude)
- Diagnose and fix real runtime issues surfaced while testing against the live Gemini API — a malformed JSON response schema, a Docker Compose env-var precedence bug, a deprecated model name, and PowerShell-vs-bash command differences (Claude)
- Build a small landing-page UI with a live `/health`/`/ready` status strip, a copyable `curl` example, and a full error-code reference table (Claude)
- Keep README/ARCHITECTURE.md/AI_USAGE.md consistent with whichever pipeline is actually the default at any point (Copilot, then Claude)

## Example Prompts

- "I decided to remove the OCR-based approach and use an AI-based approach with Google Gemini 2.5 Flash — help me implement that" (start of the Gemini migration)
- "help me to implement that" together with a functional-requirements spec, asking for a REST API, Docker setup, and structured JSON output
- Iterative debugging prompts pasting the exact server error each time it changed, e.g. a Pydantic schema-validation error, a `.env` file-not-found error, a `403 PERMISSION_DENIED`, a `404` deprecated-model error, and a `503 UNAVAILABLE`
- "what changes i need to make if i can manage a key from ai pro account"
- "i want all 1,2,3,4" (referring to four proposed additions to the landing page: a curl example, an error-code table, a live status strip, and a pipeline diagram)

## AI-Assisted Code Sections

The following areas were generated with AI assistance and then reviewed:

- FastAPI application entrypoint and route wiring (Copilot; provider dependency-injection switch added by Claude)
- Configuration, exception, and logging helpers (Copilot; Gemini-specific settings/exceptions added by Claude)
- Hybrid PaddleOCR/Tesseract OCR pipeline, parser, and local transliteration service (Copilot; kept as the `EXTRACTION_PROVIDER=legacy` fallback)
- `app/services/gemini_service.py` and `app/services/ai_extraction_service.py` — the Gemini extraction/translation call and its orchestrator (Claude)
- Image validation and preprocessing pipeline (Copilot; reused unchanged by the Gemini path for validation)
- Pydantic response models (Copilot)
- Unit and integration tests, including the Gemini-path tests with a mocked SDK (Copilot for the legacy tests; Claude for the Gemini tests)
- Docker, Compose, landing-page UI, and all project documentation (Copilot for the original scaffold; Claude for the Gemini migration, the fixes below, and this document)

## Review Process

Each generated/modified section was checked for:

- Syntax correctness (`python -m py_compile` on every changed file before packaging)
- Public response shape staying unchanged regardless of which backend produced it
- Error-handling behavior (every new failure mode maps to a documented error code)
- Privacy and logging safety (no API key or full personal data in logs)
- Actual behavior against the live Gemini API, not just mocks — several real issues below were only caught this way

## Tests Used to Verify the Code

- `pytest` unit tests: Bengali digit conversion, date parsing, label matching, translation, response schema, and — for the Gemini path — a mocked-SDK test covering successful extraction, partial extraction, malformed JSON, an empty response, and an API failure
- Endpoint-level integration tests for health, readiness, upload validation errors, and the extraction endpoint under both a mocked legacy pipeline and a mocked Gemini service
- Manual end-to-end runs against the real Gemini API via Docker (`docker compose up --build`), which is what actually surfaced the issues listed below

## Generated Code That Was Changed, and Why

- **Gemini response schema** — the first version used JSON Schema's `"type": ["string", "null"]` union syntax. Google's SDK validates the schema as its own OpenAPI-style `Schema` type, which rejected that; fixed by using `"type": "string", "nullable": true` instead. Caught by an actual `AI_EXTRACTION_FAILED` response during testing, not by the mocked unit tests (the mocks don't validate schema shape).
- **`docker-compose.yml` env handling** — an earlier version force-overwrote `GEMINI_API_KEY` with `${GEMINI_API_KEY:-}` from the host shell, silently blanking out a key set in a real `.env` file. Simplified to load `.env` directly.
- **Default `GEMINI_MODEL`** — `gemini-2.5-flash` returned a `404` because it had been cut off for new API keys/projects. Switched the default to `gemini-flash-latest`, an alias Google keeps pointed at its current stable Flash model, to avoid repeating this when models are renamed again.
- **Image service was kept, not replaced** — corrupted/empty/wrong-type/too-small checks stayed exactly as Copilot originally wrote them; the Gemini path reuses them rather than duplicating validation logic.
- **Provider made switchable, not a hard replacement** — `EXTRACTION_PROVIDER=gemini|legacy` was added instead of deleting the OCR pipeline outright, so the original code stays available and testable.

## Why Those Changes Were Necessary

- They keep the implementation aligned with the requested API contract regardless of which backend is active
- They reflect what the live API actually returned during testing, not just what the SDK documentation implied
- They make the failure modes predictable and documented (see the error-code table in `README.md`)

## Security and Privacy Checks

- Uploaded images are not persisted by default
- `GEMINI_API_KEY` is read from environment variables only, never logged, and never baked into the Docker image
- `.env` is gitignored; only `.env.example` (no real secrets) is committed
- **Note:** during development, a real Gemini API key was pasted into this AI conversation more than once while debugging. That key should be treated as compromised and rotated at https://aistudio.google.com/apikey before or immediately after submission — it must not be the key left in any submitted `.env` file.
- API error payloads are free of stack traces and secrets

## Known Limitations of AI-Generated Suggestions

- The Gemini backend depends on an external API — quota, network, and transient `503` availability issues are outside this codebase's control
- OCR quality (legacy backend) still depends on input image quality and the selected PaddleOCR recognition model
- Bengali transliteration in the legacy backend is heuristic and not perfect for every proper noun; Gemini's translation is generally more natural but not independently verified against every possible NID layout
- AI-suggested fixes were verified against the real API and real Docker runs during this project, but broader edge-case coverage (unusual card variants, non-standard fonts) has not been exhaustively tested

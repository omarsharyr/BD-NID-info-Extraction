# AI Usage Documentation

This document describes how AI tools were used while building this project, the decisions that drove that usage, and how the resulting code was verified. The goal is an accurate record, not a minimal one.

## Tools Used

| Tool | Role |
|---|---|
| **GitHub Copilot** (GPT-5.4 mini) | Original scaffold: FastAPI structure, the legacy OCR/parser/translation pipeline, initial tests, Docker setup, and first-draft documentation. |
| **Claude (Anthropic)** | Executed a set of architecture and engineering decisions made during development: migrating extraction from OCR to a single Gemini multimodal call, diagnosing and fixing runtime issues found in live testing, building the landing-page UI, and rewriting the documentation set to match the final architecture. |

## Development Approach

AI tools were used as an implementation layer for decisions made during development, not as an autonomous source of architecture. The general pattern throughout the project was:

1. Identify a problem or requirement (e.g. OCR translation quality wasn't good enough; a `docker compose up` run returned an unexpected error).
2. Decide on the direction to take (e.g. replace OCR+regex+local-translation with a single vision-and-translation model call; keep the old pipeline available behind a config flag rather than deleting it).
3. Direct the AI tool to implement that specific decision.
4. Run the result against the real system not just the assistant's own reasoning and feed back what actually happened.
5. Review the generated code before accepting it.

That loop is the reason the project has a switchable `EXTRACTION_PROVIDER` setting, a specific nullable-field schema fix, and a pinned model alias none of those were the AI's first draft; they came out of directing it toward a problem observed in real testing and having it correct course.

## Representative Prompts

The prompts below are paraphrased for clarity but preserve the actual intent and content of what was asked.

| Goal | What was asked | Outcome |
|---|---|---|
| Replace the extraction pipeline | Directed a full migration from the OCR-based pipeline to a single Google Gemini multimodal call that reads and translates both card images in one pass, while keeping the original pipeline available as a fallback rather than deleting it. | `AIExtractionService` / `GeminiNIDExtractionService`, plus an `EXTRACTION_PROVIDER` config switch. |
| Debug against the live API | Reported the exact server error at each stage of testing against the real Gemini API — a Pydantic schema-validation failure, a `.env`-not-found error, a `403 PERMISSION_DENIED`, a `404` deprecated-model error, and a `503 UNAVAILABLE` — and asked for the underlying cause and fix for each, not just a workaround. | Corrected JSON schema syntax, a `docker-compose.yml` env-loading bug, and a model name pinned to a stable alias (see below). |
| Manage the API key correctly | Asked how to structure key management so a personal/paid Gemini API key could be used safely without ending up hardcoded or logged. | Confirmed `.env`-only key loading, `.gitignore` coverage, and no key in logs or the Docker image. |
| Extend the landing page | Specified four concrete additions to the landing page — a copyable `curl` example, an error-code reference table, a live `/health`/`/ready` status strip, and a request/response pipeline diagram — then, after reviewing the result, asked for it to be removed for being visually cluttered and asked for alternatives instead. | Initial version shipped, then rolled back based on direct review; page kept to three focused sections. |
| Redesign the landing page | Asked for a new visual direction described as rather than a generic template look. | A palette and layout grounded in the actual subject (Bangladesh NID cards) instead of a generic SaaS aesthetic, reviewed and approved before merging. |
| Prepare the submission repo | Directed the setup of `.gitignore`, environment variable handling, and a clean, logically-grouped commit history suitable for review. | `.gitignore` added, secrets confirmed untracked, history organized into scoped commits. |

## AI-Assisted Code Sections

| Area | Origin |
|---|---|
| FastAPI entrypoint and route wiring | Copilot scaffold; provider dependency-injection switch added on direction |
| Config, exception, and logging helpers | Copilot scaffold; Gemini-specific settings/exceptions added on direction |
| Legacy OCR pipeline (PaddleOCR/Tesseract), parser, local transliteration | Copilot scaffold; retained as the `EXTRACTION_PROVIDER=legacy` fallback by decision, not by default |
| `gemini_service.py` / `ai_extraction_service.py` | Implemented on direction to replace the OCR pipeline |
| Image validation/preprocessing | Copilot scaffold; reused as-is by the Gemini path since the validation requirements didn't change |
| Pydantic response models | Copilot scaffold |
| Unit/integration tests, incl. mocked-Gemini-SDK tests | Copilot for the legacy suite; extended on direction for the Gemini path |
| Docker, Compose, landing page, documentation | Copilot for the original scaffold; revised on direction for the Gemini migration and the fixes below |

## Review Process

Every generated or modified section was checked for:

- Syntax correctness (`python -m py_compile` on each changed file before packaging)
- An unchanged public response shape regardless of which backend produced it
- Every new failure mode mapping to a documented, meaningful error code
- No API key or full personal data reaching logs
- Actual behavior against the **live** Gemini API, not just mocks — the issues below were only caught this way

## Tests Used to Verify the Code

- `pytest` unit tests: Bengali digit conversion, date parsing, label matching, translation, response schema, and a mocked-SDK Gemini test covering success, partial extraction, malformed JSON, an empty response, and an API failure
- Endpoint-level integration tests for health, readiness, upload validation, and extraction under both a mocked legacy pipeline and a mocked Gemini service
- Manual end-to-end runs against the real Gemini API via `docker compose up --build` — this is what surfaced the issues below; the mocked tests alone did not

## Issues Found During Live Testing, and the Fixes

- **Schema validation failure.** The first Gemini response schema used JSON Schema's `"type": ["string", "null"]` union syntax. Google's SDK validates against its own OpenAPI-style `Schema` type, which rejected that. Fixed by using `"type": "string", "nullable": true`. Caught by a real `AI_EXTRACTION_FAILED` response during a live run, not by the mocked unit tests, since the mocks don't validate schema shape.
- **`docker-compose.yml` env-var precedence bug.** An earlier version wrote `${GEMINI_API_KEY:-}`, which let an empty host-shell variable silently overwrite a real key set in `.env`. Simplified to load `.env` directly via `env_file`.
- **Deprecated model name.** The initial default, `gemini-2.5-flash`, returned a `404` for newer API keys/projects. Switched the default to `gemini-flash-latest`, an alias Google keeps pointed at its current stable Flash model, specifically to avoid repeating this when models are renamed again.
- **Validation logic reused, not rewritten.** The corrupted/empty/wrong-type/too-small image checks were kept exactly as originally scaffolded; the Gemini path reuses them rather than duplicating logic, since the input-validation requirements didn't change with the new backend.
- **Provider made switchable, not replaced outright.** `EXTRACTION_PROVIDER=gemini|legacy` was added instead of deleting the OCR pipeline, so the original implementation stays available and testable rather than discarded.

## Security and Privacy Checks

- Uploaded images are not persisted by default
- `GEMINI_API_KEY` is read from environment variables only — never logged, never baked into the Docker image
- `.env` is gitignored; only `.env.example` (no real values) is committed
- API error payloads contain no stack traces or secrets
- **Note:** a real Gemini API key was pasted into an AI conversation more than once while debugging live issues during development. That key should be treated as compromised and rotated at https://aistudio.google.com/apikey — it must not be the key left in any submitted `.env` file.

## Known Limitations

- The Gemini backend depends on an external API; quota, network, and transient `503` availability are outside this codebase's control
- The legacy OCR backend's accuracy still depends on input image quality and the selected PaddleOCR recognition model
- The legacy backend's Bengali transliteration is heuristic and imperfect for some proper nouns; Gemini's translation is generally more natural but has not been independently verified against every possible NID layout
- Fixes above were verified against the real API and real Docker runs, but exhaustive edge-case coverage (unusual card variants, non-standard fonts) has not been performed

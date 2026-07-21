"""Single-pass AI extraction + translation for Bangladesh NID cards using Gemini.

This replaces the OCR -> regex parser -> local translation pipeline with one
multimodal call: Gemini reads both card images directly and returns the
already-translated (Bengali -> English) structured fields as JSON.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field

from pydantic import BaseModel, Field, ValidationError

from app.core.config import Settings
from app.core.exceptions import AIExtractionError, AIProviderNotConfiguredError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Raw schema Gemini is asked to fill in. Kept separate from the public API
# response model (app.models.responses.ExtractionData) because it carries
# extra diagnostic fields (readability flags, warnings) that help with
# graceful partial-extraction handling but are not part of the API contract.
# ---------------------------------------------------------------------------
class GeminiNIDPayload(BaseModel):
    name: str | None = None
    father_name: str | None = Field(default=None, alias="fatherName")
    mother_name: str | None = Field(default=None, alias="motherName")
    date_of_birth: str | None = Field(default=None, alias="dateOfBirth")
    nid_number: str | None = Field(default=None, alias="nidNumber")
    present_address: str | None = Field(default=None, alias="presentAddress")
    permanent_address: str | None = Field(default=None, alias="permanentAddress")
    front_readable: bool = Field(default=True, alias="frontReadable")
    back_readable: bool = Field(default=True, alias="backReadable")
    warnings: list[str] = Field(default_factory=list)

    model_config = {"populate_by_name": True}

    def has_any_field(self) -> bool:
        return any(
            [
                self.name,
                self.father_name,
                self.mother_name,
                self.date_of_birth,
                self.nid_number,
                self.present_address,
                self.permanent_address,
            ]
        )


RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "nullable": True, "description": "Card holder's full name, translated to English."},
        "fatherName": {"type": "string", "nullable": True, "description": "Father's name, translated to English."},
        "motherName": {"type": "string", "nullable": True, "description": "Mother's name, translated to English."},
        "dateOfBirth": {"type": "string", "nullable": True, "description": "Date of birth normalized to YYYY-MM-DD if possible."},
        "nidNumber": {"type": "string", "nullable": True, "description": "The NID number exactly as printed (digits only)."},
        "presentAddress": {"type": "string", "nullable": True, "description": "Present address, translated to natural English."},
        "permanentAddress": {"type": "string", "nullable": True, "description": "Permanent address, translated to natural English."},
        "frontReadable": {"type": "boolean", "description": "False if the front image was too damaged/blurred/wrong to read at all."},
        "backReadable": {"type": "boolean", "description": "False if the back image was too damaged/blurred/wrong to read at all."},
        "warnings": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Short notes about anything illegible, ambiguous, or missing.",
        },
    },
    "required": [
        "name",
        "fatherName",
        "motherName",
        "dateOfBirth",
        "nidNumber",
        "presentAddress",
        "permanentAddress",
        "frontReadable",
        "backReadable",
        "warnings",
    ],
}

SYSTEM_PROMPT = """\
You are an expert document analyst specialized in reading Bangladesh National ID (NID) cards.

You will be shown two images in order: (1) the FRONT of the NID card, (2) the BACK of the NID card.

Task:
1. Read all visible text on both images (English and Bengali).
2. Extract these fields: full name, father's name, mother's name, date of birth,
   NID number, present address, permanent address.
   - The NID number and address fields commonly appear on the back of the card;
     name/father/mother/date of birth commonly appear on the front. Use whichever
     side actually contains each field.
3. Translate any Bengali text you extracted for name, father's name, mother's name,
   present address, and permanent address into natural, fluent English.
   Preserve the real meaning and standard English spelling of Bangladeshi place
   names and personal names (e.g. transliterate names the way they are
   conventionally spelled in English) rather than doing a stiff literal or
   word-by-word translation.
4. The NID number and date of birth are never translated. Convert Bengali digits
   (০-৯) to standard Arabic digits (0-9). Normalize the date of birth to
   YYYY-MM-DD format when the day/month/year are unambiguous; otherwise return it
   as best you can read it.
5. If a field is not visible, not present, or illegible on either image, set it to
   null. Do not guess or invent values.
6. If an entire image is unreadable (e.g. blank, wrong document, too blurry/dark to
   read anything), set that side's "Readable" flag to false and briefly say why in
   "warnings".
7. Add a short entry to "warnings" for any field you had to leave null because it
   was illegible, ambiguous, or partially obscured.

Respond with ONLY a single JSON object matching the required schema. No extra
commentary, no markdown code fences.
"""


@dataclass(slots=True)
class GeminiNIDExtractionService:
    """Wraps the Google GenAI SDK for the NID extraction use case."""

    settings: Settings
    _client: object | None = field(default=None, init=False, repr=False)

    def is_available(self) -> bool:
        return bool(self.settings.gemini_api_key)

    def _get_client(self):
        if self._client is not None:
            return self._client
        if not self.settings.gemini_api_key:
            raise AIProviderNotConfiguredError()
        try:
            from google import genai
        except ImportError as exc:  # pragma: no cover - dependency guard
            raise AIExtractionError(
                "The google-genai package is not installed on the server."
            ) from exc
        self._client = genai.Client(api_key=self.settings.gemini_api_key)
        return self._client

    def extract(
        self,
        front_bytes: bytes,
        front_mime: str,
        back_bytes: bytes,
        back_mime: str,
    ) -> GeminiNIDPayload:
        """Send both images to Gemini in one request and return the parsed payload."""
        from google.genai import types as genai_types

        client = self._get_client()

        contents = [
            genai_types.Part.from_bytes(data=front_bytes, mime_type=front_mime),
            genai_types.Part.from_bytes(data=back_bytes, mime_type=back_mime),
            SYSTEM_PROMPT,
        ]
        config = genai_types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=RESPONSE_SCHEMA,
            temperature=0.0,
        )

        last_error: Exception | None = None
        attempts = max(1, self.settings.gemini_max_retries + 1)
        for attempt in range(1, attempts + 1):
            try:
                response = client.models.generate_content(
                    model=self.settings.gemini_model,
                    contents=contents,
                    config=config,
                )
                return self._parse_response(response)
            except AIExtractionError:
                raise
            except Exception as exc:  # auth/quota/network/timeout/etc.
                last_error = exc
                status = getattr(exc, "code", None) or getattr(exc, "status_code", None)
                logger.warning("gemini_request_error attempt=%s/%s status=%s error=%s", attempt, attempts, status, exc)
                # Don't retry on obvious auth/config/bad-request failures.
                if status in (400, 401, 403):
                    break
                if attempt < attempts:
                    time.sleep(min(2**attempt, 8))

        raise AIExtractionError(f"Gemini request failed after {attempts} attempt(s): {last_error}")

    @staticmethod
    def _parse_response(response) -> GeminiNIDPayload:
        raw_text = getattr(response, "text", None)
        if not raw_text:
            # Some SDK versions surface blocked/empty responses via candidates/prompt_feedback.
            feedback = getattr(response, "prompt_feedback", None)
            raise AIExtractionError(f"Gemini returned an empty response (feedback={feedback}).")

        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:]
            cleaned = cleaned.strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise AIExtractionError("Gemini returned malformed JSON.") from exc

        try:
            return GeminiNIDPayload.model_validate(data)
        except ValidationError as exc:
            raise AIExtractionError(f"Gemini response did not match the expected schema: {exc}") from exc

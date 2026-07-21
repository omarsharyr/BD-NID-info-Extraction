"""Translation and transliteration pipeline with a local fallback."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.constants.nid_labels import ADDRESS_TERMS, TRANSLITERATION_EXCEPTIONS
from app.core.config import Settings
from app.utils.bengali_digits import normalize_bengali_digits
from app.utils.text_normalizer import normalize_unicode_text

logger = logging.getLogger(__name__)


class TranslationService(ABC):
    @abstractmethod
    def translate_person_name(self, text: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def translate_address(self, text: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def is_available(self) -> bool:
        raise NotImplementedError


@dataclass(slots=True)
class LocalTranslationService(TranslationService):
    settings: Settings

    _CHAR_MAP = {
        "অ": "a",
        "আ": "a",
        "ই": "i",
        "ঈ": "i",
        "উ": "u",
        "ঊ": "u",
        "এ": "e",
        "ঐ": "oi",
        "ও": "o",
        "ঔ": "ou",
        "ক": "k",
        "খ": "kh",
        "গ": "g",
        "ঘ": "gh",
        "ঙ": "ng",
        "চ": "ch",
        "ছ": "chh",
        "জ": "j",
        "ঝ": "jh",
        "ঞ": "ny",
        "ট": "t",
        "ঠ": "th",
        "ড": "d",
        "ঢ": "dh",
        "ণ": "n",
        "ত": "t",
        "থ": "th",
        "দ": "d",
        "ধ": "dh",
        "ন": "n",
        "প": "p",
        "ফ": "ph",
        "ব": "b",
        "ভ": "bh",
        "ম": "m",
        "য": "y",
        "র": "r",
        "ল": "l",
        "শ": "sh",
        "ষ": "sh",
        "স": "s",
        "হ": "h",
        "য়": "y",
        "ড়": "r",
        "ঢ়": "rh",
        "ং": "ng",
        "ঃ": "h",
        "ঁ": "n",
        "া": "a",
        "ি": "i",
        "ী": "i",
        "ু": "u",
        "ূ": "u",
        "ৃ": "ri",
        "ে": "e",
        "ৈ": "oi",
        "ো": "o",
        "ৌ": "ou",
        "্": "",
    }

    def is_available(self) -> bool:
        return True

    def translate_person_name(self, text: str) -> str:
        normalized = normalize_unicode_text(text)
        if not normalized:
            return normalized
        translated = self._translate_phrase(normalized, keep_address_terms=False)
        return self._post_process_name(translated)

    def translate_address(self, text: str) -> str:
        normalized = normalize_unicode_text(text)
        if not normalized:
            return normalized
        translated = self._translate_phrase(normalized, keep_address_terms=True)
        translated = self._normalize_address_terms(translated)
        return self._post_process_address(translated)

    def _post_process_name(self, text: str) -> str:
        text = normalize_bengali_digits(text)
        text = text.replace("Md..", "Md.").replace("Md ,", "Md.")
        text = text.replace("  ", " ").strip(" ,.-")
        if text.lower().startswith("md "):
            text = "Md." + text[2:]
        return text

    def _post_process_address(self, text: str) -> str:
        text = normalize_bengali_digits(text)
        text = text.replace(" ,", ",").replace("  ", " ")
        return text.strip(" ,.-")

    def _translate_phrase(self, text: str, keep_address_terms: bool) -> str:
        words = self._tokenize(text)
        translated_words: list[str] = []
        for word in words:
            if not word:
                continue
            if word in TRANSLITERATION_EXCEPTIONS:
                translated_words.append(TRANSLITERATION_EXCEPTIONS[word])
                continue
            if keep_address_terms and word in ADDRESS_TERMS:
                translated_words.append(TRANSLITERATION_EXCEPTIONS.get(word, word))
                continue
            if self._contains_bengali(word):
                translated_words.append(self._romanize(word))
            else:
                translated_words.append(word)
        return self._normalize_spacing(" ".join(translated_words))

    def _normalize_address_terms(self, text: str) -> str:
        for bengali, english in TRANSLITERATION_EXCEPTIONS.items():
            if bengali in ADDRESS_TERMS:
                text = text.replace(bengali, english)
        return self._normalize_spacing(text)

    def _tokenize(self, text: str) -> list[str]:
        return text.replace(",", " , ").replace("/", " / ").split()

    def _contains_bengali(self, text: str) -> bool:
        return any("\u0980" <= character <= "\u09ff" for character in text)

    def _normalize_spacing(self, text: str) -> str:
        return " ".join(text.split())

    def _romanize(self, word: str) -> str:
        if word in TRANSLITERATION_EXCEPTIONS:
            return TRANSLITERATION_EXCEPTIONS[word]
        if not self._contains_bengali(word):
            return word
        pieces: list[str] = []
        characters = list(word)
        index = 0
        while index < len(characters):
            pair = "".join(characters[index : index + 2])
            if pair in {"ক্র", "গ্র", "প্র", "ত্র", "দ্ব", "শ্র"}:
                pieces.append(
                    {
                        "ক্র": "kr",
                        "গ্র": "gr",
                        "প্র": "pr",
                        "ত্র": "tr",
                        "দ্ব": "dw",
                        "শ্র": "shr",
                    }[pair]
                )
                index += 2
                continue
            character = characters[index]
            pieces.append(self._CHAR_MAP.get(character, ""))
            index += 1
        romanized = self._normalize_spacing("".join(pieces))
        return romanized.title() if romanized else word


@dataclass(slots=True)
class ExternalTranslationService(TranslationService):
    settings: Settings

    def is_available(self) -> bool:
        return bool(self.settings.translation_provider and self.settings.translation_api_url)

    def translate_person_name(self, text: str) -> str:
        return text

    def translate_address(self, text: str) -> str:
        return text


def build_translation_service(settings: Settings) -> TranslationService:
    if settings.translation_provider.lower() == "cloud" and settings.translation_api_url:
        logger.info("Using external translation service configured by environment")
        return ExternalTranslationService(settings)
    return LocalTranslationService(settings)

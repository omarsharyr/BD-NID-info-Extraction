from app.core.config import Settings
from app.services.translation_service import LocalTranslationService


def test_translate_person_name_examples() -> None:
    service = LocalTranslationService(Settings())
    assert service.translate_person_name("মোঃ রহিম") == "Md. Rahim"
    assert service.translate_person_name("আব্দুল করিম") == "Abdul Karim"


def test_translate_address_examples() -> None:
    service = LocalTranslationService(Settings())
    translated = service.translate_address("ঢাকা, বাংলাদেশ")
    assert "Dhaka" in translated
    assert "Bangladesh" in translated

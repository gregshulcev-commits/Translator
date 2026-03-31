from pdf_word_translator.utils.text_normalizer import EnglishWordNormalizer


def test_normalize_strips_punctuation_and_lowercases() -> None:
    assert EnglishWordNormalizer.normalize('"Systems,"') == 'systems'
    assert EnglishWordNormalizer.normalize("Driver's") == "driver's"


def test_candidate_forms_include_useful_fallbacks() -> None:
    candidates = EnglishWordNormalizer.candidate_forms("Configured")
    assert candidates[0] == "configured"
    assert "configure" in candidates
    assert EnglishWordNormalizer.candidate_forms("systems") == ["systems", "system"]

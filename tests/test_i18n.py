"""The frontend fetches exactly one dictionary and has no runtime fallback,
so the three language files must stay in lockstep."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
I18N_DIR = ROOT / "static" / "i18n"
LANGUAGES = ("zh", "ja", "en")


def load(language: str) -> dict[str, str]:
    return json.loads((I18N_DIR / f"{language}.json").read_text(encoding="utf-8"))


def test_every_supported_language_has_a_file():
    assert {path.stem for path in I18N_DIR.glob("*.json")} == set(LANGUAGES)


@pytest.mark.parametrize("language", [lang for lang in LANGUAGES if lang != "zh"])
def test_key_sets_match_the_reference_language(language):
    reference = set(load("zh"))
    candidate = set(load(language))
    assert not reference - candidate, f"{language}.json is missing: {sorted(reference - candidate)}"
    assert not candidate - reference, f"{language}.json has extra keys: {sorted(candidate - reference)}"


@pytest.mark.parametrize("language", LANGUAGES)
def test_no_blank_translations(language):
    blank = [key for key, value in load(language).items() if not value.strip()]
    assert not blank, f"{language}.json has empty values: {blank}"


@pytest.mark.parametrize("language", [lang for lang in LANGUAGES if lang != "zh"])
def test_placeholders_match_the_reference_language(language):
    """A dropped {count} or {amount} would render a literal brace to the user."""
    reference = load("zh")
    candidate = load(language)
    for key, template in reference.items():
        expected = set(re.findall(r"\{(\w+)\}", template))
        actual = set(re.findall(r"\{(\w+)\}", candidate[key]))
        assert expected == actual, f"{language}.json['{key}'] placeholders {actual} != {expected}"


def test_keys_referenced_by_templates_and_scripts_exist():
    """Catches a data-i18n attribute or t() call pointing at a removed key."""
    reference = set(load("zh"))
    used: set[str] = set()

    for path in (ROOT / "templates").glob("*.html"):
        markup = path.read_text(encoding="utf-8")
        used.update(re.findall(r'data-i18n(?:-placeholder|-aria-label)?="([^"]+)"', markup))

    for path in (ROOT / "static" / "js").glob("*.js"):
        source = path.read_text(encoding="utf-8")
        used.update(re.findall(r"""\bt\(\s*["']([a-zA-Z][\w.]*)["']""", source))

    missing = sorted(used - reference)
    assert not missing, f"referenced but undefined translation keys: {missing}"

"""Tests for the optional pyqt6-linguistic-tools bridge.

The toolkit is a git submodule, so these tests check the bridge itself and the
locale selection rules with a fake service; they never download dictionaries.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from ksnip_py import linguistics
from ksnip_py.spellcheck import SpellChecker


class _FakeCapabilities:
    def __init__(self, spell_check: bool, thesaurus: bool = False) -> None:
        self.spell_check = spell_check
        self.thesaurus = thesaurus


class _FakeService:
    """Minimal stand-in for ``LinguisticService``."""

    def __init__(self, available: tuple[str, ...], spelling: tuple[str, ...]) -> None:
        self._available = available
        self._spelling = spelling
        self.language = available[0] if available else ""

    def available_languages(self) -> tuple[str, ...]:
        return self._available

    def capabilities(self, locale: str | None = None) -> _FakeCapabilities:
        return _FakeCapabilities(locale in self._spelling)


class ToolkitLocationTest(unittest.TestCase):
    def test_toolkit_lives_under_the_repository_root(self):
        expected = (
            linguistics.repository_root()
            / "libs"
            / linguistics.TOOLKIT_DIRECTORY_NAME
        )
        self.assertEqual(linguistics.toolkit_directory(), expected)

    def test_missing_toolkit_reports_why_it_is_unavailable(self):
        original = linguistics.toolkit_directory
        try:
            linguistics.toolkit_directory = lambda: Path("missing-toolkit-directory")
            linguistics.reset_toolkit_cache()
            self.assertFalse(linguistics.ensure_toolkit_importable())
            self.assertFalse(linguistics.toolkit_available())
            self.assertIn("not found", linguistics.toolkit_error() or "")
            self.assertIsNone(linguistics.shared_service())
        finally:
            linguistics.toolkit_directory = original
            linguistics.reset_toolkit_cache()


class LocaleSelectionTest(unittest.TestCase):
    def setUp(self) -> None:
        self._original_system_languages = linguistics._system_languages
        linguistics._system_languages = lambda: ["es_EC"]

    def tearDown(self) -> None:
        linguistics._system_languages = self._original_system_languages
        linguistics.reset_toolkit_cache()

    def test_exact_regional_match_wins(self):
        service = _FakeService(("es_EC", "es_ES"), ("es_EC", "es_ES"))
        self.assertEqual(
            linguistics.resolve_spellcheck_locale(service, ("es",)),
            "es_EC",
        )

    def test_same_language_variant_is_used_when_the_exact_one_is_absent(self):
        service = _FakeService(("es_ES", "es_MX"), ("es_ES", "es_MX"))
        self.assertEqual(
            linguistics.resolve_spellcheck_locale(service, ("es_AR",)),
            "es_ES",
        )

    def test_a_thesaurus_only_bundle_never_shadows_spelling(self):
        # "es" holds only the thesaurus; the spelling dictionary is es_ES.
        service = _FakeService(("es", "es_ES"), ("es_ES",))
        self.assertEqual(
            linguistics.resolve_spellcheck_locale(service, ("es",)),
            "es_ES",
        )

    def test_no_dictionaries_means_no_locale(self):
        service = _FakeService((), ())
        self.assertIsNone(linguistics.resolve_spellcheck_locale(service, ("es_EC",)))

    def test_installed_dictionary_is_used_when_the_language_does_not_match(self):
        service = _FakeService(("es_ES",), ("es_ES",))
        self.assertEqual(
            linguistics.resolve_spellcheck_locale(service, ("en_US",)),
            "es_ES",
        )


class SpellCheckerTest(unittest.TestCase):
    def test_backend_is_one_of_the_supported_values(self):
        checker = SpellChecker()
        self.assertIn(checker.backend_name(), {"toolkit", "hunspell", "none"})

    def test_every_requested_word_gets_a_result(self):
        checker = SpellChecker()
        results = checker.check_words(["canción", "hoola", ""])
        self.assertEqual(set(results), {"canción", "hoola", ""})
        # Without a backend, words are never reported as misspelled, which keeps
        # the annotator quiet instead of underlining everything.
        if checker.backend_name() == "none":
            self.assertTrue(all(result.correct for result in results.values()))


if __name__ == "__main__":
    unittest.main()

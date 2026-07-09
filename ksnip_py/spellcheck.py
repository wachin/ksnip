from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import dataclass

from PyQt6.QtCore import QSettings, Qt
from PyQt6.QtGui import QAction, QColor, QSyntaxHighlighter, QTextCharFormat, QTextCursor
from PyQt6.QtWidgets import QMenu, QPlainTextEdit


WORD_RE = re.compile(r"[^\W\d_]+(?:['’\-][^\W\d_]+)*", re.UNICODE)
SPELLCHECK_SCHEME_KEY = "spellcheck/misspelled_word_scheme"

DEFAULT_SPELLCHECK_SCHEME: list[tuple[str, str, str]] = [
    ("Black", "#000000", "#ffffff"),
    ("White", "#ffffff", "#000000"),
    ("Red", "#df5a17", "#ffffff"),
    ("Orange", "#f08c00", "#002b36"),
    ("Yellow", "#ffd43b", "#000000"),
    ("Green", "#2b8a3e", "#ffffff"),
    ("Cyan", "#15aabf", "#000000"),
    ("Blue", "#1971c2", "#ffffff"),
    ("Purple", "#6741d9", "#ffffff"),
    ("Magenta", "#c2255c", "#ffffff"),
    ("Brown", "#8d6e63", "#ffffff"),
    ("Gray", "#868e96", "#000000"),
]


@dataclass(frozen=True)
class SpellResult:
    correct: bool
    suggestions: tuple[str, ...] = ()


def default_spellcheck_scheme() -> list[tuple[str, QColor, QColor]]:
    return [(name, QColor(fill), QColor(underline)) for name, fill, underline in DEFAULT_SPELLCHECK_SCHEME]


def load_spellcheck_scheme(settings: QSettings | None = None) -> list[tuple[str, QColor, QColor]]:
    resolved_settings = settings or QSettings()
    payload = resolved_settings.value(SPELLCHECK_SCHEME_KEY, "")
    if isinstance(payload, str) and payload.strip():
        try:
            parsed = json.loads(payload)
            rows: list[tuple[str, QColor, QColor]] = []
            for entry in parsed:
                name = str(entry.get("name", "")).strip()
                fill = QColor(str(entry.get("fill", "")))
                underline = QColor(str(entry.get("underline", "")))
                if name and fill.isValid() and underline.isValid():
                    rows.append((name, fill, underline))
            if rows:
                return rows
        except (TypeError, ValueError, json.JSONDecodeError):
            pass
    return default_spellcheck_scheme()


def save_spellcheck_scheme(rows: list[tuple[str, QColor, QColor]], settings: QSettings | None = None) -> None:
    resolved_settings = settings or QSettings()
    payload = [
        {
            "name": name,
            "fill": fill.name(QColor.NameFormat.HexRgb),
            "underline": underline.name(QColor.NameFormat.HexRgb),
        }
        for name, fill, underline in rows
    ]
    resolved_settings.setValue(SPELLCHECK_SCHEME_KEY, json.dumps(payload))


class HunspellSpellChecker:
    def __init__(self) -> None:
        self._hunspell = shutil.which("hunspell")
        self._dictionary_names = self._preferred_dictionaries()
        self._cache: dict[str, SpellResult] = {}

    def is_available(self) -> bool:
        return bool(self._hunspell and self._dictionary_names)

    def result_for_word(self, word: str) -> SpellResult:
        normalized = word.strip()
        if not normalized:
            return SpellResult(True, ())
        cached = self._cache.get(normalized)
        if cached is not None:
            return cached
        if not self.is_available():
            result = SpellResult(True, ())
            self._cache[normalized] = result
            return result
        results = self._query_words([normalized])
        return results.get(normalized, SpellResult(True, ()))

    def check_words(self, words: list[str]) -> dict[str, SpellResult]:
        pending = [word for word in dict.fromkeys(words) if word and word not in self._cache]
        if pending and self.is_available():
            self._query_words(pending)
        return {word: self._cache.get(word, SpellResult(True, ())) for word in words}

    def _preferred_dictionaries(self) -> tuple[str, ...]:
        if not self._hunspell:
            return ()
        try:
            result = subprocess.run(
                [self._hunspell, "-D"],
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
        except (OSError, subprocess.SubprocessError):
            return ()
        dictionaries: list[str] = []
        output = "\n".join(part for part in (result.stdout, result.stderr) if part)
        for line in output.splitlines():
            entry = line.strip()
            if not entry or entry.startswith("SEARCH PATH") or entry.startswith("AVAILABLE DICTIONARIES") or entry.startswith("LOADED DICTIONARY"):
                continue
            if "/" in entry:
                dictionaries.append(entry.rsplit("/", 1)[-1])
        if not dictionaries:
            return ()
        spanish = "es_MX" if "es_MX" in dictionaries else "es_ES" if "es_ES" in dictionaries else next((name for name in dictionaries if name.startswith("es_")), None)
        english = "en_US" if "en_US" in dictionaries else "en_GB" if "en_GB" in dictionaries else next((name for name in dictionaries if name.startswith("en_")), None)
        ordered = [name for name in (spanish, english) if name]
        return tuple(ordered)

    def _query_words(self, words: list[str]) -> dict[str, SpellResult]:
        if not self._hunspell or not self._dictionary_names:
            return {}
        try:
            result = subprocess.run(
                [self._hunspell, "-d", ",".join(self._dictionary_names), "-a"],
                input="".join(f"{word}\n" for word in words),
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
        except (OSError, subprocess.SubprocessError):
            fallback = {word: SpellResult(True, ()) for word in words}
            self._cache.update(fallback)
            return fallback

        parsed: dict[str, SpellResult] = {}
        lines = [line.rstrip() for line in result.stdout.splitlines()]
        payload_lines = [line for line in lines[1:] if line]
        for word, line in zip(words, payload_lines):
            parsed[word] = self._parse_result_line(line)
        for word in words[len(parsed):]:
            parsed[word] = SpellResult(True, ())
        self._cache.update(parsed)
        return parsed

    @staticmethod
    def _parse_result_line(line: str) -> SpellResult:
        if not line:
            return SpellResult(True, ())
        if line[0] in {"*", "+", "-"}:
            return SpellResult(True, ())
        if line[0] in {"&", "#"}:
            if ":" not in line:
                return SpellResult(False, ())
            _, suggestions = line.split(":", 1)
            cleaned = tuple(part.strip() for part in suggestions.split(",") if part.strip())
            return SpellResult(False, cleaned)
        return SpellResult(True, ())


class SpellCheckHighlighter(QSyntaxHighlighter):
    def __init__(self, document, checker: HunspellSpellChecker) -> None:
        super().__init__(document)
        self._checker = checker
        self._misspelled_format = QTextCharFormat()
        self._misspelled_format.setUnderlineColor(QColor("#0b7285"))
        self._misspelled_format.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SpellCheckUnderline)

    def set_error_color(self, color: QColor) -> None:
        self._misspelled_format.setUnderlineColor(QColor(color))
        self.rehighlight()

    def highlightBlock(self, text: str) -> None:  # noqa: N802
        matches = list(WORD_RE.finditer(text))
        if not matches:
            return
        results = self._checker.check_words([match.group(0) for match in matches])
        for match in matches:
            word = match.group(0)
            if not results.get(word, SpellResult(True, ())).correct:
                self.setFormat(match.start(), match.end() - match.start(), self._misspelled_format)


class SpellCheckTextEdit(QPlainTextEdit):
    def __init__(self, parent=None, *, checker: HunspellSpellChecker | None = None) -> None:
        super().__init__(parent)
        self._spell_checker = checker or HunspellSpellChecker()
        self._spell_highlighter = SpellCheckHighlighter(self.document(), self._spell_checker)
        self._spellcheck_scheme = load_spellcheck_scheme()

    @staticmethod
    def _complementary_color(color: QColor) -> QColor:
        if not color.isValid():
            return QColor("#0b7285")
        hue = color.hue()
        if hue < 0:
            return QColor("#0b7285" if color.lightness() > 127 else "#ffd43b")
        complementary = QColor()
        complementary.setHsl((hue + 180) % 360, max(160, color.saturation()), max(80, min(200, color.lightness())))
        complementary.setAlpha(255)
        return complementary

    def set_spellcheck_color_scheme(self, rows: list[tuple[str, QColor, QColor]]) -> None:
        self._spellcheck_scheme = [(name, QColor(fill), QColor(underline)) for name, fill, underline in rows]

    def _resolve_underline_color(self, color: QColor) -> QColor:
        if not color.isValid():
            return QColor("#0b7285")
        best_distance: float | None = None
        best_color: QColor | None = None
        for _name, fill, underline in self._spellcheck_scheme:
            distance = (
                (fill.red() - color.red()) ** 2
                + (fill.green() - color.green()) ** 2
                + (fill.blue() - color.blue()) ** 2
            )
            if best_distance is None or distance < best_distance:
                best_distance = distance
                best_color = underline
        return QColor(best_color) if best_color is not None else self._complementary_color(color)

    def set_spellcheck_reference_color(self, color: QColor) -> None:
        self._spell_highlighter.set_error_color(self._resolve_underline_color(color))

    def contextMenuEvent(self, event) -> None:  # noqa: N802
        menu = self.createStandardContextMenu()
        cursor = self.cursorForPosition(event.pos())
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        word = cursor.selectedText().strip()
        if word:
            result = self._spell_checker.result_for_word(word)
            if not result.correct:
                suggestions = result.suggestions[:8]
                insert_before = menu.actions()[0] if menu.actions() else None
                if suggestions:
                    start = cursor.selectionStart()
                    end = cursor.selectionEnd()
                    for suggestion in reversed(suggestions):
                        action = QAction(suggestion, menu)
                        action.triggered.connect(
                            lambda checked=False, replacement=suggestion, start_pos=start, end_pos=end: self._replace_range(start_pos, end_pos, replacement)
                        )
                        if insert_before is None:
                            menu.addAction(action)
                        else:
                            menu.insertAction(insert_before, action)
                else:
                    action = QAction("No suggestions", menu)
                    action.setEnabled(False)
                    if insert_before is None:
                        menu.addAction(action)
                    else:
                        menu.insertAction(insert_before, action)
                if insert_before is None:
                    menu.addSeparator()
                else:
                    menu.insertSeparator(insert_before)
        menu.exec(event.globalPos())

    def _replace_word(self, cursor: QTextCursor, replacement: str) -> None:
        cursor.beginEditBlock()
        cursor.removeSelectedText()
        cursor.insertText(replacement)
        cursor.endEditBlock()
        self.setTextCursor(cursor)

    def _replace_range(self, start: int, end: int, replacement: str) -> None:
        cursor = self.textCursor()
        cursor.setPosition(start)
        cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
        self._replace_word(cursor, replacement)
        self.setFocus(Qt.FocusReason.OtherFocusReason)

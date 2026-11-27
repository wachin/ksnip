# Spell checking

ksnip-pyqt6 underlines misspelled words while you edit a **text annotation**,
offers up to eight suggestions in the right-click menu, and draws the underline
with a colour that stays readable on any fill or background colour.

Spell checking never runs on OCR output, file names, or the rest of the interface.

## Two backends

| Backend | When it is used | Where words come from |
| --- | --- | --- |
| Bundled toolkit (`pyqt6-linguistic-tools`) | **Windows only**, and only when the `libs/pyqt6-linguistic-tools` submodule is present | Pure-Python Spylls engine reading the dictionaries downloaded from the Dictionary Download Manager |
| System `hunspell` program | Every other platform, including Linux with the toolkit present | `hunspell -a`, using the dictionaries the distribution installed |

The split is deliberate: Windows has no Hunspell to install, so the toolkit and
its downloaded dictionaries are the only way to get spell checking there. Linux
distributions already package hunspell and its dictionaries, so ksnip always
uses that backend on Linux even when the submodule is present; this keeps the
behaviour identical to a distribution package and avoids a second dictionary
store. macOS uses the same fallback.

`ksnip_py/linguistics.py` owns the choice; `ksnip_py/spellcheck.py` exposes it as
one checker behind the existing editor widget. A missing backend is silent: no
underlines appear and no word is ever reported as wrong.

## Downloading dictionaries

The dictionary manager exists because Windows has no dictionary packages.

**Options → Dictionary Download Manager…** opens the toolkit's manager:

- searchable catalog of the LibreOffice dictionary corpus (57 entries);
- spelling and thesaurus badges per language;
- HTTPS download with a SHA-256 check and deep validation before publication;
- manual import of an `.aff`/`.dic` pair, and removal of bundles the
  application owns;
- personal-dictionary backup and restore.

Dictionaries are published in a per-user directory:

| Platform | Location |
| --- | --- |
| Windows | `%LOCALAPPDATA%\ksnip-pyqt6\dictionaries\{managed,user,personal}` |
| Linux | `${XDG_DATA_HOME:-~/.local/share}/ksnip-pyqt6/dictionaries/{managed,user,personal}` |
| macOS | `~/Library/Application Support/ksnip-pyqt6/dictionaries/{managed,user,personal}` |

A dictionary installed from the manager becomes active when the dialog closes:
ksnip-pyqt6 rebuilds the linguistic service and repaints open text editors, so
no restart is needed.

The action is disabled on Linux and macOS, and on Windows without the submodule,
with a tooltip explaining which case applies.

## Language selection

This only applies to the Windows toolkit backend; `hunspell` uses the dictionary
names it reports, preferring the application and system languages.

The checker uses the first installed locale that has spelling, in this order:

1. the application language (`application/language`), exactly;
2. the system locale from Qt (`QLocale.system().name()`), exactly;
3. another regional variant of the same language, for example `es_EC` asked,
   `es_ES` installed;
4. any installed locale that provides spelling.

A thesaurus-only bundle never shadows a spelling dictionary. When nothing
installed matches, the checker stays silent instead of underlining every word.

## Limitations

- The colour scheme of misspelled words is configured in
  **Settings → Annotator → Color scheme for misspelled words**; the underline
  adapts to the text background for contrast.
- Suggestions come from the dictionary; there is no learning or ignore-word menu
  yet.
- Personal words and ignored words exist in the toolkit API but are not yet
  exposed in the annotation editor.
- Spell checking follows one locale at a time; text that mixes two languages is
  checked against the selected one.

## For packagers

The toolkit is optional, and on Linux it is never used:

- **Windows source checkout / development:** the submodule provides the backend
  and the Dictionary Download Manager.
- **`.deb`, wheel, PyInstaller:** if `libs/pyqt6-linguistic-tools` is not shipped,
  the bridge reports the toolkit as unavailable and the editor uses the system
  `hunspell` program. The menu action disables itself. A Debian package can
  drop `libs/` entirely and still keep spell checking, because the platform
  check disables the toolkit on Linux before any import is attempted.
- Shipping it requires the submodule *and* its nested engine submodules
  (`libs/spylls` MPL-2.0, `libs/pythes` MIT).

Update the vendored copy with:

```bash
git submodule update --init --recursive
git -C libs/pyqt6-linguistic-tools pull
```

Adding it to a new checkout:

```bash
git submodule add https://github.com/wachin/pyqt6-linguistic-tools.git \
  libs/pyqt6-linguistic-tools
git submodule update --init --recursive
```

## Tests

`tests_py/test_linguistics.py` covers the bridge: submodule location, the
unavailable path, and the locale-selection rules with a fake service. The tests
never download dictionaries, so they pass on a machine without them.

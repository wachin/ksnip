# Translation audit

Date: 2026-11-25

## Scope

The audit covered the 41 application catalogs in
`ksnip_py/translations/ksnip_py_<locale>.ts` and their compiled
`ksnip_py_<locale>.qm` files.

It checked:

- XML validity and matching `.qm` presence;
- message counts;
- empty and unfinished translations;
- source-string differences between catalogs;
- source strings recently extracted from the Python code with `pylupdate6`.

This is a structural audit. It does not prove that every translated sentence is
semantically correct; native speakers should review the affected catalogs in
Qt Linguist.

## Results

- 41 `.ts` catalogs and 41 non-empty `.qm` catalogs exist.
- Structural validation passes for all catalogs.
- Spanish and the 30 previously incomplete locales now contain 569
  messages with no unfinished entries:
  Arabic, Bulgarian, Bengali (Bangladesh), Catalan, Czech, Danish, German,
  Greek, Estonian, Finnish, French (Canada), French, Croatian, Hungarian,
  Indonesian, Italian, Japanese, Korean, Dutch, Norwegian, Polish, Portuguese
  (Brazil), Portuguese, Romanian, Russian, Swedish, Turkish, Ukrainian,
  Simplified Chinese, and Traditional Chinese.
- The two missing MainWindow strings were added to those catalogs:

  ```text
  Model Manager
  The OCR plugin failed to open: %1
  ```

- The remaining gaps are in the ten catalogs that already had larger missing
  sections. They still have 567 messages and need native-speaker review:

  | Locale | Unfinished messages |
  | --- | ---: |
  | Central Kurdish (`ckb`) | 142 |
  | Basque (`eu`) | 357 |
  | Persian (`fa`) | 548 |
  | Galician (`gl`) | 438 |
  | Hebrew (`he`) | 537 |
  | Georgian (`ka`) | 477 |
  | Sinhala (`si`) | 456 |
  | Slovenian (`sl`) | 540 |
  | Albanian (`sq`) | 454 |
  | Tamil (`ta`) | 336 |

## Tools used

```bash
sudo apt install linguist-qt6 qt6-l10n-tools pyqt6-dev-tools
```

- `linguist6` reviews and edits a `.ts`.
- `lrelease` compiles a `.ts` into a `.qm`.
- `pylupdate6` extracts current source strings.

## Review workflow

```bash
linguist6 ksnip_py/translations/ksnip_py_es.ts
lrelease ksnip_py/translations/ksnip_py_es.ts \
  -qm ksnip_py/translations/ksnip_py_es.qm
```

When Python source strings change, run:

```bash
python3 tools/update_pyqt_translations.py
```

Then review the new unfinished entries in Qt Linguist. Do not translate model
names, product names, or placeholders such as `%1`.

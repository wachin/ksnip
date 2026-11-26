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
- All 41 catalogs now contain 569 messages with no unfinished entries.
- The two MainWindow strings are present in every catalog:

  ```text
  Model Manager
  The OCR plugin failed to open: %1
  ```

- Structural validation passes for all catalogs. Native speakers should still
  review the wording and terminology of the less common languages; the audit
  proves completeness, not linguistic perfection.

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

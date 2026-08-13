# Artwork sources

This directory contains source artwork and contact sheets used to generate
application assets. It is kept outside `ksnip_py` intentionally, so these
working files are not installed as part of the Python package.

Generated, optimized assets that the application uses belong under
`ksnip_py/stickers/`.

## TuxBaby

`TuxBaby/TuxBaby.png` is the original ChatGPT-generated contact sheet from
which the individual TuxBaby stickers were prepared. The 33 optimized,
transparent application assets are stored in
`ksnip_py/stickers/themes/tuxbaby/`.

Both the source sheet and the resulting TuxBaby stickers are covered by the
copyright, generation disclosure, attribution, and CC BY-SA 4.0 terms in
`ksnip_py/licenses/TUXBABY_LICENSE.md`.

## Konqi and Katie

The contact sheet is stored at `konqi-katie/Konqi-and-Katie.png`. Regenerate
its individual stickers from the repository root with:

```sh
python3 tools/extract_konqi_katie_stickers.py \
  artwork-sources/konqi-katie/Konqi-and-Katie.png \
  'ksnip_py/stickers/themes/konqi&katie'
```

The source sheet and all extracted stickers are licensed under CC BY-SA 4.0.
Copyright, generation disclosure, KDE mascot acknowledgement, and attribution
details are recorded in `ksnip_py/licenses/KONQI_KATIE_LICENSE.md`.

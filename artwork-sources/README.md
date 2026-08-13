# Artwork sources

This directory contains source artwork and contact sheets used to generate
application assets. It is kept outside `ksnip_py` intentionally, so these
working files are not installed as part of the Python package.

Generated, optimized assets that the application uses belong under
`ksnip_py/stickers/`.

## Konqi and Katie

The contact sheet is stored at `konqi-katie/Konqi-and-Katie.png`. Regenerate
its individual stickers from the repository root with:

```sh
python3 tools/extract_konqi_katie_stickers.py \
  artwork-sources/konqi-katie/Konqi-and-Katie.png \
  'ksnip_py/stickers/themes/konqi&katie'
```

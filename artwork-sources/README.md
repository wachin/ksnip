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

## Geeko

`Geeko/Geeko.png` is the original ChatGPT-generated contact sheet from which
the individual Geeko stickers were prepared. The 73 optimized, transparent
application assets are stored in `ksnip_py/stickers/themes/geeko/` and can be
regenerated from the repository root with:

```sh
python3 tools/extract_geeko_stickers.py \
  artwork-sources/Geeko/Geeko.png \
  ksnip_py/stickers/themes/geeko
```

The source sheet and extracted stickers are unofficial fan artwork licensed
under CC BY-SA 4.0. Copyright, generation disclosure, Geeko acknowledgement,
and trademark information are recorded in
`ksnip_py/licenses/GEEKO_LICENSE.md`.

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

## GNU Baby

`GNUBaby/gnubaby.png` is the original ChatGPT-generated contact sheet. Its
first 41 characters were extracted from the sheet; the 16 crowded utility
designs were regenerated individually and retained in
`GNUBaby/generated-utilities/` so that their source artwork remains
inspectable. The 57 optimized, transparent application assets are stored in
`ksnip_py/stickers/themes/gnubaby/`.

The contact-sheet extraction can be repeated from the repository root with:

```sh
python3 tools/extract_gnubaby_stickers.py \
  artwork-sources/GNUBaby/gnubaby.png \
  ksnip_py/stickers/themes/gnubaby
```

Existing regenerated utility stickers are preserved by the extractor. The
source images and packaged collection are unofficial fan artwork distributed
under CC BY-SA 2.0. Copyright, generation disclosure, GNU Head attribution,
and trademark information are recorded in
`ksnip_py/licenses/GNUBABY_LICENSE.md`.

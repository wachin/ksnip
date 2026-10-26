# Illustrator-style item grabbing

## Summary

When a creation tool (sticker, rectangle, ellipse, arrow, line, text, blur,
pixelate, marker, number, duplicate, etc.) is active, clicking on an already
placed and currently-selected annotation item now **grabs** that item so it can
be moved or resized, instead of creating a brand-new item at that point. Clicking
on empty canvas still creates a new item, and the tool stays active after drawing
— the same way Adobe Illustrator behaves.

This was added so users do not have to switch to the Select (S) tool just to
reposition something they just drew.

## How it works

- A click with a creation tool active first checks whether it lands on a selected
  item.
  - If it does, the item is (re)selected and a move/resize drag is armed; dragging
    the mouse moves or resizes it and releasing commits the change (with undo
    support).
  - If it does not (empty space, or an unselected item), the normal creation path
    runs and a new item is created at the click point.
- After a shape is created it is automatically selected (`select_item_after_drawing`,
  on by default) but the creation tool remains active (`switch_to_select_after_drawing`,
  off by default), so you can keep drawing and still grab what you just placed.

## Setting

- Location: **Settings > Annotator**
- Checkbox: "Grab selected item when clicking it (Illustrator-style)"
- Default: **on**

When disabled, a click with a creation tool always creates a new item (the
previous behavior), even if it lands on a selected item.

## Notes

- This applies to every creation tool, not just stickers.
- For languages other than English/Spanish the label currently falls back to the
  English source string until a translation is provided (see `translations/`).

## Translations

The setting label is:

> Grab selected item when clicking it (Illustrator-style)

Translations per catalog (generated for this feature; review by native speakers):

| Language | Catalog | Translation |
|----------|---------|-------------|
| Spanish | ksnip_py_es | Capturar el elemento seleccionado al hacer clic en él (estilo Illustrator) |
| Arabic | ksnip_py_ar | التقاط العنصر المحدد عند النقر عليه (بأسلوب Illustrator) |
| Bulgarian | ksnip_py_bg | Хващане на избрания елемент при щракване върху него (в стил Illustrator) |
| Bengali | ksnip_py_bn_BD | নির্বাচিত আইটেমটি ক্লিক করার সময় তুলে নিন (Illustrator-শৈলী) |
| Catalan | ksnip_py_ca | Captura l'element seleccionat en fer-hi clic (estil Illustrator) |
| Central Kurdish | ksnip_py_ckb | گرتنی ئایتمی دیاریکراو کاتێک دەست دەکەیت پێی (بە سبکی Illustrator) |
| Czech | ksnip_py_cs | Uchopit vybranou položku při kliknutí na ni (ve stylu Illustratoru) |
| Danish | ksnip_py_da | Grib det valgte element ved klik på det (Illustrator-stil) |
| German | ksnip_py_de | Ausgewähltes Element beim Klicken greifen (Illustrator-Stil) |
| Greek | ksnip_py_el | Λήψη του επιλεγμένου στοιχείου κατά το κλικ πάνω του (στυλ Illustrator) |
| Estonian | ksnip_py_et | Valitud elemendi haaramine sellel klikkimisel (Illustratori stiilis) |
| Basque | ksnip_py_eu | Hartu hautatutako elementua hari klik egitean (Illustrator estiloa) |
| Persian | ksnip_py_fa | گرفتن مورد انتخاب‌شده هنگام کلیک روی آن (به سبک Illustrator) |
| Finnish | ksnip_py_fi | Nappaa valittu kohde napsautettaessa sitä (Illustrator-tyylinen) |
| French | ksnip_py_fr / ksnip_py_fr_CA | Saisir l'élément sélectionné en cliquant dessus (style Illustrator) |
| Galician | ksnip_py_gl | Capturar o elemento seleccionado ao premer nel (estilo Illustrator) |
| Hebrew | ksnip_py_he | תפוס את הפריט שנבחר בעת לחיצה עליו (בסגנון Illustrator) |
| Croatian | ksnip_py_hr | Uhvati odabranu stavku prilikom klika na nju (Illustrator stil) |
| Hungarian | ksnip_py_hu | A kijelölt elem megragadása rákattintáskor (Illustrator-stílus) |
| Indonesian | ksnip_py_id | Tangkap item terpilih saat mengkliknya (gaya Illustrator) |
| Italian | ksnip_py_it | Afferra l'elemento selezionato al clic su di esso (stile Illustrator) |
| Japanese | ksnip_py_ja | クリック時に選択した要素をつかむ（Illustratorスタイル） |
| Georgian | ksnip_py_ka | მონიშნული ელემენტის ხატვა მასზე დაწკაპუნებისას (Illustrator-ის სტილში) |
| Korean | ksnip_py_ko | 클릭할 때 선택한 항목 잡기(Illustrator 스타일) |
| Dutch | ksnip_py_nl | Grijp het geselecteerde item bij het klikken (Illustrator-stijl) |
| Norwegian | ksnip_py_no | Ta tak i det valgte elementet ved klikk (Illustrator-stil) |
| Polish | ksnip_py_pl | Chwyć zaznaczony element po kliknięciu go (w stylu Illustratora) |
| Portuguese | ksnip_py_pt / ksnip_py_pt_BR | Agarrar o item selecionado ao clicar nele (estilo Illustrator) |
| Romanian | ksnip_py_ro | Prinde elementul selectat la clic pe el (stil Illustrator) |
| Russian | ksnip_py_ru | Захватить выбранный элемент при щелчке по нему (в стиле Illustrator) |
| Sinhala | ksnip_py_si | තේරු අයිතමය ක්ලික් කිරීමේදී අල්ලා ගන්න (Illustrator මෝස්තරය) |
| Slovenian | ksnip_py_sl | Zgrabi izbrani element ob kliku nanj (Illustrator slog) |
| Albanian | ksnip_py_sq | Kap elementin e zgjedhur kur klikon mbi të (stili Illustrator) |
| Swedish | ksnip_py_sv | Greppa det valda objektet när du klickar på det (Illustrator-stil) |
| Tamil | ksnip_py_ta | தேர்ந்தெடுக்கப்பட்ட உருப்படியைச் சொடுக்கும்போது பிடித்துக்கொள் (Illustrator பாணியில்) |
| Turkish | ksnip_py_tr | Tıklarken seçili öğeyi yakala (Illustrator tarzı) |
| Ukrainian | ksnip_py_uk | Схопити вибраний елемент під час клацання на ньому (у стилі Illustrator) |
| Chinese (Simplified) | ksnip_py_zh_CN | 点击时抓取所选项目（Illustrator 风格） |
| Chinese (Traditional) | ksnip_py_zh_Hant | 點擊時抓取所選項目（Illustrator 風格） |

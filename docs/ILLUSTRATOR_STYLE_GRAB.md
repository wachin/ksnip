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

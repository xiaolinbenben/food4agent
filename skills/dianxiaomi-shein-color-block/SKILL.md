---
name: dianxiaomi-shein-color-block
description: Fill missing Dianxiaomi SHEIN color-block/swatch images on the product edit page without deleting or replacing existing swatches, unless the user explicitly asks to replace all images or swatches. Use when the SHEIN color-block section has blank Add Image placeholders or missing 80x80 swatch images after colors have been selected or mapped.
---

# Dianxiaomi SHEIN Color Block

Fill only missing SHEIN color-block/swatch images by default. Do not delete, replace, regenerate, or repair existing color-block thumbnails unless the user explicitly asks to replace all images or swatches.

## Required Skills

- Use `chrome:control-chrome` for the user's real Chrome session.
- Use local solid-color swatch files first. Do not call image generation services for color blocks.

## Scope

Handle only the color-block/swatch image section, such as the section labeled `色块图`. The expected finished swatch image is a plain `80 x 80` single-color PNG.

Do not modify title, description, SKU codes, prices, inventory, product attributes, variant names, selected colors, detail images, square images, SKU product images, description images, shipping, save state, or publish state.

## Hard Rules

- Do not delete existing color-block images unless the user explicitly asks for full image or swatch replacement.
- Do not replace existing color-block images, even if they are not ideal, unless the user explicitly asks.
- Do not generate swatch files proactively for every color. Generate a swatch only after confirming that the current page has a visible empty swatch slot for that row.
- Treat visible thumbnails with a displayed size such as `80 X 80` as already filled.
- Treat visible `添加图片`, `Add Image`, `addImg`, empty dashed placeholders, or blank swatch slots as targets to fill.
- Fill only rows/slots that are currently empty.
- Scope every upload to the current color-block row/slot. Do not use a global Add Image button when multiple rows are visible.
- Do not use browser JavaScript to inject files, `data:` URLs, or hidden DOM values. Use normal file upload through Chrome file chooser.
- When explicit full replacement is requested, clicking the visible existing 80x80 swatch thumbnail can expose the same image-source dropdown. Use that row-scoped dropdown, choose local image, upload the replacement 80x80 PNG, and verify the new thumbnail source and dimensions.

## Choose The Swatch Color

Use the final selected SHEIN color for the row as the source of truth. Prefer the selected standard color label from the `颜色(Color)` mapping over the original 1688 color name when they differ.

Choose a solid hex color that visually matches the selected color:

- Black / Dark Gray: `222222` or `333333`
- Gray / Iron Gray / Volcanic Gray: `777777`
- Light Gray / Mist Gray: `B8B8B8`
- White / Pearl White: `FFFFFF`
- Cream / Cloud Cream: `F4EFE5`
- Khaki / Warm Clay: `B7A27A`
- Brown / Olive Brown: `7A5A3A`
- Red / Cherry Red / Ruby Red: `B01824`
- Pink / Sugar Pink / Ballet Pink: `F2A6B8`
- Blue / Sky Blue / Aqua Blue: `5A9FD6`
- Navy / Dark Blue: `1F2F57`
- Green / Fresh Green / Spring Green: `4E9A57`
- Yellow / Pale Yellow / Sunlit Yellow: `F2D36B`

If the color label is not covered by the examples, choose the closest obvious hex from the label and product/SKU color. If the color is ambiguous, stop and report the specific row instead of guessing.

If a variant label is a non-color value such as `fabric` or `material`, fill it only when Dianxiaomi save validation explicitly requires a missing color-block image and the visible product/SKU image shows an obvious neutral fabric tone. Use the closest neutral swatch such as `B8B8B8` for light gray fabric or `F4EFE5` for cream/off-white fabric, and record this as a human-review risk. If the tone is not obvious, stop and report the row.

## Create The 80x80 PNG

Preferred local method:

```powershell
.\.codex\skills\dianxiaomi-shein-color-block\scripts\new_swatch_png.ps1 `
  -HexColor "777777" `
  -OutputPath "data\<offerId>\image\color-block\gray-80x80.png"
```

The script writes a pure solid-color `80 x 80` PNG. Keep generated files under:

```text
data/<offerId>/image/color-block/
```

Fallback URL method, only when local generation is unavailable:

```text
https://singlecolorimage.com/get/<6-hex-color>/80x80.png
```

Examples:

```text
https://singlecolorimage.com/get/777777/80x80.png
https://singlecolorimage.com/get/ffffff/80x80.png
```

The Single Color Image API returns a PNG for `https://singlecolorimage.com/get/{{hex}}/{{width}}x{{height}}`; avoid unnecessary bulk requests because the service may rate limit.

## Upload Workflow

1. Take over a Chrome tab whose URL contains `/web/sheinProduct/edit`.
2. Read the visible color-block/swatch section only.
3. For each color-block row/slot:
   - If a real thumbnail already exists, leave it unchanged.
   - If the slot is empty, identify the row color label or selected standard color.
   - Generate one local `80 x 80` PNG for that color.
4. Click that row/slot's Add Image control and upload the local PNG with `filechooser.setFiles`.
5. After upload, verify the thumbnail is visible and the page displays `80 X 80` or equivalent accepted dimensions.
6. If upload fails because Chrome blocks local file upload, stop and report the browser permission issue.
7. If the page rejects the swatch after upload, report the row and error text. Do not delete existing swatches or change other image sections.

## Verified Dianxiaomi UI Behavior

- A blank swatch slot may not open a file chooser when clicked in the center or on the bottom operation icon. Try the active upper-left area of the slot; it can open a dropdown with local image, image space, network image, and reference-crawled-image choices.
- When the dropdown appears, choose the visible local-image entry and set the file chooser to the generated `80 x 80` PNG.
- Treat `Select Image` / `选择图片` and blank image slots as dropdown controls. Always verify the dropdown before expecting a file chooser.
- If clicking the slot opens the image-space modal instead, close it and retry the slot's active area or dropdown path before using image-space upload. Do not select a non-80x80 existing image as a swatch.
- A row that shows `80 X 80` after upload is accepted even if the surrounding row still has a stale validation class from a previous failed save.

## Save and Report

- Do not click Save, Save and Move to Pending Publication, or Publish unless the user explicitly asks.
- Report each filled color-block row, selected hex color, local file path, and whether the page accepted the `80 X 80` image.
- Report rows skipped because an existing swatch was already present.
- Report ambiguous colors that were not filled.

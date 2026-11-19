---
name: dianxiaomi-shein-image-backfill
description: Backfill Dianxiaomi SHEIN product image sections from generated local files after all non-image product fields are complete. Use when the product image/generated directory already contains finalized images from dianxiaomi-shein-image-generate and the Dianxiaomi SHEIN edit page needs old detail, description, square, and SKU images deleted, generated local files uploaded, and page-side blue-wand/batch editing used before any regeneration. Square images are reused as the first detail image and SKU image. This skill does not handle color-block/swatch images.
---

# Dianxiaomi SHEIN Image Backfill

Use generated local files to refill the Dianxiaomi SHEIN image sections. This skill starts only after title, description, price, SKU/item numbers, attributes, weight, dimensions, size chart, and other non-image fields are complete. Color-block/swatch images are outside this skill: do not read, delete, upload, refill, repair, or regenerate them.

## Required Skills

- Use `chrome:control-chrome` for the user's real Chrome session.
- Use `dianxiaomi-shein-image-generate` only when a required generated file is missing, unusable, or cannot be repaired with Dianxiaomi page tools.

## Inputs

Expected directory:

```text
data/<offerId>/image/generated/
  plan.json
  manifest.json
  detail/
  description/
  square/
```

Run the local upload manifest script first:

```powershell
.\.codex\skills\dianxiaomi-shein-image-backfill\scripts\collect_generated_upload_files.ps1 `
  -GeneratedDir "data\<offerId>\image\generated"
```

Use `generated/upload-files.json` to know which local files are ready. Do not perform image recognition; rely on filenames, plan metadata, dimensions, file sizes, and page validation text.

The upload manifest expands `plan.json` reuse mappings. A single `generated/square/<color>-square.png` file appears as a normal `square` file, a `detail` file with `reuse_role: detail-main`, and one or more `sku` files with `reuse_role: sku`.

The bundled PowerShell script must write JSON through its `Write-JsonFile` helper. In this PowerShell environment, multiline `ConvertTo-Json` output can be passed to `Set-Content` as an array, so the helper explicitly joins JSON lines into one string before writing. Convert `System.Collections.Generic.List` values to ordinary arrays with `.ToArray()` before writing upload manifests.

## Preconditions

- `generated/manifest.json` must exist.
- Required files must be local and `upload_ready: true`.
- Files over 3MB are unusable. Do not upload them.
- If required local files are missing or blocked, run the generation skill to generate or regenerate those slots before deleting page images.

## Verified Page Contract

Use the current verified page contract below. No external AGENTS page-contract file is present in this workspace.

Inside `#skuDataInfo`, the current verified table order is:

1. SKU table
2. Variant image table
3. Detail image table
4. Sell-info table
5. Reference link table
6. Inventory-proof table

For this skill:

- use the second table for variant detail, square, and color-block image rows
- use the third table for lower detail-image rows
- do not use broad `#skuDataInfo tbody tr` selectors across all tables

## Page Read Scope

Read only image-related state:

- Color rows and SKU rows.
- Detail, square, SKU, and description image slots.
- Counts such as `3 / 11` and `3 / 10`.
- Displayed dimensions such as `1254 X 1254` or `80 X 80`.
- Visible red errors in image sections.

Do not modify SKU codes, prices, inventory, product attributes, title, description text, shipping, publication state, or non-image fields.

## Deletion Rules

Delete old visible images only in these sections:

- Detail images: delete all old visible thumbnails per color row.
- Description images: delete all old visible thumbnails per description row.
- Square images: delete old square thumbnails per color.
- SKU images: always replace every visible SKU image slot with the generated SKU/square image for that row color.
Do not touch color-block/swatch slots at all, even if they appear blank or noncompliant, unless the user explicitly asks to replace all images including swatches. Use `dianxiaomi-shein-color-block` separately for the normal missing-swatch-only flow.

Treat `addImg` placeholders as empty slots. Ignore hidden `0 x 0` old image DOM remnants when visible thumbnails and counts are correct. Scope every delete to the current row and thumbnail; never globally click the first delete icon. Delete multiple thumbnails from right to left or last to first so positions do not shift.

An `addImg` placeholder may still render a visible disabled `icon_delete` control. Do not use delete-icon count alone as the deletion loop condition. Count/delete only real image containers whose visible `img.src` does not contain `addImg`; otherwise the loop can keep clicking a placeholder that cannot be removed.

## Upload Rules

- Prioritize local upload from `generated/<type>/`.
- Do not use network URL refill when a local file exists.
- Read Chrome file upload guidance before the first `filechooser.setFiles` call.
- If Chrome blocks local upload with `Not allowed`, stop and report the browser permission problem. Do not bypass Dianxiaomi with page JavaScript or `data:` URLs.
- Use the square-image reuse records from `generated/upload-files.json` for the first detail image and SKU image slots. Do not look for files under `generated/sku/`.
- Upload only records with `upload_ready: true`. The collection script blocks files whose actual dimensions fail the current page rules; do not upload blocked records even when the planned prompt requested an accepted ratio.
- Dianxiaomi image controls labeled `Select Image` / `选择图片` are dropdown menus, not direct upload buttons. Click the control, verify the visible dropdown with entries such as `本地图片`, `空间图片`, `网络图片`, and `引用采集图片`, choose `本地图片`, then set the file chooser.
- Prefer page batch buttons/controls whenever they are available for the current image section. Use them to upload or apply the same image set quickly across selected rows instead of repeating individual slot operations. After any batch action, read back each affected row's count and displayed dimensions.

## Verified Dianxiaomi UI Behavior

- In the top `Variant Images` rows, the row-level `Select Image` button uploads variant detail images. Upload at least two accepted detail images per color row; using the color square image as the first detail image plus one `detail-angle` image is accepted.
- If Save highlights a variant detail thumbnail with `img-item-border-red` and the row text says the detail image ratio must be `1:1`, `3:4`, `4:5`, or `13:16`, delete that invalid thumbnail from the detail cell. Do not keep a generated closeup just because it was part of the plan. Re-save with the remaining valid images when the row still has at least two accepted detail images.
- In the top `Variant Images` table, the row cells are separate: detail images, square image, then color-block image. A row can show `80 X 80` because the color-block cell is already filled while detail and square slots are still empty. Treat those cells independently and do not replace an accepted color-block swatch.
- Use the page's batch image control for variant/detail rows when it can target the intended rows. Select only the rows/colors being repaired, run the batch action, and verify every affected color row before continuing.
- The square-image slot is separate from the row-level detail-image area. Upload exactly one `generated/square/<color>-square.png` file to the square slot and verify the displayed dimension is `1:1`, typically `1254 X 1254`.
- The same color may also have a separate lower `Detail Images` section row. Replacing the lower detail section does not satisfy top `Variant Images` validation; both areas must be checked if saving fails.
- Clicking visible delete icons through Playwright locators can time out even when the icons are visible. If a scoped locator times out, read the current row's thumbnail/delete-icon bounding rectangles and click the visible delete icon center with CUA. Re-read the row after each deletion because row heights and y-coordinates can shift.
- Empty square slots and image slots often expose a Dianxiaomi dropdown only when clicked in the active image area, not always on the bottom operation icon. When the dropdown appears, choose the visible local-image entry and then set the file chooser.
- Empty square-image cells can expose the local-image dropdown by clicking the visible `addImg` placeholder itself. Use that path to upload exactly one square file, then verify the displayed `1254 X 1254` or other accepted `1:1` dimensions.
- The page may expose only one hidden `#localFileUploadInp` with `multiple=false`; do not use that DOM attribute to decide upload capability. After opening the Dianxiaomi local-image menu, use the Chrome file chooser's `isMultiple()` result. Detail and description row buttons can accept multiple files; square and SKU slots should be uploaded one file at a time.
- When scoping upload targets under `#skuDataInfo`, use the verified table order in this skill instead of rediscovering the table meaning from scratch.
- Before deleting thumbnails, verify that no image-source dropdown or modal is covering the row. A leftover dropdown can intercept delete-icon clicks and open `引用采集图片` instead; close the dropdown or stacked modal first, then re-read the visible delete-icon coordinates.
- Bulk/apply-to-all image actions such as applying one SKU image to all rows must be verified row by row. If any SKU row still shows the old thumbnail or old dimensions, replace that row's image individually through its own image dropdown and local upload.
- SKU image thumbnails can open the same Dianxiaomi image-source dropdown as other image slots. Click the row-scoped SKU thumbnail or placeholder, choose the visible local-image menu item, upload exactly one file, and verify that row's thumbnail source and dimensions before moving to the next row.
- For SKU thumbnails, first remove old marketplace thumbnails through the row-scoped `.img-close-icon` so every target row becomes an `addImg` placeholder. Then click each row's placeholder, choose `本地图片`, upload exactly one square file for that row color, and verify `1254 X 1254` or another accepted 1:1 dimension.
- When CUA coordinate clicks open an image-source dropdown but clicking the first-row menu coordinates does not trigger the file chooser, switch to a scoped Playwright locator on the visible dropdown menu item, such as `.ant-dropdown` filtered to visible and `.ant-dropdown-menu-item` filtered by `本地图片`. Hidden dropdown templates accumulate in the DOM.
- Treat old red `ant-form-item-has-error` classes as stale only after the row text no longer contains any red validation message and the required image counts/dimensions are visible. The next save attempt may clear the class.

## Repair Before Regeneration

If a generated local image uploads but the page reports ratio, crop, or pixel validation errors, repair it with Dianxiaomi tools before calling Terln GPT Image again:

1. Open the thumbnail image-edit menu.
2. Prefer the blue magic-wand edit entry or Dianxiaomi batch edit tool when available.
3. For square-image issues, enter `/web/newImageEditor`, use the square/main-image resize preset, Apply, then Save and Apply.
4. Return to the product edit tab and recheck displayed dimensions and red errors.
5. Regenerate only when the page editor is unavailable, Save and Apply fails, or the repaired image still fails validation.

Do not attempt page editor repair for files that are missing, unreadable, or over 3MB; regenerate those slots directly through the generation skill.

## Refill Targets

### Detail Images

- Upload only ready detail-section images per color. Start with the `reuse_role: detail-main` square record, then upload ready generated detail records from `generated/detail/`.
- Do not force the `detail-closeup` record if `upload-files.json` marks it blocked or the page rejects its displayed dimensions. At least two accepted variant detail images are enough; the square detail-main plus one valid `detail-angle` image passed current page validation.
- Prefer the section's batch upload/batch image button when it can apply the same three-file pattern to the intended color rows. Do not batch across unrelated colors unless the page makes the target mapping explicit and you can verify each row afterward.
- Confirm at least `2 / 11`, preferably `3 / 11`.
- Confirm displayed dimensions are accepted.

### Square Images

- Upload one square image per color from `generated/square/`.
- Confirm `1:1` and between `900 X 900` and `2200 X 2200`.
- Use page editor repair before regeneration if the image is otherwise uploaded successfully.

### SKU Images

- Process existing SKU rows only.
- Do not add SKU rows or modify SKU fields.
- Upload one ready `reuse_role: sku` record per visible SKU image slot; each record points to that color's square file.
- If a scoped, page-supported SKU upload path cannot be found after trying the row thumbnail/placeholder and header/batch controls, stop and report the blocker. Do not leave old SKU thumbnails in place, and do not use browser-side DOM injection or hidden file inputs to force replacement.

### Description Images

- Upload 3 generated description images per color from `generated/description/`.
- Confirm `3 / 10` and displayed dimensions above `900px` on both sides.
- If a low-pixel error appears after upload, use page repair first; regenerate only if repair fails.

## Chrome Operation Notes

- Reclaim a stale Chrome tab by visible title or URL containing `/web/sheinProduct/edit`; do not reload unless required.
- After every click that opens a menu or modal, verify the visible state before continuing.
- For Chrome file uploads, call `waitForEvent("filechooser", { timeoutMs: ... })`, not `{ timeout: ... }`. Attach a `.catch(...)` handler to the chooser promise before clicking the menu item so a timeout does not reset the node REPL kernel.
- Dropdown locators may hit hidden templates. If a locator times out, use a fresh DOM read and click the visible menu item center from its bounding rectangle.
- `generated/upload-files.json` can contain a UTF-8 BOM when written by Windows PowerShell. If parsing it from Node, strip a leading `\uFEFF` before `JSON.parse`.
- Scope row actions with the actual `tr` for the current color, description row, or SKU row. A broad ancestor can upload images into the wrong row.
- If extra thumbnails are accidentally added to a row, remove only those extras from last to first, then recheck the row count.

## Save and Recheck

- Do not click Save, Save and Move to Pending Publication, or Publish unless the user explicitly asks.
- If the user asks to save, click only the normal product page Save button.
- After saving, recheck detail counts, square dimensions, SKU thumbnails, description counts, visible image-section red errors, and that no visible image source is still from the original marketplace domains such as `cbu01` or `alicdn`.

## Final Report

State:

- `generated/upload-files.json` path.
- Old image types and counts deleted.
- Which local files were uploaded to each section.
- Whether page blue-wand, batch edit, or `/web/newImageEditor` repair was used.
- Whether regeneration was required.
- Whether product page normal Save was clicked.
- Whether visible image-section red errors remain.

---
name: dianxiaomi-shein-image-generate
description: Generate Dianxiaomi SHEIN replacement product images from raw-product.json image URLs into fixed local folders with reusable scripts. Use after the Dianxiaomi SHEIN edit page is open and variant colors/specs have already been normalized, when detail, description, and square images should be generated for later backfill. Square images are reused as the first detail image and SKU image. This skill prepares JSON image candidates, builds a generation plan from finalized page colors/SKU rows with separate reference images per color, runs Terln gpt-image-2 generations synchronously, and writes generated files plus manifest metadata into the product image/generated directory.
---

# Dianxiaomi SHEIN Image Generate

Generate replacement images only. Do not delete, upload, refill, save, or publish anything on the Dianxiaomi page in this skill. Color-block/swatch images are outside this skill: do not generate them and do not create a `swatch/` directory.

Start this skill immediately after the edit workflow has verified colors, sizes, and SKU variant rows, mapped colors to standard SHEIN colors where possible, and removed obvious non-SKU variant rows. This happens before editing title, description, attributes, price, size chart, or other form fields. Do not generate images for rows such as fabric/material samples that will be deleted.

Do not start image generation before variant-theme cleanup is complete. If the main spec is not `颜色(Color)`, if other specs include obvious non-sellable values, or if source/custom colors can be mapped to close SHEIN standard colors, fix those on the page first and then read the final row labels.

## Required Skills

- Use `chrome:control-chrome` only to read the current SHEIN edit page colors and SKU row labels.
- Use `terln-gpt-image` only through the bundled scripts. Do not hand-roll Terln API calls or create per-product runner scripts.

## Inputs

- Prefer `product-context.json` when it exists.
- Fall back to `raw-product.json` when `product-context.json` is missing.
- Read the live page only for finalized current color row labels and finalized current SKU row labels.
- The final page labels after standard-color mapping are the generation keys. If a late page correction changes `白色（755）` to `White`, `黑色（755）` to `Black`, or `咖色（755）` to `Coffee Brown`, rebuild or remap the upload plan before backfill so SKU, square, detail, and description files are uploaded to the matching final color rows.

## Workspace Layout

Given `<json_dir>/raw-product.json`, write:

```text
<json_dir>/image/
  candidates/
    files/
    manifest.json
    contact-sheet.jpg
  generated/
    plan.json
    manifest.json
    upload-files.json
    detail/
    description/
    square/
    unusable/
```

Do not create `image/originals/`. Reference images come directly from JSON URLs. Downloaded candidate files and the contact sheet are only for quick visual selection.

## Fixed Script Flow

Run all commands from the workspace root.

The bundled PowerShell scripts must write JSON through their `Save-Json` or `Write-JsonFile` helper. In this PowerShell environment, multiline `ConvertTo-Json` output can be passed to `Set-Content` as an array, so helpers explicitly join JSON lines into one string before writing. When writing `manifest.json` or `plan.json`, convert any `System.Collections.Generic.List` values to ordinary arrays with `.ToArray()` first.

1. Prepare JSON image candidates:

```powershell
.\.codex\skills\dianxiaomi-shein-image-generate\scripts\prepare_json_image_candidates.ps1 `
  -RawProductJson "data\<offerId>\raw-product.json"
```

2. Open `image/candidates/contact-sheet.jpg`. Select JSON references separately for each finalized page color. For each color, choose only reference thumbnails that visibly show that same colorway; do not pass mixed-color reference groups. Do not ask a human to exclude unsuitable images and do not create an exclusion list. If the sheet includes non-product images such as text cards, swatches, care/washing tips, logos, placeholders, or after-sale graphics, omit them from every color's reference list. If a color has no same-color product references, stop and report that color instead of borrowing another color.

3. Build the generation plan from finalized current page state. Pass current SKU row labels so the plan can map each SKU row to that color's square image; SKU labels do not create separate generation tasks.

```powershell
.\.codex\skills\dianxiaomi-shein-image-generate\scripts\new_shein_image_generation_plan.ps1 `
  -RawProductJson "data\<offerId>\raw-product.json" `
  -Colors "White","Gray" `
  -SkuKeys "White-S","White-M","Gray-S","Gray-M" `
  -ProductSummary "short product facts from the page and raw JSON" `
  -ColorReferenceIndexes "White=1,3,5","Gray=8,10,12"
```

`-ColorReferenceIndexes` is required for every color in `-Colors`. Use the exact finalized color label from the page on the left side of `=`. Do not use one global reference list for all colors. There is no swatch/color-block parameter in this skill.

When invoking from a single-line PowerShell command, pass multi-value parameters as explicit arrays to avoid positional binding mistakes:

```powershell
-Colors @("白色（755）","黑色（755）") `
-SkuKeys @("白色（755）-S","黑色（755）-S") `
-ColorReferenceIndexes @("白色（755）=11,13","黑色（755）=2,3")
```

4. Run all generation tasks and write `generated/manifest.json`:

```powershell
.\.codex\skills\dianxiaomi-shein-image-generate\scripts\run_shein_image_generation_plan.ps1 `
  -PlanPath "data\<offerId>\image\generated\plan.json"
```

The generation script calls Terln sequentially and writes each completed or failed slot back to `plan.json` immediately. If the outer shell/tool times out, already completed files and statuses are preserved and the same command can be rerun to generate only unfinished slots.

## Plan Rules

The plan script creates these tasks per color:

- 2 detail images: angle `3:4`, closeup `4:5`.
- 3 description images: all `3:4`.
- 1 square image: `1:1`; reuse it as the first detail image and as the SKU image for matching SKU rows.
- 0 standalone SKU images.

The plan sends API sizes as explicit pixel strings: `1024x1024` for square images, `960x1280` for `3:4` images, and `1024x1280` for `4:5` images. Treat any generated local file over 3MB as unusable. Regenerate that slot with corrected plan inputs instead of uploading it.

Do not assume the model obeyed the planned ratio. After generation completes, validate the actual local dimensions before upload. Current Dianxiaomi SHEIN variant detail images accept only `1:1`, `3:4`, `4:5`, or `13:16` with each side from `900px` to `2200px`; square and SKU images must be `1:1`; generated description images should remain `3:4` with both sides at least `900px`. If a downloaded file misses the accepted ratio or pixel range, mark that slot unusable and regenerate it, or omit only an optional detail image when the page still has at least two valid variant detail images.

Generated slot keys and file names must remain unique across page colors. Chinese color labels can share the same numeric suffix, such as `白色（755）`, `黑色（755）`, and `咖色（755）`; therefore the script appends a stable hash suffix to the sanitized slug. Before running generation, check `plan.json` for duplicate `local_file_path` values. If duplicates exist, fix the plan or script first; otherwise completed tasks can overwrite each other during file saving.

Prompt constraints are fixed in the plan script:

- Prompt text lives in `scripts/shein_image_prompt_templates.json`. Edit that file for common prompt wording and per-image prompt wording; keep PowerShell code focused on plan assembly.
- Preserve the product shown in JSON references.
- Explicitly state the required image ratio in every model prompt: `1:1`, `3:4`, or `4:5`.
- Use only the reference images assigned to the current color. The generated product color must match the current SKU/spec color exactly enough for a buyer to recognize the variant; do not borrow, mix, average, reinterpret, or drift toward another colorway.
- Do not add readable text, labels, logos, watermarks, typography, infographic layouts, unrelated props, or accessories.
- If any text appears anywhere in generated images, whether intentional, incidental, background, signage, garment tag, packaging, label, or generation artifact, it must be English only. Never allow Chinese or other non-English characters.
- For square images, use exactly one single product item only, match the current SKU/spec color, use pure `RGB(255,255,255)` white background, keep the product about 80% of the image area, and include no text of any kind.

## Verified Page Contract

Use the current verified page contract below. No external AGENTS page-contract file is present in this workspace.

For this skill, the relevant current verified page state is in `#skuDataInfo`:

- the first table is the SKU table
- the second table is the variant-image table

Read only:

- finalized current color row labels after standard-color mapping and non-SKU row removal
- finalized current SKU row labels from the first SKU table

Do not rediscover table meaning from scratch when the verified headers already match the current page.

## Page State To Read

Read only:

- Finalized current color row labels after standard-color mapping and non-SKU row removal.
- Finalized current SKU row labels.

Do not modify title, description, price, attributes, SKU fields, inventory, shipping, product status, or images in this skill.

## Reference Selection Rules

- Use JSON image URLs only; do not use old Dianxiaomi page images as generation references.
- Do not run an artificial manual approval step for candidates.
- For each color, prefer references that visibly cover that same color in different light conditions, model/product angles, closeups, and full-product views.
- Do not include references for another color in a color's reference group, even when the garment shape is similar.
- If raw JSON is malformed, keep using the candidate script; it extracts image URLs from raw text.
- If a color cannot be represented by any JSON reference, report that color and do not borrow another color.

## Final Report

State:

- `contact-sheet.jpg` path.
- `generated/plan.json` path.
- `generated/manifest.json` path after generation.
- Colors and SKU keys used in the plan.
- Per-color reference indexes used.
- Square-image reuse targets for detail-main and SKU rows.
- Completed, unusable, and failed generation counts.

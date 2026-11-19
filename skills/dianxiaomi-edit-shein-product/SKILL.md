---
name: dianxiaomi-edit-shein-product
description: Edit a claimed Dianxiaomi SHEIN product from its direct backend edit route. Use after a 1688 product has been crawled and claimed, when a SHEIN edit URL with an id query parameter is available, or when a uniquely verified collection-box row id must first be discovered.
---

# Edit Dianxiaomi SHEIN Crawled Product

Use this skill when the user asks to edit a product that has already been crawled from 1688 and claimed into SHEIN.

This skill owns the full non-final SHEIN edit flow:

- build and reuse `product-context.json`
- verify and normalize variants
- submit image-generation tasks
- fill title, description, attributes, source URL, item number, price, weight, package dimensions, and package type
- complete the size chart
- backfill generated images
- fill missing color-block images
- save or move to pending publication only when the user asked for that status

Do not switch into standalone title, description, or pricing skills. Those lightweight rules are handled here.

## Prerequisites

- You must use `control-chrome` to connect to the user's real Chrome.
- Assume Chrome is logged into an operable Dianxiaomi account by default. If not logged in, the account is wrong, or permissions are insufficient, stop and let the user handle it.
- Prefer local input from the current product directory:
  - `raw-product.json`
  - `product-context.json`
  - `dianxiaomi-crawl-result.json`
- If `product-context.json` is missing and `raw-product.json` exists, generate `product-context.json` first with:

```powershell
.\.codex\skills\dianxiaomi-edit-shein-product\scripts\build_product_context.ps1 `
  -RawProductJson "data\<offerId>\raw-product.json"
```

- If the user did not specify a product, default to the most recent product under `data/<offerId>/`.
- If only `raw-product.json` exists and the product has not yet been crawled into Dianxiaomi, first switch to `dianxiaomi-1688-crawl`.
- Prefer a known SHEIN product id or direct edit URL. If the claim result did not expose an id, use the SHEIN collection-box list only to discover a uniquely verified `rowid`; do not enter editing by clicking the list Edit action.

## Entry

1. If the product id is unknown but claim success is already verified, open the SHEIN collection box only for id discovery:

```text
https://www.dianxiaomi.com/web/sheinProduct/draft
```

Search by a distinctive title keyword or source URL, require exactly one matching row, and verify title, source link, store, and creation or update time before using that row's `rowid` as `<productId>`. If uniqueness cannot be proven, stop and report the blocker.

2. Open the direct Dianxiaomi SHEIN edit route:

```text
https://www.dianxiaomi.com/web/sheinProduct/edit?id=<productId>
```

3. Verify the page title, source URL, and target store before making changes.
4. If the direct edit URL is missing, permissions are insufficient, or the page reports an error, stop and let the user handle it.

## Verified Page Contract

Use the current verified page contract below instead of rediscovering the edit page from scratch every time. No external AGENTS page-contract file is present in this workspace.

Important current structure:

- `#productBasicInfo`: basic information card
- `#productInfo`: product information card
- `#productVideoInfo`: product video card
- `#skuDataInfo`: variant root
- `#skuImageInfo`: variant image card
- `#skuDescInfo`: detail image card
- `#skuSellInfo`: sell-info card
- `#skuInformationInfo`: reference-information card

Important current field names:

- `sourceUrl`
- `productTitleBuyer`
- `productItemNumber`
- `productDesc`
- `.skuAttrSizeChart`

Important current action buttons exist in both header and footer:

- `Save and Move to Pending Publication`
- `Save`
- `Publish`

Scope all actions to the intended visible container. Do not click a generic global text match when the same label exists both at the top and bottom of the page.

Inside `#skuDataInfo`, use this verified table order. For SKU edits, prefer the first table rather than broad selectors over the whole `#skuDataInfo` subtree.

## Execution Order

Follow this order exactly:

1. Verify page identity and local source files.
2. Build or refresh `product-context.json` if needed.
3. Verify and normalize variant colors, sizes, and sellable SKU rows.
4. Immediately start `dianxiaomi-shein-image-generate`.
5. Complete non-image edits:
   - category
   - attributes
   - source URL
   - title
   - description
   - item number
   - supply price
   - inventory check
   - weight
   - package dimensions
   - package type
   - product video deletion
6. Run `dianxiaomi-shein-size-chart`.
7. Run `dianxiaomi-shein-image-backfill`.
8. Run `dianxiaomi-shein-color-block`.
9. Save or move to pending publication only if the user asked for that status.

Do not use Save, Save and Move to Pending Publication, or Publish as an exploratory way to discover missing fields before the ordered flow above has been completed.

## Variant Rules

- Before image generation or image upload, inspect the variant theme area. The main spec should be `颜色(Color)` for normal apparel colorways, and the other spec should match the actual sellable secondary option such as `尺寸(Size)`.
- If the selected main spec is obviously not a color, or an other-spec option is clearly not sellable for this product, unselect/remove it before continuing. If the source evidence is ambiguous, stop and report instead of guessing.
- Map colors to existing SHEIN standard colors whenever a close standard option exists.
- Avoid custom edited colors when a standard color is adequate.
- Replace source/custom color names such as `白色（755）`, `黑色（755）`, or `咖色（755）` with the closest existing SHEIN standard colors such as `White(白色)`, `Black(黑色)`, or `Coffee Brown(咖啡棕)` when the match is clear.
- Confirm that the current page colors, selected sizes, and SKU rows match the sellable variants from the source data.
- Remove only rows that clearly cannot be sellable SKUs, such as material samples, color cards, placeholder rows, or other reference-only variants.
- If a row could reasonably be customer-selectable, report ambiguity instead of guessing.
- After changing colors or variant selections, re-read the remaining color rows, SKU rows, and image rows before continuing. Dianxiaomi can recreate variant rows and reset SKU images, variant/detail images, price, stock, weight, dimensions, package type, and SKU fields; refill and re-upload those fields after the change.

## Image Generation Handoff

After variant cleanup, start `dianxiaomi-shein-image-generate` immediately.

When building the image generation plan:

- Prefer `product-context.json` if present.
- Use only source image URLs from local files, not old Dianxiaomi page images.
- Use the finalized current page colors and current SKU row labels as the page-state input.
- Do not wait for generation completion before continuing non-image edits once task submission succeeds.

## Non-Image Edit Rules

### Category and attributes

- Select the SHEIN category before trusting downstream auto-inferred attributes.
- Audit auto-selected attributes after category selection. Correct only clear conflicts supported by source title, source attributes, product images, or size-chart evidence.
- Treat visible red-star labels as required even when the underlying inputs do not have a native `required` attribute. On the current SHEIN edit page this includes both Ant form labels such as `label.ant-form-item-required` and product-attribute labels such as `.attr-label.required`.
- For red-star product attributes, verify the selected value or checked option directly. Do not rely on the option text being visible in the group; checkbox/radio groups can show every option while none is selected.
- Map 1688 `弹力等级 微弹` to `Slight Stretch(低弹)` for `面料弹性 (Fabric Elasticity)`. If the source elasticity is missing or conflicts with the product evidence, report the ambiguity instead of guessing.
- If `成分 (Composition)` exposes percentage inputs, fill the percentages before Save, Save and Move, or Publish. Use source material content first: when the source says main material is `95%及以上` and the page has `Polyester` plus `Elastane` selected for a stretch garment, fill `Polyester 95` and `Elastane 5`; if only one material is selected, fill `100`. Blank composition percentage inputs can still trigger `存在必选项未填写`.

### Source URL

- Fill `sourceUrl` with the 1688 source link from local source data.

### Title

- Fill `productTitleBuyer`.
- Generate one English SHEIN golden title from verified source data.
- Start with the strongest searchable product category keyword.
- Then add verified high-value buyer terms in this order when supported: style or silhouette, fit, sleeve or neckline, material or fabric, pattern, season, and occasion.
- Use natural marketplace wording, not literal awkward translations.
- Avoid keyword stuffing, repeated synonyms, vague filler, and unverified trend terms.
- Do not invent brands, certifications, materials, sizes, origins, or functions.

### Description

- Fill `productDesc`.
- Generate clear English shopper-facing copy suitable for the Dianxiaomi description field.
- Preserve confirmed or image-visible attributes such as color, fabric, fit, pant length, waist type, season, and style.
- Avoid medical, body-shaping, exaggerated, and infringing claims.
- Do not invent brands, certifications, materials, sizes, origins, or functions.

### Item number

- Fill `productItemNumber`.
- Generate a random 10-digit item number whose first digit is not `0`.
- SKU is usually not required. If variant normalization recreates rows and leaves visible SKU fields blank, fill stable readable SKU values or use the page's one-click generation before saving.

### Price

- Overwrite the automatically calculated supply price in the SKU table.
- Use only this formula:

```text
base price = 1688 purchase price * 8 / 6.5
Dianxiaomi USD sale price = integer part of base price changed to .99
```

- If there are multiple SKU purchase prices, calculate the sale price separately for each SKU purchase price.
- In the current verified SKU table, the first `price` input in each row is supply price and the second `price` input is inventory.
- For speed, prefer the batch controls in the first SKU table for supply price, weight, package dimensions, and package type. Read back the affected rows after each batch edit.

### Inventory

- Preserve source/imported inventory values when present.
- If Save or Save and Move reports `库存不能为空`, fill only the empty inventory inputs with `0` and retry the same save path. This records an out-of-stock state without inventing positive stock.
- In the current verified SKU table, the second `price` input in each row is the inventory input even though its `name` is still `price`.

### Weight and package dimensions

- For apparel, set package weight to `0.3 kg`, i.e. 300 grams.
- For apparel, set package dimensions to `20 x 15 x 3 cm`.

### Package type

- For apparel, choose soft package + soft item.
- Do not accidentally overwrite purchase status while editing package type.
- In the current SKU table, package type and purchase status are native `<select>` controls in each SKU row. The first row-scoped `select` is package type, and the second row-scoped `select` is purchase status. Avoid CSS selectors such as `select.!w-90...`; class names containing `!` need escaping, so prefer row-scoped `querySelectorAll('select')[0]` and `[1]` or Playwright locators scoped to the SKU row.

### Product video

- Delete any existing product video before saving.
- Do not upload or generate a replacement video unless the user explicitly asks.
- Treat a visible `addVideo` placeholder as an empty video slot, not an existing video. Hidden `播放` / `删除` links can remain in the DOM after the slot is empty; delete only visible non-placeholder video thumbnails or controls.

### Main material weight

- If main material weight is shown as a visible red-star required field, fill it during the normal pre-save pass.
- Use explicit source material-weight evidence when available. If the source has no usable value, fill only this required field with a reasonable common-sense estimate for the product category/material and record that it was estimated.
- If main material weight is not red-star required, do not fill it proactively unless Save or Save and Move reports a validation error specifically for main material weight. Then fill only the required field, record any estimate, and retry the same save path.

## Size Chart

- If the page shows a size-chart entry such as `尺码表`, `编辑尺码表`, or `Size Chart`, use `dianxiaomi-shein-size-chart`.
- That skill owns only the size-chart modal. Do not guess size values inline here when the modal is available.

## Image Backfill

- After non-image fields and the size chart are complete, use `dianxiaomi-shein-image-backfill`.
- Then use `dianxiaomi-shein-color-block` to fill only missing `80 x 80` swatch slots, unless the user explicitly asked to replace all images including swatches.
- Full image replacement means SKU images are mandatory replacement targets. Use each row's generated square/SKU image for the SKU thumbnail, upload one generated square image in the square-image cell for the matching color, and verify every row after upload.

## Save and Move Rules

- Save is allowed only after the full ordered flow above is complete.
- Click normal `保存` only when the user asked to save.
- Click `保存并移入待发布` only when the user asked to move to pending publication.
- Do not click `发布` unless the user explicitly asked to publish after a summary.
- When the page has both header and footer action buttons with the same text, scroll the intended footer/header container into view and click the visible button in that container. Do not use a global first text/role match; it can target the offscreen header button and leave the page unchanged.
- Treat the visible modal or toast and section-level validation text as authoritative. The URL staying the same is not proof of success.
- A successful Save and Move can leave the browser on the edit URL and show an Ant modal saying the product has been moved to pending publication. Treat that modal text as the authoritative success signal, then verify the product in the pending-publication list.
- After Save or Save and Move, a top toast can report a generic error such as `产品信息中有错误，请检查`. In that case the page usually scrolls to the first error area. Read the red section label, red field border, and nearby red text in that area; the red text explains the actionable validation error.
- If Save and Move returns to the edit page without an authoritative success signal, treat that as failure.
- After moving to pending publication, verify the pending-publication list when possible:

```text
https://www.dianxiaomi.com/web/sheinProduct/offline
```

- After a successful move to pending publication, use `feishu-human-review-notify` when a Feishu webhook is configured. If no webhook is configured, report that notification was skipped.

## Output

Return:

- data source file paths
- edit page link
- `product-context.json` path
- title used
- item number used
- purchase price and derived USD sale price
- confirmed fields
- remaining missing or estimated fields
- whether normal save or move to pending publication was attempted
- whether Feishu notification was sent

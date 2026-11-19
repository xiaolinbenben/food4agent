---
name: dianxiaomi-claim-crawl-product
description: Claim a successfully crawled product from the Dianxiaomi data acquisition list into the collection box of a specified platform store. Use when the user asks to "claim the product just crawled", "click Claim in the data acquisition list", "select the store and confirm", or claim a product into a SHEIN, TikTok, or other store collection box. For SHEIN follow-up editing, open the claimed product's backend edit route directly when its product id is known; if the claim result does not expose the id, the SHEIN collection-box list may be used only to discover a uniquely verified row id.
---

# Claim Dianxiaomi Crawled Product

## Goal

Find the crawled product on the Dianxiaomi data acquisition page, click that row's Claim button, select the target store in the modal, click Confirm, and claim the product into the corresponding platform collection box. Claiming is not publishing; do not click one-click publish or publish.

## Prerequisites

- The product already appears in the data acquisition list through `dianxiaomi-1688-crawl` or another Dianxiaomi crawl method.
- The target store is known. If the page has only one selectable store and the user has asked to claim the product, that store can be used.
- You must use `control-chrome` to control the user's real Chrome and operate according to the currently visible page state.
- If claiming may be followed by SHEIN editing, locate the corresponding `raw-product.json` and keep the path available. Do not start SHEIN image generation during claim; `dianxiaomi-shein-image-generate` starts after the SHEIN edit page is open so page colors and SKU rows can drive the plan.

## Standard Flow

1. Open or take over the Dianxiaomi data acquisition page:

```text
https://www.dianxiaomi.com/web/productCrawl/dataAcquisition
```

2. Locate the target product row by a distinctive product-title keyword from `raw-product.json` or the crawl result. Do not use `offerId` search for this workflow.
3. If a crawl completion modal, claim result modal, or overlay is still on the page, close it first. Otherwise the row-level Claim button may be blocked and not clickable. Ant modal text may remain in the DOM after close; treat it as closed only after the modal is hidden by computed style or has no visible bounding rect.
4. If the list search box is needed to locate the product, React input boxes may not respond to directly setting `value`; click the input, type only the product-title keyword with real keyboard events, then press Enter or click the search button.
5. Click the target row's right-side Claim button. Scope the action to the currently visible target row; do not use a broad global `认领` text match because hidden modal remnants or other rows can cause the wrong click target. Do not click the page-level Batch Claim button unless the user explicitly asks for batch operation.
6. In the store-selection modal, find the target platform and store.
7. Select the target store. Scope all interactions to the currently visible store-selection modal. Hidden duplicate modal nodes may remain in the DOM after prior operations.
   - The modal can show non-store destinations such as `产品开发`, `产品开发SHEIN`, or `草稿箱` alongside platform stores. Do not select those when the target is a SHEIN store; select only the intended visible store row under the SHEIN platform/store area, such as `刘建锋`.
8. Prefer clicking the visible checkbox label for the intended store row instead of relying on a global text match for the store name alone. If the same store name appears more than once, use only the visible selectable row in the active modal.
9. Confirm that the right-side selected state includes exactly the intended store.
10. Click Confirm.
11. Wait for the result modal, and record success, failure, and skipped-duplicate counts.
12. For SHEIN follow-up editing, use the direct backend route once the product id is known from the claim result, backend route, local record, or a verified collection-box row id:

```text
https://www.dianxiaomi.com/web/sheinProduct/edit?id=<productId>
```

13. If the claim result modal reports success but does not expose a product id, open the relevant platform collection box only to discover the id. For SHEIN, use:

```text
https://www.dianxiaomi.com/web/sheinProduct/draft
```

Search by a distinctive title keyword or source URL, require exactly one matching row, and verify title, source link, store, and creation/update time before using that row's `rowid` as `<productId>`. In the SHEIN draft list, the id can be read from the verified table row element such as `tr.vxe-body--row.shein-product-table-row[rowid]`. Do not click the list Edit action as the edit entry point; after reading the row id, navigate directly to the backend edit URL above.
14. Verify the direct edit page against the product title/source URL before editing. If the product id still cannot be determined from a uniquely verified row, stop and report that the direct edit route cannot be constructed.
15. Close the result modal and leave the page available for the user to inspect. After close, confirm the modal is visually hidden before searching or clicking rows; hidden result text such as a prior success count can still be present in page text.

## Prohibited Actions

- Do not click One-Click Publish, Crawl and One-Click Publish, Publish, batch operations, or other final publishing actions.
- Do not automatically select multiple stores unless the user explicitly requests multi-store claiming.
- Do not select extra rules such as duplicate-claim prevention unless the user explicitly asks.
- Do not change claim rules, templates, or store authorization configuration unless the user explicitly asks.
- If the target store does not exist in the modal, names do not match, selected state is unclear, or the platform requires template selection, stop and ask the user to confirm.

## Result Record

After claiming, record:

- Target product source link
- Product title
- Target platform
- Target store
- Direct SHEIN edit URL if opened or available
- If discovered through the SHEIN collection box, the verified row id and the row checks used to prove uniqueness
- Original result modal summary
- Success count, failure count, and skipped duplicate count
- Fields requiring confirmation before the next edit or publish step

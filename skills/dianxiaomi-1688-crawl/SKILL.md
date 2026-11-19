---
name: dianxiaomi-1688-crawl
description: Crawl a 1688 product link through the Dianxiaomi data acquisition entry, then edit the generated Dianxiaomi product and enter the save or publish workflow. Use when the user asks to list a 1688 product in Dianxiaomi, crawl it into Dianxiaomi, distribute it through Dianxiaomi, crawl first and then edit/publish, or mentions https://www.dianxiaomi.com/web/productCrawl/dataAcquisition.
---

# Dianxiaomi 1688 Crawl Listing

## Goal

Use Dianxiaomi's built-in data acquisition feature to submit the selected 1688 product link to Dianxiaomi. After the crawl succeeds, hand off to `dianxiaomi-claim-crawl-product` and `dianxiaomi-edit-shein-product` if further editing is needed.

## Default Entry

Open:

```text
https://www.dianxiaomi.com/web/productCrawl/dataAcquisition
```

You must use `control-chrome` to control the user's real Chrome. Do not replace Dianxiaomi backend operations with ordinary web scraping.

## Input Sources

- Prefer the 1688 link explicitly provided by the user.
- If the user says "the product just crawled", default to the most recent `data/<offerId>/raw-product.json` in the workspace and use its `source.url`.
- Local crawl JSON is used only to determine the product link, check title, variants, purchase price, and later editing. It is not the main path for directly creating a Dianxiaomi product.
- If the workspace only contains local `raw-product.json` files and the product is not yet visible in Dianxiaomi data acquisition, treat that as "not crawled into Dianxiaomi yet". Submit the 1688 link through this skill first instead of jumping directly to claim or edit skills.
- If the next step may enter SHEIN editing, only make sure the corresponding `raw-product.json` path is known. Do not start SHEIN image generation during crawl; `dianxiaomi-shein-image-generate` starts after the SHEIN edit page is open so page colors and SKU rows can drive the plan.

## Standard Flow

1. Open the Dianxiaomi data acquisition page.
2. Confirm the page is logged in. Stop for the user to handle login, CAPTCHA, insufficient permissions, or risk controls.
   - If a `功能更新` or other announcement modal appears, close it before entering the source link or clicking crawl controls.
3. Find the crawl link input and enter the 1688 product link.
   - Multiple 1688 links may be submitted in one crawl batch when the user explicitly asks for multiple newly collected products to be processed together.
4. Click only the Start Crawl button (`开始采集`) and wait for Dianxiaomi to return crawl results. Do not click Crawl and One-Click Publish (`采集并一键发布`).
5. If a result modal or overlay appears after the crawl finishes, record the result and close the modal first. Otherwise the row-level Claim button (`认领`) may be blocked and not clickable. Ant modal text may remain in the DOM after close; verify overlay visibility with computed style or bounding rect instead of searching body text alone.
6. If the page asks for platform, store, crawl method, or group selection, continue only when the user has explicitly authorized the corresponding choice. If authorization is missing or the option meaning is unclear, stop and ask the user to confirm.
7. If the user asks to "stop after crawling" or only asks to complete the crawl, record the crawl result and edit link, then stop.
8. If the product must be found through the acquisition list search, use a distinctive product-title keyword from `raw-product.json` or the crawl result. Do not use `offerId` search for this workflow. React input boxes may not respond to direct value assignment; click the input first, type the title keyword through real keyboard events, then press Enter or click the search button.
9. If the user asks to claim the crawled product, use `dianxiaomi-claim-crawl-product`: click the target row's Claim button (`认领`) in the data acquisition list and select the target store.
10. If the user asks to continue listing or editing after a successful SHEIN claim, open the claimed product's direct backend edit route when its product id is known, for example `https://www.dianxiaomi.com/web/sheinProduct/edit?id=<productId>`. Do not open the SHEIN collection box/draft page or click a list Edit tab/button just to enter editing. If the product id is not available, stop and report that the direct edit route cannot be constructed.
11. During editing, use `dianxiaomi-edit-shein-product` for title, description, item number, inventory, supply price, package dimensions, package weight, source URL, size chart, and image workflow. SKU is not required and does not need modification.
12. Prefer saving as a draft or pending publication state. Before official publishing, submitting for review, one-click publishing, or syncing to a platform, list the summary again and wait for explicit user confirmation.

## Operating Boundaries

- Do not directly enter new product pages on platforms such as SHEIN or TikTok to create products manually unless the user explicitly asks to bypass Dianxiaomi crawling.
- Do not enable Auto Claim (`自动认领`), and do not click Crawl and One-Click Publish (`采集并一键发布`), One-Click Publish (`一键发布`), Publish (`发布`), or equivalent final actions unless the user explicitly confirms after seeing the summary.
- Do not guess target store, platform category, logistics template, weight, brand, or infringement risk.
- Do not publish the crawl result directly. Let the user see the crawl/edit summary first.
- Dianxiaomi page fields and buttons are governed by the currently visible Chrome state. Do not hard-code unverified click paths.

## Result Report

After each crawl or edit, return:

- Data source link
- Dianxiaomi crawl result or edit page link
- Product title
- SKU count
- Purchase price and USD sale price formula
- Confirmed fields
- Missing fields and risks requiring human confirmation

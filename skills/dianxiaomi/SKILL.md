---
name: dianxiaomi
description: Teach the AI to operate the Dianxiaomi backend to create, edit, review, and publish product drafts. Use when the user asks to handle cross-border product listing workflows for stores such as TikTok or SHEIN in Dianxiaomi.
---

# Dianxiaomi Operations

Use this skill when the user asks to create, edit, review, or publish product drafts in Dianxiaomi.

## Goal

- Prefer creating or updating review-ready product drafts in Dianxiaomi.
- Official publishing must be explicitly triggered by the user after they review the draft.
- The operation result must return the draft link, target store, product title, SKU count, price information, risk notes, and missing fields.

## Inputs

- Target store, such as a TikTok or SHEIN store name.
- Standard product data, such as a 1688 crawl result, AI-completed product data, or Dianxiaomi import fields.
- Listing mode. Default to creating a draft.

If the product source is 1688 and the user asks to "list it in Dianxiaomi", "crawl it into Dianxiaomi", or handle "the product just crawled", prefer `dianxiaomi-1688-crawl` and submit the 1688 link through the Dianxiaomi data acquisition entry. Do not default to manually creating a new product directly in SHEIN, TikTok, or another platform page.

## Operating Principles

- Do not depend directly on the 1688 page. 1688 product information must first enter the standard product data.
- Do not invent product facts. Mark missing fields as requiring human confirmation.
- Do not publish a product, submit it for review, or execute any final action affecting a live store before user confirmation.
- Stop and let the user handle login, CAPTCHA, insufficient permissions, missing stores, or platform rule blocks.
- Page fields, buttons, and workflows must follow the currently visible Dianxiaomi page state. Do not hard-code unverified click paths.
- If Chrome `domSnapshot()` fails on Dianxiaomi, do not treat it as a page failure. Use a bounded read-only `playwright.evaluate(...)`, screenshot, or visible DOM/CUA read to inspect the current state, then continue from the visible page.

## Draft Creation Flow

Use this direct creation flow only when the user explicitly asks to bypass Dianxiaomi crawling, copy an existing Dianxiaomi product, or the product source is not a 1688 link.

1. Open Dianxiaomi and confirm that the account is logged in.
2. Enter the product publishing or product management entry for the target platform and store.
3. Create a new product draft, or open the existing draft specified by the user.
4. Fill in basic information: title, category, brand, description, selling points, and product attributes.
5. Fill in SKU information: specification name, specification value, SKU code, inventory, purchase price, sale price, and SKU image.
6. Handle images: main images, SKU images, detail images, Chinese watermark images, and images with infringement risk that require human handling.
7. Save as a draft.
8. Return the draft result summary.

## Publish Confirmation Flow

If the user asks to publish a draft, list these items again before publishing:

- Store
- Product title
- SKU count
- Sale price range
- Draft link
- Risk notes
- Missing fields

Execute publish, submit for review, or equivalent final actions in Dianxiaomi only after the user explicitly confirms publishing.

## Companion Skills

- Use `dianxiaomi-claim-crawl-product` when a product in the Dianxiaomi data acquisition list must be claimed into a store collection box.
- Use `dianxiaomi-edit-shein-product` for the full SHEIN edit workflow, including local price calculation, title generation, and description generation.

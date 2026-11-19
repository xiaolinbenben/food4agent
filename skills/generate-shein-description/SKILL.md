---
name: generate-shein-description
description: Generate an English SHEIN product description directly from 1688 crawled product information and product image URLs. Use when editing a Dianxiaomi SHEIN crawled product to convert the crawled description into publishable English product copy.
---

# Generate SHEIN Product Description

Use this skill for the agent to generate a SHEIN product description directly from the current product directory's `raw-product.json` for the description field on the Dianxiaomi edit page. Do not call scripts, external APIs, or extra generation services.

## Input

- `raw-product.json` in the current product directory.
- Prefer product facts from `structured.title.primary`, `structured.description`, `structured.attributes.items`, `structured.sku.items`, `structured.pricing`, and `raw.text`.
- If `structured.title.primary` is clearly a store name, company name, or non-product title, such as one containing `有限公司`, `旗舰店`, or `专营店`, or if it lacks category/style terms, do not treat it as a product fact. Instead use the most product-title-like candidate from `structured.title.candidates`, `source.page_title`, detail text, and image facts.
- Product images come only from URLs in the JSON, in this priority order: `structured.images.main_images`, `structured.images.sku_images`, `structured.images.detail_images`, `structured.images.candidates`.
- Treat `quality.missing_fields` as authoritative for missing fields. Do not generate deterministic descriptions from missing fields.
- If image URLs are accessible, use the images to judge visible information such as product category, style, color, and fit.
- If image URLs are not accessible, generate only from JSON text fields, do not guess visual details, and mark in the task report that image information was not confirmed.
- Do not handle image compliance; images are reviewed by humans.

## Generation Requirements

- Output an English description.
- Do not invent brands, authorization, material percentages, origin, functions, or facts that were not crawled.
- Preserve confirmed or image-visible key attributes: color, fabric, fit, pant length, waist type, season, and style.
- Avoid medical, body-shaping, exaggerated, and infringing claims.
- Output plain text or simple paragraphs suitable for pasting into the Dianxiaomi description field. Do not return an explanation.
- The copy should be clear, accurate, natural, and consistent with SHEIN product description style.

## Suggested Prompt

```text
You are writing a SHEIN product description from verified source data.
Write clear English product copy for shoppers.
Do not invent brand names, certifications, materials, sizes, origins, or functions.
Avoid banned, exaggerated, medical, body-shaping, or infringing claims.
Return description only.

Source data:
{product facts from raw-product.json, original 1688 title/description/attribute text, and observations from accessible product image URLs}
```

## Fill Dianxiaomi

After generation, return to the Dianxiaomi edit page and fill the description into the corresponding description field. Explain the data source before and after filling. If image URLs were not accessible, state that the description did not use visual confirmation.

---
name: generate-shein-title
description: Generate an English SHEIN golden title directly from 1688 crawled product information and product image URLs, producing an all-purpose high-exposure SEO title while staying accurate to verified product facts. Use when editing a Dianxiaomi SHEIN crawled product to convert the Chinese crawled title into a publishable English product title.
---

# Generate SHEIN Product Title

Use this skill for the agent to generate a SHEIN golden title directly from the current product directory's `raw-product.json`. Do not call scripts, external APIs, or extra generation services.

## Input

- Default to reading `raw-product.json` in the current product directory.
- Prefer product facts from `structured.title.primary`, `structured.description`, `structured.attributes.items`, `structured.sku.items`, `structured.pricing`, and `raw.text`.
- If `structured.title.primary` is clearly a store name, company name, or non-product title, such as one containing `有限公司`, `旗舰店`, or `专营店`, or if it lacks category/style terms, do not use it to generate the title. Instead use the most product-title-like candidate from `structured.title.candidates`, `source.page_title`, detail text, and image facts.
- Product images come only from URLs in the JSON, in this priority order: `structured.images.main_images`, `structured.images.sku_images`, `structured.images.detail_images`, `structured.images.candidates`.
- Treat `quality.missing_fields` as authoritative for missing fields. Do not generate deterministic selling points from missing fields.
- If image URLs are accessible, use the images to judge visible information such as product category, style, color, and fit.
- If image URLs are not accessible, generate only from JSON text fields, do not guess visual details, and mark in the task report that image information was not confirmed.
- Do not make image compliance judgments; images are reviewed by humans.

## Generation Requirements

- Output one English SHEIN golden title and return only the title text, with no explanation.
- Do not invent brands, authorization, material percentages, origin, functions, or facts that were not crawled.
- Do not keep Chinese size recommendations.
- The title must target an all-purpose high-exposure SHEIN SEO style: lead with the strongest searchable product category keyword, then layer the highest-value verified attributes buyers actually search for.
- Prefer natural marketplace search terms over literal 1688 translations. Use terms buyers would search, such as the confirmed category, garment type, silhouette, fit, sleeve, neckline, material, pattern, season, and occasion.
- Order keywords by commercial search value and readability: category first, then core style/silhouette, then fit/design details, then material/pattern, then season/occasion when confirmed.
- Keep the title dense with useful keywords but still natural and readable; avoid keyword stuffing, repeated synonyms, awkward lists, and low-value filler words.
- Focus the title on category, style, fit, material, and applicable season; use only confirmed or image-visible information.
- Prefer broad-traffic buyer vocabulary that can cover search, recommendation, and conversion scenarios, but never add unverified trend terms just for exposure.
- Do not use exaggerated words, infringing terms, or platform-prohibited terms.
- The copy should be clear, accurate, natural, SEO-strong, and consistent with SHEIN product title style.

## Suggested Prompt

```text
You are writing a SHEIN golden title from verified source data.
Write one English SHEIN title optimized for SEO, exposure, search intent, and conversion.
Start with the strongest searchable product category keyword, then include the most valuable verified buyer terms in this order when supported by the data or images: core style or silhouette, fit, sleeve or neckline, material or fabric, pattern, season, and occasion.
Use natural high-traffic marketplace wording, not literal awkward translations.
Keep the title dense with useful keywords but still readable and commercially natural.
Avoid keyword stuffing, repeated synonyms, vague filler words, and unverified trend terms.
Do not invent brand names, certifications, materials, sizes, or functions.
Avoid banned, exaggerated, or infringing terms.
Return title only.

Source data:
{product facts from raw-product.json, original 1688 title/description/attribute text, and observations from accessible product image URLs}
```

## Fill Dianxiaomi

After generation, return to the Dianxiaomi edit page and fill the title into the `产品标题` field. Explain the data source before and after filling. If image URLs were not accessible, state that the title did not use visual confirmation.

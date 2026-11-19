# Automatic Listing On Ozon

Use this reference for API/XLS upload, product card automation, category mapping, required characteristics, import status checks, and moderation fixes.

## Mental Model

Ozon upload automation is not just "generate a listing." It is a structured PDP creation pipeline:

```text
source product data
-> choose category and product type
-> retrieve/fill mandatory and filter characteristics
-> normalize dictionary values and units
-> build name, description, media, price, currency, stock
-> upload by API/XLS
-> poll import status
-> resolve moderation and "requires improvement" errors
-> monitor search visibility and sales metrics
```

## Official Constraints To Preserve

- Products can be uploaded manually, via XLS/template, online tables, or API.
- For many products, brand certificates or category access documents may be required before upload.
- Products are sent to moderation after upload; official docs describe moderation as typically 1-3 business days for upload methods, while API docs note that new product moderation can take up to about three days.
- API upload uses `POST /v2/product/import`; Ozon docs state that up to 100 products can be submitted at a time.
- Upload status can be checked with `POST /v1/product/import/info`.
- Seller API can also update prices, stock, and product information, but product changes may pass moderation and appear after a delay.
- Current API docs should be checked for endpoint version changes before writing production code.

## Required Data Groups

Ask for or infer these fields before designing an upload workflow:

| Group | Fields | Ozon-specific notes |
| --- | --- | --- |
| Identity | `offer_id`, vendor code, barcode if applicable, existing Ozon ID/SKU | `offer_id` should uniquely identify product variants in the seller's system. |
| Category | category path, category ID, type ID | Wrong category can cause moderation rejection and affects commission, characteristics, and search position. |
| Core PDP | name, brand/vendor, model, description, images | Some categories auto-generate product names; do not force a title formula blindly. |
| Characteristics | mandatory characteristics, filter/navigation fields, dictionary values, units | Required fields must be complete; characteristics affect filters and search. |
| Variant logic | color, size, volume, pack count, model name / merge field | Same model variants should be merged only when Ozon category rules support it. |
| Commerce | price, currency, minimum price, VAT/tax assumptions, promotion constraints | Do not hard-code fees; current rates vary by seller country, category, and scheme. |
| Fulfillment | stock, warehouse, sales scheme, dimensions/weight | Stock and delivery scheme affect availability and conversion. |
| Compliance | brand documents, category access, certificates, restricted goods checks | Required before upload for some brands/categories. |

## Category And Type

Do not treat category selection as a UI detail. Ozon states that category determines sales commissions, product characteristics, and search-result position. Products with the wrong category can be rejected during moderation.

Workflow:

1. Identify product function and buyer use case.
2. Find candidate Ozon category/type from seller account, template, or API.
3. Compare required and filter characteristics for each candidate.
4. Prefer the category where the product can truthfully fill the strongest required/filter attributes.
5. Record category/type confidence and unresolved ambiguities.

## Characteristics

Ozon characteristics are central to discovery:

- Required characteristics are mandatory for moderation.
- Type is a main navigation attribute in many categories.
- Category-specific attributes can determine where a PDP appears on the site.
- Characteristics are indexed for search and used for filters.
- Unrelated search keys or irrelevant characteristic values can lower search/category position.
- Values may have limits; exceeding them can move a product to a "requires improvement" state.

Automation checks:

```text
required_fields_present
dictionary_values_valid
units_match_expected_unit
field_value_limits_respected
filter_attributes_populated
variant_merge_fields_consistent
no_irrelevant_search_keys
```

## Product Name

Default product name pattern from Ozon API docs:

```text
type + brand/manufacturer + model + vendor product ID if applicable + key feature such as color
```

But do not blindly apply it:

- Some categories have automatically generated names.
- The product type in the name must match selected type.
- Include only important characteristics.
- Avoid links, HTML, unsupported symbols, keyword stuffing, and unrelated terms.
- For categories with auto naming, prioritize correct characteristics over manual title tricks.

## Description

Description should help the buyer understand purpose, features, advantages, materials, and use cases.

Avoid:

- Contact details, links, social accounts.
- Price, discounts, "sale", "only today", and advertising claims.
- Large keyword lists.
- Unsupported superlatives such as "best", "top", "leader".
- Words implying copies, replicas, fakes, or "1:1".
- Product variants that are not actually in the PDP.

Important: if core characteristics are only written in description and not in structured fields, the product may not enter relevant filters and can be harder to find.

## Images

When checking image readiness:

- Confirm Ozon-supported file format, resolution, aspect ratio, and size in current docs.
- Watch category-specific aspect ratio expectations, especially clothing/footwear/accessories.
- Avoid price/discount/contact text on images.
- Avoid low-quality, blurry, black-and-white, irrelevant, copied, violent, or prohibited content.
- Some categories may not qualify for sale without images.

## API Status Loop

For API listing tasks, recommend a status-aware flow:

```text
1. Build product payloads in batches within current API limits.
2. Submit import.
3. Store task/import ID.
4. Poll import info.
5. Parse errors by product and field.
6. Classify errors:
   - missing required characteristic
   - invalid dictionary value
   - wrong category/type
   - document or brand access issue
   - image/content violation
   - duplicate/merge issue
   - price/currency/stock issue
7. Correct source data, not only the generated payload.
8. Retry only changed products.
9. After moderation, check product visibility/indexing and search diagnostics.
```

## Typical Bad AI Advice To Correct

- "Just write a longer SEO title": Ozon may auto-generate names in some categories, and structured characteristics matter more.
- "Put all keywords in the description": Ozon warns against adding all search keys to description/content.
- "Use popular keywords even if broad": Irrelevant search keys and values can lower position.
- "Upload first, fix later": missing category access, required characteristics, or documents can block moderation and create rework.
- "Treat every color as a separate unrelated listing": variants may need merge logic through model/merge attributes depending on category.

## Useful Output Templates

### Upload Field Mapping

| Source field | Ozon field | Required? | Transformation | Risk | Action |
| --- | --- | --- | --- | --- | --- |

### Moderation Error Triage

| Product | Error | Likely cause | Ozon-specific fix | Retry needed? |
| --- | --- | --- | --- | --- |

### Category Decision Table

| Candidate category/type | Required fields fit | Search/filter fit | Commission/logistics impact | Risk | Recommendation |
| --- | --- | --- | --- | --- | --- |

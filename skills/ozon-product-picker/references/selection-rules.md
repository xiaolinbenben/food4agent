# Selection rules

Use this skill when the task is: find the best Ozon product for a text query or Ozon URL and explain the choice briefly.

## Default ranking priorities
1. Product quality signals:
   - higher rating
   - more reviews
2. Price sanity:
   - lower price among comparable results
   - good-price / discount signals
3. Seller trust:
   - seller rating
   - seller order volume / review volume when available
4. Convenience:
   - installment / availability / notable marketing labels

## Practical output shape
Return:
- 1 best option
- 1-2 alternatives
- short explanation in plain Russian

## Important caveats
- Actor search results can contain near-duplicates by color or upholstery.
- Some products expose price only through the active variant, not top-level fields.
- If the query is broad, explain the tradeoff: cheapest vs most reviewed vs strongest seller.
- Do not claim exact delivery speed unless the dataset clearly includes it.
- If important fields are missing, say so.

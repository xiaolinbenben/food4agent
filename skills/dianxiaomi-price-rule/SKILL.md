---
name: dianxiaomi-price-rule
description: Calculate the USD sale price that should be entered when listing a Dianxiaomi product based on the purchase price obtained from 1688. Use when pricing, completing sale prices, or explaining pricing rules for Dianxiaomi product drafts.
---

# Dianxiaomi Sale Price Rule

Use this skill when the user needs to fill in a Dianxiaomi sale price based on 1688 product information.

## Input

- The purchase price comes from the 1688 product price.
- The purchase price unit is CNY.

## Output

- The output is the sale price to enter for the Dianxiaomi listing.
- The sale price unit is USD.

## Calculation Rule

Use the rule given by the owner:

```text
base price = 1688 purchase price * 8 / 6.5
Dianxiaomi USD sale price = integer part of base price changed to .99
```

Example:

```text
1688 purchase price: 35 CNY
base price: 35 * 8 / 6.5 = 43.076923...
Dianxiaomi USD sale price: 43.99 USD
```

## Constraints

- Calculate the sale price only with the formula above.
- The decimal rule is fixed to `.99`; do not add other decimal strategies, discounts, shipping, platform commission, profit markup, or promotional pricing.
- If the 1688 product has multiple SKU purchase prices, calculate the sale price separately for each SKU purchase price.
- In Dianxiaomi, modify the automatically calculated `供货价(USD)` / price field after crawling. If the page also has a promotional price field, fill it only when the user explicitly asks.

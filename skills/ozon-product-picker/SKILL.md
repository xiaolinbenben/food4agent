---
name: ozon-product-picker
description: Pick the best Ozon product for a user query or Ozon URL via the Apify
  actor zen-studio/ozon-scraper-pro. Use when the request is about finding, comparing,
  or choosing products on Ozon/Ozon.ru/Озон/Озоне, especially Russian phrasing like
  «найди в Ozon товар», «найди в Озоне», «поищи на Озоне», «подбери товар в Озоне»,
  «подбери на Ozon», «сравни товары на Ozon», «что лучше взять на Озоне», «посмотри
  на Ozon и выбери лучший вариант». Search Ozon, compare multiple product candidates,
  weigh price, rating, review count, seller quality, and practical trust signals,
  then return one best option plus 1-2 backups with a short rationale in Russian.
version: 1.0.0
author: web3blind / Hermes Agent
license: MIT
metadata:
  hermes:
    tags:
    - ozon-product-picker
    related_skills: []
---
# ozon-product-picker

Use this skill to find and compare Ozon products through Apify when the user asks for something like:
- "найди лучший товар на Ozon"
- "подбери лучший вариант по запросу"
- "сравни несколько кресел/ноутбуков/товаров на Ozon"
- "посмотри карточку Ozon и скажи, стоит ли брать"

## Workflow

1. Make sure `APIFY_TOKEN` is available either in the environment or in `skills/ozon-product-picker/.env`.
2. Run `scripts/run_ozon_product_picker.py` with either:
   - `--query "..."`
   - `--url "https://www.ozon.ru/..."`
3. Prefer `--seller-details` when seller trust matters.
4. Read the ranked output.
5. Return:
   - best option
   - 1-2 alternatives
   - short explanation of why the best option won
6. If the result set is noisy, say so and narrow the query on the next pass.

## Commands

### Search by query

```bash
python3 skills/ozon-product-picker/scripts/run_ozon_product_picker.py \
  --query "кресло-кровать" \
  --max-results 10 \
  --top 3 \
  --seller-details
```

### Search by Ozon URL

```bash
python3 skills/ozon-product-picker/scripts/run_ozon_product_picker.py \
  --url "https://www.ozon.ru/category/kresla-15019/" \
  --max-results 10 \
  --top 3 \
  --seller-details
```

### JSON mode

```bash
python3 skills/ozon-product-picker/scripts/run_ozon_product_picker.py \
  --query "кресло-кровать" \
  --json
```

## How ranking works

The script ranks products by a simple practical score:
- product rating
- review count
- relative price among returned candidates
- seller rating
- seller order/review volume when available
- price/discount signals like `hasGoodPrice`, `hasPriceDecreased`, discount labels, installment

Read `references/selection-rules.md` when you need the concise ranking policy.

## Output policy

Keep the final answer short and useful:
- mention price, rating, review count, seller, and the main reason
- do not dump raw JSON unless the user asked
- if several results are essentially duplicates, say that directly
- if the broad cheapest option looks much weaker, prefer the more balanced option and explain the tradeoff

## Caveats

- Ozon often returns multiple color variants as separate strong candidates.
- Some cards expose real price only on the active variant.
- The actor can take noticeable time.
- If core fields are missing, say that confidence is lower.



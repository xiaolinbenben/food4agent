#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

DEFAULT_API_URL = "https://api.apify.com/v2/acts/zen-studio~ozon-scraper-pro/run-sync-get-dataset-items"
API_URL = os.getenv("APIFY_OZON_ACTOR_URL", DEFAULT_API_URL)
TIMEOUT_SECONDS = 900


@dataclass
class RankedItem:
    title: str
    url: str
    price: int | None
    rating: float | None
    review_count: int
    seller_name: str | None
    seller_rating: float | None
    seller_orders: int | None
    score: float
    reasons: list[str]
    raw: dict[str, Any]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pick the best Ozon products via Apify actor.")
    parser.add_argument("--query", action="append", default=[], help="Search query. Repeatable.")
    parser.add_argument("--url", action="append", default=[], help="Ozon product/search/category URL. Repeatable.")
    parser.add_argument("--max-results", type=int, default=10, help="Max products per query/URL.")
    parser.add_argument("--top", type=int, default=3, help="How many ranked results to return.")
    parser.add_argument("--seller-details", action="store_true", help="Fetch seller profile details.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of human-readable text.")
    parser.add_argument("--language", default="ru", help="Actor language, default ru.")
    parser.add_argument("--currency", default="RUB", help="Actor currency, default RUB.")
    return parser.parse_args()


def load_dotenv() -> None:
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def require_token() -> str:
    load_dotenv()
    token = os.getenv("APIFY_TOKEN")
    if not token:
        raise SystemExit("APIFY_TOKEN is required")
    return token


def compact_text(value: str) -> str:
    return value.replace("\u202f", " ").replace("\xa0", " ").strip()


def parse_number_text(value: str | None) -> float | None:
    if value is None:
        return None
    text = compact_text(str(value)).lower()
    if not text:
        return None
    compact = re.sub(r"\s+", "", text)
    match = re.search(r"(\d+(?:[.,]\d+)?)\s*([kкmм])?", compact)
    if not match:
        digits = re.sub(r"\D", "", compact)
        return float(digits) if digits else None
    number = float(match.group(1).replace(",", "."))
    suffix = match.group(2)
    if suffix in {"k", "к"}:
        number *= 1000
    elif suffix in {"m", "м"}:
        number *= 1000000
    return number


def parse_price(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(round(value))
    number = parse_number_text(str(value))
    return int(round(number)) if number is not None else None


def extract_active_variant(item: dict[str, Any]) -> dict[str, Any] | None:
    for group in item.get("variants") or []:
        for option in group.get("options") or []:
            if option.get("active"):
                return option
    return None


def extract_price(item: dict[str, Any]) -> int | None:
    for key in ("priceDecimal", "price", "cardPriceDecimal", "cardPrice"):
        price = parse_price(item.get(key))
        if price:
            return price
    active_variant = extract_active_variant(item)
    if active_variant:
        for key in ("price", "formattedPrice", "originalPrice"):
            price = parse_price(active_variant.get(key))
            if price:
                return price
    return parse_price(item.get("bestSellerPrice"))


def extract_seller_orders(item: dict[str, Any]) -> int | None:
    seller_profile = item.get("sellerProfile") or {}
    for badge in seller_profile.get("badges") or []:
        text = badge.get("text")
        if not text:
            continue
        normalized = compact_text(str(text)).lower()
        if "заказ" in normalized:
            value = parse_number_text(normalized)
            return int(round(value)) if value is not None else None
    return None


def extract_seller_review_volume(item: dict[str, Any]) -> int | None:
    seller_profile = item.get("sellerProfile") or {}
    for badge in seller_profile.get("badges") or []:
        text = badge.get("text")
        if not text:
            continue
        normalized = compact_text(str(text)).lower()
        if "отзыв" in normalized:
            value = parse_number_text(normalized)
            return int(round(value)) if value is not None else None
    return None


def collect_reason(item: dict[str, Any], price: int | None, seller_orders: int | None) -> list[str]:
    reasons: list[str] = []
    rating = item.get("rating")
    reviews = int(item.get("reviewCount") or 0)
    seller = item.get("seller") or {}
    if rating is not None:
        reasons.append(f"рейтинг {rating}")
    if reviews:
        reasons.append(f"{reviews} отзывов")
    if price is not None:
        reasons.append(f"цена около {price} ₽")
    if seller.get("rating") is not None:
        reasons.append(f"продавец {seller.get('name') or 'без имени'} с рейтингом {seller.get('rating')}")
    if seller_orders:
        reasons.append(f"у продавца около {seller_orders} заказов")
    if item.get("hasGoodPrice"):
        reasons.append("есть метка «Цена что надо» или признак выгодной цены")
    if item.get("hasPriceDecreased"):
        reasons.append("цена снижалась")
    labels = item.get("marketingLabels") or []
    if labels:
        reasons.append("метки: " + ", ".join(labels[:2]))
    return reasons


def score_items(items: list[dict[str, Any]]) -> list[RankedItem]:
    prices = [extract_price(item) for item in items]
    price_values = [value for value in prices if value is not None]
    min_price = min(price_values) if price_values else None
    max_price = max(price_values) if price_values else None
    span = (max_price - min_price) if min_price is not None and max_price is not None else None

    ranked: list[RankedItem] = []
    for item in items:
        price = extract_price(item)
        rating = item.get("rating")
        reviews = int(item.get("reviewCount") or 0)
        seller = item.get("seller") or {}
        seller_rating = seller.get("rating")
        seller_orders = extract_seller_orders(item)
        seller_reviews = extract_seller_review_volume(item)

        score = 0.0
        reasons: list[str] = []

        if rating is not None:
            score += (float(rating) / 5.0) * 45.0
            if float(rating) < 4.6:
                score -= 6.0
        if reviews:
            score += min(math.log10(reviews + 1) / 4.0, 1.0) * 22.0
            if reviews < 50:
                score -= 2.0
        if price is not None and min_price is not None and max_price is not None:
            if span and span > 0:
                score += ((max_price - price) / span) * 12.0
            else:
                score += 6.0
        elif price is not None:
            score += 6.0
        if seller_rating is not None:
            score += (float(seller_rating) / 5.0) * 8.0
        if seller_orders:
            score += min(math.log10(seller_orders + 1) / 6.0, 1.0) * 5.0
        if seller_reviews:
            score += min(math.log10(seller_reviews + 1) / 6.0, 1.0) * 3.0
        if item.get("hasGoodPrice"):
            score += 2.0
        if item.get("hasPriceDecreased"):
            score += 1.0
        if item.get("discount"):
            score += 1.0
        if item.get("installment"):
            score += 0.5
        active_variant = extract_active_variant(item)
        if active_variant and active_variant.get("availability") == "inStock":
            score += 1.0
        if item.get("isAuthentic"):
            score += 1.0

        reasons = collect_reason(item, price, seller_orders)
        ranked.append(
            RankedItem(
                title=item.get("title") or "Без названия",
                url=item.get("url") or "",
                price=price,
                rating=float(rating) if rating is not None else None,
                review_count=reviews,
                seller_name=seller.get("name"),
                seller_rating=float(seller_rating) if seller_rating is not None else None,
                seller_orders=seller_orders,
                score=round(score, 2),
                reasons=reasons,
                raw=item,
            )
        )

    ranked.sort(key=lambda item: (-item.score, item.price is None, item.price or 10**12, -item.review_count))
    return ranked


def fetch_items(token: str, *, queries: list[str], urls: list[str], max_results: int, seller_details: bool, language: str, currency: str) -> list[dict[str, Any]]:
    payload: dict[str, Any] = {
        "maxResults": max_results,
        "includeSellerDetails": seller_details,
        "language": language,
        "currency": currency,
    }
    if queries:
        payload["queries"] = queries
    if urls:
        payload["urls"] = urls
    response = requests.post(API_URL, params={"token": token}, json=payload, timeout=TIMEOUT_SECONDS)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, list):
        raise RuntimeError("Unexpected actor response")
    return data


def build_output(ranked: list[RankedItem], top: int) -> dict[str, Any]:
    selected = ranked[:top]
    best = selected[0] if selected else None
    return {
        "best": serialize_ranked(best) if best else None,
        "alternatives": [serialize_ranked(item) for item in selected[1:]],
        "count": len(ranked),
    }


def serialize_ranked(item: RankedItem | None) -> dict[str, Any] | None:
    if item is None:
        return None
    return {
        "title": item.title,
        "url": item.url,
        "price": item.price,
        "rating": item.rating,
        "reviewCount": item.review_count,
        "seller": {
            "name": item.seller_name,
            "rating": item.seller_rating,
            "orders": item.seller_orders,
        },
        "score": item.score,
        "reasons": item.reasons,
    }


def print_human(output: dict[str, Any]) -> None:
    best = output.get("best")
    if not best:
        print("Ничего не найдено")
        return
    print("Лучший вариант:")
    print(f"- {best['title']}")
    print(f"- Ссылка: {best['url']}")
    print(f"- Цена: {best.get('price') or 'н/д'} ₽")
    print(f"- Рейтинг: {best.get('rating') or 'н/д'}")
    print(f"- Отзывы: {best.get('reviewCount') or 0}")
    seller = best.get("seller") or {}
    if seller.get("name"):
        print(f"- Продавец: {seller['name']} ({seller.get('rating') or 'н/д'})")
    print("- Почему:")
    for reason in best.get("reasons") or []:
        print(f"  - {reason}")
    alternatives = output.get("alternatives") or []
    if alternatives:
        print("\nЗапасные варианты:")
        for item in alternatives:
            print(f"- {item['title']} — {item.get('price') or 'н/д'} ₽, рейтинг {item.get('rating') or 'н/д'}, отзывов {item.get('reviewCount') or 0}")
            print(f"  {item['url']}")


def main() -> None:
    args = parse_args()
    if not args.query and not args.url:
        raise SystemExit("Add at least one --query or --url")
    token = require_token()
    items = fetch_items(
        token,
        queries=args.query,
        urls=args.url,
        max_results=args.max_results,
        seller_details=args.seller_details,
        language=args.language,
        currency=args.currency,
    )
    ranked = score_items(items)
    output = build_output(ranked, args.top)
    if args.json:
        json.dump(output, sys.stdout, ensure_ascii=False, indent=2)
        print()
        return
    print_human(output)


if __name__ == "__main__":
    main()

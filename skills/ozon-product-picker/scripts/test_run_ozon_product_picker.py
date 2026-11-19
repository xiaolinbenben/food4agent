#!/usr/bin/env python3
from run_ozon_product_picker import extract_price, parse_number_text, score_items


def test_parse_number_text() -> None:
    assert parse_number_text("31,2 K отзывов") == 31200
    assert parse_number_text("97,4 K заказов") == 97400
    assert parse_number_text("10 561 ₽") == 10561


def test_extract_price_from_active_variant() -> None:
    item = {
        "price": None,
        "priceDecimal": None,
        "variants": [
            {
                "options": [
                    {"active": False, "price": 7777},
                    {"active": True, "price": 5555},
                ]
            }
        ],
    }
    assert extract_price(item) == 5555


def test_score_prefers_social_proof_when_price_reasonable() -> None:
    items = [
        {
            "title": "Cheap weak item",
            "url": "https://example.com/1",
            "priceDecimal": 7000,
            "rating": 4.1,
            "reviewCount": 12,
            "seller": {"name": "Seller A", "rating": 4.1},
            "sellerProfile": {"badges": [{"text": "200 заказов"}]},
        },
        {
            "title": "Balanced strong item",
            "url": "https://example.com/2",
            "priceDecimal": 9000,
            "rating": 4.8,
            "reviewCount": 800,
            "seller": {"name": "Seller B", "rating": 4.8},
            "sellerProfile": {"badges": [{"text": "20 K заказов"}, {"text": "5 K отзывов"}]},
            "hasGoodPrice": True,
        },
    ]
    ranked = score_items(items)
    assert ranked[0].title == "Balanced strong item"


if __name__ == "__main__":
    test_parse_number_text()
    test_extract_price_from_active_variant()
    test_score_prefers_social_proof_when_price_reasonable()
    print("OK")

import importlib.util
import urllib.error
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "sea_product_agent.py"
SPEC = importlib.util.spec_from_file_location("sea_product_agent", MODULE_PATH)
sea_product_agent = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(sea_product_agent)


REAL_NEWS_TITLE = (
    "Struggling to Find the Perfect Skincare Routine for Oily Skin? "
    "These TikTok-Viral Products Are Worth It - E! News"
)
REAL_1688_ITEM = {
    "rank": 2,
    "offer_id": "640320036702",
    "title": "美容院专用护肤品套装化妆品全套正品洗面奶爽肤水按摩膏乳液水乳",
    "seller_name": "广州市蝶澜化妆品有限公司",
    "price_min": 23,
    "price_text": "¥23",
    "sales_text": "9400+件",
}


def test_match_score_real_titles_reaches_full_overlap():
    score = sea_product_agent._match_score(
        REAL_NEWS_TITLE,
        "TikTok skincare routine products for oily skin",
        "beauty",
    )
    assert score == 1.0


def test_coerce_product_source_real_1688_item_defaults_consistently():
    product = sea_product_agent._coerce_product_source(
        REAL_1688_ITEM,
        "beauty",
        "ID",
        "custom_source",
    )

    assert product == {
        "name": "美容院专用护肤品套装化妆品全套正品洗面奶爽肤水按摩膏乳液水乳",
        "nameEn": "美容院专用护肤品套装化妆品全套正品洗面奶爽肤水按摩膏乳液水乳",
        "category": "beauty",
        "country": "ID",
        "imageUrl": None,
        "price": None,
        "salesVolume": 0,
        "engagementProxy": 0,
        "salesGrowthRate": 0,
        "sentimentScore": 60,
        "searchIndex": 35,
        "searchGrowthRate": 35,
        "tags": ["beauty", "custom_source"],
        "salesSource": "custom_source",
        "trustLevel": "verified",
        "evidenceLinks": [],
        "source": "agent:custom_source",
    }


def test_score_product_locks_expected_baseline_values():
    scored = sea_product_agent._score_product(
        {
            "name": "Unlocking the glow with my LANEIGE Indonesia essentials",
            "price": 14.99,
            "salesVolume": 15400,
            "searchGrowthRate": 61,
            "sentimentScore": 77,
            "trustLevel": sea_product_agent.SourceTrust.OFFICIAL.value,
            "matched1688": REAL_1688_ITEM,
        },
        {
            "amazon_price": 14.99,
            "amazon_count": 4,
            "supply_price_cny": 23,
            "supply_count": 20,
            "news_count": 10,
        },
    )

    assert scored["competitionScore"] == 69
    assert scored["potentialScore"] == 92
    assert scored["searchIndex"] == 61
    assert scored["gmv"] == 230846.0
    assert scored["priceMin"] == 12.74
    assert scored["priceMax"] == 17.24
    assert scored["sellerCount"] == 24
    assert scored["isHot"] is True
    assert scored["isTrending"] is True


def test_score_product_applies_proxy_penalty():
    benchmark = {
        "amazon_price": 14.99,
        "amazon_count": 4,
        "supply_price_cny": 23,
        "supply_count": 20,
        "news_count": 10,
    }
    official = sea_product_agent._score_product(
        {
            "name": "Proxy penalty baseline",
            "salesVolume": 15400,
            "searchGrowthRate": 61,
            "sentimentScore": 77,
            "price": 14.99,
            "trustLevel": sea_product_agent.SourceTrust.OFFICIAL.value,
            "matched1688": REAL_1688_ITEM,
        },
        benchmark,
    )
    proxy = sea_product_agent._score_product(
        {
            "name": "Proxy penalty baseline",
            "engagementProxy": 15400,
            "searchGrowthRate": 61,
            "sentimentScore": 77,
            "price": 14.99,
            "trustLevel": sea_product_agent.SourceTrust.PROXY.value,
            "matched1688": REAL_1688_ITEM,
        },
        benchmark,
    )

    assert proxy["potentialScore"] < official["potentialScore"]


def test_score_product_uses_default_margin_when_cost_unknown():
    scored = sea_product_agent._score_product(
        {
            "name": "Indonesia skincare routine",
            "price": 12.0,
            "salesVolume": 900,
            "searchGrowthRate": 20,
            "sentimentScore": 60,
        },
        {
            "amazon_price": 12.0,
            "amazon_count": 2,
            "supply_price_cny": None,
            "supply_count": 2,
            "news_count": 0,
        },
    )

    assert scored["competitionScore"] == 90
    assert scored["potentialScore"] == 45
    assert scored["searchIndex"] == 20


def test_build_top_picks_prefers_verified_over_proxy():
    products = [
        {
            "name": "Proxy A",
            "category": "beauty",
            "country": "ID",
            "trustLevel": sea_product_agent.SourceTrust.PROXY.value,
            "potentialScore": 99,
        },
        {
            "name": "Verified A",
            "category": "fashion",
            "country": "TH",
            "trustLevel": sea_product_agent.SourceTrust.VERIFIED.value,
            "potentialScore": 60,
        },
    ]

    top_picks = sea_product_agent.build_top_picks(products, limit=2)
    assert top_picks[0]["trustLevel"] == sea_product_agent.SourceTrust.VERIFIED.value


def test_build_top_picks_limits_per_segment():
    products = [
        {
            "name": f"Beauty {idx}",
            "category": "beauty",
            "country": "ID",
            "trustLevel": sea_product_agent.SourceTrust.VERIFIED.value,
            "potentialScore": 90 - idx,
        }
        for idx in range(4)
    ]

    top_picks = sea_product_agent.build_top_picks(products, limit=4)
    assert len(top_picks) == 2
    assert all(p["category"] == "beauty" and p["country"] == "ID" for p in top_picks)


def test_generate_why_picked_uses_proxy_copy_when_needed():
    why = sea_product_agent._generate_why_picked(
        {
            "country": "ID",
            "trustLevel": sea_product_agent.SourceTrust.PROXY.value,
            "engagementProxy": 12000,
            "searchGrowthRate": 52,
            "competitionScore": 73,
            "potentialScore": 82,
        }
    )

    assert "互动代理 12,000" in why
    assert "搜索热度增长 +52%" in why


def test_write_to_platform_marks_run_degraded_on_failure(monkeypatch):
    class DummyLogger:
        def warning(self, *args, **kwargs):
            return None

    def fail_urlopen(*args, **kwargs):
        raise urllib.error.URLError("boom")

    monkeypatch.setattr("urllib.request.urlopen", fail_urlopen)
    run_record = {
        "run_id": "test-run",
        "mode": "standard",
        "status": "success",
        "summary": {},
        "products": [],
        "top_picks": [],
    }

    ok = sea_product_agent.write_to_platform(
        run_record, "http://localhost:3000", DummyLogger()
    )

    assert ok is False
    assert run_record["status"] == "degraded"
    assert run_record["summary"]["platform_write_status"] == "degraded"

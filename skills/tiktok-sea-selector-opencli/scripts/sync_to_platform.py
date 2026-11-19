#!/usr/bin/env python3
"""
将 OpenCLI 采集的数据同步到 tiktok-sea-selector Web 平台

用法:
    python sync_to_platform.py \
        --platform-url "http://localhost:3000" \
        --category "美妆" \
        --country "ID"

    # 或从已有报告文件同步
    python sync_to_platform.py \
        --platform-url "http://localhost:3000" \
        --report-file sea_product_report.json
"""

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from typing import Any


# ──────────────────────────────────────────────
# 配置
# ──────────────────────────────────────────────

CATEGORY_MAP = {
    "美妆": "beauty",
    "服饰": "fashion",
    "家居": "home",
    "3C": "electronics",
    "母婴": "baby",
    "beauty": "beauty",
    "fashion": "fashion",
    "home": "home",
    "electronics": "electronics",
    "baby": "baby",
}

# Amazon bestsellers 接受的是分类路径作为位置参数（不是 --category Name）
AMAZON_CATEGORY_PATH = {
    "美妆": "/gp/bestsellers/beauty/",
    "beauty": "/gp/bestsellers/beauty/",
    "服饰": "/gp/bestsellers/apparel/",
    "fashion": "/gp/bestsellers/apparel/",
    "家居": "/gp/bestsellers/home-garden/",
    "home": "/gp/bestsellers/home-garden/",
    "3C": "/gp/bestsellers/electronics/",
    "electronics": "/gp/bestsellers/electronics/",
    "母婴": "/gp/bestsellers/baby/",
    "baby": "/gp/bestsellers/baby/",
}


# ──────────────────────────────────────────────
# 数据采集
# ──────────────────────────────────────────────

def run_opencli(args: list[str], timeout: int = 30) -> Any:
    """执行 opencli 命令"""
    cmd = ["opencli"] + args + ["-f", "json"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode != 0:
            return None
        return json.loads(result.stdout)
    except Exception:
        return None


def fetch_products_for_category(category: str, country: str) -> list[dict]:
    """采集指定品类和国家的产品数据"""
    amazon_path = AMAZON_CATEGORY_PATH.get(category)
    products = []

    # Amazon 畅销榜：分类路径是位置参数，可省略
    bestsellers_args = ["amazon", "bestsellers"]
    if amazon_path:
        bestsellers_args.append(amazon_path)
    bestsellers_args += ["--limit", "20"]
    bestsellers = run_opencli(bestsellers_args)
    if bestsellers and isinstance(bestsellers, list):
        for item in bestsellers:
            if not isinstance(item, dict):
                continue
            products.append({
                "name": item.get("title", "Unknown")[:200],
                "category": CATEGORY_MAP.get(category, "beauty"),
                "country": country,
                "price": _parse_price(item.get("price", "0")),
                "currency": "USD",
                "salesVolume": item.get("reviewCount", 0) * 10,  # 估算
                "growthRate": 0.1,
                "competitionScore": 50,
                "sentimentScore": int(item.get("rating", 4.0) / 5.0 * 100),
                "trendScore": max(0, 100 - (item.get("rank", 50) * 2)),
                "sourceUrl": item.get("url", ""),
                "imageUrl": item.get("image", ""),
                "tags": [category, country, "amazon-bestseller"],
            })
        time.sleep(1)

    # Amazon 飙升榜：分类路径同样是位置参数
    movers_args = ["amazon", "movers-shakers"]
    if amazon_path:
        movers_args.append(amazon_path.replace("/bestsellers/", "/movers-and-shakers/"))
    movers_args += ["--limit", "10"]
    movers = run_opencli(movers_args)
    if movers and isinstance(movers, list):
        for item in movers:
            if not isinstance(item, dict):
                continue
            rank_change = item.get("rankChange", 0)
            products.append({
                "name": item.get("title", "Unknown")[:200],
                "category": CATEGORY_MAP.get(category, "beauty"),
                "country": country,
                "price": _parse_price(item.get("price", "0")),
                "currency": "USD",
                "salesVolume": 0,
                "growthRate": min(rank_change / 100, 5.0),  # 归一化
                "competitionScore": 40,
                "sentimentScore": 65,
                "trendScore": min(rank_change, 100),
                "sourceUrl": item.get("url", ""),
                "imageUrl": item.get("image", ""),
                "tags": [category, country, "amazon-rising"],
            })
        time.sleep(1)

    return products


def _parse_price(price_str: str) -> float:
    """解析价格字符串为浮点数"""
    if isinstance(price_str, (int, float)):
        return float(price_str)
    cleaned = str(price_str).replace("$", "").replace(",", "").strip()
    try:
        return float(cleaned.split("–")[0].split("-")[0])
    except (ValueError, IndexError):
        return 0.0


# ──────────────────────────────────────────────
# 平台 API 调用
# ──────────────────────────────────────────────

class PlatformClient:
    """轻量 stdlib 客户端，避免引入第三方依赖。"""

    def __init__(self, base_url: str, token: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

    def _request(self, method: str, path: str, body: dict | None = None, timeout: int = 30) -> dict:
        url = f"{self.base_url}{path}"
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, headers=self.headers, method=method)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8") or "{}"
            return json.loads(raw)

    def health_check(self) -> bool:
        try:
            self._request("GET", "/api/health", timeout=5)
            return True
        except (urllib.error.URLError, urllib.error.HTTPError, ValueError):
            return False

    def upsert_products(self, products: list[dict]) -> dict:
        """批量写入产品数据"""
        try:
            return self._request(
                "POST",
                "/api/trpc/products.batchUpsert",
                {"json": {"products": products}},
            )
        except Exception as e:
            print(f"  [错误] 写入产品失败: {e}", file=sys.stderr)
            return {"error": str(e)}


# ──────────────────────────────────────────────
# 主流程
# ──────────────────────────────────────────────

def sync_from_report(report_file: str, client: PlatformClient) -> None:
    """从已有报告文件同步数据"""
    with open(report_file, encoding="utf-8") as f:
        report = json.load(f)

    category = report["meta"]["category"]
    countries = report["meta"]["countries"]

    products = []
    for country in countries:
        fetched = fetch_products_for_category(category, country)
        products.extend(fetched)

    print(f"  采集到 {len(products)} 个产品，正在写入平台...")
    result = client.upsert_products(products)
    print(f"  写入结果：{result}")


def sync_live(category: str, country: str, client: PlatformClient) -> None:
    """实时采集并同步数据"""
    print(f"  采集 {category} / {country} 数据...")
    products = fetch_products_for_category(category, country)
    print(f"  采集到 {len(products)} 个产品，正在写入平台...")

    if not products:
        print("  [警告] 未采集到任何产品数据")
        return

    result = client.upsert_products(products)
    print(f"  写入结果：{result}")


def main():
    parser = argparse.ArgumentParser(description="同步选品数据到 tiktok-sea-selector 平台")
    parser.add_argument("--platform-url", default="http://localhost:3000", help="平台 URL")
    parser.add_argument("--token", default=os.environ.get("PLATFORM_SERVICE_TOKEN"), help="服务账号 Token")
    parser.add_argument("--category", help="品类（实时采集模式）")
    parser.add_argument("--country", help="国家代码（实时采集模式）")
    parser.add_argument("--countries", help="多个国家代码，逗号分隔（实时采集模式）")
    parser.add_argument("--categories", help="多个品类，逗号分隔（实时采集模式）")
    parser.add_argument("--report-file", help="从已有报告文件同步")
    args = parser.parse_args()

    client = PlatformClient(args.platform_url, args.token)

    print(f"\n{'='*50}")
    print(f"数据同步到 tiktok-sea-selector 平台")
    print(f"目标：{args.platform_url}")
    print(f"{'='*50}\n")

    # 检查平台连接
    if not client.health_check():
        print(f"[警告] 平台 {args.platform_url} 无法访问，将继续尝试写入...")

    if args.report_file:
        sync_from_report(args.report_file, client)
    elif args.categories and args.countries:
        categories = args.categories.split(",")
        countries = args.countries.split(",")
        for cat in categories:
            for country in countries:
                sync_live(cat, country, client)
                time.sleep(2)
    elif args.category and (args.country or args.countries):
        countries = (args.countries or args.country).split(",")
        for country in countries:
            sync_live(args.category, country, client)
            time.sleep(2)
    else:
        parser.print_help()
        sys.exit(1)

    print("\n✅ 同步完成")


if __name__ == "__main__":
    main()

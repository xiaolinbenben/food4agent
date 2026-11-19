"""Amazon 平台热搜词采集器 (by HomeSafe)"""

import re
import json
import logging
from typing import List, Tuple
from urllib.parse import quote

from bs4 import BeautifulSoup

from src.collector_base import BaseCollector

logger = logging.getLogger(__name__)

# Amazon 主要品类 ID (Best Sellers 分类)
AMAZON_BS_CATEGORIES = [
    ("electronics", "Electronics"),
    ("apparel", "Clothing, Shoes & Jewelry"),
    ("home-garden", "Home & Kitchen"),
    ("toys", "Toys & Games"),
    ("sports", "Sports & Outdoors"),
    ("beauty", "Beauty & Personal Care"),
    ("tools", "Tools & Home Improvement"),
    ("office-products", "Office Products"),
    ("baby-products", "Baby Products"),
    ("pet-supplies", "Pet Supplies"),
]


# Amazon 常用停用词（过滤噪音）
AMAZON_STOP_WORDS = {'the', 'and', 'for', 'with', 'from', 'that', 'this',
                     'out of', 'stars', 'free', 'super', 'new', 'best',
                     'great', 'easy', 'simple', 'top', 'extra', 'plus',
                     'amazon', 'price', 'shop', 'save', 'deal', 'buy',
                     'more', 'less', 'case', 'pack', 'set', 'kit'}


class CollectorAmazon(BaseCollector):
    """Amazon 热搜词采集器"""

    @property
    def platform_name(self) -> str:
        return 'amazon'

    def collect(self) -> List[Tuple[str, str, int, dict]]:
        """从多个数据源采集 Amazon 热搜词"""
        results = []
        domain = self.config.get('amazon', {}).get('domain', 'com')
        seed_keywords = self.config.get('amazon', {}).get('base_seed_keywords',
                                                          ["clothing", "electronics", "home", "beauty", "shoes"])

        # 1. 搜索自动补全 API
        logger.info("[Amazon] 采集搜索自动补全词...")
        for seed in seed_keywords:
            try:
                words = self._get_autocomplete(seed, domain)
                for w in words:
                    results.append((w, 'autocomplete', 1, {'seed': seed}))
            except Exception as e:
                logger.warning(f"[Amazon] 自动补全采集失败 ({seed}): {e}")

        # 2. Best Sellers 页面
        logger.info("[Amazon] 采集 Best Sellers...")
        for cat_id, cat_name in AMAZON_BS_CATEGORIES:
            try:
                words = self._get_bestseller_keywords(cat_id, domain)
                for w, cnt in words:
                    results.append((w, 'bestseller', cnt, {'category': cat_name}))
            except Exception as e:
                logger.warning(f"[Amazon] Best Sellers 采集失败 ({cat_name}): {e}")

        # 3. Movers & Shakers (飙升榜)
        logger.info("[Amazon] 采集 Movers & Shakers...")
        try:
            words = self._get_movers_keywords(domain)
            for w, cnt in words:
                results.append((w, 'movers', cnt, {}))
        except Exception as e:
            logger.warning(f"[Amazon] Movers & Shakers 采集失败: {e}")

        # 去重 + 过滤停用词
        seen = set()
        deduped = []
        for kw, src, freq, meta in results:
            key = kw.strip().lower()
            if key not in seen and key not in AMAZON_STOP_WORDS and len(key) >= 3:
                seen.add(key)
                deduped.append((kw, src, freq, meta))
        logger.info(f"[Amazon] 采集到 {len(deduped)} 个去重关键词")
        return deduped

    def _get_autocomplete(self, keyword: str, domain: str = 'com') -> List[str]:
        """调用 Amazon 搜索自动补全 API"""
        url = "https://completion.amazon.com/api/2017/suggestions"
        # Amazon 自动补全参数
        market_place_map = {
            'com': 'ATVPDKIKX0DER',
            'co.uk': 'A1F83G8C2ARO7P',
            'de': 'A1PA6795UKMFR9',
            'jp': 'A1VC38T8YXB528',
        }
        mid = market_place_map.get(domain, 'ATVPDKIKX0DER')

        params = {
            "mid": mid,
            "alias": "aps",
            "prefix": keyword,
            "limit": 10,
            "suggestion-type": "KEYWORD",
            "site-variant": "desktop",
            "version": "3",
            "plain-mars": "1",
            "client-info": "amazon-search-ui",
        }
        resp = self._request(url, params=params,
                             referer=f"https://www.amazon.{domain}/")
        if not resp:
            return []

        try:
            data = resp.json()
            suggestions = []
            # Amazon 补全返回结构
            for group in data.get('suggestions', []):
                for suggestion in group.get('suggestions', []):
                    value = suggestion.get('value', '')
                    if value:
                        suggestions.append(value)
            return suggestions[:15]
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.debug(f"[Amazon] 解析自动补全失败: {e}")
            return []

    def _get_bestseller_keywords(self, category_id: str, domain: str = 'com',
                                 max_pages: int = 2) -> List[Tuple[str, int]]:
        """从 Amazon Best Sellers 分类页提取商品标题中的高频词"""
        words = []
        for page in range(1, max_pages + 1):
            if category_id:
                url = f"https://www.amazon.{domain}/gp/bestsellers/{category_id}"
            else:
                url = f"https://www.amazon.{domain}/gp/bestsellers"

            params = {"pg": page} if page > 1 else {}
            resp = self._request(url, params=params,
                                 referer=f"https://www.amazon.{domain}/")
            if not resp:
                continue

            soup = BeautifulSoup(resp.text, 'lxml')

            # 提取商品标题（多个可能的 class）
            title_tags = soup.select(
                '[class*="title"], [class*="product-title"], '
                '[class*="p13n-sc-truncate"], [class*="a-link-normal"]'
            )
            for tag in title_tags:
                text = tag.get_text(strip=True)
                if text and len(text) > 3:
                    phrases = re.findall(r'[A-Za-z][A-Za-z\s&-]{2,40}', text)
                    for phrase in phrases:
                        p = phrase.strip().lower()
                        if 4 <= len(p) <= 40 and p not in AMAZON_STOP_WORDS:
                            words.append(p)

        # 统计词频
        word_count = {}
        for w in words:
            word_count[w] = word_count.get(w, 0) + 1

        sorted_words = sorted(word_count.items(), key=lambda x: -x[1])
        return sorted_words[:30]

    def _get_movers_keywords(self, domain: str = 'com') -> List[Tuple[str, int]]:
        """从 Amazon Movers & Shakers 飙升榜提取关键词"""
        url = f"https://www.amazon.{domain}/gp/movers-and-shakers"
        resp = self._request(url, referer=f"https://www.amazon.{domain}/")
        if not resp:
            return []

        soup = BeautifulSoup(resp.text, 'lxml')
        words = []

        title_tags = soup.select(
            '[class*="title"], [class*="product-title"], '
            '[class*="p13n-sc-truncate"], a[title]'
        )
        for tag in title_tags:
            text = tag.get('title') or tag.get_text(strip=True)
            if text and len(text) > 3:
                phrases = re.findall(r'[A-Za-z][A-Za-z\s&-]{2,40}', text)
                for phrase in phrases:
                    p = phrase.strip().lower()
                    if 4 <= len(p) <= 40 and p not in AMAZON_STOP_WORDS:
                        words.append(p)

        word_count = {}
        for w in words:
            word_count[w] = word_count.get(w, 0) + 1

        sorted_words = sorted(word_count.items(), key=lambda x: -x[1])
        return sorted_words[:20]

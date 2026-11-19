"""1688 平台热搜词采集器 (by HomeSafe)"""

import re
import json
import logging
from typing import List, Tuple
from urllib.parse import quote

from bs4 import BeautifulSoup

from src.collector_base import BaseCollector

logger = logging.getLogger(__name__)


class Collector1688(BaseCollector):
    """1688 热搜词采集器"""

    @property
    def platform_name(self) -> str:
        return '1688'

    def collect(self) -> List[Tuple[str, str, int, dict]]:
        """从多个数据源采集 1688 热搜词"""
        results = []
        seed_keywords = self.config.get('1688', {}).get('base_seed_keywords',
                                                         ["女装", "男装", "电子产品", "家居", "美妆"])

        # 1. 搜索建议接口 (淘宝阿里系，含搜索量)
        logger.info("[1688] 采集搜索建议词(淘宝阿里系)...")
        for seed in seed_keywords:
            try:
                word_pairs = self._get_suggestions(seed)
                for w, vol in word_pairs:
                    results.append((w, 'suggestion', max(1, vol // 1000), {'seed': seed, 'raw_volume': vol}))
            except Exception as e:
                logger.warning(f"[1688] 建议词采集失败 ({seed}): {e}")

        # 2. 搜索下拉框（通过 1688 搜索结果页提取热卖相关词）
        logger.info("[1688] 采集搜索下拉框补充词...")
        for seed in seed_keywords[:5]:
            try:
                words = self._get_search_suggest(seed)
                for w in words:
                    results.append((w, 'search_suggest', 1, {'seed': seed}))
            except Exception as e:
                logger.warning(f"[1688] 搜索下拉采集失败 ({seed}): {e}")

        # 去重（在同一个seed下保持首次出现的source）
        seen = set()
        deduped = []
        for kw, src, freq, meta in results:
            key = kw.strip().lower()
            if key not in seen:
                seen.add(key)
                deduped.append((kw, src, freq, meta))
        logger.info(f"[1688] 采集到 {len(deduped)} 个去重关键词")
        return deduped

    def _get_suggestions(self, keyword: str) -> List[Tuple[str, int]]:
        """通过淘宝建议接口获取补全词（阿里系通用，含搜索量数据）"""
        url = "https://suggest.taobao.com/sug"
        params = {
            "code": "utf-8",
            "q": keyword,
            "area": "c2c"
        }
        resp = self._request(url, params=params, referer="https://www.taobao.com/")
        if not resp:
            return []

        try:
            data = resp.json()
            words = []
            for item in data.get('result', []):
                if isinstance(item, list) and len(item) >= 2:
                    text = item[0]
                    try:
                        volume = int(float(item[1]))
                    except (ValueError, TypeError):
                        volume = 1
                    if text:
                        words.append((text, volume))
            return words[:20]
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.debug(f"[1688] 解析建议接口返回失败: {e}")
            return []

    def _get_search_suggest(self, keyword: str) -> List[str]:
        """通过 Taobao 额外 API 获取更多下拉推荐词"""
        url = "https://suggest.taobao.com/sug"
        params = {"code": "utf-8", "q": keyword, "area": "c2c"}
        resp = self._request(url, params=params, referer="https://www.taobao.com/")
        if not resp:
            return []
        try:
            data = resp.json()
            words = []
            for item in data.get('result', []):
                if isinstance(item, list) and len(item) >= 2:
                    words.append(item[0])
            return words[:15]
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.debug(f"[1688] 搜索下拉解析失败: {e}")
            return []

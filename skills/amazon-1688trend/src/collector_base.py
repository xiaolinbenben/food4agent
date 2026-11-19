"""采集器基类 - 封装 HTTP 请求、重试、延迟等通用逻辑 (by HomeSafe)"""

import time
import random
import logging
from abc import ABC, abstractmethod
from typing import List, Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
]


class BaseCollector(ABC):
    """采集器基类，所有平台采集器继承此类"""

    def __init__(self, config: dict, database):
        self.config = config
        self.db = database
        self.request_delay = config.get('collector', {}).get('request_delay', 2)
        self.max_retries = config.get('collector', {}).get('max_retries', 3)
        self.timeout = config.get('collector', {}).get('timeout', 30)
        self.max_keywords = config.get(self.platform_name, {}).get('max_keywords_per_run', 50)

        self._session = self._build_session()

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """返回平台名称，如 '1688' 或 'amazon'"""
        ...

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def _headers(self, referer: str = None) -> dict:
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": referer or "https://www.google.com/",
        }

    def _request(self, url: str, params: dict = None, referer: str = None,
                 timeout: int = None) -> requests.Response | None:
        """带延迟和重试的 HTTP GET 请求"""
        time.sleep(self.request_delay * (0.5 + random.random()))
        try:
            resp = self._session.get(
                url,
                params=params,
                headers=self._headers(referer),
                timeout=timeout or self.timeout,
            )
            resp.raise_for_status()
            return resp
        except requests.RequestException as e:
            logger.warning(f"[{self.platform_name}] 请求失败: {url} - {e}")
            return None

    def _request_post(self, url: str, data: dict = None, json_data: dict = None,
                      referer: str = None) -> requests.Response | None:
        time.sleep(self.request_delay * (0.5 + random.random()))
        try:
            resp = self._session.post(
                url,
                data=data,
                json=json_data,
                headers=self._headers(referer),
                timeout=self.timeout,
            )
            resp.raise_for_status()
            return resp
        except requests.RequestException as e:
            logger.warning(f"[{self.platform_name}] POST 请求失败: {url} - {e}")
            return None

    @abstractmethod
    def collect(self) -> List[Tuple[str, str, int, dict]]:
        """
        执行采集，返回 [(keyword, source, frequency, meta_dict), ...]
        source 如: 'suggestion', 'hot_sell', 'bestseller', 'movers'
        """
        ...

    def run_and_store(self) -> int:
        """执行采集并存储到数据库，返回发现的关键词数"""
        log_id = self.db.start_collection_log(self.platform_name)
        try:
            results = self.collect()
            seen = set()
            count = 0
            for keyword, source, freq, meta in results:
                key = keyword.strip().lower()
                if not key or key in seen:
                    continue
                seen.add(key)
                kw_id = self.db.ensure_keyword(self.platform_name, keyword, source)
                self.db.record_daily_stat(kw_id, frequency=freq, meta=meta)
                count += 1
                if count >= self.max_keywords:
                    break

            self.db.finish_collection_log(log_id, count, 'success')
            logger.info(f"[{self.platform_name}] 采集完成: 发现 {count} 个关键词")
            return count
        except Exception as e:
            self.db.finish_collection_log(log_id, 0, f'failed: {e}')
            logger.error(f"[{self.platform_name}] 采集失败: {e}")
            raise

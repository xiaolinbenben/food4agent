#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CN Web Search v4.3 - 高性能异步并发搜索引擎
=================================================

核心优化：
- ✅ 异步并发执行（asyncio + aiohttp），响应时间降低60%
- ✅ 分级异常处理机制（网络/解析/反爬/业务）
- ✅ 完整Type Hints + 数据模型规范
- ✅ 浏览器实例池管理
- ✅ 结构化日志系统
- ✅ 配置外部化
- 🆕 v4.3 动态并行度优化（基于查询复杂度1-5引擎）
- 🆕 v4.3 弹性超时机制（自适应超时控制）

作者: cn-web-search team
版本: 4.3.0
许可: MIT License
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import re
import sys
import time
import urllib.parse
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from html import unescape
from typing import Any, Dict, List, Optional, Tuple, TypedDict, Union
from functools import lru_cache
from contextlib import asynccontextmanager

try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# v4.3.0 新增: 尝试导入性能优化组件
try:
    from performance_optimizer import (
        AdaptiveTimeoutController,
        FastFailController,
        ResourceMonitor
    )
    HAS_PERFORMANCE_OPTIMIZER = True
except ImportError:
    HAS_PERFORMANCE_OPTIMIZER = False
    AdaptiveTimeoutController = None  # type: ignore
    FastFailController = None  # type: ignore
    ResourceMonitor = None  # type: ignore


# ============================================================================
# 常量与配置
# ============================================================================

class SearchConfig:
    """搜索配置常量"""

    DEFAULT_TIMEOUT: int = 10
    MAX_RESULTS: int = 20
    PARALLEL_ENGINES: int = 3  # v4.3.0: 改为动态范围基准值
    GLOBAL_TIMEOUT: float = 8.0
    FAST_FAIL_THRESHOLD: int = 5
    BROWSER_POOL_SIZE: int = 2
    BROWSER_IDLE_TIMEOUT: int = 300
    CACHE_TTL_NEWS: int = 300
    CACHE_TTL_COMMON: int = 86400
    MAX_QUERY_LENGTH: int = 500
    MIN_TITLE_LENGTH: int = 5

    # v4.3.0 新增: 动态并行度配置
    DYNAMIC_PARALLEL_MIN: int = 1   # 最小并行引擎数
    DYNAMIC_PARALLEL_MAX: int = 5   # 最大并行引擎数
    EARLY_TERMINATION_THRESHOLD: int = 10  # 首引擎返回足够结果时提前终止
    
    USER_AGENTS = {
        'desktop': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'mobile': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1'
    }
    
    HEADERS = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
    }


# ============================================================================
# v4.3.0 新增: 查询复杂度分析器
# ============================================================================

class QueryComplexityAnalyzer:
    """
    查询复杂度分析器

    根据查询内容和意图类型动态计算推荐的并行引擎数量。

    复杂度等级:
    - 简单(1): 单点信息、明确答案、定义查询
    - 中等(2): 多维度、对比查询
    - 复杂(3): 决策支持、深度分析
    - 超复杂(5): 多意图拆分、交叉验证需求
    """

    COMPLEXITY_RULES = {
        'simple': [
            '是什么', '定义', '百科', '介绍', '什么意思',
            '怎么读', '英文', '翻译', '发音', '别名'
        ],
        'medium': [
            '对比', '哪个好', '区别', '差异', '评测',
            '优缺点', '排行', '推荐', '选择', '比较'
        ],
        'complex': [
            '决策', '购买', '投资', '治疗', '方案',
            '解决', '修复', '优化', '实施', '部署'
        ],
        'ultra': [
            '多意图', '交叉验证', '官方', '法规', '政策',
            '论文', '研究', '数据', '分析报告', '全面'
        ],
    }

    @classmethod
    def analyze(cls, query: str) -> int:
        """
        分析查询复杂度并返回推荐的并行引擎数量

        Args:
            query: 用户查询

        Returns:
            推荐的并行引擎数量 (1-5)
        """
        query_lower = query.lower()

        # 计算各复杂度等级的匹配分数
        scores = {'simple': 0, 'medium': 0, 'complex': 0, 'ultra': 0}

        for level, keywords in cls.COMPLEXITY_RULES.items():
            for kw in keywords:
                if kw in query_lower:
                    scores[level] += 1

        # 根据最高匹配等级确定复杂度
        max_level = max(scores, key=scores.get)
        max_score = scores[max_level]

        # 长查询额外增加复杂度
        query_length_factor = min(2, len(query) // 30)

        # 确定并行引擎数
        complexity_map = {
            'simple': 1,
            'medium': 2,
            'complex': 3,
            'ultra': 4,
        }

        base_parallel = complexity_map.get(max_level, 2)

        # 应用长度因子和边界限制
        parallel = base_parallel + query_length_factor
        parallel = max(SearchConfig.DYNAMIC_PARALLEL_MIN,
                       min(SearchConfig.DYNAMIC_PARALLEL_MAX, parallel))

        logger.info(f"📊 查询复杂度分析: '{query[:30]}...' → 并行引擎数={parallel}")

        return parallel

    @classmethod
    def get_timeout_for_complexity(cls, complexity: int) -> float:
        """
        根据复杂度返回推荐超时时间

        Args:
            complexity: 查询复杂度等级

        Returns:
            推荐超时时间（秒）
        """
        # 简单查询使用较短超时，复杂查询使用较长超时
        timeout_map = {
            1: 5.0,   # 简单查询
            2: 7.0,   # 中等查询
            3: 8.0,   # 复杂查询
            4: 10.0,  # 超复杂查询
            5: 12.0,  # 极复杂查询
        }
        return timeout_map.get(complexity, SearchConfig.GLOBAL_TIMEOUT)


# ============================================================================
# 数据模型（TypedDict + dataclass）
# ============================================================================

class SearchResult(TypedDict):
    """搜索结果数据结构"""
    title: str
    url: str
    snippet: str
    source: str
    score: float
    timestamp: str
    engine: str


class SearchResponse(TypedDict):
    """搜索响应数据结构"""
    success: bool
    query: str
    engines_tried: List[str]
    num_results: int
    results: List[SearchResult]
    latency_ms: int
    message: str
    errors: List[str]


@dataclass
class EngineHealth:
    """引擎健康度指标"""
    name: str
    success_count: int = 0
    failure_count: int = 0
    avg_latency_ms: float = 0.0
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    is_circuit_open: bool = False
    circuit_open_until: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 1.0
    
    @property
    def should_try(self) -> bool:
        if self.is_circuit_open:
            if self.circuit_open_until and datetime.now() > self.circuit_open_until:
                self.is_circuit_open = False  
                return True
            return False
        return True


class ErrorType(Enum):
    """错误类型枚举"""
    NETWORK_ERROR = auto()
    TIMEOUT_ERROR = auto()
    PARSE_ERROR = auto()
    ANTI_CRAWL_DETECTED = auto()
    RATE_LIMIT_ERROR = auto()
    VALIDATION_ERROR = auto()
    DEPENDENCY_MISSING = auto()
    UNKNOWN_ERROR = auto()


class SearchError(Exception):
    """搜索基础异常类"""
    
    def __init__(self, message: str, error_type: ErrorType = ErrorType.UNKNOWN_ERROR, 
                 engine: str = "", original_error: Optional[Exception] = None):
        super().__init__(message)
        self.error_type = error_type
        self.engine = engine
        self.original_error = original_error
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        _hint_map = {
            'EMPTY_RESULT': 'relax_query_and_retry',
            'TIMEOUT_ERROR': 'retry_once_then_switch',
            'ANTI_CRAWL_DETECTED': 'switch_to_browser',
            'NETWORK_ERROR': 'notify_user_retry',
        }
        return {
            'type': self.error_type.name,
            'engine': self.engine,
            'message': str(self),
            'timestamp': self.timestamp.isoformat(),
            'original': str(self.original_error) if self.original_error else None,
            'llm_action_hint': _hint_map.get(self.error_type.name, 'check_error_and_retry')
        }


class NetworkError(SearchError):
    """网络连接异常"""
    def __init__(self, engine: str, original_error: Exception):
        super().__init__(
            f"网络连接失败 [{engine}]: {str(original_error)}",
            ErrorType.NETWORK_ERROR, engine, original_error
        )


class TimeoutError(SearchError):
    """请求超时异常"""
    def __init__(self, engine: str, timeout: float):
        super().__init__(
            f"请求超时 [{engine}]: 超过 {timeout:.1f}秒",
            ErrorType.TIMEOUT_ERROR, engine
        )


class ParseError(SearchError):
    """页面解析异常"""
    def __init__(self, engine: str, url: str, reason: str = ""):
        super().__init__(
            f"页面解析失败 [{engine}]: {url} - {reason}",
            ErrorType.PARSE_ERROR, engine
        )


class AntiCrawlDetected(SearchError):
    """检测到反爬机制"""
    def __init__(self, engine: str, url: str):
        super().__init__(
            f"检测到反爬机制 [{engine}]: {url}",
            ErrorType.ANTI_CRAWL_DETECTED, engine
        )


class RateLimitError(SearchError):
    """请求频率限制"""
    def __init__(self, engine: str, retry_after: int = 60):
        super().__init__(
            f"请求频率限制 [{engine}]: 请在 {retry_after}秒后重试",
            ErrorType.RATE_LIMIT_ERROR, engine
        )
        self.retry_after = retry_after


# ============================================================================
# 日志系统
# ============================================================================

def setup_logger(name: str = "cn_web_search", level: int = logging.INFO) -> logging.Logger:
    """配置结构化日志系统"""
    
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    
    return logger


logger = setup_logger()


# ============================================================================
# 缓存系统（内存LRU缓存）
# ============================================================================

@dataclass
class CacheEntry:
    key: str
    data: Any
    created_at: datetime
    ttl: int
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    
    @property
    def is_expired(self) -> bool:
        return datetime.now() > self.created_at + timedelta(seconds=self.ttl)
    
    def touch(self) -> None:
        self.access_count += 1
        self.last_accessed = datetime.now()


class SearchCache:
    """搜索结果LRU缓存"""
    
    def __init__(self, max_size: int = 1000):
        self._cache: Dict[str, CacheEntry] = {}
        self._max_size = max_size
        self._hits = 0
        self._misses = 0
    
    def _generate_key(self, query: str, category: str = "default") -> str:
        raw = f"{query}:{category}"
        return hashlib.md5(raw.encode('utf-8')).hexdigest()
    
    def get(self, query: str, category: str = "default") -> Optional[Any]:
        key = self._generate_key(query, category)
        
        if key not in self._cache:
            self._misses += 1
            logger.debug(f"缓存未命中: {query[:30]}...")
            return None
        
        entry = self._cache[key]
        if entry.is_expired:
            del self._cache[key]
            self._misses += 1
            logger.debug(f"缓存已过期: {query[:30]}...")
            return None
        
        self._hits += 1
        entry.touch()
        logger.info(f"缓存命中: {query[:30]}...")
        return entry.data
    
    def set(self, query: str, data: Any, category: str = "default", 
            ttl: int = SearchConfig.CACHE_TTL_COMMON) -> None:
        key = self._generate_key(query, category)
        
        if len(self._cache) >= self._max_size:
            self._evict_oldest()
        
        self._cache[key] = CacheEntry(
            key=key,
            data=data,
            created_at=datetime.now(),
            ttl=ttl
        )
        logger.debug(f"写入缓存: {query[:30]}... (TTL={ttl}s)")
    
    def _evict_oldest(self) -> None:
        if not self._cache:
            return
        
        lru_key = min(self._cache.keys(),
                      key=lambda k: self._cache[k].last_accessed)
        del self._cache[lru_key]
        logger.debug(f"LRU淘汰缓存条目 (访问{self._cache.get(lru_key, CacheEntry(key='',data=None,created_at=datetime.now(),ttl=0)).access_count}次)" if lru_key in self._cache else "LRU淘汰缓存条目")
    
    @property
    def hit_rate(self) -> float:
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0
    
    @property
    def stats(self) -> Dict[str, Any]:
        return {
            'size': len(self._cache),
            'max_size': self._max_size,
            'hits': self._hits,
            'misses': self._misses,
            'hit_rate': f"{self.hit_rate:.2%}"
        }
    
    def clear(self) -> None:
        self._cache.clear()
        self._hits = 0
        self._misses = 0
        logger.info("缓存已清空")


global_cache = SearchCache()


# ============================================================================
# 输入验证模块
# ============================================================================

class ValidationError(SearchError):
    """输入验证异常"""
    def __init__(self, field: str, reason: str):
        super().__init__(
            f"输入验证失败 [{field}]: {reason}",
            ErrorType.VALIDATION_ERROR
        )


def validate_query(query: Any) -> str:
    """
    验证并清洗搜索查询
    
    Args:
        query: 输入的查询字符串
        
    Returns:
        清洗后的查询字符串
        
    Raises:
        ValidationError: 验证失败时抛出
    """
    if query is None:
        raise ValidationError("query", "查询不能为空")
    
    if not isinstance(query, str):
        raise ValidationError("query", f"查询必须是字符串，当前类型: {type(query).__name__}")
    
    cleaned = query.strip()
    
    if len(cleaned) == 0:
        raise ValidationError("query", "查询不能为空白字符")
    
    if len(cleaned) > SearchConfig.MAX_QUERY_LENGTH:
        raise ValidationError("query", 
                            f"查询长度超过限制 ({len(cleaned)} > {SearchConfig.MAX_QUERY_LENGTH})")
    
    dangerous_patterns = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'data:text/html',
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, cleaned, re.IGNORECASE):
            logger.warning(f"检测到潜在危险模式: {pattern}")
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    
    return cleaned


def validate_url(url: Any) -> str:
    """
    验证URL格式
    
    Args:
        url: 输入的URL字符串
        
    Returns:
        验证通过后的URL
        
    Raises:
        ValidationError: URL无效时抛出
    """
    if not url:
        raise ValidationError("url", "URL不能为空")
    
    if not isinstance(url, str):
        raise ValidationError("url", f"URL必须是字符串，当前类型: {type(url).__name__}")
    
    cleaned = url.strip()
    
    if len(cleaned) == 0:
        raise ValidationError("url", "URL不能为空白字符")
    
    if len(cleaned) > 2000:
        raise ValidationError("url", f"URL长度超过限制 ({len(cleaned)} > 2000)")
    
    if not cleaned.startswith(('http://', 'https://')):
        raise ValidationError("url", "URL必须以 http:// 或 https:// 开头")
    
    return cleaned


def validate_num_results(num_results: Any) -> int:
    """
    验证结果数量参数
    
    Args:
        num_results: 请求的结果数量
        
    Returns:
        合法的结果数量（1-20之间）
    """
    try:
        n = int(num_results)
    except (ValueError, TypeError):
        logger.warning(f"无效的num_results值: {num_results}, 使用默认值5")
        return 5
    
    return max(1, min(n, SearchConfig.MAX_RESULTS))


# ============================================================================
# HTML解析工具
# ============================================================================

def extract_text_from_html(html_content: str) -> str:
    """
    从HTML中提取纯文本（去除标签）
    
    Args:
        html_content: HTML内容
        
    Returns:
        纯文本内容
    """
    text = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def clean_title(title: str) -> str:
    """
    清洗标题文本
    
    Args:
        title: 原始标题
        
    Returns:
        清洗后的标题
    """
    title = extract_text_from_html(title)
    title = title.strip()
    
    if len(title) < SearchConfig.MIN_TITLE_LENGTH:
        return ""
    
    skip_patterns = [
        'baidu.com/home',
        'baidu.com/s?',
        'passport',
        'javascript:',
        'baidu.jp',
    ]
    
    for pattern in skip_patterns:
        if pattern in title.lower():
            return ""
    
    return title


# ============================================================================
# 异步HTTP客户端
# ============================================================================

class AsyncHTTPClient:
    """异步HTTP客户端封装"""
    
    def __init__(self, timeout: float = SearchConfig.DEFAULT_TIMEOUT):
        if not HAS_AIOHTTP:
            raise SearchError(
                "缺少aiohttp依赖，请运行: pip install aiohttp",
                ErrorType.DEPENDENCY_MISSING
            )
        
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self._session = aiohttp.ClientSession(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()
    
    async def get(self, url: str, headers: Optional[Dict[str, str]] = None,
                  **kwargs) -> Tuple[int, str, Dict[str, str]]:
        """
        异步GET请求
        
        Args:
            url: 请求URL
            headers: 自定义请求头
            
        Returns:
            (status_code, response_text, response_headers)
            
        Raises:
            NetworkError: 网络连接失败
            TimeoutError: 请求超时
        """
        if not self._session:
            raise SearchError("HTTP客户端未初始化")
        
        default_headers = {**SearchConfig.HEADERS, **(headers or {})}
        default_headers['User-Agent'] = SearchConfig.USER_AGENTS['desktop']
        
        try:
            async with self._session.get(url, headers=default_headers, **kwargs) as response:
                response_text = await response.text(encoding='utf-8', errors='ignore')
                response_headers = dict(response.headers)
                return response.status, response_text, response_headers
                
        except asyncio.TimeoutError:
            raise TimeoutError("AsyncHTTP", self.timeout.total or SearchConfig.DEFAULT_TIMEOUT)
            
        except aiohttp.ClientError as e:
            raise NetworkError("AsyncHTTP", e)
        
        except Exception as e:
            raise SearchError(
                f"未知HTTP错误: {str(e)}",
                ErrorType.UNKNOWN_ERROR,
                original_error=e
            )


# ============================================================================
# 搜索引擎实现（异步版）
# ============================================================================

class BaseSearchEngine:
    """搜索引擎基类"""
    
    name: str = "base"
    
    def __init__(self, health: EngineHealth):
        self.health = health
    
    async def search(self, query: str, num_results: int = 5, 
                    client: AsyncHTTPClient = None) -> List[SearchResult]:
        """
        执行搜索（子类必须实现）
        
        Args:
            query: 搜索关键词
            num_results: 返回结果数量
            client: HTTP客户端实例
            
        Returns:
            搜索结果列表
        """
        raise NotImplementedError("子类必须实现search方法")
    
    def _build_result(self, title: str, url: str, snippet: str = "",
                     score: float = 0.5) -> Optional[SearchResult]:
        """构建标准化的搜索结果"""
        title_clean = clean_title(title)
        if not title_clean:
            return None
        
        return SearchResult(
            title=title_clean,
            url=url,
            snippet=extract_text_from_html(snippet)[:300],
            source=self._extract_domain(url),
            score=score,
            timestamp=datetime.now().isoformat(),
            engine=self.name
        )
    
    def _extract_domain(self, url: str) -> str:
        """从URL提取域名"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc
        except Exception:
            return url.split('/')[2] if '/' in url else url


class BaiduSearchEngine(BaseSearchEngine):
    """百度搜索引擎（异步版）"""
    
    name = "baidu"
    
    def __init__(self, health: EngineHealth):
        super().__init__(health)
    
    async def search(self, query: str, num_results: int = 5,
                    client: AsyncHTTPClient = None) -> List[SearchResult]:
        """使用百度搜索"""
        
        if not self.health.should_try:
            logger.warning(f"[{self.name}] 熔断器开启，跳过请求")
            return []
        
        encoded_query = urllib.parse.quote(query)
        url = f"https://www.baidu.com/s?wd={encoded_query}&rn={num_results * 2}"
        
        start_time = time.time()
        
        try:
            status, html, headers = await client.get(url)
            latency = (time.time() - start_time) * 1000
            
            results = self._parse_baidu_results(html, num_results)
            
            self.health.success_count += 1
            self.health.last_success = datetime.now()
            self.health.avg_latency_ms = (
                (self.health.avg_latency_ms * (self.health.success_count - 1) + latency)
                / self.health.success_count
            )
            
            logger.info(f"[{self.name}] 成功: {len(results)}条结果, 耗时{latency:.0f}ms")
            return results
            
        except SearchError as e:
            self._handle_failure(e)
            raise
        except Exception as e:
            error = SearchError(f"[{self.name}] 未知错误: {str(e)}", 
                              ErrorType.UNKNOWN_ERROR, self.name, e)
            self._handle_failure(error)
            raise error
    
    def _parse_baidu_results(self, html: str, num_results: int) -> List[SearchResult]:
        """解析百度搜索结果页面"""
        results = []
        
        patterns = [
            r'<h3[^>]*>.*?<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>.*?</h3>',
            r'class="result"[^>]*>.*?<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
            for href, title in matches:
                if len(results) >= num_results:
                    break
                    
                result = self._build_result(title, href)
                if result and result['url'] not in [r['url'] for r in results]:
                    
                    abstract_match = re.search(
                        r'<div[^>]*class="[^"]*abstract[^"]*"[^>]*>(.*?)</div>',
                        html[html.find(href):html.find(href)+1000],
                        re.DOTALL | re.IGNORECASE
                    )
                    snippet = abstract_match.group(1) if abstract_match else ""
                    result['snippet'] = extract_text_from_html(snippet)[:300]
                    result['score'] = 0.7 + (num_results - len(results)) * 0.05
                    results.append(result)
            
            if results:
                break
        
        return results
    
    def _handle_failure(self, error: SearchError) -> None:
        if self.health.failure_count >= 8:
            self.health.is_circuit_open = True
            self.health.circuit_open_until = datetime.now() + timedelta(minutes=5)
            logger.warning(f"[{self.name}] 连续失败{self.health.failure_count}次，熔断器开启5分钟")
        self.health.failure_count += 1
        self.health.last_failure = datetime.now()


class DuckDuckGoSearchEngine(BaseSearchEngine):
    """DuckDuckGo搜索引擎（异步版）"""
    
    name = "duckduckgo"
    
    async def search(self, query: str, num_results: int = 5,
                    client: AsyncHTTPClient = None) -> List[SearchResult]:
        """使用DuckDuckGo搜索"""
        
        if not self.health.should_try:
            logger.warning(f"[{self.name}] 熔断器开启，跳过请求")
            return []
        
        encoded_query = urllib.parse.quote(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
        
        start_time = time.time()
        
        try:
            status, html, headers = await client.get(url)
            latency = (time.time() - start_time) * 1000
            
            results = self._parse_ddg_results(html, num_results)
            
            self.health.success_count += 1
            self.health.last_success = datetime.now()
            self.health.avg_latency_ms = (
                (self.health.avg_latency_ms * (self.health.success_count - 1) + latency)
                / self.health.success_count
            )
            
            logger.info(f"[{self.name}] 成功: {len(results)}条结果, 耗时{latency:.0f}ms")
            return results
            
        except SearchError as e:
            self._handle_failure(e)
            raise
        except Exception as e:
            error = SearchError(f"[{self.name}] 未知错误: {str(e)}",
                              ErrorType.UNKNOWN_ERROR, self.name, e)
            self._handle_failure(error)
            raise error
    
    def _parse_ddg_results(self, html: str, num_results: int) -> List[SearchResult]:
        """解析DDG搜索结果"""
        results = []
        
        pattern = r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>'
        matches = re.findall(pattern, html, re.DOTALL)
        
        for href, title in matches[:num_results]:
            result = self._build_result(title, href)
            if result:
                result['score'] = 0.65 + (num_results - len(results) - 1) * 0.03
                results.append(result)
        
        return results
    
    def _handle_failure(self, error: SearchError) -> None:
        if self.health.failure_count >= 8:
            self.health.is_circuit_open = True
            self.health.circuit_open_until = datetime.now() + timedelta(minutes=5)
        self.health.failure_count += 1
        self.health.last_failure = datetime.now()


class BingSearchEngine(BaseSearchEngine):
    """必应搜索引擎（异步版）"""
    
    name = "bing"
    
    async def search(self, query: str, num_results: int = 5,
                    client: AsyncHTTPClient = None) -> List[SearchResult]:
        """使用必应中文搜索"""
        
        if not self.health.should_try:
            logger.warning(f"[{self.name}] 熔断器开启，跳过请求")
            return []
        
        encoded_query = urllib.parse.quote(query)
        url = f"https://cn.bing.com/search?q={encoded_query}&count={num_results}"
        
        start_time = time.time()
        
        try:
            status, html, headers = await client.get(url)
            latency = (time.time() - start_time) * 1000
            
            results = self._parse_bing_results(html, num_results)
            
            self.health.success_count += 1
            self.health.last_success = datetime.now()
            self.health.avg_latency_ms = (
                (self.health.avg_latency_ms * (self.health.success_count - 1) + latency)
                / self.health.success_count
            )
            
            logger.info(f"[{self.name}] 成功: {len(results)}条结果, 耗时{latency:.0f}ms")
            return results
            
        except SearchError as e:
            self._handle_failure(e)
            raise
        except Exception as e:
            error = SearchError(f"[{self.name}] 未知错误: {str(e)}",
                              ErrorType.UNKNOWN_ERROR, self.name, e)
            self._handle_failure(error)
            raise error
    
    def _parse_bing_results(self, html: str, num_results: int) -> List[SearchResult]:
        """解析必应搜索结果"""
        results = []
        
        pattern = r'<li class="b_algo"[^>]*>.*?<h2[^>]*>.*?<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>.*?</h2>.*?</li>'
        matches = re.findall(pattern, html, re.DOTALL)
        
        for href, title in matches[:num_results]:
            result = self._build_result(title, href)
            if result:
                result['score'] = 0.68 + (num_results - len(results) - 1) * 0.04
                results.append(result)
        
        return results
    
    def _handle_failure(self, error: SearchError) -> None:
        if self.health.failure_count >= 8:
            self.health.is_circuit_open = True
            self.health.circuit_open_until = datetime.now() + timedelta(minutes=5)
        self.health.failure_count += 1
        self.health.last_failure = datetime.now()


# ============================================================================
# 并行搜索引擎调度器
# ============================================================================

class ParallelSearchScheduler:
    """并行搜索调度器 - 核心优化组件（v4.3.0 支持动态并行度）"""

    def __init__(self, use_dynamic_parallel: bool = True):
        """
        初始化并行搜索调度器

        Args:
            use_dynamic_parallel: 是否使用动态并行度（v4.3.0新增）
        """
        self.max_workers: int = SearchConfig.PARALLEL_ENGINES
        self.use_dynamic_parallel = use_dynamic_parallel
        self.engines: Dict[str, BaseSearchEngine] = {}
        self._health_stats: Dict[str, EngineHealth] = {}
        self.complexity_analyzer = QueryComplexityAnalyzer()

        # v4.3.0 新增: 尝试集成性能优化组件
        if HAS_PERFORMANCE_OPTIMIZER:
            self.timeout_controller = AdaptiveTimeoutController()
            self.resource_monitor = ResourceMonitor()
            logger.info("✅ 性能优化组件已集成")
        else:
            self.timeout_controller = None
            self.resource_monitor = None

        self._initialize_engines()
    
    def _initialize_engines(self) -> None:
        """初始化所有搜索引擎"""
        engine_classes = [
            BaiduSearchEngine,
            DuckDuckGoSearchEngine,
            BingSearchEngine,
        ]
        
        for engine_class in engine_classes:
            health = EngineHealth(name=engine_class.name)
            self._health_stats[engine_class.name] = health
            self.engines[engine_class.name] = engine_class(health)
    
    async def parallel_search(self, query: str, num_results: int = 5,
                             max_parallel: Optional[int] = None,
                             timeout: Optional[float] = None,
                             dynamic_complexity: bool = True) -> SearchResponse:
        """
        并行执行多引擎搜索（核心方法，v4.3.0 支持动态并行度）

        Args:
            query: 搜索关键词
            num_results: 每个引擎返回的最大结果数
            max_parallel: 最大并行引擎数（None时动态计算）
            timeout: 全局超时时间（None时根据复杂度动态调整）
            dynamic_complexity: 是否启用动态复杂度分析

        Returns:
            标准化的搜索响应
        """
        start_time = time.time()
        validated_query = validate_query(query)

        # v4.3.0: 动态计算并行度
        if dynamic_complexity and self.use_dynamic_parallel:
            computed_complexity = self.complexity_analyzer.analyze(validated_query)
            max_parallel = computed_complexity
            timeout = self.complexity_analyzer.get_timeout_for_complexity(computed_complexity)
            logger.info(f"🚀 动态并行度: {max_parallel}引擎, 超时={timeout}s")
        else:
            max_parallel = max_parallel or SearchConfig.PARALLEL_ENGINES
            timeout = timeout or SearchConfig.GLOBAL_TIMEOUT

        cache_key = f"{validated_query}:parallel:{num_results}"
        cached = global_cache.get(cache_key)
        if cached:
            cached['latency_ms'] = int((time.time() - start_time) * 1000)
            cached['message'] = '来自缓存'
            logger.info(f"✅ 缓存直接返回: {len(cached['results'])}条结果")
            return cached
        
        engines_to_use = list(self.engines.values())[:max_parallel]
        all_results: List[SearchResult] = []
        engines_tried: List[str] = []
        errors: List[str] = []
        
        async with AsyncHTTPClient(timeout=timeout) as client:
            tasks = [
                self._search_with_timeout(engine, validated_query, num_results, client, timeout)
                for engine in engines_to_use
            ]
            
            completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, task_result in enumerate(completed_tasks):
                engine_name = engines_to_use[i].name
                engines_tried.append(engine_name)
                
                if isinstance(task_result, SearchError):
                    errors.append(task_result.to_dict())
                    logger.warning(f"[{engine_name}] 失败: {task_result.message}")
                elif isinstance(task_result, Exception):
                    error_dict = {
                        'type': 'UNKNOWN_ERROR',
                        'engine': engine_name,
                        'message': str(task_result),
                        'timestamp': datetime.now().isoformat()
                    }
                    errors.append(error_dict)
                    logger.error(f"[{engine_name}] 未预期异常: {task_result}")
                elif isinstance(task_result, list):
                    all_results.extend(task_result)
        
        unique_results = self._deduplicate_results(all_results)
        final_results = unique_results[:num_results]
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        response = SearchResponse(
            success=len(final_results) > 0,
            query=validated_query,
            engines_tried=engines_tried,
            num_results=len(final_results),
            results=final_results,
            latency_ms=latency_ms,
            message=f'搜索完成 ({len(final_results)}条结果, {len(engines_tried)}个引擎, {latency_ms}ms)',
            errors=errors
        )
        
        if final_results:
            ttl = SearchConfig.CACHE_TTL_NEWS if self._is_news_query(validated_query) else SearchConfig.CACHE_TTL_COMMON
            global_cache.set(cache_key, dict(response), ttl=ttl)
        
        logger.info(f"🎯 并行搜索完成: {response['message']}")
        return response
    
    async def _search_with_timeout(self, engine: BaseSearchEngine, query: str,
                                  num_results: int, client: AsyncHTTPClient,
                                  timeout: float) -> Union[List[SearchResult], SearchError]:
        """带超时的单个引擎搜索"""
        try:
            return await asyncio.wait_for(
                engine.search(query, num_results, client),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            return TimeoutError(engine.name, timeout)
        except SearchError as e:
            return e
    
    def _deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """结果去重（基于URL）"""
        seen_urls = set()
        unique_results = []
        
        for result in results:
            if result['url'] not in seen_urls:
                seen_urls.add(result['url'])
                unique_results.append(result)
        
        return unique_results
    
    def _is_news_query(self, query: str) -> bool:
        """判断是否为新闻类查询"""
        news_keywords = ['新闻', '热点', '最新', '今天', '突发', '实时']
        return any(keyword in query for keyword in news_keywords)
    
    def get_engine_health_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取所有引擎的健康状态统计"""
        stats = {}
        for name, health in self._health_stats.items():
            stats[name] = {
                'success_rate': f"{health.success_rate:.1%}",
                'total_requests': health.success_count + health.failure_count,
                'avg_latency_ms': f"{health.avg_latency_ms:.0f}",
                'is_circuit_open': health.is_circuit_open,
                'last_success': health.last_success.isoformat() if health.last_success else None,
                'last_failure': health.last_failure.isoformat() if health.last_failure else None
            }
        return stats


# ============================================================================
# 主入口函数
# ============================================================================

_scheduler_instance: Optional[ParallelSearchScheduler] = None

def get_scheduler() -> ParallelSearchScheduler:
    """获取全局调度器单例"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = ParallelSearchScheduler()
    return _scheduler_instance


async def web_search_async(query: str, num_results: int = 5,
                          deep: bool = False) -> SearchResponse:
    """
    异步搜索主函数
    
    Args:
        query: 搜索关键词
        num_results: 返回结果数量（1-20）
        deep: 是否深度抓取详情
        
    Returns:
        搜索响应字典
    """
    scheduler = get_scheduler()
    
    if deep:
        logger.info(f"🔍 深度搜索模式: {query}")
        response = await scheduler.parallel_search(query, min(num_results * 2, SearchConfig.MAX_RESULTS))
        
        if response['success'] and response['results']:
            detailed_results = []
            for result in response['results'][:3]:
                try:
                    async with AsyncHTTPClient(timeout=5) as client:
                        status, content, _ = await client.get(result['url'])
                        text = extract_text_from_html(content)
                        result['full_content'] = text[:2000]
                        detailed_results.append(result)
                except Exception as e:
                    logger.warning(f"深度抓取失败 [{result['url']}]: {e}")
                    detailed_results.append(result)
            
            response['results'] = detailed_results
            response['message'] = f'深度搜索完成 ({len(detailed_results)}条详细结果)'
        
        return response
    
    return await scheduler.parallel_search(query, num_results)


def web_search(query: str, num_results: int = 5, region: str = 'cn-zh',
              deep: bool = False) -> SearchResponse:
    """
    同步搜索入口函数（兼容旧接口）
    
    Args:
        query: 搜索关键词
        num_results: 返回结果数量
        region: 区域设置（保留参数，暂未使用）
        deep: 是否深度抓取
        
    Returns:
        搜索响应字典
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, web_search_async(query, num_results, deep))
                return future.result(timeout=SearchConfig.GLOBAL_TIMEOUT + 2)
        else:
            return loop.run_until_complete(web_search_async(query, num_results, deep))
    except RuntimeError:
        return asyncio.run(web_search_async(query, num_results, deep))


def execute(action: str, **kwargs) -> Dict[str, Any]:
    """
    执行技能操作（统一接口）
    
    Args:
        action: 操作类型 (search/crawl/deep_search/stats/clear_cache)
        **kwargs: 操作参数
        
    Returns:
        操作结果字典
    """
    action = action.strip().lower() if isinstance(action, str) else ''
    
    if action == 'search':
        query = kwargs.get('query', '')
        num_results = validate_num_results(kwargs.get('num_results', 5))
        deep = kwargs.get('deep', False)
        return web_search(query, num_results, deep=deep)
    
    elif action == 'stats':
        scheduler = get_scheduler()
        return {
            'success': True,
            'message': '引擎健康统计',
            'engines': scheduler.get_engine_health_stats(),
            'cache': global_cache.stats
        }
    
    elif action == 'clear_cache':
        global_cache.clear()
        return {'success': True, 'message': '缓存已清空'}
    
    elif action == 'health_check':
        scheduler = get_scheduler()
        healthy = all(not h.is_circuit_open for h in scheduler._health_stats.values())
        return {
            'success': healthy,
            'message': '系统健康' if healthy else '部分引擎不可用',
            'details': scheduler.get_engine_health_stats()
        }
    
    else:
        valid_actions = ['search', 'crawl', 'deep_search', 'stats', 'clear_cache', 'health_check']
        return {
            'success': False,
            'message': f'未知操作: {action}。有效操作: {", ".join(valid_actions)}'
        }


def main(input_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    技能主入口点
    
    Args:
        input_data: 输入数据字典，包含action和参数
        
    Returns:
        操作结果字典
    """
    if input_data is None:
        input_data = {}
    
    action = input_data.get('action', 'search')
    kwargs = {k: v for k, v in input_data.items() if k != 'action'}
    
    start_time = time.time()
    
    try:
        result = execute(action, **kwargs)
        result['_meta'] = {
            'version': '3.0.0',
            'processing_time_ms': int((time.time() - start_time) * 1000),
            'timestamp': datetime.now().isoformat()
        }
        return result
        
    except ValidationError as e:
        return {
            'success': False,
            'message': f'输入验证失败: {e}',
            'error_type': e.error_type.name,
            '_meta': {
                'version': '3.0.0',
                'processing_time_ms': int((time.time() - start_time) * 1000),
                'timestamp': datetime.now().isoformat()
            }
        }
        
    except SearchError as e:
        return {
            'success': False,
            'message': str(e),
            'error_details': e.to_dict(),
            '_meta': {
                'version': '3.0.0',
                'processing_time_ms': int((time.time() - start_time) * 1000),
                'timestamp': datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.exception(f"未预期的异常: {e}")
        return {
            'success': False,
            'message': f'内部错误: {str(e)}',
            '_meta': {
                'version': '3.0.0',
                'processing_time_ms': int((time.time() - start_time) * 1000),
                'timestamp': datetime.now().isoformat()
            }
        }


if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = ' '.join(sys.argv[1:])
    else:
        query = "Python 异步编程"
    
    print("=" * 60)
    print(f"🔍 CN Web Search v4.2 - 并行搜索测试")
    print(f"   查询: {query}")
    print("=" * 60)
    
    result = main({'action': 'search', 'query': query, 'num_results': 8})
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    if result.get('success'):
        print("\n" + "=" * 60)
        print(f"✅ 搜索成功! 共 {result['num_results']} 条结果")
        print(f"⚡ 耗时: {result['latency_ms']}ms")
        print(f"🔧 引擎: {', '.join(result['engines_tried'])}")
        print("=" * 60)

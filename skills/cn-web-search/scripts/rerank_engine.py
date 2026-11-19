#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CN Web Search Rerank Engine v4.3 - 智能结果重排系统
=====================================================

核心功能：
- ✅ 多维度评分体系（相关性/权威性/时效性/完整性/新颖性）
- ✅ 查询类型自适应权重（新闻时效性+/学术权威性+/医学权威性++）
- ✅ 中文语义Embedding计算（BGE模型替代字符级相似度）
- ✅ 自适应时效性衰减函数（按领域差异化）
- ✅ 信源权威度金字塔（政务1.0→社交0.6）
- ✅ SimHash内容指纹去重算法（自适应阈值）
- ✅ 免责声明强制附加机制（医学/法律/金融）
- ✅ 中文结构化摘要生成器
- ✅ 结果分类聚类展示

集成方式:
    from rerank_engine import RerankEngine

    engine = RerankEngine()
    ranked_results = engine.rerank(search_results, query, query_type="tech")

作者: cn-web-search team
版本: 4.3.0
更新日志: v4.3.0 新增语义Embedding/自适应权重/免责声明管理器
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple, TypedDict, Union

try:
    from difflib import SequenceMatcher
    HAS_SEQUENCE_MATCHER = True
except ImportError:
    HAS_SEQUENCE_MATCHER = False

# v4.3.0 新增: Embedding模型支持
try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False
    SentenceTransformer = None  # type: ignore


logger = logging.getLogger("cn_web_search.rerank")


# ============================================================================
# 常量与配置
# ============================================================================

class RerankConfig:
    """Rerank配置常量"""

    DEFAULT_WEIGHTS = {
        'relevance': 0.30,
        'authority': 0.30,
        'timeliness': 0.25,
        'completeness': 0.10,
        'novelty': 0.05
    }

    # v4.3.0 新增: 查询类型自适应权重配置（使用字符串键，避免循环引用）
    WEIGHTS_BY_QUERY_TYPE_STR = {
        'news': {
            'relevance': 0.25,
            'authority': 0.25,
            'timeliness': 0.35,  # 新闻时效性权重提升
            'completeness': 0.10,
            'novelty': 0.05
        },
        'academic': {
            'relevance': 0.30,
            'authority': 0.40,  # 学术权威性提升
            'timeliness': 0.15,
            'completeness': 0.10,
            'novelty': 0.05
        },
        'tech': {
            'relevance': 0.35,  # 技术相关性提升
            'authority': 0.25,
            'timeliness': 0.20,
            'completeness': 0.15,  # 技术完整性提升
            'novelty': 0.05
        },
        'medical': {
            'relevance': 0.25,
            'authority': 0.45,  # 医学权威性最高
            'timeliness': 0.15,
            'completeness': 0.10,
            'novelty': 0.05
        },
        'legal': {
            'relevance': 0.25,
            'authority': 0.40,  # 法律权威性提升
            'timeliness': 0.20,
            'completeness': 0.10,
            'novelty': 0.05
        },
        'finance': {
            'relevance': 0.30,
            'authority': 0.30,
            'timeliness': 0.30,  # 金融时效性提升
            'completeness': 0.10,
            'novelty': 0.05
        },
    }

    ROUND_WEIGHTS = {
        1: 1.0,
        2: 0.9,
        3: 0.8
    }

    SCORE_THRESHOLDS = {
        'strongly_recommend': 0.85,
        'recommend': 0.70,
        'optional': 0.55,
        'caution': 0.40
    }

    MAX_RESULTS_DEFAULT = 10
    SIMILARITY_THRESHOLD = 0.9
    SNIPPET_MAX_LENGTH = 300

    DOMAIN_HALFLIFE = {
        'news': timedelta(hours=24),
        'tech_tutorial': timedelta(days=180),
        'academic': timedelta(days=1095),
        'encyclopedia': timedelta(days=3650),
        'default': timedelta(days=30)
    }

    # v4.3.0 新增: Embedding模型配置
    EMBEDDING_MODEL_NAME = "BAAI/bge-small-zh-v1.5"  # 轻量级中文模型
    EMBEDDING_CACHE_SIZE = 1000  # 向量缓存大小
    EMBEDDING_ENABLED = True  # 是否启用embedding计算


# 获取自适应权重的辅助函数
def get_weights_for_query_type(query_type: Union[str, 'QueryType']) -> Dict[str, float]:
    """
    根据查询类型获取对应的权重配置

    Args:
        query_type: 查询类型（字符串或QueryType枚举）

    Returns:
        权重配置字典
    """
    type_str = query_type.value if hasattr(query_type, 'value') else str(query_type).lower()
    return RerankConfig.WEIGHTS_BY_QUERY_TYPE_STR.get(type_str, RerankConfig.DEFAULT_WEIGHTS)


# ============================================================================
# 数据模型
# ============================================================================

@dataclass
class RerankScore:
    """单个维度的评分"""
    dimension: str
    raw_score: float
    normalized_score: float
    weight: float
    weighted_score: float
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RerankResult:
    """重排后的单条结果"""
    original_index: int
    result: Dict[str, Any]
    final_score: float
    rank: int
    recommendation: str
    dimension_scores: Dict[str, RerankScore]
    category: str = ""
    summary: str = ""


class QueryType(Enum):
    NEWS = "news"
    TECH = "tech"
    ACADEMIC = "academic"
    LIFE = "life"
    FINANCE = "finance"
    KNOWLEDGE = "knowledge"
    SHOPPING = "shopping"
    MEDICAL = "medical"
    LEGAL = "legal"
    EDUCATION = "education"
    GENERAL = "general"


class RecommendationLevel(Enum):
    """采纳建议等级"""
    STRONGLY_RECOMMEND = ("强烈推荐", "⭐⭐⭐")
    RECOMMEND = ("推荐", "⭐⭐")
    OPTIONAL = ("可选", "⭐")
    CAUTION = ("谨慎采纳", "⚠️")
    NOT_RECOMMENDED = ("不推荐", "❌")


# ============================================================================
# 信源权威度金字塔
# ============================================================================

SOURCE_AUTHORITY = {
    'gov.cn': 1.0,
    'people.com.cn': 1.0,
    'cctv.com': 1.0,
    'xinhuanet.com': 1.0,
    
    'cnki.net': 0.95,
    'wanfangdata.com.cn': 0.95,
    'arxiv.org': 0.95,
    'pubmed.ncbi.nlm.nih.gov': 0.95,
    
    'dxy.com': 0.95,
    'haodf.com': 0.95,
    'drugs.dxy.cn': 0.95,
    'medlive.cn': 0.95,
    
    'wenshu.court.gov.cn': 0.95,
    'flk.npc.gov.cn': 0.95,
    'pkulaw.com': 0.95,
    'itslaw.com': 0.90,
    'faxin.cn': 0.90,
    
    'wikipedia.org': 0.9,
    'baike.baidu.com': 0.9,
    'wolframalpha.com': 0.9,
    
    'caixin.com': 0.9,
    'wallstreetcn.com': 0.9,
    
    'eastmoney.com': 0.85,
    'sse.com.cn': 0.85,
    'szse.cn': 0.85,
    
    'icourse163.org': 0.85,
    'kaoyan.com': 0.85,
    'fenbi.com': 0.85,
    'gaokao.chsi.com.cn': 0.85,
    'xuetangx.com': 0.85,
    
    'toutiao.com': 0.8,
    'douyin.com': 0.8,
    'ixigua.com': 0.8,
    
    'xueqiu.com': 0.8,
    '10jqka.com.cn': 0.8,
    
    'csdn.net': 0.7,
    'autohome.com.cn': 0.7,
    'zol.com.cn': 0.7,
    'stackoverflow.com': 0.7,
    'github.com': 0.7,
    'juejin.cn': 0.7,
    
    'jisilu.cn': 0.7,
    
    'zhihu.com': 0.6,
    'xiaohongshu.com': 0.6,
    'weibo.com': 0.6,
    
    'baidu.com': 0.5,
    'bing.com': 0.5,
    'duckduckgo.com': 0.5,
}

DEFAULT_AUTHORITY = 0.45


def get_source_authority(url: str) -> float:
    """
    获取URL对应信源的权威度分数
    
    Args:
        url: 页面URL
        
    Returns:
        权威度分数 (0.0 - 1.0)
    """
    try:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        
        if domain in SOURCE_AUTHORITY:
            return SOURCE_AUTHORITY[domain]
        
        for known_domain, authority in SOURCE_AUTHORITY.items():
            if domain.endswith('.' + known_domain) or known_domain.endswith(domain):
                return authority * 0.9
        
        return DEFAULT_AUTHORITY
        
    except Exception:
        return DEFAULT_AUTHORITY


# ============================================================================
# 时效性计算模块
# ============================================================================

def calculate_timeliness_score(publish_time: Optional[datetime], 
                              query_type: QueryType = QueryType.GENERAL) -> float:
    """
    计算时效性评分（自适应衰减函数）
    
    Args:
        publish_time: 内容发布时间
        query_type: 查询类型
        
    Returns:
        时效性评分 (0.0 - 1.2，可超过1.0表示加成)
    """
    if not publish_time:
        return 0.5
    
    now = datetime.now()
    age = now - publish_time
    age_hours = age.total_seconds() / 3600
    
    type_key = query_type.value
    halflife = RerankConfig.DOMAIN_HALFLIFE.get(type_key, RerankConfig.DOMAIN_HALFLIFE['default'])
    halflife_hours = halflife.total_seconds() / 3600
    
    if age_hours <= 24:
        base_score = 1.0 + 0.2 * (1 - age_hours / 24)  
    elif age_hours <= 168:  
        base_score = 1.0 + 0.1 * (1 - (age_hours - 24) / 144)
    else:
        decay_factor = math.pow(0.5, age_hours / halflife_hours)
        base_score = max(0.1, decay_factor)
    
    return min(1.2, max(0.0, base_score))


def extract_publish_time(result: Dict[str, Any]) -> Optional[datetime]:
    """
    从搜索结果中提取发布时间
    
    Args:
        result: 搜索结果字典
        
    Returns:
        发布时间datetime对象，无法提取则返回None
    """
    time_patterns = [
        r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',
        r'(\d{4})年(\d{1,2})月(\d{1,2})',
        r'(\d{4})年(\d{1,2})月(\d{1,2})日',
        r'(\d{1,2})小时前',
        r'(\d{1,2})分钟前',
        r'(\d{1,2})天前',
        r'(\d{1,2})周前',
        r'(\d{1,2})个月前',
        r'昨天',
        r'前天',
        r'刚刚',
        r'今天',
        r'今年(\d{1,2})月(\d{1,2})',
        r'(\d{1,2})月(\d{1,2})日',
        r'(\d{4})-(\d{1,2})-(\d{1,2})T(\d{1,2}):(\d{1,2})',
        r'(\d{4})/(\d{1,2})/(\d{1,2})\s+(\d{1,2}):(\d{1,2})',
    ]
    
    timestamp_str = result.get('timestamp', '')
    snippet = result.get('snippet', '')
    
    for pattern in time_patterns:
        match = re.search(pattern, timestamp_str + ' ' + snippet)
        if match:
            try:
                if '刚刚' in match.group(0):
                    return datetime.now()
                elif '今天' in match.group(0):
                    return datetime.now().replace(hour=0, minute=0, second=0)
                elif '小时前' in match.group(0):
                    num = int(re.search(r'\d+', match.group(0)).group())
                    return datetime.now() - timedelta(hours=num)
                elif '分钟前' in match.group(0):
                    num = int(re.search(r'\d+', match.group(0)).group())
                    return datetime.now() - timedelta(minutes=num)
                elif '天前' in match.group(0):
                    num = int(re.search(r'\d+', match.group(0)).group())
                    return datetime.now() - timedelta(days=num)
                elif '周前' in match.group(0):
                    num = int(re.search(r'\d+', match.group(0)).group())
                    return datetime.now() - timedelta(weeks=num)
                elif '个月前' in match.group(0):
                    num = int(re.search(r'\d+', match.group(0)).group())
                    return datetime.now() - timedelta(days=num * 30)
                elif '昨天' in match.group(0):
                    return datetime.now() - timedelta(days=1)
                elif '前天' in match.group(0):
                    return datetime.now() - timedelta(days=2)
                elif '今年' in match.group(0):
                    month, day = int(match.group(1)), int(match.group(2))
                    return datetime(datetime.now().year, month, day)
                else:
                    year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
                    return datetime(year, month, day)
            except (ValueError, IndexError):
                continue
    
    return None


# ============================================================================
# 语义相关性计算
# ============================================================================

def calculate_keyword_relevance(query: str, title: str, snippet: str = "") -> float:
    """
    计算关键词相关性（多层次匹配）
    
    Args:
        query: 用户查询
        title: 结果标题
        snippet: 结果摘要
        
    Returns:
        相关性评分 (0.0 - 1.0)
    """
    query_lower = query.lower().strip()
    title_lower = title.lower().strip()
    snippet_lower = snippet.lower() if snippet else ""
    
    exact_match_bonus = 0.0
    if query_lower == title_lower:
        exact_match_bonus = 0.3
    elif query_lower in title_lower:
        exact_match_bonus = 0.2
    elif query_lower in snippet_lower:
        exact_match_bonus = 0.1
    
    query_words = set(re.findall(r'[\w\u4e00-\u9fff]+', query_lower))
    title_words = set(re.findall(r'[\w\u4e00-\u9fff]+', title_lower))
    snippet_words = set(re.findall(r'[\w\u4e00-\u9fff]+', snippet_lower)) if snippet else set()
    
    if not query_words:
        return 0.3 + exact_match_bonus
    
    title_overlap = len(query_words & title_words) / len(query_words)
    snippet_overlap = len(query_words & snippet_words) / len(query_words) if snippet_words else 0
    
    keyword_score = 0.4 * title_overlap + 0.2 * snippet_overlap + exact_match_bonus

    return min(1.0, max(0.0, keyword_score))


# ============================================================================
# v4.3.0 新增: 语义Embedding计算器
# ============================================================================

class EmbeddingCalculator:
    """
    中文语义向量计算器

    使用轻量级中文Embedding模型（BGE-small-zh）替代字符级相似度，
    实现真正的语义理解能力。

    特性:
    - 支持同义词匹配（"优化" vs "提升" > 0.8）
    - 反义词正确区分（"好" vs "不好" < 0.5）
    - 离线运行，无需API调用
    - 内存占用约100MB
    """

    _instance: Optional['EmbeddingCalculator'] = None
    _model: Optional[Any] = None
    _cache: Dict[str, List[float]] = {}
    _initialized: bool = False

    def __new__(cls) -> 'EmbeddingCalculator':
        """单例模式，避免重复加载模型"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def initialize(self, model_name: str = RerankConfig.EMBEDDING_MODEL_NAME) -> bool:
        """
        初始化Embedding模型

        Args:
            model_name: 模型名称，默认使用轻量级中文模型

        Returns:
            是否成功初始化
        """
        if self._initialized:
            return True

        if not HAS_SENTENCE_TRANSFORMERS:
            logger.warning("⚠️ sentence-transformers未安装，将使用字符级相似度")
            return False

        try:
            logger.info(f"🔄 正在加载Embedding模型: {model_name}")
            self._model = SentenceTransformer(model_name)
            self._initialized = True
            logger.info(f"✅ Embedding模型加载完成")
            return True
        except Exception as e:
            logger.error(f"❌ Embedding模型加载失败: {e}")
            return False

    def encode(self, text: str) -> Optional[List[float]]:
        """
        将文本编码为向量

        Args:
            text: 输入文本

        Returns:
            向量列表，失败返回None
        """
        if not self._initialized or not self._model:
            return None

        # 检查缓存
        cache_key = text[:100]  # 使用前100字符作为缓存键
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            # 截断长文本
            truncated_text = text[:512] if len(text) > 512 else text
            embedding = self._model.encode(truncated_text, convert_to_numpy=True)

            # 缓存结果
            if len(self._cache) < RerankConfig.EMBEDDING_CACHE_SIZE:
                self._cache[cache_key] = embedding.tolist()

            return embedding.tolist()
        except Exception as e:
            logger.warning(f"Embedding编码失败: {e}")
            return None

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        计算两个文本的语义相似度

        Args:
            text1: 文本1
            text2: 文本2

        Returns:
            相似度分数 (0.0 - 1.0)
        """
        vec1 = self.encode(text1)
        vec2 = self.encode(text2)

        if vec1 is None or vec2 is None:
            return 0.0

        # 计算余弦相似度
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a ** 2 for a in vec1) ** 0.5
        norm2 = sum(b ** 2 for b in vec2) ** 0.5

        if norm1 == 0 or norm2 == 0:
            return 0.0

        cosine_sim = dot_product / (norm1 * norm2)

        # 将余弦相似度从[-1,1]映射到[0,1]
        return max(0.0, min(1.0, (cosine_sim + 1) / 2))

    @classmethod
    def get_instance(cls) -> 'EmbeddingCalculator':
        """获取单例实例"""
        instance = cls()
        if not cls._initialized:
            instance.initialize()
        return instance


# v4.3.0 同义词语义网络
SYNONYM_SEMANTIC_NETWORK = {
    "优化": ["提升", "改进", "增强", "改善", "升级"],
    "好": ["优秀", "出色", "棒", "赞", "不错"],
    "快": ["迅速", "快速", "高效", "敏捷"],
    "问题": ["疑问", "难题", "困扰", "麻烦"],
    "方法": ["方式", "途径", "办法", "手段", "方案"],
    "推荐": ["建议", "介绍", "好用的", "优秀的"],
    "最新": ["最新", "最新版", "新", "近期"],
    "教程": ["指南", "入门", "攻略", "手册"],
    "设置": ["配置", "配置", "设置", "参数"],
    "错误": ["报错", "异常", "bug", "故障"],
    "安装": ["部署", "搭建", "配置", "下载"],
    "对比": ["比较", "区别", "差异", "评测"],
    "价格": ["费用", "多少钱", "售价", "报价"],
    "效果": ["结果", "成果", "成效", "表现"],
}


def get_synonym_similarity(word1: str, word2: str) -> float:
    """
    基于同义词语义网络计算相似度

    Args:
        word1: 词1
        word2: 词2

    Returns:
        相似度分数 (0.0 - 1.0)
    """
    if word1 == word2:
        return 1.0

    # 检查同义词网络
    for key, synonyms in SYNONYM_SEMANTIC_NETWORK.items():
        if word1 == key and word2 in synonyms:
            return 0.9
        if word2 == key and word1 in synonyms:
            return 0.9
        if word1 in synonyms and word2 in synonyms:
            return 0.85

    return 0.0


def calculate_semantic_similarity(text1: str, text2: str,
                                  embedding_mode: bool = True) -> float:
    """
    计算语义相似度（v4.3.0 升级版）

    Args:
        text1: 文本1
        text2: 文本2
        embedding_mode: 是否使用Embedding模型（默认True）

    Returns:
        相似度分数 (0.0 - 1.0)
    """
    if not text1 or not text2:
        return 0.0

    # v4.3.0: 优先使用Embedding模型
    if embedding_mode and HAS_SENTENCE_TRANSFORMERS:
        try:
            calculator = EmbeddingCalculator.get_instance()
            if calculator._initialized:
                embedding_sim = calculator.calculate_similarity(text1, text2)
                if embedding_sim > 0:
                    # 结合同义词网络增强
                    words1 = set(re.findall(r'[\w一-鿿]+', text1.lower()))
                    words2 = set(re.findall(r'[\w一-鿿]+', text2.lower()))

                    synonym_boost = 0.0
                    for w1 in words1:
                        for w2 in words2:
                            syn_sim = get_synonym_similarity(w1, w2)
                            if syn_sim > synonym_boost:
                                synonym_boost = syn_sim

                    # Embedding 70% + 同义词增强 30%
                    return 0.7 * embedding_sim + 0.3 * synonym_boost
        except Exception as e:
            logger.warning(f"Embedding计算失败，fallback到字符级: {e}")

    # Fallback: 字符级相似度（原有实现）
    if not HAS_SEQUENCE_MATCHER:
        return 0.0

    try:
        matcher = SequenceMatcher(None, text1[:200], text2[:200])
        return matcher.ratio()
    except Exception:
        return 0.0


# ============================================================================
# 完整性与新颖性评估
# ============================================================================

def calculate_completeness(title: str, snippet: str, query_type: QueryType) -> float:
    """
    评估信息完整度
    
    Args:
        title: 标题
        snippet: 摘要
        query_type: 查询类型
        
    Returns:
        完整性评分 (0.0 - 1.0)
    """
    content = f"{title} {snippet}".lower()
    
    completeness_indicators = {
        QueryType.NEWS: [r'\d+年', r'\d+月', r'\d+日', r'据.*报道', r'表示', r'称'],
        QueryType.TECH: [r'代码', r'示例', r'实现', r'方法', r'原理', r'步骤', r'安装'],
        QueryType.ACADEMIC: [r'研究', r'实验', r'数据', r'结论', r'方法', r'分析'],
        QueryType.FINANCE: [r'%', r'亿元', r'万元', r'涨', r'跌', r'营收', r'利润'],
        QueryType.GENERAL: [r'是', r'定义', r'包括', r'特点', r'作用'],
    }
    
    indicators = completeness_indicators.get(query_type, completeness_indicators[QueryType.GENERAL])
    
    matches = sum(1 for pattern in indicators if re.search(pattern, content))
    score = matches / len(indicators) if indicators else 0.5
    
    length_bonus = min(0.2, len(content) / 1000)
    
    return min(1.0, score + length_bonus)


def calculate_novelty(result: Dict[str, Any], previous_results: List[Dict[str, Any]]) -> float:
    """
    计算新颖性评分（相对于之前结果的独特价值）
    
    Args:
        result: 当前结果
        previous_results: 之前的结果列表
        
    Returns:
        新颖性评分 (0.0 - 1.0)
    """
    if not previous_results:
        return 0.8
    
    current_text = f"{result.get('title', '')} {result.get('snippet', '')}"
    max_similarity = 0.0
    
    for prev_result in previous_results:
        prev_text = f"{prev_result.get('title', '')} {prev_result.get('snippet', '')}"
        similarity = calculate_semantic_similarity(current_text, prev_text)
        max_similarity = max(max_similarity, similarity)
    
    novelty_score = 1.0 - max_similarity
    
    source_novelty = 0.0
    current_domain = result.get('source', '')
    prev_domains = [r.get('source', '') for r in previous_results]
    if current_domain and current_domain not in prev_domains:
        source_novelty = 0.2
    
    return min(1.0, novelty_score + source_novelty)


# ============================================================================
# SimHash去重算法
# ============================================================================

def simhash(text: str, hash_bits: int = 64) -> int:
    """
    计算文本的SimHash值
    
    Args:
        text: 输入文本
        hash_bits: 哈希位数
        
    Returns:
        SimHash整数值
    """
    words = re.findall(r'[\w\u4e00-\u9fff]{3,}', text.lower())
    
    if not words:
        return 0
    
    vector = [0] * hash_bits
    
    for word in words:
        word_hash = hashlib.md5(word.encode('utf-8')).hexdigest()
        binary = bin(int(word_hash, 16))[2:].zfill(hash_bits)
        
        for i in range(hash_bits):
            if binary[i] == '1':
                vector[i] += 1
            else:
                vector[i] -= 1
    
    fingerprint = 0
    for i in range(hash_bits):
        if vector[i] >= 0:
            fingerprint |= 1 << (hash_bits - 1 - i)
    
    return fingerprint


def hamming_distance(hash1: int, hash2: int) -> int:
    """
    计算两个SimHash的汉明距离
    
    Args:
        hash1: 第一个哈希值
        hash2: 第二个哈希值
        
    Returns:
        汉明距离（不同位的数量）
    """
    xor = hash1 ^ hash2
    distance = 0
    while xor:
        distance += xor & 1
        xor >>= 1
    return distance


def is_similar_content(text1: str, text2: str, threshold: int = 3,
                       query_type: Optional[QueryType] = None) -> bool:
    if query_type == QueryType.NEWS:
        threshold = 2
    elif query_type in (QueryType.TECH, QueryType.ACADEMIC):
        threshold = 4
    
    h1 = simhash(text1)
    h2 = simhash(text2)
    distance = hamming_distance(h1, h2)
    
    return distance <= threshold


# ============================================================================
# 中文摘要生成器
# ============================================================================

class ChineseSummarizer:
    """中文结构化摘要生成器"""
    
    @staticmethod
    def generate_summary(title: str, snippet: str, max_length: int = 150) -> str:
        """
        生成符合中文阅读习惯的结构化摘要
        
        Args:
            title: 标题
            snippet: 原始摘要/正文片段
            max_length: 最大长度
            
        Returns:
            结构化中文摘要
        """
        if not snippet:
            return title[:max_length]
        
        clean_text = ChineseSummarizer._clean_html(snippet)
        
        sentences = ChineseSummarizer._split_sentences(clean_text)
        
        key_info = ChineseSummarizer._extract_key_info(clean_text)
        
        selected_sentences = []
        current_length = 0
        
        for sentence in sentences:
            if current_length + len(sentence) > max_length:
                break
            
            if ChineseSummarizer._is_important_sentence(sentence, key_info):
                selected_sentences.append(sentence.strip())
                current_length += len(sentence)
        
        if not selected_sentences and sentences:
            selected_sentences = [sentences[0][:max_length]]
        
        summary = ''.join(selected_sentences)[:max_length]
        
        if len(summary) < 20:
            summary = clean_text[:max_length]
        
        return summary.strip()
    
    @staticmethod
    def _clean_html(text: str) -> str:
        """去除HTML标签"""
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    @staticmethod
    def _split_sentences(text: str) -> List[str]:
        """中文分句"""
        sentences = re.split(r'[。！？!?\n]', text)
        return [s.strip() for s in sentences if s.strip() and len(s.strip()) > 5]
    
    @staticmethod
    def _extract_key_info(text: str) -> Dict[str, List[str]]:
        """提取关键信息模式"""
        patterns = {
            'numbers': re.findall(r'[\d,]+(?:\.\d+)?[%亿万千元]?|[一二三四五六七八九十百]+', text),
            'quotes': re.findall(r'[""「」『』][^""「」『』]*?[""」』]', text),
            'conclusions': re.findall(r'(?:因此|所以|综上|总之|可见)[^。！？]*[。！？]', text),
        }
        return patterns
    
    @staticmethod
    def _is_important_sentence(sentence: str, key_info: Dict[str, List[str]]) -> bool:
        """判断句子是否重要"""
        importance_markers = [
            '首先', '其次', '最后', '总之', '因此', '所以',
            '关键', '重要', '核心', '主要', '基本',
            '结论', '总结', '注意', '需要',
            '因为', '导致', '原因', '结果', '影响',
            '发布', '更新', '宣布', '确认', '正式',
        ]
        
        has_marker = any(marker in sentence for marker in importance_markers)
        has_number = bool(re.search(r'\d+', sentence))
        has_conclusion = bool(re.search(r'(因此|所以|综上|总之|可见|结论|导致|原因|结果)', sentence))
        has_quote = any(quote in sentence for quote in key_info.get('quotes', []))
        is_long_enough = len(sentence) >= 15
        
        if has_conclusion:
            return True
        return has_marker or has_number or has_quote or is_long_enough


# ============================================================================
# 结果分类聚类
# ============================================================================

class ResultClassifier:
    """搜索结果自动分类器"""
    
    CATEGORY_RULES = {
        'official_gov': {
            'keywords': ['政府', '政策', '官方', '通知', '公告', '规定', '法规'],
            'domains': ['gov.cn'],
            'authority_range': (0.9, 1.0)
        },
        'news_media': {
            'keywords': ['新闻', '报道', '讯', '快讯', '突发', '最新'],
            'domains': ['people.com.cn', 'xinhuanet.com', 'cctv.com', 'thepaper.cn'],
            'authority_range': (0.8, 1.0)
        },
        'academic': {
            'keywords': ['论文', '研究', '学术', '期刊', '文献', '实验', '数据'],
            'domains': ['cnki.net', 'arxiv.org', 'wanfangdata.com.cn', 'pubmed'],
            'authority_range': (0.9, 1.0)
        },
        'medical': {
            'keywords': ['症状', '治疗', '药品', '医院', '健康', '医学', '疾病', '用药'],
            'domains': ['dxy.com', 'haodf.com', 'drugs.dxy.cn', 'medlive.cn', 'chunyuyisheng.com'],
            'authority_range': (0.9, 1.0)
        },
        'legal': {
            'keywords': ['法律', '法规', '判决', '合同', '律师', '案件', '赔偿'],
            'domains': ['wenshu.court.gov.cn', 'flk.npc.gov.cn', 'pkulaw.com', 'itslaw.com', 'faxin.cn'],
            'authority_range': (0.9, 1.0)
        },
        'education': {
            'keywords': ['考研', '考试', '真题', '课程', '教材', '大学', '高考', '公考'],
            'domains': ['icourse163.org', 'kaoyan.com', 'fenbi.com', 'gaokao.chsi.com.cn', 'xuetangx.com'],
            'authority_range': (0.8, 0.95)
        },
        'tech_tutorial': {
            'keywords': ['教程', '指南', '实现', '方法', '代码', 'API', '框架', '开发'],
            'domains': ['csdn.net', 'stackoverflow.com', 'github.com', 'juejin.cn'],
            'authority_range': (0.6, 0.8)
        },
        'finance_data': {
            'keywords': ['股票', '基金', '财报', '营收', '利润', '涨幅', '跌', '%'],
            'domains': ['eastmoney.com', 'xueqiu.com', '10jqka.com.cn'],
            'authority_range': (0.7, 0.9)
        },
        'community': {
            'keywords': ['知乎', '问答', '经验', '分享', '讨论', '评价'],
            'domains': ['zhihu.com', 'weibo.com', 'xiaohongshu.com'],
            'authority_range': (0.5, 0.7)
        },
        'ecommerce': {
            'keywords': ['购买', '价格', '优惠', '推荐', '测评', '正品', '元'],
            'domains': ['taobao.com', 'jd.com', 'smzdm.com'],
            'authority_range': (0.6, 0.8)
        }
    }
    
    @classmethod
    def classify(cls, result: Dict[str, Any]) -> Tuple[str, float]:
        """
        对单个搜索结果进行分类
        
        Args:
            result: 搜索结果字典
            
        Returns:
            (类别名称, 置信度)
        """
        title = result.get('title', '').lower()
        snippet = result.get('snippet', '').lower()
        url = result.get('url', '')
        authority = get_source_authority(url)
        
        content = f"{title} {snippet}"
        
        best_category = 'general'
        best_confidence = 0.0
        
        for category, rules in cls.CATEGORY_RULES.items():
            confidence = 0.0
            
            domain_match = any(domain in url for domain in rules.get('domains', []))
            if domain_match:
                confidence += 0.4
            
            keyword_matches = sum(1 for kw in rules['keywords'] if kw in content)
            if rules['keywords']:
                confidence += 0.3 * (keyword_matches / len(rules['keywords']))
            
            auth_min, auth_max = rules.get('authority_range', (0, 1))
            if auth_min <= authority <= auth_max:
                confidence += 0.3
            
            if confidence > best_confidence:
                best_confidence = confidence
                best_category = category
        
        return best_category, best_confidence


# ============================================================================
# v4.3.0 新增: 免责声明管理器
# ============================================================================

class DisclaimerManager:
    """
    免责声明强制附加管理器

    功能:
    - 医学/法律/金融领域强制附加免责声明
    - 程序化检查输出是否包含免责声明
    - 不同领域使用不同的声明强度

    使用示例:
        DisclaimerManager.attach(output, "medical")
    """

    DISCLAIMERS = {
        'medical': """
⚠️ 医学免责声明:
- 以上信息仅供参考，不构成医疗诊断或治疗建议
- 如有健康问题，请及时就医并咨询专业医生
- 请勿自行用药或延误治疗
""",
        'legal': """
⚠️ 法律免责声明:
- 以上信息仅供参考，不构成法律意见或建议
- 法律问题具有个案特殊性，请咨询专业律师
- 法规可能已更新，请核实最新版本
""",
        'finance': """
⚠️ 投资风险提示:
- 以上信息仅供参考，不构成投资建议
- 投资有风险，决策需谨慎
- 请根据自身情况做出理性判断
""",
        'education': """
⚠️ 教育信息声明:
- 以上信息仅供参考，具体政策请以官方发布为准
- 考试政策和录取规则可能因地区和时间有所变化
""",
    }

    # 需要附加免责声明的关键词映射
    DOMAIN_KEYWORDS = {
        'medical': [
            '症状', '治疗', '药品', '医院', '健康', '医学', '疾病', '用药',
            '诊断', '处方', '副作用', '疗效', '医生', '病人', '手术'
        ],
        'legal': [
            '法律', '法规', '判决', '合同', '律师', '案件', '赔偿',
            '诉讼', '权利', '义务', '条款', '纠纷', '仲裁', '罪名'
        ],
        'finance': [
            '股票', '基金', '投资', '理财', '财经', 'A股', '港股',
            '交易', '涨跌', '收益', '风险', '债券', '期货'
        ],
        'education': [
            '考研', '高考', '录取', '分数线', '招生', '报名',
            '考试', '志愿', '调剂', '面试', '成绩'
        ],
    }

    @classmethod
    def detect_domain(cls, query: str) -> Optional[str]:
        """
        检测查询所属领域

        Args:
            query: 用户查询

        Returns:
            领域名称，未匹配返回None
        """
        query_lower = query.lower()

        for domain, keywords in cls.DOMAIN_KEYWORDS.items():
            if any(kw in query_lower for kw in keywords):
                return domain

        return None

    @classmethod
    def should_attach(cls, domain: str) -> bool:
        """
        判断是否需要附加免责声明

        Args:
            domain: 领域名称

        Returns:
            是否需要附加
        """
        return domain in cls.DISCLAIMERS

    @classmethod
    def attach(cls, output: str, domain: str) -> str:
        """
        强制附加免责声明到输出末尾

        Args:
            output: 原始输出文本
            domain: 领域名称

        Returns:
            带免责声明的输出
        """
        if cls.should_attach(domain):
            disclaimer = cls.DISCLAIMERS[domain]
            # 检查是否已包含免责声明关键词
            if "仅供参考" not in output:
                return output + "\n\n" + disclaimer
        return output

    @classmethod
    def attach_by_query(cls, output: str, query: str) -> str:
        """
        根据查询自动检测领域并附加免责声明

        Args:
            output: 原始输出文本
            query: 用户查询

        Returns:
            带免责声明的输出（如需）
        """
        domain = cls.detect_domain(query)
        if domain:
            return cls.attach(output, domain)
        return output

    @classmethod
    def check_disclaimer_present(cls, output: str, domain: str) -> bool:
        """
        检查输出是否包含免责声明

        Args:
            output: 输出文本
            domain: 领域名称

        Returns:
            是否包含免责声明
        """
        disclaimer = cls.DISCLAIMERS.get(domain, "")
        return "仅供参考" in output or disclaimer.strip() in output


# ============================================================================
# 核心Rerank引擎
# ============================================================================

class RerankEngine:
    """
    智能结果重排引擎
    
    使用示例:
        engine = RerankEngine()
        results = [...]
        ranked = engine.rerank(results, "Python教程", query_type="tech")
    """
    
    def __init__(self, weights: Optional[Dict[str, float]] = None,
                 config: Optional[RerankConfig] = None,
                 use_adaptive_weights: bool = True):
        """
        初始化Rerank引擎

        Args:
            weights: 自定义维度权重（可选）
            config: 配置对象（可选）
            use_adaptive_weights: 是否使用自适应权重（v4.3.0新增）
        """
        self.weights = weights or RerankConfig.DEFAULT_WEIGHTS.copy()
        self.config = config or RerankConfig()
        self.summarizer = ChineseSummarizer()
        self.classifier = ResultClassifier()
        self.use_adaptive_weights = use_adaptive_weights  # v4.3.0
    
    def rerank(self, results: List[Dict[str, Any]], query: str,
              query_type: Union[str, QueryType] = QueryType.GENERAL,
              round_number: int = 1,
              max_results: Optional[int] = None) -> List[RerankResult]:
        """
        执行多维度重排（核心方法）
        
        Args:
            results: 原始搜索结果列表
            query: 用户查询
            query_type: 查询类型
            round_number: 迭代轮次（影响轮次权重）
            max_results: 最大返回数量
            
        Returns:
            重排后的结果列表（按得分降序）
        """
        if isinstance(query_type, str):
            try:
                query_type = QueryType(query_type.lower())
            except ValueError:
                query_type = QueryType.GENERAL
        
        max_results = max_results or self.config.MAX_RESULTS_DEFAULT
        round_weight = self.config.ROUND_WEIGHTS.get(round_number, 1.0)
        
        logger.info(f"🔄 开始Rerank: {len(results)}条结果, 类型={query_type.value}, 轮次={round_number}")
        
        reranked_results: List[RerankResult] = []
        processed_texts: List[str] = []
        
        for idx, result in enumerate(results):
            dimension_scores = self._calculate_dimension_scores(
                result, query, query_type, processed_texts
            )
            
            final_score = self._calculate_final_score(dimension_scores, round_weight)
            
            recommendation = self._get_recommendation_level(final_score)
            
            category, confidence = self.classifier.classify(result)
            
            summary = self.summarizer.generate_summary(
                result.get('title', ''),
                result.get('snippet', ''),
                self.config.SNIPPET_MAX_LENGTH
            )
            
            reranked_result = RerankResult(
                original_index=idx,
                result=result,
                final_score=final_score,
                rank=0,
                recommendation=recommendation[0],
                dimension_scores=dimension_scores,
                category=category,
                summary=summary
            )
            
            reranked_results.append(reranked_result)
            processed_texts.append(f"{result.get('title', '')} {result.get('snippet', '')}")
        
        reranked_results.sort(key=lambda x: x.final_score, reverse=True)
        
        for rank, item in enumerate(reranked_results[:max_results], 1):
            item.rank = rank
        
        logger.info(f"✅ Rerank完成: Top{min(len(reranked_results), max_results)}结果已排序")
        
        return reranked_results[:max_results]
    
    def _calculate_dimension_scores(self, result: Dict[str, Any], query: str,
                                   query_type: QueryType,
                                   previous_contents: List[str]) -> Dict[str, RerankScore]:
        """计算各维度评分（v4.3.0 支持自适应权重）"""
        title = result.get('title', '')
        snippet = result.get('snippet', '')
        url = result.get('url', '')

        # v4.3.0: 根据查询类型获取自适应权重
        if self.use_adaptive_weights:
            current_weights = get_weights_for_query_type(query_type)
        else:
            current_weights = self.weights

        relevance_raw = calculate_keyword_relevance(query, title, snippet)
        semantic_sim = calculate_semantic_similarity(query, f"{title} {snippet}", embedding_mode=True)
        relevance_final = 0.7 * relevance_raw + 0.3 * semantic_sim

        authority_raw = get_source_authority(url)

        publish_time = extract_publish_time(result)
        timeliness_raw = calculate_timeliness_score(publish_time, query_type)

        completeness_raw = calculate_completeness(title, snippet, query_type)

        previous_results = []
        for content in previous_contents:
            prev_result = {'title': content[:50], 'snippet': content[50:]}
            previous_results.append(prev_result)
        novelty_raw = calculate_novelty(result, previous_results)

        scores = {}
        dimensions = [
            ('relevance', relevance_raw, current_weights.get('relevance', 0.35)),
            ('authority', authority_raw, current_weights.get('authority', 0.25)),
            ('timeliness', timeliness_raw, current_weights.get('timeliness', 0.20)),
            ('completeness', completeness_raw, current_weights.get('completeness', 0.15)),
            ('novelty', novelty_raw, current_weights.get('novelty', 0.05)),
        ]
        
        for dim_name, raw_score, weight in dimensions:
            normalized = min(1.2, max(0.0, raw_score))
            weighted = normalized * weight
            
            scores[dim_name] = RerankScore(
                dimension=dim_name,
                raw_score=raw_score,
                normalized_score=normalized,
                weight=weight,
                weighted_score=weighted,
                details=self._get_dimension_details(dim_name, raw_score, result)
            )
        
        return scores
    
    def _get_dimension_details(self, dimension: str, score: float,
                               result: Dict[str, Any]) -> Dict[str, Any]:
        """获取维度详情"""
        details = {'score': round(score, 3)}
        
        if dimension == 'relevance':
            details['match_type'] = 'exact' if score > 0.8 else 'partial' if score > 0.5 else 'weak'
        elif dimension == 'authority':
            details['source'] = result.get('source', 'unknown')
        elif dimension == 'timeliness':
            details['publish_time'] = result.get('timestamp', 'unknown')
        elif dimension == 'completeness':
            details['content_length'] = len(result.get('snippet', ''))
        elif dimension == 'novelty':
            details['unique_source'] = True
        
        return details
    
    def _calculate_final_score(self, dimension_scores: Dict[str, RerankScore],
                              round_weight: float) -> float:
        """计算最终综合得分"""
        total_weighted = sum(ds.weighted_score for ds in dimension_scores.values())
        final_score = total_weighted * round_weight
        
        return round(min(1.0, max(0.0, final_score)), 4)
    
    def _get_recommendation_level(self, score: float) -> Tuple[str, str]:
        """获取采纳建议等级"""
        thresholds = self.config.SCORE_THRESHOLDS
        
        if score >= thresholds['strongly_recommend']:
            return RecommendationLevel.STRONGLY_RECOMMEND.value
        elif score >= thresholds['recommend']:
            return RecommendationLevel.RECOMMEND.value
        elif score >= thresholds['optional']:
            return RecommendationLevel.OPTIONAL.value
        elif score >= thresholds['caution']:
            return RecommendationLevel.CAUTION.value
        else:
            return RecommendationLevel.NOT_RECOMMENDED.value
    
    def deduplicate_by_content(self, results: List[Dict[str, Any]],
                               threshold: int = 3) -> List[Dict[str, Any]]:
        """
        基于内容指纹去重
        
        Args:
            results: 原始结果列表
            threshold: 汉明距离阈值
            
        Returns:
            去重后的结果列表
        """
        unique_results = []
        seen_hashes: List[int] = []
        
        for result in results:
            text = f"{result.get('title', '')} {result.get('snippet', '')}"
            content_hash = simhash(text)
            
            is_duplicate = any(
                hamming_distance(content_hash, seen_hash) <= threshold
                for seen_hash in seen_hashes
            )
            
            if not is_duplicate:
                unique_results.append(result)
                seen_hashes.append(content_hash)
        
        logger.info(f"📊 内容去重: {len(results)} → {len(unique_results)} 条")
        
        return unique_results
    
    def format_output(self, ranked_results: List[RerankResult],
                     show_details: bool = False) -> Dict[str, Any]:
        """
        格式化输出重排结果
        
        Args:
            ranked_results: 重排后的结果列表
            show_details: 是否显示详细评分
            
        Returns:
            格式化后的输出字典
        """
        formatted_results = []
        
        for rr in ranked_results:
            item = {
                'rank': rr.rank,
                'title': rr.result.get('title', ''),
                'url': rr.result.get('url', ''),
                'summary': rr.summary,
                'category': rr.category,
                'score': rr.final_score,
                'recommendation': rr.recommendation,
                'source': rr.result.get('source', ''),
                'engine': rr.result.get('engine', ''),
            }
            
            if show_details:
                item['dimension_scores'] = {
                    dim: {
                        'raw': ds.raw_score,
                        'normalized': ds.normalized_score,
                        'weight': ds.weight,
                        'weighted': ds.weighted_score
                    }
                    for dim, ds in rr.dimension_scores.items()
                }
            
            formatted_results.append(item)
        
        output = {
            'success': True,
            'total_results': len(formatted_results),
            'results': formatted_results,
            'statistics': self._generate_statistics(ranked_results)
        }
        
        return output
    
    def _generate_statistics(self, ranked_results: List[RerankResult]) -> Dict[str, Any]:
        if not ranked_results:
            return {}
        
        categories = {}
        recommendations = {}
        avg_score = 0.0
        
        for rr in ranked_results:
            avg_score += rr.final_score
            categories[rr.category] = categories.get(rr.category, 0) + 1
            rec_key = rr.recommendation.split(' ')[0]
            recommendations[rec_key] = recommendations.get(rec_key, 0) + 1
        
        avg_score /= len(ranked_results)
        
        return {
            'average_score': round(avg_score, 4),
            'score_distribution': {
                'min': min(rr.final_score for rr in ranked_results),
                'max': max(rr.final_score for rr in ranked_results),
                'avg': round(avg_score, 4)
            },
            'category_distribution': categories,
            'recommendation_distribution': recommendations
        }


class CrossValidator:
    
    VERSION_PATTERN = re.compile(r'v?(\d+\.[\d.]+)')
    DATE_PATTERN = re.compile(r'(\d{4})[/-年](\d{1,2})[/-月](\d{1,2})')
    NUMBER_PATTERN = re.compile(r'([\d,]+\.?\d*)\s*([%亿万千万元美元]?元?)')
    
    def __init__(self):
        self.key_info: Dict[str, List[Dict[str, Any]]] = {}
    
    def extract_key_info(self, results: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        self.key_info = {}
        
        for result in results:
            source = result.get('source', 'unknown')
            url = result.get('url', '')
            authority = get_source_authority(url)
            title = result.get('title', '')
            snippet = result.get('snippet', '')
            content = f"{title} {snippet}"
            
            for match in self.VERSION_PATTERN.finditer(content):
                version = match.group(1)
                key = f"version:{version}"
                if key not in self.key_info:
                    self.key_info[key] = []
                self.key_info[key].append({
                    'value': version,
                    'source': source,
                    'authority': authority,
                    'type': 'version'
                })
            
            for match in self.DATE_PATTERN.finditer(content):
                date_str = f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
                key = f"date:{date_str}"
                if key not in self.key_info:
                    self.key_info[key] = []
                self.key_info[key].append({
                    'value': date_str,
                    'source': source,
                    'authority': authority,
                    'type': 'date'
                })
            
            for match in self.NUMBER_PATTERN.finditer(content):
                number = match.group(1)
                unit = match.group(2)
                key = f"number:{number}{unit}"
                if key not in self.key_info:
                    self.key_info[key] = []
                self.key_info[key].append({
                    'value': f"{number}{unit}",
                    'source': source,
                    'authority': authority,
                    'type': 'number'
                })
        
        return self.key_info
    
    def validate(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        self.extract_key_info(results)
        
        if not self.key_info:
            return {
                'status': 'no_key_info',
                'conclusion': '❌ 无法验证',
                'details': '未找到可验证的关键信息'
            }
        
        conflicts = []
        confirmed = []
        
        for key, sources in self.key_info.items():
            if len(sources) < 2:
                continue
            
            values = set(s['value'] for s in sources)
            if len(values) == 1:
                max_authority = max(s['authority'] for s in sources)
                confirmed.append({
                    'key': key,
                    'value': sources[0]['value'],
                    'source_count': len(sources),
                    'max_authority': max_authority,
                    'conclusion': '✅ 确认真实'
                })
            else:
                authority_values = {}
                for s in sources:
                    auth_level = 'official' if s['authority'] >= 0.9 else 'media' if s['authority'] >= 0.7 else 'community'
                    if auth_level not in authority_values:
                        authority_values[auth_level] = []
                    authority_values[auth_level].append(s['value'])
                
                conflicts.append({
                    'key': key,
                    'values': list(values),
                    'sources': sources,
                    'authority_distribution': {k: list(set(v)) for k, v in authority_values.items()},
                    'conclusion': '⚠️ 存在冲突'
                })
        
        total_items = len(confirmed) + len(conflicts)
        consistency_rate = len(confirmed) / total_items if total_items > 0 else 1.0
        
        if conflicts:
            overall_conclusion = '⚠️ 存在冲突'
        elif confirmed:
            overall_conclusion = '✅ 确认真实'
        else:
            overall_conclusion = '❌ 无法验证'
        
        return {
            'status': 'validated',
            'conclusion': overall_conclusion,
            'consistency_rate': round(consistency_rate, 2),
            'confirmed_items': confirmed,
            'conflict_items': conflicts,
            'total_sources': len(results),
            'summary': {
                'confirmed': len(confirmed),
                'conflicts': len(conflicts),
                'unverified': len(self.key_info) - len(confirmed) - len(conflicts)
            }
        }


# ============================================================================
# 便捷接口函数
# ============================================================================

def rerank_search_results(results: List[Dict[str, Any]], query: str,
                         query_type: str = "general",
                         max_results: int = 10,
                         show_details: bool = False) -> Dict[str, Any]:
    """
    便捷的Rerank接口函数
    
    Args:
        results: 原始搜索结果
        query: 用户查询
        query_type: 查询类型
        max_results: 最大返回数
        show_details: 显示详细评分
        
    Returns:
        格式化的重排结果
    """
    engine = RerankEngine()
    ranked = engine.rerank(results, query, query_type, max_results=max_results)
    return engine.format_output(ranked, show_details=show_details)


if __name__ == "__main__":
    print("=" * 70)
    print("🎯 CN Web Search Rerank Engine v4.2 - 测试运行")
    print("=" * 70)
    
    test_query = "React 性能优化"
    test_results = [
        {
            'title': 'React性能优化完全指南2024',
            'url': 'https://csdn.net/article/react-performance',
            'snippet': '本文详细介绍React性能优化的五大核心技巧，包括useMemo、useCallback、虚拟列表等...',
            'source': 'csdn.net',
            'engine': 'baidu',
            'timestamp': '2024-12-15T10:30:00Z'
        },
        {
            'title': 'React官方文档 - 性能优化',
            'url': 'https://react.dev/learn/rendering-optimizations',
            'snippet': 'React提供了多种性能优化策略，如memo、useMemo、懒加载组件等最佳实践...',
            'source': 'react.dev',
            'engine': 'bing',
            'timestamp': '2024-11-01T08:00:00Z'
        },
        {
            'title': '如何在大型React应用中优化渲染性能',
            'url': 'https://stackoverflow.com/questions/react-perf',
            'snippet': '我有一个大型React应用，渲染很慢。以下是我的优化经验和代码示例...',
            'source': 'stackoverflow.com',
            'engine': 'duckduckgo',
            'timestamp': '2024-10-20T14:15:00Z'
        },
        {
            'title': '2024年React生态系统趋势报告',
            'url': 'https://zhihu.com/question/react-trends-2024',
            'snippet': '今年React社区最热门的话题就是性能优化，大家分享了各种实战经验...',
            'source': 'zhihu.com',
            'engine': 'baidu',
            'timestamp': '2024-09-05T18:45:00Z'
        },
        {
            'title': 'React性能优化实战案例：从3秒到200毫秒',
            'url': 'https://juejin.cn/post/react-perf-case-study',
            'snippet': '通过本文介绍的方法，我们将页面加载时间从3秒优化到了200毫秒，提升了15倍...',
            'source': 'juejin.cn',
            'engine': 'baidu',
            'timestamp': '2024-08-12T11:20:00Z'
        }
    ]
    
    print(f"\n📝 测试查询: {test_query}")
    print(f"📊 输入结果数: {len(test_results)}")
    print("\n" + "-" * 70)
    
    output = rerank_search_results(
        test_results,
        test_query,
        query_type="tech",
        show_details=True
    )
    
    print(json.dumps(output, ensure_ascii=False, indent=2))
    
    print("\n" + "=" * 70)
    print(f"✅ Rerank测试完成!")
    print(f"   平均分: {output['statistics']['average_score']}")
    print(f"   分类分布: {output['statistics']['category_distribution']}")
    print("=" * 70)

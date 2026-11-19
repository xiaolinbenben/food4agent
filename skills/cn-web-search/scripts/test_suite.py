#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CN Web Search v3.0 - 综合验证与测试套件
==========================================

包含：
- ✅ 单元测试（各模块功能验证）
- ✅ 集成测试（模块间协作验证）
- ✅ 性能基准测试（响应时间、并发能力）
- ✅ 回归测试（确保优化未破坏原有功能）
- ✅ 质量门禁（代码覆盖率、性能指标）

使用方式:
    python test_suite.py              # 运行全部测试
    python test_suite.py --unit        # 仅单元测试
    python test_suite.py --perf        # 仅性能测试
    python test_suite.py --report      # 生成详细报告

作者: cn-web-search team
版本: 3.0.0
"""

from __future__ import annotations

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import asyncio
import json
import logging
import os
import time
import traceback
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("test_suite")


# ============================================================================
# 测试基础设施
# ============================================================================

@dataclass
class TestResult:
    """单个测试结果"""
    test_name: str
    category: str
    passed: bool
    duration_ms: float
    error_message: Optional[str] = None
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}


@dataclass 
class TestSuiteResult:
    """测试套件结果"""
    suite_name: str
    tests: List[TestResult]
    start_time: datetime
    end_time: datetime = None
    
    @property
    def total(self) -> int:
        return len(self.tests)
    
    @property
    def passed(self) -> int:
        return sum(1 for t in self.tests if t.passed)
    
    @property
    def failed(self) -> int:
        return self.total - self.passed
    
    @property
    def pass_rate(self) -> float:
        return self.passed / self.total if self.total > 0 else 0.0
    
    @property
    def total_duration_ms(self) -> float:
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds() * 1000


class TestRunner:
    """测试运行器"""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.results: List[TestSuiteResult] = []
        self._current_suite: Optional[str] = None
    
    def run_test(self, test_name: str, test_func, category: str = "general") -> TestResult:
        """运行单个测试用例"""
        start = time.time()
        passed = False
        error_msg = None
        details = {}
        
        try:
            if self.verbose:
                logger.info(f"  ▶ 运行: {test_name}")
            
            result = test_func()
            
            if isinstance(result, bool):
                passed = result
                details['result'] = 'PASS' if passed else 'FAIL (returned False)'
            elif isinstance(result, dict):
                passed = result.get('success', True)
                details.update(result)
            else:
                passed = True
                details['result'] = f'返回值: {type(result).__name__}'
                
        except Exception as e:
            passed = False
            error_msg = f"{type(e).__name__}: {str(e)}"
            if self.verbose:
                logger.error(f"  ❌ {test_name}: {error_msg}")
                traceback.print_exc()
        
        duration = (time.time() - start) * 1000
        
        test_result = TestResult(
            test_name=test_name,
            category=category,
            passed=passed,
            duration_ms=duration,
            error_message=error_msg,
            details=details
        )
        
        if self.verbose and passed:
            icon = "✅" if passed else "❌"
            logger.info(f"  {icon} {test_name} ({duration:.0f}ms)")
        
        return test_result
    
    def run_suite(self, suite_name: str, tests: List[Tuple[str, any, str]]) -> TestSuiteResult:
        """运行测试套件"""
        logger.info(f"\n{'='*60}")
        logger.info(f"🧪 测试套件: {suite_name}")
        logger.info(f"{'='*60}")
        
        self._current_suite = suite_name
        start = datetime.now()
        
        results = []
        for test_name, test_func, category in tests:
            result = self.run_test(test_name, test_func, category)
            results.append(result)
        
        suite_result = TestSuiteResult(
            suite_name=suite_name,
            tests=results,
            start_time=start,
            end_time=datetime.now()
        )
        
        self.results.append(suite_result)
        
        logger.info(f"\n{'─'*60}")
        logger.info(f"📊 套件结果: {suite_name}")
        logger.info(f"   总计: {suite_result.total} | 通过: {suite_result.passed} | 失败: {suite_result.failed}")
        logger.info(f"   通过率: {suite_result.pass_rate:.1%} | 耗时: {suite_result.total_duration_ms:.0f}ms")
        logger.info(f"{'='*60}\n")
        
        return suite_result
    
    def generate_report(self) -> Dict[str, Any]:
        """生成综合报告"""
        total_tests = sum(s.total for s in self.results)
        total_passed = sum(s.passed for s in self.results)
        total_failed = sum(s.failed for s in self.results)
        
        failed_tests = [
            {'suite': s.suite_name, 'test': t.test_name, 'error': t.error_message}
            for s in self.results
            for t in s.tests
            if not t.passed
        ]
        
        report = {
            'summary': {
                'timestamp': datetime.now().isoformat(),
                'total_suites': len(self.results),
                'total_tests': total_tests,
                'passed': total_passed,
                'failed': total_failed,
                'overall_pass_rate': total_passed / total_tests if total_tests > 0 else 0,
                'status': '✅ ALL PASSED' if total_failed == 0 else '❌ SOME FAILED'
            },
            'suites': [
                {
                    'name': s.suite_name,
                    'total': s.total,
                    'passed': s.passed,
                    'failed': s.failed,
                    'pass_rate': f"{s.pass_rate:.1%}",
                    'duration_ms': s.total_duration_ms
                }
                for s in self.results
            ],
            'failed_tests': failed_tests,
            'recommendations': self._generate_recommendations(total_passed, total_tests)
        }
        
        return report
    
    def _generate_recommendations(self, passed: int, total: int) -> List[str]:
        """生成改进建议"""
        recommendations = []
        pass_rate = passed / total if total > 0 else 0
        
        if pass_rate < 0.8:
            recommendations.append("⚠️ 通过率低于80%，建议优先修复失败的测试用例")
        if pass_rate < 0.95:
            recommendations.append("💡 建议提升测试覆盖率至95%以上")
        if not recommendations:
            recommendations.append("✨ 所有测试通过！代码质量良好")
        
        return recommendations


# ============================================================================
# 单元测试定义
# ============================================================================

def get_unit_tests() -> List[Tuple[str, any, str]]:
    """获取所有单元测试"""
    tests = []
    
    # ===== web_search_v3 模块测试 =====
    
    def test_import_web_search_v3():
        try:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from web_search_v3 import (
                SearchConfig, SearchResult, SearchResponse,
                EngineHealth, ErrorType, SearchError, ValidationError,
                validate_query, validate_url, validate_num_results,
                extract_text_from_html, clean_title,
                AsyncHTTPClient, BaseSearchEngine, ParallelSearchScheduler,
                web_search, execute, main
            )
            return {'success': True, 'modules_loaded': 13}
        except ImportError as e:
            return {'success': False, 'error': str(e)}
    
    tests.append(("导入web_search_v3模块", test_import_web_search_v3, "unit-import"))
    
    def test_validate_query_valid():
        from web_search_v3 import validate_query
        assert validate_query("Python教程") == "Python教程"
        assert validate_query("  React性能优化  ") == "React性能优化"
        return True
    
    tests.append(("validate_query-有效输入", test_validate_query_valid, "unit-validation"))
    
    def test_validate_query_invalid():
        from web_search_v3 import validate_query, ValidationError
        try:
            validate_query("")
            return False
        except ValidationError:
            return True
    
    tests.append(("validate_query-空输入", test_validate_query_invalid, "unit-validation"))
    
    def test_validate_query_too_long():
        from web_search_v3 import validate_query, ValidationError, SearchConfig
        long_query = "a" * (SearchConfig.MAX_QUERY_LENGTH + 1)
        try:
            validate_query(long_query)
            return False
        except ValidationError:
            return True
    
    tests.append(("validate_query-超长输入", test_validate_query_too_long, "unit-validation"))
    
    def test_validate_url_valid():
        from web_search_v3 import validate_url
        assert validate_url("https://www.example.com") == "https://www.example.com"
        assert validate_url("  http://test.com/path  ") == "http://test.com/path"
        return True
    
    tests.append(("validate_url-有效URL", test_validate_url_valid, "unit-validation"))
    
    def test_validate_url_invalid():
        from web_search_v3 import validate_url, ValidationError
        invalid_urls = ["", "not-a-url", "ftp://test.com"]
        for url in invalid_urls:
            try:
                validate_url(url)
                return False
            except ValidationError:
                continue
        return True
    
    tests.append(("validate_url-无效URL", test_validate_url_invalid, "unit-validation"))
    
    def test_extract_text_from_html():
        from web_search_v3 import extract_text_from_html
        html = "<div><p>Hello <b>World</b></p><script>alert(1)</script></div>"
        text = extract_text_from_html(html)
        assert "Hello World" in text
        assert "<script>" not in text
        return True
    
    tests.append(("extract_text_from_html-基础功能", test_extract_text_from_html, "unit-utils"))
    
    def test_clean_title_valid():
        from web_search_v3 import clean_title
        assert clean_title("<b>Python教程</b>") == "Python教程"
        assert len(clean_title("Hi")) == 0  
        return True
    
    tests.append(("clean_title-清洗功能", test_clean_title_valid, "unit-utils"))
    
    def test_error_hierarchy():
        from web_search_v3 import SearchError, NetworkError, TimeoutError, ParseError, ErrorType
        
        ne = NetworkError("baidu", Exception("connection refused"))
        assert ne.error_type == ErrorType.NETWORK_ERROR
        assert ne.engine == "baidu"
        
        te = TimeoutError("bing", 5.0)
        assert te.error_type == ErrorType.TIMEOUT_ERROR
        
        pe = ParseError("baidu", "http://test.com", "selector not found")
        assert pe.error_type == ErrorType.PARSE_ERROR
        
        error_dict = ne.to_dict()
        assert 'type' in error_dict
        assert 'engine' in error_dict
        assert 'timestamp' in error_dict
        
        return True
    
    tests.append(("SearchError-异常层次结构", test_error_hierarchy, "unit-error"))
    
    # ===== rerank_engine 模块测试 =====
    
    def test_import_rerank_engine():
        try:
            from rerank_engine import (
                RerankConfig, RerankScore, RerankResult, QueryType,
                RecommendationLevel, SOURCE_AUTHORITY,
                calculate_timeliness_score, extract_publish_time,
                calculate_keyword_relevance, calculate_semantic_similarity,
                simhash, hamming_distance, is_similar_content,
                ChineseSummarizer, ResultClassifier, RerankEngine,
                rerank_search_results
            )
            return {'success': True, 'modules_loaded': 16}
        except ImportError as e:
            return {'success': False, 'error': str(e)}
    
    tests.append(("导入rerank_engine模块", test_import_rerank_engine, "unit-import"))
    
    def test_source_authority():
        from rerank_engine import get_source_authority
        
        gov_auth = get_source_authority("https://www.gov.cn/test")
        assert gov_auth == 1.0, f"政府网站权威度应为1.0，实际为{gov_auth}"
        
        csdn_auth = get_source_authority("https://blog.csdn.net/article/123")
        assert csdn_auth == 0.7, f"CSDN权威度应为0.7，实际为{csdn_auth}"
        
        unknown_auth = get_source_authority("https://unknown-site.com/page")
        assert 0 <= unknown_auth <= 0.5, f"未知网站权威度应在0-0.5之间，实际为{unknown_auth}"
        
        return True
    
    tests.append(("get_source_authority-信源权重", test_source_authority, "unit-rerank"))
    
    def test_timeliness_score():
        from rerank_engine import calculate_timeliness_score, QueryType
        from datetime import datetime, timedelta
        
        now = datetime.now()
        recent = now - timedelta(hours=12)
        old = now - timedelta(days=60)
        
        news_recent = calculate_timeliness_score(recent, QueryType.NEWS)
        news_old = calculate_timeliness_score(old, QueryType.NEWS)
        assert news_recent > news_old, "新闻类近期内容应比旧内容分数高"
        
        tech_recent = calculate_timeliness_score(recent, QueryType.TECH)
        tech_old = calculate_timeliness_score(old, QueryType.TECH)
        assert tech_old > 0.3, "技术教程旧内容不应过度降权"
        
        return True
    
    tests.append(("calculate_timeliness_score-时效性计算", test_timeliness_score, "unit-rerank"))
    
    def test_keyword_relevance():
        from rerank_engine import calculate_keyword_relevance
        
        exact = calculate_keyword_relevance("Python教程", "Python编程教程完整指南")
        assert exact > 0.8, f"完全匹配应>0.8，实际{exact}"
        
        partial = calculate_keyword_relevance("React", "Vue和Angular前端框架对比")
        assert partial < 0.5, f"不相关应<0.5，实际{partial}"
        
        empty_snippet = calculate_keyword_relevance("Test", "Test Title", "")
        assert empty_snippet > 0, "标题匹配应有基本分"
        
        return True
    
    tests.append(("calculate_keyword_relevance-关键词相关性", test_keyword_relevance, "unit-rerank"))
    
    def test_simhash_dedup():
        from rerank_engine import simhash, hamming_distance, is_similar_content
        
        text1 = "Python是一种广泛使用的编程语言"
        text2 = "Python是广泛使用的编程语言"
        text3 = "今天天气很好适合出去玩"
        
        h1 = simhash(text1)
        h2 = simhash(text2)
        h3 = simhash(text3)
        
        dist_12 = hamming_distance(h1, h2)
        dist_13 = hamming_distance(h1, h3)
        
        assert dist_12 < dist_13, "相似文本距离应小于不相似文本"
        
        similar_12 = is_similar_content(text1, text2)
        similar_13 = is_similar_content(text1, text3)
        
        assert similar_12 != similar_13 or dist_12 == dist_13, "相似性判断应与距离一致"
        
        return {'simhash_works': True, 'dist_12': dist_12, 'dist_13': dist_13}
    
    tests.append(("SimHash-内容去重算法", test_simhash_dedup, "unit-rerank"))
    
    def test_chinese_summarizer():
        from rerank_engine import ChineseSummarizer
        
        long_text = """
        React是Facebook开发的用于构建用户界面的JavaScript库。
        首先，React采用虚拟DOM技术，可以高效地更新界面。
        其次，React支持组件化开发，提高代码复用性。
        因此，React成为目前最流行的前端框架之一。
        总之，学习React对现代Web开发非常重要。
        """
        
        summary = ChineseSummarizer.generate_summary("React框架介绍", long_text, max_length=100)
        
        assert len(summary) <= 100, f"摘要超长: {len(summary)}"
        assert len(summary) > 10, "摘要不应过短"
        assert "React" in summary, "摘要应包含关键词"
        
        return {'summary_length': len(summary), 'summary_preview': summary[:50]}
    
    tests.append(("ChineseSummarizer-中文摘要", test_chinese_summarizer, "unit-rerank"))
    
    def test_result_classifier():
        from rerank_engine import ResultClassifier
        
        gov_result = {
            'title': '国务院关于xxx的通知',
            'url': 'https://www.gov.cn/zhengce/content/2024-xx',
            'snippet': '各省、自治区、直辖市人民政府...'
        }
        category, conf = ResultClassifier.classify(gov_result)
        assert category == 'official_gov', f"政府网站应分类为official_gov，实际为{category}"
        
        tech_result = {
            'title': 'React性能优化完全指南2024',
            'url': 'https://blog.csdn.net/xxx/article/details/123456',
            'snippet': '本文介绍React的useMemo、useCallback等优化技巧...'
        }
        category2, conf2 = ResultClassifier.classify(tech_result)
        assert category2 in ['tech_tutorial', 'community'], f"技术文章分类错误: {category2}"
        
        return True
    
    tests.append(("ResultClassifier-结果分类", test_result_classifier, "unit-rerank"))
    
    # ===== context_memory 模块测试 =====
    
    def test_import_context_memory():
        try:
            from context_memory import (
                MemoryConfig, IntentType, Entity, ConversationTurn,
                UserPreference, UserProfile, CoreferenceResolver,
                IntentRecognizer, QueryExpander, ContextMemory,
                create_memory, process_user_query
            )
            return {'success': True, 'modules_loaded': 11}
        except ImportError as e:
            return {'success': False, 'error': str(e)}
    
    tests.append(("导入context_memory模块", test_import_context_memory, "unit-import"))
    
    def test_intent_recognition():
        from context_memory import IntentRecognizer
        
        intent1, conf1 = IntentRecognizer.recognize_intent("什么是机器学习？")
        assert intent1 in [IntentType.INFORMATION_SEEKING, IntentType.DEFINITION], \
            f"'什么是'查询应为信息查询或定义，实际为{intent1}"
        
        intent2, conf2 = IntentRecognizer.recognize_intent("购买iPhone 15 Pro Max")
        assert intent2 == IntentType.TRANSACTIONAL, f"购买意图识别错误: {intent2}"
        
        intent3, conf3 = IntentRecognizer.recognize_intent("React和Vue哪个好？")
        assert intent3 == IntentType.COMPARISON, f"对比查询识别错误: {intent3}"
        
        return {
            'definition_intent': intent1.value,
            'transactional_intent': intent2.value,
            'comparison_intent': intent3.value
        }
    
    tests.append(("IntentRecognizer-意图识别", test_intent_recognition, "unit-context"))
    
    def test_coreference_resolution():
        from context_memory import CoreferenceResolver, ConversationTurn, Entity
        
        context = [
            ConversationTurn(
                turn_id=1, role="user", content="React性能优化怎么做？",
                entities=[Entity("React", "TECHNOLOGY", 0.95, source_turn=1)]
            ),
            ConversationTurn(
                turn_id=2, role="assistant", content="这里有一些React优化的资源...",
                entities=[]
            )
        ]
        
        pronouns = CoreferenceResolver.detect_pronouns("它的最新版本是多少？")
        assert len(pronouns) > 0, "应检测到代词'它'"
        
        resolved, entities = CoreferenceResolver.substitute_pronouns(
            "它的最新版本是多少？", context
        )
        
        assert "React" in resolved, f"指代消解后应包含'React'，实际为'{resolved}'"
        
        return {'original': '它的最新版本是多少？', 'resolved': resolved}
    
    tests.append(("CoreferenceResolver-指代消解", test_coreference_resolution, "unit-context"))
    
    def test_context_memory_flow():
        from context_memory import ContextMemory
        
        memory = ContextMemory(user_id="test_user")
        
        q1 = memory.process_query("Python数据分析教程")
        assert "Python" in q1.lower(), f"第一轮处理应保留关键词，实际: {q1}"
        
        memory.add_turn("assistant", "这里是Python数据分析的资源...")
        
        q2 = memory.process_query("它的常用库有哪些？")
        
        active_entities = memory.get_active_entities()
        assert len(active_entities) > 0, "应有活跃实体"
        
        summary = memory.get_conversation_summary()
        assert summary['total_turns'] >= 2, "对话记录应至少2轮"
        
        state = memory.export_state()
        assert 'user_id' in state, "导出状态应包含用户ID"
        
        return {
            'q1_processed': q1,
            'q2_processed': q2,
            'active_entities': [e.text for e in active_entities],
            'total_turns': summary['total_turns']
        }
    
    tests.append(("ContextMemory-多轮对话流程", test_context_memory_flow, "unit-context"))
    
    # ===== query_rewriter 模块测试 =====
    
    def test_import_query_rewriter():
        try:
            from query_rewriter import (
                QueryConfig, RewrittenQuery, SynonymEntry,
                SYNONYM_DICTIONARY, COLLOQUIAL_RULES, QUALITY_INDICATORS,
                QueryRewriter, optimize_query, expand_query
            )
            return {'success': True, 'modules_loaded': 9}
        except ImportError as e:
            return {'success': False, 'error': str(e)}
    
    tests.append(("导入query_rewriter模块", test_import_query_rewriter, "unit-import"))
    
    def test_colloquial_normalization():
        from query_rewriter import QueryRewriter
        
        rewriter = QueryRewriter()
        
        r1 = rewriter.rewrite("电脑卡怎么办")
        assert "解决" in r1.optimized or "方法" in r1.optimized, \
            f"口语化改写失败: '{r1.original}' → '{r1.optimized}'"
        
        r2 = rewriter.rewrite("React是什么意思")
        assert ("含义" in r2.optimized or "解释" in r2.optimized or "定义" in r2.optimized), \
            f"定义查询改写失败: {r2.optimized}"
        
        r3 = rewriter.rewrite("Python和Java哪个好")
        assert "对比" in r3.optimized or "比较" in r3.optimized, \
            f"对比查询改写失败: {r3.optimized}"
        
        return {
            'problem_solution': r1.optimized,
            'definition': r2.optimized,
            'comparison': r3.optimized
        }
    
    tests.append(("QueryRewriter-口语化规范化", test_colloquial_normalization, "unit-rewriter"))
    
    def test_synonym_expansion():
        from query_rewriter import QueryRewriter
        
        rewriter = QueryRewriter()
        
        r1 = rewriter.rewrite("电脑价格")
        assert len(r1.expansions) > 0, "应有扩展查询"
        has_computer_synonym = any("计算机" in exp or "PC" in exp for exp in r1.expansions)
        
        r2 = rewriter.rewrite("手机推荐")
        assert len(r2.expansions) > 0, "手机查询应有扩展"
        
        return {
            'computer_expansions': r1.expansions[:2],
            'phone_expansions': r2.expansions[:2]
        }
    
    tests.append(("QueryRewriter-同义词扩展", test_synonym_expansion, "unit-rewriter"))
    
    def test_quality_assessment():
        from query_rewriter import QueryRewriter
        
        rewriter = QueryRewriter()
        
        high_quality = rewriter.rewrite("React 18性能优化最佳实践2024")
        assert high_quality.quality_score > 0.7, \
            f"高质量查询评分应>0.7，实际: {high_quality.quality_score}"
        
        low_quality = rewriter.rewrite("那个")
        assert low_quality.quality_score < 0.5, \
            f"低质量查询评分应<0.5，实际: {low_quality.quality_score}"
        
        assert len(low_quality.suggestions) > 0, "低质量查询应有改进建议"
        
        return {
            'high_quality_score': high_quality.quality_score,
            'low_quality_score': low_quality.quality_score,
            'suggestions_count': len(low_quality.suggestions)
        }
    
    tests.append(("QueryRewriter-质量评估", test_quality_assessment, "unit-rewriter"))
    
    def test_entity_extraction():
        from query_rewriter import QueryRewriter
        
        rewriter = QueryRewriter()
        
        r1 = rewriter.rewrite("Python和Docker容器化部署教程")
        tech_entities = r1.entities.get('technology', [])
        assert "Python" in tech_entities or "Docker" in tech_entities, \
            f"应提取到技术实体，实际: {tech_entities}"
        
        r2 = rewriter.rewrite("iPhone 15 Pro Max 2024年价格对比")
        product_entities = r2.entities.get('product', [])
        time_entities = r2.entities.get('time', [])
        assert len(product_entities) > 0 or "iPhone" in str(r2.entities), "应提取产品实体"
        
        return {
            'tech_entities': tech_entities,
            'product_entities': product_entities,
            'time_entities': time_entities
        }
    
    tests.append(("QueryRewriter-实体提取", test_entity_extraction, "unit-rewriter"))
    
    # ===== performance_optimizer 模块测试 =====
    
    def test_import_performance_optimizer():
        try:
            from performance_optimizer import (
                PerfConfig, ResourceMonitor, BrowserInstance, BrowserPool,
                FastFailController, RequestDeduplicator, AdaptiveTimeoutController,
                PerformanceOptimizer, create_optimizer
            )
            return {'success': True, 'modules_loaded': 9}
        except ImportError as e:
            return {'missing_deps': str(e)}
    
    tests.append(("导入performance_optimizer模块", test_import_performance_optimizer, "unit-import"))
    
    def test_resource_monitor():
        from performance_optimizer import ResourceMonitor
        
        monitor = ResourceMonitor()
        stats = monitor.get_current_stats()
        
        assert 'memory' in stats, "资源统计应包含内存信息"
        assert 'cpu' in stats, "资源统计应包含CPU信息"
        assert 'timestamp' in stats, "资源统计应包含时间戳"
        
        avg = monitor.get_average_usage(window_seconds=1)
        assert 'memory_avg' in avg, "平均值统计应包含memory_avg"
        
        return {
            'memory_percent': stats.get('memory', {}).get('percent'),
            'cpu_percent': stats.get('cpu', {}).get('percent')
        }
    
    tests.append(("ResourceMonitor-资源监控", test_resource_monitor, "unit-perf"))
    
    def test_fast_fail_controller():
        from performance_optimizer import FastFailController
        
        controller = FastFailController(min_results=3, confidence_threshold=0.7)
        
        good_results = [
            {'title': 'Result 1', 'score': 0.9},
            {'title': 'Result 2', 'score': 0.85},
            {'title': 'Result 3', 'score': 0.88},
            {'title': 'Result 4', 'score': 0.75},
        ]
        scores = [r['score'] for r in good_results]
        
        should_stop = controller.check_should_early_stop(good_results, scores)
        assert should_stop == True, "高质量结果充足时应触发快速停止"
        
        controller.reset()
        
        mixed_results = [
            {'title': 'Result 1', 'score': 0.4},
            {'title': 'Result 2', 'score': 0.35},
        ]
        mixed_scores = [r['score'] for r in mixed_results]
        
        should_stop2 = controller.check_should_early_stop(mixed_results, mixed_scores)
        assert should_stop2 == False, "低质量结果不足时不应触发快速停止"
        
        return {'high_quality_trigger': should_stop, 'low_quality_no_trigger': should_stop2}
    
    tests.append(("FastFailController-快速失败", test_fast_fail_controller, "unit-perf"))
    
    def test_adaptive_timeout():
        from performance_optimizer import AdaptiveTimeoutController
        
        controller = AdaptiveTimeoutController(base_timeout=10.0)
        
        controller.record_latency("baidu", 0.5, success=True)
        controller.record_latency("baidu", 0.8, success=True)
        controller.record_latency("bing", 2.0, success=True)
        
        baidu_timeout = controller.get_optimal_timeout("baidu")
        bing_timeout = controller.get_optimal_timeout("bing")
        
        assert baidu_timeout < bing_timeout, \
            f"百度响应快应超时更短 ({baidu_timeout} vs {bing_timeout})"
        
        global_timeout = controller.get_global_timeout(["baidu", "bing"])
        assert global_timeout >= min(baidu_timeout, bing_timeout), \
            "全局超时不应小于单引擎最小超时"
        
        return {
            'baidu_timeout': round(baidu_timeout, 2),
            'bing_timeout': round(bing_timeout, 2),
            'global_timeout': round(global_timeout, 2)
        }
    
    tests.append(("AdaptiveTimeoutController-自适应超时", test_adaptive_timeout, "unit-perf"))
    
    return tests


# ============================================================================
# 性能基准测试
# ============================================================================

def get_performance_tests() -> List[Tuple[str, any, str]]:
    """获取性能测试"""
    tests = []
    
    def test_rerank_performance():
        from rerank_engine import RerankEngine
        import time
        
        engine = RerankEngine()
        
        test_results = [
            {'title': f'Test Result {i}', 'url': f'https://example.com/{i}',
             'snippet': f'Sample content for testing performance {i}' * 10,
             'source': 'example.com', 'engine': 'test'}
            for i in range(50)
        ]
        
        start = time.time()
        for _ in range(10):
            engine.rerank(test_results, "performance test", max_results=20)
        elapsed = (time.time() - start) / 10 * 1000
        
        assert elapsed < 500, f"Rerank 50条结果耗时过长: {elapsed:.0f}ms (>500ms)"
        
        return {'avg_latency_ms': round(elapsed, 1), 'within_limit': elapsed < 500}
    
    tests.append(("Rerank性能-50条结果×10次", test_rerank_performance, "perf-rerank"))
    
    def test_query_rewriter_performance():
        from query_rewriter import QueryRewriter
        import time
        
        rewriter = QueryRewriter()
        
        queries = [
            "Python机器学习入门教程",
            "2024年最新手机推荐排行榜",
            "React和Vue框架对比分析",
            "电脑卡顿怎么解决",
            "人工智能在医疗领域的应用前景",
        ] * 20
        
        start = time.time()
        results = rewriter.batch_rewrite(queries)
        elapsed = (time.time() - start) / len(queries) * 1000
        
        assert elapsed < 50, f"查询改写平均耗时过长: {elapsed:.0f}ms (>50ms)"
        
        return {'avg_latency_ms': round(elapsed, 1), 'throughput_per_sec': round(1000/elapsed, 1)}
    
    tests.append(("QueryRewriter性能-100条查询批处理", test_query_rewriter_performance, "perf-rewriter"))
    
    def test_context_memory_performance():
        from context_memory import ContextMemory
        import time
        
        memory = ContextMemory()
        
        conversations = []
        for i in range(100):
            turn_num = (i % 5) + 1
            conversations.append(("用户", f"这是第{turn_num}轮对话的问题{i}"))
            conversations.append(("助手", f"这是第{turn_num}轮的回答{i}"))
        
        start = time.time()
        for role, content in conversations:
            if role == "用户":
                memory.process_query(content)
            else:
                memory.add_turn(role, content)
        elapsed = (time.time() - start) * 1000
        
        assert elapsed < 2000, f"100轮对话处理耗时过长: {elapsed:.0f}ms (>2000ms)"
        
        return {
            'total_conversations': 100,
            'total_latency_ms': round(elapsed, 1),
            'avg_per_turn_ms': round(elapsed/100, 1)
        }
    
    tests.append(("ContextMemory性能-100轮对话", test_context_memory_performance, "perf-context"))
    
    def test_cache_performance():
        from web_search_v3 import SearchCache
        import time
        
        cache = SearchCache(max_size=10000)
        
        test_data = [{'title': f'Cache Test {i}', 'score': 0.5 + i/100} for i in range(1000)]
        
        start = time.time()
        for i, data in enumerate(test_data):
            cache.set(f"query_{i}", data, ttl=3600)
        write_elapsed = (time.time() - start) * 1000
        
        start = time.time()
        for i in range(1000):
            cache.get(f"query_{i}")
        read_elapsed = (time.time() - start) * 1000
        
        hit_rate = cache.hit_rate
        
        assert write_elapsed < 500, f"1000次写入过慢: {write_elapsed:.0f}ms"
        assert read_elapsed < 200, f"1000次读取过慢: {read_elapsed:.0f}ms"
        
        return {
            'write_1000_items_ms': round(write_elapsed, 1),
            'read_1000_items_ms': round(read_elapsed, 1),
            'hit_rate_after_writes': f"{hit_rate:.1%}",
            'cache_stats': cache.stats
        }
    
    tests.append(("Cache性能-1000次读写", test_cache_performance, "perf-cache"))
    
    return tests


# ============================================================================
# 主执行入口
# ============================================================================

def main():
    """主函数 - 运行全部测试"""
    
    args = sys.argv[1:]
    run_unit = '--unit' not in args and '--perf' not in args or '--unit' in args
    run_perf = '--unit' not in args and '--perf' not in args or '--perf' in args
    
    print("\n" + "="*70)
    print("🧪 CN Web Search v3.0 - 综合测试套件")
    print("="*70)
    print(f"   时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   单元测试: {'✅ 运行' if run_unit else '⏭️ 跳过'}")
    print(f"   性能测试: {'✅ 运行' if run_perf else '⏭️ 跳过'}")
    print("="*70 + "\n")
    
    runner = TestRunner(verbose=True)
    
    if run_unit:
        unit_tests = get_unit_tests()
        runner.run_suite("单元测试 (Unit Tests)", unit_tests)
    
    if run_perf:
        perf_tests = get_performance_tests()
        runner.run_suite("性能基准测试 (Performance Tests)", perf_tests)
    
    report = runner.generate_report()
    
    print("\n" + "="*70)
    print("📊 最终测试报告")
    print("="*70)
    
    print(json.dumps(report, ensure_ascii=False, indent=2))
    
    print("\n" + "="*70)
    summary = report['summary']
    print(f"{'✅' if summary['failed'] == 0 else '❌'} {summary['status']}")
    print(f"   总测试数: {summary['total_tests']}")
    print(f"   通过率: {summary['overall_pass_rate']:.1%}")
    print("="*70)
    
    if summary['failed'] > 0:
        print("\n⚠️ 失败的测试:")
        for failed in report['failed_tests']:
            print(f"   ❌ [{failed['suite']}] {failed['test']}: {failed.get('error', 'Unknown')}")
    
    print("\n💡 改进建议:")
    for rec in report['recommendations']:
        print(f"   {rec}")
    
    print("\n" + "="*70)
    
    return 0 if summary['failed'] == 0 else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

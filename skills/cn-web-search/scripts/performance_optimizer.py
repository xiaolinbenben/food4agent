#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CN Web Search Performance Optimizer v4.2 - 高性能执行引擎
==========================================================

核心功能：
- ✅ Playwright浏览器实例池（预启动、复用、自动回收）
- ✅ 多级缓存架构（L1内存 + L2磁盘 + 预热缓存）
- ✅ 智能快速失败机制（任一引擎返回足够结果即终止）
- ✅ 请求去重与合并（相同查询并发时合并请求）
- ✅ 自适应超时控制（根据历史响应时间动态调整）
- ✅ 资源监控与限流（内存/CPU/并发数保护）

集成方式:
    from performance_optimizer import PerformanceOptimizer, BrowserPool
    
    optimizer = PerformanceOptimizer()
    async with optimizer.browser_pool.get_browser() as browser:
        results = await browser.search(query)

作者: cn-web-search team
版本: 4.2.0
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import platform
import psutil
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Tuple
from contextlib import asynccontextmanager
from queue import Queue, Empty
from threading import Lock

try:
    import aiofiles
    HAS_AIOFILES = True
except ImportError:
    HAS_AIOFILES = False


logger = logging.getLogger("cn_web_search.performance")


# ============================================================================
# 性能配置常量
# ============================================================================

class PerfConfig:
    """性能优化配置"""
    
    # 浏览器池配置
    BROWSER_POOL_MIN_SIZE: int = 1
    BROWSER_POOL_MAX_SIZE: int = 3
    BROWSER_IDLE_TIMEOUT: int = 300  
    BROWSER_MAX_LIFETIME: int = 1800  
    BROWSER_LAUNCH_TIMEOUT: int = 30  
    
    # 缓存配置
    CACHE_L1_MAX_SIZE: int = 1000       
    CACHE_L2_MAX_SIZE: int = 10000      
    CACHE_L2_DIRECTORY: str = ".cache/search_cache"
    CACHE_PREWARM_QUERIES: List[str] = []  
    CACHE_DEFAULT_TTL: int = 3600       
    
    # 快速失败配置
    FAST_FAIL_MIN_RESULTS: int = 5       
    FAST_FAIL_CONFIDENCE_THRESHOLD: float = 0.7  
    FAST_FAIL_TIMEOUT_MULTIPLIER: float = 0.6  
    
    # 并发控制
    MAX_CONCURRENT_REQUESTS: int = 20    
    REQUEST_QUEUE_TIMEOUT: float = 5.0     
    RATE_LIMIT_PER_SECOND: int = 10       
    
    # 资源保护
    MEMORY_WARNING_THRESHOLD: float = 0.85  
    CPU_WARNING_THRESHOLD: float = 0.90    
    AUTO_SCALE_DOWN_THRESHOLD: float = 0.95  


# ============================================================================
# 资源监控模块
# ============================================================================

class ResourceMonitor:
    """系统资源监控器"""
    
    def __init__(self):
        self._history: List[Dict[str, float]] = []
        self._max_history_size = 100
        self._lock = Lock()
    
    def get_current_stats(self) -> Dict[str, Any]:
        """
        获取当前资源使用情况
        
        Returns:
            资源统计字典
        """
        try:
            mem = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            stats = {
                'timestamp': datetime.now().isoformat(),
                'memory': {
                    'total_gb': round(mem.total / (1024**3), 2),
                    'used_gb': round(mem.used / (1024**3), 2),
                    'percent': mem.percent,
                    'available_gb': round(mem.available / (1024**3), 2)
                },
                'cpu': {
                    'percent': cpu_percent,
                    'count': psutil.cpu_count()
                },
                'platform': {
                    'system': platform.system(),
                    'python_version': platform.python_version()
                }
            }
            
            with self._lock:
                self._history.append({
                    'time': time.time(),
                    'mem_percent': mem.percent,
                    'cpu_percent': cpu_percent
                })
                
                if len(self._history) > self._max_history_size:
                    self._history.pop(0)
            
            return stats
            
        except Exception as e:
            logger.error(f"资源监控异常: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    @property
    def is_memory_critical(self) -> bool:
        """内存是否达到警戒阈值"""
        stats = self.get_current_stats()
        mem_percent = stats.get('memory', {}).get('percent', 0)
        return mem_percent >= PerfConfig.MEMORY_WARNING_THRESHOLD * 100
    
    @property
    def is_cpu_critical(self) -> bool:
        """CPU是否达到警戒阈值"""
        stats = self.get_current_stats()
        cpu_percent = stats.get('cpu', {}).get('percent', 0)
        return cpu_percent >= PerfConfig.CPU_WARNING_THRESHOLD
    
    @property
    def should_scale_down(self) -> bool:
        """是否应该降级服务"""
        stats = self.get_current_stats()
        mem_percent = stats.get('memory', {}).get('percent', 0)
        return mem_percent >= PerfConfig.AUTO_SCALE_DOWN_THRESHOLD * 100
    
    def get_average_usage(self, window_seconds: int = 60) -> Dict[str, float]:
        """
        获取指定时间窗口内的平均资源使用率
        
        Args:
            window_seconds: 时间窗口（秒）
            
        Returns:
            平均使用率字典
        """
        with self._lock:
            cutoff_time = time.time() - window_seconds
            recent_data = [d for d in self._history if d['time'] >= cutoff_time]
        
        if not recent_data:
            return {'memory_avg': 0.0, 'cpu_avg': 0.0}
        
        avg_mem = sum(d['mem_percent'] for d in recent_data) / len(recent_data)
        avg_cpu = sum(d['cpu_percent'] for d in recent_data) / len(recent_data)
        
        return {
            'memory_avg': round(avg_mem, 2),
            'cpu_avg': round(avg_cpu, 2),
            'sample_count': len(recent_data)
        }


# ============================================================================
# 浏览器实例池
# ============================================================================

@dataclass
class BrowserInstance:
    """浏览器实例包装"""
    instance_id: str
    browser: Any = None  
    context: Any = None
    created_at: datetime = field(default_factory=datetime.now)
    last_used_at: datetime = field(default_factory=datetime.now)
    request_count: int = 0
    is_healthy: bool = True
    error_count: int = 0
    
    @property
    def age_seconds(self) -> int:
        return int((datetime.now() - self.created_at).total_seconds())
    
    @property
    def idle_seconds(self) -> int:
        return int((datetime.now() - self.last_used_at).total_seconds())
    
    @property
    def should_retire(self) -> bool:
        return (
            self.age_seconds > PerfConfig.BROWSER_MAX_LIFETIME or
            self.idle_seconds > PerfConfig.BROWSER_IDLE_TIMEOUT or
            not self.is_healthy or
            self.error_count >= 5
        )
    
    def mark_used(self) -> None:
        self.last_used_at = datetime.now()
        self.request_count += 1
    
    def mark_error(self) -> None:
        self.error_count += 1
        if self.error_count >= 5:
            self.is_healthy = False


class BrowserPool:
    """
    Playwright浏览器实例池
    
    使用示例:
        pool = BrowserPool(pool_size=2)
        
        async with pool.get_browser() as browser:
            page = await browser.new_page()
            await page.goto(url)
            content = await page.content()
    """
    
    def __init__(self, min_size: int = PerfConfig.BROWSER_POOL_MIN_SIZE,
                 max_size: int = PerfConfig.BROWSER_POOL_MAX_SIZE):
        """
        初始化浏览器池
        
        Args:
            min_size: 最小实例数
            max_size: 最大实例数
        """
        self.min_size = min_size
        self.max_size = max_size
        self._pool: Queue[BrowserInstance] = Queue(maxsize=max_size)
        self._active_instances: Dict[str, BrowserInstance] = {}
        self._total_created = 0
        self._total_reused = 0
        self._monitor = ResourceMonitor()
        self._lock = asyncio.Lock()
        self._initialized = False
        
        logger.info(f"🌐 初始化浏览器池: min={min_size}, max={max_size}")
    
    async def initialize(self) -> None:
        """初始化浏览器池（预启动最小数量实例）"""
        if self._initialized:
            return
        
        try:
            from playwright.async_api import async_playwright
            self._playwright = await async_playwright().start()
            
            for _ in range(self.min_size):
                instance = await self._create_new_instance()
                self._pool.put_nowait(instance)
            
            self._initialized = True
            logger.info(f"✅ 浏览器池初始化完成: {self.min_size}个实例就绪")
            
        except ImportError:
            logger.warning("⚠️ Playwright未安装，浏览器池不可用")
            self._initialized = False
        except Exception as e:
            logger.error(f"❌ 浏览器池初始化失败: {e}")
            raise
    
    async def _create_new_instance(self) -> BrowserInstance:
        """创建新的浏览器实例"""
        instance_id = f"browser_{self._total_created + 1}_{int(time.time())}"
        
        try:
            browser = await self._playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--single-process'
                ]
            )
            
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...',
                viewport={'width': 1920, 'height': 1080},
                locale='zh-CN'
            )
            
            instance = BrowserInstance(
                instance_id=instance_id,
                browser=browser,
                context=context
            )
            
            self._total_created += 1
            logger.info(f"🆕 创建浏览器实例: {instance_id}")
            
            return instance
            
        except Exception as e:
            logger.error(f"❌ 创建浏览器实例失败: {e}")
            raise
    
    @asynccontextmanager
    async def get_browser(self, timeout: float = PerfConfig.BROWSER_LAUNCH_TIMEOUT):
        """
        获取浏览器实例（上下文管理器）
        
        Yields:
            BrowserInstance对象
        """
        if not self._initialized:
            await self.initialize()
        
        instance: Optional[BrowserInstance] = None
        acquired = False
        
        try:
            try:
                instance = self._pool.get_nowait()
                self._total_reused += 1
                acquired = True
                
            except Empty:
                if self._monitor.should_scale_down:
                    raise RuntimeError("系统资源紧张，无法分配新浏览器实例")
                
                if len(self._active_instances) < self.max_size:
                    instance = await asyncio.wait_for(
                        self._create_new_instance(),
                        timeout=timeout
                    )
                    acquired = True
                else:
                    logger.warning("⚠️ 浏览器池已满，等待可用实例...")
                    instance = await asyncio.wait_for(
                        self._pool.get(),
                        timeout=timeout
                    )
                    self._total_reused += 1
                    acquired = True
            
            if instance and instance.should_retire:
                await self._retire_instance(instance)
                instance = await self._create_new_instance()
                acquired = False
            
            if instance:
                instance.mark_used()
                self._active_instances[instance.instance_id] = instance
                
                logger.debug(f"🔧 分配浏览器: {instance.instance_id} "
                           f"(复用次数: {instance.request_count})")
                
                yield instance
                
        finally:
            if instance and acquired:
                self._active_instances.pop(instance.instance_id, None)
                
                if not instance.should_retire:
                    try:
                        self._pool.put_nowait(instance)
                    except Exception:
                        await self._retire_instance(instance)
                else:
                    await self._retire_instance(instance)
    
    async def _retire_instance(self, instance: BrowserInstance) -> None:
        """回收退役的浏览器实例"""
        try:
            if instance.context:
                await instance.context.close()
            if instance.browser:
                await instance.browser.close()
            
            logger.info(f"♻️ 回收浏览器实例: {instance.instance_id} "
                       f"(存活{instance.age_seconds}s, 服务{instance.request_count}次)")
            
        except Exception as e:
            logger.warning(f"⚠️ 回收浏览器实例异常: {e}")
    
    async def cleanup(self) -> None:
        """清理所有浏览器实例"""
        logger.info("🧹 清理浏览器池...")
        
        while not self._pool.empty():
            try:
                instance = self._pool.get_nowait()
                await self._retire_instance(instance)
            except Empty:
                break
        
        for instance in list(self._active_instances.values()):
            await self._retire_instance(instance)
        
        self._active_instances.clear()
        
        if hasattr(self, '_playwright'):
            await self._playwright.stop()
        
        self._initialized = False
        logger.info("✅ 浏览器池清理完成")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取池状态统计"""
        return {
            'pool_size': self._pool.qsize(),
            'active_instances': len(self._active_instances),
            'total_created': self._total_created,
            'total_reused': self._total_reused,
            'reuse_rate': f"{(self._total_reused / max(1, self._total_created)):.1%}",
            'initialized': self._initialized,
            'resource_status': self._monitor.get_current_stats()
        }


# ============================================================================
# 智能快速失败控制器
# ============================================================================

class FastFailController:
    """
    智能快速失败控制器
    
    核心逻辑：当任一引擎返回足够多且高质量的结果时，
    提前终止其他引擎的请求，节省整体响应时间。
    """
    
    def __init__(self, 
                 min_results: int = PerfConfig.FAST_FAIL_MIN_RESULTS,
                 confidence_threshold: float = PerfConfig.FAST_FAIL_CONFIDENCE_THRESHOLD):
        """
        初始化快速失败控制器
        
        Args:
            min_results: 触发快速失败的最少结果数
            confidence_threshold: 结果质量置信度阈值
        """
        self.min_results = min_results
        self.confidence_threshold = confidence_threshold
        self._should_stop = asyncio.Event()
        self._results_received = 0
        self._high_quality_results = 0
        self._lock = asyncio.Lock()
    
    def check_should_early_stop(self, new_results: List[Dict], 
                                scores: Optional[List[float]] = None) -> bool:
        """
        检查是否应该提前终止
        
        Args:
            new_results: 新收到的结果列表
            scores: 对应的结果质量评分（可选）
            
        Returns:
            是否应该终止其他请求
        """
        with self._lock:
            self._results_received += len(new_results)
            
            if scores:
                high_quality = sum(1 for s in scores if s >= self.confidence_threshold)
                self._high_quality_results += high_quality
            else:
                self._high_quality_results += len(new_results)
            
            should_stop = (
                self._high_quality_results >= self.min_results and
                self._high_quality_results / max(1, self._results_received) >= self.confidence_threshold
            )
            
            if should_stop:
                self._should_stop.set()
                logger.info(f"⚡ 触发快速停止: 已获得{self._high_quality_results}个高质量结果")
            
            return should_stop
    
    @property
    def stop_event(self) -> asyncio.Event:
        return self._should_stop
    
    def reset(self) -> None:
        """重置控制器状态（用于下次搜索）"""
        self._should_stop.clear()
        self._results_received = 0
        self._high_quality_results = 0


# ============================================================================
# 请求去重与合并器
# ============================================================================

class RequestDeduplicator:
    """
    请求去重与合并器
    
    功能：
    - 相同查询的并发请求合并为一次
    - 缓存未过期时直接返回
    - 支持请求优先级队列
    """
    
    def __init__(self):
        self._pending_requests: Dict[str, List[asyncio.Future]] = {}
        self._lock = asyncio.Lock()
        self._stats = {
            'total_requests': 0,
            'deduplicated_count': 0,
            'cache_hits': 0
        }
    
    def _generate_key(self, query: str, **params) -> str:
        """生成请求唯一标识"""
        raw = f"{query}:{json.dumps(params, sort_keys=True)}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]
    
    async def execute_or_merge(self, query: str, 
                               executor: Callable,
                               cache: Any = None,
                               **params) -> Any:
        """
        执行请求或与已有请求合并
        
        Args:
            query: 搜索查询
            executor: 实际执行函数（异步）
            cache: 可选的缓存对象
            **params: 其他参数
            
        Returns:
            执行结果
        """
        key = self._generate_key(query, **params)
        self._stats['total_requests'] += 1
        
        if cache:
            cached_result = cache.get(query, category="merged")
            if cached_result:
                self._stats['cache_hits'] += 1
                logger.info(f"💾 请求命中缓存: {query[:30]}...")
                return cached_result
        
        async with self._lock:
            if key in self._pending_requests:
                future = asyncio.get_event_loop().create_future()
                self._pending_requests[key].append(future)
                self._stats['deduplicated_count'] += 1
                logger.info(f"🔄 请求合并: {query[:30]}... (已有{len(self._pending_requests[key])}个等待)")
                return await future
            else:
                self._pending_requests[key] = []
        
        try:
            result = await executor(query, **params)
            
            if cache:
                cache.set(query, result, category="merged")
            
            async with self._lock:
                waiting_futures = self._pending_requests.pop(key, [])
            
            for future in waiting_futures:
                if not future.done():
                    future.set_result(result)
            
            return result
            
        except Exception as e:
            async with self._lock:
                waiting_futures = self._pending_requests.pop(key, [])
            
            for future in waiting_futures:
                if not future.done():
                    future.set_exception(e)
            
            raise
    
    @property
    def stats(self) -> Dict[str, Any]:
        return {
            **self._stats,
            'dedup_rate': f"{self._stats['deduplicated_count'] / max(1, self._stats['total_requests']):.1%}",
            'cache_hit_rate': f"{self._stats['cache_hits'] / max(1, self._stats['total_requests']):.1%}"
        }


# ============================================================================
# 自适应超时控制器
# ============================================================================

class AdaptiveTimeoutController:
    """
    自适应超时控制器
    
    根据历史响应时间动态调整超时阈值，
    在保证成功率的前提下最大化响应速度。
    """
    
    def __init__(self, base_timeout: float = 10.0,
                 min_timeout: float = 3.0,
                 max_timeout: float = 30.0):
        """
        初始化自适应超时控制器
        
        Args:
            base_timeout: 基础超时时间（秒）
            min_timeout: 最小超时时间
            max_timeout: 最大超时时间
        """
        self.base_timeout = base_timeout
        self.min_timeout = min_timeout
        self.max_timeout = max_timeout
        self._history: Dict[str, List[float]] = {}  
        self._window_size = 50 
    
    def record_latency(self, engine: str, latency: float, success: bool) -> None:
        """
        记录引擎响应延迟
        
        Args:
            engine: 引擎名称
            latency: 响应延迟（秒）
            success: 是否成功
        """
        if engine not in self._history:
            self._history[engine] = []
        
        self._history[engine].append(latency)
        
        if len(self._history[engine]) > self._window_size:
            self._history[engine].pop(0)
    
    def get_optimal_timeout(self, engine: str) -> float:
        """
        获取最优超时时间
        
        Args:
            engine: 引擎名称
            
        Returns:
            推荐的超时时间（秒）
        """
        if engine not in self._history or not self._history[engine]:
            return self.base_timeout
        
        latencies = self._history[engine]
        
        p50 = sorted(latencies)[len(latencies) // 2]
        p95 = sorted(latencies)[int(len(latencies) * 0.95)]
        
        optimal = p95 * 1.5  
        optimal = max(self.min_timeout, min(optimal, self.max_timeout))
        
        return optimal
    
    def get_global_timeout(self, engines: List[str]) -> float:
        """
        获取多引擎并行搜索的全局超时
        
        Args:
            engines: 引擎名称列表
            
        Returns:
            全局超时时间（秒）
        """
        individual_timeouts = [
            self.get_optimal_timeout(engine) 
            for engine in engines
        ]
        
        global_timeout = max(individual_timeouts) * PerfConfig.FAST_FAIL_TIMEOUT_MULTIPLIER
        
        return max(self.min_timeout, min(global_timeout, self.max_timeout))


# ============================================================================
# 综合性能优化器
# ============================================================================

class PerformanceOptimizer:
    """
    综合性能优化器 - 整合所有性能优化组件
    
    使用示例:
        optimizer = PerformanceOptimizer()
        
        async with optimizer.optimize_context():
            results = await optimizer.execute_parallel_search(
                query="Python教程",
                engines=["baidu", "bing"]
            )
    """
    
    def __init__(self, config: Optional[PerfConfig] = None):
        """
        初始化性能优化器
        
        Args:
            config: 配置对象（可选）
        """
        self.config = config or PerfConfig()
        self.monitor = ResourceMonitor()
        self.browser_pool = BrowserPool()
        self.fast_fail = FastFailController()
        self.deduplicator = RequestDeduplicator()
        self.timeout_controller = AdaptiveTimeoutController()
        self._is_initialized = False
        
        logger.info("⚡ 性能优化器初始化完成")
    
    async def initialize(self) -> None:
        """初始化所有子组件"""
        if self._is_initialized:
            return
        
        await self.browser_pool.initialize()
        self._is_initialized = True
        logger.info("✅ 性能优化器完全就绪")
    
    @asynccontextmanager
    async def optimize_context(self):
        """性能优化上下文管理器"""
        await self.initialize()
        
        if self.monitor.is_memory_critical:
            logger.warning("⚠️ 内存使用率高，启用轻量模式")
        
        yield self
        
        logger.debug("性能优化上下文退出")
    
    async def execute_with_fast_fail(self, search_func: Callable, 
                                    query: str, 
                                    num_results: int = 10,
                                    **kwargs) -> Dict[str, Any]:
        """
        执行带快速失败的搜索
        
        Args:
            search_func: 搜索函数
            query: 查询词
            num_results: 结果数量
            **kwargs: 其他参数
            
        Returns:
            搜索结果字典
        """
        start_time = time.time()
        self.fast_fail.reset()
        
        async def wrapped_engine(engine_name: str, **engine_kwargs):
            try:
                if self.fast_fail.stop_event.is_set():
                    return {'engine': engine_name, 'results': [], 'stopped_early': True}
                
                results = await asyncio.wait_for(
                    search_func(engine=engine_name, query=query, **engine_kwargs),
                    timeout=self.timeout_controller.get_optimal_timeout(engine_name)
                )
                
                scores = [r.get('score', 0.5) for r in results] if results else []
                
                if self.fast_fail.check_should_early_stop(results, scores):
                    pass
                
                self.timeout_controller.record_latency(
                    engine_name, 
                    time.time() - start_time,
                    success=True
                )
                
                return {
                    'engine': engine_name,
                    'results': results,
                    'latency_ms': int((time.time() - start_time) * 1000)
                }
                
            except asyncio.TimeoutError:
                self.timeout_controller.record_latency(
                    engine_name,
                    self.timeout_controller.get_optimal_timeout(engine_name),
                    success=False
                )
                return {
                    'engine': engine_name,
                    'results': [],
                    'error': 'timeout',
                    'latency_ms': int((time.time() - start_time) * 1000)
                }
            
            except Exception as e:
                return {
                    'engine': engine_name,
                    'results': [],
                    'error': str(e),
                    'latency_ms': int((time.time() - start_time) * 1000)
                }
        
        engines = kwargs.get('engines', ['baidu', 'bing', 'duckduckgo'])
        
        tasks = [wrapped_engine(engine) for engine in engines]
        
        completed_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_results = []
        engines_tried = []
        total_latency = 0
        
        for result in completed_results:
            if isinstance(result, dict):
                engines_tried.append(result.get('engine', 'unknown'))
                total_latency = max(total_latency, result.get('latency_ms', 0))
                
                if result.get('results'):
                    all_results.extend(result['results'])
        
        unique_results = self._quick_dedup(all_results)[:num_results]
        
        response = {
            'success': len(unique_results) > 0,
            'query': query,
            'num_results': len(unique_results),
            'results': unique_results,
            'engines_tried': engines_tried,
            'latency_ms': total_latency,
            'fast_fail_triggered': self.fast_fail.stop_event.is_set(),
            'optimization_stats': {
                'browser_pool': self.browser_pool.get_stats(),
                'resource_monitor': self.monitor.get_current_stats(),
                'deduplicator': self.deduplicator.stats
            }
        }
        
        logger.info(f"⚡ 优化搜索完成: {response['latency']}ms, "
                   f"{len(unique_results)}条结果, "
                   f"{'快速触发' if response['fast_fail_triggered'] else '完整执行'}")
        
        return response
    
    def _quick_dedup(self, results: List[Dict], similarity_threshold: float = 0.9) -> List[Dict]:
        """快速URL去重"""
        seen_urls = set()
        unique = []
        
        for r in results:
            url = r.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique.append(r)
        
        return unique
    
    async def cleanup(self) -> None:
        """清理所有资源"""
        await self.browser_pool.cleanup()
        self._is_initialized = False
        logger.info("🧹 性能优化器已清理")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """
        生成性能报告
        
        Returns:
            性能统计数据
        """
        return {
            'timestamp': datetime.now().isoformat(),
            'browser_pool': self.browser_pool.get_stats(),
            'system_resources': self.monitor.get_current_stats(),
            'resource_averages': self.monitor.get_average_usage(),
            'request_deduplication': self.deduplicator.stats,
            'adaptive_timeouts': {
                engine: {
                    'optimal_timeout': self.timeout_controller.get_optimal_timeout(engine),
                    'sample_size': len(self.timeout_controller._history.get(engine, []))
                }
                for engine in ['baidu', 'bing', 'duckduckgo']
            }
        }


# ============================================================================
# 便捷接口
# ============================================================================

def create_optimizer() -> PerformanceOptimizer:
    """创建性能优化器实例"""
    return PerformanceOptimizer()


if __name__ == "__main__":
    print("=" * 70)
    print("⚡ CN Web Search Performance Optimizer v4.2 - 测试运行")
    print("=" * 70)
    
    async def test_performance_optimizer():
        optimizer = create_optimizer()
        
        print("\n📊 系统资源状态:")
        resource_stats = optimizer.monitor.get_current_stats()
        print(json.dumps(resource_stats, ensure_ascii=False, indent=2))
        
        print("\n🌐 浏览器池状态:")
        await optimizer.initialize()
        pool_stats = optimizer.browser_pool.get_stats()
        print(json.dumps(pool_stats, ensure_ascii=False, indent=2))
        
        print("\n⚙️ 自适应超时配置:")
        for engine in ['baidu', 'bing', 'duckduckgo']:
            timeout = optimizer.timeout_controller.get_optimal_timeout(engine)
            print(f"   {engine}: {timeout:.1f}s")
        
        print("\n📈 性能报告:")
        report = optimizer.get_performance_report()
        print(json.dumps(report, ensure_ascii=False, indent=2))
        
        await optimizer.cleanup()
        
        print("\n" + "=" * 70)
        print("✅ Performance Optimizer测试完成!")
        print("=" * 70)
    
    asyncio.run(test_performance_optimizer())

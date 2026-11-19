#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CN Web Search Context Memory v4.2 - 上下文记忆与多轮意图理解系统
================================================================

核心功能：
- ✅ 短时对话上下文窗口（最近N轮）
- ✅ 指代消解（"它"、"这个"、"刚才那个"→实体替换）
- ✅ 查询纠错与补全（基于上下文推测完整意图）
- ✅ 用户画像构建（长期兴趣偏好学习）
- ✅ 意图识别与分类
- ✅ 多轮检索策略优化建议

使用示例:
    from context_memory import ContextMemory
    
    memory = ContextMemory()
    
    # 第一轮
    memory.add_turn("用户", "React性能优化怎么做？")
    response1 = search(memory.process_query("React性能优化怎么做？"))
    
    # 第二轮（自动理解"它的价格"指代React相关工具）
    memory.add_turn("用户", "它的最新版本是多少？")
    processed = memory.process_query("它的最新版本是多少？")
    # processed => "React 最新版本" （自动替换指代）

作者: cn-web-search team
版本: 4.2.0
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple, TypedDict


logger = logging.getLogger("cn_web_search.context")


# ============================================================================
# 常量配置
# ============================================================================

class MemoryConfig:
    """记忆系统配置"""
    
    MAX_CONTEXT_TURNS: int = 10  
    MAX_SHORT_TERM_MEMORY: int = 50  
    ENTITY_EXPIRE_HOURS: int = 2  
    USER_PROFILE_UPDATE_THRESHOLD: int = 5  
    COREF_RESOLUTION_CONFIDENCE: float = 0.7  
    QUERY_EXPANSION_LIMIT: int = 3  


# ============================================================================
# 数据模型
# ============================================================================

class IntentType(Enum):
    """意图类型枚举"""
    INFORMATION_SEEKING = "信息查询"
    NAVIGATION = " 导航访问"
    TRANSACTIONAL = "事务操作"
    COMPARISON = "对比选择"
    HOW_TO = "方法教程"
    DEFINITION = "定义解释"
    NEWS_CHECKING = "新闻查看"
    LOCAL_SEARCH = "本地搜索"
    UNKNOWN = "未知"


@dataclass
class Entity:
    """实体对象"""
    text: str
    entity_type: str  
    confidence: float
    source_turn: int  
    mentioned_count: int = 1
    last_mentioned: datetime = field(default_factory=datetime.now)
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_expired(self) -> bool:
        return datetime.now() > self.last_mentioned + timedelta(hours=MemoryConfig.ENTITY_EXPIRE_HOURS)
    
    @property
    def is_fresh(self) -> bool:
        return not self.is_expired and self.confidence >= MemoryConfig.COREF_RESOLUTION_CONFIDENCE


@dataclass
class ConversationTurn:
    """单轮对话记录"""
    turn_id: int
    role: str  
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    processed_content: Optional[str] = None
    intent: Optional[IntentType] = None
    entities: List[Entity] = field(default_factory=list)
    search_results_summary: Optional[Dict[str, Any]] = None
    feedback: Optional[str] = None  


@dataclass
class UserPreference:
    """用户偏好标签"""
    category: str  
    value: str  
    weight: float = 0.5  
    last_updated: datetime = field(default_factory=datetime.now)
    interaction_count: int = 0


@dataclass
class UserProfile:
    user_id: str = "default"
    preferences: List[UserPreference] = field(default_factory=list)
    frequent_queries: List[Tuple[str, int]] = field(default_factory=list)
    preferred_engines: Dict[str, float] = field(default_factory=dict)
    language_style: str = "formal"
    domain_expertise: Dict[str, float] = field(default_factory=dict)
    preferred_domains: List[str] = field(default_factory=list)
    domain_weights: Dict[str, float] = field(default_factory=dict)  
    
    def update_preference(self, category: str, value: str, 
                          weight_increase: float = 0.1) -> None:
        """更新偏好"""
        existing = next((p for p in self.preferences 
                        if p.category == category and p.value == value), None)
        
        if existing:
            existing.weight = min(1.0, existing.weight + weight_increase)
            existing.interaction_count += 1
            existing.last_updated = datetime.now()
        else:
            new_pref = UserPreference(
                category=category,
                value=value,
                weight=weight_increase,
                interaction_count=1
            )
            self.preferences.append(new_pref)
    
    def record_query(self, query: str) -> None:
        self.frequent_queries.append((query, 1))
        
        if len(self.frequent_queries) > MemoryConfig.MAX_SHORT_TERM_MEMORY:
            self.frequent_queries.pop(0)
    
    def get_routing_adjustment(self) -> Dict[str, float]:
        adjustments: Dict[str, float] = {}
        for domain in self.preferred_domains:
            adjustments[domain] = adjustments.get(domain, 0.0) + 0.3
        for domain, weight in self.domain_weights.items():
            adjustments[domain] = adjustments.get(domain, 0.0) + weight * 0.3
        for domain, expertise in self.domain_expertise.items():
            adjustments[domain] = adjustments.get(domain, 0.0) + expertise * 0.2
        return adjustments


# ============================================================================
# 指代消解模块
# ============================================================================

class CoreferenceResolver:
    """中文指代消解器"""
    
    PRONOUN_PATTERNS = {
        r'它|它们': 'THING',           
        r'他|她|他们|她们': 'PERSON',    
        r'这(个|种|些)|那(个|种|些)': 'DEMONSTRATIVE',  
        r'这(里|边)|那(里|边)': 'LOCATION',
        r'刚才(?:那个|提到的|说的)': 'RECENT_MENTION',
        r'上面(?:提到|说)(?:的|那个)': 'PREVIOUS_MENTION',
        r'前者|后者': 'ORDINAL',
        r'该(?:产品|技术|方案|方法)': 'FORMAL_REFERENCE',
    }
    
    CONTEXTUAL_CLUES = [
        (r'(?:价格|费用|成本|多少钱)', 'PRICE'),
        (r'(?:版本|型号|代数|v?\d+\.?\d*)', 'VERSION'),
        (r'(?:大小|尺寸|重量|规格)', 'SPECIFICATION'),
        (r'(?:时间|日期|什么时候|何时)', 'TIME'),
        (r'(?:如何|怎么|怎样|方法)', 'METHOD'),
        (r'(?:优缺点|好坏|对比|评价)', 'EVALUATION'),
        (r'(?:下载|安装|购买|获取)', 'ACTION'),
    ]
    
    @classmethod
    def detect_pronouns(cls, text: str) -> List[Tuple[str, str, int]]:
        """
        检测文本中的代词
        
        Args:
            text: 输入文本
            
        Returns:
            [(代词原文, 代词类型, 位置)]
        """
        pronouns_found = []
        
        for pattern, pronoun_type in cls.PRONOUN_PATTERNS.items():
            for match in re.finditer(pattern, text):
                pronouns_found.append((match.group(), pronoun_type, match.start()))
        
        return pronouns_found
    
    @classmethod
    def resolve_reference(cls, pronoun: str, pronoun_type: str,
                         context: List[ConversationTurn]) -> Optional[Entity]:
        """
        根据上下文解析代词指代的实体
        
        Args:
            pronoun: 代词原文
            pronoun_type: 代词类型
            context: 对话上下文
            
        Returns:
            解析出的实体，无法解析返回None
        """
        if not context:
            return None
        
        candidate_entities = []
        
        for turn in reversed(context):
            for entity in turn.entities:
                if entity.is_fresh:
                    relevance_score = cls._calculate_relevance(pronoun_type, entity)
                    recency_score = cls._calculate_recency_score(turn, context)
                    frequency_score = min(1.0, entity.mentioned_count / 5)
                    
                    total_score = (
                        0.4 * relevance_score +
                        0.3 * recency_score +
                        0.3 * frequency_score
                    )
                    
                    candidate_entities.append((entity, total_score))
        
        if not candidate_entities:
            return None
        
        best_match = max(candidate_entities, key=lambda x: x[1])
        
        if best_match[1] >= MemoryConfig.COREF_RESOLUTION_CONFIDENCE:
            return best_match[0]
        
        return None
    
    @classmethod
    def _calculate_relevance(cls, pronoun_type: str, entity: Entity) -> float:
        """计算代词与实体的相关性"""
        type_mapping = {
            'THING': ['PRODUCT', 'TECHNOLOGY', 'CONCEPT', 'TOOL'],
            'PERSON': ['PERSON', 'ORGANIZATION'],
            'DEMONSTRATIVE': ['PRODUCT', 'TECHNOLOGY', 'CONCEPT'],
            'LOCATION': ['LOCATION', 'ORGANIZATION'],
        }
        
        compatible_types = type_mapping.get(pronoun_type, [])
        return 1.0 if entity.entity_type in compatible_types else 0.3
    
    @classmethod
    def _calculate_recency_score(cls, turn: ConversationTurn,
                                 context: List[ConversationTurn]) -> float:
        """计算时间新鲜度分数"""
        if not context:
            return 0.0
        
        latest_turn = max(context, key=lambda t: t.turn_id)
        age = latest_turn.turn_id - turn.turn_id
        
        return max(0.0, 1.0 - (age / MemoryConfig.MAX_CONTEXT_TURNS))
    
    @classmethod
    def substitute_pronouns(cls, text: str, context: List[ConversationTurn]) -> Tuple[str, List[Entity]]:
        """
        执行代词替换
        
        Args:
            text: 包含代词的文本
            context: 对话上下文
            
        Returns:
            (替换后的文本, 使用的实体列表)
        """
        resolved_entities = []
        modified_text = text
        
        pronouns = cls.detect_pronouns(text)
        
        for pronoun, pronoun_type, position in pronouns:
            entity = cls.resolve_reference(pronoun, pronoun_type, context)
            
            if entity:
                replacement = entity.text
                
                clue_patterns = [pattern for pattern, _ in cls.CONTEXTUAL_CLUES]
                has_contextual_clue = any(re.search(p, text) for p in clue_patterns)
                
                if has_contextual_clue and pronoun_type in ['DEMONSTRATIVE', 'RECENT_MENTION']:
                    modified_text = re.sub(re.escape(pronoun), replacement, modified_text, count=1)
                elif pronoun_type in ['THING', 'FORMAL_REFERENCE']:
                    modified_text = re.sub(re.escape(pronoun), replacement, modified_text, count=1)
                
                resolved_entities.append(entity)
                entity.mentioned_count += 1
                entity.last_mentioned = datetime.now()
                
                logger.info(f"🔗 指代消解: '{pronoun}' → '{entity.text}' (置信度={entity.confidence:.2f})")
        
        return modified_text, resolved_entities


# ============================================================================
# 意图识别器
# ============================================================================

class IntentRecognizer:
    """查询意图识别器"""
    
    INTENT_PATTERNS = {
        IntentType.INFORMATION_SEEKING: [
            r'什么是|怎么是|什么是叫|介绍(?:一下)?|了解(?:一下)?|告诉我',
            r'[^?？]*[?？]$',
            r'(?:如何|怎样|怎么)(?:做|办|弄|搞|实现)',
        ],
        IntentType.NAVIGATION: [
            r'(?:打开|访问|进入|去|到)\s*(?:网站|网页|页面|链接)',
            r'https?://\S+',
            r'(?:搜|查|找)(?:一下)?(?:网址|官网|链接)',
        ],
        IntentType.TRANSACTIONAL: [
            r'(?:购买|买|下单|预订|订购|预约)',
            r'(?:下载|安装|注册|报名|申请)',
            r'(?:多少钱|价格|费用|收费)',
        ],
        IntentType.COMPARISON: [
            r'(?:对比|比较|哪个好|区别|差异|vs|或者|还是)',
            r'(?:A和B|前者.*后者)',
        ],
        IntentType.HOW_TO: [
            r'(?:教程|指南|步骤|方法|技巧|攻略)',
            r'(?:如何实现|怎么写|代码示例)',
            r'(?:解决|修复|处理|排查).*?(?:问题|错误|bug)',
        ],
        IntentType.DEFINITION: [
            r'(?:定义|概念|含义|意思|是指)',
            r'^\S+(?:是什么|的定义)',
        ],
        IntentType.NEWS_CHECKING: [
            r'(?:新闻|热点|最新|今天|昨天|突发|实时)',
            r'(?:发生了什么|有什么消息|动态)',
        ],
        IntentType.LOCAL_SEARCH: [
            r'(?:附近|周边|本地|哪里有)',
            r'(?:地址|位置|路线|怎么去)',
        ],
    }
    
    DOMAIN_KEYWORDS = {
        'tech': ['编程', '代码', 'API', '框架', '语言', '开发', '算法', 'AI', '机器学习'],
        'finance': ['股票', '基金', '投资', '理财', '财经', 'A股', '港股', '美股'],
        'academic': ['论文', '研究', '学术', '文献', '期刊', '博士', '硕士'],
        'life': ['天气', '餐厅', '酒店', '机票', '电影', '美食', '旅游'],
        'shopping': ['购买', '价格', '优惠', '推荐', '测评', '正品'],
        'medical': ['症状', '治疗', '药品', '医院', '医生', '健康'],
    }
    
    @classmethod
    def recognize_intent(cls, query: str, context: Optional[List[ConversationTurn]] = None) -> Tuple[IntentType, float]:
        """
        识别查询意图
        
        Args:
            query: 用户查询
            context: 可选的对话上下文
            
        Returns:
            (意图类型, 置信度)
        """
        query_lower = query.lower().strip()
        
        best_intent = IntentType.UNKNOWN
        best_confidence = 0.0
        
        for intent_type, patterns in cls.INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    confidence = cls._calculate_pattern_confidence(pattern, query_lower)
                    
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_intent = intent_type
                    
                    break 
        
        if context and len(context) >= 2:
            prev_intents = [turn.intent for turn in context[-3:] if turn.intent]
            if prev_intents:
                most_common_intent = max(set(prev_intents), key=prev_intents.count)
                
                if best_intent == IntentType.UNKNOWN or best_confidence < 0.6:
                    continuity_bonus = prev_intents.count(most_common_intent) / len(prev_intents)
                    
                    if continuity_bonus >= 0.6:
                        best_intent = most_common_intent
                        best_confidence = max(best_confidence, continuity_bonus)
        
        logger.info(f"🎯 意图识别: '{query[:30]}...' → {best_intent.value} (置信度={best_confidence:.2f})")
        
        return best_intent, best_confidence
    
    @classmethod
    def extract_domain(cls, query: str) -> Tuple[str, float]:
        """
        提取查询领域
        
        Returns:
            (领域名称, 置信度)
        """
        query_lower = query.lower()
        
        domain_scores = {}
        for domain, keywords in cls.DOMAIN_KEYWORDS.items():
            matches = sum(1 for kw in keywords if kw in query_lower)
            if keywords:
                domain_scores[domain] = matches / len(keywords)
        
        if not domain_scores:
            return 'general', 0.3
        
        best_domain = max(domain_scores, key=domain_scores.get)
        return best_domain, domain_scores[best_domain]
    
    @classmethod
    def _calculate_pattern_confidence(cls, pattern: str, query: str) -> float:
        """计算模式匹配置信度"""
        match = re.search(pattern, query)
        if not match:
            return 0.0
        
        match_length = len(match.group())
        query_length = len(query)
        
        base_confidence = 0.7
        
        if match_length <= 5:
            base_confidence += 0.1
        elif match_length <= 10:
            base_confidence += 0.15
        else:
            base_confidence += 0.2
        
        position_factor = match.start() / max(query_length, 1)
        if position_factor < 0.3:
            base_confidence += 0.05
        
        return min(1.0, base_confidence)


# ============================================================================
# 查询扩展与优化
# ============================================================================

class QueryExpander:
    """查询扩展器"""
    
    SYNONYM_DICT = {
        '电脑': ['计算机', 'PC', '笔记本', '台式机'],
        '手机': ['移动电话', '智能手机', 'iPhone', 'Android'],
        '价格': ['费用', '多少钱', '售价', '报价', '成本'],
        '教程': ['指南', '入门', '方法', '技巧', '攻略', 'how to'],
        '优化': ['提升', '改进', '加速', '性能调优', '性能优化'],
        '问题': ['bug', '错误', '故障', '异常', '报错'],
        '下载': ['获取', '安装包', 'installer', 'download'],
        '比较': ['对比', '区别', '差异', 'vs', '哪个好'],
    }
    
    CONTEXTUAL_EXPANSIONS = {
        ('HOW_TO', 'tech'): ['代码示例', '实现步骤', '最佳实践', '注意事项'],
        ('INFORMATION_SEEKING', 'finance'): ['最新数据', '市场分析', '行业报告'],
        ('COMPARISON', 'shopping'): ['性价比', '用户评价', '优缺点分析'],
        ('NEWS_CHECKING', 'general'): ['最新进展', '官方回应', '影响分析'],
    }
    
    @classmethod
    def expand_query(cls, query: str, intent: IntentType,
                    domain: str, context: Optional[List[ConversationTurn]] = None) -> List[str]:
        """
        扩展查询（生成多个变体）
        
        Args:
            query: 原始查询
            intent: 识别的意图
            domain: 识别的领域
            context: 对话上下文
            
        Returns:
            扩展后的查询列表（包含原始查询）
        """
        expansions = [query]
        
        for word, synonyms in cls.SYNONYM_DICT.items():
            if word in query:
                for synonym in synonyms[:2]:  
                    expanded = query.replace(word, synonym, 1)
                    if expanded != query and expanded not in expansions:
                        expansions.append(expanded)
        
        expansion_key = (intent, domain)
        if expansion_key in cls.CONTEXTUAL_EXPANSIONS:
            contextual_terms = cls.CONTEXTUAL_EXPANSIONS[expansion_key]
            
            for term in contextual_terms[:2]:
                expanded = f"{query} {term}"
                if expanded not in expansions:
                    expansions.append(expanded)
        
        if context:
            recent_entities = []
            for turn in reversed(context[-3:]):
                for entity in turn.entities:
                    if entity.is_fresh and entity not in recent_entities:
                        recent_entities.append(entity)
            
            for entity in recent_entities[:2]:
                expanded = f"{query} {entity.text}"
                if expanded not in expansions:
                    expansions.append(expanded)
        
        limited_expansions = expansions[:MemoryConfig.QUERY_EXPANSION_LIMIT + 1]
        
        logger.info(f"📝 查询扩展: '{query}' → {len(limited_expansions)} 个变体")
        
        return limited_expansions
    
    @classmethod
    def refine_query(cls, query: str) -> str:
        """
        查询精炼（清洗和规范化）
        
        Args:
            query: 原始查询
            
        Returns:
            精炼后的查询
        """
        refined = query.strip()
        
        refined = re.sub(r'\s+', ' ', refined)
        
        filler_words = ['嗯', '啊', '呃', '那个', '这个', '就是', '的话']
        for filler in filler_words:
            refined = re.sub(rf'\s*{filler}\s*', ' ', refined)
        
        question_markers = ['吗', '呢', '吧', '啊']
        if refined and refined[-1] in question_markers:
            refined = refined[:-1].strip()
        
        if not re.search(r'[?？！。]$', refined) and not re.search(r'(?:怎么|如何|什么|哪|谁|为什么)', refined):
            pass
        
        return refined.strip()


# ============================================================================
# 核心上下文记忆管理器
# ============================================================================

class ContextMemory:
    """
    上下文记忆管理器 - 核心类
    
    使用示例:
        memory = ContextMemory()
        
        # 处理第一轮
        processed_q1 = memory.process_query("React性能优化")
        # => "React 性能优化"
        
        # 记录第一轮结果
        memory.add_turn("assistant", "这是关于React性能优化的搜索结果...", 
                       entities=[Entity("React", "TECHNOLOGY", 0.95)])
        
        # 处理第二轮（自动理解指代）
        processed_q2 = memory.process_query("它的最新版本")
        # => "React 最新版本" （自动将"它"替换为"React"）
    """
    
    def __init__(self, user_id: str = "default",
                 max_context_turns: int = MemoryConfig.MAX_CONTEXT_TURNS):
        """
        初始化上下文记忆
        
        Args:
            user_id: 用户标识
            max_context_turns: 最大保留轮次
        """
        self.user_id = user_id
        self.max_context_turns = max_context_turns
        self.conversation_history: List[ConversationTurn] = []
        self.user_profile = UserProfile(user_id=user_id)
        self.turn_counter = 0
        self.coref_resolver = CoreferenceResolver()
        self.intent_recognizer = IntentRecognizer()
        self.query_expander = QueryExpander()
    
    def process_query(self, raw_query: str) -> str:
        """
        处理用户查询（核心方法）
        
        执行完整流程：精炼 → 指代消解 → 实体提取 → 意图识别 → 查询扩展
        
        Args:
            raw_query: 原始用户输入
            
        Returns:
            处理后的优化查询
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"📥 处理查询: '{raw_query}'")
        
        refined_query = self.query_expander.refine_query(raw_query)
        
        resolved_query, resolved_entities = self.coref_resolver.substitute_pronouns(
            refined_query, self.conversation_history
        )
        
        intent, intent_confidence = self.intent_recognizer.recognize_intent(
            resolved_query, self.conversation_history
        )
        
        domain, domain_confidence = self.intent_recognizer.extract_domain(resolved_query)
        
        current_turn = ConversationTurn(
            turn_id=self.turn_counter,
            role="user",
            content=raw_query,
            processed_content=resolved_query,
            intent=intent,
            entities=resolved_entities
        )
        
        extracted_entities = self._extract_entities_from_query(resolved_query, intent, domain)
        current_turn.entities.extend(extracted_entities)
        
        self.conversation_history.append(current_turn)
        self.turn_counter += 1
        
        if len(self.conversation_history) > self.max_context_turns:
            removed = self.conversation_history.pop(0)
            logger.debug(f"移除过期轮次: Turn {removed.turn_id}")
        
        self.user_profile.record_query(resolved_query)
        
        if domain != 'general':
            self.user_profile.update_preference('domain', domain, 0.1)
        
        if intent != IntentType.UNKNOWN:
            self.user_profile.update_preference('intent', intent.value, 0.05)
        
        final_query = resolved_query
        
        logger.info(f"✅ 查询处理完成:")
        logger.info(f"   原始: '{raw_query}'")
        logger.info(f"   处理后: '{final_query}'")
        logger.info(f"   意图: {intent.value} (置信度={intent_confidence:.2f})")
        logger.info(f"   领域: {domain} (置信度={domain_confidence:.2f})")
        logger.info(f"   实体: {[e.text for e in current_turn.entities]}")
        logger.info(f"{'='*60}\n")
        
        return final_query
    
    def add_turn(self, role: str, content: str,
                processed_content: Optional[str] = None,
                intent: Optional[IntentType] = None,
                entities: Optional[List[Entity]] = None,
                search_results_summary: Optional[Dict[str, Any]] = None,
                feedback: Optional[str] = None) -> ConversationTurn:
        """
        手动添加一轮对话（通常用于助手回复）
        
        Args:
            role: 角色 (user/assistant/system)
            content: 原始内容
            processed_content: 处理后的内容
            intent: 意图
            entities: 实体列表
            search_results_summary: 搜索结果摘要
            feedback: 用户反馈
            
        Returns:
            创建的对话轮次对象
        """
        turn = ConversationTurn(
            turn_id=self.turn_counter,
            role=role,
            content=content,
            processed_content=processed_content or content,
            intent=intent,
            entities=entities or [],
            search_results_summary=search_results_summary,
            feedback=feedback
        )
        
        self.conversation_history.append(turn)
        self.turn_counter += 1
        
        if len(self.conversation_history) > self.max_context_turns:
            self.conversation_history.pop(0)
        
        return turn
    
    def get_context_window(self, last_n: int = 5) -> List[ConversationTurn]:
        """
        获取最近N轮对话上下文
        
        Args:
            last_n: 获取的轮次数
            
        Returns:
            最近N轮对话列表
        """
        return self.conversation_history[-last_n:]
    
    def get_active_entities(self) -> List[Entity]:
        """
        获取当前活跃实体（未过期的）
        
        Returns:
            活跃实体列表
        """
        all_entities = []
        seen_texts = set()
        
        for turn in reversed(self.conversation_history):
            for entity in turn.entities:
                if entity.is_fresh and entity.text not in seen_texts:
                    all_entities.append(entity)
                    seen_texts.add(entity.text)
        
        return all_entities
    
    def get_suggested_expansions(self, current_query: str) -> List[str]:
        """
        获取基于上下文的查询扩展建议
        
        Args:
            current_query: 当前查询
            
        Returns:
            建议的扩展查询列表
        """
        last_turn = self.conversation_history[-1] if self.conversation_history else None
        
        if not last_turn or not last_turn.intent:
            return []
        
        intent = last_turn.intent
        domain, _ = self.intent_recognizer.extract_domain(current_query)
        
        expansions = self.query_expander.expand_query(
            current_query, intent, domain, self.conversation_history
        )
        
        return expansions[1:] if len(expansions) > 1 else []
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """
        获取对话摘要统计
        
        Returns:
            对话摘要字典
        """
        intents = [turn.intent for turn in self.conversation_history if turn.intent]
        domains = []
        
        for turn in self.conversation_history:
            _, domain = self.intent_recognizer.extract_domain(turn.content)
            domains.append(domain)
        
        return {
            'total_turns': len(self.conversation_history),
            'user_turns': sum(1 for t in self.conversation_history if t.role == 'user'),
            'assistant_turns': sum(1 for t in self.conversation_history if t.role == 'assistant'),
            'active_entities': len(self.get_active_entities()),
            'intent_distribution': {
                intent.value: intents.count(intent) 
                for intent in set(intents)
            } if intents else {},
            'domain_distribution': {
                domain: domains.count(domain) 
                for domain in set(domains)
            } if domains else {},
            'user_profile': {
                'top_preferences': sorted(
                    self.user_profile.preferences, 
                    key=lambda p: p.weight, 
                    reverse=True
                )[:5],
                'domain_expertise': dict(self.user_profile.domain_expertise)
            }
        }
    
    def clear_context(self) -> None:
        """清空对话上下文（开始新对话）"""
        self.conversation_history.clear()
        self.turn_counter = 0
        logger.info("🗑️ 对话上下文已清空")
    
    def export_state(self) -> Dict[str, Any]:
        """
        导出当前状态（用于持久化或调试）
        
        Returns:
            状态字典
        """
        return {
            'user_id': self.user_id,
            'turn_counter': self.turn_counter,
            'conversation_length': len(self.conversation_history),
            'summary': self.get_conversation_summary(),
            'recent_turns': [
                {
                    'turn_id': t.turn_id,
                    'role': t.role,
                    'content_preview': t.content[:50],
                    'intent': t.intent.value if t.intent else None,
                    'entities': [e.text for e in t.entities],
                    'timestamp': t.timestamp.isoformat()
                }
                for t in self.conversation_history[-5:]
            ]
        }
    
    def _extract_entities_from_query(self, query: str, intent: IntentType,
                                    domain: str) -> List[Entity]:
        """从查询中提取实体"""
        entities = []
        
        tech_keywords = ['Python', 'Java', 'JavaScript', 'React', 'Vue', 'Angular',
                        'Docker', 'Kubernetes', 'AI', 'ML', 'LLM', 'GPT', 'TensorFlow']
        
        finance_keywords = ['A股', '美股', '港股', '比特币', '以太坊', '黄金', '原油',
                          '茅台', '腾讯', '阿里巴巴', '苹果公司', '特斯拉']
        
        domain_keyword_map = {
            'tech': tech_keywords,
            'finance': finance_keywords,
        }
        
        keywords_to_check = domain_keyword_map.get(domain, tech_keywords + finance_keywords)
        
        for keyword in keywords_to_check:
            if keyword.lower() in query.lower():
                entity_type = 'TECHNOLOGY' if domain == 'tech' else ('FINANCIAL' if domain == 'finance' else 'ENTITY')
                entities.append(Entity(
                    text=keyword,
                    entity_type=entity_type,
                    confidence=0.9,
                    source_turn=self.turn_counter
                ))
        
        number_pattern = r'(\d+(?:\.\d+)?)\s*(?:%|亿元|万元|元|美元|版)?'
        numbers = re.findall(number_pattern, query)
        for num in numbers:
            entities.append(Entity(
                text=num,
                entity_type='MEASURE',
                confidence=0.7,
                source_turn=self.turn_counter
            ))
        
        return entities[:5]


# ============================================================================
# 便捷接口函数
# ============================================================================

def create_memory(user_id: str = "default") -> ContextMemory:
    """创建新的上下文记忆实例"""
    return ContextMemory(user_id=user_id)


def process_user_query(raw_query: str, memory: ContextMemory) -> str:
    """
    处理用户查询的便捷函数
    
    Args:
        raw_query: 原始查询
        memory: 上下文记忆实例
        
    Returns:
        处理后的查询
    """
    return memory.process_query(raw_query)


if __name__ == "__main__":
    print("=" * 70)
    print("🧠 CN Web Search Context Memory v4.2 - 测试运行")
    print("=" * 70)
    
    memory = ContextMemory(user_id="test_user")
    
    test_conversations = [
        ("用户", "React性能优化怎么做？"),
        ("助手", "这里有一些关于React性能优化的资源..."),
        ("用户", "它的最新版本是多少？"),
        ("助手", "React 18是最新版本，发布于2022年..."),
        ("用户", "和Vue相比呢？"),
        ("助手", "React和Vue在以下方面有所不同..."),
        ("用户", "前者在大型项目中的表现如何？"),
    ]
    
    print("\n📝 模拟多轮对话:\n")
    
    for i, (role, content) in enumerate(test_conversations):
        print(f"[{i+1}] {role}: {content}")
        
        if role == "用户":
            processed = memory.process_query(content)
            print(f"    ✅ 处理后: '{processed}'")
            
            active = memory.get_active_entities()
            if active:
                print(f"    🔗 活跃实体: {[e.text for f in active]}")
        else:
            memory.add_turn(role, content)
        
        print()
    
    print("\n" + "=" * 70)
    print("📊 对话摘要:")
    summary = memory.get_conversation_summary()
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    
    print("\n" + "=" * 70)
    print("💾 状态导出:")
    state = memory.export_state()
    print(json.dumps(state, ensure_ascii=False, indent=2))
    
    print("\n" + "=" * 70)
    print("✅ Context Memory测试完成!")
    print("=" * 70)

# CN-Web-Search 更新日志归档

## v4.3.2 (2026-05-16) - 电商运营领域拓展 🆕

### 核心升级
- 🌐 **新增领域**: 天猫运营（tmall-ops）+ 京东运营（jd-ops）+ 1688批发（1688-ops）
- 🔧 **新增引擎**: 天猫商家中心/规则中心/营销中心 + 京东商家中心/规则中心/营销中心 + 1688批发市场/分销平台/阿里商学院（+9引擎）
- 🔀 **路由扩展**: 新增3电商领域关键词匹配
- 📈 **引擎总数**: 144 → 150（+6新增）
- 📈 **领域总数**: 18 → 21（+3新增）

### 新增文件
- `domains/tmall-ops.md` → 天猫电商运营领域
- `domains/jd-ops.md` → 京东电商运营领域
- `domains/1688-ops.md` → 1688批发平台运营领域

### 文件更新
- `SKILL.md` → v4.3.2（新增路由规则+领域引擎选择）
- `engines/index.md` → v4.3.2（新增电商运营平台引擎组）
- `_meta.json` → v4.3.2

---

## v4.3.1 (2026-05-16) - 领域拓展 + 执行优化 🆕

### 核心升级
- 🌐 **新增领域**: AI技术/开发者生态（ai-ecosystem）+ 小红书运营（xiaohongshu-ops）+ 抖音运营（douyin-ops）
- 🔧 **新增引擎**: GitHub + skills.sh + 腾讯SkillHub + 千瓜数据 + 巨量算数 + 飞瓜数据 + 达人通（+6引擎）
- 📊 **执行效率基准**: 静态性能指标表（5种查询类型时间基准≤15秒）
- 🎯 **检查点改进**: 新增Step1.5路由确认 + Step5.3结果缺口检查点
- 🔀 **路由扩展**: 新增3领域关键词匹配 + 运营类多意图拆分规则
- 📈 **引擎总数**: 138 → 144（+6新增）

### 新增文件
- `domains/ai-ecosystem.md` → AI技术/开发者生态领域
- `domains/xiaohongshu-ops.md` → 小红书运营领域
- `domains/douyin-ops.md` → 抖音运营领域

### 文件更新
- `SKILL.md` → v4.3.1（新增路由规则+执行效率基准+检查点设计）
- `engines/index.md` → v4.3.1（新增AI生态+运营数据工具引擎组）
- `_meta.json` → v4.3.1

### 关键词优先级扩展（v4.3.1）
```
新增优先级层级（介于tech和content之间）:
- ai_ecosystem（AI工具/技能平台/Claude Code/Cursor/MCP Server）
- xiaohongshu_ops（小红书运营/种草/笔记/账号运营）
- douyin_ops（抖音运营/短视频/直播/达人/带货）
```

### 执行效率基准（v4.3.1新增）
```
| 查询类型 | 目标时间 | 最大并行数 | 迭代轮数 |
|----------|----------|------------|----------|
| 简单事实 | ≤5秒     | 1          | 1轮      |
| 中等复杂 | ≤10秒    | 2          | 1-2轮    |
| 时效热点 | ≤8秒     | 2          | 1轮      |
| 复杂研究 | ≤15秒    | 3          | 2-3轮    |
| 运营查询 | ≤12秒    | 2          | 2轮      |
```

---

## v4.0.0 (2026-05-02) - 全能合并版 🆕

### 核心升级
- 🔀 **合并cn-search-hub v3.1.1**: 智能路由、迭代检索、Rerank评分、来源识别
- 🔀 **合并workbuddy v2.4.0**: 美股深度、全球宏观、Pre-IPO、散户情绪
- 🆕 **引擎总数**: 109 → 118（+9个海外专用引擎）
- 🆕 **智能路由决策树**: 关键词 → 12领域映射 + 优先级冲突解决
- 🆕 **美股深度搜索**: Seeking Alpha + Finviz + Macrotrends
- 🆕 **全球宏观数据**: BEA + Treasury + Census
- 🆕 **Pre-IPO搜索**: IPOScoop + StockAnalysis + CB Insights
- 🆕 **散户情绪/政治监测**: Reddit WSB + Nitter
- 🆕 **关键词优先级扩展**: 8级 → 12级（新增us_stock/macro/pre_ipo/sentiment）
- 🆕 **信源权重扩展**: 新增海外官方数据源权重
- 🆕 **采纳建议扩展**: 新增散户情绪专用评级

### 文件更新
- `SKILL.md` → v4.0.0（全能合并版主入口）
- `core/router.md` → v4.0.0（12领域路由+4新领域）
- `domains/finance.md` → v4.0.0（含美股/宏观/Pre-IPO/情绪）
- `engines/index.md` → v4.0.0（118引擎+9新引擎）
- `_meta.json` → v4.0.0
- `package.json` → v4.0.0

### 关键词优先级规则（v4.0.0扩展）
```
1. academic（论文/学术/研究）
2. finance（股票/基金/A股）
3. us_stock（Seeking Alpha/Finviz/Macrotrends/TICKER）
4. macro（GDP/国债/收益率/BEA/Treasury）
5. pre_ipo（IPO/独角兽/Pre-IPO/CB Insights）
6. sentiment（WSB/Reddit/散户/Nitter）
7. tech（AI/编程/React/Python）
8. news（新闻/热点/最新/今天）
9. knowledge（是什么/定义/百科）
10. life（附近/餐厅/天气/酒店）
11. content（视频/B站/抖音/知乎）
12. general（默认）
```

---

## v3.1.1 (2026-04-04) - 权威性识别增强版

### 核心优化
- 🆕 **来源类型识别**: 🏢官方/📰权威媒体/👥技术社区/📝个人博客
- 🆕 **时效性标签**: ✅最新/⚠️可能过时/❌已过时
- 🆕 **采纳建议增强**: 基于来源类型提供验证建议
- 🆕 **关键词优先级规则**: 解决路由冲突

### 建议书吸收
- 基于实际使用中的错误判断教训优化
- 避免LLM忽视官方来源证据
- 增强权威性识别和验证提示

### 文件更新
- `core/workflow.md` → v3.1.1（来源类型识别、时效性标签、采纳建议增强）
- `core/router.md` → v3.1.1（关键词优先级规则）
- `domains/tech.md` → v3.1.1（增加来源类型标识）
- `domains/academic.md` → v3.1.1（增加来源类型标识）
- `domains/finance.md` → v3.1.1（增加来源类型标识）
- `domains/news.md` → v3.1.1（增加来源类型标识）
- `SKILL_v3.1.1.md` - 新版本主入口

### 关键词优先级规则
```
1. academic（论文/学术/研究）
2. finance（股票/基金/A股）
3. tech（AI/编程/React/Python）
4. news（新闻/热点/最新/今天）
5. knowledge（是什么/定义/百科）
6. life（附近/餐厅/天气/酒店）
7. content（视频/B站/抖音/知乎）
8. general（默认）
```

---

## v3.1.0 (2026-04-04) - LLM友好性优化版

### 核心优化
- 🔧 **Token压缩59%**: 从10850降至4400
- 🔧 **检索提速187%**: 从1150ms降至400ms
- 🔧 **结构扁平化**: 3层目录→2层
- 🔧 **路由精简**: 20类关键词→8领域映射
- 📊 **文件减少**: 28个→18个（-36%）

### 目录重构
- 新增 `core/` 目录：router.md, workflow.md, fallback.md
- 新增 `domains/` 目录：6个精简领域文件
- 新增 `engines/` 目录：index.md, operators.md
- 新增 `archive/` 目录：归档历史文档
- 保留 `scripts/` 目录：v3.0 Python脚本集

### SKILL.md精简
- 行数：350行→120行（-65%）
- Token：2850→1200（-58%）
- 结构：五层渐进→三层快速路由

---

## v3.0.0 (2026-04-02) - 异步并发版

### 核心升级
- 🆕 异步并发架构，响应速度提升60-73%
- 🆕 多维语义Rerank引擎
- 🆕 上下文记忆系统（10轮对话）
- 🆕 浏览器实例池（95%延迟降低）
- 🆕 中文查询改写引擎

### 新增脚本
- `web_search_v3.py` - 异步并发搜索引擎
- `rerank_engine.py` - 多维智能重排引擎
- `context_memory.py` - 多轮对话上下文记忆
- `performance_optimizer.py` - 高性能执行优化器
- `query_rewriter.py` - 中文智能查询改写
- `test_suite.py` - 综合验证测试套件

---

## v2.7.0 (2026-03-xx) - 渐进式引导版

### 核心升级
- 🔧 五层渐进式引导结构
- 🆕 109个搜索引擎聚合
- 🆕 21类查询路由表
- 🆕 网络可用性标注
- 📊 P0核心站点标注（59个）

### 子技能文件
- `tech-search.md` - 技术社区搜索
- `academic-search.md` - 学术论文搜索
- `finance-search.md` - 财经投资搜索
- `news-search.md` - 新闻媒体搜索
- `knowledge-search.md` - 知识百科搜索
- `life-search.md` - 生活购物搜索
- `content-search.md` - 内容平台搜索
- `iterative-search.md` - 迭代检索流程
- `rerank.md` - 结果重排评分
- `parallel-execution.md` - 并行执行策略

---

## v2.5.0 (2026-02-xx) - 合并增强版

### 核心升级
- 🆕 新增备用执行器：集成web-search-ex-skill的Python脚本执行器
- 🆕 `scripts/web_search.py`：当firecrawl/agent-browser不可用时作为fallback
- 🔧 工具选择决策树：增加脚本执行器说明

---

## v2.4.1 (2026-01-xx)

### 核心升级
- 🆕 触发机制：新增自动触发条件，优先于内置WebSearch/WebFetch

---

## v2.3.0 (2025-12-xx)

### 核心升级
- 🆕 迭代检索：新增"检索-推理-再检索"迭代循环机制
- 🆕 Rerank评分：多维度评分体系
  - 相关性 35%
  - 权威性 25%
  - 时效性 20%
  - 完整性 15%
  - 新颖性 5%

---

## v0.9.0 (初始版本)

### 核心功能
- 13+ 免费搜索引擎聚合
- 无需API Key
- 公众号文章搜索支持
- 中文/英文/技术/专用引擎分类
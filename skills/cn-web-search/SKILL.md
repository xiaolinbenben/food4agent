---
name: cn-web-search
version: 4.3.2
description: 中文网页搜索 - 渐进式智能路由检索系统 聚合150+搜索引擎，渐进式路由决策，按查询类型自动选择最优引擎 支持"检索-推理-再检索"迭代循环 + 结果Rerank + 交叉验证 + 采纳建议评分 无需API Key，支持中国网络环境 🆕 v4.3.2 新增天猫/京东/1688电商运营领域
author: joansongjr
author_url: https://github.com/joansongjr
repository: https://github.com/joansongjr/cn-web-search
license: MIT
tags:
  - search
  - chinese
  - web-search
  - 多引擎
  - 聚合搜索
  - 免费无需API
  - 中文搜索
  - 迭代检索
  - Rerank
  - 智能路由
  - 交叉验证
  - 渐进式引导
  - 语义Embedding
  - 动态并行
trigger:
  keywords: [搜索, 查找, 查询, 查一下, 搜一下, 找一下, 看看, 检索, 了解一下, 搜, 查, 找]
  priority: 中文内容优先，优于WebSearch/WebFetch
---

# 中文网页搜索 v4.3.0

> **核心原则**: 渐进式引导 — 首Token定路由，按需加载详情，逐步深化检索
> **v4.3.0 新特性**: 语义理解突破 + 动态并行优化 + 查询类型自适应权重 + 免责声明强化

---

## ⚡ Step 1: 首Token路由（必须最先执行）

> **规则**: 读取用户查询后，立即匹配下表确定领域，再加载对应详情

```
IF 查询含[论文/学术/研究/博士/硕士/文献/专利]        → academic  → GOTO Step2-academic
IF 查询含[股票/基金/A股/港股/财报/黄金/理财]          → finance   → GOTO Step2-finance
IF 查询含[TICKER/Seeking/Finviz/Macrotrends]          → us_stock  → GOTO Step2-us_stock
IF 查询含[GDP/国债/收益率/BEA/Treasury]               → macro     → GOTO Step2-macro
IF 查询含[IPO/独角兽/Pre-IPO/CB Insights]             → pre_ipo   → GOTO Step2-pre_ipo
IF 查询含[WSB/Reddit/散户/Nitter/情绪]                 → sentiment → GOTO Step2-sentiment
IF 查询含[AI/编程/React/Python/Java/Go/代码/bug/框架]  → tech      → GOTO Step2-tech
IF 查询含[AI工具/技能平台/Agent Skills/Claude Code/Cursor/MCP Server] → ai_ecosystem → GOTO Step2-ai_ecosystem
IF 查询含[小红书运营/种草/笔记/账号运营/涨粉]          → xiaohongshu_ops → GOTO Step2-xiaohongshu_ops
IF 查询含[抖音运营/短视频/直播/达人/带货]               → douyin_ops → GOTO Step2-douyin_ops
IF 查询含[天猫运营/天猫店铺/天猫规则/天猫入驻]          → tmall_ops → GOTO Step2-tmall_ops
IF 查询含[京东运营/京东店铺/京东规则/京东入驻]          → jd_ops    → GOTO Step2-jd_ops
IF 查询含[1688运营/1688店铺/批发/B2B/一件代发]         → 1688_ops  → GOTO Step2-1688_ops
IF 查询含[新闻/热点/最新/今天/实时/突发]               → news      → GOTO Step2-news
IF 查询含[是什么/定义/百科/介绍/意思]                  → knowledge → GOTO Step2-knowledge
IF 查询含[附近/餐厅/天气/酒店/外卖/购物/机票]          → life      → GOTO Step2-life
IF 查询含[考研/考试/真题/课程/教材/大学]               → education → GOTO Step2-education
IF 查询含[症状/治疗/药品/医院/健康/医学]               → medical   → GOTO Step2-medical
IF 查询含[法律/法规/判决/合同/律师]                    → legal     → GOTO Step2-legal
IF 查询含[视频/B站/抖音/知乎/微博/公众号/小红书]       → content   → GOTO Step2-content
ELSE                                                  → general   → GOTO Step2-general
```

### 多意图拆分规则

```
IF 查询含多个领域关键词（如"英伟达财报和最新新闻"）:
  → 拆分为多个子查询
  → 按领域分别路由
  → 结果合并输出
```

### 否定意图处理

```
IF 查询含[不想/除了/不要/排除/去掉]-X:
  → 记录排除项X
  → 搜索结果中过滤包含X的来源
  → 示例: "除了CSDN以外的React教程" → 排除csdn.net域名
```

### 地域敏感查询识别

```
IF 查询含[附近/周边/本地/同城] OR 查询含地域敏感词[房价/招聘/外卖/天气/餐厅]:
  → 检查是否含城市名
  → IF 无城市名 → 提示用户指定城市，或使用默认城市配置
  → IF 有城市名 → 在URL模板中注入城市参数
```

---

## 📖 Step 2: 领域引擎选择（按Step1结果加载对应段落）

### Step2-tech → domains/tech.md

| 子类型 | P0引擎 | P1引擎 | URL模板 |
|--------|--------|--------|---------|
| AI技术 | CSDN + ArXiv | 掘金 + GitHub | `so.csdn.net/so/search/s.do?q=QUERY` |
| 前后端 | StackOverflow + CSDN | 掘金 + GitHub | `stackoverflow.com/search?q=QUERY` |
| 移动端 | CSDN + 掘金 | StackOverflow | `juejin.cn/search?query=QUERY` |

### Step2-ai_ecosystem → domains/ai-ecosystem.md 🆕

| 子类型 | P0引擎 | P1引擎 | URL模板 |
|--------|--------|--------|---------|
| AI代码工具 | GitHub + 腾讯SkillHub | CSDN + 掘金 | `github.com/search?q=QUERY&type=code` |
| 技能平台 | skills.sh + 腾讯SkillHub | GitHub | `skillhub.tencent.com/search?keyword=QUERY` |
| MCP Server | GitHub + ArXiv | CSDN | `github.com/search?q=QUERY&type=repositories` |

### Step2-xiaohongshu_ops → domains/xiaohongshu-ops.md 🆕

| 子类型 | P0引擎 | P1引擎 | URL模板 |
|--------|--------|--------|---------|
| 账号运营 | 小红书 + 千瓜数据 | 新红数据 | `xiaohongshu.com/search_result?keyword=QUERY` |
| 内容创作 | 小红书 + 千瓜数据 | 蝉妈妈 | `qiangua.com/search?keyword=QUERY` |
| 投放策略 | 千瓜数据 + 新红数据 | 小红书 | `newrank.cn/search?keyword=QUERY` |

### Step2-douyin_ops → domains/douyin-ops.md 🆕

| 子类型 | P0引擎 | P1引擎 | URL模板 |
|--------|--------|--------|---------|
| 账号运营 | 抖音 + 巨量算数 | 飞瓜数据 | `douyin.com/search/QUERY` |
| 直播带货 | 巨量算数 + 飞瓜数据 | 达人通 | `trendinsight.oceanengine.com/search?keyword=QUERY` |
| 投流策略 | 巨量算数 + 飞瓜数据 | 抖音 | `feigua.cn/search?keyword=QUERY` |

### Step2-tmall_ops → domains/tmall-ops.md 🆕v4.3.2

| 子类型 | P0引擎 | P1引擎 | URL模板 |
|--------|--------|--------|---------|
| 店铺运营 | 天猫商家中心 + 淘宝大学 | 千牛头条 | `daxue.taobao.com/search?keyword=QUERY` |
| 规则政策 | 天猫规则中心 + 淘宝大学 | 千牛头条 | `rule.tmall.com` |
| 营销活动 | 天猫营销中心 + 淘宝大学 | 千牛头条 | `marketing.tmall.com` |

### Step2-jd_ops → domains/jd-ops.md 🆕v4.3.2

| 子类型 | P0引擎 | P1引擎 | URL模板 |
|--------|--------|--------|---------|
| 店铺运营 | 京东商家中心 + 京商学院 | 京麦头条 | `xue.jd.com/search?keyword=QUERY` |
| 规则政策 | 京东规则中心 + 京商学院 | 京麦头条 | `rule.jd.com` |
| 营销活动 | 京东营销中心 + 京商学院 | 京麦头条 | `marketing.jd.com` |

### Step2-1688_ops → domains/1688-ops.md 🆕v4.3.2

| 子类型 | P0引擎 | P1引擎 | URL模板 |
|--------|--------|--------|---------|
| 店铺运营 | 1688商家中心 + 阿里商学院 | 商家资讯 | `xue.1688.com/search?keyword=QUERY` |
| 批发货源 | 1688批发市场 + 阿里商学院 | 商家资讯 | `1688.com` |
| 一件代发 | 1688分销平台 + 阿里商学院 | 商家资讯 | `fenxiao.1688.com` |

### Step2-academic → domains/academic.md

| 子类型 | P0引擎 | P1引擎 | URL模板 |
|--------|--------|--------|---------|
| 中文论文 | 知网 + 万方 | 维普 + 百度学术 | `cnki.net/search?q=QUERY` |
| 英文论文 | ArXiv + Google Scholar | Semantic Scholar | `arxiv.org/api/query?search_query=all:QUERY` |
| 专利 | 国家知识产权局 | Google Patents | `pss-system.cponline.cnipa.gov.cn` |

### Step2-finance → domains/finance.md

| 子类型 | P0引擎 | P1引擎 | URL模板 |
|--------|--------|--------|---------|
| A股 | 东方财富 + 雪球 | 同花顺 + 集思录 | `so.eastmoney.com/news/s?keyword=QUERY` |
| 基金 | 天天基金 + 蛋卷 | 且慢 | `fund.eastmoney.com` |
| 黄金 | 金十数据 + 上金所 | 东方财富 | `jin10.com/search?keyword=QUERY` |

### Step2-us_stock

| 子类型 | P0引擎 | URL模板 |
|--------|--------|---------|
| 基本面 | Seeking Alpha | `seekingalpha.com/symbol/TICKER` |
| 数据筛选 | Finviz | `finviz.com/quote.ashx?t=TICKER` |
| 历史财务 | Macrotrends | `macrotrends.net/stocks/charts/TICKER/NAME/revenue` |

### Step2-macro

| 子类型 | P0引擎 | URL模板 |
|--------|--------|---------|
| 经济数据 | BEA | `bea.gov/news/current-releases` |
| 国债利率 | Treasury | `home.treasury.gov/` |
| 经济指标 | Census | `census.gov/economic-indicators/` |

### Step2-pre_ipo

| 子类型 | P0引擎 | URL模板 |
|--------|--------|---------|
| IPO日历 | IPOScoop | `iposcoop.com/ipo-calendar/` |
| IPO数据 | StockAnalysis | `stockanalysis.com/ipos/` |
| 独角兽 | CB Insights | `cbinsights.com/research-unicorn-companies` |

### Step2-sentiment

| 子类型 | P0引擎 | URL模板 |
|--------|--------|---------|
| WSB情绪 | Reddit WSB | `reddit.com/r/wallstreetbets/top/.rss` |
| 政策风向 | Nitter | `nitter.net/USERNAME/rss` |

### Step2-news → domains/news.md

| 子类型 | P0引擎 | P1引擎 | URL模板 |
|--------|--------|--------|---------|
| 热点 | 百度资讯 + 头条 | 微博 | `baidu.com/s?wd=QUERY&rtt=1` |
| 财经 | 东方财富 + 财新 | 华尔街见闻 | `eastmoney.com` |
| 政务 | 中国政府网 + 人民日报 | 央视新闻 | `gov.cn/search` |

**时效筛选**: 新闻查询自动附加时间参数 → `&rtt=1&bsst=1`（百度）/ `&tf=pw`（Brave本周）

### Step2-knowledge → domains/knowledge.md

| 子类型 | P0引擎 | P1引擎 | URL模板 |
|--------|--------|--------|---------|
| 百科 | 百度百科 + Wikipedia | 知乎百科 | `baike.baidu.com/item/QUERY` |
| 计算 | WolframAlpha | DDG Instant | `wolframalpha.com/input?i=QUERY` |

### Step2-life → domains/life.md

| 子类型 | P0引擎 | P1引擎 | URL模板 |
|--------|--------|--------|---------|
| 本地 | 高德 + 大众点评 | 美团 | `amap.com/search?query=QUERY&city=CITY` |
| 购物 | 淘宝 + 京东 | 什么值得买 | `s.taobao.com/search?q=QUERY` |
| 出行 | 12306 + 携程 | 去哪儿 | `12306.cn` |
| 天气 | 和风天气 | 百度天气 | `qweather.com/search?city=CITY` |

### Step2-education → domains/education.md

| 子类型 | P0引擎 | P1引擎 | URL模板 |
|--------|--------|--------|---------|
| 考研 | 考研帮 + 中国知网 | 学堂在线 | `kaoyan.com/search?keyword=QUERY` |
| 公考 | 粉笔公考 | 华图教育 | `fenbi.com/search?keyword=QUERY` |
| 课程 | 中国大学MOOC | 学堂在线 | `icourse163.org/search?keyword=QUERY` |
| 论文 | 知网 + 万方 | 百度学术 | `cnki.net/search?q=QUERY` |

### Step2-medical → domains/medical.md

| 子类型 | P0引擎 | P1引擎 | URL模板 |
|--------|--------|--------|---------|
| 症状 | 丁香园 + 好大夫 | 春雨医生 | `search.dxy.com/?keyword=QUERY` |
| 用药 | 用药助手 | 丁香医生 | `drugs.dxy.cn/search?keyword=QUERY` |
| 学术 | PubMed | 医脉通 | `pubmed.ncbi.nlm.nih.gov/?term=QUERY` |

### Step2-legal → domains/legal.md

| 子类型 | P0引擎 | P1引擎 | URL模板 |
|--------|--------|--------|---------|
| 判例 | 中国裁判文书网 | 无讼 | `wenshu.court.gov.cn` |
| 法规 | 国家法律法规库 | 北大法宝 | `flk.npc.gov.cn/` |
| 合同 | 法信 | 找法网 | `faxin.cn/search?keyword=QUERY` |

### Step2-content → domains/content.md

| 子类型 | P0引擎 | P1引擎 | URL模板 |
|--------|--------|--------|---------|
| 公众号 | 搜狗微信 | 必应公众号 | `weixin.sogou.com/weixin?type=2&query=QUERY` |
| 视频 | B站 + 抖音 | 西瓜视频 | `search.bilibili.com/all?keyword=QUERY` |
| 社交 | 知乎 + 微博 | 小红书 | `zhihu.com/search?q=QUERY` |

### Step2-general

| 引擎 | URL模板 | 说明 |
|------|---------|------|
| 百度 | `baidu.com/s?wd=QUERY` | 中文综合首选 |
| 头条 | `so.toutiao.com/search?keyword=QUERY` | 字节生态 |
| 必应 | `cn.bing.com/search?q=QUERY` | 微软引擎 |

---

## 🔧 Step 3: 上下文预处理（每次搜索前必须执行）

```
1. 指代消解: 检测"它/这个/那个/前者/后者" → 替换为前轮实体
2. 口语规范化: "X怎么办"→"X解决方法" / "X好不好"→"X评价推荐"
3. 否定提取: 检测"除了/不想/不要"-X → 记录排除项
4. 查询扩展: 同义词替换 + 领域术语补充
5. 多意图拆分: 检测多领域关键词 → 拆分子查询
```

---

## 🚀 Step 4: 执行搜索

### 工具选择

```
默认: web_fetch (快速抓取，90%场景)
切换: agent-browser (需登录/交互/反爬/动态内容)
兜底: scripts/web_search_v3.py (MCP不可用时)
```

### 迭代检索策略

| 查询类型 | 迭代轮数 | 策略 |
|----------|----------|------|
| 简单事实 | 1轮 | 单引擎，直接输出 |
| 复杂研究 | 2-3轮 | 双引擎并行 + 缺口分析 |
| 时效热点 | 2轮 | 多引擎并行 + 时效优先 |
| 决策支持 | 3轮 | 三引擎 + 深度分析 + 交叉验证 |

### 并行执行

```
简单查询: 1个P0引擎
中等查询: 2个引擎并行（P0 + P0/P1）
复杂查询: 3个引擎并行（P0 + P0 + P1）
超时: 单引擎≤5秒，并行≤8秒
```

---

## ✅ Step 5: 结果处理与输出

### Rerank五维评分

| 维度 | 权重 | 评分规则 |
|------|------|----------|
| 相关性 | 30% | 标题匹配 + 语义匹配 + 查询类型适配 |
| 权威性 | 30% | 来源权重（政务1.0→社交0.6） |
| 时效性 | 25% | 自适应时间衰减（新闻T½=24h，学术T½=3年） |
| 完整性 | 10% | 信息覆盖度 + 子问题覆盖 |
| 新颖性 | 5% | 多轮检索新发现价值 |

### 来源类型识别

| 标识 | 来源类型 | 权威性 | 采纳建议 |
|------|----------|--------|----------|
| 🏢 | 官方来源 | 95-100% | ⭐⭐⭐ 无需交叉验证 |
| 📰 | 权威媒体 | 80-94% | ⭐⭐ 建议与官方交叉验证 |
| 👥 | 技术社区 | 60-79% | ⭐ 需与官方交叉验证 |
| 📝 | 个人博客 | 40-59% | ⚠️ 强烈建议交叉验证 |
| ❓ | 未验证 | <40% | ❌ 不推荐 |

### 交叉验证（关键信息必须执行）

```
IF 查询涉及[版本号/发布日期/数据指标/政策法规]:
  → 提取关键信息（版本/日期/数值）
  → 多来源对比是否一致
  → 输出验证结论:
    ✅ 确认真实 (N个来源一致, 可信度X%)
    ⚠️ 存在冲突 (来源A说X, 来源B说Y)
```

### 输出格式（必须遵守）

```markdown
## 搜索结果 (按可信度排序)

### 🏢 官方来源
1. **标题** (权威性: 98%)
   - 来源: 🏢 来源名
   - 发布: YYYY-MM-DD (✅最新 / ⚠️可能过时 / ❌已过时)
   - URL: https://...
   - 摘要: ...
   - 采纳: ⭐⭐⭐ 强烈推荐

### 📰 权威媒体
2. **标题** (权威性: 85%)
   - 来源: 📰 媒体名
   - 采纳: ⭐⭐ 推荐

### 👥 技术社区
3. **标题** (权威性: 70%)
   - 采纳: ⭐ 可选

### 🔍 交叉验证
- 关键信息: [提取的关键事实]
- 验证结论: ✅确认 / ⚠️冲突
- 来源数: X个 (Y个官方 + Z个权威 + W个社区)
- 一致性: 100% / 描述冲突点

### ⏰ 时效性声明
- 数据获取时间: YYYY-MM-DD HH:MM
- 最新来源发布: YYYY-MM-DD
```

---

## 🛡️ Step 6: 错误恢复（搜索失败时必须执行）

```
IF web_fetch返回空结果:
  1. 放宽关键词（去除修饰词，保留核心词）
  2. 同义词替换重试
  3. 切换备用引擎
  4. IF 仍失败 → 英文翻译重试
  5. IF 仍失败 → 提示用户补充查询方向

IF web_fetch返回反爬/验证码:
  1. 自动切换 agent-browser
  2. IF agent-browser不可用 → 切换备用引擎

IF 搜索结果质量低:
  1. 放宽查询词
  2. 切换不同类型引擎（如从社区切到官方）
  3. 增加迭代轮数

IF 信息冲突:
  1. 标注冲突点
  2. 优先采信官方来源
  3. 提示用户需人工确认
```

---

## 📊 执行效率基准（v4.3.1新增）

> **静态性能指标表** — 不同查询类型的时间基准

| 查询类型 | 定义 | 目标时间 | 最大并行数 | 迭代轮数 |
|----------|------|----------|------------|----------|
| **简单事实** | 单点信息、明确答案（如"React是什么"） | ≤5秒 | 1 | 1轮 |
| **中等复杂** | 多维度需对比（如"React vs Vue"） | ≤10秒 | 2 | 1-2轮 |
| **时效热点** | 新闻、政策、事件（含时间筛选） | ≤8秒 | 2 | 1轮 |
| **复杂研究** | 决策支持、深度分析 | ≤15秒 | 3 | 2-3轮 |
| **运营查询** | 新增领域（ai_ecosystem/运营类） | ≤12秒 | 2 | 2轮 |

### 动态并行度调整

```
IF 查询含[对比/vs/哪个好/推荐/建议]:
  → 自动提升并行数至2-3
IF 查询含[是什么/定义/百科]:
  → 保持单引擎串行
```

---

## 🎯 检查点设计（v4.3.1新增）

> **关键决策用户确认点** — 防止自主失控，提升交互可控性

| 检查点位置 | 触发条件 | 确认内容 | 用户选项 |
|------------|----------|----------|----------|
| **Step1.5 路由确认** | 查询匹配≥2个领域 | "检测到多领域意图，是否拆分搜索？" | [确认拆分] / [选择主领域] / [取消] |
| **Step5.3 结果缺口** | 迭代后信息缺口仍存在 | "仍有未覆盖信息，是否继续迭代？" | [继续迭代] / [输出当前结果] |

### 检查点执行规则

```
// Step1.5 路由确认检查点
IF matchedDomains.length >= 2:
  → 提示用户: "检测到多领域意图（${matchedDomains}），建议拆分并行搜索"
  → 等待用户选择: [确认拆分] / [选择主领域] / [取消搜索]
  → IF 用户选择"选择主领域" → 路由到用户选定领域

// Step5.3 结果缺口检查点
IF gaps.length > 0 AND round < 3:
  → 提示用户: "仍有未覆盖信息：${gaps}，是否继续迭代？"
  → 等待用户选择: [继续迭代] / [输出当前结果]
  → IF 用户选择"输出当前结果" → 终止迭代，输出现有结果
```

---

## 📍 位置配置

```
默认城市: 通过_meta.json或环境变量CN_SEARCH_CITY配置
用户可随时说"我在XX市"更新默认城市
本地搜索URL自动注入城市参数
```

---

## 引用索引

| 需要详情 | 跳转链接 |
|----------|----------|
| 智能路由决策 | → [core/router.md](core/router.md) |
| 执行流程详解 | → [core/workflow.md](core/workflow.md) |
| 失败切换策略 | → [core/fallback.md](core/fallback.md) |
| 交叉验证机制 | → [skills/cross-validation.md](skills/cross-validation.md) |
| 垂直领域详情 | → [domains/](domains/) |
| 引擎完整列表 | → [engines/index.md](engines/index.md) |
| 高级操作符 | → [engines/operators.md](engines/operators.md) |
| 迭代检索流程 | → [skills/iterative-search.md](skills/iterative-search.md) |
| Rerank评分 | → [skills/rerank.md](skills/rerank.md) |
| 并行执行策略 | → [skills/parallel-execution.md](skills/parallel-execution.md) |

---

## 网络可用性标识

| 标识 | 含义 | 决策 |
|------|------|------|
| ✅ | 中国网络无障碍 | **优先使用** |
| ⚠️ | 部分地区不稳定 | 备用，失败时切换 |
| ❌ | 需网络代理 | 仅特殊需求使用 |

---

## 更新日志

### v4.3.2 (2026-05-16) - 电商运营领域拓展 🆕
- 🌐 **新增领域**: 天猫运营（tmall-ops）+ 京东运营（jd-ops）+ 1688批发（1688-ops）
- 🔧 **新增引擎**: 天猫商家中心/规则中心/营销中心 + 京东商家中心/规则中心/营销中心 + 1688批发市场/分销平台（+6引擎）
- 🔀 **路由扩展**: 新增3电商领域关键词匹配
- 📈 **引擎总数**: 150+（原144 + 6新增）
- 📈 **领域总数**: 21（原18 + 3新增）

### v4.3.1 (2026-05-16) - 领域拓展 + 执行优化 🆕
- 🌐 **新增领域**: AI技术/开发者生态（ai-ecosystem）+ 小红书运营（xiaohongshu-ops）+ 抖音运营（douyin-ops）
- 🔧 **新增引擎**: GitHub + skills.sh + 腾讯SkillHub + 千瓜数据 + 巨量算数 + 飞瓜数据 + 达人通（+6引擎）
- 📊 **执行效率基准**: 静态性能指标表（5种查询类型时间基准≤15秒）
- 🎯 **检查点改进**: 新增Step1.5路由确认 + Step5.3结果缺口检查点
- 🔀 **路由扩展**: 新增3领域关键词匹配 + 运营类多意图拆分规则
- 📈 **引擎总数**: 144+（原138 + 6新增）

### v4.3.0 (2026-05-02) - 语义理解突破
- 🧠 **语义Embedding**: 接入BGE中文模型替代字符级相似度，支持同义词语义匹配
- 🚀 **动态并行度**: 基于查询复杂度动态调整引擎数量（1-5），集成自适应超时控制
- ⚖️ **自适应权重**: 查询类型驱动的Rerank权重（新闻时效性+/学术权威性+/医学权威性++）
- ⚠️ **免责声明强化**: 医学/法律/金融领域程序化强制附加免责声明
- ⏰ **时间参数智能注入**: TimeIntentAnalyzer识别历史/当前查询，动态时间范围推断

### v4.2.0 (2026-05-02) - 渐进式引导架构重构
- 🏗️ **渐进式技能引导**: 首Token路由决策，按需加载领域详情
- 🔀 **多意图拆分**: 支持单查询多领域并行检索
- 🚫 **否定意图处理**: "除了X"自动排除指定来源
- 📍 **地理位置感知**: 本地搜索自动注入城市参数
- ✅ **交叉验证机制**: 关键信息多来源对比+冲突检测
- 🏥 **医学领域**: 新增好大夫/春雨医生/用药助手/医脉通
- ⚖️ **法律领域**: 新增无讼/法信/找法网
- 🎓 **教育领域**: 新增考研帮/粉笔公考/中国大学MOOC/学堂在线
- 🌤️ **天气专用引擎**: 新增和风天气API
- ⚖️ **Rerank权重调整**: 相关性30%+权威性30%+时效性25%+完整性10%+新颖性5%
- 🛡️ **错误恢复决策树**: 结构化重试策略+反爬自动降级
- 📋 **输出格式强制约束**: 按可信度排序+交叉验证+时效性声明

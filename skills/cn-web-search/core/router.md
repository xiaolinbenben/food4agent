---
name: router
description: 智能路由决策树 - 渐进式路由 + 上下文消歧 + 多意图 + 否定意图 + 地域感知
version: 4.2.0
changelog: v4.2.0 渐进式路由重构，新增多意图/否定意图/地域感知/消歧
---

# 智能路由决策树 v4.2.0

> **核心原则**: 渐进式路由 — 首Token定领域，按需消歧，逐步细化

---

## Level 0: 查询预处理（路由前必须执行）

### 0.1 指代消解

```
检测指代词: "它/这个/那个/前者/后者/上面/刚才"
→ 替换为前轮对话中的实体
→ 示例: "它的价格" + 前轮"英伟达" → "英伟达的价格"
```

### 0.2 口语规范化

```
"X怎么办"     → "X解决方法"
"X好不好"     → "X评价推荐"
"X靠谱不"     → "X可靠性评价"
"整一个X教程" → "X入门教程"
"X咋搞"       → "X操作方法"
"X多少钱"     → "X价格"
"X和Y哪个好"  → "X Y对比评测"
```

### 0.3 否定意图提取

```
检测否定词: "除了/不想/不要/排除/去掉/别/非/不包括"
→ 提取排除项X
→ 生成排除过滤器
→ 示例: "除了CSDN以外的React教程" → 排除 csdn.net
→ 示例: "不想看广告多的推荐" → 排除含"推广/广告/赞助"的结果
```

### 0.4 多意图识别与拆分

```
IF 查询含多个领域关键词:
  → 拆分为独立子查询
  → 按领域分别路由
  → 结果合并输出

示例:
"英伟达财报和最新新闻" → 子查询1: "英伟达财报"(finance) + 子查询2: "英伟达最新新闻"(news)
"React性能优化论文"   → 子查询1: "React性能优化"(tech) + 子查询2: "性能优化论文"(academic)
```

### 0.5 地域敏感查询识别

```
地域敏感词表: [附近/周边/本地/同城/房价/招聘/外卖/天气/餐厅/酒店/机票/快递/医院/学校/银行]

IF 查询含地域敏感词:
  → 检查是否含城市名
  → IF 无城市名:
      → 读取默认城市配置（_meta.json → CN_SEARCH_CITY）
      → IF 无默认城市 → 提示用户"请告诉我您所在的城市"
  → IF 有城市名 → 注入城市参数到URL模板
```

---

## Level 1: 首Token领域匹配

> **执行时间**: <50ms | **规则**: 按关键词首次命中确定领域

```
关键词 → 领域映射表:

论文/学术/研究/博士/硕士/文献/专利/标准        → academic
股票/基金/A股/港股/财报/黄金/理财              → finance
TICKER/Seeking/Finviz/Macrotrends              → us_stock
GDP/国债/收益率/BEA/Treasury                   → macro
IPO/独角兽/Pre-IPO/CB Insights                 → pre_ipo
WSB/Reddit/散户/Nitter/情绪                     → sentiment
AI/编程/React/Python/Java/Go/代码/bug/框架      → tech
新闻/热点/最新/今天/实时/突发                   → news
是什么/定义/百科/介绍/意思                      → knowledge
附近/餐厅/天气/酒店/机票/外卖/购物              → life
考研/考试/真题/课程/教材/大学/高考/公考         → education
症状/治疗/药品/医院/健康/医学/疾病              → medical
法律/法规/判决/合同/律师/案件                   → legal
视频/B站/抖音/知乎/微博/公众号/小红书           → content
其他                                           → general
```

---

## Level 2: 上下文消歧

> **解决路由冲突**: 当关键词匹配多个领域时，结合上下文消歧

### 2.1 优先级排序（从高到低）

| 优先级 | 领域 | 关键词示例 | 决策理由 |
|--------|------|------------|----------|
| 1 | **academic** | 论文、学术、研究、博士、硕士 | 学术查询最精准 |
| 2 | **medical** | 症状、治疗、药品、医院 | 医疗安全优先 |
| 3 | **legal** | 法律、法规、判决、合同 | 法律准确性优先 |
| 4 | **finance** | 股票、基金、A股、港股 | 财经查询专业性强 |
| 5 | **us_stock** | Seeking Alpha、Finviz | 美股深度专用 |
| 6 | **macro** | GDP、国债、收益率 | 宏观数据专用 |
| 7 | **pre_ipo** | IPO、独角兽 | 上市前专用 |
| 8 | **sentiment** | WSB、Reddit | 情绪监测专用 |
| 9 | **education** | 考研、考试、真题 | 教育专用 |
| 10 | **tech** | AI、编程、React、Python | 技术查询最常见 |
| 11 | **news** | 新闻、热点、最新 | 时效性优先 |
| 12 | **knowledge** | 是什么、定义、百科 | 知识查询通用 |
| 13 | **life** | 附近、餐厅、天气 | 生活查询本地化 |
| 14 | **content** | 视频、B站、抖音 | 内容查询补充 |
| 15 | **general** | 其他 | 默认兜底 |

### 2.2 上下文消歧规则

```
IF 关键词匹配多个领域:
  → 检查前轮对话的领域上下文
  → 检查查询中其他词的领域倾向
  → 按优先级排序选择

示例1: "知乎上关于AI的讨论"
  匹配: 知乎(content) + AI(tech)
  其他词: "讨论" → 偏content
  决策: content（"讨论"消歧）

示例2: "今天的AI新闻"
  匹配: 今天(news) + AI(tech)
  其他词: "新闻" → 偏news
  决策: news（时效性优先）

示例3: "苹果"歧义消解
  前轮聊"手机" → tech（苹果公司）
  前轮聊"水果" → life（苹果水果）
  无上下文 → finance（苹果公司，更常见搜索意图）
```

---

## Level 3: 领域引擎选择

> **执行时间**: <100ms

### 技术领域 (tech)

| 子类型 | P0引擎 | P1引擎 | URL模板 |
|--------|--------|--------|---------|
| AI技术 | CSDN + ArXiv | 掘金 + GitHub | `so.csdn.net/so/search/s.do?q=QUERY` |
| 前后端 | StackOverflow + CSDN | 掘金 + GitHub | `stackoverflow.com/search?q=QUERY` |
| 移动端 | CSDN + 掘金 | StackOverflow | `juejin.cn/search?query=QUERY` |

### 学术领域 (academic)

| 子类型 | P0引擎 | P1引擎 | URL模板 |
|--------|--------|--------|---------|
| 中文论文 | 知网 + 万方 | 维普 + 百度学术 | `cnki.net/search?q=QUERY` |
| 英文论文 | ArXiv + Google Scholar | Semantic Scholar | `arxiv.org/api/query?search_query=all:QUERY` |
| 专利 | 国家知识产权局 | Google Patents | `pss-system.cponline.cnipa.gov.cn` |

### 财经领域 (finance)

| 子类型 | P0引擎 | P1引擎 | URL模板 |
|--------|--------|--------|---------|
| A股 | 东方财富 + 雪球 | 同花顺 + 集思录 | `so.eastmoney.com/news/s?keyword=QUERY` |
| 基金 | 天天基金 + 蛋卷 | 且慢 | `fund.eastmoney.com` |
| 黄金 | 金十数据 + 上金所 | 东方财富 | `jin10.com/search?keyword=QUERY` |

### 美股深度 (us_stock)

| 子类型 | P0引擎 | URL模板 | 说明 |
|--------|--------|---------|------|
| 基本面 | Seeking Alpha | `seekingalpha.com/symbol/TICKER` | 公司介绍、产品线 |
| 数据筛选 | Finviz | `finviz.com/quote.ashx?t=TICKER` | P/E、EPS、机构持仓 |
| 历史财务 | Macrotrends | `macrotrends.net/stocks/charts/TICKER/NAME/revenue` | 年度/季度收入 |

### 全球宏观 (macro)

| 子类型 | P0引擎 | URL模板 | 说明 |
|--------|--------|---------|------|
| 经济数据 | BEA | `bea.gov/news/current-releases` | GDP、国际贸易 |
| 国债利率 | Treasury | `home.treasury.gov/` | 收益率曲线 |
| 经济指标 | Census | `census.gov/economic-indicators/` | 零售、制造业PMI |

### Pre-IPO (pre_ipo)

| 子类型 | P0引擎 | URL模板 | 说明 |
|--------|--------|---------|------|
| IPO日历 | IPOScoop | `iposcoop.com/ipo-calendar/` | 承销商、SCOOP评级 |
| IPO数据 | StockAnalysis | `stockanalysis.com/ipos/` | 首日涨幅、破发 |
| 独角兽 | CB Insights | `cbinsights.com/research-unicorn-companies` | 估值、行业 |

### 散户情绪 (sentiment)

| 子类型 | P0引擎 | URL模板 | 说明 |
|--------|--------|---------|------|
| WSB情绪 | Reddit WSB | `reddit.com/r/wallstreetbets/top/.rss` | 散户热帖 |
| 政策风向 | Nitter | `nitter.net/USERNAME/rss` | 推文RSS |

### 新闻领域 (news)

| 子类型 | P0引擎 | P1引擎 | URL模板 | 时效参数 |
|--------|--------|--------|---------|----------|
| 热点 | 百度资讯 + 头条 | 微博 | `baidu.com/s?wd=QUERY&rtt=1` | `&bsst=1` |
| 财经 | 东方财富 + 财新 | 华尔街见闻 | `eastmoney.com` | - |
| 政务 | 中国政府网 + 人民日报 | 央视新闻 | `gov.cn/search` | - |

### 知识领域 (knowledge)

| 子类型 | P0引擎 | P1引擎 | URL模板 |
|--------|--------|--------|---------|
| 百科 | 百度百科 + Wikipedia | 知乎百科 | `baike.baidu.com/item/QUERY` |
| 计算 | WolframAlpha | DDG Instant | `wolframalpha.com/input?i=QUERY` |

### 生活领域 (life)

| 子类型 | P0引擎 | P1引擎 | URL模板 |
|--------|--------|--------|---------|
| 本地 | 高德 + 大众点评 | 美团 | `amap.com/search?query=QUERY&city=CITY` |
| 购物 | 淘宝 + 京东 | 什么值得买 | `s.taobao.com/search?q=QUERY` |
| 出行 | 12306 + 携程 | 去哪儿 | `12306.cn` |
| 天气 | 和风天气 | 百度天气 | `qweather.com/search?city=CITY` |

### 教育领域 (education) 🆕

| 子类型 | P0引擎 | P1引擎 | URL模板 |
|--------|--------|--------|---------|
| 考研 | 考研帮 + 中国知网 | 学堂在线 | `kaoyan.com/search?keyword=QUERY` |
| 公考 | 粉笔公考 | 华图教育 | `fenbi.com/search?keyword=QUERY` |
| 课程 | 中国大学MOOC | 学堂在线 | `icourse163.org/search?keyword=QUERY` |
| 论文 | 知网 + 万方 | 百度学术 | `cnki.net/search?q=QUERY` |
| 高考 | 高考网 + 阳光高考 | 掌上高考 | `gaokao.chsi.com.cn` |

### 医学领域 (medical) 🆕

| 子类型 | P0引擎 | P1引擎 | URL模板 |
|--------|--------|--------|---------|
| 症状 | 丁香园 + 好大夫 | 春雨医生 | `search.dxy.com/?keyword=QUERY` |
| 用药 | 用药助手 | 丁香医生 | `drugs.dxy.cn/search?keyword=QUERY` |
| 学术 | PubMed | 医脉通 | `pubmed.ncbi.nlm.nih.gov/?term=QUERY` |
| 医院 | 好大夫 | 春雨医生 | `haodf.com/search?keyword=QUERY` |

### 法律领域 (legal) 🆕

| 子类型 | P0引擎 | P1引擎 | URL模板 |
|--------|--------|--------|---------|
| 判例 | 中国裁判文书网 | 无讼 | `wenshu.court.gov.cn` |
| 法规 | 国家法律法规库 | 北大法宝 | `flk.npc.gov.cn/` |
| 合同 | 法信 | 找法网 | `faxin.cn/search?keyword=QUERY` |
| 咨询 | 找法网 | 华律网 | `findlaw.cn/search?keyword=QUERY` |

### 内容领域 (content)

| 子类型 | P0引擎 | P1引擎 | URL模板 |
|--------|--------|--------|---------|
| 公众号 | 搜狗微信 | 必应公众号 | `weixin.sogou.com/weixin?type=2&query=QUERY` |
| 视频 | B站 + 抖音 | 西瓜视频 | `search.bilibili.com/all?keyword=QUERY` |
| 社交 | 知乎 + 微博 | 小红书 | `zhihu.com/search?q=QUERY` |

### 通用搜索 (general)

| 引擎 | URL模板 | 说明 |
|------|---------|------|
| 百度 | `baidu.com/s?wd=QUERY` | 中文综合首选 |
| 头条 | `so.toutiao.com/search?keyword=QUERY` | 字节生态 |
| 必应 | `cn.bing.com/search?q=QUERY` | 微软引擎 |

---

## Level 4: 执行策略决策

> **动态决策，基于查询复杂度**

| 复杂度 | 判断条件 | 执行策略 | 交叉验证 |
|--------|----------|----------|----------|
| 简单 | 单点信息、明确答案 | 单引擎单轮 | 不需要 |
| 中等 | 多维度、需对比 | 双引擎并行 + 2轮迭代 | 建议验证 |
| 时效 | 新闻、政策、事件 | 多引擎并行 + 时效优先 | 建议验证 |
| 复杂 | 决策支持、购买/投资 | 三引擎 + 3轮迭代 + 深度分析 | **必须验证** |

---

## 路由决策示例

```
示例1: 技术查询
用户: "React性能优化怎么做"
→ 预处理: 无指代/无否定/无地域
→ 领域匹配: "React" → tech
→ 子类型: 前后端
→ 引擎: CSDN + StackOverflow
→ 策略: 双引擎并行

示例2: 多意图查询
用户: "英伟达财报和最新新闻"
→ 预处理: 多意图拆分
→ 子查询1: "英伟达财报" → finance → 东方财富 + 雪球
→ 子查询2: "英伟达最新新闻" → news → 百度资讯 + 头条
→ 策略: 4引擎并行，结果合并

示例3: 否定意图查询
用户: "除了CSDN以外的React教程"
→ 预处理: 否定提取 → 排除csdn.net
→ 领域匹配: "React" → tech
→ 引擎: StackOverflow + 掘金 + GitHub
→ 策略: 排除CSDN，双引擎并行

示例4: 地域敏感查询
用户: "附近好吃的火锅"
→ 预处理: 地域敏感 → 检查城市 → "北京"
→ 领域匹配: "附近" → life
→ 引擎: 高德 + 大众点评
→ URL: amap.com/search?query=火锅&city=北京

示例5: 歧义消解
用户: "苹果" (前轮聊"手机壳")
→ 预处理: 指代消解 → 前轮"手机壳" → tech倾向
→ 领域匹配: "苹果" → tech(公司) vs life(水果)
→ 上下文消歧: 前轮tech → 选择tech
→ 引擎: CSDN + 掘金

示例6: 医学查询 🆕
用户: "头疼是什么原因"
→ 领域匹配: "头疼" → medical
→ 子类型: 症状
→ 引擎: 丁香园 + 好大夫
→ 策略: 双引擎 + ⚠️免责声明

示例7: 法律查询 🆕
用户: "劳动合同解除赔偿标准"
→ 领域匹配: "合同" → legal
→ 子类型: 法规
→ 引擎: 国家法律法规库 + 法信
→ 策略: 双引擎 + 交叉验证（必须）
```

---
domain: finance
keywords: [股票, 基金, 财经, A股, 港股, 美股, 黄金, 投资, 理财, 财报, K线, 涨停, 可转债, ETF, TICKER, Seeking Alpha, Finviz, Macrotrends, GDP, 国债, 收益率, BEA, Treasury, IPO, 独角兽, Pre-IPO, WSB, Reddit, 散户]
version: 4.2.0
---

# 财经领域搜索（含美股深度/宏观/Pre-IPO/情绪）

## 快速路由

| 子类型 | 触发关键词 | P0引擎 | P1引擎 |
|--------|------------|--------|--------|
| A股股票 | A股、股票代码、财报、业绩、研报 | 东方财富 + 雪球 | 同花顺 + 集思录 |
| 美股港股 | 美股、港股、纳斯达克 | 雪球 + 富途牛牛 | 老虎证券 |
| 美股深度 | TICKER、Seeking Alpha、Finviz | Seeking Alpha + Finviz | Macrotrends |
| 全球宏观 | GDP、国债、收益率、BEA | Treasury + BEA | Census |
| Pre-IPO | IPO、独角兽、Pre-IPO | IPOScoop + StockAnalysis | CB Insights |
| 散户情绪 | WSB、Reddit、散户情绪 | Reddit WSB | Nitter |
| 基金 | 基金、ETF、LOF、公募基金 | 天天基金 + 蛋卷基金 | 且慢 |
| 黄金贵金属 | 黄金、金价、贵金属 | 金十数据 + 上金所 | 东方财富黄金 |
| 理财投资 | 理财、投资、可转债、国债 | 集思录 + 且慢 | 支付宝基金 |

---

## 引擎URL模板

### A股/港股/基金

| 引擎 | URL模板 | 说明 | 来源类型 |
|------|---------|------|----------|
| 东方财富 | `https://so.eastmoney.com/news/s?keyword=QUERY` | A股财经首选 | 🏢 官方 |
| 雪球 | `https://xueqiu.com/k?q=QUERY` | 股票社区、研报 | 👥 技术社区 |
| 同花顺 | `https://t.10jqka.com.cn/search?keyword=QUERY` | 股票信息 | 🏢 官方 |
| 天天基金 | `https://fund.eastmoney.com/fund.html#QUERY` | 基金数据 | 🏢 官方 |
| 蛋卷基金 | `https://danjuanfunds.com/search?keyword=QUERY` | 基金社区 | 👥 技术社区 |
| 集思录 | `https://www.jisilu.cn/explore/?keyword=QUERY` | 投资策略社区 | 👥 技术社区 |
| 金十数据 | `https://www.jin10.com/search?keyword=QUERY` | 贵金属外汇资讯 | 📰 权威媒体 |
| 财新 | `https://search.caixin.com/search/news?keyword=QUERY` | 深度财经 | 📰 权威媒体 |

### 美股深度 🆕

| 引擎 | URL模板 | 说明 | 来源类型 |
|------|---------|------|----------|
| Seeking Alpha | `https://seekingalpha.com/symbol/TICKER` | 公司基本面、业务分析 | 📰 权威媒体 |
| Finviz | `https://finviz.com/quote.ashx?t=TICKER` | P/E、EPS、内部人交易、机构持仓 | 🏢 官方数据 |
| Macrotrends | `https://www.macrotrends.net/stocks/charts/TICKER/NAME/revenue` | 历史财务数据 | 🏢 官方数据 |

### 全球宏观 🆕

| 引擎 | URL模板 | 说明 | 来源类型 |
|------|---------|------|----------|
| BEA | `https://www.bea.gov/news/current-releases` | GDP、个人收入、国际贸易 | 🏢 官方 |
| Treasury | `https://home.treasury.gov/` | 国债收益率曲线 | 🏢 官方 |
| Census | `https://www.census.gov/economic-indicators/` | 建筑许可、零售、PMI | 🏢 官方 |

### Pre-IPO 🆕

| 引擎 | URL模板 | 说明 | 来源类型 |
|------|---------|------|----------|
| IPOScoop | `https://www.iposcoop.com/ipo-calendar/` | IPO日历、SCOOP评级 | 📰 权威媒体 |
| StockAnalysis | `https://stockanalysis.com/ipos/` | 首日涨幅、破发情况 | 📰 权威媒体 |
| CB Insights | `https://www.cbinsights.com/research-unicorn-companies` | 独角兽名单 | 📰 权威媒体 |

### 散户情绪 🆕

| 引擎 | URL模板 | 说明 | 来源类型 |
|------|---------|------|----------|
| Reddit WSB | `https://www.reddit.com/r/wallstreetbets/top/.rss` | 散户情绪、热帖 | 👥 社区 |
| Nitter | `https://nitter.net/USERNAME/rss` | 政策风向RSS | 👥 社交 |

---

## 执行示例

### A股/港股查询

```javascript
web_fetch(url="https://so.eastmoney.com/news/s?keyword=英伟达财报", maxChars=10000)
web_fetch(url="https://xueqiu.com/k?q=英伟达", maxChars=8000)
```

### 美股深度查询 🆕

```javascript
web_fetch(url="https://seekingalpha.com/symbol/AAPL", extractMode="text", maxChars=8000)
web_fetch(url="https://finviz.com/quote.ashx?t=NVDA", extractMode="text", maxChars=8000)
web_fetch(url="https://www.macrotrends.net/stocks/charts/AAPL/apple/revenue", extractMode="text", maxChars=8000)
```

### 宏观数据查询 🆕

```javascript
web_fetch(url="https://www.bea.gov/news/current-releases", extractMode="text", maxChars=8000)
web_fetch(url="https://home.treasury.gov/", extractMode="text", maxChars=8000)
web_fetch(url="https://www.census.gov/economic-indicators/", extractMode="text", maxChars=8000)
```

### Pre-IPO查询 🆕

```javascript
web_fetch(url="https://www.iposcoop.com/ipo-calendar/", extractMode="text", maxChars=8000)
web_fetch(url="https://stockanalysis.com/ipos/", extractMode="text", maxChars=8000)
web_fetch(url="https://www.cbinsights.com/research-unicorn-companies", extractMode="text", maxChars=8000)
```

### 散户情绪查询 🆕

```javascript
web_fetch(url="https://www.reddit.com/r/wallstreetbets/top/.rss", extractMode="text", maxChars=8000)
web_fetch(url="https://nitter.net/realDonaldTrump/rss", extractMode="text", maxChars=8000)
```

### 基金/黄金/理财

```javascript
web_fetch(url="https://danjuanfunds.com/search?keyword=沪深300")
web_fetch(url="https://www.jin10.com/search?keyword=黄金")
web_fetch(url="https://www.jisilu.cn/explore/?keyword=可转债")
web_fetch(url="https://search.caixin.com/search/news?keyword=金融监管")
```

---

## 并行策略

| 场景 | 并行组合 | 说明 |
|------|----------|------|
| A股查询 | 东方财富 + 雪球 | 数据+社区观点 |
| 美股深度 | Seeking Alpha + Finviz + Macrotrends | 基本面+数据+历史 |
| 宏观分析 | Treasury + BEA + Census | 利率+GDP+PMI |
| Pre-IPO | IPOScoop + StockAnalysis | 日历+表现数据 |
| 情绪监测 | Reddit WSB + Nitter | 散户+政策 |
| 基金查询 | 天天基金 + 蛋卷基金 | 数据+社区讨论 |
| 投资策略 | 集思录 + 且慢 | 社区+投顾 |
| 财经新闻 | 财新 + 华尔街见闻 | 深度+国际 |

---

## 信源权重（v4.0.0更新）

```
🏢 官方数据（交易所、BEA、Treasury、Census）     → 权重 1.0
🏢 官方平台（东方财富、同花顺、天天基金）         → 权重 0.95
🏢 官方数据（Finviz、Macrotrends）                → 权重 0.95
📰 权威财经（财新、华尔街见闻、金十数据、SA）      → 权重 0.9
📰 专业平台（IPOScoop、StockAnalysis、CB Insights）→ 权重 0.85
👥 投资社区（雪球、集思录、蛋卷基金）              → 权重 0.7
👥 散户情绪（Reddit WSB、Nitter）                 → 权重 0.6
👥 综合资讯（头条、百度）                          → 权重 0.5
```

---

## 采纳建议（v4.0.0更新）

| 来源类型 | 采纳建议 | 验证建议 |
|----------|----------|----------|
| 🏢 官方数据/平台 | ⭐⭐⭐ 强烈推荐 | 无需交叉验证 |
| 🏢 Finviz/Macrotrends数据 | ⭐⭐⭐ 强烈推荐 | 无需交叉验证 |
| 📰 权威财经媒体 | ⭐⭐ 推荐 | 建议与官方来源交叉验证 |
| 📰 专业平台(SA/IPOScoop/CB) | ⭐⭐ 推荐 | 建议与官方来源交叉验证 |
| 👥 投资社区 | ⭐ 可选 | 需与官方来源交叉验证 |
| 👥 散户情绪(WSB/Nitter) | ⚠️ 谨慎采纳 | 仅供情绪参考，非投资建议 |
| 👥 综合资讯 | ⚠️ 谨慎采纳 | 强烈建议交叉验证 |

---
name: finance-search
description: 财经投资类搜索子技能 - 股票、基金、黄金、理财、财经新闻
trigger:
  keywords: [股票, 基金, 财经, A股, 美股, 港股, 黄金, 投资, 理财, 财报, 基金定投, 可转债, ETF]
---

# 财经投资类搜索

## 查询类型识别

| 子类型 | 触发关键词 |
|--------|------------|
| A股股票 | A股、股票代码、财报、业绩、研报 |
| 美股港股 | 美股、港股、纳斯达克、纽交所 |
| 基金 | 基金、基金定投、ETF、LOF、公募基金 |
| 黄金贵金属 | 黄金、金价、贵金属、白银、铂金 |
| 理财投资 | 理财、投资、可转债、国债、信托 |

---

## 引擎路由表

### A股股票

| 优先级 | 引擎 | URL模板 | 说明 |
|--------|------|---------|------|
| P0 | 东方财富 | `https://so.eastmoney.com/news/s?keyword=QUERY` | A股财经首选 |
| P0 | 雪球 | `https://xueqiu.com/k?q=QUERY` | 股票社区、研报 |
| P1 | 同花顺 | `https://t.10jqka.com.cn/search?keyword=QUERY` | 股票信息 |
| P1 | 新浪财经 | `https://search.sina.com.cn/?q=QUERY&c=news&from=channel` | 财经资讯 |
| B | 百度资讯 | `https://www.baidu.com/s?wd=QUERY&rtt=1` | 广泛搜索 |

### 美股港股

| 优先级 | 引擎 | URL模板 | 说明 |
|--------|------|---------|------|
| P0 | 雪球 | `https://xueqiu.com/k?q=QUERY` | 美股港股社区 |
| P0 | 富途牛牛 | `https://www.futunn.com/search?q=QUERY` | 港美股行情 |
| P1 | 老虎证券 | `https://www.laohu8.com/search?keyword=QUERY` | 美股资讯 |
| B | 必应英文 | `https://www.bing.com/search?q=QUERY+stock` | 英文搜索 |

### 基金

| 优先级 | 引擎 | URL模板 | 说明 |
|--------|------|---------|------|
| P0 | 天天基金 | `https://fund.eastmoney.com/fund.html#QUERY` | 基金数据 |
| P0 | 蛋卷基金 | `https://danjuanfunds.com/search?keyword=QUERY` | 基金社区 |
| P1 | 且慢 | `https://qieman.com/search?keyword=QUERY` | 基金投顾 |
| B | 东方财富 | `https://so.eastmoney.com/news/s?keyword=QUERY` | 广泛搜索 |

### 黄金贵金属

| 优先级 | 引擎 | URL模板 | 说明 |
|--------|------|---------|------|
| P0 | 金十数据 | `https://www.jin10.com/search?keyword=QUERY` | 贵金属资讯 |
| P0 | 上海黄金交易所 | `https://www.sge.com.cn/sjzx/jrhq` | 黄金行情官方 |
| P1 | 东方财富黄金 | `https://quote.eastmoney.com/center/gridlist.html#hg_qihuo` | 黄金期货行情 |
| B | 百度资讯 | `https://www.baidu.com/s?wd=QUERY+金价` | 广泛搜索 |

### 理财投资

| 优先级 | 引擎 | URL模板 | 说明 |
|--------|------|---------|------|
| P0 | 集思录 | `https://www.jisilu.cn/explore/?keyword=QUERY` | 投资社区 |
| P0 | 且慢 | `https://qieman.com/search?keyword=QUERY` | 基金投顾 |
| P1 | 支付宝基金 | `https://fundprod.alipay.com/agreement/fundsign.htm` | 基金平台 |
| B | 东方财富 | `https://so.eastmoney.com/news/s?keyword=QUERY` | 广泛搜索 |

### 财经新闻

| 优先级 | 引擎 | URL模板 | 说明 |
|--------|------|---------|------|
| P0 | 财新 | `https://search.caixin.com/search/news?keyword=QUERY` | 深度财经 |
| P0 | 东方财富 | `https://so.eastmoney.com/news/s?keyword=QUERY` | 财经资讯 |
| P1 | 华尔街见闻 | `https://wallstreetcn.com/search?q=QUERY` | 国际财经 |
| B | 头条搜索 | `https://so.toutiao.com/search?keyword=QUERY` | 广泛搜索 |

---

## 并行策略

| 场景 | 并行组合 | 说明 |
|------|----------|------|
| A股查询 | 东方财富 + 雪球 | 数据+社区观点 |
| 基金查询 | 天天基金 + 蛋卷基金 | 数据+社区讨论 |
| 投资策略 | 集思录 + 且慢 | 社区+投顾 |
| 财经新闻 | 财新 + 华尔街见闻 | 深度+国际 |

---

## 使用示例

```javascript
// A股股票查询
web_fetch(url="https://so.eastmoney.com/news/s?keyword=英伟达财报", maxChars=10000)
web_fetch(url="https://xueqiu.com/k?q=英伟达", maxChars=8000)

// 基金查询
web_fetch(url="https://danjuanfunds.com/search?keyword=沪深300", maxChars=8000)

// 黄金行情
web_fetch(url="https://www.jin10.com/search?keyword=黄金", maxChars=8000)
web_fetch(url="https://www.sge.com.cn/sjzx/jrhq", maxChars=5000)

// 可转债查询
web_fetch(url="https://www.jisilu.cn/explore/?keyword=可转债", maxChars=8000)

// 财经深度
web_fetch(url="https://search.caixin.com/search/news?keyword=金融监管", maxChars=10000)
```

---

## 信源权重（Rerank用）

```
官方数据（交易所、官方平台）     → 权重 1.0
专业财经（财新、华尔街见闻）     → 权重 0.9
数据平台（东方财富、同花顺）     → 权重 0.8
投资社区（雪球、集思录）         → 权重 0.7
综合资讯（头条、百度）           → 权重 0.5
```
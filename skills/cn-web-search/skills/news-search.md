---
name: news-search
description: 新闻类搜索子技能 - 热点新闻、财经新闻、政务新闻
trigger:
  keywords: [新闻, 热点, 最新, 今天, 实时, 财经, 政策, 政府]
---

# 新闻类搜索

## 查询类型识别

| 子类型 | 触发关键词 |
|--------|------------|
| 热点新闻 | 新闻、热点、最新、今天、实时 |
| 财经新闻 | 财经、A股、财报、公司名 |
| 政务新闻 | 政策、政府、国务院、发改委 |

---

## 引擎路由表

### 热点新闻

| 优先级 | 引擎 | URL模板 | 说明 |
|--------|------|---------|------|
| P0 | 百度资讯 | `https://www.baidu.com/s?wd=QUERY&rtt=1&bsst=1` | 实时热点 |
| P0 | 今日头条 | `https://so.toutiao.com/search?keyword=QUERY` | 字节生态 |
| P1 | 微博热搜 | `https://s.weibo.com/weibo?q=QUERY` | 社交热点 |
| B | 必应中文 | `https://cn.bing.com/search?q=QUERY` | 广泛搜索 |

### 财经新闻

| 优先级 | 引擎 | URL模板 | 说明 |
|--------|------|---------|------|
| P0 | 东方财富 | `https://so.eastmoney.com/news/s?keyword=QUERY` | A股财经 |
| P0 | 财新 | `https://search.caixin.com/search/news?keyword=QUERY` | 深度财经 |
| P1 | 华尔街见闻 | `https://wallstreetcn.com/search?q=QUERY` | 国际财经 |
| B | 头条搜索 | `https://so.toutiao.com/search?keyword=QUERY` | 广泛搜索 |

### 政务新闻

| 优先级 | 引擎 | URL模板 | 说明 |
|--------|------|---------|------|
| P0 | 中国政府网 | `https://www.gov.cn/search/index.htm?keyword=QUERY` | 权威政务 |
| P0 | 人民日报 | `http://search.people.com.cn/cnpeople/search.do?keyword=QUERY` | 权威媒体 |
| P1 | 央视新闻 | `https://news.cctv.com/search.shtml?q=QUERY` | 央媒 |
| B | 必应中文 | `https://cn.bing.com/search?q=QUERY` | 广泛搜索 |

---

## 并行策略

| 场景 | 并行组合 | 说明 |
|------|----------|------|
| 热点新闻 | 百度资讯 + 今日头条 | 多信源热点 |
| 财经新闻 | 东方财富 + 财新 | 资讯+深度 |

---

## 信源权重

```
权威政务媒体（政府网、人民日报、央视） → 权重 1.0
专业财经（财新、华尔街见闻）          → 权重 0.9
字节生态（头条、抖音）                → 权重 0.8
综合资讯（百度资讯）                  → 权重 0.7
社交平台（微博）                      → 权重 0.6
```
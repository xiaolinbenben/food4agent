---
domain: news
keywords: [新闻, 热点, 最新, 今天, 实时, 突发, 动态, 事件, 政策, 政府, 国务院]
version: 4.2.0
---

# 新闻领域搜索

## 快速路由

| 子类型 | 触发关键词 | P0引擎 | P1引擎 |
|--------|------------|--------|--------|
| 热点新闻 | 新闻、热点、最新、今天、实时 | 百度资讯 + 头条 | 微博 |
| 财经新闻 | 财经、A股、财报、公司名 | 东方财富 + 财新 | 华尔街见闻 |
| 政务新闻 | 政策、政府、国务院、发改委 | 中国政府网 + 人民日报 | 央视新闻 |

---

## 引擎URL模板

| 引擎 | URL模板 | 说明 | 来源类型 |
|------|---------|------|----------|
| 百度资讯 | `https://www.baidu.com/s?wd=QUERY&rtt=1&bsst=1` | 实时热点 | 👥 技术社区 |
| 头条搜索 | `https://so.toutiao.com/search?keyword=QUERY` | 字节生态 | 🏢 官方 |
| 微博热搜 | `https://s.weibo.com/weibo?q=QUERY` | 社交热点 | 👥 技术社区 |
| 央视新闻 | `https://news.cctv.com/search.shtml?q=QUERY` | 央媒权威 | 🏢 官方 |
| 人民日报 | `http://search.people.com.cn/cnpeople/search.do?keyword=QUERY` | 党媒权威 | 🏢 官方 |
| 澎湃新闻 | `https://www.thepaper.cn/search?keyword=QUERY` | 深度报道 | 📰 权威媒体 |
| 中国政府网 | `https://www.gov.cn/search/index.htm?keyword=QUERY` | 权威政务 | 🏢 官方 |

---

## 执行示例

```javascript
// 热点新闻（并行）
web_fetch(url="https://www.baidu.com/s?wd=AI热点&rtt=1&bsst=1")
web_fetch(url="https://so.toutiao.com/search?keyword=AI热点")

// 政务新闻
web_fetch(url="https://www.gov.cn/search/index.htm?keyword=新能源政策")
web_fetch(url="http://search.people.com.cn/cnpeople/search.do?keyword=新能源政策")

// 央媒新闻
web_fetch(url="https://news.cctv.com/search.shtml?q=科技新闻")

// 深度报道
web_fetch(url="https://www.thepaper.cn/search?keyword=社会热点")
```

---

## 并行策略

| 场景 | 并行组合 | 说明 |
|------|----------|------|
| 热点新闻 | 百度资讯 + 头条 | 多信源热点 |
| 财经新闻 | 东方财富 + 财新 | 资讯+深度 |
| 政务新闻 | 中国政府网 + 人民日报 | 权威+党媒 |

---

## 信源权重（v3.1.1更新）

```
🏢 权威政务媒体（政府网、人民日报、央视）  → 权重 1.0
🏢 官方平台（头条、抖音官方账号）          → 权重 0.95
📰 权威媒体（澎湃新闻、财新）              → 权重 0.9
👥 字节生态（头条、抖音）                  → 权重 0.8
👥 综合资讯（百度资讯）                    → 权重 0.7
👥 社交平台（微博）                        → 权重 0.6
```

---

## 采纳建议（v3.1.1新增）

| 来源类型 | 采纳建议 | 验证建议 |
|----------|----------|----------|
| 🏢 权威政务媒体 | ⭐⭐⭐ 强烈推荐 | 无需交叉验证 |
| 🏢 官方平台 | ⭐⭐⭐ 强烈推荐 | 无需交叉验证 |
| 📰 权威媒体 | ⭐⭐ 推荐 | 建议与官方来源交叉验证 |
| 👥 字节生态/综合资讯 | ⭐ 可选 | 需与官方来源交叉验证 |
| 👥 社交平台 | ⚠️ 谨慎采纳 | 强烈建议交叉验证 |
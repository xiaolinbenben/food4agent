---
domain: academic
keywords: [论文, 研究, 学术, 文献, 期刊, 博士, 硕士, 毕业, 专利, 标准, GB, ISO]
version: 4.2.0
---

# 学术领域搜索

## 快速路由

| 子类型 | 触发关键词 | P0引擎 | P1引擎 |
|--------|------------|--------|--------|
| 中文论文 | 论文、研究、学术、博士、硕士 | 知网 + 万方 | 维普 + 百度学术 |
| 英文论文 | paper、research、arxiv | ArXiv + Google Scholar | Semantic Scholar |
| 专利 | 专利、发明、实用新型 | 国家知识产权局 | Google Patents |
| 标准 | 标准、GB、ISO、规范 | 国家标准委 | ISO官网 |

---

## 引擎URL模板

| 引擎 | URL模板 | 说明 | 来源类型 |
|------|---------|------|----------|
| 知网CNKI | `https://www.cnki.net/search?q=QUERY` | 中文学术首选 | 🏢 官方 |
| 万方 | `https://s.wanfangdata.com.cn/paper?q=QUERY` | 中文学术资源 | 🏢 官方 |
| 维普 | `https://qikan.cqvip.com/Qikan/Search?kw=QUERY` | 中文期刊 | 🏢 官方 |
| 百度学术 | `https://xueshu.baidu.com/s?wd=QUERY` | 中英文学术聚合 | 👥 技术社区 |
| ArXiv | `http://export.arxiv.org/api/query?search_query=all:QUERY&max_results=5` | 英文前沿论文 | 🏢 官方 |
| PubMed | `https://pubmed.ncbi.nlm.nih.gov/?term=QUERY` | 医学文献 | 🏢 官方 |

---

## 执行示例

```javascript
// 中文学术论文
web_fetch(url="https://www.cnki.net/search?q=深度学习图像识别", maxChars=12000)

// 英文前沿论文
web_fetch(url="http://export.arxiv.org/api/query?search_query=all:LLM+reasoning&max_results=5")

// 医学文献
web_fetch(url="https://pubmed.ncbi.nlm.nih.gov/?term=machine+learning+diagnosis")

// 中国专利
web_fetch(url="https://pss-system.cponline.cnipa.gov.cn/conventionalSearch")
```

---

## 信源权重（v3.1.1更新）

```
🏢 官方学术平台（知网、万方、ArXiv、PubMed）  → 权重 1.0
🏢 官方专利平台（国家知识产权局）            → 权重 1.0
🏢 官方标准平台（国家标准委、ISO）           → 权重 1.0
🏢 国际学术平台（Google Scholar）            → 权重 0.9
👥 综合学术搜索（必应学术、百度学术）         → 权重 0.7
```

---

## 采纳建议（v3.1.1新增）

| 来源类型 | 采纳建议 | 验证建议 |
|----------|----------|----------|
| 🏢 官方学术平台 | ⭐⭐⭐ 强烈推荐 | 无需交叉验证 |
| 🏢 官方专利/标准平台 | ⭐⭐⭐ 强烈推荐 | 无需交叉验证 |
| 🏢 国际学术平台 | ⭐⭐ 推荐 | 建议与官方来源交叉验证 |
| 👥 综合学术搜索 | ⭐ 可选 | 需与官方来源交叉验证 |
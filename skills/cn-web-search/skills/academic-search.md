---
name: academic-search
description: 学术类搜索子技能 - 论文、专利、标准
trigger:
  keywords: [论文, 研究, 学术, 博士, 硕士, 参考文献, 专利, 标准, GB, ISO]
---

# 学术类搜索

## 查询类型识别

| 子类型 | 触发关键词 |
|--------|------------|
| 中文学术论文 | 论文、研究、学术、博士、硕士 |
| 英文学术论文 | paper、research、arxiv |
| 专利 | 专利、发明、实用新型 |
| 标准 | 标准、GB、ISO、规范 |

---

## 引擎路由表

### 中文学术论文

| 优先级 | 引擎 | URL模板 | 说明 |
|--------|------|---------|------|
| P0 | 知网 | `https://www.cnki.net/search?q=QUERY` | 中文学术首选 |
| P0 | 万方 | `https://s.wanfangdata.com.cn/paper?q=QUERY` | 中文学术资源 |
| P1 | 维普 | `https://qikan.cqvip.com/Qikan/Search?kw=QUERY` | 中文期刊 |
| P1 | 百度学术 | `https://xueshu.baidu.com/s?wd=QUERY` | 中英文学术聚合 |
| B | 必应学术 | `https://cn.bing.com/academic/search?q=QUERY` | 广泛搜索 |

### 英文学术论文

| 优先级 | 引擎 | URL模板 | 说明 |
|--------|------|---------|------|
| P0 | ArXiv | `http://export.arxiv.org/api/query?search_query=all:QUERY&max_results=5` | 前沿论文 |
| P0 | Google Scholar | `https://scholar.google.com/scholar?q=QUERY` | 学术搜索 |
| P1 | Semantic Scholar | `https://www.semanticscholar.org/search?q=QUERY` | AI学术 |
| B | 必应学术 | `https://cn.bing.com/academic/search?q=QUERY` | 广泛搜索 |

### 专利查询

| 优先级 | 引擎 | URL模板 | 说明 |
|--------|------|---------|------|
| P0 | 国家知识产权局 | `https://pss-system.cponline.cnipa.gov.cn/conventionalSearch` | 中国专利官方 |
| P1 | Google Patents | `https://patents.google.com/?q=QUERY` | 全球专利 |
| B | 必应中文 | `https://cn.bing.com/search?q=QUERY+专利` | 广泛搜索 |

### 标准查询

| 优先级 | 引擎 | URL模板 | 说明 |
|--------|------|---------|------|
| P0 | 国家标准委 | `https://std.samr.gov.cn/gb/search/gbDetailedInfo` | 中国标准官方 |
| P1 | ISO | `https://www.iso.org/search?keyword=QUERY` | 国际标准 |
| B | 必应中文 | `https://cn.bing.com/search?q=QUERY+标准` | 广泛搜索 |

---

## 使用示例

```javascript
// 中文学术论文
web_fetch(url="https://www.cnki.net/search?q=深度学习图像识别", maxChars=12000)

// 英文前沿论文
web_fetch(url="http://export.arxiv.org/api/query?search_query=all:LLM+reasoning&max_results=5", maxChars=8000)

// 中国专利
web_fetch(url="https://pss-system.cponline.cnipa.gov.cn/conventionalSearch", maxChars=10000)
```

---

## 信源权重

```
官方学术平台（知网、万方、ArXiv） → 权重 1.0
国际学术平台（Google Scholar）   → 权重 0.9
综合学术搜索（必应学术）         → 权重 0.7
```
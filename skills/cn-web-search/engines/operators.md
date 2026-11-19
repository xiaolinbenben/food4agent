---
name: operators
description: 高级搜索操作符指南 - 精确搜索、站内搜索、时间筛选集成
version: 4.2.0
---

# 高级搜索操作符 v4.2.0

## 时间筛选集成指令 🆕

> **规则**: 根据查询类型自动附加时间筛选参数

| 查询类型 | 时间筛选 | 百度参数 | Brave参数 | Google参数 |
|----------|----------|----------|-----------|------------|
| 新闻热点 | 过去一周 | `&rtt=1&bsst=1` | `&tf=pw` | `&tbs=qdr:w` |
| 技术版本 | 过去一年 | - | `&tf=py` | `&tbs=qdr:y` |
| 政策法规 | 过去一月 | - | `&tf=pm` | `&tbs=qdr:m` |
| 学术论文 | 不限制 | - | - | - |
| 百科知识 | 不限制 | - | - | - |
| 实时查询 | 过去24小时 | `&rtt=1&bsst=1` | - | `&tbs=qdr:d` |

### 使用规则

```
新闻查询: 自动附加时间参数
  → 百度: &rtt=1&bsst=1 (按时间排序)
  → Brave: &tf=pw (过去一周)
  → Google: tbs=qdr:w (一周)

技术版本查询: 附加近一年筛选
  → Google: tbs=qdr:y
  → Brave: &tf=py

历史/学术查询: 不附加时间参数
```

---

## Google操作符（需代理）

### 基础操作符

| 操作符 | 功能 | 示例 |
|--------|------|------|
| `""` | 精确匹配 | `"machine learning"` |
| `-` | 排除关键词 | `python -snake` |
| `OR` | 或运算 | `machine learning OR deep learning` |
| `*` | 通配符 | `machine * algorithms` |
| `..` | 数字范围 | `laptop $500..$1000` |

### 站点与文件搜索

| 操作符 | 功能 | 示例 |
|--------|------|------|
| `site:` | 站内搜索 | `site:github.com python projects` |
| `filetype:` | 文件类型 | `filetype:pdf annual report` |
| `inurl:` | URL包含 | `inurl:login admin` |
| `intitle:` | 标题包含 | `intitle:"index of" mp3` |

### 时间筛选

| 参数 | 含义 | 示例 |
|------|------|------|
| `tbs=qdr:h` | 过去1小时 | `&tbs=qdr:h` |
| `tbs=qdr:d` | 过去24小时 | `&tbs=qdr:d` |
| `tbs=qdr:w` | 过去1周 | `&tbs=qdr:w` |
| `tbs=qdr:m` | 过去1月 | `&tbs=qdr:m` |
| `tbs=qdr:y` | 过去1年 | `&tbs=qdr:y` |

---

## 百度搜索参数 🆕

| 参数 | 功能 | 示例 |
|------|------|------|
| `&rtt=1` | 资讯排序 | `&rtt=1` |
| `&bsst=1` | 按时间排序 | `&bsst=1` |
| `&gpc=stf` | 时间范围 | `&gpc=stf=1719792000,1720483200` |

---

## DuckDuckGo Bangs（快捷跳转）

| Bang | 目标 | 示例 |
|------|------|------|
| `!g` | Google | `!g python tutorial` |
| `!gh` | GitHub | `!gh tensorflow` |
| `!so` | Stack Overflow | `!so javascript error` |
| `!npm` | npmjs.com | `!npm express` |
| `!pypi` | PyPI | `!pypi requests` |
| `!mdn` | MDN Web Docs | `!mdn fetch api` |
| `!w` | Wikipedia | `!w machine learning` |

---

## Brave Search参数

| 参数 | 功能 | 示例 |
|------|------|------|
| `tf=pw` | 本周 | `&tf=pw` |
| `tf=pm` | 本月 | `&tf=pm` |
| `tf=py` | 本年 | `&tf=py` |
| `source=news` | 新闻搜索 | `&source=news` |

---

## 否定排除操作符 🆕

| 操作符 | 功能 | 示例 |
|--------|------|------|
| `-site:` | 排除指定站点 | `-site:csdn.net React教程` |
| `-[关键词]` | 排除关键词 | `React -广告 -推广` |

### 使用规则

```
IF 查询含否定意图（"除了CSDN"）:
  → 在搜索URL中附加 -site:csdn.net
  → 示例: baidu.com/s?wd=React教程+-site:csdn.net
```

---

## 使用示例

```
新闻查询（自动时间筛选）:
web_fetch(url="https://www.baidu.com/s?wd=英伟达新闻&rtt=1&bsst=1")

排除指定站点:
web_fetch(url="https://www.baidu.com/s?wd=React教程+-site:csdn.net")

站内搜索:
web_fetch(url="https://www.google.com/search?q=site:github.com+python+ml")

时间筛选:
web_fetch(url="https://www.google.com/search?q=news&tbs=qdr:w")
```

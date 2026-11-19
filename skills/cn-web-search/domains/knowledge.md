---
domain: knowledge
keywords: [是什么, 定义, 百科, 介绍, 意思, 如何理解, 计算, 换算, 汇率, 公式]
version: 4.2.0
---

# 知识百科搜索

## 快速路由

| 子类型 | 触发关键词 | P0引擎 | P1引擎 |
|--------|------------|--------|--------|
| 百科知识 | 是什么、定义、百科、介绍 | 百度百科 + Wikipedia | 知乎百科 |
| 知识计算 | 计算、换算、汇率、公式 | WolframAlpha | DDG Instant |

---

## 引擎URL模板

| 引擎 | URL模板 | 说明 |
|------|---------|------|
| 百度百科 | `https://baike.baidu.com/item/QUERY` | 中文本土百科 |
| Wikipedia中文 | `https://zh.wikipedia.org/w/index.php?search=QUERY` | 中文百科首选 |
| Wikipedia英文 | `https://en.wikipedia.org/w/index.php?search=QUERY` | 英文百科标杆 |
| 知乎百科 | `https://www.zhihu.com/search?q=QUERY&type=knowledge` | 知识问答聚合 |
| WolframAlpha | `https://www.wolframalpha.com/input?i=QUERY` | 计算公式数据 |
| DDG Instant | `https://api.duckduckgo.com/?q=QUERY&format=json` | JSON即时答案 |

---

## 执行示例

```javascript
// 百科查询
web_fetch(url="https://baike.baidu.com/item/量子计算", maxChars=8000)
web_fetch(url="https://zh.wikipedia.org/w/index.php?search=机器学习")

// 知识计算
web_fetch(url="https://www.wolframalpha.com/input?i=1+USD+to+CNY")

// 即时答案
web_fetch(url="https://api.duckduckgo.com/?q=Python+programming&format=json&no_html=1")
```

---

## 信源权重

```
Wikipedia                        → 权重 0.9
百度百科                         → 权重 0.85
WolframAlpha（计算类）           → 权重 0.9
知乎百科                         → 权重 0.7
DDG Instant Answer               → 权重 0.6
```
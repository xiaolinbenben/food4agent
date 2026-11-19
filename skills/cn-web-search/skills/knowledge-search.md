---
name: knowledge-search
description: 知识百科类搜索子技能 - 百科、定义、即时答案、知识计算
trigger:
  keywords: [是什么, 定义, 百科, 解释, 概念, 计算, 换算, 汇率, 股价, 公式, 积分, 方程, 单位转换]
---

# 知识百科类搜索

## 查询类型识别

| 子类型 | 触发关键词 |
|--------|------------|
| 百科定义 | 是什么、定义、百科、解释、概念 |
| 即时答案 | 计算、换算、时间、天气、事实 |
| 知识计算 | 积分、方程、汇率、股价、公式、单位转换、数学 |

---

## 引擎路由表

### 百科定义

| 优先级 | 引擎 | URL模板 | 说明 |
|--------|------|---------|------|
| P0 | Wikipedia中文 | `https://zh.wikipedia.org/w/index.php?search=QUERY&title=Special:Search` | 中文百科首选 |
| P0 | Wikipedia英文 | `https://en.wikipedia.org/w/index.php?search=QUERY&title=Special:Search` | 英文百科 |
| P1 | 百度百科 | `https://baike.baidu.com/item/QUERY` | 中文百科 |
| B | 必应中文 | `https://cn.bing.com/search?q=QUERY` | 广泛搜索 |

### 即时答案

| 优先级 | 引擎 | URL模板 | 说明 |
|--------|------|---------|------|
| P0 | DDG Instant Answer | `https://api.duckduckgo.com/?q=QUERY&format=json&no_html=1` | JSON即时答案 |
| P1 | Wolfram Alpha | `https://www.wolframalpha.com/input?i=QUERY` | 计算、公式 |
| B | Wikipedia中文 | `https://zh.wikipedia.org/w/index.php?search=QUERY` | 知识查询 |

### WolframAlpha 知识计算（⚠️ 可能受限）

> **适用场景**: 数学计算、单位换算、货币转换、科学数据查询

| 数据类型 | 查询示例 | 说明 |
|----------|---------|------|
| 数学计算 | `integrate x^2 dx` | 微积分、方程求解 |
| 单位换算 | `100 miles to km` | 长度、重量、温度 |
| 货币转换 | `100 USD to CNY` | 实时汇率 |
| 股票数据 | `AAPL stock` | 实时股价 |
| 天气查询 | `weather in Beijing` | 天气预报 |
| 化学元素 | `properties of gold` | 元素属性 |
| 营养成分 | `nutrition of apple` | 食物营养 |

👉 **WolframAlpha 深度指南**: [special-engines.md](../references/special-engines.md)

---

## 使用示例

### 百科定义

```javascript
// 中文百科
web_fetch(url="https://zh.wikipedia.org/w/index.php?search=量子计算&title=Special:Search", maxChars=8000)

// 百度百科
web_fetch(url="https://baike.baidu.com/item/人工智能", maxChars=8000)

// 英文百科
web_fetch(url="https://en.wikipedia.org/w/index.php?search=machine+learning", maxChars=8000)
```

### 即时答案

```javascript
// DDG 即时答案（JSON格式）
web_fetch(url="https://api.duckduckgo.com/?q=Python&format=json&no_html=1", maxChars=5000)
```

### WolframAlpha 知识计算

```javascript
// 数学计算 - 解方程
web_fetch(url="https://www.wolframalpha.com/input?i=solve+x%5E2-5x%2B6%3D0", maxChars=5000)

// 数学计算 - 积分
web_fetch(url="https://www.wolframalpha.com/input?i=integrate+sin%28x%29+from+0+to+pi", maxChars=5000)

// 货币转换（实时汇率）
web_fetch(url="https://www.wolframalpha.com/input?i=100+USD+to+CNY", maxChars=5000)

// 单位换算
web_fetch(url="https://www.wolframalpha.com/input?i=100+miles+to+km", maxChars=5000)

// 股票数据
web_fetch(url="https://www.wolframalpha.com/input?i=AAPL+stock", maxChars=5000)

// 化学计算
web_fetch(url="https://www.wolframalpha.com/input?i=molar+mass+of+H2SO4", maxChars=5000)

// 天气查询
web_fetch(url="https://www.wolframalpha.com/input?i=weather+in+Beijing", maxChars=5000)

// 营养信息
web_fetch(url="https://www.wolframalpha.com/input?i=calories+in+banana", maxChars=5000)
```

---

## 信源权重

```
Wikipedia                       → 权重 0.9
Wolfram Alpha（计算类）          → 权重 0.95  // 计算类查询最高权重
Wolfram Alpha（数据类）          → 权重 0.85
DDG Instant Answer              → 权重 0.8
百度百科                         → 权重 0.7
```
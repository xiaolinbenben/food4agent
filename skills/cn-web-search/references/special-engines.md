# 国际特殊搜索引擎指南

> **可用性标注**: ❌ 需代理 | ⚠️ 可能受限
> **适用场景**: 特殊需求下的国际搜索、隐私搜索、知识计算

---

## Google 搜索（❌ 需代理）

### 基本信息

| 属性 | 值 |
|------|-----|
| URL模板 | `https://www.google.com/search?q=QUERY` |
| 可用性 | ❌ 需代理 |
| 优先级 | 特殊需求 |
| 适用场景 | 英文精确搜索、学术研究、技术文档 |

### 核心优势

1. **全球最大索引**: 覆盖最广泛的网页内容
2. **高级操作符**: 支持 site/filetype/inurl/intitle 等丰富操作符
3. **学术搜索**: Google Scholar 学术论文专用
4. **多类型搜索**: 图片/新闻/视频/购物/图书

### 使用场景

| 场景 | 操作示例 |
|------|----------|
| 英文技术文档 | `python async tutorial` |
| 站内搜索 | `site:github.com react hooks` |
| 文件类型搜索 | `filetype:pdf machine learning` |
| 学术论文 | Google Scholar: `deep learning optimization` |

### 高级搜索示例

```javascript
// 1. 站内搜索 GitHub
web_fetch({"url": "https://www.google.com/search?q=site:github.com+python+machine+learning"})

// 2. 时间筛选（过去一周）
web_fetch({"url": "https://www.google.com/search?q=AI+news&tbs=qdr:w"})

// 3. 文件类型搜索
web_fetch({"url": "https://www.google.com/search?q=react+tutorial+filetype:pdf"})

// 4. 排除特定站点
web_fetch({"url": "https://www.google.com/search?q=python+-wikipedia"})

// 5. 学术搜索
web_fetch({"url": "https://scholar.google.com/scholar?q=transformer+architecture"})
```

---

## Google HK 搜索（❌ 需代理）

### 基本信息

| 属性 | 值 |
|------|-----|
| URL模板 | `https://www.google.com.hk/search?q=QUERY` |
| 可用性 | ❌ 需代理 |
| 优先级 | 特殊需求 |
| 适用场景 | 中文内容 + Google 索引 |

### 特点

- 中文界面友好
- 结合 Google 全球索引与中文优化
- 适合中文内容的国际视角搜索

---

## Ecosia 环保搜索（⚠️ 可能受限）

### 基本信息

| 属性 | 值 |
|------|-----|
| URL模板 | `https://www.ecosia.org/search?q=QUERY` |
| 可用性 | ⚠️ 可能受限 |
| 优先级 | P3 |
| 特点 | 搜索植树、环保公益 |

### 核心价值

- **环保公益**: 每次搜索贡献植树
- **隐私保护**: 不追踪用户搜索
- ** Bing 索引**: 基于 Bing 搜索结果

### 使用示例

```javascript
// Ecosia 搜索
web_fetch({"url": "https://www.ecosia.org/search?q=sustainable+living"})
```

---

## 隐私搜索引擎对比

### 引擎隐私级别对比表

| 引擎 | 追踪级别 | 数据保留 | 加密 | 推荐场景 |
|------|---------|---------|------|---------|
| **DuckDuckGo** | 无追踪 | 无保留 | 是 | 日常隐私搜索 |
| **Startpage** | 无追踪 | 无保留 | 是 | 需要Google结果但保护隐私 |
| **Brave** | 无追踪 | 无保留 | 是 | 独立索引，无偏见 |
| **Qwant** | 无追踪 | 无保留 | 是 | 欧盟合规要求 |
| **Ecosia** | 低追踪 | 最短保留 | 是 | 环保公益搜索 |

### DuckDuckGo（⚠️ 可能受限）

| 属性 | 值 |
|------|-----|
| URL模板 | `https://duckduckgo.com/html/?q=QUERY` |
| Lite版 | `https://lite.duckduckgo.com/lite/?q=QUERY` |
| 可用性 | ⚠️ 可能受限 |
| 优先级 | P1（英文综合） |

### Startpage（⚠️ 可能受限）

| 属性 | 值 |
|------|-----|
| URL模板 | `https://www.startpage.com/sp/search?query=QUERY` |
| 可用性 | ⚠️ 可能受限 |
| 优先级 | P2（英文综合） |

**特色功能**:
- **代理浏览**: 匿名访问搜索结果
- **无追踪**: 不记录搜索历史
- **EU服务器**: 受欧盟隐私法保护
- **Google结果**: 提供 Google 搜索结果 + 隐私保护

### Brave Search（⚠️ 可能受限）

| 属性 | 值 |
|------|-----|
| URL模板 | `https://search.brave.com/search?q=QUERY` |
| 可用性 | ⚠️ 可能受限 |
| 优先级 | P1（英文综合） |

**特色功能**:
- **独立索引**: 不依赖 Google/Bing
- **Goggles**: 自定义搜索规则
- **Discussions**: 论坛讨论搜索

### Qwant（❌ 需代理）

| 属性 | 值 |
|------|-----|
| URL模板 | `https://www.qwant.com/?q=QUERY` |
| 可用性 | ❌ 需代理 |
| 优先级 | P2（英文综合） |

**特点**: 欧盟 GDPR 合规，法国搜索引擎

---

## WolframAlpha 知识计算引擎（⚠️ 可能受限）

### 基本信息

| 属性 | 值 |
|------|-----|
| URL模板 | `https://www.wolframalpha.com/input?i=QUERY` |
| 可用性 | ⚠️ 可能受限 |
| 优先级 | P1（知识百科） |
| 特点 | 结构化知识计算 |

### 数据类型支持（13 类）

| 类型 | 查询示例 | 说明 |
|------|---------|------|
| **数学计算** | `integrate x^2 dx` | 微积分、方程求解 |
| **单位换算** | `100 miles to km` | 长度、重量、温度等 |
| **货币转换** | `100 USD to CNY` | 实时汇率 |
| **股票数据** | `AAPL stock` | 实时股价信息 |
| **天气查询** | `weather in Beijing` | 天气预报 |
| **人口数据** | `population of China` | 统计数据 |
| **化学元素** | `properties of gold` | 元素属性查询 |
| **营养成分** | `nutrition of apple` | 食物营养信息 |
| **日期计算** | `days between Jan 1 2020 and Dec 31 2024` | 日期间隔计算 |
| **时区转换** | `10am Beijing to New York` | 时区转换 |
| **IP地址** | `8.8.8.8` | IP信息查询 |
| **条形码** | `scan barcode 123456789` | 条码信息 |
| **飞机航班** | `flight AA123` | 航班信息 |

### WolframAlpha 深度示例

```javascript
// 1. 数学计算 - 积分
web_fetch({"url": "https://www.wolframalpha.com/input?i=integrate+sin%28x%29+from+0+to+pi"})

// 2. 数学计算 - 解方程
web_fetch({"url": "https://www.wolframalpha.com/input?i=solve+x%5E2-5x%2B6%3D0"})

// 3. 货币实时汇率
web_fetch({"url": "https://www.wolframalpha.com/input?i=100+USD+to+CNY"})

// 4. 股票实时数据
web_fetch({"url": "https://www.wolframalpha.com/input?i=Apple+stock+price"})

// 5. 天气查询
web_fetch({"url": "https://www.wolframalpha.com/input?i=weather+in+Shanghai+tomorrow"})

// 6. 国家统计对比
web_fetch({"url": "https://www.wolframalpha.com/input?i=GDP+of+China+vs+USA"})

// 7. 化学计算
web_fetch({"url": "https://www.wolframalpha.com/input?i=molar+mass+of+H2SO4"})

// 8. 物理常数
web_fetch({"url": "https://www.wolframalpha.com/input?i=speed+of+light"})

// 9. 营养信息
web_fetch({"url": "https://www.wolframalpha.com/input?i=calories+in+banana"})

// 10. 历史日期
web_fetch({"url": "https://www.wolframalpha.com/input?i=events+on+July+20+1969"})
```

---

## 隐私搜索最佳实践

### 搜索引擎选择策略

| 需求场景 | 推荐引擎 | 原因 |
|----------|---------|------|
| **日常隐私搜索** | DuckDuckGo | 无追踪，功能完整 |
| **需要Google结果** | Startpage | Google索引 + 隐私保护 |
| **独立无偏见结果** | Brave Search | 独立索引，无过滤 |
| **欧盟合规要求** | Qwant | GDPR合规 |
| **环保公益** | Ecosia | 搜索植树 |

### 隐私保护建议

1. **日常使用**: DuckDuckGo 或 Brave
2. **需要Google结果但保护隐私**: Startpage
3. **学术研究**: Google Scholar（学术用途追踪较少）
4. **敏感查询**: 使用 Tor 浏览器 + DuckDuckGo onion 服务
5. **跨设备同步**: 避免登录搜索引擎账户

---

## 使用建议

### 中国境内用户

| 场景 | 建议 |
|------|------|
| **日常中文搜索** | 使用 cn-search-hub 国内引擎（百度/头条/CSDN等） |
| **英文技术搜索** | Brave/DDG Lite（可能可用）或必应英文 |
| **隐私搜索** | DuckDuckGo Lite（轻量版更易访问） |
| **知识计算** | WolframAlpha（可能可用）或百度百科 |
| **特殊需求（Google）** | 需代理环境，参考 [advanced-operators.md](./advanced-operators.md) |

### 有代理环境用户

| 场景 | 建议 |
|------|------|
| **英文精确搜索** | Google + 高级操作符 |
| **学术研究** | Google Scholar |
| **隐私敏感** | DuckDuckGo / Startpage |
| **知识计算** | WolframAlpha |

---

## 相关参考

- [高级搜索操作符指南](./advanced-operators.md) - Google/DDG 操作符详解
- [完整引擎列表](./engine-list.md) - 109 个搜索引擎总览
- [知识百科搜索子技能](../skills/knowledge-search.md) - WolframAlpha 路由说明
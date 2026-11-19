# 高级搜索操作符指南

> **适用场景**: 需要精确搜索、站内搜索、文件类型搜索、时间筛选等高级需求
> **网络要求**: Google 操作符在中国境内需代理，DDG Bangs 部分可用

---

## Google 高级操作符

### 基础操作符

| 操作符 | 功能 | 示例 | URL |
|--------|------|------|-----|
| `""` | 精确匹配 | `"machine learning"` | `https://www.google.com/search?q=%22machine+learning%22` |
| `-` | 排除关键词 | `python -snake` | `https://www.google.com/search?q=python+-snake` |
| `OR` | 或运算 | `machine learning OR deep learning` | `https://www.google.com/search?q=machine+learning+OR+deep+learning` |
| `*` | 通配符 | `machine * algorithms` | `https://www.google.com/search?q=machine+*+algorithms` |
| `()` | 分组 | `(apple OR microsoft) phones` | `https://www.google.com/search?q=(apple+OR+microsoft)+phones` |
| `..` | 数字范围 | `laptop $500..$1000` | `https://www.google.com/search?q=laptop+%24500..%241000` |

### 站点与文件搜索

| 操作符 | 功能 | 示例 |
|--------|------|------|
| `site:` | 站内搜索 | `site:github.com python projects` |
| `filetype:` | 文件类型 | `filetype:pdf annual report` |
| `inurl:` | URL包含 | `inurl:login admin` |
| `intitle:` | 标题包含 | `intitle:"index of" mp3` |
| `intext:` | 正文包含 | `intext:password filetype:txt` |
| `cache:` | 查看缓存 | `cache:example.com` |
| `related:` | 相关网站 | `related:github.com` |
| `info:` | 网站信息 | `info:example.com` |

### 时间筛选参数

| 参数 | 含义 | URL示例 |
|------|------|---------|
| `tbs=qdr:h` | 过去1小时 | `https://www.google.com/search?q=news&tbs=qdr:h` |
| `tbs=qdr:d` | 过去24小时 | `https://www.google.com/search?q=news&tbs=qdr:d` |
| `tbs=qdr:w` | 过去1周 | `https://www.google.com/search?q=news&tbs=qdr:w` |
| `tbs=qdr:m` | 过去1月 | `https://www.google.com/search?q=news&tbs=qdr:m` |
| `tbs=qdr:y` | 过去1年 | `https://www.google.com/search?q=news&tbs=qdr:y` |
| `tbs=cdr:1,cd_min:1/1/2024,cd_max:12/31/2024` | 自定义日期范围 | 2024年全年 |

### 语言和地区筛选

| 参数 | 功能 | 示例 |
|------|------|------|
| `hl=en` | 界面语言 | `https://www.google.com/search?q=test&hl=en` |
| `lr=lang_zh-CN` | 搜索结果语言 | `https://www.google.com/search?q=test&lr=lang_zh-CN` |
| `cr=countryCN` | 国家/地区 | `https://www.google.com/search?q=test&cr=countryCN` |
| `gl=us` | 地理位置 | `https://www.google.com/search?q=test&gl=us` |

### 特殊搜索类型

| 类型 | URL参数 | 说明 |
|------|---------|------|
| 图片搜索 | `tbm=isch` | `https://www.google.com/search?q=QUERY&tbm=isch` |
| 新闻搜索 | `tbm=nws` | `https://www.google.com/search?q=QUERY&tbm=nws` |
| 视频搜索 | `tbm=vid` | `https://www.google.com/search?q=QUERY&tbm=vid` |
| 地图搜索 | `tbm=map` | `https://www.google.com/search?q=QUERY&tbm=map` |
| 购物搜索 | `tbm=shop` | `https://www.google.com/search?q=QUERY&tbm=shop` |
| 图书搜索 | `tbm=bks` | `https://www.google.com/search?q=QUERY&tbm=bks` |
| 学术搜索 | Google Scholar | `https://scholar.google.com/scholar?q=QUERY` |

---

## DuckDuckGo Bangs 快捷跳转

> **Bangs 是 DuckDuckGo 的特色功能，使用 `!缩写` 直接跳转到指定网站搜索**

### 搜索引擎类

| Bang | 目标 | 示例 |
|------|------|------|
| `!g` | Google | `!g python tutorial` |
| `!b` | Bing | `!b weather` |
| `!y` | Yahoo | `!y finance` |
| `!sp` | Startpage | `!sp privacy` |
| `!brave` | Brave Search | `!brave tech` |

### 编程开发类

| Bang | 目标 | 示例 |
|------|------|------|
| `!gh` | GitHub | `!gh tensorflow` |
| `!so` | Stack Overflow | `!so javascript error` |
| `!npm` | npmjs.com | `!npm express` |
| `!pypi` | PyPI | `!pypi requests` |
| `!mdn` | MDN Web Docs | `!mdn fetch api` |
| `!docs` | DevDocs | `!docs python` |
| `!docker` | Docker Hub | `!docker nginx` |

### 知识百科类

| Bang | 目标 | 示例 |
|------|------|------|
| `!w` | Wikipedia | `!w machine learning` |
| `!wen` | Wikipedia英文 | `!wen artificial intelligence` |
| `!wt` | Wiktionary | `!wt serendipity` |
| `!imdb` | IMDb | `!imdb inception` |

### 购物价格类

| Bang | 目标 | 示例 |
|------|------|------|
| `!a` | Amazon | `!a wireless headphones` |
| `!e` | eBay | `!e vintage watch` |
| `!ali` | AliExpress | `!ali phone case` |

### 地图视频类

| Bang | 目标 | 示例 |
|------|------|------|
| `!m` | Google Maps | `!m Beijing` |
| `!maps` | OpenStreetMap | `!maps Paris` |
| `!yt` | YouTube | `!yt python tutorial` |

### DuckDuckGo 特色工具

| 功能 | 语法 | 示例 |
|------|------|------|
| 密码生成 | `password` | `https://duckduckgo.com/?q=password+20` |
| 颜色转换 | `color` | `https://duckduckgo.com/?q=+%23FF5733` |
| 短链接 | `shorten` | `https://duckduckgo.com/?q=shorten+example.com` |
| 二维码 | `qr` | `https://duckduckgo.com/?q=qr+hello+world` |
| 生成UUID | `uuid` | `https://duckduckgo.com/?q=uuid` |
| Base64编解码 | `base64` | `https://duckduckgo.com/?q=base64+hello` |

---

## Brave Search 参数

| 参数 | 功能 | 示例 |
|------|------|------|
| `tf=pw` | 本周 | `https://search.brave.com/search?q=news&tf=pw` |
| `tf=pm` | 本月 | `https://search.brave.com/search?q=tech&tf=pm` |
| `tf=py` | 本年 | `https://search.brave.com/search?q=AI&tf=py` |
| `safesearch=strict` | 严格安全 | `https://search.brave.com/search?q=test&safesearch=strict` |
| `source=news` | 新闻搜索 | `https://search.brave.com/search?q=tech&source=news` |
| `source=images` | 图片搜索 | `https://search.brave.com/search?q=cat&source=images` |
| `source=videos` | 视频搜索 | `https://search.brave.com/search?q=music&source=videos` |

---

## 使用示例集

### 技术开发搜索

```javascript
// 1. 搜索GitHub上的Python机器学习项目
web_fetch({"url": "https://www.google.com/search?q=site:github.com+python+machine+learning"})

// 2. 使用 Bangs 快速跳转 Stack Overflow
web_fetch({"url": "https://duckduckgo.com/html/?q=!so+python+list+comprehension"})

// 3. 搜索 GitHub 代码
web_fetch({"url": "https://duckduckgo.com/html/?q=!gh+react+performance"})

// 4. 搜索 MDN 文档
web_fetch({"url": "https://duckduckgo.com/html/?q=!mdn+javascript+async+await"})
```

### 学术研究搜索

```javascript
// 5. Google Scholar 论文
web_fetch({"url": "https://scholar.google.com/scholar?q=deep+learning+optimization"})

// 6. 搜索PDF论文
web_fetch({"url": "https://www.google.com/search?q=machine+learning+tutorial+filetype:pdf"})

// 7. arXiv 论文（通过 DDG）
web_fetch({"url": "https://duckduckgo.com/html/?q=site:arxiv.org+abs+quantum"})
```

### 新闻时事搜索

```javascript
// 8. Google 最新新闻（过去1小时）
web_fetch({"url": "https://www.google.com/search?q=breaking+news&tbs=qdr:h&tbm=nws"})

// 9. Brave 本周科技新闻
web_fetch({"url": "https://search.brave.com/search?q=technology&tf=pw&source=news"})

// 10. DuckDuckGo 新闻
web_fetch({"url": "https://duckduckgo.com/html/?q=world+news&ia=news"})
```

### 隐私保护搜索

```javascript
// 11. DuckDuckGo 隐私搜索
web_fetch({"url": "https://duckduckgo.com/html/?q=privacy+tools"})

// 12. Startpage 匿名搜索
web_fetch({"url": "https://www.startpage.com/sp/search?query=secure+messaging"})

// 13. Brave 无追踪搜索
web_fetch({"url": "https://search.brave.com/search?q=encryption+software"})
```

### 高级组合搜索

```javascript
// 14. 多条件精确搜索
web_fetch({"url": "https://www.google.com/search?q=%22machine+learning%22+site:github.com+filetype:pdf+2024"})

// 15. 排除特定站点
web_fetch({"url": "https://www.google.com/search?q=python+tutorial+-wikipedia+-w3schools"})

// 16. 价格范围搜索
web_fetch({"url": "https://www.google.com/search?q=laptop+%24800..%241200+best+review"})

// 17. 使用 Bangs 跳转 Google 站内搜索
web_fetch({"url": "https://duckduckgo.com/html/?q=!g+site:medium.com+python"})
```

---

## 快捷函数模板

### URL 编码

```javascript
// URL编码关键词
function encodeKeyword(keyword) {
  return encodeURIComponent(keyword);
}
```

### 批量搜索 URL 生成

```javascript
// 多引擎批量搜索
function generateSearchUrls(keyword) {
  const encoded = encodeURIComponent(keyword);
  return {
    google: `https://www.google.com/search?q=${encoded}`,
    duckduckgo: `https://duckduckgo.com/html/?q=${encoded}`,
    brave: `https://search.brave.com/search?q=${encoded}`,
    startpage: `https://www.startpage.com/sp/search?query=${encoded}`,
    bing_intl: `https://cn.bing.com/search?q=${encoded}&ensearch=1`
  };
}
```

### 时间筛选快捷生成

```javascript
// Google时间筛选
function googleTimeSearch(keyword, period) {
  const periods = {
    hour: 'qdr:h',
    day: 'qdr:d',
    week: 'qdr:w',
    month: 'qdr:m',
    year: 'qdr:y'
  };
  return `https://www.google.com/search?q=${encodeURIComponent(keyword)}&tbs=${periods[period]}`;
}
```

---

## 相关参考

- [特殊搜索引擎指南](./special-engines.md) - Google/WolframAlpha/隐私搜索详解
- [完整引擎列表](./engine-list.md) - 109 个搜索引擎总览
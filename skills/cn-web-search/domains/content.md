---
domain: content
keywords: [视频, B站, 抖音, 公众号, 微博, 知乎, 小红书, 西瓜视频, 文章]
version: 4.2.0
---

# 内容平台搜索

## 快速路由

| 子类型 | 触发关键词 | P0引擎 | P1引擎 |
|--------|------------|--------|--------|
| 公众号文章 | 公众号、微信文章 | 搜狗微信 | 必应公众号 |
| 视频内容 | 视频、B站、抖音 | B站 + 抖音 | 西瓜视频 |
| 社交内容 | 知乎、微博、小红书 | 知乎 + 微博 | 小红书 |

---

## 引擎URL模板

| 引擎 | URL模板 | 说明 |
|------|---------|------|
| 搜狗微信 | `https://weixin.sogou.com/weixin?type=2&query=QUERY` | 公众号文章 |
| 必应公众号 | `https://cn.bing.com/search?q=site:mp.weixin.qq.com+QUERY` | 公众号索引 |
| B站 | `https://search.bilibili.com/all?keyword=QUERY` | 视频平台知识 |
| 抖音搜索 | `https://www.douyin.com/search/QUERY` | 短视频搜索 |
| 抖音热榜 | `https://www.douyin.com/hot` | 抖音热榜热点 |
| 知乎 | `https://www.zhihu.com/search?q=QUERY&type=content` | 深度讨论问答 |
| 微博 | `https://s.weibo.com/weibo?q=QUERY` | 实时动态热搜 |
| 小红书 | `https://www.xiaohongshu.com/search_result?keyword=QUERY` | 种草测评攻略 |
| 西瓜视频 | `https://www.ixigua.com/search/QUERY` | 长视频平台 |

---

## 执行示例

```javascript
// 公众号文章
web_fetch(url="https://weixin.sogou.com/weixin?type=2&query=AI技术")

// B站视频
web_fetch(url="https://search.bilibili.com/all?keyword=Python教程")

// 抖音热榜
web_fetch(url="https://www.douyin.com/hot")

// 知乎问答
web_fetch(url="https://www.zhihu.com/search?q=职业规划&type=content")

// 微博热搜
web_fetch(url="https://s.weibo.com/weibo?q=今日热点")

// 小红书种草
web_fetch(url="https://www.xiaohongshu.com/search_result?keyword=护肤推荐")
```

---

## 并行策略

| 场景 | 并行组合 | 说明 |
|------|----------|------|
| 公众号文章 | 搜狗微信 + 必应公众号 | 多索引覆盖 |
| 视频内容 | B站 + 抖音 | 短视频+长视频 |
| 社交热点 | 微博 + 知乎 | 实时+深度 |

---

## 信源权重

```
公众号文章（权威账号）            → 权重 0.85
B站（知识类UP主）                → 权重 0.75
知乎（专业回答）                  → 权重 0.7
微博（官方账号）                  → 权重 0.65
小红书（真实分享）                → 权重 0.6
抖音（娱乐内容）                  → 权重 0.5
```
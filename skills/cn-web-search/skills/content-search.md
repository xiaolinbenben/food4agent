---
name: content-search
description: 内容平台类搜索子技能 - 公众号、视频、社交媒体
trigger:
  keywords: [公众号, 微信, 自媒体, 视频, 教程, 直播, 短视频, 知乎, 小红书]
---

# 内容平台类搜索

## 查询类型识别

| 子类型 | 触发关键词 |
|--------|------------|
| 公众号/自媒体 | 公众号、微信、自媒体 |
| 视频/短视频 | 视频、教程、直播、短视频 |
| 社交媒体 | 讨论、观点、分享、推荐 |

---

## 引擎路由表

### 公众号/自媒体

| 优先级 | 引擎 | URL模板 | 说明 |
|--------|------|---------|------|
| P0 | 搜狗微信 | `https://weixin.sogou.com/weixin?type=2&query=QUERY&page=1` | 公众号文章 |
| P1 | 必应公众号 | `https://cn.bing.com/search?q=site:mp.weixin.qq.com+QUERY` | 公众号索引 |
| B | 百度 | `https://www.baidu.com/s?wd=QUERY` | 广泛搜索 |

### 视频/短视频

| 优先级 | 引擎 | URL模板 | 说明 |
|--------|------|---------|------|
| P0 | 抖音搜索 | `https://www.douyin.com/search/QUERY` | 字节生态 |
| P0 | 抖音热榜 | `https://www.douyin.com/hot` | 抖音热榜 |
| P0 | B站 | `https://search.bilibili.com/all?keyword=QUERY` | 视频/教程 |
| P1 | 西瓜视频 | `https://www.ixigua.com/search/QUERY` | 字节生态 |
| B | 百度视频 | `https://www.baidu.com/sf/vsearch?wd=QUERY` | 广泛搜索 |

### 社交媒体

| 优先级 | 引擎 | URL模板 | 说明 |
|--------|------|---------|------|
| P0 | 知乎 | `https://www.zhihu.com/search?q=QUERY&type=content` | 深度讨论 |
| P0 | 小红书 | `https://www.xiaohongshu.com/search_result?keyword=QUERY` | 生活分享 |
| P1 | 微博 | `https://s.weibo.com/weibo?q=QUERY` | 实时动态 |
| B | 百度 | `https://www.baidu.com/s?wd=QUERY` | 广泛搜索 |

---

## 使用示例

```javascript
// 公众号文章
web_fetch(url="https://weixin.sogou.com/weixin?type=2&query=AI技术趋势&page=1", maxChars=10000)

// B站视频
web_fetch(url="https://search.bilibili.com/all?keyword=Python教程", maxChars=8000)

// 知乎讨论
web_fetch(url="https://www.zhihu.com/search?q=AI就业前景&type=content", maxChars=8000)

// 小红书
web_fetch(url="https://www.xiaohongshu.com/search_result?keyword=护肤心得", maxChars=8000)
```

---

## 信源权重

```
专业平台（B站、知乎）          → 权重 0.8
字节生态（抖音、西瓜）          → 权重 0.75
社交平台（小红书、微博）        → 权重 0.7
公众号文章                      → 权重 0.65
```
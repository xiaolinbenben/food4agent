---
domain: tech
keywords: [AI, 机器学习, 深度学习, LLM, GPT, 编程, React, Vue, Python, Java, Go, Android, iOS, Flutter, Unity, 游戏开发, 代码, API, bug, 框架]
version: 4.2.0
---

# 技术领域搜索

## 快速路由

| 子类型 | 触发关键词 | P0引擎 | P1引擎 |
|--------|------------|--------|--------|
| AI技术 | AI、机器学习、深度学习、LLM、GPT、RAG、Agent | CSDN + ArXiv | 掘金 + GitHub |
| 前后端 | React、Vue、Python、Java、Go、Node.js、API | StackOverflow + CSDN | 掘金 + GitHub |
| 移动端 | Android、iOS、Flutter、React Native | CSDN + 掘金 | StackOverflow |
| 游戏开发 | Unity、Unreal、游戏引擎、GameDev | CSDN + StackOverflow | 知乎 |

---

## 引擎URL模板

| 引擎 | URL模板 | 说明 | 来源类型 |
|------|---------|------|----------|
| CSDN | `https://so.csdn.net/so/search/s.do?q=QUERY` | 中文技术首选 | 👥 技术社区 |
| StackOverflow | `https://stackoverflow.com/search?q=QUERY` | 英文技术问答标杆 | 👥 技术社区 |
| Gitee | `https://search.gitee.com/?q=QUERY` | 国产开源镜像 | 🏢 官方 |
| GitHub代码 | `https://github.com/search?q=QUERY&type=code` | 代码示例 | 🏢 官方 |
| 掘金 | `https://juejin.cn/search?query=QUERY` | 前端技术 | 👥 技术社区 |
| ArXiv | `http://export.arxiv.org/api/query?search_query=all:QUERY` | AI论文 | 🏢 官方 |

---

## 执行示例

```javascript
// AI技术
web_fetch(url="https://so.csdn.net/so/search/s.do?q=LLM+Agent", maxChars=10000)
web_fetch(url="http://export.arxiv.org/api/query?search_query=all:LLM+Agent&max_results=5")

// React问题
web_fetch(url="https://stackoverflow.com/search?q=React+hooks+best+practices")

// Flutter开发
web_fetch(url="https://so.csdn.net/so/search/s.do?q=Flutter状态管理")

// GitHub代码
web_fetch(url="https://github.com/search?q=React+performance&type=code")
```

---

## 并行策略

| 场景 | 并行组合 | 说明 |
|------|----------|------|
| 中文技术问题 | CSDN + 掘金 | 中文技术社区 |
| 英文技术问题 | StackOverflow + GitHub | 英文代码+问答 |
| AI技术 | CSDN + ArXiv | 教程+论文 |

---

## 信源权重（v4.2.0更新）

```
🏢 官方文档（React.dev、Python.org、GitHub官方）  → 权重 1.0
🏢 官方平台（GitHub、Gitee、ArXiv）              → 权重 0.95
📰 权威媒体（InfoQ、腾讯云开发者社区）            → 权重 0.85
👥 技术社区（StackOverflow、CSDN、掘金）         → 权重 0.7
📝 个人博客（知乎专栏、个人站点）                 → 权重 0.5
```

---

## 采纳建议（v4.2.0更新）

| 来源类型 | 采纳建议 | 验证建议 |
|----------|----------|----------|
| 🏢 官方文档 | ⭐⭐⭐ 强烈推荐 | 无需交叉验证 |
| 🏢 官方平台 | ⭐⭐⭐ 强烈推荐 | 无需交叉验证 |
| 📰 权威媒体 | ⭐⭐ 推荐 | 建议与官方来源交叉验证 |
| 👥 技术社区 | ⭐ 可选 | 需与官方来源交叉验证 |
| 📝 个人博客 | ⚠️ 谨慎采纳 | 强烈建议交叉验证 |
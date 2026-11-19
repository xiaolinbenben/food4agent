---
name: tech-search
description: 技术类搜索子技能 - AI技术、前后端编程、移动端开发、游戏开发
trigger:
  keywords: [AI, 机器学习, 深度学习, LLM, GPT, 编程, React, Vue, Python, Java, Go, Android, iOS, Flutter, Unity, 游戏开发]
---

# 技术类搜索

## 查询类型识别

| 子类型 | 触发关键词 |
|--------|------------|
| AI技术 | AI、机器学习、深度学习、LLM、GPT、神经网络、RAG、Agent |
| 前后端 | React、Vue、Python、Java、Go、Node.js、API、框架名 |
| 移动端 | Android、iOS、Flutter、React Native、Swift、Kotlin |
| 游戏开发 | Unity、Unreal、游戏引擎、GameDev、OpenGL |

---

## 引擎路由表

### AI技术

| 优先级 | 引擎 | URL模板 | 说明 |
|--------|------|---------|------|
| P0 | CSDN | `https://so.csdn.net/so/search/s.do?q=QUERY` | 中文AI教程 |
| P0 | Stack Overflow | `https://stackoverflow.com/search?q=QUERY` | 英文技术问答标杆 |
| P0 | Gitee | `https://search.gitee.com/?q=QUERY` | 国产开源镜像 |
| P1 | 知乎 | `https://www.zhihu.com/search?q=QUERY&type=content` | 行业讨论 |
| P1 | ArXiv | `http://export.arxiv.org/api/query?search_query=all:QUERY` | 学术论文 |
| B | 必应中文 | `https://cn.bing.com/search?q=QUERY` | 广泛搜索 |

### 前后端编程

| 优先级 | 引擎 | URL模板 | 说明 |
|--------|------|---------|------|
| P0 | Stack Overflow | `https://stackoverflow.com/search?q=QUERY` | 代码问答标杆 |
| P0 | CSDN | `https://so.csdn.net/so/search/s.do?q=QUERY` | 中文教程 |
| P1 | GitHub代码 | `https://github.com/search?q=QUERY&type=code` | 代码示例 |
| P1 | 掘金 | `https://juejin.cn/search?query=QUERY` | 前端技术 |
| B | 必应中文 | `https://cn.bing.com/search?q=QUERY` | 广泛搜索 |

### 移动端开发

| 优先级 | 引擎 | URL模板 | 说明 |
|--------|------|---------|------|
| P0 | CSDN | `https://so.csdn.net/so/search/s.do?q=QUERY` | Android/iOS |
| P0 | Stack Overflow | `https://stackoverflow.com/search?q=QUERY` | 移动端问答标杆 |
| P1 | 掘金 | `https://juejin.cn/search?query=QUERY` | Flutter/RN |
| B | 必应中文 | `https://cn.bing.com/search?q=QUERY` | 广泛搜索 |

### 游戏开发

| 优先级 | 引擎 | URL模板 | 说明 |
|--------|------|---------|------|
| P0 | CSDN | `https://so.csdn.net/so/search/s.do?q=QUERY` | Unity/UE教程 |
| P0 | Stack Overflow | `https://stackoverflow.com/search?q=QUERY` | 游戏引擎问答标杆 |
| P1 | 知乎 | `https://www.zhihu.com/search?q=QUERY&type=content` | 游戏设计 |
| B | 必应中文 | `https://cn.bing.com/search?q=QUERY` | 广泛搜索 |

---

## 并行策略

| 场景 | 并行组合 | 说明 |
|------|----------|------|
| 中文技术问题 | CSDN + 掘金 | 中文技术社区 |
| 英文技术问题 | Stack Overflow + GitHub | 英文代码+问答 |
| AI技术 | CSDN + ArXiv | 教程+论文 |

---

## 使用示例

```javascript
// AI技术
web_fetch(url="https://so.csdn.net/so/search/s.do?q=LLM+Agent", maxChars=10000)
web_fetch(url="http://export.arxiv.org/api/query?search_query=all:LLM+Agent&max_results=5", maxChars=8000)

// React问题
web_fetch(url="https://stackoverflow.com/search?q=React+hooks+best+practices", maxChars=10000)

// Flutter开发
web_fetch(url="https://so.csdn.net/so/search/s.do?q=Flutter状态管理", maxChars=10000)
```
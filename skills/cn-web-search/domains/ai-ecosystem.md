---
domain: ai-ecosystem
keywords: [AI工具, 技能平台, Agent Skills, Claude Code, Cursor, Windsurf, Copilot, MCP Server, 开发者生态, 技能市场, LLM应用]
version: 4.3.1
---

# AI技术/开发者生态搜索

> 覆盖AI代码工具、技能平台、MCP Server等开发者生态资源

---

## 快速路由

| 子类型 | 触发关键词 | P0引擎 | P1引擎 |
|--------|------------|--------|--------|
| AI代码工具 | Claude Code, Cursor, Windsurf, Copilot, Qwen Code | GitHub + 腾讯SkillHub | CSDN + 掘金 |
| 技能平台 | skills.sh, Agent Skills, Coze, SkillHub, GPTs | skills.sh + 腾讯SkillHub | GitHub |
| MCP Server | MCP, Model Context Protocol, MCP Server | GitHub + ArXiv | CSDN |
| LLM应用 | RAG, Agent, LangChain, Prompt Engineering | GitHub + 腾讯SkillHub | ArXiv + 掘金 |

---

## 引擎URL模板

| 引擎 | URL模板 | 说明 | 来源类型 |
|------|---------|------|----------|
| GitHub | `https://github.com/search?q=QUERY&type=code` | 代码/项目搜索 | 🏢 官方 |
| skills.sh | `https://skills.sh` | Vercel技能聚合站 | 🏢 官方 |
| 腾讯SkillHub | `https://skillhub.tencent.com/search?keyword=QUERY` | 国内技能市场 | 🏢 官方 |
| CSDN | `https://so.csdn.net/so/search/s.do?q=QUERY` | 中文技术社区 | 👥 技术社区 |
| 掘金 | `https://juejin.cn/search?query=QUERY` | 前端技术平台 | 👥 技术社区 |
| ArXiv | `http://export.arxiv.org/api/query?search_query=all:QUERY` | AI论文预印本 | 🏢 官方 |
| Coze | `https://www.coze.cn/skills?keyword=QUERY` | 字节技能平台 | 🏢 官方 |
| agentskills.io | `https://agentskills.io/home` | Agent Skills官方注册表 | 🏢 官方 |

---

## 执行示例

```javascript
// AI代码工具查询
web_fetch(url="https://github.com/search?q=Claude+Code+best+practices&type=code")
web_fetch(url="https://skillhub.tencent.com/search?keyword=Claude Code")

// 技能平台查询
web_fetch(url="https://skills.sh")
web_fetch(url="https://skillhub.tencent.com/search?keyword=Agent Skills")

// MCP Server查询
web_fetch(url="https://github.com/search?q=MCP+Server&type=repositories")
web_fetch(url="http://export.arxiv.org/api/query?search_query=all:Model+Context+Protocol&max_results=5")

// LLM应用查询
web_fetch(url="https://github.com/search?q=RAG+Agent&type=code")
web_fetch(url="https://skillhub.tencent.com/search?keyword=LangChain")
```

---

## 并行策略

| 场景 | 并行组合 | 说明 |
|------|----------|------|
| AI代码工具 | GitHub + 腾讯SkillHub | 代码+技能市场 |
| 技能平台 | skills.sh + 腾讯SkillHub | 国际+国内市场 |
| MCP Server | GitHub + ArXiv | 代码+论文 |
| LLM应用 | GitHub + 腾讯SkillHub + ArXiv | 三引擎并行 |

---

## 信源权重

```
🏢 官方平台（GitHub、skills.sh、SkillHub、ArXiv）  → 权重 1.0
🏢 官方技能市场（Coze、agentskills.io）           → 权重 0.95
📰 权威媒体（InfoQ、腾讯云开发者社区）            → 权重 0.85
👥 技术社区（CSDN、掘金）                        → 权重 0.7
📝 个人博客（知乎专栏、个人站点）                 → 权重 0.5
```

---

## 采纳建议

| 来源类型 | 采纳建议 | 验证建议 |
|----------|----------|----------|
| 🏢 官方平台 | ⭐⭐⭐ 强烈推荐 | 无需交叉验证 |
| 🏢 官方技能市场 | ⭐⭐⭐ 强烈推荐 | 无需交叉验证 |
| 📰 权威媒体 | ⭐⭐ 推荐 | 建议与官方来源交叉验证 |
| 👥 技术社区 | ⭐ 可选 | 需与官方来源交叉验证 |
| 📝 个人博客 | ⚠️ 谨慎采纳 | 强烈建议交叉验证 |

---

## 典型查询示例

| 用户查询 | 路由结果 | 推荐引擎 |
|----------|----------|----------|
| "Claude Code怎么用" | ai-ecosystem/AI代码工具 | GitHub + 腾讯SkillHub |
| "有什么好的Agent Skills" | ai-ecosystem/技能平台 | skills.sh + 腾讯SkillHub |
| "MCP Server开发教程" | ai-ecosystem/MCP Server | GitHub + CSDN |
| "RAG架构设计" | ai-ecosystem/LLM应用 | GitHub + ArXiv |
| "Cursor vs Windsurf对比" | ai-ecosystem/AI代码工具 | GitHub + 掘金（对比并行） |

---

## 特殊处理规则

### 工具对比查询

```
IF 查询含[vs/对比/哪个好] + AI工具关键词:
  → 自动生成对比表格
  → 维度：价格/功能/性能/生态/学习曲线
  → 并行数提升至3引擎
```

### 技能发现查询

```
IF 查询含[推荐/有什么/好的] + 技能平台关键词:
  → 优先搜索技能聚合站（skills.sh/SkillHub）
  → 输出按热度/评分排序的技能列表
```

---

_更新: 2026-05-16 (v4.3.1新增领域)_
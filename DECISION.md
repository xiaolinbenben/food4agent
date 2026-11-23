# Decision Log

本文档只记录当前有效的架构决策。不要记录旧方案、过程结论或一次性排查说明。

## 受众

- food4agent 给 Agent 提供 skill 和 MCP。
- 文档、示例和站点不针对某一个 Agent 来写。
- 不写某个 Agent 的私有目录、私有配置或专有命令。

## 技能安装

- 技能源码只放在仓库 `skills/<name>`。
- 安装地址是 `https://food4agent.com/skills/<name>`。
- 安装到当前工作目录的 `skills/<name>`。
- 不安装到用户主目录，也不安装到某个 Agent 自己的技能目录。
- 再次安装前删除已有同名目录。
- 目录名只用小写字母、数字和短横线，并且等于 `SKILL.md` 的 `name`。

## MCP

- MCP 由 Agent 以 stdio 启动 `server.py`。
- 工作目录是本机仓库里的 `mcp/<name>`。
- 不写入某个 Agent 的私有配置。

## 文档

- 长期规则只写在 `DECISION.md`。
- README 只说明仓库怎么用，不记录决策日志。

## 站点

- 公共站点用 `/skills` 列出收录的全部技能，用 `/mcp` 列出收录的 MCP。
- 单个技能的网站地址是 `https://food4agent.com/skills/<name>`。
- 技能主分类统一维护在 `skills/categories.json`，按实际用途归类，每个技能恰好属于一个分类。
- 新增、删除或重命名技能时同步分类清单，构建拒绝遗漏、重复归类和不存在的技能引用。
- 技能分类通过 `/skills?category=<id>` 筛选，搜索词使用 `q` 参数匹配技能名称和简介；分页保留分类与搜索词，切换分类或提交搜索回到第一页。
- 技能集合用复数路径。MCP 目录用 `/mcp`。
- 首页只链到这两类内容和安装方式。
- 公共页面不放与技能和 MCP 无关的演示。

## 技能分发

- 技能以静态文件分发，不压缩、不经过数据库或对象存储，构建时由 `apps/web` 生成到站点产物的 `registry/`。
- `registry/skills.json` 是全量索引，包含名称、简介、分类、版本、更新时间、文件数和总字节数。
- `registry/skills/<name>/` 保持标准 Skill 目录结构，文件可按原路径直接获取；同目录 `manifest.json` 列出每个文件的路径、sha256 和字节数。
- 只发布 git 跟踪的文件，跳过以点开头的路径段。
- 版本是文件路径与 sha256 排序后的内容哈希前 12 位，不人工维护版本号，`SKILL.md` 不写版本。
- registry 地址不带哈希，响应统一 `Cache-Control: no-cache`；不存在的 registry 路径返回 404，不回落到站点首页。

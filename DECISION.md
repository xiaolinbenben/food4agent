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
- 技能集合用复数路径。MCP 目录用 `/mcp`。
- 首页只链到这两类内容和安装方式。
- 公共页面不放与技能和 MCP 无关的演示。

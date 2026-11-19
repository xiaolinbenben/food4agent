# Decision Log

本文档只记录当前有效的架构决策。不要记录旧方案、过程结论或一次性排查说明。

## 受众

- food4agent 给 Agent 提供 skill 和 MCP。
- 不绑定单一宿主。
- 说明、配置示例和站点文案不写宿主私有目录、私有配置文件或宿主专有命令。

## 技能安装

- 技能源码只放在仓库 `skills/<name>`。
- 安装来源有两条路径，装的是同一份技能：GitHub 上的 `skills/<name>`，以及本机 food4agent 仓库里的 `skills/<name>`。
- 两条路径都安装到当前工作目录的 `skills/<name>`。
- 不安装到用户主目录、宿主私有技能目录或其他位置。
- 再次安装前删除已有同名目录。
- 目录名只用小写字母、数字和短横线，并且等于 `SKILL.md` 的 `name`。

## MCP

- MCP 由 Agent 以 stdio 启动 `server.py`。
- 工作目录是本机仓库里的 `mcp/<name>`。
- 不把 MCP 写进某个宿主的私有配置文件。

## 文档

- 长期规则只写在 `DECISION.md`。
- README 只说明仓库怎么用，不记录决策日志。

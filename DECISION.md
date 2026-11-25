# Decision Log

本文档只记录当前有效的架构决策。不要记录旧方案、过程结论或一次性排查说明。

## 受众

- food4agent 给 Agent 提供 skill 和 MCP。
- 文档、示例和站点不针对某一个 Agent 来写。
- 不写某个 Agent 的私有目录、私有配置或专有命令。

## 技能安装

- 仓库收录的技能源码只放在 `skills/<name>`。
- 收录技能的安装地址是 `https://food4agent.com/skills/<name>`。
- 用户自己的技能不放进这个目录。
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

- 仓库收录的技能在站点上仍以未压缩目录展示，构建时生成到 `registry/`。
- `registry/skills.json` 是收录技能的展示索引，包含名称、简介、分类、版本、更新时间、文件数、总字节数和安装包摘要。
- `registry/skills/<name>/` 保持标准 Skill 目录结构，供页面按原路径读取；同目录 `manifest.json` 列出每个文件的路径、sha256 和字节数。
- 安装协议是发现索引加 zip，不把 `registry/` 当作安装入口。全站索引是 `/.well-known/agent-skills/index.json`，单个技能索引是 `/skills/<name>/.well-known/agent-skills/index.json`。
- 安装包是未压缩 zip，`SKILL.md` 在根目录，放在 `/.well-known/agent-skills/<name>.zip`。账号技能的安装包使用同一相对文件名，放在该技能发现索引旁边。索引使用 `https://schemas.agentskills.io/discovery/0.2.0/schema.json`，`digest` 是 zip 原始字节的 `sha256:` 加 64 位十六进制。
- 只发布 git 跟踪的文件，跳过以点开头的路径段。
- 收录技能的版本是文件路径与 sha256 排序后的内容哈希前 12 位，不人工维护版本号，`SKILL.md` 不写版本。
- registry 地址不带哈希，响应统一 `Cache-Control: no-cache`；不存在的 registry 路径返回 404，不回落到站点首页。
- 用户自己的技能不进入公共 registry，也不出现在公共索引里。

## 账号

- 用户 ID 是主页和技能地址里的稳定标识，规则与 GitHub 用户名相同：1 到 39 位字母、数字或单个短横线，不能连续，也不能开头或结尾。
- 用户 ID 不区分大小写，地址使用小写形式。
- 昵称可以修改，不作为地址。
- 账号预留邮箱，登录先只用用户 ID 和密码。
- 个人主页是 `https://food4agent.com/<user-id>`，也是这个账号的控制台。
- 个人主页管理访问令牌。技能列表在 `https://food4agent.com/<user-id>/skills`。
- 不使用单独的控制台域名。
- `skills`、`registry`、`api`、`admin`、`mcp`、`login` 这类系统路径不能注册为用户 ID。

## 账号技能

- 一个技能只属于一个用户。不同用户可以有同名技能。
- 技能可以公开或私有。公开技能无需登录即可读取，私有技能需要该用户的登录会话或访问令牌。
- 没有权限和不存在返回同样的 404，私有响应不进入公共缓存。
- 每个账号只有一个访问令牌，注册时生成，可以重置。重置后旧令牌立即失效。
- 账号令牌可以读取该账号下的全部私有技能。重置令牌后，旧令牌和带旧令牌的安装地址立即失效。
- 私有技能的安装地址是 `https://food4agent.com/<user-id>/skills/<name>/g/<token>`，其中 token 就是这个账号令牌。
- 公开的账号技能安装地址是 `https://food4agent.com/<user-id>/skills/<name>`，不带令牌。
- 访问令牌使用统一前缀，不按技能或接口种类拆开。
- 修改先进草稿。已发布版本不可改写。
- 账号技能的版本是目录内容的完整哈希。
- 每个技能只保留最近发布的 10 个版本，更早的连同文件一起删除。正在作为当前发布的版本即使更旧也不删除。
- 客户端把安装地址当成来源，只请求该地址下的 `/.well-known/agent-skills/index.json`，不退回全站索引，也不保留查询参数。
- 索引里只有一个 archive 技能时才安装。客户端下载 zip，核对 digest，确认根目录 `SKILL.md` 的 name 后解压。本地有未同步修改时不覆盖。

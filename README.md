# food4agent

给 Codex 提供 skill 和 MCP。链接指向 `main` 上的最新内容。

## 目录

```text
skills/<name>/SKILL.md
skills/<name>/scripts/
mcp/<name>/server.py
```

skill 自己的脚本放在该 skill 目录里，随 skill 一起安装。目录名就是链接最后一段，并等于 `SKILL.md` 里的 `name`。名称只用小写字母、数字和短横线。

## 链接

- Skill：`https://github.com/xiaolinbenben/food4agent/skills/hello-world`
- Skill：`https://github.com/xiaolinbenben/food4agent/skills/terln-image-gen`
- MCP：`https://github.com/xiaolinbenben/food4agent/mcp/hello-world`

把 skill 链接发给 Codex 即可安装，安装位置是 `~/.codex/skills/<name>`。同一个链接再次安装前，先删除已有的同名目录。

MCP 把 `server.py` 写入 `~/.codex/config.toml`。`cwd` 指向上面的目录；仓库更新后重启 Codex。

```toml
[mcp_servers.hello-world]
type = "stdio"
command = "python3"
args = ["server.py"]
cwd = "/你的路径/food4agent/mcp/hello-world"
enabled = true
```

## 现有内容

- `skills/hello-world`：运行 `scripts/hello.py`，输出 `hello world`。
- `skills/terln-image-gen`：用 `gpt-image-2` 生成或编辑图片。
- `mcp/hello-world`：提供 `hello_world` 工具，返回 `hello world`。

自定义域名还没有接。

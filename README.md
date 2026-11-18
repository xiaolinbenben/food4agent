# food4agent

给 Codex 提供 skill 和 MCP。链接指向 `main` 上的最新内容。

## 链接

- Skill：`https://github.com/xiaolinbenben/food4agent/skills/hello-world`
- Skill：`https://github.com/xiaolinbenben/food4agent/skills/terln-image-gen`
- Skill：`https://github.com/xiaolinbenben/food4agent/skills/get-amazon-image`
- Skill：`https://github.com/xiaolinbenben/food4agent/skills/print-fission`
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
- `skills/get-amazon-image`：获取 Amazon 商品图，并保存到本地。
- `skills/print-fission`：先读取印花的共同元素，再改写风格与细节，逐张裂变。
- `mcp/hello-world`：提供 `hello_world` 工具，返回 `hello world`。

自定义域名还没有接。

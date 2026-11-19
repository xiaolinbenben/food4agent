# food4agent

给 agent 提供 skill 和 MCP。链接指向 `main` 上的最新内容。

## 授权

免费 skill 用来安装和传播。Rainforest 这类付费接口不向用户要 key，也不把 key 放进仓库。

用户只在 https://food4agent.com/authorize 登录一次。food4agent 保管供应商 key，按调用计费。付费 skill 共用 `~/.food4agent/credentials.json` 里的 `access_token`，请求发到 `https://api.food4agent.com`。新增付费 skill 时只增加平台调用，不增加新的 key 配置。当前仓库只有 skill 客户端，授权页和 API 还没有上线。

`get-amazon-image` 调用 `POST /v1/rainforest/product-images`。请求体是 `asin` 加 `amazon_domain`，或 Amazon 商品页 `url`。平台用自己的 Rainforest key 取回图片地址，skill 再把图片保存到本地。

## 链接

- Skill：`https://github.com/xiaolinbenben/food4agent/skills/hello-world`
- Skill：`https://github.com/xiaolinbenben/food4agent/skills/terln-image-gen`
- Skill：`https://github.com/xiaolinbenben/food4agent/skills/get-amazon-image`
- Skill：`https://github.com/xiaolinbenben/food4agent/skills/print-fission`
- Skill：`https://github.com/xiaolinbenben/food4agent/skills/listing`
- MCP：`https://github.com/xiaolinbenben/food4agent/mcp/hello-world`

把 skill 链接发给 agent 即可安装，安装到当前工作目录的 `skills/<name>`。不要装到用户主目录或其他位置。同一个链接再次安装前，先删除已有的同名目录。

MCP 由 agent 以 stdio 启动 `server.py`。工作目录是 `mcp/hello-world`。仓库更新后重启 agent。

```text
command: python3
args: server.py
cwd: /你的路径/food4agent/mcp/hello-world
```

## 现有内容

- `skills/hello-world`：运行 `scripts/hello.py`，输出 `hello world`。
- `skills/terln-image-gen`：用 `gpt-image-2` 生成或编辑图片。
- `skills/get-amazon-image`：通过 food4agent 获取 Amazon 商品图，并保存到本地。
- `skills/print-fission`：先读取印花的共同元素，再改写风格与细节，逐张裂变。
- `skills/listing`：读取任务目录 `input/` 的商品资料，按脚本里的列生成 `output/listing.xlsx`。列还是演示列。
- `mcp/hello-world`：提供 `hello_world` 工具，返回 `hello world`。

## 站点

`apps/` 是全栈站点，架构与 fullstack-app-template 相同。公共首页介绍本仓库的 Skill 和 MCP。用法见 `apps/README.md`。


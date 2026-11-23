# food4agent

给 Agent 提供 skill 和 MCP。技能安装地址是 `https://food4agent.com/skills/<name>`。长期规则见 `DECISION.md`。

## 安装

把 `https://food4agent.com/skills/<name>` 发给 Agent。技能会装到当前项目的 `skills/<name>`。不要装到用户主目录。同名目录已经存在时，先删掉再装。

## 静态分发

站点构建时把每个技能原样发布到 `https://food4agent.com/registry/skills/<name>/`，不压缩。索引是 `https://food4agent.com/registry/skills.json`，单个技能的文件清单是 `registry/skills/<name>/manifest.json`。版本是目录内容哈希，内容变了版本就变。

## 授权

免费 skill 用来安装和传播。Rainforest 这类付费接口不向用户要 key，也不把 key 放进仓库。

用户只在 https://food4agent.com/authorize 登录一次。food4agent 保管供应商 key，按调用计费。付费 skill 共用 `~/.food4agent/credentials.json` 里的 `access_token`，请求发到 `https://api.food4agent.com`。新增付费 skill 时只增加平台调用，不增加新的 key 配置。当前仓库只有 skill 客户端，授权页和 API 还没有上线。

`get-amazon-image` 调用 `POST /v1/rainforest/product-images`。请求体是 `asin` 加 `amazon_domain`，或 Amazon 商品页 `url`。平台用自己的 Rainforest key 取回图片地址，skill 再把图片保存到本地。

## 链接

- Skill：`https://food4agent.com/skills/hello-world`
- Skill：`https://food4agent.com/skills/terln-image-gen`
- Skill：`https://food4agent.com/skills/get-amazon-image`
- Skill：`https://food4agent.com/skills/print-fission`
- Skill：`https://food4agent.com/skills/listing`
- MCP：`https://food4agent.com/mcp`
- 仓库：`https://github.com/xiaolinbenben/food4agent`

MCP 由 Agent 以 stdio 启动 `server.py`。工作目录是本机仓库里的 `mcp/hello-world`。仓库更新后重启 Agent。

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

`apps/` 是全栈站点。公共首页介绍本仓库的 Skill 和 MCP，技能目录是 `/skills`，MCP 目录是 `/mcp`。用法见 `apps/README.md`。


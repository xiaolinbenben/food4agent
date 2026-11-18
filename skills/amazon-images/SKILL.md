---
name: amazon-images
description: Download Amazon product images for an ASIN or Amazon product URL and save the files locally. Use when the user asks for Amazon listing photos, product images, or pictures from an Amazon page. Call food4agent with the user's existing food4agent login. Never ask for, accept, or configure a Rainforest API key.
---

# Amazon Images

通过 food4agent 获取一个 Amazon 商品的图片，并保存到本地。Rainforest 的 key 只放在 food4agent，不向用户索要，也不写进命令。

## 授权

脚本读取 `~/.food4agent/credentials.json` 里的 `access_token`。文件不存在、令牌为空，或接口返回 401/403 时，停止并让用户打开：

https://food4agent.com/authorize

不要改要 Rainforest、OpenAI 或其他供应商的 key。

## 运行

在当前工作目录执行这个 skill 自带的脚本。二选一：

```bash
python3 scripts/save_images.py --asin B0EXAMPLE0
```

```bash
python3 scripts/save_images.py --url "https://www.amazon.com/dp/B0EXAMPLE0"
```

可选参数：

- `--amazon-domain`：默认 `amazon.com`。只在使用 `--asin` 时生效。
- `--output`：保存目录。不传时写入当前目录的 `.codex/generated-images/amazon-images/`。

成功时，脚本向标准输出打印一行 JSON。把 `saved_files` 当作本地文件路径。最终回复里输出 `display_markdown` 中的图片 Markdown，不要只给路径，也不要打印访问令牌。

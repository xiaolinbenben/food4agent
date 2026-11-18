---
name: amazon-images
description: Download Amazon product images for an ASIN or Amazon product URL and save the files locally. Use when the user asks for Amazon listing photos, product images, or pictures from an Amazon page. Ask the user for the API key and pass it with --api-key. Do not read ~/.food4agent or any local credential file.
---

# Amazon Images

获取一个 Amazon 商品的图片，并保存到本地。

## API key

运行前向用户要 API key。这次对话里还没有 key 时，先停下来问，不要猜。

不要读取 `~/.food4agent`，也不要读取其他本地凭证文件。不要把 key 写入文件。不要在回复、命令回显或结果里打印 key。

## 运行

在当前工作目录执行这个 skill 自带的脚本。二选一：

```bash
python3 scripts/save_images.py --asin B0EXAMPLE0 --api-key "用户提供的 key"
```

```bash
python3 scripts/save_images.py --url "https://www.amazon.com/dp/B0EXAMPLE0" --api-key "用户提供的 key"
```

可选参数：

- `--amazon-domain`：默认 `amazon.com`。只在使用 `--asin` 时生效。
- `--output`：保存目录。不传时写入当前目录的 `.codex/generated-images/amazon-images/`。

成功时，脚本向标准输出打印一行 JSON。把 `saved_files` 当作本地文件路径。最终回复里输出 `display_markdown` 中的图片 Markdown，不要只给路径。

key 无效或请求失败时，转告错误信息，并再向用户要一次 key。

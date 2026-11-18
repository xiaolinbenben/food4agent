---
name: get-amazon-image
description: 获取 Amazon 商品图片并保存到本地。用户要 get amazon image、商品图或 Amazon 页面图片时使用。先向用户要 Rainforest API key，再运行脚本。
---

# Get Amazon Image

向用户要 Rainforest（rainforestapi.com）的 API key。在这个 skill 目录里运行脚本。把结果里的图片 Markdown 贴到回复中。

```bash
python3 scripts/save_images.py --asin B0EXAMPLE0 --api-key "用户提供的 key"
```

```bash
python3 scripts/save_images.py --url "https://www.amazon.com/dp/B0EXAMPLE0" --api-key "用户提供的 key"
```

可选：`--amazon-domain`，`--output`。成功后使用 `saved_files[0]`。

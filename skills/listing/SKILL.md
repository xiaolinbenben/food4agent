---
name: listing
description: 读取当前工作区 input/ 的商品资料，调用本技能脚本生成 output/listing.xlsx。平台模板未确定时使用脚本中的演示列。
---

处理当前任务工作区，不要修改工作区以外的文件。

1. 阅读 input/ 中的文本、CSV、Markdown。存在 input/note.txt 时，把它当作用户补充说明。
2. 图片只记录文件名，不要把图片内容交给模型。
3. 用 read 阅读 scripts/write-listing.mjs 里的 COLUMNS。这是当前唯一的列定义，不要自行增删列。
4. 保持 shell 的当前目录为任务工作区，执行：

```bash
node "<本技能目录>/scripts/write-listing.mjs" output/listing.xlsx
```

本技能目录见上方 location。标准输入是 JSON，格式为 `{"rows":[...]}`。每个字段都必须出现，未知内容用空字符串。至少一行，并且每行的商品名称不能为空。
5. 脚本成功后停止。不要再写其他表格。

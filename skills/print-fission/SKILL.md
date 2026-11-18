---
name: print-fission
description: Fission print patterns by reading shared motifs first, then rewriting style and detail into one English prompt per image. Use when the user asks for 印花裂变, 图案裂变, print pattern variations, or similar-style pattern images. Keep subject elements fixed. Generate one image at a time from the reference prints. Never make a collage or a text-only prompt.
---

# 印花裂变

先读取印花图里的共同元素，再改写提示词，逐张生成新图案。默认 4 张。用户指定张数或风格时只改变量。

提示词按 Nano Banana 2（`gemini-3.1-flash-image`）的正向提示词来写：完整英文句子，不堆关键词。

## 读取元素

查看用户给出的全部印花图。多张图只保留共同特征；只有一张时，就读取这一张。

提取这些事实：

- 主体元素：花、动物、几何形、文字纹样等具体题材
- 构图：单枚、四方连续、满底、留白
- 风格：线条、配色、疏密、材质、笔触

据此写一条英文底稿。底稿只留给后续改写，不发给用户，也不直接拿去生图。不要把几张参考图拼进同一张画面。

## 改写

每张成图单独改写一条提示词。主体元素整句保留，只改风格和细节，例如笔触、冷暖、纹理、疏密、光泽和背景处理。不新增参考图里没有的主体。

写给模型的内容只有最终英文提示词。不要加分析、标题、编号说明，也不要出现“文生图提示词”。

```text
Create one standalone print pattern of [原样保留的主体元素].
[这一张改写后的风格与细节].
Use the reference prints only as the source of those motifs.
Fill one continuous pattern, with no collage, no grid, no contact sheet, no text, and no watermark.
```

禁止两条：

- 不要生成由几张图拼接、拼贴或排成宫格的一张图。
- 不要写纯文生图提示词。每条都必须基于参考印花图改写。

## 生成

调用已安装的 `terln-image-gen`。不要换模型，也不要向用户要 key。技能不存在时停止，让用户先安装：

`https://github.com/xiaolinbenben/food4agent/skills/terln-image-gen`

每次只生成一张，并把全部参考印花图都传进去。尺寸 `1024x1024`，质量 `medium`。输出放到当前工作目录的 `.codex/generated-images/print-fission/`，文件名按序号编号，且不能覆盖已有文件。

macOS 每张重复一次 `--reference-image`：

```text
/bin/bash "$HOME/.codex/skills/terln-image-gen/scripts/invoke-image.sh" --prompt "最终英文提示词" --reference-image "/绝对路径/印花1" --reference-image "/绝对路径/印花2" --size "1024x1024" --quality "medium" --output "/绝对路径/.codex/generated-images/print-fission/01.png"
```

Windows：

```text
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\.codex\skills\terln-image-gen\scripts\invoke-image.ps1" -Prompt "最终英文提示词" -ReferenceImage "C:\绝对路径\印花1","C:\绝对路径\印花2" -Size "1024x1024" -Quality "medium" -OutputPath "C:\绝对路径\.codex\generated-images\print-fission\01.png"
```

成功后读取该次 JSON 的 `saved_files[0]`。某一张失败就停在这一张。

## 检查

并排看：主体元素是否还在，风格是否确实不同，有没有把参考图拼在一起，有没有文字或水印。

只重跑不合格的那一张，仍传全部参考图。最终回复按顺序输出每张图片 Markdown，不要贴底稿或分析。

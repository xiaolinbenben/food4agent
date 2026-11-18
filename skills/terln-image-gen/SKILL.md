---
name: terln-image-gen
description: 用 gpt-image-2 生成或编辑图片。用户要生图、改图、用参考图合成，或在对话里看生成结果时使用。先向用户要 API key，再运行脚本。
---

# Terln Image Gen

向用户要 API key，再按当前系统运行脚本。每次一张。把结果里的图片 Markdown 贴到回复中。

macOS：

```text
/bin/bash "$HOME/.codex/skills/terln-image-gen/scripts/invoke-image.sh" --prompt "提示词" --api-key "用户提供的 key"
```

有参考图时重复 `--reference-image`。

Windows：

```text
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\.codex\skills\terln-image-gen\scripts\invoke-image.ps1" -Prompt "提示词" -ApiKey "用户提供的 key"
```

有参考图时用 `-ReferenceImage`，多个路径用逗号分隔。

可选：`--size` / `-Size`，`--quality` / `-Quality`，`--output` / `-OutputPath`。成功后使用 `saved_files[0]`。

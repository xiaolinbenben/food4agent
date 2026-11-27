---
name: terln-image-gen
description: 用 gpt-image-2 生成或编辑图片。用户要生图、改图、用参考图合成，或在对话里看生成结果时使用。不要向用户要 API key，脚本会读取 Codex 配置里的 experimental_bearer_token。
---

# Terln Image Gen

不要向用户要 API key，也不要在命令里传 key。脚本读取 Codex 配置里的 `experimental_bearer_token`。

配置文件：

- macOS：`$HOME/.codex/config.toml`，也就是 `~/.codex/config.toml`
- Windows：`%USERPROFILE%\.codex\config.toml`
- 设置了 `CODEX_HOME` 时，两边都改读 `$CODEX_HOME/config.toml`（Windows 上是 `%CODEX_HOME%\config.toml`）

在这个 skill 目录里运行脚本，每次一张。把结果里的图片 Markdown 贴到回复中。

macOS：

```text
/bin/bash scripts/invoke-image.sh --prompt "提示词"
```

有参考图时重复 `--reference-image`。

Windows：

```text
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/invoke-image.ps1 -Prompt "提示词"
```

有参考图时用 `-ReferenceImage`，多个路径用逗号分隔。

可选：`--size` / `-Size`，`--quality` / `-Quality`，`--output` / `-OutputPath`。成功后使用 `saved_files[0]`。

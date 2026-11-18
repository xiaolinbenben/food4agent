---
name: terln-image-gen
description: Generate or edit general-purpose images with gpt-image-2 using the provider credentials in the user-level Codex config file. Use when the user asks to create an image from a prompt, edit or transform one or more local reference images, compose subjects from reference images, or show an API-generated image in the ChatGPT/Codex GUI. Read base_url and experimental_bearer_token from [model_providers.custom] in ~/.codex/config.toml. Supports Windows through PowerShell and macOS through the built-in shell and system utilities, without requiring Node.js or Python.
---

# Terln Image Gen

Generate an image from text or edit up to sixteen local reference images. Select the bundled Windows or macOS implementation, save the result locally, and render it in the chat response.

## Credentials And API Routing

- Read `base_url` and `experimental_bearer_token` only from `[model_providers.custom]` in `~/.codex/config.toml`.
- On macOS, resolve the user-level config file as `$HOME/.codex/config.toml`.
- On Windows, resolve the user-level config file as `%USERPROFILE%\.codex\config.toml`.
- Use `base_url` as the API base URL and `experimental_bearer_token` as the Bearer token.
- Use `gpt-image-2` and generate one image per invocation.
- With no reference image, send JSON to `<base_url>/images/generations`.
- With one or more reference images, send multipart form data to `<base_url>/images/edits` using repeated `image[]` fields.
- Accept local reference files only. Do not silently switch to URL-based or provider-specific edit request shapes.
- Always save the returned image to a local file. Never leave a base64 result only in terminal output.
- Never print the API key or include it in result JSON, errors, or chat output.
- Do not require Node.js, Python, jq, Homebrew, Git Bash, or WSL.

## Select The Platform Script

Inspect the current OS before running a command:

- On Windows, run `scripts\invoke-image.ps1` with `powershell.exe`.
- On macOS, run `scripts/invoke-image.sh` with `/bin/bash`.
- On any other OS, stop and report that the skill supports Windows and macOS only.

Do not run the Windows script on macOS or the macOS script on Windows.

## Workflow

1. Resolve the user's final prompt. For edits, make the intended changes and the elements to preserve explicit.
2. Resolve every reference image to an existing local file path. If a required chat attachment has no accessible local path, ask the user to attach or provide the file again.
3. Select and run the script for the current OS.
4. Read the JSON result and use `saved_files[0]` as the source of truth.
5. Inspect the saved image when an image-viewing tool is available.
6. In the final response, emit `display_markdown[0]` as actual Markdown so the generated image is visible in the ChatGPT/Codex GUI. Do not return only a path, URL, or fenced JSON block.

## Windows

Generate from text:

```text
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".codex\skills\terln-image-gen\scripts\invoke-image.ps1" -Prompt "A quiet lakeside cabin at blue hour, cinematic photography" -Size "1536x1024"
```

Edit one or more local reference images:

```text
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".codex\skills\terln-image-gen\scripts\invoke-image.ps1" -Prompt "Compose the subjects into one natural group portrait" -ReferenceImage "C:\path\person-a.png","C:\path\person-b.jpg" -Size "1536x1024" -Quality "high"
```

## macOS

Generate from text:

```text
/bin/bash ".codex/skills/terln-image-gen/scripts/invoke-image.sh" --prompt "A quiet lakeside cabin at blue hour, cinematic photography" --size "1536x1024"
```

Edit one or more local reference images by repeating `--reference-image`:

```text
/bin/bash ".codex/skills/terln-image-gen/scripts/invoke-image.sh" --prompt "Compose the subjects into one natural group portrait" --reference-image "/path/person-a.png" --reference-image "/path/person-b.jpg" --size "1536x1024" --quality "high"
```

## Parameters

Required:

- Windows `-Prompt` / macOS `--prompt`: final text instruction for generation or editing.

Optional:

- Windows `-ReferenceImage`: one to sixteen local PNG, JPEG, or WebP files, passed as comma-separated quoted values after one parameter. macOS `--reference-image`: repeat the option for each file. Supplying any reference selects edit mode.
- Windows `-Size` / macOS `--size`: `auto` or a `WIDTHxHEIGHT` string. Default `1024x1024`.
- Windows `-Quality` / macOS `--quality`: `auto`, `low`, `medium`, or `high`. Default `auto`.
- Windows `-OutputPath` / macOS `--output`: destination `.png`, `.jpg`, `.jpeg`, or `.webp` path. If omitted, save a unique PNG under `.codex/generated-images/` in the current workspace.
- Windows `-TimeoutSeconds` / macOS `--timeout-seconds`: request timeout. Default 300 seconds.

Both scripts print the same compact JSON shape on success:

```json
{
  "status": "completed",
  "operation": "generation",
  "model": "gpt-image-2",
  "size": "1024x1024",
  "saved_files": ["/absolute/path/generated.png"],
  "display_markdown": ["![Generated image](</absolute/path/generated.png>)"]
}
```

## Failure Handling

- If the user-level config file is missing, report its expected OS-specific path. If `base_url` or `experimental_bearer_token` is missing, report the exact field and ask the user to launch ChatGPT from the Terln assistant again so the config file is rewritten.
- If a reference file is missing or unsupported, report that exact path and do not call the API.
- If the API returns an error, report its message without exposing credentials.
- If the response contains neither `b64_json` nor `url`, report a bounded response summary and do not create a placeholder image.
- If the output path already exists, stop instead of overwriting it.

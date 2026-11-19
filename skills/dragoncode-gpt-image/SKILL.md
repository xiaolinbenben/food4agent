---
name: dragoncode-gpt-image
description: Use when Codex needs to submit text-to-image or image-to-image requests to the DragonCode GPT-Image-2 API, especially when another image generation or image editing skill has already prepared the prompt, aspect ratio, resolution, and optional reference images and needs a normalized API client. Handles the fixed endpoint, .env API key lookup, request shape, supported size/resolution validation, submit-only task creation, existing task polling, and final image URL extraction.
---

# DragonCode GPT Image

Use DragonCode GPT-Image-2 as the API transport for image generation or image editing tasks. This skill does not decide artistic direction, rewrite prompts, or infer editing intent; the caller must provide the final prompt and optional reference images.

## Contract

- Read the API key from `.env` in the current user workspace directory.
- The required environment variable is `TERLN_API_KEY`.
- Read proxy settings from standard proxy variables when present: `HTTPS_PROXY`, `HTTP_PROXY`, or `ALL_PROXY`.
- If no proxy variable is configured, read common local Mihomo/Clash config files and use a listening top-level `mixed-port` or `port`; otherwise probe common local Mihomo/Clash ports.
- Use base URL `https://dragoncode.codes/gpt-image/v1`.
- Submit requests to `/images/generations`.
- Poll results from `/tasks/{task_id}`.
- Always send `model: "gpt-image-2"` and `n: 1`.
- Return the completed image URL from `data.result.images[0].url[0]` or the list of generated URLs.
- For upstream workflows that can do other work while images generate, use submit-only mode first, then poll the returned task IDs later. Do not resubmit a task just because the first command returned only a task ID.

## Parameters

Required:

- `prompt`: final image prompt supplied by the user or an upstream image editing/generation skill.

Optional:

- `size`: one of `auto`, `1:1`, `3:2`, `2:3`, `4:3`, `3:4`, `5:4`, `4:5`, `16:9`, `9:16`, `2:1`, `1:2`, `21:9`, `9:21`. Default to `1:1` when the caller does not specify an aspect ratio.
- `resolution`: one of `1k`, `2k`, `4k`. Default to `2k`.
- `image_urls`: zero to sixteen URL or base64 data URI reference images for image-to-image tasks. In the Windows command, pass multiple references as comma-separated quoted values after one `-ImageUrl` parameter, for example `-ImageUrl "url-a","url-b"`.
- `SubmitOnly`: submit the task and return `task_id` without polling.
- `TaskId`: poll an existing task ID and return the completed image URLs.
- `PollOnce`: with `TaskId`, check current status/progress/image URLs once and return immediately without waiting for completion. Use this for watcher scripts that poll many tasks.

Reject `4k` unless `size` is one of `16:9`, `9:16`, `2:1`, `1:2`, `21:9`, `9:21`.

## Workflow

1. Confirm the user workspace `.env` contains `TERLN_API_KEY=...`.
2. Let the upstream image editing/generation logic provide the final prompt, size, resolution, and image URLs.
3. Run `.codex\skills\dragoncode-gpt-image\scripts\generate_image.cmd` from the user workspace root so `.env` resolves correctly.
4. Show the returned URL to the user, or embed it in Markdown/HTML when the user requested a visible image.

The bundled command uses Windows PowerShell through `powershell.exe -NoProfile -ExecutionPolicy Bypass`, so it does not require Python, Node.js, PyYAML, or any extra user installation on Windows.

Example:

```bat
.codex\skills\dragoncode-gpt-image\scripts\generate_image.cmd ^
  -Prompt "A clean product render of a matte black desk lamp on a white background" ^
  -Size "1:1" ^
  -Resolution "2k"
```

Image-to-image example:

```bat
.codex\skills\dragoncode-gpt-image\scripts\generate_image.cmd ^
  -Prompt "Convert the reference image into a watercolor illustration" ^
  -Size "4:3" ^
  -Resolution "2k" ^
  -ImageUrl "https://example.com/photo-a.jpg","https://example.com/photo-b.jpg"
```

Submit-only example:

```bat
.codex\skills\dragoncode-gpt-image\scripts\generate_image.cmd ^
  -Prompt "A clean product render of a white T-shirt" ^
  -Size "1:1" ^
  -Resolution "1k" ^
  -SubmitOnly
```

Poll an existing task:

```bat
.codex\skills\dragoncode-gpt-image\scripts\generate_image.cmd ^
  -TaskId "task_xxx"
```

Check an existing task once without blocking:

```bat
.codex\skills\dragoncode-gpt-image\scripts\generate_image.cmd ^
  -TaskId "task_xxx" ^
  -PollOnce
```

The script prints JSON on success:

```json
{
  "task_id": "task_xxx",
  "status": "completed",
  "image_urls": ["https://dragoncode.codes/gpt-image/media/task_xxx/0?token=..."]
}
```
The script may also print progress text such as `Submitted task ...` or `pending ...` while polling. Treat the process exit code and final JSON object as authoritative; do not classify progress written to stderr as a failed generation by itself.

## Failure Handling

- If `.env` or `TERLN_API_KEY` is missing in the current working directory, stop and ask the user to add it.
- In PowerShell scripts, do not create a local variable named `$home`. PowerShell variable names are case-insensitive, so `$home` conflicts with the built-in read-only `$HOME` variable. Use a name such as `$userProfileDir` for user-profile paths.
- If the API returns `failed`, report the API error message.
- If polling times out, report the task ID so the user can query it later.
- If submit-only returns `status: "submitted"`, continue the upstream workflow and poll with `-TaskId` later.
- If a wrapper or terminal session stops after printing `Submitted task <task_id>`, poll that task with `-TaskId` before submitting the same prompt again.
- If the upstream workflow has many task IDs, use `-PollOnce` in a loop so one unfinished task does not block checks and downloads for already completed tasks.
- Do not add alternate API key names, alternate base URLs, compatibility fields, or fallback request shapes unless the user explicitly confirms that change.

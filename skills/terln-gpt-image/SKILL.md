---
name: terln-gpt-image
description: Use when Codex needs to submit text-to-image or image-to-image requests to the Terln gpt-image-2 image API through https://api.terln.com/v1/images/generations, especially when another image generation workflow has already prepared the prompt, size, and optional reference image URLs and needs a normalized API client. Handles fixed endpoint usage, .env TERLN_API_KEY lookup, request shape, proxy discovery, synchronous image result extraction, and optional local image saving.
---

# Terln GPT Image

Use Terln `gpt-image-2` as the API transport for image generation tasks. This skill does not decide artistic direction, rewrite prompts, or infer editing intent; the caller must provide the final prompt and optional reference images.

## Contract

- Read the API key from `.env` in the current user workspace directory.
- The required environment variable is `TERLN_API_KEY`.
- Read proxy settings from standard proxy variables when present: `HTTPS_PROXY`, `HTTP_PROXY`, or `ALL_PROXY`.
- If no proxy variable is configured, read common local Mihomo/Clash config files and use a listening top-level `mixed-port` or `port`; otherwise probe common local Mihomo/Clash ports.
- Use fixed base URL `https://api.terln.com`.
- Submit requests to `/v1/images/generations`.
- Always send `model: "gpt-image-2"` and `n: 1`.
- Send `size` as an API size string such as `1024x1024`, `960x1280`, or `1024x1280`.
- Pass `image_urls` only when the upstream workflow supplied reference image URLs for the current request.
- Return generated image URLs when the API returns URLs.
- If the API returns base64 image data and `-OutputPath` is provided, decode the first image directly to that local file.
- Do not add task polling, alternate API key names, alternate base URLs, compatibility request shapes, or fallback providers unless the user explicitly confirms that change.

## Parameters

Required:

- `prompt`: final image prompt supplied by the user or an upstream image generation skill.

Optional:

- `size`: API image size string. Default to `1024x1024`.
- `image_urls`: zero to sixteen URL reference images. In the Windows command, pass multiple references as comma-separated quoted values after one `-ImageUrl` parameter, for example `-ImageUrl "url-a","url-b"`.
- `OutputPath`: local path where the first returned image should be saved. Use this for workflows that need files for later upload.
- `TimeoutSeconds`: request timeout. Default to 300 seconds.

## Workflow

1. Confirm the user workspace `.env` contains `TERLN_API_KEY=...`.
2. Let the upstream image generation logic provide the final prompt, size, and optional image URLs.
3. Run `.codex\skills\terln-gpt-image\scripts\generate_image.cmd` from the user workspace root so `.env` resolves correctly.
4. Use the returned JSON result. If `OutputPath` was supplied, treat `saved_files[0]` as the generated local file.

The bundled command uses Windows PowerShell through `powershell.exe -NoProfile -ExecutionPolicy Bypass`, so it does not require Python, Node.js, PyYAML, or any extra user installation on Windows.

Example:

```bat
.codex\skills\terln-gpt-image\scripts\generate_image.cmd ^
  -Prompt "A clean product render of a matte black desk lamp on a white background" ^
  -Size "1024x1024"
```

Image-to-image example:

```bat
.codex\skills\terln-gpt-image\scripts\generate_image.cmd ^
  -Prompt "Use the reference images to create a clean catalog product image" ^
  -Size "1024x1024" ^
  -ImageUrl "https://example.com/photo-a.jpg","https://example.com/photo-b.jpg" ^
  -OutputPath "data\offer\image\generated\square\black-square.png"
```

The script prints JSON on success:

```json
{
  "status": "completed",
  "model": "gpt-image-2",
  "size": "1024x1024",
  "image_urls": ["https://..."],
  "b64_json_count": 0,
  "saved_files": ["C:\\path\\to\\image.png"]
}
```

## Failure Handling

- If `.env` or `TERLN_API_KEY` is missing in the current working directory, stop and ask the user to add it.
- In PowerShell scripts, do not create a local variable named `$home`. PowerShell variable names are case-insensitive, so `$home` conflicts with the built-in read-only `$HOME` variable. Use a name such as `$userProfileDir` for user-profile paths.
- If the API returns an error, report the API error message.
- If the response contains neither URL nor base64 image data, report the raw response summary and do not create placeholder files.

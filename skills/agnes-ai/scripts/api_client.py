"""Core API client for Agnes AI text, image, and video generation."""

from __future__ import annotations

import json
import os
import re
import sys
import time
from typing import Any

try:
    import requests
except ImportError as _exc:
    raise SystemExit(
        "The 'requests' library is required. Install it with: pip install requests"
    ) from _exc

BASE_URL = "https://apihub.agnes-ai.com/v1"
TEXT_MODEL = "agnes-2.0-flash"
IMAGE_MODEL = "agnes-image-2.1-flash"
VIDEO_MODEL = "agnes-video-v2.0"
SIZE_RE = re.compile(r"^[1-9]\d*x[1-9]\d*$")


def get_api_key() -> str:
    for name in ("AGNES_API_KEY", "AGNES_API_TOKEN", "APIHUB_AGNES_API_KEY"):
        value = os.environ.get(name)
        if value:
            return value
    raise SystemExit(
        "Missing API key. Set AGNES_API_KEY, AGNES_API_TOKEN, or APIHUB_AGNES_API_KEY."
    )


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {get_api_key()}",
        "Content-Type": "application/json",
    }


class AgnesAPIError(RuntimeError):
    """Error from Agnes AI API calls."""


def _request(method: str, path: str, payload: dict[str, Any] | None = None,
              max_retries: int = 3, retry_delay: float = 2.0) -> requests.Response:
    """Make an HTTP request with automatic retry on transient errors."""
    url = BASE_URL + path
    last_exc: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            if method.upper() == "GET":
                resp = requests.get(url, headers=_headers(), timeout=180)
            else:
                resp = requests.post(url, headers=_headers(), json=payload, timeout=180)
            resp.raise_for_status()
            return resp
        except requests.exceptions.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else 0
            # Retry on 401 (gateway auth flapping), 429 (rate limit), 502, 503, 504
            if attempt < max_retries and status in (401, 429, 502, 503, 504):
                print(f"  Retrying ({attempt + 1}/{max_retries}) after HTTP {status}...", file=sys.stderr)
                time.sleep(retry_delay * (attempt + 1))
                last_exc = exc
                continue
            raise AgnesAPIError(
                f"HTTP {status} from {url}: {(exc.response.text[:500] if exc.response is not None else str(exc))}"
            ) from exc
        except requests.exceptions.RequestException as exc:
            if attempt < max_retries:
                print(f"  Retrying ({attempt + 1}/{max_retries}) after connection error...", file=sys.stderr)
                time.sleep(retry_delay * (attempt + 1))
                last_exc = exc
                continue
            raise AgnesAPIError(f"Request failed for {url}: {exc}") from exc
    raise AgnesAPIError(f"Max retries exceeded for {url}") from last_exc


def request_json(method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    resp = _request(method, path, payload)
    return resp.json() if resp.text else {}


def request_text(method: str, path: str, payload: dict[str, Any] | None = None) -> str:
    resp = _request(method, path, payload)
    return resp.text


def needs_english_translation(text: str) -> bool:
    return any(ord(ch) > 127 for ch in text)


def translate_to_english(text: str) -> str:
    payload = {
        "model": TEXT_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Translate the following text into fluent English. "
                    "Preserve all concrete visual details, style words, camera motion, lighting, "
                    "composition constraints, and negative instructions. Return only the English text."
                ),
            },
            {"role": "user", "content": text},
        ],
        "temperature": 0,
        "max_tokens": 1000,
    }
    data = request_json("POST", "/chat/completions", payload)
    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise AgnesAPIError(f"Translation failed: {json.dumps(data, ensure_ascii=False)}") from exc


def ensure_english(text: str) -> str:
    if needs_english_translation(text):
        return translate_to_english(text)
    return text


def generate_text(prompt: str, system: str | None = None, temperature: float = 0.7,
                  max_tokens: int = 2000, json_mode: bool = False) -> str:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    payload: dict[str, Any] = {
        "model": TEXT_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    data = request_json("POST", "/chat/completions", payload)
    # Validate response format
    if "error" in data and "choices" not in data:
        raise AgnesAPIError(f"API returned error: {json.dumps(data, ensure_ascii=False)[:300]}")
    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise AgnesAPIError(f"Text generation failed (unexpected format): {json.dumps(data, ensure_ascii=False)[:300]}") from exc


def generate_image(prompt: str, size: str = "1152x768", image_url: str | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": IMAGE_MODEL,
        "prompt": prompt,
        "extra_body": {"response_format": "url"},
    }
    if size:
        payload["size"] = size
    if image_url:
        payload["extra_body"]["image"] = [image_url]
    return request_json("POST", "/images/generations", payload)


def extract_image_urls(data: dict[str, Any]) -> list[str]:
    urls = []
    if isinstance(data.get("url"), str):
        urls.append(data["url"])
    if isinstance(data.get("image_url"), str):
        urls.append(data["image_url"])
    if isinstance(data.get("data"), list):
        for item in data["data"]:
            if isinstance(item, dict):
                for key in ("url", "image_url"):
                    if isinstance(item.get(key), str):
                        urls.append(item[key])
    return urls


def create_video_task(prompt: str, image_url: str | None = None, width: int = 1152,
                      height: int = 768, num_frames: int = 81, frame_rate: float = 24,
                      seed: int | None = None, negative_prompt: str | None = None,
                      image_list: list[str] | None = None, mode: str | None = None,
                      extra_body: dict | None = None) -> dict[str, Any]:
    """Create a video generation task.

    Args:
        prompt: English text description of the video.
        image_url: Single image URL for image-to-video.
        image_list: List of image URLs/paths for keyframe mode.
        mode: Generation mode, e.g. 'keyframes' for multi-image keyframe animation.
        extra_body: Additional fields passed verbatim in extra_body of the API call.

    Either image_url, image_list, or neither may be provided.
    When image_list is provided, mode defaults to 'keyframes'.
    """
    payload: dict[str, Any] = {
        "model": VIDEO_MODEL,
        "prompt": prompt,
        "width": width,
        "height": height,
        "num_frames": num_frames,
        "frame_rate": frame_rate,
    }
    # Single image mode (existing behavior)
    if image_url:
        payload["image"] = image_url
    # Keyframe / multi-image mode (new)
    if image_list and len(image_list) > 0:
        if mode is None:
            mode = "keyframes"
        payload["extra_body"] = extra_body if extra_body else {}
        payload["extra_body"]["image"] = image_list
        if mode:
            payload["extra_body"]["mode"] = mode
    elif mode:
        payload["mode"] = mode
    if seed is not None:
        payload["seed"] = seed
    if negative_prompt:
        payload["negative_prompt"] = negative_prompt
    return request_json("POST", "/videos", payload)


def get_video_task(task_id: str) -> dict[str, Any]:
    return request_json("GET", f"/videos/{task_id}")


def poll_video_task(task_id: str, timeout: int = 900, interval: int = 10) -> dict[str, Any]:
    deadline = time.time() + timeout
    last: dict[str, Any] = {}
    while time.time() < deadline:
        last = get_video_task(task_id)
        status = str(last.get("status", "")).lower()
        progress = last.get("progress")
        if status:
            print(f"  Task {task_id}: status={status} progress={progress}", file=sys.stderr)
        if status in ("completed", "failed"):
            return last
        time.sleep(interval)
    raise AgnesAPIError(f"Timed out waiting for video task {task_id}. Last: {json.dumps(last)}")


def extract_video_urls(data: dict[str, Any]) -> list[str]:
    urls = []
    for key in ("video_url", "url", "remixed_from_video_id"):
        value = data.get(key)
        if isinstance(value, str) and value.startswith(("http://", "https://")):
            urls.append(value)
    if isinstance(data.get("data"), list):
        for item in data["data"]:
            if isinstance(item, dict):
                urls.extend(extract_video_urls(item))
    return list(dict.fromkeys(urls))


def download_url(url: str, dest_path: str) -> str:
    try:
        resp = requests.get(url, timeout=300)
        resp.raise_for_status()
        os.makedirs(os.path.dirname(dest_path) or ".", exist_ok=True)
        with open(dest_path, "wb") as f:
            f.write(resp.content)
        return dest_path
    except Exception as exc:
        raise AgnesAPIError(f"Download failed for {url}: {exc}") from exc

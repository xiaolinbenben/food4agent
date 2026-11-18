#!/usr/bin/env python3
"""Download Amazon product images through food4agent and save them locally."""

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path


class RejectNonHttps(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not str(newurl).startswith("https://"):
            fail("图片地址必须是 https。")
        return urllib.request.HTTPRedirectHandler.redirect_request(
            self, req, fp, code, msg, headers, newurl
        )


OPENER = urllib.request.build_opener(RejectNonHttps)

API_URL = "https://api.food4agent.com/v1/rainforest/product-images"
AUTHORIZE_URL = "https://food4agent.com/authorize"
USER_AGENT = "food4agent-amazon-images"
MAX_IMAGES = 30
MAX_BYTES = 15 * 1024 * 1024
ASIN_RE = re.compile(r"^[A-Z0-9]{10}$")
DOMAIN_RE = re.compile(r"^[a-z0-9.-]+\.[a-z]{2,}$")
VARIANT_RE = re.compile(r"[^A-Za-z0-9_-]+")


def fail(message):
    print("Error: %s" % message, file=sys.stderr)
    raise SystemExit(1)


def credentials_path():
    return Path.home() / ".food4agent" / "credentials.json"


def load_token():
    path = credentials_path()
    if not path.is_file():
        fail("未登录 food4agent。打开 %s 完成授权，不要配置供应商 key。" % AUTHORIZE_URL)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        fail("无法读取 %s。打开 %s 重新授权。" % (path, AUTHORIZE_URL))
    token = data.get("access_token") if isinstance(data, dict) else None
    if not isinstance(token, str) or not token.strip():
        fail("未登录 food4agent。打开 %s 完成授权，不要配置供应商 key。" % AUTHORIZE_URL)
    return token.strip()


def asin_from_url(url):
    match = re.search(r"/(?:dp|gp/product)/([A-Za-z0-9]{10})(?:[/?]|$)", url)
    if not match:
        return "product"
    return match.group(1).upper()


def parse_args(argv):
    parser = argparse.ArgumentParser(description="通过 food4agent 下载 Amazon 商品图片")
    parser.add_argument("--asin", help="10 位 ASIN")
    parser.add_argument("--url", help="Amazon 商品页 URL")
    parser.add_argument("--amazon-domain", default="amazon.com")
    parser.add_argument("--output", help="保存目录")
    args = parser.parse_args(argv)
    has_asin = bool(args.asin)
    has_url = bool(args.url)
    if has_asin == has_url:
        fail("必须且只能提供 --asin 或 --url。")
    if has_url:
        if not args.url.startswith("https://") or " " in args.url:
            fail("--url 必须是 https 链接。")
        label = asin_from_url(args.url)
        payload = {"type": "product", "url": args.url}
    else:
        asin = args.asin.strip().upper()
        if not ASIN_RE.fullmatch(asin):
            fail("--asin 必须是 10 位字母或数字。")
        domain = args.amazon_domain.strip().lower()
        if not DOMAIN_RE.fullmatch(domain):
            fail("--amazon-domain 不合法。")
        label = asin
        payload = {"type": "product", "asin": asin, "amazon_domain": domain}
    return args, payload, label


def request_json(url, payload, token):
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": "Bearer %s" % token,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        },
        method="POST",
    )
    try:
        with OPENER.open(request, timeout=60) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            fail("food4agent 授权无效或已过期。打开 %s 重新登录。" % AUTHORIZE_URL)
        detail = exc.read().decode("utf-8", "replace")[:300].replace(token, "***")
        fail("food4agent 请求失败：HTTP %s %s" % (exc.code, detail))
    except urllib.error.URLError as exc:
        fail("无法连接 food4agent：%s" % exc.reason)
    try:
        body = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        fail("food4agent 没有返回 JSON。")
    if not isinstance(body, dict) or not isinstance(body.get("images"), list):
        fail("food4agent 响应缺少 images。")
    return body


def image_entries(body):
    entries = []
    for item in body["images"]:
        if not isinstance(item, dict):
            fail("food4agent 返回了无法识别的图片。")
        url = item.get("url")
        if not isinstance(url, str) or not url.startswith("https://"):
            fail("图片地址必须是 https。")
        variant = item.get("variant", "")
        if not isinstance(variant, str):
            fail("图片 variant 不合法。")
        entries.append((url, VARIANT_RE.sub("", variant)[:32]))
    if not entries:
        fail("这个商品没有返回图片。")
    if len(entries) > MAX_IMAGES:
        fail("图片超过 %s 张，已停止。" % MAX_IMAGES)
    return entries


def sniff_extension(data):
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data.startswith(b"\xff\xd8"):
        return "jpg"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return "gif"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "webp"
    return None


def download(url):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with OPENER.open(request, timeout=60) as response:
            chunks = []
            total = 0
            while True:
                chunk = response.read(64 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_BYTES:
                    fail("图片超过 15MB，已停止。")
                chunks.append(chunk)
    except urllib.error.URLError as exc:
        fail("图片下载失败：%s" % exc.reason)
    data = b"".join(chunks)
    extension = sniff_extension(data)
    if not extension:
        fail("下载结果不是支持的图片。")
    return data, extension


def output_dir(args, label):
    if args.output:
        path = Path(args.output).expanduser()
        if path.exists() and any(path.iterdir()):
            fail("输出目录已存在且不为空：%s" % path)
        return path
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return Path.cwd() / "generated-images" / "amazon-images" / label / stamp


def save_all(entries, directory):
    directory.mkdir(parents=True, exist_ok=True)
    written = []
    try:
        for index, (url, variant) in enumerate(entries, start=1):
            data, extension = download(url)
            suffix = ("-%s" % variant) if variant else ""
            path = directory / ("%02d%s.%s" % (index, suffix, extension))
            path.write_bytes(data)
            written.append(path.resolve())
    except SystemExit:
        for path in written:
            path.unlink(missing_ok=True)
        raise
    return written


def main(argv):
    args, payload, label = parse_args(argv)
    token = load_token()
    body = request_json(API_URL, payload, token)
    saved = save_all(image_entries(body), output_dir(args, label))
    markdown = ["![Amazon image](<%s>)" % path.as_posix() for path in saved]
    print(json.dumps({
        "status": "completed",
        "saved_files": [str(path) for path in saved],
        "display_markdown": markdown,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

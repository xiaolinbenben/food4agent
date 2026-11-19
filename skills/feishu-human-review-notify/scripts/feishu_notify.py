#!/usr/bin/env python3
import argparse
import json
import os
import re
import socket
import urllib.request
from pathlib import Path


PROXY_ENV_KEYS = (
    "HTTPS_PROXY",
    "https_proxy",
    "HTTP_PROXY",
    "http_proxy",
    "ALL_PROXY",
    "all_proxy",
)
COMMON_PROXY_PORTS = (7879, 7897, 7890, 7899, 10809, 8080, 1080)
FEISHU_DEFAULT_PROXY_PORT = 7879


def load_env(path):
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            if "=" not in line or line.lstrip().startswith("#"):
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def normalize_proxy_url(value):
    value = value.strip()
    if not value:
        return None
    if "://" not in value:
        value = "http://" + value
    return value


def configured_proxy_url():
    for key in PROXY_ENV_KEYS:
        value = os.environ.get(key, "")
        proxy_url = normalize_proxy_url(value)
        if proxy_url:
            return proxy_url
    return None


def proxy_config_paths():
    home = Path.home()
    paths = []

    appdata = os.environ.get("APPDATA")
    if appdata:
        appdata_path = Path(appdata)
        paths.extend(
            [
                appdata_path / "Terln AI" / "proxy" / "config.yaml",
                appdata_path / "terln-ai-client" / "proxy" / "config.yaml",
                appdata_path / "io.github.clash-verge-rev.clash-verge-rev" / "config.yaml",
                appdata_path / "io.github.clash-verge-rev.clash-verge-rev" / "clash-verge.yaml",
                appdata_path / "io.github.clash-verge-rev.clash-verge-rev" / "verge.yaml",
                appdata_path / "Clash for Windows" / "config.yaml",
            ]
        )

    paths.extend(
        [
            home / ".config" / "mihomo" / "config.yaml",
            home / ".config" / "clash" / "config.yaml",
            home / ".config" / "clash-verge-rev" / "config.yaml",
            home / "Library" / "Application Support" / "io.github.clash-verge-rev.clash-verge-rev" / "config.yaml",
            home / "Library" / "Application Support" / "Clash" / "config.yaml",
        ]
    )

    seen = set()
    for path in paths:
        path_text = str(path)
        if path_text not in seen:
            seen.add(path_text)
            yield path


def configured_proxy_ports():
    pattern = re.compile(r"^(mixed-port|port)\s*:\s*([0-9]+)\s*(?:#.*)?$")
    for path in proxy_config_paths():
        if not path.exists():
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line in lines:
            match = pattern.match(line)
            if not match:
                continue
            port = int(match.group(2))
            if 0 < port <= 65535:
                yield port


def local_port_open(port):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.25):
            return True
    except OSError:
        return False


def detected_proxy_url():
    proxy_url = configured_proxy_url()
    if proxy_url:
        return proxy_url

    ports = []
    for port in configured_proxy_ports():
        if port not in ports:
            ports.append(port)
    for port in (FEISHU_DEFAULT_PROXY_PORT, *COMMON_PROXY_PORTS):
        if port not in ports:
            ports.append(port)

    for port in ports:
        if local_port_open(port):
            return f"http://127.0.0.1:{port}"

    return f"http://127.0.0.1:{FEISHU_DEFAULT_PROXY_PORT}"


def open_url(request, timeout):
    proxy_url = detected_proxy_url()
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({"http": proxy_url, "https": proxy_url})
    )
    return opener.open(request, timeout=timeout)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", required=True)
    parser.add_argument("--env", default=".env")
    args = parser.parse_args()

    load_env(args.env)
    webhook = os.environ.get("FEISHU_WEBHOOK_URL", "")
    if not webhook:
        raise SystemExit("Missing FEISHU_WEBHOOK_URL in .env")

    payload = {"msg_type": "text", "content": {"text": args.text}}

    req = urllib.request.Request(
        webhook,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with open_url(req, timeout=30) as resp:
        print(resp.read().decode("utf-8"))


if __name__ == "__main__":
    main()

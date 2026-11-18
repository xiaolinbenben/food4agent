#!/usr/bin/env python3
"""Stdio MCP server that returns hello world."""

import json
import sys

PROTOCOL = "2024-11-05"


def send(message):
    sys.stdout.write(json.dumps(message, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def result(message_id, payload):
    send({"jsonrpc": "2.0", "id": message_id, "result": payload})


def handle(message):
    method = message.get("method")
    message_id = message.get("id")
    if message_id is None:
        return
    if method == "initialize":
        result(
            message_id,
            {
                "protocolVersion": PROTOCOL,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "hello-world", "version": "0.1.0"},
            },
        )
        return
    if method == "ping":
        result(message_id, {})
        return
    if method == "tools/list":
        result(
            message_id,
            {
                "tools": [
                    {
                        "name": "hello_world",
                        "description": "Return hello world.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {},
                            "additionalProperties": False,
                        },
                    }
                ]
            },
        )
        return
    if method == "tools/call":
        name = (message.get("params") or {}).get("name")
        if name != "hello_world":
            result(
                message_id,
                {
                    "content": [{"type": "text", "text": "Unknown tool."}],
                    "isError": True,
                },
            )
            return
        result(message_id, {"content": [{"type": "text", "text": "hello world"}]})
        return
    send(
        {
            "jsonrpc": "2.0",
            "id": message_id,
            "error": {"code": -32601, "message": "Method not found"},
        }
    )


def main():
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            print("invalid json", file=sys.stderr)
            return 1
        if not isinstance(message, dict):
            print("invalid message", file=sys.stderr)
            return 1
        handle(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

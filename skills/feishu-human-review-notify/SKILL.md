---
name: feishu-human-review-notify
description: Notify human reviewers of Dianxiaomi products pending publication through a Feishu bot webhook. Use after a product has been saved and moved to pending publication to remind humans to check image compliance, title and description quality, and publishing risk.
---

# Feishu Human Review Notification

Use this skill to notify human reviewers after a product has been edited in Dianxiaomi and moved to pending publication.

## Configuration

Read the Feishu notification URL from `.env` in the workspace root:

```text
FEISHU_WEBHOOK_URL=
```

The script reads `.env` in the current directory by default. It can also be given `--env <path>`.

Proxy handling:

- The script first uses standard proxy variables from the process or `.env`: `HTTPS_PROXY`, `HTTP_PROXY`, or `ALL_PROXY`.
- If no proxy variable is configured, it reads common local Mihomo/Clash config files and uses a listening top-level `mixed-port` or `port`.
- If no config port is available, Feishu notification defaults to `http://127.0.0.1:7879`, after checking common local Mihomo/Clash ports.

## Notification Content

The notification must include at least:

- Store name.
- Platform.
- Product title.
- 1688 link.
- Dianxiaomi edit page or pending publication page link.
- Sale price.
- Items requiring human review: image compliance, title and description, and publishing risk.

## Sending Rules

- Send only after the product has been moved to pending publication.
- If `.env` in the workspace does not configure `FEISHU_WEBHOOK_URL`, do not pretend the notification was sent. Record the reason it was not sent and tell the user.
- After successful sending, record the Feishu API response.

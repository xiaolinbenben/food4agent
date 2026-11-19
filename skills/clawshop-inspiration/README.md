# 🛒 clawshop-inspiration

**ClawShop 全渠道选品商机发现路由** — 7种选品流统一入口，专为抖音小店一件代发场景设计。

## 功能

| 选品流 | 来源渠道 | 目标 |
|--------|----------|------|
| 🔍 数据流 | 抖音商机中心 | 四维全达标商品（成交/搜索增速+需供比） |
| 🎨 审美流 | 小红书 | 颜值爆款、高种草潜力商品 |
| 💰 差价流 | 淘宝/拼多多/京东 | 加价率 > 200% 的套利商品 |
| 📅 时令流 | 抖音节日热搜 | 未来15天节日/时令应季商品 |
| 💣 痛点流 | 用户评论分析 | 解决高频差评痛点的改良型商品 |
| 🌍 逆向流 | Amazon/TikTok/Etsy | 海外热销但国内未爆的蓝海商品 |
| 📹 视频流 | 抖音/快手 | 评论区求购声音强烈的带货视频商品 |

每次选品结果统一写入飞书 Bitable 候选库（状态：⏳待评估），供后续搜品铺货任务消费。

## 依赖

- [OpenClaw](https://github.com/openclaw/openclaw) Agent 运行环境
- `clawshop-data-manager` Skill（Bitable 商品候选库）
- 飞书账号 + Bitable 应用权限
- 浏览器 `profile=openclaw`（已登录抖音商机中心 / 小红书等）

## 安装

将本目录放入你的 OpenClaw workspace 的 `skills/` 目录下：

```bash
git clone https://github.com/linbojin/clawshop-inspiration skills/clawshop-inspiration
```

然后在 `openclaw.json` 的 `skills.entries` 中注册即可。

## 使用

在 Agent 对话中直接触发：

```
执行 🔍数据流
执行 💰差价流
执行 📅时令流
...
```

或配合 cron job 每日自动运行，参考 [clawshop-cronjobs](https://github.com/linbojin/clawshop-cronjobs)。

## License

MIT

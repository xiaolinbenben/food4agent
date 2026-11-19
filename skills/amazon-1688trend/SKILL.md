---
name: amazon-1688trend
description: 跨境电商热词趋势追踪 — 定时采集 1688(淘宝) 和 Amazon 热搜词，计算热度变化率，支持趋势报告和 CSV/JSON 导出
category: data-science
toolsets:
  - terminal
  - web
  - file
  - cronjob
---

# Amazon & 1688 跨境电商热词趋势追踪

> **by HomeSafe** — 实时追踪 1688(淘宝) 和 Amazon 热搜词趋势，辅助跨境电商选品决策。

## 它能做什么

这是一个 **CLI 命令行工具 + Hermes Skill**，用于从国内（1688/淘宝）和海外（Amazon）电商平台**定时采集热搜词**，存储历史数据，计算**热度变化趋势**。

- 🎯 **发现热销品类** — 1688/Amazon 上哪些关键词正在变热
- 📈 **追踪趋势变化** — 近 7 天/14 天热度升降百分比
- 🆕 **捕获新晋热词** — 哪些词刚出现在搜索热榜上
- 📊 **导出数据分析** — CSV/JSON 导出，进 Excel 或分析工具
- ⏰ **持续监控** — 后台定时采集，每天自动更新

## 快速开始（AI 引导使用）

### 1. 安装依赖

```bash
cd /path/to/amazon-1688trend
pip install -r requirements.txt
```

### 2. 手动采集一次

```bash
python3 main.py collect
```

首次运行会自动创建 `data/trends.db` 和 `config.json` 中的 `secret_key`。

### 3. 查看趋势报告

```bash
python3 main.py report
```

### 4. 导出数据

```bash
python3 main.py export --format csv
```

## 持续监控（Hermes CronJob 方式）

使用 Hermes 的 cronjob 功能实现每日自动采集。推荐两种方式：

### 方式 A：定时采集（内置 schedule）

```bash
python3 main.py schedule --interval 6
```
每 6 小时采集一次，前台运行，按 Ctrl+C 停止。

### 方式 B：Hermes CronJob（推荐）

用 cronjob 创建每日自动采集任务：

```bash
# 每天 UTC 0 点、6 点、12 点、18 点采集
crontab -e
# 添加：
0 */6 * * * cd /path/to/amazon-1688trend && python3 main.py collect >> data/cron.log 2>&1
```

或者在 Hermes 中设置 cronjob：

```text
/hermes cron every 6h "cd /path/to/amazon-1688trend && python3 main.py collect"
/hermes cron report "cd /path/to/amazon-1688trend && python3 main.py report --rising --limit 10"
```

## 命令参考

```text
collect    手动采集热词数据
report     生成趋势报告
export     导出数据 (CSV/JSON)
schedule   启动定时采集
```

### collect — 手动采集

```bash
python3 main.py collect              # 采集全部平台
python3 main.py collect --platform 1688   # 仅 1688
python3 main.py collect --platform amazon # 仅 Amazon
```

### report — 趋势报告

```bash
python3 main.py report                       # 近 7 天
python3 main.py report --days 14             # 近 14 天
python3 main.py report --platform amazon     # 仅 Amazon
python3 main.py report --rising --limit 10   # 仅升温词 TOP 10
```

### export — 导出数据

```bash
python3 main.py export --format csv
python3 main.py export --format json --days 14 --platform amazon
```

## 数据来源

| 平台 | 数据源 | 说明 |
|------|--------|------|
| **1688/淘宝** | Taobao Suggest API | 搜索自动补全词 + 搜索量 |
| **Amazon** | Amazon Autocomplete API | 实时搜索推荐词 |
| **Amazon** | Movers & Shakers 飙升榜 | 商品标题关键词提取 |

## 配置

编辑 `config.json`：

- `collector.interval_hours` — 定时采集间隔（默认 6h）
- `1688.base_seed_keywords` — 1688/淘宝的种子关键词
- `amazon.base_seed_keywords` — Amazon 的种子关键词
- `amazon.domain` — Amazon 站点域名（com/co.uk/de/jp 等）

## 数据模型

```text
keywords 表                daily_stats 表
┌──────────────┐          ┌───────────────┐
│ id           │◄────────┤ keyword_id    │
│ platform     │          │ date          │
│ keyword      │          │ frequency     │
│ source       │          │ meta (JSON)   │
│ first_seen   │          └───────────────┘
│ last_seen    │
└──────────────┘
```

## 趋势算法

```
当前热度 = 近 X 天的 frequency 总和
历史热度 = 前 X 天的 frequency 总和
变化率(%) = (当前 - 历史) / 历史 × 100
```

正数 = 升温，负数 = 降温。首次出现（近 X 天内）标记为 🆕 新词。

---

> Made by **HomeSafe** · 2026 · GitHub: https://github.com/HomeSafe2017

# Amazon & 1688 跨境电商热词趋势追踪

> **by HomeSafe** — 实时追踪 1688(淘宝) 和 Amazon 热搜词趋势，辅助跨境电商选品决策。
>
> GitHub: [https://github.com/HomeSafe2017/amazon-1688trend](https://github.com/HomeSafe2017/amazon-1688trend)

```text
  ╔═══════════════════════════════════════╗
  ║   跨境电商热词趋势追踪系统 v1.0        ║
  ║   by HomeSafe                          ║
  ╚═══════════════════════════════════════╝
  📡 跨平台 (1688 + Amazon)   🗄️ SQLite
  🔑 一键运行，零配置
```

## 它能做什么

这是一个 **CLI 命令行工具**，用于从国内（1688/淘宝）和海外（Amazon）电商平台 **定时采集热搜词**，存储历史数据，计算 **热度变化趋势**，辅助跨境电商选品决策。

你可以用它来：

- 🎯 **发现热销品类** — 1688/Amazon 上哪些关键词正在变热
- 📈 **追踪趋势变化** — 近 7 天/14 天热度升降百分比
- 🆕 **捕获新晋热词** — 哪些词刚出现在搜索热榜上
- 📊 **导出数据分析** — CSV/JSON 导出，进 Excel 或分析工具
- ⏰ **持续监控** — 后台定时采集，每天自动更新

## 快速开始

### 安装

```bash
# 1. 克隆项目
git clone https://github.com/HomeSafe2017/amazon-1688trend.git
cd amazon-1688trend

# 2. 安装依赖
pip install -r requirements.txt
```

### 使用

```bash
# 一键采集（1688 + Amazon）
python3 main.py collect

# 查看趋势报告
python3 main.py report

# 只显示 Amazon 升温词 TOP 10
python3 main.py report --platform amazon --rising --limit 10

# 导出 CSV
python3 main.py export --format csv
```

## 🤖 给 AI Agent 的一键安装引导

如果你想让你用的 AI 编程助手（如 Claude Code、Cursor、Hermes Agent 等）自动安装并使用本工具，请将以下内容复制给 AI：

> ---
>
> **你好！请安装 amazon-1688trend 技能。按以下步骤操作：**
>
> 1. 克隆仓库：`git clone https://github.com/HomeSafe2017/amazon-1688trend.git`
> 2. 安装依赖：`pip install -r requirements.txt`
> 3. 读取项目中的 `SKILL.md` 了解完整功能和使用方式
> 4. （可选）如果是 Hermes Agent，执行：
>    ```bash
>    mkdir -p ~/.hermes/skills/amazon-1688trend
>    cp amazon-1688trend/SKILL.md ~/.hermes/skills/amazon-1688trend/SKILL.md
>    ```
> 5. 运行 `python3 main.py collect` 验证安装
> 6. 设置定时采集（建议每 6 小时一次）：
>    ```bash
>    crontab -e
>    # 添加：0 */6 * * * cd /path/to/amazon-1688trend && python3 main.py collect
>    ```
>
> 完成后给我一个确认信息。

> ---

## 输出效果

### 采集

```text
  🔄 采集 [1688] 热词...
  ✅ [1688] 完成: 发现 50 个关键词

  🔄 采集 [amazon] 热词...
  ✅ [amazon] 完成: 发现 50 个关键词
```

### 趋势报告

```text
============================================================
  📊 1688 热词趋势报告 (近 7 天)
============================================================
  # 关键词                              热度      变化率 来源             新词
────────────────────────────────────────────────────────────
  1 女装套装                            177      +100.0% 🔥 suggestion     🆕
  2 男装春装                            165      +100.0% 🔥 suggestion     🆕
  ...
────────────────────────────────────────────────────────────
  共 15 个热词
  🔥 变化率 >+50%  ↑ 变化率 >+20%  → 平稳  ↓ 下降 >20%
  🆕 新词（首次出现在近 7 天内）
```

**注意**：首次运行所有词显示 `+100% 🔥` 是正常的——因为只有单次数据，没有历史对比。**连续运行 2 天以上**就能看到真实的升降趋势。

## 数据来源

| 平台 | 数据源 | 采集内容 | 可靠性 |
|------|--------|----------|--------|
| **1688/淘宝** | [Taobao Suggest API](https://suggest.taobao.com/sug) | 搜索自动补全词 + 搜索量 | ⭐⭐⭐⭐⭐ 含搜索量权重 |
| **Amazon** | [Amazon Autocomplete API](https://completion.amazon.com/api/2017/suggestions) | 实时搜索推荐词 | ⭐⭐⭐⭐ 无需渲染 |
| **Amazon** | [Movers & Shakers](https://www.amazon.com/gp/movers-and-shakers) | 飙升榜商品标题关键词 | ⭐⭐⭐ 服务端渲染可解析 |

### 为什么不用 1688 官方接口

1688 的 `suggest.1688.com/sug` 接口**已失效**（返回 404）。我们改用同属阿里系的**淘宝建议 API**（`suggest.taobao.com/sug`），效果更好——直接返回 **关键词 + 搜索量数值**。

## 命令参考

### `collect` — 手动采集

```bash
python3 main.py collect [--platform {1688,amazon,all}]
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--platform` | 采集平台 | `all` |

### `report` — 趋势报告

```bash
python3 main.py report [--days N] [--platform {1688,amazon,all}] [--limit N] [--rising]
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--days` | 分析近 N 天趋势 | `7` |
| `--platform` | 平台筛选 | `all` |
| `--limit` | 显示前 N 个热词 | `20` |
| `--rising` | 只显示升温词 | 不启用 |

### `export` — 导出数据

```bash
python3 main.py export [--format csv|json] [--days N] [--platform {1688,amazon,all}] [--output PATH]
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--format` | 导出格式 | `csv` |
| `--days` | 导出近 N 天数据 | `7` |
| `--platform` | 平台筛选 | `all` |
| `--output` | 输出文件路径 | 自动生成 |

### `schedule` — 定时采集

```bash
python3 main.py schedule [--interval N]
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--interval` | 采集间隔（小时） | `config.json` 中的值（默认 6h） |

启动后会立即执行一次，然后按间隔循环。按 `Ctrl+C` 停止。

## 配置

所有可变配置集中在 `config.json`，不需要修改代码：

```json
{
  "collector": {
    "interval_hours": 6,
    "request_delay": 2,
    "max_retries": 3,
    "timeout": 30
  },
  "1688": {
    "enabled": true,
    "base_seed_keywords": ["女装", "男装", "电子产品", "家居", ...],
    "max_keywords_per_run": 50
  },
  "amazon": {
    "enabled": true,
    "domain": "com",
    "base_seed_keywords": ["clothing", "electronics", "home", ...],
    "max_keywords_per_run": 50
  }
}
```

| 配置项 | 说明 |
|--------|------|
| `collector.interval_hours` | 定时采集间隔（小时） |
| `collector.request_delay` | 每次请求间延迟（秒） |
| `1688.base_seed_keywords` | 1688/淘宝的种子关键词 |
| `amazon.base_seed_keywords` | Amazon 的种子关键词 |
| `amazon.domain` | Amazon 站点域名（com/co.uk/de/jp 等） |

## 架构

```
amazon-1688trend/
├── SKILL.md                    # Hermes Agent skill 定义
├── README.md                   # 本文件
├── main.py                     # CLI 入口
├── config.json                 # 所有可变配置
├── requirements.txt            # 依赖
├── history.md                  # 开发记录
├── .gitignore
├── src/
│   ├── collector_base.py       # 采集器基类（HTTP、重试、延迟）
│   ├── collector_1688.py       # 1688/淘宝热搜词采集器
│   ├── collector_amazon.py     # Amazon 热搜词采集器
│   ├── database.py             # SQLite 存储与查询
│   ├── analyzer.py             # 趋势分析与导出
│   └── scheduler.py            # 定时调度器
└── data/
    └── trends.db               # SQLite 数据库（自动创建）
```

### 数据模型

```text
keywords 表                daily_stats 表             collection_log 表
┌──────────────┐          ┌───────────────┐          ┌──────────────────┐
│ id           │◄────────┤ keyword_id    │          │ id               │
│ platform     │          │ date          │          │ platform         │
│ keyword      │          │ rank          │          │ started_at       │
│ source       │          │ frequency     │          │ finished_at      │
│ first_seen   │          │ meta (JSON)   │          │ keywords_found   │
│ last_seen    │          └───────────────┘          │ status           │
└──────────────┘                                     └──────────────────┘
```

## 与开源竞品对比

| 项目 | 平台 | 数据质量 | 维护状态 | 趋势分析 |
|------|------|----------|----------|----------|
| **本工具** | 1688/淘宝 + Amazon | ⭐⭐⭐⭐ | ✅ 活跃 | ✅ 有 |
| yuangyu9507/crawler | 仅 1688 | ⭐⭐（接口已死） | ❌ 未维护 | ❌ |
| LSCLWH/Crawl_Hotsearch | 多平台聚合 | ⭐⭐⭐ | ❌ 低活跃 | ❌ |
| 商业工具 | 单一平台 | ⭐⭐⭐⭐⭐ | ✅ | ✅（付费） |

**本工具的核心优势**：免费 + 跨平台（1688+Amazon）+ 历史趋势可追踪 + 数据自主可控。

## 路线图

- [x] CLI 热词采集（1688 + Amazon）
- [x] SQLite 本地存储
- [x] 趋势报告（变化率 + 新词检测）
- [x] CSV/JSON 导出
- [x] 定时自动采集
- [x] Hermes Agent Skill 封装
- [ ] Web Dashboard 可视化
- [ ] 微信/Telegram 每日热词推送
- [ ] 更多平台（TikTok Shop、拼多多）
- [ ] 关键词竞争度分析
- [ ] 多站点 Amazon 支持（de/jp/uk）

## 开发说明

### 作者偏好

- 所有可变配置集中在 `config.json`
- `secret_key` 首次启动自动生成
- 服务器 IP 自动检测，不写死
- Python 3 开发
- Git 版本管理
- 代码标注 **by HomeSafe**

### 环境

```bash
Python 3.12+
Linux / macOS / WSL
```

---

> Made by **HomeSafe** · 2026 · GitHub: [https://github.com/HomeSafe2017](https://github.com/HomeSafe2017)
>
> *如果你觉得这个工具有用，欢迎 ⭐ Star 支持！*

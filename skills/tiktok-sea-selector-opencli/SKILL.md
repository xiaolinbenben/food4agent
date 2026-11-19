---
name: tiktok-sea-selector-opencli
description: 东南亚跨境选品信号采集与候选品评分 Agent。通过 OpenCLI 复用本机 Chrome 登录态，从 TikTok / Amazon / 1688 / Reddit / 小红书 / Google Trends 等平台采集真实市场信号，按 quick/standard/deep 三档运行，生成结构化候选产品并通过 HTTP 上报到平台。触发场景：爆款发现、市场情绪、竞品饱和度分析、供应链定价、定时数据同步。
---

# TikTok 东南亚选品 Agent Skill

> **定位：** 一个**可调度的本地数据采集 Agent**。优先复用 OpenCLI + 本机 Chrome 登录态；当 OpenCLI 不覆盖关键数据源时，也允许直接使用 Agent 自身能力访问目标站点或 API，完成后通过 HTTP POST 把结果上报到平台。

当前输出分为两层：

- `products`：完整候选池，用于数据库留存和前端列表展示
- `top_picks`：按可信度和潜力排序后的 top 10，用于回答“今天可以选什么、为什么”

## 架构总览

```
Manus Schedule 触发 → 本机 Agent (sea_product_agent.py)
                          ├─ OpenCLI（TikTok / Amazon / 1688 / Reddit / 小红书 / Google / …）
                          └─ Agent 自身能力（站点访问 / API / 浏览器自动化）
                                    ↓
                       候选品结构化 + 评分
                                    ↓
                        POST /api/trpc/dataSync.recordRun → 平台 DB → 前端
```

**工具策略：**

- **OpenCLI** — 内置 76+ 平台适配器（含 TikTok、Amazon、1688、Reddit、小红书、Google 等），通过 Browser Bridge Chrome 扩展连接本机 Chrome。
- **Agent 自身能力** — 当关键数据源缺失或 OpenCLI 适配受限时可直接补齐，例如站内搜索页、公开 API、浏览器自动化访问。

### 数据源能力矩阵

> 按工具实际可用性标注。详见 `references/data-sources.md`。

| 数据源                | 命令                                                     | 适配器状态 | 用于模式  |
| --------------------- | -------------------------------------------------------- | ---------- | --------- |
| Google Trends         | `opencli google trends`                                  | 内置 ✅    | quick+    |
| Google News           | `opencli google news`                                    | 内置 ✅    | quick+    |
| TikTok 搜索/探索      | `opencli tiktok search/explore`                          | 内置 ✅    | standard+ |
| Amazon 畅销/飙升/新品 | `opencli amazon bestsellers/movers-shakers/new-releases` | 内置 ✅    | deep      |
| 1688 供货搜索         | `opencli 1688 search/item`                               | 内置 ✅    | deep      |
| Reddit 情绪           | `opencli reddit search`                                  | 内置 ✅    | deep      |
| 小红书                | `opencli xiaohongshu search`                             | 内置 ✅    | deep      |
| 其他电商/站内结果页   | OpenCLI 或 Agent 自身能力                                | 按实际实现 | 按需扩展  |

**说明：** 不要把 Skill 限制在 OpenCLI 适配器覆盖范围内。若 OpenCLI 无稳定适配器，应优先评估 Agent 自身能力是否可以直接访问目标数据，再决定是否补 OpenCLI 自建适配器。

### 可选扩展数据源（OpenCLI 内置但本 Skill 尚未集成）

| 平台      | 命令                              | 选品价值         |
| --------- | --------------------------------- | ---------------- |
| 淘宝      | `opencli taobao search/item`      | 国内竞品定价     |
| 京东      | `opencli jd search/item`          | 品牌正品价格     |
| 闲鱼      | `opencli xianyu search/item`      | 二手市场热度     |
| Coupang   | `opencli coupang search`          | 韩国电商对标     |
| 抖音      | `opencli douyin search/explore`   | 国内趋势先行指标 |
| Twitter/X | `opencli twitter trending/search` | 欧美社媒情绪     |

> 运行 `opencli list` 查看全部可用适配器；运行 `opencli <platform> --help` 获取具体参数。

---

## 环境与登录

| 工具                    | 安装                          | 连接方式                   |
| ----------------------- | ----------------------------- | -------------------------- |
| Node ≥ 18, Python ≥ 3.9 | 系统包管理器                  | —                          |
| OpenCLI ≥ 1.6.9         | `npm i -g @jackwener/opencli` | Browser Bridge Chrome 扩展 |

### 连接方式

**Browser Bridge Chrome 扩展**

从 [OpenCLI Releases](https://github.com/jackwener/OpenCLI/releases) 下载 Chrome 扩展，在 `chrome://extensions` 开发者模式加载。OpenCLI 通过此扩展连接本机 Chrome 的登录态。

验证连接：

```bash
opencli doctor   # 应显示 "connected"
```

### 站点登录

需要在浏览器中**预先登录一次**（Cookie 持久化后定时任务自动复用）：

| 站点   | 模式要求                   | 登录地址        |
| ------ | -------------------------- | --------------- |
| TikTok | standard+                  | tiktok.com      |
| Amazon | deep                       | amazon.com      |
| 小红书 | deep                       | xiaohongshu.com |
| Reddit | deep                       | reddit.com      |
| 1688   | deep（需 OpenCLI ≥ 1.6.9） | 1688.com        |

若某数据源改由 Agent 自身能力直连，则按该实现选择：

- 复用本机浏览器 Cookie
- 使用站点公开 API
- 使用无登录页面抓取
- 使用专门服务账号/密钥

### 启动自检

脚本启动时会自动检查 OpenCLI 连通性和各站点登录状态（按当前运行模式检测所需平台）。
探测顺序是：

- 优先尝试轻量命令（如 `auth status` / `status` / `--help`）
- 只有无法得到结论时，才回退到最小真实请求

```bash
python scripts/sea_product_agent.py --mode deep --categories beauty --countries ID
# 输出示例：
# ╭─ 环境自检 ──────────────────────────────╮
# │ OpenCLI 版本     : ✅ 1.6.9              │
# │ Browser Bridge   : ✅ 已连接             │
# │ TikTok           : ✅ 已登录             │
# │ Amazon           : ✅ 已登录             │
# │ Reddit           : ✅ 已登录             │
# │ 小红书           : ❌ 未登录 → 请在 Chrome 中登录对应站点 │
# │ 1688             : ⚠️  适配器不可用（需 OpenCLI ≥ 1.6.9）│
# ╰─────────────────────────────────────────╯
```

若你已经确认本机环境稳定，可跳过自检以减少真实探测请求：

```bash
python scripts/sea_product_agent.py --mode deep --skip-preflight
```

## 运行模式

| 模式       | 数据源                              | 耗时    | 登录要求                        |
| ---------- | ----------------------------------- | ------- | ------------------------------- |
| `quick`    | Google Trends + Google News（5 国） | ~3 min  | 信号收集，不保证产出 `products` |
| `standard` | + TikTok 搜索/探索                  | ~8 min  | TikTok Chrome 登录              |
| `deep`     | + Amazon + 1688 + Reddit + 小红书   | ~20 min | 全部 Chrome 登录                |

## 快速开始

```bash
# 1. 公开数据，无需登录
python scripts/sea_product_agent.py --mode quick

# 2. 标准采集 + 上报
python scripts/sea_product_agent.py --mode standard --write-db \
  --platform-url https://your-platform.example.com

# 3. 深度全量
python scripts/sea_product_agent.py --mode deep \
  --categories beauty,fashion,home --countries ID,TH,VN --write-db
```

环境变量：

- `SEA_PLATFORM_URL` — 默认平台地址
- `SEA_DATA_DIR` — 本地数据/日志目录（默认 `~/.sea_data`）
- `PLATFORM_SERVICE_TOKEN` — 可选；如远端平台启用鉴权，则作为 Bearer Token 注入上报请求

## 命令速查（关键陷阱）

> 完整参数和字段定义见 **`references/data-sources.md`**。
> 运行时发现参数：`opencli <platform> <subcommand> --help`

1. **关键词永远是位置参数**，不要写 `--query` / `--keyword` / `--geo`。
2. **`opencli google trends` 不接受关键词**，只有 `--region` 和 `--limit`。
3. **输出格式统一用 `-f json`**。
4. **Amazon bestsellers 用分类路径**（如 `/gp/bestsellers/beauty/`），不用 `--category`。
5. **若要减少站点探测痕迹**，可使用 `--skip-preflight` 跳过启动自检。

## Manus 调度建议

| 频率         | Cron           | 模式     |
| ------------ | -------------- | -------- |
| 每日 08:00   | `0 0 8 * * *`  | quick    |
| 每日 20:00   | `0 0 20 * * *` | standard |
| 每周一 06:00 | `0 0 6 * * 1`  | deep     |

调度 Prompt 模板：

```
请加载 tiktok-sea-selector-opencli Skill，以 {mode} 模式运行
sea_product_agent.py，目标国家 ID/TH/VN/PH/MY，品类
beauty/fashion/home/electronics/health，结果上报到 {PLATFORM_URL}。
```

## 数据上报 API

```
POST {PLATFORM_URL}/api/trpc/dataSync.recordRun
Content-Type: application/json

{ "json": { "runId": "...", "mode": "...", "status": "success",
             "categories": [...], "countries": [...],
             "summary": {...},
             "products": [
               {
                 "name": "...",
                 "category": "beauty",
                 "country": "ID",
                 "price": 12.9,
                 "salesVolume": 1200,
                 "salesGrowthRate": 18.5,
                 "gmv": 15480,
                 "competitionScore": 62,
                 "sentimentScore": 71,
                 "potentialScore": 78,
                 "searchGrowthRate": 24,
                 "sellerCount": 15,
                 "priceMin": 8.9,
                 "priceMax": 15.9,
                 "tags": ["tiktok", "amazon", "1688"],
                 "isHot": true,
                 "isTrending": true,
                 "source": "agent"
               }
             ] } }
```

详见 `references/platform-integration.md`。

## 故障排查

| 症状                              | 根因                  | 处理                  |
| --------------------------------- | --------------------- | --------------------- |
| `too many arguments for 'trends'` | 给 trends 传了关键词  | 只传 `--region`       |
| `unknown option '--query'`        | 不存在的 flag         | 关键词写位置参数      |
| `opencli doctor` 未连接           | Chrome 扩展未启用     | 重装 Browser Bridge   |
| 数据返回空                        | Chrome 未登录对应站点 | 在 Chrome 手动登录    |
| 平台上报失败                      | URL/Token 错误        | 检查 `--platform-url` |
| 沙盒无法连接 Chrome               | 网络隔离              | 必须在本机运行        |

## 实现原则

1. 不要把 Skill 限定为“只能调用 OpenCLI”。
2. 对每个数据源，优先选择最稳定、最低维护成本的方式：
   - OpenCLI 现成适配器
   - Agent 自身直接访问能力
   - 必要时自建适配器
3. 对任何关键数据源，若 Agent 自身能力能直接获取，优先以业务价值为准，不必等待 OpenCLI 覆盖。
4. 不要为单一来源单独设计平台字段；只定义“如何提取原始数据”，平台字段统一在公共归一化层处理。
5. `custom_source` 的定位是“外部数据注入口”，用于把额外抓取结果接入当前结构化评分链路，而不是单独维护一套平台字段。

## 信任分层

每条候选产品都会附带 `trustLevel` 与 `salesSource`，用于区分“真实销量”和“代理信号”：

- `official`：官方或直接来源的真实销量
- `verified`：可信外部来源或人工注入快照
- `proxy`：互动量、搜索热度、评论量等代理值

`whyPicked` 会基于这些字段生成确定性的解释文案，帮助快速判断“为什么推荐这条”。

## 上游参考（渐进式披露）

运行时不确定命令参数？优先用 CLI 自身的帮助系统，而非翻阅本文档：

```bash
opencli list                              # 列出所有可用适配器
opencli <platform> --help                 # 查看子命令
opencli <platform> <subcommand> --help    # 查看具体参数
```

上游文档（本 Skill 命令参考的权威来源）：

- OpenCLI 适配器文档：[docs/adapters/browser/](https://github.com/jackwener/OpenCLI/tree/main/docs/adapters/browser)
- 本 Skill 已验证的命令组合：`references/data-sources.md`

## Skill 内文件

| 文件                                 | 作用                                           |
| ------------------------------------ | ---------------------------------------------- |
| `scripts/sea_product_agent.py`       | 主 Agent 脚本（quick/standard/deep）           |
| `scripts/sync_to_platform.py`        | 单品类按需同步到平台                           |
| `references/data-sources.md`         | 已验证的命令参数 + 输出字段 + 自建适配器指南   |
| `references/ai-analysis-prompt.md`   | AI 选品分析 Prompt 模板（含当前/未来字段说明） |
| `references/platform-integration.md` | 平台 tRPC API 集成                             |

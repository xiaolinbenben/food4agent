# 与 tiktok-sea-selector 平台集成指南

## 架构概述

```
OpenCLI
        │
        │ 采集真实市场数据
        ▼
sea_product_agent.py（本 Skill 的 Agent 脚本）
        │
        │ HTTP POST（JSON）
        ▼
tiktok-sea-selector Web 平台（tRPC API）
        │
        │ 存储到 MySQL 数据库
        ▼
前端展示（仪表盘、爆款榜单、趋势图表等）
```

---

## tRPC API 端点

平台运行在 `http://localhost:3000`（开发环境）。

### Agent 主写入入口

**端点：** `POST /api/trpc/dataSync.recordRun`

Agent 通过一次调用同时写入：

- `agentRuns` 运行记录
- `products` 结构化候选产品列表

**请求体（JSON）：**

```json
{
  "json": {
    "runId": "2026-04-10_20-00-00",
    "mode": "deep",
    "status": "success",
    "categories": ["beauty"],
    "countries": ["ID"],
    "summary": {
      "candidateProducts": 12,
      "topPotentialScore": 82,
      "outputFile": "/Users/name/.sea_data/runs/run_2026-04-10_20-00-00.json"
    },
    "products": [
      {
        "name": "防晒霜 SPF50",
        "nameEn": "Sunscreen SPF50",
        "category": "beauty",
        "country": "ID",
        "imageUrl": "https://...",
        "price": 12.99,
        "salesVolume": 15420,
        "salesGrowthRate": 34,
        "gmv": 200365.8,
        "competitionScore": 65,
        "sentimentScore": 82,
        "potentialScore": 78,
        "searchGrowthRate": 41,
        "sellerCount": 18,
        "priceMin": 9.99,
        "priceMax": 15.99,
        "tags": ["防晒", "美妆", "夏季"],
        "isHot": true,
        "isTrending": true,
        "source": "agent"
      }
    ]
  }
}
```

### 当前服务端已存在的读取端点

- `GET/POST /api/trpc/dataSync.runHistory`
- `GET/POST /api/trpc/dataSync.getSchedule`
- `GET/POST /api/trpc/products.list`
- `GET/POST /api/trpc/products.getById`
- `GET/POST /api/trpc/products.hotList`
- `GET/POST /api/trpc/products.trendingList`

### 当前不存在的 Agent 写入端点

当前平台服务端没有以下端点，Skill 不应依赖它们：

- `products.upsert`
- `aiRecommendations.create`

如需 Agent 自动写入自然语言报告，需要未来新增专用 ingestion API。

---

## 数据字段映射

将 OpenCLI 采集的原始数据映射到平台数据库字段：

| 平台字段           | 数据来源                         | 采集命令                                               |
| ------------------ | -------------------------------- | ------------------------------------------------------ |
| `salesVolume`      | TikTok/Amazon 热度代理值         | `opencli tiktok search` / `opencli amazon bestsellers` |
| `salesGrowthRate`  | TikTok/News/Trends 增长代理值    | `opencli tiktok search` / `opencli google news`        |
| `competitionScore` | Amazon/1688 供给密度归一化       | `opencli amazon bestsellers` / `opencli 1688 search`   |
| `sentimentScore`   | 评论正负面比例 × 100             | 评论文本分析                                           |
| `potentialScore`   | 利润空间 + 趋势 + 竞争度综合评分 | 多源计算                                               |
| `searchGrowthRate` | Google News/Trends 热度代理值    | `opencli google trends` / `opencli google news`        |

**归一化公式：**

```python
# competitionScore：卖家数越少，分数越高
competition_score = max(0, 100 - seller_count * 2)

# trendScore：Google Trends 指数直接使用（0–100）
trend_score = google_trends_value

# sentimentScore：正面评论比例 × 100
sentiment_score = positive_count / total_count * 100
```

---

## 认证

当前本机服务模式下，Agent 可直接调用本地平台接口，无需额外 Token。

如未来部署到远端平台，或服务端启用鉴权，可通过 `PLATFORM_SERVICE_TOKEN` 自动附加 Bearer Token：

```python
headers = {
    "Authorization": f"Bearer {os.environ['PLATFORM_SERVICE_TOKEN']}",
    "Content-Type": "application/json"
}
```

当前代码库的 `dataSync.recordRun` 默认不校验该 Token；若环境变量存在，Agent 会附加 `Authorization` 头，但服务端是否校验由部署侧决定。

---

## 定时同步

配置 cron 任务每日自动同步最新数据：

```bash
# 每天凌晨 2 点（东南亚时区 UTC+7）同步数据
0 19 * * * python /home/ubuntu/skills/tiktok-sea-selector-opencli/scripts/sync_to_platform.py \
  --platform-url "https://your-app.manus.space" \
  --categories "beauty,fashion,home,electronics,baby" \
  --countries "ID,TH,VN,PH,MY" \
  >> /var/log/sea-sync.log 2>&1
```

---

## 错误处理

| 错误码     | 原因           | 处理方式                                            |
| ---------- | -------------- | --------------------------------------------------- |
| 401        | Token 无效     | 检查或刷新 PLATFORM_SERVICE_TOKEN（仅远端鉴权场景） |
| 429        | 请求频率过高   | 添加 `time.sleep(1)` 限速                           |
| 500        | 服务器错误     | 检查服务端控制台日志                                |
| TRPC_ERROR | 数据格式不匹配 | 检查字段类型（price 需为 float，非 string）         |

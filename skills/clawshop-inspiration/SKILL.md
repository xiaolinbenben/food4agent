---
name: clawshop-inspiration
description: 电商选品全渠道商机发现路由。7种选品流统一入口：数据流/审美流/差价流/时令流/痛点流/逆向流/视频流。 触发词：执行选品、发现商机、数据流/审美流/差价流/时令流/痛点流/逆向流/视频流。
---

# clawshop-inspiration · 商机发现总路由

> 全渠道选品 · 7流合一 · 统一入库

---

## 🚨 全局铁律（每次必须遵守）

| 规则 | 说明 |
|------|------|
| Bitable读写 | 只用 `feishu_bitable_*` 工具函数，禁止自己拼 curl |
| 主字段名 | 由 `clawshop-data-manager` 建表时配置，见 `references/bitable.md` |
| 浏览器 | `profile=openclaw`，禁止 `profile=chrome` |
| 入库确认 | 必须确认返回的 `record_id` 存在才算成功 |
| 状态值 | 只允许 7 个合法候选状态（见 `references/bitable.md`） |


---

## 🚀 Bootstrap（每次必须先执行，再做任何事）

**Step 1：读取 Bitable token**

```
gateway config.get path=skills.entries.clawshop-data-manager.env
→ 取 CLAWSHOP_APP_TOKEN 和 CLAWSHOP_TABLE_ID
```

> ⚠️ `echo $CLAWSHOP_APP_TOKEN` 在隔离 session 中读不到，必须用 gateway 接口获取。

**Step 2：校验连通性**

调用 `feishu_bitable_list_fields(app_token, table_id)`：
- ✅ 返回字段列表 → 继续
- ❌ 报错 / token 为空 → 按 `clawshop-data-manager/SKILL.md` 重建表后继续

---

## 🗺️ 流程路由

收到「执行 [X流]」指令时，按以下顺序执行：

```
Bootstrap
  → read {skillDir}/references/flows/[X流].md
  → 执行该流的商机发现逻辑（产出候选商品列表）
  → Bitable 入库（统一格式，见下）
  → 汇报（统一格式，见下）
  → 经验沉淀（append 到 memory/clawshop-learnings.md）
```

**支持的流：**

| 流名 | 参考文件 | 来源渠道 |
|------|----------|---------|
| 🔍数据流 | `references/flows/数据流.md` | 抖音商机中心 |
| 🎨审美流 | `references/flows/审美流.md` | 小红书 |
| 💰差价流 | `references/flows/差价流.md` | 淘宝/拼多多/京东 |
| 📅时令流 | `references/flows/时令流.md` | 抖音节日热搜 |
| 💣痛点流 | `references/flows/痛点流.md` | 用户评论分析 |
| 🌍逆向流 | `references/flows/逆向流.md` | Amazon/TikTok |
| 📹视频流 | `references/flows/视频流.md` | 抖音/快手 |

---

## 📝 统一 Bitable 入库格式

每件商品调用 `feishu_bitable_create_record(app_token, table_id, fields)`。

> ⚠️ 主字段名以 `feishu_bitable_list_fields` 返回的第一个 `is_primary: true` 字段为准，见 `references/bitable.md`。

**必填字段：**

```json
{
  "<主字段名>": "商品名（主字段，必须）",
  "候选状态": "⏳待评估",
  "来源方法": "🔍数据流",
  "来源渠道": "抖音商机中心",
  "记录日期": 1700000000000
}
```

**选填字段（按流程补充）：**

```json
{
  "评估备注": "供应商信息 / 商机四维 / 差价数据 / 痛点描述 等"
}
```

字段类型和合法值 → `{skillDir}/references/bitable.md`

---

## 📊 统一汇报格式

```
[Emoji]流名 选品完成 · YYYY-MM-DD
- 候选商品：X件
- 入库成功：X件（record_id 已确认）
- 失败/跳过：X件（原因）
- [流程特有补充]
```

---

## 📚 经验沉淀（每次完成后必须执行）

回顾本次选品，精炼 2-3 条有数据支撑的经验，append 到：
`memory/clawshop-learnings.md`

# 数据源命令参考

> **原则：** 本文件只记录经过实机验证的命令组合。参数有疑问时，优先运行
> `opencli <platform> <subcommand> --help` 获取当前版本的权威帮助。
>
> 上游文档：
>
> - OpenCLI 适配器：https://github.com/jackwener/OpenCLI/tree/main/docs/adapters/browser

---

## 一、Google Trends（OpenCLI · 无需登录）

```bash
opencli google trends [options] -f json
```

**⚠️ 关键限制：`google trends` 不接受关键词位置参数！只返回该国当日热搜榜。**

| 参数          | 类型 | 说明                          |
| ------------- | ---- | ----------------------------- |
| `--region CC` | 选项 | 国家代码（ID/TH/VN/PH/MY 等） |
| `--limit N`   | 选项 | 返回条数                      |

```bash
# ✅ 正确
opencli google trends --region ID --limit 20 -f json

# ❌ 错误（会报 too many arguments）
opencli google trends skincare --limit 5
opencli google trends --query skincare
opencli google trends --geo ID
```

**输出字段：** `title`, `traffic`, `date`

---

## 二、Google News（OpenCLI · 无需登录）

```bash
opencli google news [keyword] [options] -f json
```

| 参数          | 类型             | 说明                     |
| ------------- | ---------------- | ------------------------ |
| `keyword`     | 位置参数（可选） | 直接写，**不加 --query** |
| `--region CC` | 选项             | 国家代码                 |
| `--lang en`   | 选项             | 语言代码                 |
| `--limit N`   | 选项             | 返回条数                 |

```bash
# ✅ 正确
opencli google news "skincare viral tiktok" --region ID --lang en --limit 10 -f json
opencli google news --limit 10 -f json   # 不加关键词 = 全球头条
```

**输出字段：** `title`, `source`, `date`, `url`

---

## 三、TikTok（OpenCLI · 需 Browser Bridge + Chrome 登录）

```bash
opencli tiktok search <query> [--limit N] -f json
opencli tiktok explore [--limit N] -f json
```

| 参数        | 类型                        | 说明                 |
| ----------- | --------------------------- | -------------------- |
| `query`     | 位置参数（search **必填**） | 直接写，不加 --query |
| `--limit N` | 选项                        | 返回条数             |

```bash
# ✅ 正确
opencli tiktok search "skincare" --limit 20 -f json
opencli tiktok explore --limit 30 -f json

# ❌ 错误
opencli tiktok search --keyword "skincare"
opencli tiktok search --query "skincare"
```

**输出字段（search）：** `rank`, `desc`, `author`, `url`, `plays`, `likes`, `comments`, `shares`
**输出字段（explore）：** `rank`, `author`, `views`, `url`

**选品关键词策略：**

- `<品类> haul`、`<品类> review`、`<品类> unboxing`、`<品类> viral`
- 东南亚本地语言：`produk viral`（印尼）、`ของมาแรง`（泰）、`sản phẩm hot`（越南）

> 上游详细文档：[docs/adapters/browser/tiktok.md](https://github.com/jackwener/OpenCLI/tree/main/docs/adapters/browser/tiktok.md)

---

## 四、Amazon（OpenCLI · 需 Browser Bridge + Chrome 登录）

```bash
opencli amazon bestsellers [category_path] [--limit N] -f json
opencli amazon movers-shakers [category_path] [--limit N] -f json
opencli amazon new-releases [category_path] [--limit N] -f json
opencli amazon search <query> [--limit N] -f json
opencli amazon product --asin <ASIN> -f json
```

| 参数            | 类型             | 说明                                                       |
| --------------- | ---------------- | ---------------------------------------------------------- |
| `category_path` | 位置参数（可选） | 如 `/gp/bestsellers/beauty/`，**不是** `--category Beauty` |
| `--limit N`     | 选项             | 返回条数                                                   |
| `--asin`        | 选项（product）  | Amazon ASIN                                                |

```bash
# ✅ 正确
opencli amazon bestsellers /gp/bestsellers/beauty/ --limit 20 -f json
opencli amazon movers-shakers /gp/movers-and-shakers/beauty/ --limit 10 -f json
opencli amazon new-releases /gp/new-releases/beauty/ --limit 10 -f json
opencli amazon search "skincare set" --limit 20 -f json

# ❌ 错误
opencli amazon bestsellers --category Beauty   # 无 --category 参数
```

常用分类路径：

| 品类 | bestsellers 路径               |
| ---- | ------------------------------ |
| 美妆 | `/gp/bestsellers/beauty/`      |
| 服饰 | `/gp/bestsellers/apparel/`     |
| 家居 | `/gp/bestsellers/home-garden/` |
| 3C   | `/gp/bestsellers/electronics/` |
| 健康 | `/gp/bestsellers/hpc/`         |
| 母婴 | `/gp/bestsellers/baby/`        |

**输出字段（bestsellers）：** `list_type`, `rank`, `asin`, `title`, `price_text`, `rating_value`, `review_count`

> 上游详细文档：[docs/adapters/browser/amazon.md](https://github.com/jackwener/OpenCLI/tree/main/docs/adapters/browser/amazon.md)

---

## 五、1688 供货价（OpenCLI · 需 Browser Bridge + Chrome 登录）

> 1688 是供应链定价的核心数据源。利润空间 = 目标市场售价 - 1688 供货价 × 3–5（含运费/佣金/广告）。

```bash
opencli 1688 search <query> [--limit N] -f json
opencli 1688 item <item_id> -f json
```

| 参数        | 类型                        | 说明       |
| ----------- | --------------------------- | ---------- |
| `query`     | 位置参数（search **必填**） | 商品关键词 |
| `item_id`   | 位置参数（item **必填**）   | 商品 ID    |
| `--limit N` | 选项                        | 返回条数   |

```bash
# ✅ 正确
opencli 1688 search "防晒霜 SPF50" --limit 20 -f json
opencli 1688 search "wireless earbuds" --limit 20 -f json
opencli 1688 item 726534821456 -f json
```

> 上游详细文档：[docs/adapters/browser/1688.md](https://github.com/jackwener/OpenCLI/tree/main/docs/adapters/browser/1688.md)

---

## 六、Reddit（OpenCLI · 需 Browser Bridge + Chrome 登录）

```bash
opencli reddit search <query> [options] -f json
```

| 参数          | 说明                           |
| ------------- | ------------------------------ |
| `query`       | 位置参数（**必填**），直接写   |
| `--subreddit` | 限定 subreddit                 |
| `--sort`      | relevance/hot/top/new/comments |
| `--time`      | hour/day/week/month/year/all   |
| `--limit N`   | 返回条数                       |

```bash
opencli reddit search "skincare southeast asia" --sort top --time month --limit 20 -f json
```

**输出字段：** `title`, `subreddit`, `author`, `score`, `comments`, `url`

推荐 subreddit：r/AsianBeauty, r/BuyItForLife, r/indonesia, r/Thailand, r/Philippines

> 上游详细文档：[docs/adapters/browser/reddit.md](https://github.com/jackwener/OpenCLI/tree/main/docs/adapters/browser/reddit.md)

---

## 七、小红书（OpenCLI · 需 Browser Bridge + Chrome 登录）

```bash
opencli xiaohongshu search <query> [--limit N] -f json
```

| 参数        | 类型                 | 说明       |
| ----------- | -------------------- | ---------- |
| `query`     | 位置参数（**必填**） | 搜索关键词 |
| `--limit N` | 选项                 | 返回条数   |

```bash
# ✅ 正确
opencli xiaohongshu search "美妆护肤" --limit 20 -f json
opencli xiaohongshu search "东南亚爆款" --limit 20 -f json
```

**小红书作为先行指标：** 小红书爆款通常比东南亚市场早 3–6 个月，可作为趋势预判。

> 上游详细文档：[docs/adapters/browser/xiaohongshu.md](https://github.com/jackwener/OpenCLI/tree/main/docs/adapters/browser/xiaohongshu.md)

---

## 八、命令参数规律总结

| 平台               | 关键词传递                      | 输出格式  |
| ------------------ | ------------------------------- | --------- |
| Google Trends      | **无位置参数**（只 `--region`） | `-f json` |
| Google News        | 可选位置参数                    | `-f json` |
| TikTok search      | 必填位置参数                    | `-f json` |
| TikTok explore     | 无参数                          | `-f json` |
| Amazon bestsellers | 可选位置参数（分类路径）        | `-f json` |
| 1688 search        | 必填位置参数                    | `-f json` |
| Reddit search      | 必填位置参数                    | `-f json` |
| 小红书 search      | 必填位置参数                    | `-f json` |

**通用规律：**

1. 关键词永远是位置参数，不加 `--query` / `--keyword`
2. Google Trends 是唯一不接受关键词的命令
3. 所有命令统一用 `-f json` 输出 JSON

---

## 九、扩展：自建适配器（额外电商平台 / 站内结果页等）

当 OpenCLI 无内置适配器，或你需要访问额外电商平台 / 站内结果页时，可通过 OpenCLI 自动生成适配器：

```bash
# 1. 探索站点 API
opencli explore "https://shopee.co.id" --site shopee

# 2. 自动合成适配器
opencli synthesize shopee

# 3. 或一步到位：指定目标，自动生成
opencli generate "https://shopee.co.id/search?keyword=skincare" \
  --goal "extract product name, price, sold count, rating"
```

生成后即可像内置适配器一样使用：`opencli shopee search skincare -f json`

---

## 十、数据输出格式

OpenCLI 支持 `-f` 参数：

| 格式     | 参数       | 适用场景             |
| -------- | ---------- | -------------------- |
| JSON     | `-f json`  | 程序处理、数据库写入 |
| 表格     | `-f table` | 人工快速浏览（默认） |
| Markdown | `-f md`    | 报告生成             |
| CSV      | `-f csv`   | Excel 导入           |

配合 jq：

```bash
opencli amazon bestsellers /gp/bestsellers/beauty/ -f json | jq '.[] | {title, price_text}'
opencli tiktok search "skincare" -f json | jq '.[] | select(.likes > 10000)'
opencli 1688 search "防晒霜" -f json | jq '.[] | {title, price}'
```

---

## 十一、自检与轻量探测

`sea_product_agent.py` 启动时默认会执行 preflight：

- 优先尝试轻量命令，如 `opencli <platform> auth status`、`opencli <platform> status`、`opencli <platform> <subcommand> --help`
- 若轻量命令无法判断登录状态，再回退到最小真实请求

约定：

- exit code `77` 表示“未登录或无有效登录态”
- 其他非零退出按异常处理

如你已经确认本机环境稳定，可直接跳过：

```bash
python scripts/sea_product_agent.py --skip-preflight
```

---

## 十二、运行时参数发现（渐进式披露）

当本文件未覆盖某个平台或子命令时，使用 CLI 自身的帮助系统：

```bash
opencli list                               # 所有可用适配器
opencli <platform> --help                  # 平台子命令
opencli <platform> <subcommand> --help     # 具体参数
```

上游文档权威来源：

- OpenCLI：`https://github.com/jackwener/OpenCLI/tree/main/docs/adapters/browser/<platform>.md`

# AI 选品分析 Prompt 模板

## 使用方式

将真实采集到的数据填入 `{{占位符}}` 后，调用 LLM（通过 `invokeLLM` 或 OpenCLI 的 AI 接口）执行分析。**数据质量决定分析质量**——注入真实数字，而非让 LLM 凭空生成。

## 当前状态说明

当前代码库的 Agent 已稳定产出的字段主要是：

- TikTok 内容热度信号
- Google Trends / Google News 热度代理值
- Amazon 榜单价格与热销代理值
- 1688 供货价代理值
- Reddit / 小红书情绪代理值
- 基于以上信号计算出的 `competitionScore` / `sentimentScore` / `potentialScore` / `searchGrowthRate`

当前尚未稳定产出的字段包括：

- 特定平台的在售商品数 / 卖家数 / 佣金率
- 外部电商站点搜索结果数
- 高质量评论级 `sentiment_ratio`

因此本文件中的模板应分为两类理解：

- 当前可落地模板：使用已采集字段或其代理值
- 未来扩展模板：依赖额外电商平台或站内结果页等后续数据源

---

## 模板一：单品爆款潜力评估

```
你是一位专注东南亚跨境电商的资深选品分析师，精通内容电商与货架电商运营逻辑。

## 产品信息
- 产品名称：{{product_name}}
- 目标市场：{{countries}}（如：印尼、泰国、越南）
- 卖家预算：USD {{budget}}

## 市场数据（真实采集）

### TikTok 热度信号
- 相关视频数量：{{tiktok_video_count}}
- 近7日平均播放量：{{avg_play_count}}
- 话题标签热度：{{hashtag_stats}}
- 典型评论情绪摘要：{{comment_summary}}

### 搜索趋势（Google Trends）
- 印尼搜索指数（近3月）：{{id_trend}}
- 泰国搜索指数（近3月）：{{th_trend}}
- 越南搜索指数（近3月）：{{vn_trend}}
- 趋势方向：{{trend_direction}}（上升/下降/平稳）

### 竞争格局
- Amazon 同类产品数量：{{amazon_competitor_count}}
- 价格区间：USD {{price_min}} – {{price_max}}
- 平均评分：{{avg_rating}} / 5.0
- 头部卖家评论数：{{top_seller_reviews}}
- 1688 供货价：CNY {{supply_price}}

### 社媒情绪
- 正面评价关键词：{{positive_keywords}}
- 负面评价关键词：{{negative_keywords}}
- 情绪比例（正:负）：{{sentiment_ratio}}

## 分析任务

请基于以上真实数据，输出以下结构化分析：

1. **爆款潜力评分**（0–100）及评分依据（3句话）
2. **最优目标国家**（按优先级排序，说明理由）
3. **最佳入场时机**（立即/等待/观望，说明依据）
4. **差异化切入点**（相比现有竞品的3个可行方向）
5. **核心风险**（2–3个最需警惕的风险点）
6. **建议定价区间**（结合供货成本和市场价格）

输出格式：JSON，字段名使用英文，值使用中文。
```

---

## 模板二：品类趋势分析

```
你是东南亚电商市场分析专家。基于以下多维度数据，分析 {{category}} 品类在东南亚市场的当前趋势。

## 品类数据

### 各国 TikTok 热度
{{#each countries}}
- {{country}}：视频数 {{video_count}}，平均互动率 {{engagement_rate}}%
{{/each}}

### Google Trends 对比（近6个月）
{{trends_data}}

### Amazon 品类畅销榜 TOP 10
{{bestsellers_data}}

### 小红书相关笔记趋势
- 近30天笔记数：{{xhs_note_count}}
- 近30天互动量：{{xhs_engagement}}
- 热门关键词：{{xhs_keywords}}

## 分析任务

1. **品类热度判断**：当前处于趋势哪个阶段（萌芽期/成长期/爆发期/饱和期）
2. **各国市场成熟度对比**：哪个国家最先进入爆发期
3. **细分机会**：品类内哪些细分方向尚未饱和
4. **季节性规律**：结合东南亚节日，预测未来3个月的需求波动
5. **TOP 3 选品方向**：具体产品形态建议

输出格式：结构化 Markdown 报告。
```

---

## 模板三：竞品饱和度深度分析（未来扩展）

```
分析以下产品在东南亚目标电商市场的竞争饱和度，判断是否值得入场。

## 产品：{{product_name}}

### 竞争数据
- 目标平台同类在售产品数：{{market_listing_count}}（估算）
- Amazon 同类 ASIN 数量：{{amazon_asin_count}}
- 外部电商搜索结果数：{{external_result_count}}
- 1688 供应商数量：{{supplier_count}}

### 头部玩家分析
{{top_sellers_data}}

### 价格分布
- 低价段（<USD {{low_price}}）：{{low_price_ratio}}%
- 中价段（USD {{mid_price_range}}）：{{mid_price_ratio}}%
- 高价段（>USD {{high_price}}）：{{high_price_ratio}}%

### 用户痛点（来自评论分析）
{{pain_points}}

## 分析任务

1. **饱和度评级**：低/中/高/极高，并给出量化依据
2. **利润空间评估**：基于供货价和市场价，估算净利润率区间
3. **差异化空间**：现有产品的共同缺陷和可改进方向
4. **入场壁垒**：新卖家入场面临的主要障碍
5. **建议**：入场/谨慎入场/不建议入场，附具体理由

输出格式：JSON，包含 saturation_level、profit_margin_range、entry_recommendation 等字段。
```

---

## 数据注入最佳实践

**原则：垃圾进，垃圾出。** LLM 的分析质量完全取决于注入数据的真实性和完整性。

| 数据字段                | 采集命令                                                   | 最低要求              |
| ----------------------- | ---------------------------------------------------------- | --------------------- |
| tiktok_video_count      | `opencli tiktok search <keyword> -f json \| jq length`     | 至少搜索3个关键词变体 |
| avg_play_count          | 计算搜索结果的 playCount 均值                              | 样本量 ≥ 20           |
| amazon_competitor_count | `opencli amazon search <keyword> -f json \| jq length`     | 使用精确关键词        |
| supply_price            | `opencli 1688 search <keyword> -f json \| jq '.[0].price'` | 取前5名均价           |
| sentiment_ratio         | 从评论文本中统计正负面比例                                 | 样本量 ≥ 50 条评论    |

**当某项数据无法采集时**，在 Prompt 中明确标注 `数据缺失`，不要用估算值替代，让 LLM 在分析时降低该维度的权重。

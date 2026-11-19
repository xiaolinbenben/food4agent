---
name: nsfc-figure
description: NSFC标书配图制作辅助。帮助设计和绘制机制假说图、技术路线图、 预实验数据图等标书核心图表。触发词：机制图、流程图、假说图、 技术路线图、预实验图、标书配图、作图、画图、图表。
version: 0.1.0
author: NSFC Medicine Skill Group
---

# NSFC Figure — 标书配图设计器

辅助设计NSFC标书中的核心图表，对标中标标书的视觉呈现标准。

## Routing protocol

### 1. Load the manifest and core layer

Read [manifest.yaml](manifest.yaml). Always load:
- `../../../_shared/core/winning-patterns.md` — 图表使用模式
- `static/core/stance.md` — 默认立场
- `static/core/figure-taxonomy.md` — 图表类型学

### 2. Detect axes

| Axis | Values | Method |
|------|--------|--------|
| `figure_type` | mechanism / workflow / data / combined | 从用户需求检测 |
| `backend` | python / r / schematic（示意） | 根据图表类型推荐 |

### 3. Load matching fragments

- `figure_type` → `static/fragments/{mechanism,workflow,data,combined}.md`
- `backend` → `static/fragments/backend/{python,r,schematic}.md`

### 4. NSFC标书图表类型体系

| 图类型 | 用途 | 中标标书出现率 | 制作工具 |
|--------|------|-------------|---------|
| **机制假说图** | 总结全文假说、关键分子/通路关系 | 100% | 推荐BioRender/PPT方向，AI辅助设计 |
| **信号通路图** | 展示已知通路+本研究探索部分 | 90% | 同上 |
| **技术路线图** | 研究步骤流程图 | 85% | Mermaid/流程图工具 |
| **预实验数据图** | Western blot/统计图/显微照片 | 100% | Python/matplotlib, R/ggplot2 |
| **生物信息学图** | 热图/火山图/GSEA/韦恩图 | 80% | Python/R |
| **临床相关性图** | 生存曲线/ROC/相关矩阵 | 45% | R/GraphPad风格 |

### 5. 机制假说图设计原则

基于中标标书中机制假说图的分析：

#### 布局模式
```
┌─────────────────────────────────────────────────┐
│   [上游刺激/病理条件]                              │
│        ↓                                          │
│   ┌─────────────┐                                 │
│   │  核心分子A   │ ← 本研究关注的核心               │
│   └──────┬──────┘                                 │
│          ↓ (虚线 = 待验证)                         │
│   ┌─────────────┐      ┌─────────────┐            │
│   │  通路B       │ ─?──→│  效应蛋白C   │            │
│   └──────┬──────┘      └──────┬──────┘            │
│          ↓                      ↓                  │
│   ┌──────────────────────────────────┐            │
│   │        细胞表型D                   │            │
│   └──────────────┬───────────────────┘            │
│                  ↓                                 │
│   ┌──────────────────────────────────┐            │
│   │        疾病结局E                   │            │
│   └──────────────────────────────────┘            │
│                                                    │
│   图例: ── 已知通路    - - - 本研究假说    ? 待验证 │
└─────────────────────────────────────────────────┘
```

#### 设计规范
- 实线 = 已知机制（有文献或预实验支撑）
- 虚线 = 本研究假说（待验证）
- "?" = 待验证的关键环节
- 色彩：核心分子用醒目的暖色（红/橙），已知分子用冷色（蓝/绿）
- 避免过于复杂的网络图（评审专家30秒内应能看懂核心逻辑）

### 6. 技术路线图设计原则

```
Phase 1: 数据挖掘与筛选
  ├─ 公共数据库分析
  ├─ 差异基因/蛋白筛选
  └─ 候选靶点确定
        ↓
Phase 2: 体外功能验证
  ├─ 细胞模型构建
  ├─ 过表达/敲减表型分析
  └─ 分子机制初探
        ↓
Phase 3: 体内模型验证
  ├─ 动物模型表型
  ├─ 组织病理学
  └─ 体内机制验证
        ↓
Phase 4: 干预策略探索
  ├─ 靶向干预
  ├─ Rescue实验
  └─ 临床相关性分析
```

### 7. 参考

- Python绘图 → `references/python-plotting.md`（matplotlib/seaborn）
- R绘图 → `references/r-plotting.md`（ggplot2/ComplexHeatmap）
- 配色方案 → `references/color-palettes.md`
- 中标标书图表范例 → `references/figure-examples.md`

---
name: video-visual-styles
description: 视频视觉风格模块库 — 16种产品信息图风格 → HTML/CSS 视频模板。用于把 product-infographic-styles 的16种风格（手工纸艺/3D粘土/黑板粉笔/孟菲斯/实验室蓝图等）转化为 HyperFrames 可渲染的 HTML 模板，嵌入到模块化视频引擎的视频视觉风格维度中。触发词：视频风格、视觉风格、做视频换风格、产品信息图风格、16种风格。
---

# 视频视觉风格模块库（16种产品信息图风格 → 视频模板）

> 来源：Word Buddy 的 product-infographic-styles 技能库
> 融合目标：把这16种风格变成视频生产的视觉风格模块，每种风格对应一套 HTML/CSS 模板
> 技术标准：HyperFrames 可渲染（1080×1920 竖屏，GSAP 动画，≤25秒）

## 融合架构

```
模块化视频引擎（现有）
├── A. 钩子模块（35个）← 不变
├── B. 信息模块（37个）← 不变
├── C. 风格模块（8个语音风格）← 扩充为"语音风格+视觉风格"双维度
│   ├── C1. 语音风格（聊天式/算账式/故事式...）← 原有
│   └── C2. 视觉风格（16种产品信息图风格）← 新增 ⭐
├── D. 结尾模块（6个）← 不变
└── E. 热点模块（5类）← 不变
```

**视觉风格选择**：用户可以说"用黑板粉笔风格做视频"或"要孟菲斯扁平感的"，AI 自动匹配对应 HTML 模板。

## 16种风格 → 视频视觉模板映射

### 核心设计原则

每种视觉风格 = 一套 CSS 变量 + 背景纹理 + 字体效果 + 卡片样式 + 装饰元素 + 动画节奏

| 风格ID | 中文名 | 视频适用场景 | 核心视觉特征 |
|--------|--------|------------|------------|
| **VS01** | 手工纸艺 | 走心种草、贴膜教程 | 牛皮纸纹理、剪纸拼贴、温暖大地色 |
| **VS02** | 3D粘土 | 可爱柔和、吸引眼球 | 软陶质感、圆润、暖光 |
| **VS03** | 日式可爱 | 少女风、快消品 | 粉紫pastel、星星爱心、泡泡字体 |
| **VS04** | 水彩绘本 | 文艺故事、品牌感 | 湿画法水彩、艺术笔触、梦幻 |
| **VS05** | 黑板粉笔 | ⭐教学科普、参数说明 | 绿板白粉笔、手绘箭头、教室感 |
| **VS07** | 漫画波普 | ⭐促销大促、大声量 | 半调网点、粗黑轮廓、原色爆炸 |
| **VS08** | 复古学术 | ⭐高端旗舰、品牌信赖 | 羊皮纸、衬线体、纹章徽章 |
| **VS09** | 孟菲斯扁平 | ⭐朋友圈、数据展示 | 几何色块、圆角数据卡、现代商务 |
| **VS11** | 折纸几何 | 极简科技、结构美 | 折痕线条、低多边形、禅意 |
| **VS12** | 8-bit像素 | 游戏周边、复古潮流 | 方块像素、NES游戏、街机感 |
| **VS16** | 排列平铺 | ⭐多品展示、产品目录 | 俯拍网格、白色背景、目录式 |
| **VS17** | 乐高积木 | DIY、创意组装 | 塑料积木、拼装感 |
| **VS18** | 实验室蓝图 | ⭐科技参数、专业背书 | 蓝色蓝图、网格线、化学公式 |
| **VS19** | 莫兰迪手账 | 精致文艺、高审美 | 低饱和pastel、和纸胶带、拍立得 |
| **VS20** | 70年代复古 | 怀旧营销、潮流 | 芥末黄/焦橙色、地球色系、半调 |
| **VS21** | 马卡龙手绘 | 温馨教育、种草 | 糖果色、马克笔画、白板风 |

⭐ = 鑫源光电高频适用场景

## 模板技术规范

### 每个视觉风格模板的结构

```html
<!-- 示例：VS05 黑板粉笔风格 -->
<style>
  /* 1. CSS 变量定义 */
  :root {
    --bg-color: #2d5a27;        /* 黑板绿 */
    --text-color: #f5f5f0;      /* 粉笔白 */
    --accent-color: #ffeb3b;    /* 黄色粉笔 */
    --card-bg: rgba(255,255,255,0.08);
    --font-main: 'Courier New', monospace;  /* 手写感 */
  }

  /* 2. 背景纹理 */
  body {
    background: 
      repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.03) 2px, rgba(0,0,0,0.03) 4px),
      linear-gradient(135deg, #2d5a27, #1a3a15);
  }

  /* 3. 卡片样式 */
  .chalk-card {
    background: var(--card-bg);
    border: 2px solid rgba(255,255,255,0.3);
    border-radius: 4px;           /* 轻微圆角，不像粘土那么圆 */
    font-family: var(--font-main);
  }

  /* 4. 装饰元素 */
  .chalk-dust { /* 粉笔灰效果 */ }
  .hand-drawn-arrow { /* 手绘箭头 */ }
</style>
```

### 通用技术要求（所有风格共享）

| 项目 | 标准 |
|------|------|
| 分辨率 | 1080×1920 竖屏 |
| 时长 | 25秒标准（4场景：5s+8s+7s+5s） |
| 动画库 | GSAP 3.12.5 CDN |
| 字体 | `-apple-system, 'Inter', 'Helvetica Neue', Arial, sans-serif`（HyperFrames 兼容） |
| 转场 | y轴进出场（y:1920→0 进入，y:0→-1920 退出） |
| 确定性 | 无 Math.random()，无 repeat:-1 |
| 文件大小 | ≤3MB（粒子≤2个，无浮动动画） |

## 风格选择指南

### 按内容类型匹配视觉风格

| 视频内容 | 推荐视觉风格 | 原因 |
|---------|------------|------|
| **钢化膜参数科普** | VS05 黑板粉笔 / VS18 实验室蓝图 | 教学感、专业背书 |
| **产品促销/大促** | VS07 漫画波普 / VS09 孟菲斯扁平 | 冲击力、大声量 |
| **高端旗舰膜** | VS08 复古学术 / VS11 折纸几何 | 高端感、品牌信赖 |
| **多品展示/目录** | VS16 排列平铺 | 清晰并列、一目了然 |
| **走心种草/教程** | VS01 手工纸艺 / VS19 莫兰迪手账 | 温暖、有人情味 |
| **少女/女性市场** | VS03 日式可爱 / VS21 马卡龙手绘 | 可爱、温馨 |
| **科技参数/评测** | VS18 实验室蓝图 / VS09 孟菲斯扁平 | 理性、数据感 |
| **品牌故事/态度** | VS04 水彩绘本 / VS08 复古学术 | 文艺、有质感 |

### 按发布平台匹配

| 平台 | 推荐风格 | 原因 |
|------|---------|------|
| **视频号（老板群体）** | VS09 孟菲斯 / VS18 蓝图 / VS05 黑板 | 专业、数据感、教学 |
| **抖音（泛流量）** | VS07 漫画波普 / VS03 日式可爱 / VS21 马卡龙 | 视觉冲击、年轻 |
| **朋友圈** | VS19 莫兰迪 / VS01 手工纸艺 / VS08 复古学术 | 精致、有品位 |
| **公众号配图** | VS16 排列平铺 / VS09 孟菲斯 / VS18 蓝图 | 信息密度高 |

## 与现有 P0 标准的对比

| 维度 | P0 标准（深蓝黑鎏金） | 新视觉风格模块 |
|------|---------------------|--------------|
| 背景 | 深蓝黑渐变+扫描线 | 16种各异（牛皮纸/绿板/蓝图/粉紫...） |
| 字体 | Inter/Arial 白色+鎏金 | 每种风格不同字体效果（粉笔字/手写/像素...） |
| 卡片 | 毛玻璃+内发光 | 每种风格不同卡片（剪纸/砖块/拍立得...） |
| 装饰 | 粒子+光晕 | 每种风格不同装饰（粉笔灰/网点/和纸胶带...） |
| 适用 | 通用产品推广 | 按内容/平台/受众精准匹配 |
| 多样性 | 单一风格 | 16种风格可轮换，避免观众审美疲劳 |

**核心价值**：P0 标准是"保底风格"（任何时候都不会出错），新视觉风格模块是"进阶选项"（针对特定内容和平台做差异化）。

### ⚠️ P0 vs 新风格决策规则（2026-07-02 新增 ⭐⭐⭐）

**核心认知**：P0是保底，新风格是进阶。不是"哪个更好"，是"什么时候用哪个"。

| 场景 | 推荐 | 原因 |
|------|------|------|
| 夜间飞轮批量生产 | **P0** | 速度快、模板稳定、已验证 |
| 公众号文章转视频 | **P0** | 已有成熟模板和流程 |
| 单条精品视频 | **新风格** | 针对性强、差异化高 |
| 系列视频（同主题多集） | **风格轮换** | 避免审美疲劳 |
| 紧急/临时需求 | **P0** | 拿来就用 |
| 节日/促销活动 | **VS07漫画 / VS09孟菲斯** | 大声量、视觉冲击 |
| 新品首发 | **VS09孟菲斯** | 现代感、专业感 |
| 技术科普 | **VS05黑板 / VS18蓝图** | 教学感、权威感 |
| 品牌故事 | **VS01手工 / VS19莫兰迪** | 温暖、有质感 |

**混合使用模式**：
- 模式A：P0打底+新风格点睛（钩子用P0、科普用黑板、数据用孟菲斯、结尾用P0）
- 模式B：系列视频风格轮换（第1集黑板、第2集蓝图、第3集孟菲斯）
- 模式C：平台差异化（视频号用孟菲斯/蓝图、抖音用漫画/可爱、朋友圈用莫兰迪/手工）

## 实施计划

### Phase 1：高优先级风格模板（5个）⭐⭐⭐

**进度（2026-07-02）**: 5/5 全部完成 ✅

| # | 风格 | 选题 | 文件大小 | 渲染方式 |
|---|------|------|---------|---------|
| 1 | ✅ VS05 黑板粉笔 | 曲面膜翘边科普 | 1.8MB | 标准渲染 |
| 2 | ✅ VS09 孟菲斯扁平 | 晶钻膜数据对比 | 535KB | 标准渲染 |
| 3 | ✅ VS18 实验室蓝图 | 超声波指纹技术 | 1.1MB | `PRODUCER_LOW_MEMORY_MODE=true` |
| 4 | ✅ VS07 漫画波普 | 晶钻膜促销 | 853KB | 标准渲染 |
| 5 | ✅ VS16 排列平铺 | 三大系列展示 | 268KB | 标准渲染 |
| 6 | ✅ VS09 孟菲斯（产品大图卡） | 鸟迪支架 Z20/Z51/Z33 | 1.1MB | `PRODUCER_LOW_MEMORY_MODE=true`，30秒 |

> 全部通过质检：1080×1920 / 30fps / AAC音频 / MD5帧差异校验
> 渲染耗时基准：标准渲染~20秒，VS18低内存模式~30秒，产品大图卡模式~29秒

### Phase 2：中优先级风格模板（5个）⭐⭐

6. **VS08 复古学术** — 高端旗舰
7. **VS01 手工纸艺** — 走心种草
8. **VS19 莫兰迪手账** — 精致文艺
9. **VS03 日式可爱** — 少女/快消
10. **VS21 马卡龙手绘** — 温馨教育

### Phase 3：剩余6种风格

S02 3D粘土、S04 水彩绘本、S11 折纸几何、S12 8-bit像素、S17 乐高积木、S20 70年代复古

## 模板文件结构

```
~/.hermes/skills/video-visual-styles/
├── SKILL.md                                    ← 本文件
├── references/
│   ├── style-mapping.md                        ← 16种风格→视频场景映射表
│   ├── template-vs05-chalkboard.md             ← VS05 黑板粉笔模板
│   ├── template-vs09-memphis.md                ← VS09 孟菲斯模板
│   ├── template-vs18-lab-blueprint.md          ← VS18 实验室蓝图模板
│   ├── template-vs07-pop-comic.md              ← VS07 漫画波普模板
│   ├── template-vs16-knolling.md               ← VS16 排列平铺模板
│   └── ...（后续Phase 2/3）
├── templates/
│   ├── vs05-chalkboard.html                    ← ✅ 黑板粉笔（已渲染验证，1.8MB）
│   ├── vs09-memphis.html                       ← ✅ 孟菲斯（已渲染验证，535KB）
│   ├── vs16-knolling.html                      ← ✅ 排列平铺（已渲染验证，268KB）
│   ├── vs18-lab-blueprint.html                 ← ✅ 实验室蓝图（已渲染验证，1.1MB，需LOW_MEMORY_MODE）
│   ├── vs07-pop-comic.html                     ← ✅ 漫画波普（已渲染验证，853KB）
│   └── ...（后续Phase 2/3）
└── scripts/
    └── style-selector.py                       ← 风格选择辅助脚本
```

## 与 product-infographic-styles 的关系

| 维度 | product-infographic-styles（Word Buddy） | video-visual-styles（Hermes） |
|------|----------------------------------------|------------------------------|
| 用途 | ImageGen 生成静态产品图 | HyperFrames 渲染视频 |
| 输出 | PNG 图片（1024×1024） | MP4 视频（1080×1920，25秒） |
| 工具 | ImageGen API | HTML+CSS+GSAP+HyperFrames |
| 风格来源 | 16种英文提示词 | 从16种风格提取视觉特征→CSS实现 |
| 产品替换 | `phone case` → `tempered glass screen protector` | 视频文案中的产品名称 |
| 协作方式 | Word Buddy 生成产品图素材 | Hermes 生成视频成品 |

**互补关系**：
- product-infographic-styles 生成**静态产品图**（朋友圈配图、公众号封面、产品目录）
- video-visual-styles 生成**动态视频**（视频号、抖音、朋友圈视频）
- 两者共用同一套16种风格的视觉语言，保持品牌一致性

## 使用示例

### 用户说："用黑板粉笔风格做个钢化膜科普视频"

AI 执行流程：
1. 从 module-library 选钩子（如 H14 曲面屏翘边痛点）
2. 从 module-library 选信息（如 I22 曲面膜翘边原理）
3. 从 module-library 选语音风格（S04 教学式）
4. **从 video-visual-styles 选视觉风格（VS05 黑板粉笔）** ← 新增
5. 从 module-library 选结尾（C04 教学式结尾）
6. 加载 `templates/vs05-chalkboard.html` 模板
7. 替换文案内容
8. 生成配音 + HyperFrames 渲染

### 用户说："我要做一批产品目录视频，要孟菲斯风格"

AI 执行流程：
1. 选信息模块：I01-I10（各系列膜）
2. **选视觉风格：VS09 孟菲斯扁平** ← 多品展示最佳
3. 加载 `templates/vs09-memphis.html` 模板
4. 批量生成（每个产品一个视频，模板不变只换内容）

## 注意事项

1. **CSS 兼容性**：HyperFrames 基于 Chromium，不支持 `backdrop-filter` 的部分特性，用 `background: rgba()` 替代
2. **字体限制**：不能用 PingFang SC/Noto Sans SC（编译超时），用 Inter/Arial 回退
3. **动画简化**：复杂3D变换（rotateX/Y）在 HyperFrames 中可能不支持，优先用 opacity+y+scale
4. **文件大小**：纹理背景（如牛皮纸、水彩）如果用 CSS 渐变模拟，文件小；如果用图片，需压缩到 100KB 以内
5. **风格轮换**：同一系列视频不要连续用同一种视觉风格，避免观众审美疲劳
6. **⚠️ 时长应匹配内容，不固定22秒**（2026-07-02 新增 ⭐⭐⭐）：
   - 4场景视频（钩子→参数→卖点→品牌）= 12秒足够，每个场景2-3秒
   - 22秒=浪费渲染时间（每个22秒视频要15-17秒渲染），用户明确要求"按需定时长"
   - 简单内容10-12秒，中等内容15秒，复杂内容20秒
   - 模板中 `data-duration` 设为实际需要的秒数，不要默认22

7. **⚠️ 视频必须带配音**（2026-07-02 新增 ⭐⭐⭐）：
   - 用户要求"有画面、有声音、有文字"才是完整体验
   - Edge-TTS 生成配音 → FFmpeg 混合到视频
   - 配音文案 = 每个场景一句核心话术，总字数控制在 40-60 字（12秒配音约48字，按4字/秒）
   - Edge-TTS 命令：`edge-tts --voice zh-CN-XiaoxiaoNeural --rate="-10%" --text "文案" --write-media voice.wav`
   - FFmpeg 混合：`ffmpeg -i video.mp4 -i voice.wav -c:v copy -c:a aac -af "volume=0.9" -shortest output.mp4`

8. **⚠️ 静态图 ≠ 视频模板**：skr 生成的 HTML（900×600 横屏单页）不能直接复用为 HyperFrames 视频模板。视频模板需要 1080×1920 竖屏 + 4个 scene 依次切换 + GSAP 时间线。每次做新风格视频模板都要从零写 HTML。

### ⚠️ 已知陷阱

### ⚠️ HyperFrames DOM节点预算（2026-07-02 新增 ⭐⭐⭐）

**问题**：HTML中DOM节点过多 → `Set maximum size exceeded` 内存溢出，即使低内存模式也不行。
**根因**：5个场景×每个场景多个div（装饰元素、卡片、标签等）→ 750帧每帧都要渲染整个DOM树。
**修复**：
1. **装饰元素用CSS类代替div**：`<div class="dot d1"></div>` 代替 `<div class="memphis-dot"></div><div class="memphis-line"></div>`
2. **每个场景最少DOM节点**：场景容器 + 标题 + 卡片 + 卡片内元素，越少越好
3. **用CSS伪元素或背景**：能写CSS的不用额外div
4. **产品大图卡模式**：产品图片+描述+标签放在一个大card内，而不是分散多个元素
5. **如果仍然OOM**：减少场景数（4→3），或降低时长（30→25）
**适用范围**：所有HyperFrames渲染的HTML视频模板
**验证方法**：先数DOM节点，<30个节点安全，30-50个有风险，>50个大概率OOM

### ⚠️ VS18蓝图渲染OOM（2026-07-02）

**问题**：`repeat:-1`（无限循环）+ 复杂GSAP动画 → `Set maximum size exceeded` 内存溢出
**修复**：
1. `repeat:-1` → `repeat:3`（有限次数）
2. 渲染时加环境变量：`PRODUCER_LOW_MEMORY_MODE=true bash render.sh`
3. 或使用 `--workers 1` 限制并发
**适用范围**：所有含 `repeat:-1` 的GSAP动画（不仅是蓝图风格）

### ⚠️ CSS transform与GSAP动画冲突（2026-07-02）

**问题**：元素CSS中写了 `transform: scale(X)`，GSAP又动画同一个属性 → GSAP覆盖整个transform，丢失CSS中的translate/center定位
**修复**：CSS中不要写 `transform`，全部用GSAP的 `fromTo()` 或 `to()` 控制
**适用范围**：所有视觉风格模板

### ⚠️ 文件大小差异巨大（2026-07-02）

实测Phase1五个风格文件大小：
- VS16排列平铺：268KB（纯白背景+少量色块，压缩率极高）
- VS09孟菲斯：535KB（白色背景+几何色块）
- VS07漫画波普：853KB（网点纹理+粗轮廓）
- VS18实验室蓝图：1.1MB（深蓝底色+网格线）
- VS05黑板粉笔：1.8MB（绿色纹理+粉笔灰效果）

**经验**：背景越复杂（纹理/渐变/粒子），文件越大。纯白背景+几何图形最小。

### ⚠️ HyperFrames 版本兼容性（2026-07-07 ⭐⭐⭐⭐⭐ 致命）

**问题**：`npx hyperframes render .` 在 0.7.38+ 版本全部报 `HierarchyRequestError: Only one element on document allowed`，0.7.37 正常。
**根因**：0.7.38+ 的 Chromium 渲染引擎对 DOM 结构校验更严格，`<div id="root">` 外的嵌套结构导致 insertBefore 失败。
**修复**：
1. **始终用 `npx hyperframes@0.7.37`** 渲染，不要用最新版
2. 模板结构必须：`<div id="root">` 包裹所有内容，场景用 `#root .s1` 选择器
3. 不要在外层再用 `<div id="root">` 套一层（双重 root 会导致 HierarchyRequestError）
**适用范围**：所有 HyperFrames 渲染的 HTML 视频模板
**验证方法**：渲染前 `npx hyperframes@0.7.37 render . --output renders/test.mp4` 先试跑一版

### ⚠️ edge-tts 双 Python 环境问题（2026-07-07 ⭐⭐⭐⭐）

**问题**：hermes venv 的 edge-tts 不支持中文语音名（zh-CN-XiaoxiaoNeural），homebrew python3.14 的 edge-tts 报 asyncio 错误但文件已生成。
**根因**：两个 Python 环境的 edge-tts 版本不同（venv=3.11/旧版 vs homebrew=3.14/新版），asyncio.run(main()) 在 3.14 中 main 不是 coroutine。
**修复**：
1. **用 homebrew python3.14** 调用 edge_tts：`/opt/homebrew/opt/python3/bin/python3.14 -c 'import asyncio; from edge_tts.util import main; asyncio.run(main())'`
2. 语音名必须用 `zh-CN-XiaoxiaoNeural`（中文 locale），不是 `XiaoxiaoNeural`（英文 locale）
3. 如果 s2/s3 生成 0KB，重新生成一次（asyncio 报错但文件已写入）
**适用范围**：所有需要 edge-tts 生成中文配音的场景

### ⚠️ VS09 孟菲斯模板标准结构（2026-07-07 ⭐⭐⭐⭐⭐ 新增）

**最佳实践**：从 vs09-memphis-v7 提取的标准模板结构，所有新视频基于此结构修改。
**关键特征**：
- `<div id="root">` 包裹全部场景
- 场景选择器：`#root .s1`, `#root .s2`, `#root .s3`, `#root .s4`
- GSAP 时间线：`tl.set('#root .s1', {opacity:1})` 开头，`tl.to('#root .s1', {opacity:0})` 结尾
- 装饰元素：`.deco dc1/dc2/dc3` 三个静态装饰
- 场景过渡：每个场景先 `set(opacity:1)` 再动画子元素，最后 `to(opacity:0)` 转场
**适用范围**：所有 VS09 孟菲斯风格视频

### ⚠️ HyperFrames 版本兼容性（2026-07-07 ⭐⭐⭐⭐⭐ 致命）

**问题**：`npx hyperframes render .` 在 0.7.38+ 版本全部报 `HierarchyRequestError: Only one element on document allowed`，0.7.37 正常。
**根因**：0.7.38+ 的 Chromium 渲染引擎对 DOM 结构校验更严格，`<div id="root">` 外的嵌套结构导致 insertBefore 失败。
**修复**：
1. **始终用 `npx hyperframes@0.7.37`** 渲染，不要用最新版
2. 模板结构必须：`<div id="root">` 包裹全部内容，场景用 `#root .s1` 选择器
3. 不要在外层再用 `<div id="root">` 套一层（双重 root 会导致 HierarchyRequestError）
**适用范围**：所有 HyperFrames 渲染的 HTML 视频模板
**验证方法**：渲染前 `npx hyperframes@0.7.37 render . --output renders/test.mp4` 先试跑一版

### ⚠️ edge-tts 双 Python 环境问题（2026-07-07 ⭐⭐⭐⭐）

**问题**：hermes venv 的 edge-tts 不支持中文语音名（zh-CN-XiaoxiaoNeural），homebrew python3.14 的 edge-tts 报 asyncio 错误但文件已生成。
**根因**：两个 Python 环境的 edge-tts 版本不同（venv=3.11/旧版 vs homebrew=3.14/新版），asyncio.run(main()) 在 3.14 中 main 不是 coroutine。
**修复**：
1. **用 homebrew python3.14** 调用 edge_tts：`/opt/homebrew/opt/python3/bin/python3.14 -c 'import asyncio; from edge_tts.util import main; asyncio.run(main())'`
2. 语音名必须用 `zh-CN-XiaoxiaoNeural`（中文 locale），不是 `XiaoxiaoNeural`（英文 locale）
3. 如果 s2/s3 生成 0KB，重新生成一次（asyncio 报错但文件已写入）
**适用范围**：所有需要 edge-tts 生成中文配音的场景

### ⚠️ VS09 孟菲斯模板标准结构（2026-07-07 ⭐⭐⭐⭐⭐ 新增）

**最佳实践**：从 vs09-memphis-v7 提取的标准模板结构，所有新视频基于此结构修改。
**关键特征**：
- `<div id="root">` 包裹全部场景
- 场景选择器：`#root .s1`, `#root .s2`, `#root .s3`, `#root .s4`
- GSAP 时间线：`tl.set('#root .s1', {opacity:1})` 开头，`tl.to('#root .s1', {opacity:0})` 结尾
- 装饰元素：`.deco dc1/dc2/dc3` 三个静态装饰
- 场景过渡：每个场景先 `set(opacity:1)` 再动画子元素，最后 `to(opacity:0)` 转场
**适用范围**：所有 VS09 孟菲斯风格视频

### ⚠️ 字号可读性标准（2026-07-02 ⭐⭐⭐⭐⭐ 关键）

**问题**：Phase1五个视频的小标题和正文/描述字号太小，在手机竖屏1080x1920上看不清。
**根因**：参考旧模板字号体系，没有考虑竖屏手机上正文至少需要36-44px才可读。

**强制字号标准（所有1080x1920视频模板必须遵守）：**

| 层级 | 最小字号 | 推荐字号 | 说明 |
|------|---------|---------|------|
| 大标题 | 52px | 64px | 每场景第一个出现的标题 |
| 中标题 | 40px | 48px | 场景副标题、章节名 |
| 正文/描述 | **36px** | **44px** | 卡片内文字、参数说明、列表项 |
| 标签/角标 | 28px | 32px | tag、小注释 |
| 价格/数字 | 44px | 56px | 突出显示的价格、数据值 |

**检查方法**：渲染前 `grep -oE 'font-size:[^;"]+' index.html \| grep -oE '[0-9]+' \| sort -n \| head -3`，确认最小字号≥28px，正文字号≥36px。

**修复记录**：Phase1五个视频全部在21:08-21:12重渲染，正文最小字号从18-30px提升到26-44px。

---

_此 skill 是 product-infographic-styles 和 modular-video-engine 的桥梁，把静态产品图风格转化为动态视频视觉风格。_

## 参考资源

- **模板参考文档**: `references/template-vs05-chalkboard.md` — VS05 黑板粉笔视频模板
- **模板参考文档**: `references/template-vs09-memphis.md` — VS09 孟菲斯扁平视频模板
- **模板参考文档**: `references/template-vs18-lab-blueprint.md` — VS18 实验室蓝图视频模板
- **风格映射表**: `references/style-mapping.md` — 16种风格→视频场景映射（按内容类型/平台/月度轮换）
- **上游风格源**: `~/.workbuddy/skills/product-infographic-styles/` — Word Buddy 的 product-infographic-styles 技能库，16种风格的英文提示词和参考图（ImageGen 静态产品图）
- **下游应用**: 本 skill 的视觉风格通过 HTML/CSS/GSAP 转化为 HyperFrames 可渲染的 MP4 视频（1080×1920 竖屏）
- **渲染报告**: `references/render-vs05-09-16-validation.md` — VS05/VS09/VS16 批量渲染验证报告（模板结构、关键教训、时长控制）
- **渲染报告**: `references/render-vs05-chalkboard-report.md` — VS05黑板粉笔第一条视频渲染验证报告（2026-07-02）
- **Phase1实战经验**: `references/phase1-render-experience.md` — 5个风格全部渲染验证记录（文件大小基准、GSAP陷阱、CSS冲突、配音字数）⭐⭐⭐
- **Phase4膜世界品牌视频**: `references/phase4-mosze-brand-videos.md` — 4个品牌系列视频（F晶钻/S防窥/K壳瓷/O电镀）标准化生产记录（HyperFrames版本、edge-tts双Python、模板结构）⭐⭐⭐
- **产品图片提取**: `references/mmbiz-image-extraction.md`
- **产品图片提取**: `references/mmbiz-image-extraction.md` — 从公众号文章HTML提取产品图片URL的方法（mmbiz.qpic.cn域名特征、提取命令、已知图片列表）
- **融合操作手册**: `references/fusion-manual.md` — 16种风格×P0标准×模块化引擎完整融合方案（2026-07-02新增）
- **多风格引擎**: `multi-style-video-engine` — 自动选风格+配音+渲染+推送的完整管道，本技能的16种风格由其调用方。触发词："做个视频"/"换个风格"

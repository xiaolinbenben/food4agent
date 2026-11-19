# VS05/VS09/VS16 批量渲染验证报告

> 日期：2026-07-02
> 目的：验证 product-infographic-styles 的16种风格能否正确转为 HyperFrames 视频模板

## 渲染结果

| 风格 | 模板 | 渲染时长 | 文件大小 | 状态 |
|------|------|---------|---------|------|
| VS05 黑板粉笔 | templates/vs05-chalkboard.html | 17.1s | 1.1MB | ✅ 通过 |
| VS09 孟菲斯扁平 | templates/vs09-memphis.html | 15.8s | 559KB | ✅ 通过 |
| VS16 排列平铺 | templates/vs16-knolling.html | 16.0s | 523KB | ✅ 通过 |

## 模板结构（通用模式）

所有模板遵循统一结构：
```html
<!DOCTYPE html>
<html lang="zh-CN" data-composition-id="root" data-width="1080" data-height="1920" data-duration="22" data-start="0">
<head>
  <script src="gsap CDN"></script>
  <style>
    /* 风格专属 CSS 变量 + 背景 + 卡片 + 装饰 */
    /* 4个 scene（s1-s4），每个 scene 内含内容元素 */
  </style>
</head>
<body>
  <div id="root">
    <div class="scene s1">钩子场景</div>
    <div class="scene s2">信息场景</div>
    <div class="scene s3">产品场景</div>
    <div class="scene s4">结尾场景</div>
  </div>
  <script>
    const tl = gsap.timeline({ paused: true });
    // 每个场景：set(opacity:1) → 子元素动画 → to(opacity:0)
    window.__timelines["root"] = tl;
  </script>
</body>
</html>
```

## 关键教训

### 1. 静态图 vs 视频模板是两套不同的 HTML

skr（静态图）用 900×600 横屏，单页布局。
HyperFrames（视频）用 1080×1920 竖屏，4个 scene 依次切换。
**不能直接复用 skr 的 HTML**，需要重新设计场景结构和动画时序。

### 2. GSAP 动画模式（验证有效）

```javascript
// 场景切换模式
tl.set('#scene', { opacity: 1 })        // 准备可见
  .to('#scene .element', { opacity: 1, duration: 0.6, ease: 'power2.out' })  // 子元素入场
  .to('#scene', { opacity: 0, duration: 0.8, ease: 'power2.in' });           // 场景淡出
```

### 3. 时长控制

- data-duration 设为 22 秒（4场景 × 5.5秒 ≈ 22秒）
- 每个场景停留 4-5秒，进出场各 0.8-1.0秒
- 总时长控制在 22秒以内，避免 HyperFrames 渲染超时（>25秒有风险）

### 4. 字体选择

- 黑板粉笔：Courier New（系统自带，无需下载）
- 孟菲斯/排列平铺：Inter, -apple-system, Helvetica Neue（系统回退链）
- **永远不要引用 PingFang SC / Noto Sans SC**（Google Fonts 下载超时）

## 下一步

- VS18 实验室蓝图 — 蓝色蓝图+网格线+化学公式元素
- VS07 漫画波普 — 半调网点+粗黑轮廓+爆炸效果
- 其余 11 种风格按 Phase 2/3 逐步开发

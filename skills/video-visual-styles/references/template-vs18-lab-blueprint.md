# VS18 实验室蓝图 — 视频模板

> 风格来源：product-infographic-styles S18 实验室蓝图
> 适用场景：科技参数、专业背书、钢化膜技术讲解
> 核心特征：蓝色蓝图背景、白色网格线、科学仪器插图

## CSS 变量

```css
:root {
  --blueprint-blue: #0d47a1;
  --blueprint-light: #1976d2;
  --blueprint-grid: rgba(255, 255, 255, 0.15);
  --tech-white: #e3f2fd;
  --accent-cyan: #00e5ff;
  --accent-green: #69f0ae;
}
```

## 背景

```css
body {
  background: var(--blueprint-blue);
  background-image:
    /* 主网格 */
    linear-gradient(var(--blueprint-grid) 1px, transparent 1px),
    linear-gradient(90deg, var(--blueprint-grid) 1px, transparent 1px),
    /* 次网格（更密）*/
    linear-gradient(rgba(255,255,255,0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.05) 1px, transparent 1px);
  background-size: 100px 100px, 100px 100px, 20px 20px, 20px 20px;
}
```

## 技术卡片

```css
.tech-card {
  background: rgba(13, 71, 161, 0.8);
  border: 2px solid var(--accent-cyan);
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 0 15px rgba(0, 229, 255, 0.3);
}
.tech-label {
  color: var(--accent-cyan);
  font-size: 16px;
  text-transform: uppercase;
  letter-spacing: 2px;
}
.tech-value {
  color: var(--tech-white);
  font-size: 42px;
  font-weight: bold;
}
```

## 装饰元素

```css
/* 化学分子式装饰 */
.molecule {
  position: absolute;
  color: rgba(255,255,255,0.1);
  font-size: 24px;
  font-family: monospace;
}
/* 仪器轮廓 */
.instrument-outline {
  border: 2px dashed rgba(255,255,255,0.2);
  border-radius: 50%;
  position: absolute;
}
```

## 动画节奏

| 场景 | 停留 | 动画 |
|------|------|------|
| S1 钩子 | 5s | 网格线绘制效果+标题打字机 |
| S2 信息 | 8s | 技术参数卡片逐个浮现 |
| S3 产品 | 7s | 对比条形图（渐变色填充） |
| S4 结尾 | 5s | 品牌印章+科技光效 |

## 适用内容

✅ 钢化膜技术参数（0.33mm/9H/透光率）
✅ 超声波指纹解决方案
✅ 折叠屏膜技术原理
✅ 产品检测报告/认证展示

## 配音建议

S04 教学式（Yunxi男声）+ 语速中等，像科技博主讲解

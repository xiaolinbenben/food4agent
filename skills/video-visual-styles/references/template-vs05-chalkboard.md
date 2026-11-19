# VS05 黑板粉笔 — 视频模板

> 风格来源：product-infographic-styles S05 黑板粉笔
> 适用场景：教学科普、参数说明、知识讲解、贴膜教程
> 核心特征：绿板白粉笔、手绘箭头、教室感

## CSS 变量

```css
:root {
  --board-green: #2d5a27;
  --board-dark: #1a3a15;
  --chalk-white: #f5f5f0;
  --chalk-yellow: #ffeb3b;
  --chalk-blue: #64b5f6;
  --chalk-red: #ef5350;
  --chalk-gray: #bdbdbd;
  --font-hand: 'Courier New', 'Comic Sans MS', monospace;
}
```

## 背景纹理

```css
body {
  background:
    /* 粉笔灰微粒 */
    radial-gradient(circle at 20% 30%, rgba(255,255,255,0.03) 0%, transparent 50%),
    radial-gradient(circle at 80% 70%, rgba(255,255,255,0.02) 0%, transparent 40%),
    /* 黑板绿渐变 */
    linear-gradient(135deg, var(--board-green), var(--board-dark));
  /* 轻微纹理 */
  background-size: 100% 100%;
}
```

## 卡片样式

```css
.chalk-card {
  background: rgba(255, 255, 255, 0.05);
  border: 2px solid rgba(255, 255, 255, 0.25);
  border-radius: 6px;
  padding: 24px;
  font-family: var(--font-hand);
  color: var(--chalk-white);
  box-shadow: 3px 3px 8px rgba(0, 0, 0, 0.3);
}
```

## 文字效果

```css
.chalk-title {
  font-size: 56px;
  font-weight: bold;
  color: var(--chalk-white);
  text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
  letter-spacing: 2px;
}

.chalk-accent {
  color: var(--chalk-yellow);
  text-decoration: underline;
  text-decoration-style: wavy;
  text-decoration-color: var(--chalk-yellow);
}

.chalk-highlight {
  background: rgba(255, 235, 59, 0.15);
  padding: 2px 8px;
  border-radius: 4px;
}
```

## 装饰元素

```css
/* 手绘箭头 */
.chalk-arrow {
  position: relative;
  display: inline-block;
}
.chalk-arrow::after {
  content: '→';
  margin-left: 8px;
  color: var(--chalk-red);
  font-size: 1.2em;
}

/* 下划线标注 */
.chalk-underline {
  border-bottom: 3px solid var(--chalk-yellow);
  padding-bottom: 2px;
}

/* 粉笔灰粒子 */
.chalk-dust {
  width: 4px;
  height: 4px;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  position: absolute;
}
```

## 动画节奏

| 场景 | 停留时间 | 动画风格 |
|------|---------|---------|
| S1 钩子 | 5s | 粉笔书写效果（逐字出现） |
| S2 信息 | 8s | 卡片滑入+手绘箭头标注 |
| S3 产品 | 7s | 参数逐个列出（像老师板书） |
| S4 结尾 | 5s | 品牌名粉笔字+擦除效果 |

## 配音建议

- **语音风格**：S04 教学式（Yunxi 男声全程）
- **语速**：中等偏慢（4字/秒，给学生消化时间）
- **语气**：像老师在黑板前讲课，亲切专业

## 适用内容类型

✅ 钢化膜参数科普（厚度/硬度/透光率）
✅ 贴膜教程（无尘舱使用方法）
✅ 知识问答（UV膜和普通膜区别）
✅ 选购指南（怎么判断膜的好坏）
✅ 故障排除（气泡/翘边/指纹失灵）

❌ 不适合：促销大促（冲击力不够）、品牌故事（太严肃）

## 与其他风格的搭配

| 搭配 | 效果 |
|------|------|
| VS05 黑板粉笔 + VS18 实验室蓝图 | 科普系列：先黑板引入→蓝图深入 |
| VS05 黑板粉笔 + VS09 孟菲斯扁平 | 教学+数据：先原理→再参数对比 |
| VS05 黑板粉笔 + VS01 手工纸艺 | 教程+走心：先教方法→再讲感受 |

## 参考产品替换

提示词中的产品替换：
- `Phone accessories` → `tempered glass screen protector`（钢化膜）
- `Chalk drawings` → 手绘箭头/方框标注产品特性
- `Product specs in chalk` → 参数用不同颜色粉笔区分

## 文件结构

```
templates/
└── vs05-chalkboard/
    ├── index.html              # 完整HTML模板（4场景）
    ├── gsap_chalkboard.js      # GSAP动画脚本
    └── render.sh               # 渲染脚本模板
```

---

_此模板是16种风格中的第一个，验证通过后复制到 Phase 2/3 风格。_

# VS09 孟菲斯扁平 — 视频模板

> 风格来源：product-infographic-styles S09 孟菲斯扁平
> 适用场景：朋友圈、数据展示、现代商务、产品推广
> 核心特征：几何色块、圆角数据卡、 vibrant 蓝黄红配色

## CSS 变量

```css
:root {
  --memphis-blue: #2196f3;
  --memphis-yellow: #ffeb3b;
  --memphis-red: #f44336;
  --memphis-green: #4caf50;
  --bg-white: #ffffff;
  --text-dark: #212121;
  --text-light: #757575;
  --card-radius: 16px;
}
```

## 背景

```css
body {
  background: var(--bg-white);
  position: relative;
}
/* 孟菲斯装饰元素 */
.memphis-dot {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--memphis-yellow);
  position: absolute;
}
.memphis-square {
  width: 16px;
  height: 16px;
  background: var(--memphis-red);
  position: absolute;
  transform: rotate(15deg);
}
.memphis-wave {
  width: 60px;
  height: 30px;
  border-bottom: 3px solid var(--memphis-blue);
  border-radius: 0 0 30px 30px;
  position: absolute;
}
```

## 卡片样式

```css
.memphis-card {
  background: var(--bg-white);
  border-radius: var(--card-radius);
  padding: 20px;
  box-shadow: 4px 4px 0 var(--memphis-blue);
  border: 3px solid var(--text-dark);
}
.memphis-card-accent {
  border-color: var(--memphis-yellow);
  box-shadow: 4px 4px 0 var(--memphis-red);
}
```

## 数据卡片（4并排）

```css
.data-row {
  display: flex;
  gap: 12px;
  justify-content: space-between;
}
.data-card {
  flex: 1;
  background: var(--bg-white);
  border: 2px solid var(--text-dark);
  border-radius: 12px;
  padding: 16px;
  text-align: center;
}
.data-value {
  font-size: 48px;
  font-weight: bold;
  color: var(--memphis-blue);
}
.data-label {
  font-size: 18px;
  color: var(--text-light);
  margin-top: 4px;
}
```

## 动画节奏

| 场景 | 停留 | 动画 |
|------|------|------|
| S1 钩子 | 5s | 几何色块弹入+文字逐字 |
| S2 信息 | 8s | 4数据卡片依次弹出（stagger 0.15s） |
| S3 产品 | 7s | 卡片翻转+参数条形图滑入 |
| S4 结尾 | 5s | 品牌色块堆积+印章效果 |

## 适用内容

✅ 产品数据对比（厚度/硬度/透光率/价格）
✅ 朋友圈推广（现代商务感）
✅ 多品展示（清晰并列）
✅ 促销海报（ vibrant 色彩冲击）

## 参考

与 P0 标准对比：孟菲斯更现代活泼，P0更科技沉稳。朋友圈用孟菲斯，视频号老板群体用P0或实验室蓝图。

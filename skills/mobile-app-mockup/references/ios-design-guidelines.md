# iOS 设计规范参考

## iPhone 15 Pro 规格

| 属性 | 值 |
|------|-----|
| 逻辑分辨率 | 393 x 852 pt |
| 物理分辨率 | 1179 x 2556 px (@3x) |
| 对角线 | 6.1 inches |
| 设备圆角 | ~55px（屏幕区域约 44px） |
| 状态栏高度 | 54px（含 Dynamic Island） |
| 底部安全区 | 34pt（Home Indicator 区域） |
| Tab Bar 高度 | 50pt（不含安全区） |
| 导航栏高度 | 44pt |

## 安全区域

```
┌──────────────────────────┐
│    Status Bar (54pt)     │  ← Dynamic Island 区域
│                          │
│    Nav Bar (44pt)        │  ← 可选，二级页面使用
├──────────────────────────┤
│                          │
│    Content Area          │  ← 主要内容区域
│                          │
│                          │
├──────────────────────────┤
│    Tab Bar (50pt)        │  ← 仅 Tab 主页面
│    Safe Area (34pt)      │  ← Home Indicator
└──────────────────────────┘
```

## 点击目标

iOS HIG 建议最小点击目标为 44x44pt。列表行高通常为 44pt。

## 配色参考

### iOS 系统色
- System Blue: #007AFF
- System Green: #34C759
- System Indigo: #5856D6
- System Orange: #FF9500
- System Pink: #FF2D55
- System Purple: #AF52DE
- System Red: #FF3B30
- System Teal: #5AC8FA
- System Yellow: #FFCC00

### iOS 灰度
- Background: #F2F2F7（浅）/ #000000（深）
- Card: #FFFFFF（浅）/ #1C1C1E（深）
- Separator: #E5E5EA（浅）/ #38383A（深）
- Text Primary: #000000 / #FFFFFF
- Text Secondary: #8E8E93 / #98989D
- Text Tertiary: #C7C7CC / #48484A

## 字体

iOS 使用 San Francisco (SF) 字体族。Web 端使用系统字体栈模拟：
```
font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, sans-serif;
```

## 圆角参考

- 设备外框：44px
- 大卡片/面板：16px
- 标准卡片：12px
- 按钮/输入框：12px
- 小标签/Chip：16px（胶囊形）
- 弹窗/Alert：20px

## 常见页面布局模式

### 列表页
```
[Status Bar]
[Search Bar / Header]
[Section Title]  [See All >]
[Item 1]
[Item 2]
[Item 3]
...
[Tab Bar]
```

### 详情页
```
[Status Bar]
[Nav Bar: < Back    Title    Share]
[Hero Image]
[Title + Meta]
[Description Content]
[Action Button(s)]
```

### 个人中心
```
[Status Bar]
[Profile Header: Avatar + Name + Stats]
[Menu List:
  我的订单      >
  我的收藏      >
  收货地址      >
  设置         >
]
[Tab Bar]
```

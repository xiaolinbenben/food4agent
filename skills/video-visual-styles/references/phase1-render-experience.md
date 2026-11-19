# Phase1 渲染实战经验（2026-07-02）

5个视觉风格全部完成渲染验证，以下是实战记录。

## 渲染基准

| 风格 | 文件大小 | 渲染耗时 | 特殊要求 |
|------|---------|---------|---------|
| VS05 黑板粉笔 | 1.8MB | ~20s | 无 |
| VS09 孟菲斯扁平 | 535KB | ~20s | 无 |
| VS18 实验室蓝图 | 1.1MB | ~30s | `PRODUCER_LOW_MEMORY_MODE=true` |
| VS07 漫画波普 | 853KB | ~20s | 无 |
| VS16 排列平铺 | 268KB | ~18s | 无 |

## 关键教训

### 1. GSAP repeat 不能用 -1
- VS18首次渲染因 `repeat:-1` 导致 `Set maximum size exceeded`
- 修复：所有 `repeat:-1` → `repeat:3`（25秒内循环3次足够）

### 2. CSS transform 与 GSAP 冲突
- VS07 中 `.product-box { transform: scale(0.8) }` 与 GSAP 动画冲突
- 修复：CSS 中不写 `transform`，全部用 GSAP `fromTo()` 控制

### 3. 文件大小差异巨大
- 纯白背景+几何图形（VS16）：268KB
- 纹理背景+粒子（VS05）：1.8MB
- 背景越复杂，文件越大

### 4. 配音字数控制
- 25秒视频上限：100字（25×4字/秒）
- 实际配音范围：52-89字
- 建议：4场景视频，开场3-5字+讲解40-60字+结尾10-15字

### 5. 渲染命令
```bash
# 标准渲染（4个风格）
bash render.sh

# VS18蓝图需要低内存模式
PRODUCER_LOW_MEMORY_MODE=true bash render.sh
```

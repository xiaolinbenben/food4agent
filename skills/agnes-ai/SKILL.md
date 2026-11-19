---
name: agnes-ai
description: 使用 Agnes AI 全模态 API 生成短视频内容。工作流：文本生成脚本 → 图片生成场景 → 视频生成/动画 → 下载合并。适用于自媒体短视频、电台风格视频、解说类视频、画面配文类内容创作。触发词：生成视频、制作视频、agnes视频、短视频生成、电台视频、解说视频、场景视频、视频脚本、文生视频、图生视频。
version: 1.0.0
---

# Agnes AI 视频工坊

通过 Agnes AI 全模态 API（文本 + 图片 + 视频）实现完整的短视频制作工作流。

## 前置条件

1. **API Key**：在 https://platform.agnes-ai.com/ 注册并获取 API Key
2. **环境变量**：设置 `AGNES_API_KEY`（或 `AGNES_API_TOKEN` / `APIHUB_AGNES_API_KEY`）
3. **Python 3.10+**：脚本使用标准库，无需额外安装

## 工作流程概览

```
用户输入主题/描述
    │
    ├─ Step 1: 生成脚本（文本 API）
    │     agnes-2.0-flash → 分镜脚本 + 每镜描述
    │
    ├─ Step 2: 生成场景图片（图片 API）
    │     agnes-image-2.1-flash → 每个分镜一张关键帧图片
    │
    ├─ Step 3: 图片转视频（视频 API）
    │     agnes-video-v2.0 → 每张图片生成一段动画视频
    │
    └─ Step 4: 下载素材 + 可选合并
          下载所有图片和视频文件到输出目录
```

## 命令参考

所有脚本位于 `scripts/` 目录，运行时需设置 `AGNES_API_KEY` 环境变量。

### Step 1 - 生成视频脚本

```bash
python scripts/generate_script.py --topic "描述主题" [--style 电台/解说/诗意/纪实] [--duration 30] [--output-dir ./output]
```

参数：
- `--topic`：视频主题描述（必填）
- `--style`：视频风格，可选 `电台`（默认）、`解说`、`诗意`、`纪实`
- `--duration`：目标视频时长（秒），默认 30
- `--output-dir`：输出目录，默认 `./output`
- `--scenes`：指定分镜数量，默认根据时长自动计算（约每 5 秒一镜）
- `--raw`：输出原始 API 响应

输出：`{output_dir}/script.json`，包含分镜列表，每个分镜有 `narration`（旁白）和 `visual_prompt`（画面描述）

### Step 2 - 生成场景图片

```bash
python scripts/generate_images.py --script ./output/script.json [--output-dir ./output] [--size 1152x768]
```

参数：
- `--script`：Step 1 输出的脚本 JSON 文件路径（必填）
- `--output-dir`：输出目录，默认与脚本同目录
- `--size`：图片尺寸，默认 `1152x768`
- `--parallel`：并行请求数，默认 1（串行，更稳定）
- `--raw`：输出原始 API 响应

输出：`{output_dir}/images/scene_N.png`，每镜一张图片；更新 `script.json` 中每镜的 `image_path`

### Step 3 - 图片转视频

**模式 A：脚本驱动（默认）**

```bash
python scripts/generate_videos.py --script ./output/script.json [--output-dir ./output] [--num-frames 81] [--frame-rate 24]
```

参数：
- `--script`：Step 2 输出的脚本 JSON 文件路径（必填）
- `--output-dir`：输出目录，默认与脚本同目录
- `--num-frames`：每段视频帧数，默认 81（约 3.4 秒）
- `--frame-rate`：帧率，默认 24
- `--seed`：随机种子（可选，用于可复现结果）
- `--timeout`：轮询超时（秒），默认 900
- `--interval`：轮询间隔（秒），默认 10
- `--raw`：输出原始 API 响应

输出：`{output_dir}/videos/scene_N.mp4`，每镜一段视频；更新 `script.json` 中每镜的 `video_path`

**模式 B：自定义图片 + 提示词（单图单视频）**

```bash
python scripts/generate_videos.py --prompt "请基于图片生成广告宣传视频" --images img1.png,img2.png --output-dir ./output
```

参数：
- `--prompt`：视频描述提示词（必填）
- `--images`：逗号分隔的本地图片文件路径列表（必填）
- `--mode`：`single`（默认）= 每张图片生成一段视频，`keyframes` = 多张图片作为关键帧生成一段视频
- `--num-frames`：默认 121（约 5 秒），关键帧模式建议 121
- 其余参数同上

**模式 C：多图关键帧动画**

```bash
python scripts/generate_videos.py --prompt "从这张照片过渡到那张照片" --mode keyframes --images img1.png,img2.png,img3.png --num-frames 121
```

输出：`{output_dir}/videos/output.mp4`，包含所有图片关键帧的过渡动画；同时生成 `script.json`

输出：`{output_dir}/videos/output_N.mp4`，每张图片对应一个视频；同时更新 `script.json`

### Step 4 - 下载素材

```bash
python scripts/download_assets.py --script ./output/script.json [--output-dir ./output]
```

从 API 返回的 URL 下载所有图片和视频到本地。

### 一键全流程

```bash
python scripts/full_pipeline.py --topic "描述主题" [--style 电台] [--duration 30] [--output-dir ./output]
```

自动执行 Step 1-4 全部流程。

## 风格预设

### 电台风格（默认）
- 温暖、柔和的画面色调
- 缓慢的镜头运动
- 每镜 3-5 秒，配合旁白节奏
- 视觉提示词偏向：诗意、电影感、柔光、暖色调

### 解说风格
- 信息密度较高
- 画面切换稍快
- 包含标题、文字叠加视觉元素
- 视觉提示词偏向：清晰、信息图风格、明亮

### 诗意风格
- 极简画面、留白多
- 长镜头
- 视觉提示词偏向：抽象、梦幻、水彩、极简

### 纪实风格
- 写实画面
- 自然光线
- 视觉提示词偏向：纪实、自然光、真实场景

## API 参考

详细 API 参数见 `references/api.md`。

关键信息：
- Base URL: `https://apihub.agnes-ai.com`
- 认证: `Authorization: Bearer YOUR_API_KEY`
- 文本模型: `agnes-2.0-flash`，端点 `POST /v1/chat/completions`
- 图片模型: `agnes-image-2.1-flash`，端点 `POST /v1/images/generations`
- 视频模型: `agnes-video-v2.0`，端点 `POST /v1/videos`（异步）+ `GET /v1/videos/{task_id}`（轮询）
- 视频帧数约束：`8n + 1` 且 ≤ 441
- 推荐视频尺寸：1152x768

## 注意事项

- Agnes 视频生成使用英文提示词更稳定，脚本会自动将中文提示词翻译为英文
- 视频生成是异步的，单段视频可能需要 1-10 分钟
- 建议先小规模测试（2-3 个分镜）再批量生成
- 免费额度可能有限制，注意 API 调用量
- `num_frames=81` 适合短片段（约 3.4 秒），`num_frames=121` 适合稍长片段（约 5 秒）

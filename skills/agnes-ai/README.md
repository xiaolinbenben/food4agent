# Agnes AI 视频工坊

`Agnes AI 视频工坊` 是一个用于调用 Agnes AI 全模态 API 生成短视频素材的 Workbuddy skill。它把短视频制作拆成四个阶段：生成分镜脚本、生成场景图片、图片转视频、下载本地素材，适合制作自媒体短视频、电台风格视频、知识解说视频、诗意画面配文和纪实感短片。

## 适用场景

- 根据一个主题快速生成短视频分镜脚本
- 为每个分镜生成关键帧图片
- 将关键帧图片转成短视频片段
- 批量下载图片和视频素材到本地
- 为后续剪辑、配音、字幕和合成准备结构化素材

## 前置条件

1. 在 [Agnes AI 平台](https://platform.agnes-ai.com/) 注册并获取 API Key。
2. 安装 Python 3.10 或更高版本。
3. 安装 `requests` 依赖：

   ```bash
   python -m pip install requests
   ```

4. 设置 API Key 环境变量。脚本会依次读取以下变量之一：

   - `AGNES_API_KEY`
   - `AGNES_API_TOKEN`
   - `APIHUB_AGNES_API_KEY`

   PowerShell 示例：

   ```powershell
   $env:AGNES_API_KEY="你的_API_Key"
   ```

   Bash 示例：

   ```bash
   export AGNES_API_KEY="你的_API_Key"
   ```

## 快速开始

在 skill 根目录运行一键流程：

```bash
python scripts/full_pipeline.py --topic "一段关于城市夜归人的温暖短片" --style 电台 --duration 30 --output-dir ./output
```

执行完成后，主要输出会保存在：

```text
output/
  script.json
  images/
    scene_01.png
    scene_02.png
  videos/
    scene_01.mp4
    scene_02.mp4
```

`script.json` 会记录主题、风格、总时长、分镜列表，以及每个分镜的旁白、画面提示词、镜头运动、图片 URL、本地图片路径、视频 URL 和本地视频路径。

## 分步使用

### 1. 生成分镜脚本

```bash
python scripts/generate_script.py --topic "描述你的短视频主题" --style 电台 --duration 30 --output-dir ./output
```

常用参数：

- `--topic`：视频主题，必填
- `--style`：风格，可选 `电台`、`解说`、`诗意`、`纪实`
- `--duration`：目标总时长，默认 `30`
- `--scenes`：指定分镜数量；不指定时会按时长自动估算
- `--output-dir`：输出目录，默认 `./output`
- `--raw`：输出完整生成结果

输出文件：

```text
output/script.json
```

### 2. 生成场景图片

```bash
python scripts/generate_images.py --script ./output/script.json --size 1152x768
```

常用参数：

- `--script`：上一步生成的 `script.json`
- `--output-dir`：输出目录；默认使用 `script.json` 所在目录
- `--size`：图片尺寸，默认 `1152x768`
- `--parallel`：并行请求数，默认 `1`
- `--raw`：在结果中保留原始 API 响应

输出文件：

```text
output/images/scene_01.png
output/images/scene_02.png
```

脚本也会回写 `script.json`，为每个分镜补充 `image_url` 和 `image_path`。

### 3. 生成视频片段

```bash
python scripts/generate_videos.py --script ./output/script.json --num-frames 81 --frame-rate 24
```

常用参数：

- `--script`：包含图片信息的 `script.json`
- `--output-dir`：输出目录；默认使用 `script.json` 所在目录
- `--num-frames`：每段视频帧数，必须满足 `8n + 1` 且不超过 `441`，常用值为 `81`、`121`、`241`
- `--frame-rate`：帧率，默认 `24`
- `--width` / `--height`：视频尺寸，默认 `1152x768`
- `--seed`：随机种子，用于结果复现
- `--timeout`：单个视频任务轮询超时，默认 `900` 秒
- `--interval`：轮询间隔，默认 `10` 秒
- `--raw`：在结果中保留原始 API 响应

输出文件：

```text
output/videos/scene_01.mp4
output/videos/scene_02.mp4
```

脚本会优先使用 `image_url` 做图生视频。如果某个视频文件已经存在，会跳过该分镜，便于中断后继续运行。

### 4. 下载素材

如果 `script.json` 里已有远程 URL，但本地文件缺失，可以运行：

```bash
python scripts/download_assets.py --script ./output/script.json
```

它会根据 `image_url` 和 `video_url` 下载缺失的图片或视频，并回写本地路径。

## 风格说明

| 风格 | 适合内容 | 画面倾向 |
| --- | --- | --- |
| `电台` | 情绪短片、生活感旁白、温暖故事 | 电影感、暖色调、柔光、舒缓镜头 |
| `解说` | 知识类、观点类、信息类视频 | 清晰明亮、信息密度高、现代设计感 |
| `诗意` | 文艺短片、抽象表达、画面配文 | 极简、留白、梦幻、水彩、长镜头 |
| `纪实` | 真实场景、人物故事、观察类内容 | 写实、自然光、真实环境、手持感 |

## 参数建议

- 小规模测试：先用 `--scenes 2 --num-frames 81` 验证 API Key、额度和风格效果。
- 30 秒短片：可使用 `--duration 30 --num-frames 81`，通常会生成多个 3 秒左右片段。
- 更长片段：可把 `--num-frames` 调整为 `121`，约 5 秒，生成耗时也会增加。
- 稳定复现：传入 `--seed`，但实际一致性仍取决于服务端模型行为。
- 中文主题可以直接输入；视频提示词会尽量使用英文描述，以提高图像和视频生成稳定性。

## API 信息

默认服务地址：

```text
https://apihub.agnes-ai.com/v1
```

脚本使用的模型：

- 文本：`agnes-2.0-flash`
- 图片：`agnes-image-2.1-flash`
- 视频：`agnes-video-v2.0`

更详细的接口字段见 `references/api.md`。

## 常见问题

### 缺少 API Key

如果看到类似错误：

```text
Missing API key. Set AGNES_API_KEY, AGNES_API_TOKEN, or APIHUB_AGNES_API_KEY.
```

请确认当前终端会话已经设置环境变量，并且变量值没有多余空格或引号。

### 缺少 requests

如果看到：

```text
The 'requests' library is required. Install it with: pip install requests
```

运行：

```bash
python -m pip install requests
```

### 视频生成很慢

视频接口是异步任务。每个分镜可能需要数分钟，脚本会轮询任务状态。可以通过 `--timeout` 增加等待时间，或先减少 `--scenes` 和 `--num-frames` 做测试。

### num_frames 参数报错

`--num-frames` 必须满足 `8n + 1` 且不超过 `441`。推荐使用：

```text
81, 121, 161, 241, 441
```

### 生成到一半中断

可以重新运行 `generate_videos.py`。如果某个分镜的视频文件已经存在，脚本会自动跳过该分镜。

## 目录结构

```text
.
  SKILL.md
  README.md
  references/
    api.md
  scripts/
    api_client.py
    generate_script.py
    generate_images.py
    generate_videos.py
    download_assets.py
    full_pipeline.py
```

## 给 Workbuddy 使用时的建议

当用户提出“生成视频”“制作短视频”“文生视频”“图生视频”“电台视频”“解说视频”等需求时，可以调用本 skill。建议先明确主题、风格、目标时长和输出目录；如果用户没有指定，默认使用 `电台` 风格、`30` 秒、`./output` 输出目录，并优先小规模测试后再批量生成。

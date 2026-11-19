---
name: douyin-video-insight
description: 抖音视频下载、ASR转录、AI总结与章节分析
metadata: { "openclaw": { "emoji": "🎬" } }
---

# 抖音视频洞察

输入抖音视频链接，自动下载视频、提取音频、ASR转录，生成关键观点总结和章节分析。

## 触发方式
- "分析这个抖音视频 https://v.douyin.com/..."
- "帮我总结这个视频 https://www.douyin.com/video/..."
- "拆解这个短视频的内容"

## 使用方法

### 基础用法

python3 /root/workspace/skills/douyin-video-insight/insight.py --url "https://v.douyin.com/xxxxx"
包含全量转录


python3 /root/workspace/skills/douyin-video-insight/insight.py --url "https://v.douyin.com/xxxxx" --include-transcript
指定 whisper 模型


python3 /root/workspace/skills/douyin-video-insight/insight.py --url "https://v.douyin.com/xxxxx" --whisper-model medium
输出
report.md - 完整分析报告
video.mp4 - 原始视频
audio.wav - 提取的音频
transcript.json - ASR 转录结果（含时间戳）
环境变量
DOUYIN_COOKIES - cookies 文件路径（可选，用于私密视频）
DASHSCOPE_API_KEY - DashScope API Key（必需）
依赖
yt-dlp
ffmpeg
faster-whisper
httpx

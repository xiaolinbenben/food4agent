# 抖音视频洞察 (Douyin Video Insight)

自动下载抖音视频、ASR 转录、AI 生成章节分析报告。

## 功能

1. **下载视频** - 使用 yt-dlp 下载抖音视频
2. **提取音频** - 使用 ffmpeg 转换为 16kHz mono WAV
3. **ASR 转录** - 使用 faster-whisper 生成带时间戳的转录
4. **AI 分析** - 使用 DashScope qwen-plus 生成：
   - 关键观点总结（5-10 条）
   - 重点章节分析（6-12 章，带时间范围）
   - 行动清单

## 安装依赖

### 方式 1：容器内安装

# 进入容器
docker exec -it clawdbot bash

# 安装系统依赖
apt-get update && apt-get install -y ffmpeg

# 安装 Python 依赖
pip install yt-dlp faster-whisper httpx
方式 2：Dockerfile（推荐）
在 Dockerfile 中添加：

Dockerfile

RUN apt-get update && apt-get install -y ffmpeg \
    && pip install yt-dlp faster-whisper httpx
使用方法
基础用法

python3 /root/workspace/skills/douyin-video-insight/insight.py \
    --url "https://v.douyin.com/xxxxx"
包含全量转录

python3 /root/workspace/skills/douyin-video-insight/insight.py \
    --url "https://v.douyin.com/xxxxx" \
    --include-transcript
使用更大的 Whisper 模型（更准确但更慢）

python3 /root/workspace/skills/douyin-video-insight/insight.py \
    --url "https://v.douyin.com/xxxxx" \
    --whisper-model medium
配置
环境变量
变量	说明	默认值
DASHSCOPE_API_KEY	DashScope API Key	必需
DOUYIN_COOKIES	Cookies 文件路径	/root/workspace/secrets/cookies.txt
API Key 配置
方式 1：环境变量


export DASHSCOPE_API_KEY="sk-xxxx"
方式 2：在 /root/workspace/secrets/.env 中添加


DASHSCOPE_API_KEY=sk-xxxx
输出文件
所有文件保存在 /root/workspace/data/douyin_cache/<timestamp>/：

文件	说明
video.mp4	原始视频
audio.wav	提取的音频（16kHz mono）
transcript.json	ASR 转录结果（含时间戳）
report.md	最终分析报告
常见问题
1. 下载失败：需要登录
现象：提示 login required 或 cookie

解决：

在浏览器登录抖音 (douyin.com)
使用浏览器扩展导出 cookies（如 "Get cookies.txt LOCALLY"）
保存到 /root/workspace/secrets/cookies.txt
重新运行
2. 转录很慢
原因：faster-whisper 在 CPU 上运行较慢

解决：

使用更小的模型：--whisper-model tiny 或 base
短视频（<5分钟）建议用 small
长视频（>10分钟）建议用 tiny 或 base
3. 模型下载慢
原因：首次运行需要下载 Whisper 模型

解决：

模型会缓存在 ~/.cache/huggingface/
可以预先下载：
Python

from faster_whisper import WhisperModel
WhisperModel("small", device="cpu")
4. 内存不足
现象：OOM 或进程被 kill

解决：

使用更小的模型：--whisper-model tiny
增加容器内存限制
5. LLM 调用失败
现象：DASHSCOPE_API_KEY not found

解决：

检查环境变量是否设置
检查 .env 文件路径是否正确
确认 API Key 有效
Whisper 模型对比
模型	大小	内存	速度	准确度
tiny	75MB	~1GB	最快	一般
base	142MB	~1GB	快	较好
small	466MB	~2GB	中等	好
medium	1.5GB	~5GB	慢	很好
large	3GB	~10GB	最慢	最好
推荐：

快速预览：tiny
日常使用：small
高质量需求：medium
示例输出
Markdown

# 视频拆解：创业者如何找到产品市场契合点

## 关键观点

1. PMF 不是一个时刻，而是一个持续的状态
2. 用户留存率比用户增长更重要
3. ...

## 重点章节

### 00:00-02:30 什么是 PMF

**要点**：
- Product Market Fit 是产品与市场的契合
- 判断标准：用户会不会推荐给朋友
- ...

**关键原话**：
> [01:15] "如果你的产品消失了，用户会不会难过？"

### 02:30-05:00 如何衡量 PMF
...

## 行动清单

1. 每周统计 NPS 分数
2. 建立用户访谈机制
3. ...
开发说明
文件结构

douyin-video-insight/
├── SKILL.md          # OpenClaw skill 描述
├── README.md         # 本文档
├── insight.py        # 主程序
└── requirements.txt  # Python 依赖
扩展
支持其他平台：修改 download_video() 函数，yt-dlp 支持多平台
更换 LLM：修改 call_llm() 函数
自定义 prompt：修改 CHUNK_PROMPT 和 SUMMARY_PROMPT

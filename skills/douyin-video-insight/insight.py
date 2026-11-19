#!/usr/bin/env python3
"""
视频洞察 - 下载、转录、AI分析
支持：YouTube / Bilibili / 抖音
"""

import argparse
import asyncio
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# ================================================================
# 配置
# ================================================================

CACHE_DIR = Path("/root/workspace/data/douyin_cache")
ENV_FILE = "/root/workspace/secrets/.env"
HOST_ENV_FILE = os.path.expanduser("~/tanwei-bot/.env")

DASHSCOPE_API_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
DEFAULT_MODEL = "qwen-plus"
DEFAULT_WHISPER_MODEL = "small"


# ================================================================
# 工具函数
# ================================================================

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def load_env():
    env = {}
    for path in [ENV_FILE, HOST_ENV_FILE]:
        if os.path.exists(path):
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        k, v = line.split('=', 1)
                        env[k.strip()] = v.strip().strip('"\'')
    return env


def get_api_key():
    key = os.environ.get("DASHSCOPE_API_KEY")
    if not key:
        env = load_env()
        key = env.get("DASHSCOPE_API_KEY")
    if not key:
        raise ValueError("未找到 DASHSCOPE_API_KEY")
    return key


def call_llm(prompt, system_prompt="", model=DEFAULT_MODEL, max_tokens=4000):
    import httpx
    api_key = get_api_key()
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    try:
        resp = httpx.post(DASHSCOPE_API_URL, json={
            "model": model, "messages": messages, "max_tokens": max_tokens,
        }, headers={
            "Authorization": f"Bearer {api_key}", "Content-Type": "application/json",
        }, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        tokens = data.get("usage", {}).get("total_tokens", 0)
        log(f"LLM 完成: {len(content)} 字符, tokens={tokens}")
        return content
    except Exception as e:
        log(f"LLM 调用失败: {e}")
        raise


def format_time(seconds):
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"


# ================================================================
# 抖音专用下载
# ================================================================

async def download_douyin_video(url, output_dir):
    """通过抖音分享页面解析下载视频"""
    import aiohttp
    
    log("解析抖音短链...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 12) AppleWebKit/537.36 Chrome/107.0.0.0 Mobile Safari/537.36'
    }
    
    async with aiohttp.ClientSession() as session:
        # 1. 短链跳转获取视频ID
        async with session.get(url, headers=headers, allow_redirects=True,
                               timeout=aiohttp.ClientTimeout(total=15)) as resp:
            final_url = str(resp.url)
        
        match = re.search(r'video/(\d+)', final_url)
        if not match:
            raise RuntimeError(f"无法提取视频ID: {final_url}")
        
        video_id = match.group(1)
        log(f"视频ID: {video_id}")
        
        # 2. 访问分享页面提取视频链接
        share_url = f"https://www.iesdouyin.com/share/video/{video_id}/"
        log("获取视频页面...")
        async with session.get(share_url, headers=headers,
                               timeout=aiohttp.ClientTimeout(total=15)) as resp:
            html = await resp.text()
        
        # 提取视频 URL
        video_url = None
        patterns = [
            r'"play_addr".*?"url_list":\["(.*?)"',
            r'playAddr.*?src.*?:"(https?://[^"]+)"',
            r'src="(https?://.*?\.mp4[^"]*)"',
        ]
        for p in patterns:
            matches = re.findall(p, html)
            if matches:
                video_url = matches[0].replace(r'\u002F', '/')
                break
        
        if not video_url:
            raise RuntimeError("无法从页面提取视频链接")
        
        # 去水印
        video_url = video_url.replace('/playwm/', '/play/')
        
        # 提取视频信息
        info = {"title": "未知标题", "uploader": "未知作者", "duration": 0, "description": ""}
        
        title_match = re.search(r'"desc":"(.*?)"', html)
        if title_match:
            info["title"] = title_match.group(1)
        
        author_match = re.search(r'"nickname":"(.*?)"', html)
        if author_match:
            info["uploader"] = author_match.group(1)
        
        duration_match = re.search(r'"duration":(\d+)', html)
        if duration_match:
            info["duration"] = int(duration_match.group(1)) // 1000
        
        log(f"标题: {info['title']}")
        log(f"作者: {info['uploader']}")
        
        # 3. 下载视频
        log("下载视频文件...")
        video_path = output_dir / "video.mp4"
        async with session.get(video_url, headers=headers,
                               timeout=aiohttp.ClientTimeout(total=120)) as resp:
            if resp.status != 200:
                raise RuntimeError(f"视频下载失败: HTTP {resp.status}")
            with open(video_path, 'wb') as f:
                while True:
                    chunk = await resp.content.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)
        
        file_size = video_path.stat().st_size
        log(f"下载完成: {video_path} ({file_size // 1024}KB)")
        return {"video_path": video_path, "info": info}


# ================================================================
# 通用下载 (yt-dlp)
# ================================================================

def download_ytdlp(url, output_dir):
    """使用 yt-dlp 下载视频"""
    log(f"使用 yt-dlp 下载: {url}")
    video_path = output_dir / "video.mp4"
    
    cmd = [
        "yt-dlp",
        "-o", str(video_path),
        "--write-info-json",
        "--no-playlist",
        "--no-check-certificates",
        "--user-agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        url
    ]
    
    cookies_path = os.environ.get("DOUYIN_COOKIES", "/root/workspace/secrets/cookies.txt")
    if os.path.exists(cookies_path):
        log(f"使用 cookies: {cookies_path}")
        cmd.extend(["--cookies", cookies_path])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            raise RuntimeError(f"yt-dlp 失败: {result.stderr[:500]}")
        
        # 找到实际视频文件
        video_files = [f for f in output_dir.glob("video.mp4*") if not f.name.endswith('.json')]
        if video_files:
            video_path = video_files[0]
        
        log(f"下载完成: {video_path}")
        
        # 读取视频信息
        info = {"title": "未知标题", "uploader": "未知作者", "duration": 0, "description": ""}
        info_files = list(output_dir.glob("*.info.json"))
        if info_files:
            with open(info_files[0]) as f:
                raw = json.load(f)
                info = {
                    "title": raw.get("title", "未知标题"),
                    "uploader": raw.get("uploader", "未知作者"),
                    "duration": raw.get("duration", 0),
                    "description": raw.get("description", ""),
                }
        
        return {"video_path": video_path, "info": info}
    except subprocess.TimeoutExpired:
        raise RuntimeError("下载超时（>5分钟）")


# ================================================================
# 统一下载入口
# ================================================================

def download_video(url, output_dir):
    """自动选择下载器"""
    log(f"开始下载视频: {url}")
    
    if "douyin.com" in url or "iesdouyin.com" in url:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(download_douyin_video(url, output_dir))
        finally:
            loop.close()
    else:
        return download_ytdlp(url, output_dir)


# ================================================================
# 音频提取
# ================================================================

def extract_audio(video_path, output_dir):
    log("提取音频...")
    audio_path = output_dir / "audio.wav"
    cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
        str(audio_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg 失败: {result.stderr[:300]}")
    log(f"音频提取完成: {audio_path}")
    return audio_path


# ================================================================
# ASR 转录
# ================================================================

def transcribe_audio(audio_path, output_dir, model=DEFAULT_WHISPER_MODEL):
    log(f"ASR 转录 (模型: {model})...")
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise RuntimeError("未安装 faster-whisper")
    
    log(f"加载 Whisper 模型: {model}")
    whisper = WhisperModel(model, device="cpu", compute_type="int8")
    
    log("开始转录...")
    segments_iter, info = whisper.transcribe(
        str(audio_path), language="zh", vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500),
    )
    
    segments = []
    for seg in segments_iter:
        segments.append({
            "start": round(seg.start, 2),
            "end": round(seg.end, 2),
            "text": seg.text.strip(),
        })
        if len(segments) % 10 == 0:
            log(f"已转录 {len(segments)} 段...")
    
    log(f"转录完成: {len(segments)} 段")
    
    with open(output_dir / "transcript.json", "w", encoding="utf-8") as f:
        json.dump(segments, f, ensure_ascii=False, indent=2)
    
    return segments


# ================================================================
# LLM 分析
# ================================================================

CHUNK_PROMPT = """你是视频内容分析助手。下面给你一段"带时间戳的转录片段"。
请输出严格 JSON，字段如下：
- range: "mm:ss-mm:ss"
- title: 本段小标题（不超过12字）
- bullets: 3-6条要点
- key_quotes: 1-3条关键原话，每条含 time 和 quote

转录片段：
{segments_text}

只输出 JSON，不要额外解释。"""

SUMMARY_PROMPT = """你是"短视频拆解与学习笔记"助手。
根据以下 chunk JSON 摘要，生成 Markdown 报告：

# 视频拆解：一句话总览
## 关键观点（5-10条，按重要性排序）
## 重点章节（6-12章，带时间范围，每章：标题+要点+关键原话）
## 行动清单（3-8条可执行行动）

约束：不编造信息；章节覆盖全片；语言简洁。

视频信息：
{video_info}

chunk JSON 列表：
{chunk_json_list}"""


def chunk_segments(segments, chunk_duration=180):
    if not segments:
        return []
    chunks, current, start = [], [], segments[0]["start"]
    for seg in segments:
        current.append(seg)
        if seg["end"] - start >= chunk_duration:
            chunks.append(current)
            current, start = [], seg["end"]
    if current:
        chunks.append(current)
    return chunks


def analyze_chunk(chunk, chunk_index):
    lines = [f"[{format_time(s['start'])}] {s['text']}" for s in chunk]
    time_range = f"{format_time(chunk[0]['start'])}-{format_time(chunk[-1]['end'])}"
    log(f"分析 Chunk {chunk_index + 1}: {time_range}")
    
    response = call_llm(CHUNK_PROMPT.format(segments_text="\n".join(lines)))
    response = response.strip()
    if response.startswith("```"):
        response = re.sub(r'^```json?\n?', '', response)
        response = re.sub(r'\n?```$', '', response)
    
    try:
        result = json.loads(response)
        result["chunk_index"] = chunk_index
        if "range" not in result:
            result["range"] = time_range
        return result
    except json.JSONDecodeError:
        return {
            "chunk_index": chunk_index, "range": time_range,
            "title": f"片段 {chunk_index + 1}", "bullets": ["解析失败"],
            "key_quotes": [], "raw_response": response[:500]
        }


def generate_report(chunks_analysis, video_info, include_transcript, segments):
    log("生成最终报告...")
    info_str = f"- 标题: {video_info.get('title', '未知')}\n- 作者: {video_info.get('uploader', '未知')}\n- 时长: {format_time(video_info.get('duration', 0))}"
    chunk_json_str = json.dumps(chunks_analysis, ensure_ascii=False, indent=2)
    
    report = call_llm(SUMMARY_PROMPT.format(
        video_info=info_str, chunk_json_list=chunk_json_str
    ), max_tokens=4000)
    
    if include_transcript and segments:
        report += "\n\n---\n\n## 全量转录\n\n"
        for seg in segments:
            report += f"**[{format_time(seg['start'])}]** {seg['text']}\n\n"
    
    return report


# ================================================================
# 主流程
# ================================================================

def process_video(url, whisper_model=DEFAULT_WHISPER_MODEL, include_transcript=False):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    work_dir = CACHE_DIR / datetime.now().strftime("%Y%m%d_%H%M%S")
    work_dir.mkdir(exist_ok=True)
    log(f"工作目录: {work_dir}")
    
    # 1. 下载
    result = download_video(url, work_dir)
    video_path = result["video_path"]
    video_info = result["info"]
    
    # 2. 提取音频
    audio_path = extract_audio(video_path, work_dir)
    
    # 3. 转录
    segments = transcribe_audio(audio_path, work_dir, whisper_model)
    if not segments:
        raise RuntimeError("转录结果为空")
    
    # 4. 分块分析
    log("开始 LLM 分析...")
    chunks = chunk_segments(segments, chunk_duration=180)
    log(f"共 {len(chunks)} 个 chunk")
    
    chunks_analysis = []
    for i, chunk in enumerate(chunks):
        analysis = analyze_chunk(chunk, i)
        chunks_analysis.append(analysis)
        time.sleep(0.5)
    
    # 5. 生成报告
    report = generate_report(chunks_analysis, video_info, include_transcript, segments)
    
    report_path = work_dir / "report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    
    log(f"✅ 报告已生成: {report_path}")
    return report


def main():
    parser = argparse.ArgumentParser(description="视频洞察 - 下载、转录、AI分析")
    parser.add_argument("--url", required=True, help="视频链接")
    parser.add_argument("--whisper-model", default=DEFAULT_WHISPER_MODEL,
                        choices=["tiny", "base", "small", "medium", "large"],
                        help="Whisper 模型 (默认: small)")
    parser.add_argument("--include-transcript", action="store_true",
                        help="包含全量转录")
    args = parser.parse_args()
    
    try:
        report = process_video(args.url, args.whisper_model, args.include_transcript)
        print("\n" + "=" * 60)
        print(report)
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ 错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

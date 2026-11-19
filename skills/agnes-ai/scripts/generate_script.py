"""Step 1: Generate video script from topic using Agnes text API."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from api_client import generate_text, needs_english_translation, translate_to_english


STYLE_PROMPTS = {
    "电台": (
        "你是一个短视频脚本创作者，擅长制作电台/播客风格的短视频。"
        "画面温暖柔和，配合旁白，节奏舒缓。"
        "每个分镜3-5秒，画面描述要适合AI图片生成。"
    ),
    "解说": (
        "你是一个短视频脚本创作者，擅长制作知识解说类短视频。"
        "画面清晰、信息密度高，配合解说词，节奏适中。"
        "每个分镜3-5秒，画面描述要具体、适合AI图片生成。"
    ),
    "诗意": (
        "你是一个短视频脚本创作者，擅长制作诗意/文艺风格的短视频。"
        "画面极简、留白多、意境深远，配合诗意旁白。"
        "每个分镜5-8秒，画面描述偏向抽象、梦幻、极简风格。"
    ),
    "纪实": (
        "你是一个短视频脚本创作者，擅长制作纪实风格的短视频。"
        "画面写实、自然光线、真实场景，配合纪实旁白。"
        "每个分镜4-6秒，画面描述要写实具体。"
    ),
}

STYLE_VISUAL_HINTS = {
    "电台": "cinematic, warm tones, soft lighting, gentle camera movement, atmospheric, dreamy",
    "解说": "clean, clear, informative, bright lighting, text overlay style, modern design",
    "诗意": "minimalist, abstract, watercolor, ethereal, vast negative space, poetic",
    "纪实": "documentary style, natural lighting, realistic, authentic scene, handheld camera feel",
}

SCRIPT_SYSTEM_PROMPT = """\
你是一个专业的短视频分镜脚本撰写者。根据用户给出的主题，生成一个完整的分镜脚本。

输出格式必须为严格的JSON数组，每个元素是一个分镜对象，包含：
- "scene": 分镜编号（从1开始）
- "narration": 该分镜的旁白/解说文字（中文）
- "visual_prompt": 该分镜的画面描述（英文），用于AI图片和视频生成，需包含：主体 + 场景 + 风格 + 光线 + 构图 + 镜头运动
- "camera_motion": 镜头运动描述（英文），如 slow pan left, gentle zoom in, static shot 等
- "duration": 该分镜持续时间（秒）

要求：
1. 旁白文字要有感染力，适合配音朗读
2. visual_prompt 必须是英文，具体且详细
3. 画面描述要适合AI生成，避免过于抽象或不可能实现的画面
4. 每个分镜之间要有自然的视觉过渡
5. 只输出JSON数组，不要有任何其他文字
"""


def generate_script(topic: str, style: str = "电台", duration: int = 30,
                   num_scenes: int | None = None) -> list[dict]:
    if num_scenes is None:
        avg_scene_duration = 4 if style == "诗意" else 4
        num_scenes = max(2, min(12, duration // avg_scene_duration))

    visual_hint = STYLE_VISUAL_HINTS.get(style, "")
    style_system = STYLE_PROMPTS.get(style, STYLE_PROMPTS["电台"])

    full_system = f"{style_system}\n\n画面风格要求：{visual_hint}"

    # Translate topic to English for better understanding if needed
    topic_en = topic
    if needs_english_translation(topic):
        topic_en = f"{topic}\n(Original topic language: {topic})"

    prompt = f"""\
请为主题「{topic}」生成一个{style}风格的短视频分镜脚本。

总时长约 {duration} 秒，共 {num_scenes} 个分镜。

请确保：
1. 每个分镜的旁白自然流畅，可以连贯朗读
2. 画面描述用英文，详细到可以直接用于AI图片生成
3. 画面之间有视觉连贯性
4. 最后一个分镜有收尾感

输出格式：JSON数组，每个元素包含 scene, narration, visual_prompt, camera_motion, duration 字段。
只输出JSON，不要输出其他任何文字。"""

    raw = None
    last_error = None
    for attempt in range(3):
        try:
            raw = generate_text(prompt, system=full_system, temperature=0.8, max_tokens=3000, json_mode=True)
            break
        except Exception as exc:
            last_error = exc
            if attempt < 2:
                print(f"  Script generation failed (attempt {attempt + 1}/3), retrying: {exc}", file=sys.stderr)
                time.sleep(3 * (attempt + 1))
                continue
            raise
    if raw is None:
        raise SystemExit(f"Script generation failed after retries: {last_error}")

    # Strip markdown code block if present
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
    if raw.endswith("```"):
        raw = raw[:-3]
    if raw.startswith("json"):
        raw = raw[4:].strip()

    try:
        scenes = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"Warning: Failed to parse script JSON, trying to extract...", file=sys.stderr)
        # Try to find JSON array in the response
        import re
        match = re.search(r'\[.*\]', raw, re.DOTALL)
        if match:
            scenes = json.loads(match.group())
        else:
            raise SystemExit(f"Cannot parse script output: {raw[:500]}") from exc

    if not isinstance(scenes, list):
        # LLM might wrap the array in an object like {"scenes": [...]}
        # or return a single scene object instead of an array
        if isinstance(scenes, dict):
            # Check for known wrapper keys first
            for key in ("scenes", "scene_list", "data", "results", "shots", "script", "script_json", "output"):
                if key in scenes and isinstance(scenes[key], list):
                    scenes = scenes[key]
                    break
            else:
                # Check if this dict itself is a single scene (has visual_prompt or narration)
                if "visual_prompt" in scenes or "narration" in scenes or "scene" in scenes:
                    print("  LLM returned a single scene object, wrapping in list.", file=sys.stderr)
                    scenes = [scenes]
                else:
                    raise SystemExit(f"Cannot find scene list in JSON object. Keys: {list(scenes.keys())}")
        else:
            raise SystemExit(f"Script output is not a list: {type(scenes)}")

    # Validate and normalize
    for i, scene in enumerate(scenes):
        scene.setdefault("scene", i + 1)
        if "visual_prompt" not in scene:
            raise SystemExit(f"Scene {i+1} missing visual_prompt")
        if "narration" not in scene:
            scene["narration"] = ""
        if "camera_motion" not in scene:
            scene["camera_motion"] = "gentle camera movement"
        if "duration" not in scene:
            scene["duration"] = duration // len(scenes)

    return scenes


def main():
    parser = argparse.ArgumentParser(description="Generate video script from topic.")
    parser.add_argument("--topic", required=True, help="Video topic description")
    parser.add_argument("--style", default="电台", choices=STYLE_PROMPTS.keys(), help="Video style")
    parser.add_argument("--duration", type=int, default=30, help="Target duration in seconds")
    parser.add_argument("--scenes", type=int, default=None, help="Number of scenes")
    parser.add_argument("--output-dir", default="./output", help="Output directory")
    parser.add_argument("--raw", action="store_true", help="Output raw API response")
    args = parser.parse_args()

    print(f"Generating {args.style} style script for: {args.topic}", file=sys.stderr)
    print(f"Target duration: {args.duration}s", file=sys.stderr)

    scenes = generate_script(args.topic, args.style, args.duration, args.scenes)

    result = {
        "topic": args.topic,
        "style": args.style,
        "duration": args.duration,
        "total_scenes": len(scenes),
        "scenes": scenes,
    }

    os.makedirs(args.output_dir, exist_ok=True)
    output_path = os.path.join(args.output_dir, "script.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\nScript generated: {len(scenes)} scenes", file=sys.stderr)
    for scene in scenes:
        print(f"  Scene {scene['scene']}: {scene['narration'][:50]}... ({scene['duration']}s)", file=sys.stderr)
    print(f"\nSaved to: {output_path}", file=sys.stderr)

    if args.raw:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps({"output": output_path, "scenes": len(scenes)}, ensure_ascii=False))


if __name__ == "__main__":
    main()

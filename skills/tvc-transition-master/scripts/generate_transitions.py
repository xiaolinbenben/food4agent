#!/usr/bin/env python3
"""tvc-transition-master: 转场方案生成"""
import argparse, json, os, sys
from datetime import datetime

def get_ark_client():
    api_key = os.environ.get("ARK_API_KEY")
    if not api_key: print("❌ 未设置 ARK_API_KEY"); sys.exit(1)
    from volcenginesdkarkruntime import Ark
    return Ark(api_key=api_key)

def main():
    parser = argparse.ArgumentParser(description="TVC转场设计")
    parser.add_argument("--storyboard", required=True)
    parser.add_argument("--style", default="cinematic", choices=["cinematic","smooth","energetic","minimal","experimental"])
    parser.add_argument("--music-bpm", type=int, default=0)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    with open(args.storyboard, "r", encoding="utf-8") as f:
        storyboard = json.load(f)

    client = get_ark_client()
    scenes = storyboard.get("scenes", [])
    prompt = f"""你是专业TVC后期剪辑师。为以下{len(scenes)}个分镜设计转场方案。

分镜脚本：{json.dumps(scenes, ensure_ascii=False)}
转场风格：{args.style}
配乐BPM：{args.music_bpm or '未指定'}

为每两个相邻场景设计转场，包含type(match_cut/silk_smooth/whip_pan/morph/light_leak/zoom_through/rhythmic_cut/invisible_cut)、detail描述、duration_ms、audio_sync说明、prompt_hint。
以JSON格式输出 {{"transitions": [...]}}"""

    resp = client.chat.completions.create(
        model="doubao-seed-2.0-thinking",
        messages=[{"role":"user","content":prompt}], temperature=0.7)
    content = resp.choices[0].message.content.strip()
    if "```json" in content: content = content.split("```json")[1].split("```")[0]
    try: result = json.loads(content)
    except: result = {"raw": content}

    result["metadata"] = {"style": args.style, "bpm": args.music_bpm, "timestamp": datetime.now().isoformat()}
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"✅ 转场方案生成 → {args.output}")

if __name__ == "__main__":
    main()

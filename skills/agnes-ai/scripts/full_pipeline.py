"""Full pipeline: topic -> script -> images -> videos -> download."""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api_client import download_url
from generate_script import generate_script
from generate_images import generate_scene_images
from generate_videos import generate_scene_videos


def full_pipeline(topic: str, style: str = "电台", duration: int = 30,
                 output_dir: str = "./output", num_frames: int = 81,
                 frame_rate: float = 24, size: str = "1152x768",
                 num_scenes: int | None = None, seed: int | None = None,
                 timeout: int = 900) -> dict:
    os.makedirs(output_dir, exist_ok=True)
    script_path = os.path.join(output_dir, "script.json")

    # Step 1: Generate script
    print("=" * 50, file=sys.stderr)
    print("Step 1/3: Generating script...", file=sys.stderr)
    print("=" * 50, file=sys.stderr)
    scenes = generate_script(topic, style, duration, num_scenes)

    script = {
        "topic": topic,
        "style": style,
        "duration": duration,
        "total_scenes": len(scenes),
        "scenes": scenes,
    }
    with open(script_path, "w", encoding="utf-8") as f:
        json.dump(script, f, ensure_ascii=False, indent=2)
    print(f"Script saved: {script_path} ({len(scenes)} scenes)\n", file=sys.stderr)

    # Step 2: Generate images
    print("=" * 50, file=sys.stderr)
    print("Step 2/3: Generating scene images...", file=sys.stderr)
    print("=" * 50, file=sys.stderr)
    img_result = generate_scene_images(script_path, output_dir, size)
    print(f"Images: {img_result['success']}/{img_result['total']}\n", file=sys.stderr)

    # Step 3: Generate videos
    print("=" * 50, file=sys.stderr)
    print("Step 3/3: Generating video clips...", file=sys.stderr)
    print("=" * 50, file=sys.stderr)
    print("This may take several minutes per scene. Please wait...\n", file=sys.stderr)
    vid_result = generate_scene_videos(
        script_path, output_dir, num_frames, frame_rate,
        seed=seed, timeout=timeout
    )
    print(f"Videos: {vid_result['success']}/{vid_result['total']}\n", file=sys.stderr)

    # Summary
    with open(script_path, "r", encoding="utf-8") as f:
        final_script = json.load(f)

    print("=" * 50, file=sys.stderr)
    print("Pipeline Complete!", file=sys.stderr)
    print("=" * 50, file=sys.stderr)
    print(f"Script: {script_path}", file=sys.stderr)
    print(f"Images: {img_result.get('image_dir', 'N/A')}", file=sys.stderr)
    print(f"Videos: {vid_result.get('video_dir', 'N/A')}", file=sys.stderr)

    for scene in final_script.get("scenes", []):
        print(f"  Scene {scene.get('scene', '?')}: "
              f"narration={scene.get('narration', '')[:30]}... "
              f"img={'OK' if scene.get('image_path') else 'MISSING'} "
              f"vid={'OK' if scene.get('video_path') else 'MISSING'}",
              file=sys.stderr)

    return {
        "script_path": script_path,
        "image_dir": img_result.get("image_dir"),
        "video_dir": vid_result.get("video_dir"),
        "total_scenes": len(scenes),
        "images_generated": img_result["success"],
        "videos_generated": vid_result["success"],
    }


def main():
    parser = argparse.ArgumentParser(description="Full video generation pipeline.")
    parser.add_argument("--topic", required=True, help="Video topic description")
    parser.add_argument("--style", default="电台", choices=["电台", "解说", "诗意", "纪实"],
                        help="Video style")
    parser.add_argument("--duration", type=int, default=30, help="Target duration in seconds")
    parser.add_argument("--output-dir", default="./output", help="Output directory")
    parser.add_argument("--num-frames", type=int, default=81, help="Frames per video clip")
    parser.add_argument("--frame-rate", type=float, default=24, help="Frame rate")
    parser.add_argument("--size", default="1152x768", help="Image size")
    parser.add_argument("--scenes", type=int, default=None, help="Number of scenes")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    parser.add_argument("--timeout", type=int, default=900, help="Video polling timeout (seconds)")
    args = parser.parse_args()

    if args.num_frames > 441 or (args.num_frames - 1) % 8 != 0:
        print("Error: --num-frames must satisfy 8n+1 and be <= 441", file=sys.stderr)
        sys.exit(1)

    result = full_pipeline(
        topic=args.topic,
        style=args.style,
        duration=args.duration,
        output_dir=args.output_dir,
        num_frames=args.num_frames,
        frame_rate=args.frame_rate,
        size=args.size,
        num_scenes=args.scenes,
        seed=args.seed,
        timeout=args.timeout,
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

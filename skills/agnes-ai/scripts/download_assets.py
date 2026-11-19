"""Step 4: Download all generated assets (images + videos) from URLs in script."""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from api_client import download_url


def download_all_assets(script_path: str, output_dir: str | None = None) -> dict:
    with open(script_path, "r", encoding="utf-8") as f:
        script = json.load(f)

    if output_dir is None:
        output_dir = os.path.dirname(script_path) or "."

    img_dir = os.path.join(output_dir, "images")
    vid_dir = os.path.join(output_dir, "videos")
    os.makedirs(img_dir, exist_ok=True)
    os.makedirs(vid_dir, exist_ok=True)

    scenes = script.get("scenes", [])
    results = {"images": 0, "videos": 0, "errors": []}

    for scene in scenes:
        scene_num = scene.get("scene", 0)

        # Download image
        img_url = scene.get("image_url")
        if img_url and not scene.get("image_path"):
            try:
                img_path = os.path.join(img_dir, f"scene_{scene_num:02d}.png")
                download_url(img_url, img_path)
                scene["image_path"] = img_path
                results["images"] += 1
                print(f"  Downloaded image for scene {scene_num}", file=sys.stderr)
            except Exception as exc:
                results["errors"].append(f"Scene {scene_num} image: {exc}")

        # Download video
        vid_url = scene.get("video_url")
        if vid_url and not scene.get("video_path"):
            try:
                vid_path = os.path.join(vid_dir, f"scene_{scene_num:02d}.mp4")
                download_url(vid_url, vid_path)
                scene["video_path"] = vid_path
                results["videos"] += 1
                print(f"  Downloaded video for scene {scene_num}", file=sys.stderr)
            except Exception as exc:
                results["errors"].append(f"Scene {scene_num} video: {exc}")

    # Update script
    script["scenes"] = scenes
    with open(script_path, "w", encoding="utf-8") as f:
        json.dump(script, f, ensure_ascii=False, indent=2)

    return results


def main():
    parser = argparse.ArgumentParser(description="Download all assets from script URLs.")
    parser.add_argument("--script", required=True, help="Path to script.json")
    parser.add_argument("--output-dir", default=None, help="Output directory")
    args = parser.parse_args()

    print(f"Downloading assets from: {args.script}", file=sys.stderr)

    result = download_all_assets(args.script, args.output_dir)

    print(f"\nDone: {result['images']} images, {result['videos']} videos downloaded", file=sys.stderr)
    if result["errors"]:
        print(f"Errors: {result['errors']}", file=sys.stderr)

    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()

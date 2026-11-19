"""Step 2: Generate scene images from script using Agnes image API."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from api_client import generate_image, extract_image_urls, download_url


def generate_scene_images(script_path: str, output_dir: str | None = None,
                          size: str = "1152x768", parallel: int = 1,
                          raw: bool = False) -> dict:
    with open(script_path, "r", encoding="utf-8") as f:
        script = json.load(f)

    if output_dir is None:
        output_dir = os.path.dirname(script_path) or "."

    img_dir = os.path.join(output_dir, "images")
    os.makedirs(img_dir, exist_ok=True)

    scenes = script.get("scenes", [])
    results = []

    for scene in scenes:
        scene_num = scene.get("scene", 0)
        visual_prompt = scene.get("visual_prompt", "")
        camera_motion = scene.get("camera_motion", "gentle camera movement")

        # Enhance prompt with camera motion hint for better image composition
        enhanced_prompt = (
            f"{visual_prompt}, {camera_motion}, "
            f"high quality, detailed, cinematic composition"
        )

        print(f"  Generating image for scene {scene_num}...", file=sys.stderr)
        print(f"    Prompt: {enhanced_prompt[:80]}...", file=sys.stderr)

        try:
            data = generate_image(enhanced_prompt, size=size)
            urls = extract_image_urls(data)

            if urls:
                img_url = urls[0]
                # Download image
                img_filename = f"scene_{scene_num:02d}.png"
                img_path = os.path.join(img_dir, img_filename)
                print(f"    Downloading from {img_url[:80]}...", file=sys.stderr)
                local_path = download_url(img_url, img_path)

                scene["image_url"] = img_url
                scene["image_path"] = local_path
                print(f"    Saved: {local_path}", file=sys.stderr)
            else:
                print(f"    Warning: No image URL returned", file=sys.stderr)

            results.append({
                "scene": scene_num,
                "success": bool(urls),
                "raw": data if raw else None,
            })
        except Exception as exc:
            print(f"    Error: {exc}", file=sys.stderr)
            results.append({"scene": scene_num, "success": False, "error": str(exc)})

        if parallel > 1 and scene_num < len(scenes):
            time.sleep(0.5)  # Small delay between requests

    # Update script file
    script["scenes"] = scenes
    with open(script_path, "w", encoding="utf-8") as f:
        json.dump(script, f, ensure_ascii=False, indent=2)

    return {
        "script_path": script_path,
        "image_dir": img_dir,
        "total": len(scenes),
        "success": sum(1 for r in results if r["success"]),
        "results": results if raw else None,
    }


def main():
    parser = argparse.ArgumentParser(description="Generate scene images from script.")
    parser.add_argument("--script", required=True, help="Path to script.json")
    parser.add_argument("--output-dir", default=None, help="Output directory (default: same as script)")
    parser.add_argument("--size", default="1152x768", help="Image size (WIDTHxHEIGHT)")
    parser.add_argument("--parallel", type=int, default=1, help="Parallel requests (default: 1)")
    parser.add_argument("--raw", action="store_true", help="Include raw API responses")
    args = parser.parse_args()

    print(f"Generating images from script: {args.script}", file=sys.stderr)

    result = generate_scene_images(args.script, args.output_dir, args.size, args.parallel, args.raw)

    print(f"\nDone: {result['success']}/{result['total']} images generated", file=sys.stderr)
    print(f"Images saved to: {result['image_dir']}", file=sys.stderr)

    print(json.dumps({
        "output_dir": result["image_dir"],
        "total": result["total"],
        "success": result["success"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()

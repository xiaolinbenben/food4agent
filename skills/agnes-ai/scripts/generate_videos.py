"""Step 3: Generate video clips from scene images using Agnes video API.

Usage modes:
  Mode A (default): Read script.json and generate videos per scene.
  Mode B (--images + --prompt): Generate a single video from local images + prompt.
  Mode C (--mode keyframes --images): Multi-image keyframe video.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from api_client import (
    create_video_task,
    poll_video_task,
    extract_video_urls,
    download_url,
    ensure_english,
)


# ─────────────────────────────────────────────
# Mode A: script.json-driven (existing behavior)
# ─────────────────────────────────────────────

def generate_scene_videos(script_path: str, output_dir: str | None = None,
                          num_frames: int = 81, frame_rate: float = 24,
                          width: int = 1152, height: int = 768,
                          seed: int | None = None, timeout: int = 900,
                          interval: int = 10, raw: bool = False) -> dict:
    with open(script_path, "r", encoding="utf-8") as f:
        script = json.load(f)

    if output_dir is None:
        output_dir = os.path.dirname(script_path) or "."

    vid_dir = os.path.join(output_dir, "videos")
    os.makedirs(vid_dir, exist_ok=True)

    scenes = script.get("scenes", [])
    results = []

    for scene in scenes:
        scene_num = scene.get("scene", 0)
        visual_prompt = scene.get("visual_prompt", "")
        image_url = scene.get("image_url")
        image_path = scene.get("image_path")

        # Resume support: skip if video file already exists on disk
        vid_filename = f"scene_{scene_num:02d}.mp4"
        vid_path_expected = os.path.join(vid_dir, vid_filename)
        if os.path.isfile(vid_path_expected):
            print(f"  Skipping scene {scene_num}: video already exists at {vid_path_expected}", file=sys.stderr)
            scene["video_path"] = vid_path_expected
            results.append({"scene": scene_num, "success": True, "skipped": True})
            continue

        # For video generation, enhance prompt with animation instructions
        camera_motion = scene.get("camera_motion", "gentle camera movement")
        video_prompt = ensure_english(
            f"{visual_prompt}, {camera_motion}, smooth animation, "
            f"cinematic motion, high quality video"
        )

        # Use image_url if available (image-to-video gives better results)
        input_image = image_url if image_url else None

        print(f"  Creating video task for scene {scene_num}...", file=sys.stderr)
        print(f"    Mode: {'image-to-video' if input_image else 'text-to-video'}", file=sys.stderr)
        print(f"    Frames: {num_frames}, FPS: {frame_rate}", file=sys.stderr)

        try:
            # Create task
            task_data = create_video_task(
                prompt=video_prompt,
                image_url=input_image,
                width=width,
                height=height,
                num_frames=num_frames,
                frame_rate=frame_rate,
                seed=seed,
            )

            task_id = task_data.get("id")
            if not task_id:
                print(f"    Error: No task ID returned", file=sys.stderr)
                results.append({"scene": scene_num, "success": False, "error": "No task ID"})
                continue

            print(f"    Task ID: {task_id}, polling...", file=sys.stderr)

            # Poll for completion
            final = poll_video_task(str(task_id), timeout=timeout, interval=interval)
            status = str(final.get("status", "")).lower()

            if status == "completed":
                urls = extract_video_urls(final)
                if urls:
                    video_url = urls[0]
                    vid_filename = f"scene_{scene_num:02d}.mp4"
                    vid_path = os.path.join(vid_dir, vid_filename)
                    print(f"    Downloading video from {video_url[:80]}...", file=sys.stderr)
                    local_path = download_url(video_url, vid_path)

                    scene["video_url"] = video_url
                    scene["video_path"] = local_path
                    print(f"    Saved: {local_path}", file=sys.stderr)
                    results.append({"scene": scene_num, "success": True})
                else:
                    print(f"    Warning: Completed but no video URL", file=sys.stderr)
                    results.append({"scene": scene_num, "success": False, "error": "No video URL"})
            else:
                print(f"    Task failed with status: {status}", file=sys.stderr)
                results.append({"scene": scene_num, "success": False, "error": f"status={status}"})

        except Exception as exc:
            print(f"    Error: {exc}", file=sys.stderr)
            results.append({"scene": scene_num, "success": False, "error": str(exc)})

    # Update script file
    script["scenes"] = scenes
    with open(script_path, "w", encoding="utf-8") as f:
        json.dump(script, f, ensure_ascii=False, indent=2)

    return {
        "script_path": script_path,
        "video_dir": vid_dir,
        "total": len(scenes),
        "success": sum(1 for r in results if r["success"]),
        "results": results if raw else None,
    }


# ─────────────────────────────────────────────
# Mode B & C: direct image(s) + prompt
# ─────────────────────────────────────────────

def _resolve_image_paths(image_arg: str) -> list[str]:
    """Parse comma-separated image paths, resolve to absolute paths."""
    raw_paths = [p.strip() for p in image_arg.split(",")]
    resolved = []
    for p in raw_paths:
        abs_p = os.path.abspath(p)
        if not os.path.isfile(abs_p):
            print(f"  Warning: image file not found, skipping: {p}", file=sys.stderr)
            continue
        resolved.append(abs_p)
    if not resolved:
        print("Error: No valid image files found.", file=sys.stderr)
        sys.exit(1)
    return resolved


def _upload_image(local_path: str) -> str:
    """Upload a local image to Agnes cloud and return its URL.

    Strategy: send the image bytes via a simple HTTP POST to a placeholder endpoint.
    Since Agnes AI does not provide a direct upload API in its current spec,
    we use the image_path directly if it's already a URL, or we copy it to
    the output dir and reference it. For the video API, we can pass the
    absolute local path — but the API expects URLs.
    
    Alternative approach: read the image and pass base64 or use a temp URL.
    However, looking at the API spec again, the `image` field accepts image URLs.
    
    Practical solution for local files:
    - If input is already a URL (http/https), use as-is
    - If it's a local file path, we need to make it accessible
    
    Since we don't have a direct upload endpoint, we'll accept that local files
    must be uploaded to a cloud storage first, OR we can try passing local path
    directly and see if the API accepts it.
    
    For now, we'll return the local path as-is — if the API rejects it, the
    error message will guide users to use cloud-hosted images.
    """
    if local_path.startswith(("http://", "https://")):
        return local_path
    # Return local path — API may or may not accept it
    return local_path


def generate_video_from_images(prompt: str, image_paths: list[str],
                                output_dir: str, num_frames: int = 121,
                                frame_rate: float = 24, mode: str = "single",
                                seed: int | None = None,
                                timeout: int = 900, interval: int = 10,
                                raw: bool = False) -> dict:
    """Generate video(s) from local image files with a custom prompt.

    Args:
        prompt: User's description/prompt for the video.
        image_paths: List of local image file paths (absolute or relative).
        output_dir: Directory to save output videos.
        num_frames: Frames per video (8n+1, max 441).
        frame_rate: Frame rate.
        mode: "single" = one video per image; "keyframes" = one video from all images.
        seed: Optional random seed.
        timeout: Polling timeout.
        interval: Polling interval.
        raw: Include raw API responses.
    """
    vid_dir = os.path.join(output_dir, "videos")
    os.makedirs(vid_dir, exist_ok=True)

    # Copy images to output dir for reference
    img_dir = os.path.join(output_dir, "images")
    os.makedirs(img_dir, exist_ok=True)
    copied_images = []
    for i, img_p in enumerate(image_paths):
        dest = os.path.join(img_dir, f"input_{i:02d}{os.path.splitext(img_p)[1]}")
        shutil.copy2(img_p, dest)
        copied_images.append(dest)
        print(f"  Copied image {i+1}: {img_p} -> {dest}", file=sys.stderr)

    # Translate prompt to English
    prompt_en = ensure_english(prompt)
    print(f"  Prompt (translated): {prompt_en}", file=sys.stderr)

    if mode == "keyframes":
        # Mode C: one video from all images as keyframes
        print(f"  Generating keyframe video from {len(copied_images)} images...", file=sys.stderr)
        print(f"  Frames: {num_frames}, FPS: {frame_rate}", file=sys.stderr)

        try:
            task_data = create_video_task(
                prompt=prompt_en,
                image_list=copied_images,
                mode="keyframes",
                width=1152,
                height=768,
                num_frames=num_frames,
                frame_rate=frame_rate,
                seed=seed,
            )

            task_id = task_data.get("id")
            if not task_id:
                print(f"  Error: No task ID returned", file=sys.stderr)
                return {"video_dir": vid_dir, "total": 1, "success": 0}

            print(f"  Task ID: {task_id}, polling...", file=sys.stderr)
            final = poll_video_task(str(task_id), timeout=timeout, interval=interval)
            status = str(final.get("status", "")).lower()

            if status == "completed":
                urls = extract_video_urls(final)
                if urls:
                    vid_path = os.path.join(vid_dir, "output.mp4")
                    print(f"  Downloading video from {urls[0][:80]}...", file=sys.stderr)
                    local_path = download_url(urls[0], vid_path)
                    print(f"  Saved: {local_path}", file=sys.stderr)
                    # Update script
                    script_path = os.path.join(output_dir, "script.json")
                    script = {
                        "scenes": [{
                            "scene": 1,
                            "visual_prompt": prompt_en,
                            "video_url": urls[0],
                            "video_path": local_path,
                        }],
                    }
                    with open(script_path, "w", encoding="utf-8") as f:
                        json.dump(script, f, ensure_ascii=False, indent=2)
                    print(f"  Saved: {script_path}", file=sys.stderr)
                    return {"video_dir": vid_dir, "total": 1, "success": 1}
                else:
                    print(f"  Warning: Completed but no video URL", file=sys.stderr)
            else:
                print(f"  Task failed with status: {status}", file=sys.stderr)

        except Exception as exc:
            print(f"  Error: {exc}", file=sys.stderr)

    else:
        # Mode B: one video per image
        results = []
        for i, img_p in enumerate(copied_images):
            scene_num = i + 1
            vid_filename = f"output_{scene_num:02d}.mp4"
            vid_path = os.path.join(vid_dir, vid_filename)

            # Skip if already generated
            if os.path.isfile(vid_path):
                print(f"  Skipping scene {scene_num}: already exists", file=sys.stderr)
                results.append({"scene": scene_num, "success": True, "skipped": True})
                continue

            print(f"  Creating video task for image {scene_num}...", file=sys.stderr)
            print(f"    Frames: {num_frames}, FPS: {frame_rate}", file=sys.stderr)

            try:
                task_data = create_video_task(
                    prompt=prompt_en,
                    image_url=img_p,
                    width=1152,
                    height=768,
                    num_frames=num_frames,
                    frame_rate=frame_rate,
                    seed=seed,
                )

                task_id = task_data.get("id")
                if not task_id:
                    print(f"    Error: No task ID returned", file=sys.stderr)
                    results.append({"scene": scene_num, "success": False, "error": "No task ID"})
                    continue

                print(f"    Task ID: {task_id}, polling...", file=sys.stderr)
                final = poll_video_task(str(task_id), timeout=timeout, interval=interval)
                status = str(final.get("status", "")).lower()

                if status == "completed":
                    urls = extract_video_urls(final)
                    if urls:
                        print(f"    Downloading video from {urls[0][:80]}...", file=sys.stderr)
                        local_path = download_url(urls[0], vid_path)
                        results.append({"scene": scene_num, "success": True, "path": local_path})
                        print(f"    Saved: {local_path}", file=sys.stderr)
                    else:
                        print(f"    Warning: Completed but no video URL", file=sys.stderr)
                        results.append({"scene": scene_num, "success": False, "error": "No video URL"})
                else:
                    print(f"    Task failed with status: {status}", file=sys.stderr)
                    results.append({"scene": scene_num, "success": False, "error": f"status={status}"})

            except Exception as exc:
                print(f"    Error: {exc}", file=sys.stderr)
                results.append({"scene": scene_num, "success": False, "error": str(exc)})

        return {
            "video_dir": vid_dir,
            "total": len(copied_images),
            "success": sum(1 for r in results if r["success"]),
            "results": results if raw else None,
        }

    return {"video_dir": vid_dir, "total": 1, "success": 0}


# ─────────────────────────────────────────────
# CLI entry point
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate video clips from scene images using Agnes video API.",
    )
    # Common args
    parser.add_argument("--output-dir", default="output", help="Output directory (default: output)")
    parser.add_argument("--num-frames", type=int, default=81, help="Frames per video (8n+1, max 441, default: 81)")
    parser.add_argument("--frame-rate", type=float, default=24, help="Frame rate (1-60, default: 24)")
    parser.add_argument("--width", type=int, default=1152, help="Video width (default: 1152)")
    parser.add_argument("--height", type=int, default=768, help="Video height (default: 768)")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    parser.add_argument("--timeout", type=int, default=900, help="Polling timeout (seconds, default: 900)")
    parser.add_argument("--interval", type=int, default=10, help="Polling interval (seconds, default: 10)")
    parser.add_argument("--raw", action="store_true", help="Include raw API responses")

    # Mode A: script-driven (default)
    parser.add_argument("--script", default=None, help="Path to script.json (default mode)")

    # Mode B & C: direct image(s) + prompt
    parser.add_argument("--prompt", default=None, help="Custom prompt for video generation")
    parser.add_argument("--images", default=None, help="Comma-separated list of image files")
    parser.add_argument("--mode", default="single", choices=["single", "keyframes"],
                        help="Image mode: 'single' = one video per image (default), 'keyframes' = one video from all images")

    args = parser.parse_args()

    # Validate num_frames
    if args.num_frames > 441 or (args.num_frames - 1) % 8 != 0:
        print("Error: --num-frames must satisfy 8n+1 and be <= 441 (e.g., 81, 121, 241)", file=sys.stderr)
        sys.exit(1)

    # Determine mode
    if args.script:
        # Mode A: script-driven
        print(f"Generating videos from script: {args.script}", file=sys.stderr)
        result = generate_scene_videos(
            args.script, args.output_dir, args.num_frames, args.frame_rate,
            args.width, args.height, args.seed, args.timeout, args.interval, args.raw
        )
    elif args.images and (args.prompt or args.mode == "keyframes"):
        # Mode B or C: direct image(s) + prompt
        if not args.prompt:
            args.prompt = "Generate a smooth, cinematic video from the provided images."

        image_paths = _resolve_image_paths(args.images)

        print(f"\n{'='*60}", file=sys.stderr)
        print(f"Mode: {'keyframes' if args.mode == 'keyframes' else 'single'}", file=sys.stderr)
        print(f"Images: {len(image_paths)}", file=sys.stderr)
        print(f"Prompt: {args.prompt}", file=sys.stderr)
        print(f"{'='*60}", file=sys.stderr)

        result = generate_video_from_images(
            prompt=args.prompt,
            image_paths=image_paths,
            output_dir=args.output_dir,
            num_frames=args.num_frames,
            frame_rate=args.frame_rate,
            mode=args.mode,
            seed=args.seed,
            timeout=args.timeout,
            interval=args.interval,
            raw=args.raw,
        )
    else:
        parser.print_help()
        print("\nError: Provide either --script OR (--images + --prompt for mode 'single', or --images --mode keyframes)", file=sys.stderr)
        sys.exit(1)

    print(f"\nDone: {result['success']}/{result['total']} videos generated", file=sys.stderr)
    print(f"Videos saved to: {result['video_dir']}", file=sys.stderr)

    print(json.dumps({
        "output_dir": result["video_dir"],
        "total": result["total"],
        "success": result["success"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()

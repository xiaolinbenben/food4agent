#!/usr/bin/env python3
"""
拉片抽帧脚本

从一组对标视频里按"前 3 秒每秒 1 帧 + 中段每 3 秒 1 帧 + 最后 5 秒每秒 1 帧"
的策略抽出关键帧，缩到 1/2 尺寸保存为 JPG，便于 Claude 用 Read 看图分析。

用法：
    python extract_frames.py <视频源目录> [-o <输出目录>] [-p <挑选模式>]

    -p auto       : 自动取目录里所有 mp4/mov（默认）
    -p '0,3,7,12' : 用文件按文件名字典序排列后，挑指定序号（0-based）
    -p '关键词1,关键词2' : 用文件名包含的关键词匹配，每个关键词最多挑 1 个

示例：
    # 抽全部
    python extract_frames.py ~/Downloads/对标账号/

    # 只抽 5 条精拉对比的
    python extract_frames.py ~/Downloads/对标账号/ -p '面试真题,560和590,南方科技大学,亚洲最长,6条降分'

输出：
    每个视频抽到的帧放在 <输出目录>/<视频短名>/ 下，文件名 NN_tSSS.S.jpg
    + 一份 meta.json 索引

依赖：opencv-python（pip install opencv-python）
"""

import argparse
import json
import os
import sys
import shutil
from pathlib import Path

try:
    import cv2
except ImportError:
    print("缺少 opencv-python，请先安装：pip install opencv-python", file=sys.stderr)
    sys.exit(1)


def extract_one(src_path: Path, out_dir: Path, scale: float = 0.5, quality: int = 75) -> dict:
    """对单个视频抽帧，返回 metadata dict"""
    cap = cv2.VideoCapture(str(src_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total <= 0:
        cap.release()
        return {"error": "无法读取帧数", "src": src_path.name}
    duration = total / fps

    # 抽帧时间点
    timestamps = []
    t = 0.0
    while t < duration:
        if t <= 3.0 or t >= duration - 5:
            timestamps.append(round(t, 1))
            t += 1.0
        else:
            timestamps.append(round(t, 1))
            t += 3.0

    out_dir.mkdir(parents=True, exist_ok=True)
    saved = 0
    for i, ts in enumerate(timestamps):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(ts * fps))
        ret, frame = cap.read()
        if not ret:
            continue
        if scale != 1.0:
            h, w = frame.shape[:2]
            frame = cv2.resize(frame, (int(w * scale), int(h * scale)))
        out_path = out_dir / f"{i:02d}_t{ts:05.1f}.jpg"
        cv2.imwrite(str(out_path), frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
        saved += 1
    cap.release()

    return {
        "src": src_path.name,
        "duration_s": round(duration, 1),
        "fps": round(fps, 1),
        "frames_extracted": saved,
        "out_dir": str(out_dir.relative_to(out_dir.parent.parent)) if out_dir.parent.parent else str(out_dir),
    }


def pick_videos(src_dir: Path, pattern: str) -> list:
    """按选择模式挑视频"""
    all_videos = sorted([p for p in src_dir.iterdir()
                         if p.is_file() and p.suffix.lower() in {'.mp4', '.mov', '.m4v'}])
    if pattern == 'auto':
        return all_videos
    if ',' not in pattern and pattern.isdigit():
        # 单个序号
        idx = int(pattern)
        return [all_videos[idx]] if 0 <= idx < len(all_videos) else []
    # 多关键词或多序号
    parts = [p.strip() for p in pattern.split(',') if p.strip()]
    if all(p.isdigit() for p in parts):
        # 全是序号
        return [all_videos[int(p)] for p in parts if 0 <= int(p) < len(all_videos)]
    # 关键词匹配（每个关键词最多取 1 个）
    picked = []
    used = set()
    for kw in parts:
        for v in all_videos:
            if kw in v.name and v.name not in used:
                picked.append(v)
                used.add(v.name)
                break
    return picked


def safe_short_name(filename: str, max_len: int = 40) -> str:
    """生成一个 OS 友好的短目录名"""
    base = Path(filename).stem
    # 去掉空格、特殊字符替换
    base = base.replace(' ', '_').replace('/', '_')
    if len(base) > max_len:
        base = base[:max_len]
    return base or 'video'


def main():
    ap = argparse.ArgumentParser(
        description='对标视频拉片抽帧',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument('src_dir', help='视频源目录')
    ap.add_argument('-o', '--out-dir', default=None,
                    help='输出目录（默认在源目录同级建 duibiao_frames/）')
    ap.add_argument('-p', '--pick', default='auto',
                    help='挑选模式 (auto / 序号列表 / 关键词列表)，默认 auto')
    ap.add_argument('--scale', type=float, default=0.5, help='缩放比例（默认 0.5）')
    ap.add_argument('--quality', type=int, default=75, help='JPG 质量（默认 75）')
    args = ap.parse_args()

    src_dir = Path(args.src_dir).expanduser().resolve()
    if not src_dir.is_dir():
        print(f"源目录不存在: {src_dir}", file=sys.stderr)
        sys.exit(1)

    if args.out_dir:
        out_root = Path(args.out_dir).expanduser().resolve()
    else:
        out_root = src_dir.parent / 'duibiao_frames'
    out_root.mkdir(parents=True, exist_ok=True)

    videos = pick_videos(src_dir, args.pick)
    if not videos:
        print(f"没挑到视频。源目录 {src_dir} 里 mp4/mov 文件数：{len(list(src_dir.glob('*.mp4'))) + len(list(src_dir.glob('*.mov')))}", file=sys.stderr)
        sys.exit(1)

    print(f"挑到 {len(videos)} 条视频，输出到：{out_root}")
    meta = {}
    for i, v in enumerate(videos, 1):
        tag = f"{i:02d}_{safe_short_name(v.name)}"
        out_dir = out_root / tag
        print(f"  [{i}/{len(videos)}] {v.name[:60]}...", end=' ', flush=True)
        info = extract_one(v, out_dir, scale=args.scale, quality=args.quality)
        if 'error' in info:
            print(f"FAIL: {info['error']}")
        else:
            print(f"{info['duration_s']}s → {info['frames_extracted']} frames")
            meta[tag] = info

    with open(out_root / 'meta.json', 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f"\n完成。meta.json 写入 {out_root / 'meta.json'}")


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Analyze subtitles and generate chapters.
Parse VTT subtitle files and prepare data for analysis.
"""

import sys
import re
import json
import html
from pathlib import Path

from typing import List, Dict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from utils import time_to_seconds, seconds_to_time, get_video_duration_display


def parse_vtt(vtt_path: str) -> List[Dict]:
    """
    Parse VTT subtitle file.

    Args:
        vtt_path: Path to VTT file

    Returns:
        List[Dict]: List of subtitles, each containing {start, end, text}

    Example:
        [
            {'start': 0.0, 'end': 3.5, 'text': 'Hello world'},
            {'start': 3.5, 'end': 7.2, 'text': 'This is a test'},
            ...
        ]
    """
    vtt_path = Path(vtt_path)

    if not vtt_path.exists():
        raise FileNotFoundError(f"Subtitle file not found: {vtt_path}")

    print(f"INFO: Parsing subtitle file: {vtt_path.name}")

    subtitles = []

    with open(vtt_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Remove WEBVTT header and style info
    content = re.sub(r"^WEBVTT.*?\n\n", "", content, flags=re.DOTALL)
    content = re.sub(r"STYLE.*?-->", "", content, flags=re.DOTALL)

    # Split subtitle blocks
    blocks = content.strip().split("\n\n")

    for block in blocks:
        lines = block.strip().split("\n")

        if len(lines) < 2:
            continue

        # Find timestamp line
        timestamp_line = None
        text_lines = []

        for line in lines:
            # Match timestamp format: 00:00:00.000 --> 00:00:03.000
            if "-->" in line:
                timestamp_line = line
            elif line and not line.isdigit():  # Skip sequence numbers
                text_lines.append(line)

        if not timestamp_line or not text_lines:
            continue

        # Parse timestamps
        try:
            # Remove potential position info (e.g. align:start position:0%)
            timestamp_line = re.sub(r"align:.*|position:.*", "", timestamp_line).strip()

            times = timestamp_line.split("-->")
            start_str = times[0].strip()
            end_str = times[1].strip()

            start = time_to_seconds(start_str)
            end = time_to_seconds(end_str)

            # Join text lines
            text = " ".join(text_lines)

            # 1. Unescape HTML entities (e.g., &gt;&gt; -> >>)
            text = html.unescape(text)

            # 2. Clean HTML tags
            text = re.sub(r"<[^>]+>", "", text)

            # 3. Remove leading speaker markers like >> or >>>
            text = re.sub(r"^\s*>>+\s*", "", text)

            # 4. Remove non-speech cues in brackets like [Music] or [Laughter]
            text = re.sub(r"\[[^\]]*\]", "", text)

            # 5. Normalize whitespace
            text = " ".join(text.split())

            # Clean special characters
            text = text.strip()

            if text:
                subtitles.append({"start": start, "end": end, "text": text})

        except Exception as e:
            # Skip unparseable blocks
            continue

    print(f"INFO: Found {len(subtitles)} subtitles")

    if subtitles:
        total_duration = subtitles[-1]["end"]
        print(f"INFO: Total duration: {get_video_duration_display(total_duration)}")

    return subtitles


def prepare_analysis_data(
    subtitles: List[Dict], target_chapter_duration: int = 180
) -> Dict:
    """
    Prepare data for analysis.

    Args:
        subtitles: List of subtitles
        target_chapter_duration: Target chapter duration (seconds), default 180s (3m)

    Returns:
        Dict: {
            'subtitle_text': Complete subtitle text with timestamps,
            'total_duration': Total duration,
            'subtitle_count': Number of subtitles,
            'target_chapter_duration': Target chapter duration,
            'estimated_chapters': Estimated number of chapters
        }
    """
    if not subtitles:
        raise ValueError("No subtitles to analyze")

    print(f"\nINFO: Preparing analysis data...")

    # Join subtitles into complete text with timestamps
    full_text_lines = []

    for sub in subtitles:
        time_str = seconds_to_time(sub["start"], include_hours=True, use_comma=False)
        full_text_lines.append(f"[{time_str}] {sub['text']}")

    full_text = "\n".join(full_text_lines)

    total_duration = subtitles[-1]["end"]
    estimated_chapters = max(1, int(total_duration / target_chapter_duration))

    print(f"INFO: Total duration: {get_video_duration_display(total_duration)}")
    print(f"INFO: Subtitle count: {len(subtitles)}")
    print(
        f"INFO: Target chapter duration: {target_chapter_duration}s ({target_chapter_duration // 60}m)"
    )
    print(f"INFO: Estimated chapters: {estimated_chapters}")

    return {
        "subtitle_text": full_text,
        "total_duration": total_duration,
        "subtitle_count": len(subtitles),
        "target_chapter_duration": target_chapter_duration,
        "estimated_chapters": estimated_chapters,
        "subtitles_raw": subtitles,  # Keep raw data for later use
    }


def save_analysis_data(data: Dict, output_path: str):
    """
    Save analysis data to JSON file.

    Args:
        data: Analysis data
        output_path: Output file path
    """
    output_path = Path(output_path)

    # Create output directory
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save as JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"DONE: Analysis data saved: {output_path}")


def main():
    """CLI entry point"""
    if len(sys.argv) < 2:
        print(
            "Usage: python analyze_subtitles.py <vtt_file> [target_duration] [output_json]"
        )
        print("\nArguments:")
        print("  vtt_file         - Path to VTT subtitle file")
        print("  target_duration  - Target chapter duration (seconds), default 180")
        print("  output_json      - Path to output JSON file (optional)")
        print("\nExample:")
        print("  python analyze_subtitles.py video.en.vtt")
        print("  python analyze_subtitles.py video.en.vtt 240")
        print("  python analyze_subtitles.py video.en.vtt 240 analysis.json")
        sys.exit(1)

    vtt_file = sys.argv[1]
    target_duration = int(sys.argv[2]) if len(sys.argv) > 2 else 180
    output_json = sys.argv[3] if len(sys.argv) > 3 else None

    try:
        # Parse subtitles
        subtitles = parse_vtt(vtt_file)

        if not subtitles:
            print("ERROR: No valid subtitles found")
            sys.exit(1)

        # Prepare analysis data
        analysis_data = prepare_analysis_data(subtitles, target_duration)

        # Output subtitle text (for Claude analysis)
        print("\n" + "=" * 60)
        print("INFO: Subtitle text preview (first 50 lines):")
        print("=" * 60)
        lines = analysis_data["subtitle_text"].split("\n")
        preview_lines = lines[:50]
        print("\n".join(preview_lines))
        if len(lines) > 50:
            print(f"\n... (remaining {len(lines) - 50} lines)")

        # Save to file (if specified)
        if output_json:
            save_analysis_data(analysis_data, output_json)

        # Output summary info
        print("\n" + "=" * 60)
        print("INFO: Analysis summary:")
        print("=" * 60)
        print(
            json.dumps(
                {
                    "total_duration": analysis_data["total_duration"],
                    "total_duration_display": get_video_duration_display(
                        analysis_data["total_duration"]
                    ),
                    "subtitle_count": analysis_data["subtitle_count"],
                    "target_chapter_duration": analysis_data["target_chapter_duration"],
                    "estimated_chapters": analysis_data["estimated_chapters"],
                },
                indent=2,
                ensure_ascii=False,
            )
        )

        print(
            "\nINFO: You can now analyze the subtitle text above using Claude AI to generate detailed chapters."
        )

    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

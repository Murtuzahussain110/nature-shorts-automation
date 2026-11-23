#!/usr/bin/env python3
"""Pick the most visually active adjacent scenes and export captioned cartoon highlights.

The main renderer already produces scene clips, per-scene Urdu voice files, and a
final subtitled MP4. This script scores each scene using frame-to-frame motion
and dialogue loudness, then cuts the strongest adjacent scene pairs from the
finished MP4 so the original voice and burned-in subtitles stay synchronized.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"
SCENES = OUT
AUDIO = OUT / "audio"
FINAL = OUT / "tom_jerry_short.mp4"
HIGHLIGHTS = OUT / "highlights"
MAX_HIGHLIGHTS = 3


def run(args: list[str]) -> str:
    result = subprocess.run(args, check=True, capture_output=True, text=True)
    return result.stdout + result.stderr


def duration(path: Path) -> float:
    value = run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path)
    ]).strip()
    return float(value)


def motion_score(path: Path) -> float:
    # Frame blending in difference mode measures actual frame-to-frame change.
    output = run([
        "ffmpeg", "-hide_banner", "-i", str(path),
        "-vf", "tblend=all_mode=difference,signalstats,metadata=print:file=-",
        "-an", "-f", "null", "-"
    ])
    values = [float(v) for v in re.findall(r"lavfi\.signalstats\.YAVG=([0-9.]+)", output)]
    return sum(values) / len(values) if values else 0.0


def voice_score(path: Path) -> float:
    if not path.exists():
        return 0.0
    output = run(["ffmpeg", "-hide_banner", "-i", str(path), "-af", "volumedetect", "-f", "null", "-"])
    match = re.search(r"mean_volume:\s*(-?[0-9.]+) dB", output)
    return max(0.0, min(1.0, (float(match.group(1)) + 55.0) / 45.0)) if match else 0.0


def main() -> None:
    if not FINAL.exists():
        raise SystemExit(f"Finished episode not found: {FINAL}")
    scene_files = sorted(
        SCENES.glob("clip_*.mp4"),
        key=lambda p: int(re.search(r"clip_(\d+)", p.stem).group(1))
    )
    if len(scene_files) < 2:
        raise SystemExit("At least two rendered scene clips are required.")

    durations = [duration(p) for p in scene_files]
    scores = []
    for index, scene in enumerate(scene_files, start=1):
        motion = motion_score(scene)
        voice = voice_score(AUDIO / f"voice_{index:02}.mp3")
        scores.append((motion, voice, 0.75 * motion + 0.25 * voice))
        print(f"Scene {index}: motion={motion:.3f}, voice={voice:.3f}, score={scores[-1][2]:.3f}")

    # Rank two-scene story beats. Adjacent scenes retain setup + payoff.
    candidates = []
    offset = 0.0
    starts = []
    for length in durations:
        starts.append(offset)
        offset += length
    for i in range(len(scene_files) - 1):
        pair_score = (scores[i][2] + scores[i + 1][2]) / 2
        start = starts[i]
        end = starts[i + 1] + durations[i + 1]
        if end - start >= 4.0:
            candidates.append((pair_score, i, start, end))

    chosen = []
    for candidate in sorted(candidates, reverse=True):
        _, index, _, _ = candidate
        if all(abs(index - other[1]) > 1 for other in chosen):
            chosen.append(candidate)
        if len(chosen) == MAX_HIGHLIGHTS:
            break
    if not chosen:
        raise SystemExit("No usable adjacent scene pairs were found.")

    HIGHLIGHTS.mkdir(parents=True, exist_ok=True)
    for old in HIGHLIGHTS.glob("highlight_*.mp4"):
        old.unlink()
    chosen.sort(key=lambda item: item[2])
    for number, (score, index, start, end) in enumerate(chosen, start=1):
        target = HIGHLIGHTS / f"highlight_{number:02}.mp4"
        run([
            "ffmpeg", "-y", "-hide_banner", "-ss", f"{start:.3f}",
            "-i", str(FINAL), "-t", f"{end - start:.3f}",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
            "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
            str(target)
        ])
        print(f"Exported {target.name}: scenes {index + 1}-{index + 2}, "
              f"score={score:.3f}, duration={end - start:.1f}s")
    print(f"Created {len(chosen)} highlight clip(s) in {HIGHLIGHTS}")


if __name__ == "__main__":
    main()

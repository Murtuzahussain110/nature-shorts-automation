"""Export up to three high-energy scene-pair highlights from the daily story.

Uses the six rendered scene clips and their matching voice tracks, then cuts
those moments from the final subtitled MP4 so captions and narration stay in sync.
"""
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"
AUDIO = OUT / "audio"
FINAL = OUT / "daily_story.mp4"
HIGHLIGHTS = OUT / "highlights"


def run(args, capture=False):
    return subprocess.run(
        args, check=True, text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None
    )


def duration(path):
    result = run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path)
    ], capture=True)
    return float(result.stdout.strip())


def motion_score(path):
    result = run([
        "ffmpeg", "-hide_banner", "-i", str(path),
        "-vf", "tblend=all_mode=difference,signalstats,metadata=print",
        "-an", "-f", "null", "-"
    ], capture=True)
    values = [
        float(value) for value in re.findall(
            r"lavfi\.signalstats\.YAVG=([0-9.]+)", result.stderr
        )
    ]
    return sum(values) / len(values) if values else 0.0


def audio_score(path):
    if not path.exists():
        return -60.0
    result = run([
        "ffmpeg", "-hide_banner", "-i", str(path),
        "-af", "volumedetect", "-f", "null", "-"
    ], capture=True)
    match = re.search(r"mean_volume:\s*(-?[0-9.]+) dB", result.stderr)
    return float(match.group(1)) if match else -60.0


def main():
    if not FINAL.exists():
        raise RuntimeError("output/daily_story.mp4 is missing; cannot cut highlights.")
    clips = sorted(
        OUT.glob("clip_*.mp4"),
        key=lambda path: int(re.search(r"clip_(\d+)", path.stem).group(1))
    )
    if len(clips) < 2:
        raise RuntimeError(f"Expected at least two scene clips; found {len(clips)}.")

    scenes = []
    cursor = 0.0
    for clip in clips:
        number = int(re.search(r"clip_(\d+)", clip.stem).group(1))
        length = duration(clip)
        voice = AUDIO / f"voice_{number}.mp3"
        motion = motion_score(clip)
        loudness = audio_score(voice)
        scenes.append({
            "number": number, "start": cursor, "duration": length,
            "motion": motion, "loudness": loudness
        })
        cursor += length

    pairs = []
    for index in range(len(scenes) - 1):
        left, right = scenes[index], scenes[index + 1]
        motion = (left["motion"] + right["motion"]) / 2
        loudness = (left["loudness"] + right["loudness"]) / 2
        # Normalize visual activity and dialogue loudness into a stable rank.
        score = motion * 0.7 + max(0.0, loudness + 45.0) * 0.3
        pairs.append({
            "first": index, "start": left["start"],
            "length": left["duration"] + right["duration"],
            "score": score
        })

    selected = []
    used = set()
    for pair in sorted(pairs, key=lambda item: item["score"], reverse=True):
        first = pair["first"]
        if first in used or first + 1 in used:
            continue
        selected.append(pair)
        used.update((first, first + 1))
        if len(selected) == 3:
            break

    HIGHLIGHTS.mkdir(parents=True, exist_ok=True)
    for old in HIGHLIGHTS.glob("highlight_*.mp4"):
        old.unlink()
    for rank, item in enumerate(sorted(selected, key=lambda value: value["start"]), 1):
        target = HIGHLIGHTS / f"highlight_{rank:02}.mp4"
        run([
            "ffmpeg", "-y", "-ss", f"{item['start']:.3f}", "-i", str(FINAL),
            "-t", f"{item['length']:.3f}", "-c:v", "libx264", "-preset", "veryfast",
            "-crf", "22", "-c:a", "aac", "-movflags", "+faststart", str(target)
        ])
        if not target.exists() or target.stat().st_size < 10000:
            raise RuntimeError(f"Highlight export failed: {target.name}")
        print(
            f"EXPORTED {target}: {item['length']:.1f}s "
            f"(moment score {item['score']:.2f})",
            flush=True
        )
    print(f"Highlight export complete: {len(selected)} clip(s).", flush=True)


if __name__ == "__main__":
    main()

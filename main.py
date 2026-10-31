import os
import json
import random
import subprocess
import wave
import math
import struct
import asyncio
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import edge_tts
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request

OUT = Path("output")
OUT.mkdir(exist_ok=True)
SOURCE_VIDEO = Path("nature.mp4")
WIDTH, HEIGHT, DURATION = 1080, 1920, 30
CHANNEL_VOICE = "en-US-AriaNeural"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

QUOTES = [
    [
        "You do not need to see the whole path.",
        "Take one brave step today.",
        "Small progress is still progress.",
        "Keep going. Your future is being built."
    ],
    [
        "Let the mountains remind you to rise.",
        "Let the quiet teach you to breathe.",
        "Your journey is not a race.",
        "Move forward, one beautiful step at a time."
    ],
    [
        "Some days, courage is simply beginning again.",
        "Rest when you need to.",
        "Never mistake a slow season for a lost future.",
        "Your next chapter is still yours to write."
    ],
    [
        "The world is wide, and your story is still unfolding.",
        "Choose curiosity over fear.",
        "Take the road that helps you grow.",
        "There is more ahead than behind."
    ],
    [
        "You have survived every difficult day so far.",
        "Give yourself credit for that.",
        "Breathe, reset, and try once more.",
        "You are allowed to grow at your own pace."
    ],
]

HASHTAGS = "#Motivation #Nature #TravelShorts #Mindset #YouTubeShorts"


def run(cmd):
    subprocess.run(cmd, check=True)


def choose_quote():
    return random.choice(QUOTES)


async def _make_voice(text, destination):
    communicate = edge_tts.Communicate(
        text, CHANNEL_VOICE, rate="-5%", pitch="-2Hz"
    )
    await communicate.save(str(destination))


def create_voice(lines):
    asyncio.run(_make_voice(" ".join(lines), OUT / "voice.mp3"))


def create_original_ambient_music(path, seconds=30, sample_rate=44100):
    # Original synthesized ambient bed; no third-party song recording.
    chords = [
        (220.00, 277.18, 329.63),
        (196.00, 246.94, 293.66),
        (174.61, 220.00, 261.63),
        (196.00, 246.94, 293.66),
    ]
    frames = int(seconds * sample_rate)
    audio = bytearray()
    for i in range(frames):
        t = i / sample_rate
        chord = chords[int(t // 7.5) % len(chords)]
        fade = min(1.0, t / 2.0, max(0.0, (seconds - t) / 2.0))
        sample = sum(math.sin(2 * math.pi * f * t) for f in chord) / 3.0
        value = int(32767 * 0.045 * fade * sample)
        audio.extend(struct.pack("<hh", value, value))
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio)


def make_srt(lines, path):
    starts = [0, 7, 14, 22]
    ends = [7, 14, 22, 30]

    def stamp(sec):
        ms = int(round(sec * 1000))
        h, rem = divmod(ms, 3600000)
        m, rem = divmod(rem, 60000)
        s, ms = divmod(rem, 1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"

    chunks = []
    for i, line in enumerate(lines):
        chunks.append(
            f"{i+1}\n{stamp(starts[i])} --> {stamp(ends[i])}\n{line}\n"
        )
    path.write_text("\n".join(chunks), encoding="utf-8")


def render_video(source, lines):
    create_voice(lines)
    create_original_ambient_music(OUT / "music.wav", DURATION)
    make_srt(lines, OUT / "captions.srt")

    srt_path = str((OUT / "captions.srt").resolve()).replace("\\", "/")
    srt_path = srt_path.replace(":", r"\:")
    vf = (
        "scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,fps=30,"
        f"subtitles='{srt_path}':force_style='FontName=DejaVu Sans,"
        "FontSize=18,Bold=1,PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00101010,BorderStyle=1,Outline=2,"
        "Shadow=1,Alignment=2,MarginV=220'"
    )

    run([
        "ffmpeg", "-y", "-stream_loop", "-1", "-i", str(source),
        "-i", str(OUT / "voice.mp3"),
        "-i", str(OUT / "music.wav"),
        "-filter_complex",
        "[1:a]volume=1.0,apad=pad_dur=30[voice];"
        "[2:a]volume=0.20[bg];"
        "[voice][bg]amix=inputs=2:duration=longest:dropout_transition=2[a]",
        "-map", "0:v:0", "-map", "[a]", "-vf", vf,
        "-t", str(DURATION), "-r", "30",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k", "-shortest",
        "-movflags", "+faststart", str(OUT / "short.mp4")
    ])


def youtube_client():
    client_json_text = os.getenv("YOUTUBE_CLIENT_JSON", "")
    refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN", "")
    if not client_json_text:
        raise RuntimeError(
            "Missing GitHub secret YOUTUBE_CLIENT_JSON. Add the complete "
            "OAuth Desktop client JSON as a repository Actions secret."
        )
    if not refresh_token:
        raise RuntimeError(
            "Missing GitHub secret YOUTUBE_REFRESH_TOKEN. YouTube OAuth "
            "authorization is still required before automatic upload."
        )

    client_data = json.loads(client_json_text)
    if "installed" not in client_data and "web" not in client_data:
        raise ValueError(
            "YOUTUBE_CLIENT_JSON must contain the complete downloaded "
            "Google OAuth client JSON."
        )
    client = client_data.get("installed") or client_data.get("web")
    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri=client.get(
            "token_uri", "https://oauth2.googleapis.com/token"
        ),
        client_id=client["client_id"],
        client_secret=client["client_secret"],
        scopes=SCOPES,
    )
    creds.refresh(Request())
    return build("youtube", "v3", credentials=creds)


def upload_video(lines):
    youtube = youtube_client()
    title = (lines[0].rstrip(".!") + " | Nature & Motivation #Shorts")[:100]
    description = (
        "A little reminder to keep moving forward. Original motivational "
        "narration and original synthesized ambient music over a nature visual.\n\n"
        "Background footage: user-provided Mixkit video. Check its license "
        "and attribution requirements before publishing.\n\n"
        + HASHTAGS
    )
    privacy = os.getenv("YOUTUBE_PRIVACY_STATUS", "private")
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": ["motivation", "nature", "travel", "mindset", "shorts"],
            "categoryId": "22",
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
        },
    }
    media = MediaFileUpload(
        str(OUT / "short.mp4"), mimetype="video/mp4", resumable=True
    )
    request = youtube.videos().insert(
        part="snippet,status", body=body, media_body=media
    )
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Upload progress: {int(status.progress() * 100)}%")
    print("Upload complete. Video ID:", response.get("id"))
    print("Privacy status:", privacy)


def main():
    if not SOURCE_VIDEO.exists():
        raise FileNotFoundError(
            "nature.mp4 was not found in the repository root. "
            "Upload the video beside main.py and name it exactly nature.mp4."
        )
    lines = choose_quote()
    print("Using local background video:", SOURCE_VIDEO)
    print("Original narration:", " ".join(lines))
    render_video(SOURCE_VIDEO, lines)
    print("Video rendered:", OUT / "short.mp4")
    upload_video(lines)


if __name__ == "__main__":
    main()
    

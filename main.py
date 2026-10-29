import os, json, random, subprocess, wave, math, struct, textwrap, re, requests
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import edge_tts
import asyncio
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request

OUT = Path("output")
OUT.mkdir(exist_ok=True)
WIDTH, HEIGHT, DURATION = 1080, 1920, 30
PEXELS_KEY = os.environ["PEXELS_API_KEY"]
CLIENT_JSON = os.environ["YOUTUBE_CLIENT_JSON"]
REFRESH_TOKEN = os.environ["YOUTUBE_REFRESH_TOKEN"]
CHANNEL_VOICE = "en-US-AriaNeural"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

IDEAS = [
    ("nature", "mountain sunrise forest river waterfall"),
    ("travel", "cinematic winding mountain road travel adventure"),
    ("nature", "misty green mountains lake sunrise"),
    ("travel", "beautiful mountain valley road scenic journey"),
    ("nature", "ocean waves forest waterfall peaceful landscape"),
    ("travel", "snow mountains hiking scenic travel landscape"),
    ("nature", "golden sunrise clouds mountains"),
    ("travel", "river bridge green valley aerial landscape"),
]
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

def download_pexels_video(query):
    headers = {"Authorization": PEXELS_KEY}
    r = requests.get(
        "https://api.pexels.com/videos/search",
        headers=headers,
        params={"query": query, "per_page": 15, "orientation": "portrait"},
        timeout=30,
    )
    r.raise_for_status()
    data = r.json().get("videos", [])
    if not data:
        # Retry a broad query in case portrait inventory is limited.
        r = requests.get(
            "https://api.pexels.com/videos/search",
            headers=headers,
            params={"query": "nature mountains landscape", "per_page": 15},
            timeout=30,
        )
        r.raise_for_status()
        data = r.json().get("videos", [])
    if not data:
        raise RuntimeError("Pexels returned no videos. Check the API key or try again later.")
    random.shuffle(data)
    for video in data:
        files = sorted(video.get("video_files", []), key=lambda x: (x.get("width", 0), x.get("height", 0)), reverse=True)
        candidates = [f for f in files if f.get("link") and f.get("file_type") == "video/mp4"]
        if candidates:
            selected = candidates[0]
            resp = requests.get(selected["link"], timeout=90)
            resp.raise_for_status()
            path = OUT / "source.mp4"
            path.write_bytes(resp.content)
            # Keep source URL/creator for a basic audit trail.
            (OUT / "source_info.txt").write_text(
                f"Source: Pexels\nVideo page: {video.get('url','')}\nCreator: {video.get('user',{}).get('name','')}\n",
                encoding="utf-8"
            )
            return path
    raise RuntimeError("No downloadable MP4 found in Pexels results.")

def create_voice(lines):
    text = " ".join(lines)
    async def make():
        communicate = edge_tts.Communicate(text, CHANNEL_VOICE, rate="-5%", pitch="-2Hz")
        await communicate.save(str(OUT / "voice.mp3"))
    asyncio.run(make())

def create_original_ambient_music(path, seconds=30, sample_rate=44100):
    # Original synthesized ambient bed; no third-party recording or copyrighted song.
    # Soft pad-like chord progression made from sine waves.
    chords = [
        (220.00, 277.18, 329.63),
        (196.00, 246.94, 293.66),
        (174.61, 220.00, 261.63),
        (196.00, 246.94, 293.66),
    ]
    frames = int(seconds * sample_rate)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        for i in range(frames):
            t = i / sample_rate
            chord = chords[int(t // 7.5) % len(chords)]
            fade = min(1.0, t / 2.0, max(0.0, (seconds - t) / 2.0))
            sample = sum(math.sin(2 * math.pi * f * t) for f in chord) / 3.0
            # very quiet music bed under narration
            value = int(32767 * 0.055 * fade * sample)
            wf.writeframesraw(struct.pack("<hh", value, value))

def make_srt(lines, path):
    # Approximate even timing; readable two-line captions.
    starts = [0, 7, 14, 22]
    ends   = [7, 14, 22, 30]
    def stamp(sec):
        ms = int(round(sec * 1000))
        h, rem = divmod(ms, 3600000)
        m, rem = divmod(rem, 60000)
        s, ms = divmod(rem, 1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"
    chunks = []
    for i, line in enumerate(lines):
        chunks.append(f"{i+1}\n{stamp(starts[i])} --> {stamp(ends[i])}\n{line}\n")
    path.write_text("\n".join(chunks), encoding="utf-8")

def render_video(source, lines):
    create_voice(lines)
    create_original_ambient_music(OUT / "music.wav", DURATION)
    make_srt(lines, OUT / "captions.srt")
    # Portrait crop, subtle brightness/contrast, burned captions, original generated music,
    # and female English neural narration. Use a widely available font.
    srt_path = str((OUT / "captions.srt").resolve()).replace("\\", "/").replace(":", r"\:")
    vf = (
        "scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,"
        "fps=30,"
        f"subtitles='{srt_path}':force_style='FontName=DejaVu Sans,FontSize=18,"
        "Bold=1,PrimaryColour=&H00FFFFFF,OutlineColour=&H00101010,BorderStyle=1,"
        "Outline=2,Shadow=1,Alignment=2,MarginV=220'"
    )
    run([
        "ffmpeg", "-y", "-stream_loop", "-1", "-i", str(source),
        "-i", str(OUT / "voice.mp3"), "-i", str(OUT / "music.wav"),
        "-filter_complex",
        "[1:a]volume=1.0,apad=pad_dur=30[voice];[2:a]volume=0.20[bg];[voice][bg]amix=inputs=2:duration=longest:dropout_transition=2[a]",
        "-map", "0:v:0", "-map", "[a]",
        "-vf", vf, "-t", str(DURATION), "-r", "30",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k", "-shortest",
        "-movflags", "+faststart", str(OUT / "short.mp4")
    ])

def youtube_client():
    client_data = json.loads(CLIENT_JSON)
    # Accept standard downloaded Desktop OAuth JSON.
    if "installed" not in client_data and "web" not in client_data:
        raise ValueError("YOUTUBE_CLIENT_JSON must contain the complete downloaded OAuth client JSON.")
    client = client_data.get("installed") or client_data.get("web")
    creds = Credentials(
        token=None,
        refresh_token=REFRESH_TOKEN,
        token_uri=client.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=client["client_id"],
        client_secret=client["client_secret"],
        scopes=SCOPES,
    )
    creds.refresh(Request())
    return build("youtube", "v3", credentials=creds)

def upload_video(lines, query):
    youtube = youtube_client()
    title_seed = lines[0].rstrip(".!")
    title = (title_seed + " | Nature & Motivation #Shorts")[:100]
    description = (
        "A little reminder to keep moving forward. Original motivational narration and "
        "original synthesized ambient music over a nature/travel visual.\n\n"
        f"Visual search theme: {query}\n"
        "Nature/travel footage source details are recorded in the workflow artifact.\n\n"
        + HASHTAGS
    )
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": ["motivation", "nature", "travel", "mindset", "shorts"],
            "categoryId": "22",
        },
        "status": {
            "privacyStatus": os.getenv("YOUTUBE_PRIVACY_STATUS", "private"),
            "selfDeclaredMadeForKids": False,
        },
    }
    media = MediaFileUpload(str(OUT / "short.mp4"), mimetype="video/mp4", resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Upload progress: {int(status.progress() * 100)}%")
    print("Upload complete. Video ID:", response.get("id"))
    print("Privacy status:", body["status"]["privacyStatus"])

def main():
    theme, query = random.choice(IDEAS)
    lines = choose_quote()
    print("Theme:", theme, "| Query:", query)
    print("Original narration:", " ".join(lines))
    source = download_pexels_video(query)
    render_video(source, lines)
    upload_video(lines, query)

if __name__ == "__main__":
    main()

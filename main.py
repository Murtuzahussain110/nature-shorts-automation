import os
import json
import random
import subprocess
import textwrap
from pathlib import Path

import requests
from PIL import Image
import edge_tts

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


# =========================
# SETTINGS
# =========================

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
SCENES_DIR = OUTPUT_DIR / "scenes"

OUTPUT_DIR.mkdir(exist_ok=True)
SCENES_DIR.mkdir(exist_ok=True)

VIDEO_FILE = OUTPUT_DIR / "nature_short.mp4"
VOICE_FILE = OUTPUT_DIR / "voice.mp3"
SUBTITLE_FILE = OUTPUT_DIR / "subtitles.srt"
CONCAT_FILE = OUTPUT_DIR / "clips.txt"

WIDTH = 1080
HEIGHT = 1920
FPS = 25

VOICE = "ur-PK-UzmaNeural"
PEXELS_API = "https://api.pexels.com/v1/search"


# =========================
# STORIES
# =========================

STORIES = [
    {
        "title": "Lost in the World's Wildest Jungle",
        "narration": (
            "ایک مسافر گھنے جنگل میں راستہ بھول گیا۔ "
            "ہر طرف عجیب آوازیں سنائی دے رہی تھیں۔ "
            "اچانک اسے درختوں کے پیچھے دو چمکتی ہوئی آنکھیں نظر آئیں۔ "
            "وہ آہستہ آہستہ پیچھے ہٹنے لگا۔ "
            "لیکن پھر اسے زمین پر ایک پرانا نقشہ ملا۔ "
            "کیا یہ نقشہ اسے جنگل سے باہر نکال سکتا تھا؟"
        ),
        "scenes": [
            ("tropical jungle dense forest", "A mysterious jungle stretches endlessly."),
            ("jungle narrow forest path", "He follows a lonely path into the forest."),
            ("dark jungle sunlight trees", "Strange sounds come from the darkness."),
            ("wild animal eyes dark forest", "Two glowing eyes appear behind the trees."),
            ("old map on forest ground", "An old map is hidden beneath the leaves."),
            ("jungle sunrise forest river", "A new path appears beyond the trees.")
        ]
    },
    {
        "title": "The Secret Hidden Under the Ocean",
        "narration": (
            "سمندر کی گہرائی میں ایک غوطہ خور کو ایک پراسرار دروازہ ملا۔ "
            "یہ دروازہ عام پتھروں جیسا نہیں تھا۔ "
            "اس پر عجیب نشان بنے ہوئے تھے۔ "
            "جیسے ہی اس نے دروازے کو چھوا، روشنی چمکنے لگی۔ "
            "اس کے سامنے ایک پرانی ڈوبی ہوئی دنیا تھی۔ "
            "آخر یہ جگہ ہزاروں سال سے کس راز کو چھپائے ہوئے تھی؟"
        ),
        "scenes": [
            ("deep blue ocean underwater", "Deep beneath the ocean, something waits."),
            ("scuba diver underwater rocks", "A diver discovers a strange structure."),
            ("underwater ancient stone door", "Mysterious symbols cover the doorway."),
            ("underwater glowing blue light", "The ancient door begins to glow."),
            ("underwater lost ancient city ruins", "A forgotten city appears underwater."),
            ("underwater sun rays ocean ruins", "The ocean keeps its secret.")
        ]
    },
    {
        "title": "A Strange Light in the Mountains",
        "narration": (
            "ایک پہاڑی گاؤں میں ہر رات ایک عجیب روشنی دکھائی دیتی تھی۔ "
            "لوگ اسے دیکھ کر خوفزدہ ہو جاتے تھے۔ "
            "ایک نوجوان نے اس راز کو جاننے کا فیصلہ کیا۔ "
            "وہ رات کے اندھیرے میں پہاڑ کی طرف روانہ ہوا۔ "
            "وہاں اسے ایک پرانی غار نظر آئی۔ "
            "غار کے اندر کیا تھا، یہ آج تک کوئی نہیں جانتا۔"
        ),
        "scenes": [
            ("dramatic mountain village night", "A quiet village hides a strange mystery."),
            ("mountains glowing light night", "A mysterious light appears every night."),
            ("hiker walking mountain trail night", "A young explorer follows the light."),
            ("rocky mountain cave entrance", "He discovers an ancient cave."),
            ("mysterious cave glowing crystals", "A strange glow fills the cave."),
            ("mountain sunrise mist landscape", "The mystery remains unsolved.")
        ]
    },
    {
        "title": "The Forest That Never Sleeps",
        "narration": (
            "دنیا میں ایک ایسا جنگل بھی ہے جہاں رات کو درختوں سے آوازیں آتی ہیں۔ "
            "ایک تحقیقاتی ٹیم وہاں پہنچی۔ "
            "انہوں نے کیمرے لگائے اور رات کا انتظار کیا۔ "
            "آدھی رات کو درختوں کے درمیان حرکت محسوس ہوئی۔ "
            "صبح کیمرے میں ایک حیران کن منظر ریکارڈ تھا۔ "
            "کیا یہ کوئی جانور تھا یا قدرت کا کوئی انوکھا راز؟"
        ),
        "scenes": [
            ("mysterious forest fog tall trees", "A forest hides an unusual secret."),
            ("scientists exploring forest", "A research team enters the forest."),
            ("wildlife camera in forest at night", "Cameras watch the forest after dark."),
            ("dark forest moonlight mist", "Something moves between the trees."),
            ("forest animal silhouette night", "The camera captures a mysterious shape."),
            ("sunlight through green forest", "Nature still holds many secrets.")
        ]
    },
    {
        "title": "The World's Most Dangerous Road",
        "narration": (
            "پہاڑوں کے درمیان ایک ایسی سڑک ہے جہاں ذرا سی غلطی خطرناک ہو سکتی ہے۔ "
            "ایک طرف بلند پہاڑ اور دوسری طرف گہری کھائی ہے۔ "
            "ڈرائیور آہستہ آہستہ گاڑی آگے بڑھاتا ہے۔ "
            "راستے میں اچانک شدید دھند چھا جاتی ہے۔ "
            "کچھ لمحوں کے لیے اسے کچھ دکھائی نہیں دیتا۔ "
            "کیا وہ بحفاظت منزل تک پہنچ پائے گا؟"
        ),
        "scenes": [
            ("dangerous narrow mountain road", "A road winds through towering mountains."),
            ("mountain road deep valley", "A deep valley lies beside the road."),
            ("vehicle driving mountain road", "A driver carefully moves forward."),
            ("thick fog mountain highway", "Suddenly, thick fog covers the road."),
            ("winding road mountain mist", "The road disappears into the mist."),
            ("beautiful mountain road sunrise", "At last, the road opens ahead.")
        ]
    },
    {
        "title": "The Hidden Paradise in the Mountains",
        "narration": (
            "ایک سیاح پہاڑوں میں سفر کر رہا تھا۔ "
            "اچانک اسے ایک تنگ راستہ نظر آیا۔ "
            "وہ راستے پر چلتا ہوا ایک خوبصورت وادی میں پہنچ گیا۔ "
            "وہاں صاف پانی، سبز میدان اور بلند پہاڑ تھے۔ "
            "اس نے ایسی خوبصورتی پہلے کبھی نہیں دیکھی تھی۔ "
            "دنیا میں آج بھی کئی ایسی جگہیں ہیں جو انسانوں کی نظروں سے چھپی ہوئی ہیں۔"
        ),
        "scenes": [
            ("majestic green mountains landscape", "A traveler explores the mountains."),
            ("narrow mountain hiking trail", "A hidden trail leads deeper into the hills."),
            ("beautiful green mountain valley", "A breathtaking valley appears."),
            ("clear river flowing green meadow", "Crystal-clear water flows through the valley."),
            ("snow capped mountains peaceful nature", "Snow-covered peaks surround the paradise."),
            ("sunrise alpine valley landscape", "Some beautiful places remain undiscovered.")
        ]
    }
]


# =========================
# RUN COMMAND
# =========================

def run_command(command):
    print("Running:", " ".join(map(str, command)))
    subprocess.run(
        command,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )


def get_duration(file_path):
    result = subprocess.run(
        [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(file_path)
        ],
        check=True,
        capture_output=True,
        text=True
    )
    return float(result.stdout.strip())


# =========================
# DOWNLOAD PEXELS PHOTOS
# =========================

def generate_image(query, scene_number, used_photo_ids):
    api_key = os.getenv("PEXELS_API_KEY")

    if not api_key:
        raise RuntimeError(
            "PEXELS_API_KEY secret is missing from GitHub."
        )

    print(f"Searching Pexels scene {scene_number}: {query}")

    response = requests.get(
        PEXELS_API,
        headers={"Authorization": api_key},
        params={
            "query": query,
            "orientation": "portrait",
            "per_page": 30
        },
        timeout=60
    )
    response.raise_for_status()

    photos = response.json().get("photos", [])

    if not photos:
        raise RuntimeError(f"No Pexels photos found for: {query}")

    available = [
        photo for photo in photos
        if photo.get("id") not in used_photo_ids
    ]

    if not available:
        available = photos

    photo = random.choice(available)
    used_photo_ids.add(photo.get("id"))

    image_url = (
        photo.get("src", {}).get("large2x")
        or photo.get("src", {}).get("large")
    )

    if not image_url:
        raise RuntimeError("Pexels did not return a usable image URL.")

    image_response = requests.get(image_url, timeout=90)
    image_response.raise_for_status()

    destination = SCENES_DIR / f"scene_{scene_number}.jpg"
    destination.write_bytes(image_response.content)

    with Image.open(destination) as img:
        img.verify()

    with Image.open(destination) as img:
        if img.width < 500 or img.height < 500:
            raise RuntimeError("Downloaded photo resolution is too small.")

    print(f"Scene {scene_number} photo verified.")
    return destination


# =========================
# CREATE SIX SCENES
# =========================

def generate_all_images(story):
    used_photo_ids = set()
    image_files = []

    for number, scene in enumerate(story["scenes"], start=1):
        query, caption = scene

        image_path = generate_image(
            query,
            number,
            used_photo_ids
        )

        image_files.append(image_path)

    return image_files


# =========================
# URDU VOICE
# =========================

async def generate_voice(text):
    print("Generating Urdu voice-over...")

    communicate = edge_tts.Communicate(
        text=text,
        voice=VOICE,
        rate="-5%",
        volume="+0%"
    )

    await communicate.save(str(VOICE_FILE))

    if not VOICE_FILE.exists() or VOICE_FILE.stat().st_size < 1000:
        raise RuntimeError("Urdu voice generation failed.")

    print("Urdu voice-over ready.")


# =========================
# ENGLISH SUBTITLES
# =========================

def make_subtitles(story, total_duration):
    scenes = story["scenes"]
    scene_duration = total_duration / len(scenes)

    def timestamp(seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds - int(seconds)) * 1000)

        return (
            f"{hours:02}:{minutes:02}:"
            f"{secs:02},{millis:03}"
        )

    subtitle_lines = []

    for index, scene in enumerate(scenes):
        start = index * scene_duration
        end = min((index + 1) * scene_duration, total_duration)

        caption = scene[1]

        subtitle_lines.append(
            f"{index + 1}\n"
            f"{timestamp(start)} --> {timestamp(end)}\n"
            f"{caption}\n"
        )

    SUBTITLE_FILE.write_text(
        "\n".join(subtitle_lines),
        encoding="utf-8"
    )


# =========================
# CREATE VIDEO CLIPS
# =========================

def create_scene_clips(image_files, total_duration):
    clip_duration = total_duration / len(image_files)
    clip_files = []

    for index, image_path in enumerate(image_files, start=1):
        clip_path = OUTPUT_DIR / f"clip_{index}.mp4"
        frames = max(1, int(clip_duration * FPS))

        video_filter = (
            f"scale={WIDTH}:{HEIGHT}:"
            "force_original_aspect_ratio=increase,"
            f"crop={WIDTH}:{HEIGHT},"
            "setsar=1,"
            f"zoompan=z='min(zoom+0.0008,1.08)':"
            "x='iw/2-(iw/zoom/2)':"
            "y='ih/2-(ih/zoom/2)':"
            f"d={frames}:s={WIDTH}x{HEIGHT}:fps={FPS},"
            "format=yuv420p"
        )

        run_command([
            "ffmpeg",
            "-y",
            "-loop", "1",
            "-i", str(image_path),
            "-vf", video_filter,
            "-t", str(clip_duration),
            "-r", str(FPS),
            "-an",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-pix_fmt", "yuv420p",
            str(clip_path)
        ])

        clip_files.append(clip_path)
        print(f"Created video scene {index}/{len(image_files)}.")

    return clip_files


# =========================
# JOIN VIDEO CLIPS
# =========================

def join_clips(clip_files):
    lines = []

    for clip in clip_files:
        safe_path = str(clip.resolve()).replace("'", "'\\''")
        lines.append(f"file '{safe_path}'")

    CONCAT_FILE.write_text(
        "\n".join(lines),
        encoding="utf-8"
    )

    silent_video = OUTPUT_DIR / "silent_video.mp4"

    run_command([
        "ffmpeg",
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(CONCAT_FILE),
        "-c", "copy",
        str(silent_video)
    ])

    return silent_video


# =========================
# FINAL VIDEO
# =========================

def create_final_video(silent_video):
    print("Adding subtitles and voice-over...")

    subtitle_path = str(SUBTITLE_FILE.resolve())
    subtitle_path = subtitle_path.replace("\\", "/")
    subtitle_path = subtitle_path.replace(":", "\\:")

    subtitle_filter = (
        f"subtitles='{subtitle_path}':"
        "force_style='FontName=DejaVu Sans,"
        "FontSize=20,"
        "PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,"
        "BorderStyle=1,"
        "Outline=2,"
        "Shadow=1,"
        "Alignment=2,"
        "MarginV=150'"
    )

    # Soft synthesized background tone.
    # This is ambient audio, not a real music track or sound effects.
    run_command([
        "ffmpeg",
        "-y",
        "-i", str(silent_video),
        "-i", str(VOICE_FILE),
        "-f", "lavfi",
        "-i", "sine=frequency=110:sample_rate=44100",
        "-filter_complex",
        (
            f"[0:v]{subtitle_filter}[v];"
            "[1:a]volume=1.0[voice];"
            "[2:a]volume=0.035[ambient];"
            "[voice][ambient]amix=inputs=2:"
            "duration=first:dropout_transition=2[a]"
        ),
        "-map", "[v]",
        "-map", "[a]",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "-movflags", "+faststart",
        str(VIDEO_FILE)
    ])

    if not VIDEO_FILE.exists() or VIDEO_FILE.stat().st_size < 10000:
        raise RuntimeError("Final video was not created correctly.")

    print("Final video created successfully.")


# =========================
# YOUTUBE UPLOAD
# =========================

def upload_to_youtube(title):
    print("Preparing YouTube upload...")

    client_json = os.getenv("YOUTUBE_CLIENT_JSON")
    refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN")

    if not client_json:
        raise RuntimeError("YOUTUBE_CLIENT_JSON secret is missing.")

    if not refresh_token:
        raise RuntimeError("YOUTUBE_REFRESH_TOKEN secret is missing.")

    client_data = json.loads(client_json)

    client_info = (
        client_data.get("installed")
        or client_data.get("web")
    )

    if not client_info:
        raise RuntimeError(
            "Your YouTube client JSON must contain installed or web details."
        )

    credentials = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri=client_info.get(
            "token_uri",
            "https://oauth2.googleapis.com/token"
        ),
        client_id=client_info["client_id"],
        client_secret=client_info["client_secret"],
        scopes=["https://www.googleapis.com/auth/youtube.upload"]
    )

    youtube = build(
        "youtube",
        "v3",
        credentials=credentials
    )

    privacy = os.getenv("YOUTUBE_PRIVACY_STATUS", "private")

    if privacy not in ("private", "unlisted", "public"):
        privacy = "private"

    body = {
        "snippet": {
            "title": title[:100],
            "description": (
                "A short cinematic nature and mystery story.\n\n"
                "Subscribe for more nature, adventure and mystery videos.\n\n"
                "#Nature #Adventure #Mystery #Shorts"
            ),
            "tags": [
                "nature",
                "adventure",
                "mystery",
                "shorts",
                "travel",
                "cinematic"
            ],
            "categoryId": "22"
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False
        }
    }

    media = MediaFileUpload(
        str(VIDEO_FILE),
        mimetype="video/mp4",
        resumable=True
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    response = None

    while response is None:
        status, response = request.next_chunk()

        if status:
            print(
                f"YouTube upload: {int(status.progress() * 100)}%"
            )

    video_id = response.get("id")

    print("YouTube upload successful.")
    print(f"Video ID: {video_id}")
    print(f"Privacy: {privacy}")
    print(f"Video URL: https://www.youtube.com/watch?v={video_id}")


# =========================
# MAIN
# =========================

def main():
    print("\n===================================")
    print("       NATURE SHORTS AUTOMATION")
    print("===================================\n")

    run_id = os.getenv("GITHUB_RUN_ID", "local")
    attempt = os.getenv("GITHUB_RUN_ATTEMPT", "1")

    random.seed(f"{run_id}-{attempt}")

    story = random.choice(STORIES)

    print("Selected story:", story["title"])

    # Remove old scene files so old images cannot be reused.
    for old_file in SCENES_DIR.glob("*"):
        if old_file.is_file():
            old_file.unlink()

    image_files = generate_all_images(story)

    import asyncio
    asyncio.run(generate_voice(story["narration"]))

    total_duration = get_duration(VOICE_FILE)
    print(f"Voice duration: {total_duration:.1f} seconds")

    make_subtitles(story, total_duration)

    clip_files = create_scene_clips(
        image_files,
        total_duration
    )

    silent_video = join_clips(clip_files)

    create_final_video(silent_video)

    upload_to_youtube(story["title"])

    print("\nALL TASKS COMPLETED.")


if __name__ == "__main__":
    main()

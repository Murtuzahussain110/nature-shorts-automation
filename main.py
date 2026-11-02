
import os
import json
import random
import hashlib
import asyncio
import subprocess
import requests
from pathlib import Path
from urllib.parse import quote

from PIL import Image
import edge_tts

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


# ==========================================
# CONFIGURATION
# ==========================================

OUTPUT = Path("output")
SCENES = OUTPUT / "scenes"

OUTPUT.mkdir(exist_ok=True)
SCENES.mkdir(exist_ok=True)

VOICE_FILE = OUTPUT / "voice.mp3"
MUSIC_FILE = OUTPUT / "music.mp3"
SUBTITLE_FILE = OUTPUT / "subtitles.srt"
VIDEO_FILE = OUTPUT / "nature_short.mp4"

WIDTH = 1080
HEIGHT = 1920
FPS = 25

VOICE = "ur-PK-UzmaNeural"

IMAGE_ENDPOINT = "https://image.pollinations.ai/prompt/"

# ==========================================
# STORIES
# ==========================================

TOPICS = [
    {
        "title": "The Door Hidden in the Forest",
        "english": [
            "Deep inside a forgotten forest, something strange was discovered.",
            "A mysterious wooden door stood between two ancient trees.",
            "Nobody knew who built it or what was hidden behind it.",
            "An explorer slowly reached for its rusty handle.",
            "A cold wind suddenly came from the other side.",
            "And then, the door began opening by itself."
        ],
        "urdu": [
            "ایک بھولے بسرے جنگل میں ایک عجیب چیز دریافت ہوئی۔",
            "دو قدیم درختوں کے درمیان لکڑی کا ایک پراسرار دروازہ تھا۔",
            "کسی کو معلوم نہیں تھا کہ اسے کس نے بنایا یا اس کے پیچھے کیا چھپا تھا۔",
            "ایک مہم جو آہستہ آہستہ اس کے زنگ آلود ہینڈل تک پہنچا۔",
            "اچانک دوسری طرف سے ٹھنڈی ہوا آنے لگی۔",
            "اور پھر دروازہ خود بخود کھلنے لگا۔"
        ],
        "prompts": [
            "A vast mysterious ancient forest covered in thick fog, enormous trees, cinematic photorealistic photography",
            "An old wooden door standing between two giant ancient trees, moss and mysterious atmosphere, realistic film still",
            "Close up of a mysterious old wooden door covered in moss and strange carvings, cinematic lighting",
            "A lone explorer in a dark outdoor jacket approaching an ancient forest door, photorealistic wide shot",
            "Cold mist flowing from a half open wooden door in a dark forest, dramatic cinematic photography",
            "An ancient wooden door opening by itself in a foggy forest, mysterious cinematic scene"
        ]
    },
    {
        "title": "What Happens Inside a Black Hole?",
        "english": [
            "Somewhere in space, gravity becomes unbelievably powerful.",
            "Scientists call this mysterious object a black hole.",
            "Its gravity is so strong that even light cannot escape.",
            "Anything crossing its boundary cannot return.",
            "At its center, our understanding of physics faces a mystery.",
            "And the truth about what happens inside is still unknown."
        ],
        "urdu": [
            "خلاء میں کہیں کشش ثقل ناقابل یقین حد تک طاقتور ہو جاتی ہے۔",
            "سائنس دان اس پراسرار چیز کو بلیک ہول کہتے ہیں۔",
            "اس کی کشش اتنی مضبوط ہے کہ روشنی بھی باہر نہیں نکل سکتی۔",
            "اس کی حد عبور کرنے والی کوئی چیز واپس نہیں آ سکتی۔",
            "اس کے مرکز میں ہماری فزکس کی سمجھ ایک راز بن جاتی ہے۔",
            "اور اندر کیا ہوتا ہے، اس کی حقیقت ابھی تک معلوم نہیں۔"
        ],
        "prompts": [
            "A giant black hole in deep space with a glowing accretion disk, photorealistic scientific visualization",
            "A black hole surrounded by distant stars and galaxies, breathtaking cinematic space photography",
            "A powerful black hole bending light from nearby stars, realistic astrophysics visualization",
            "A small research spacecraft approaching the event horizon of a giant black hole, cinematic",
            "Mysterious glowing gravitational center of a black hole, detailed scientific space visualization",
            "A black hole surrounded by cosmic dust and distant galaxies, ultra detailed cinematic scene"
        ]
    },
    {
        "title": "Lost in the World's Wildest Jungle",
        "english": [
            "A traveler entered a jungle that few people had ever explored.",
            "The trees were so tall that sunlight barely reached the ground.",
            "Strange sounds followed him through the thick green forest.",
            "After hours of walking, he discovered an abandoned path.",
            "It led to ruins hidden beneath the roots of giant trees.",
            "But something inside those ruins was still moving."
        ],
        "urdu": [
            "ایک مسافر ایسے جنگل میں داخل ہوا جہاں بہت کم لوگ گئے تھے۔",
            "درخت اتنے اونچے تھے کہ سورج کی روشنی زمین تک مشکل سے پہنچتی تھی۔",
            "گھنے سبز جنگل میں عجیب آوازیں اس کا پیچھا کر رہی تھیں۔",
            "کئی گھنٹے چلنے کے بعد اسے ایک پرانا راستہ ملا۔",
            "یہ راستہ دیوہیکل درختوں کی جڑوں کے نیچے چھپے کھنڈرات تک جاتا تھا۔",
            "لیکن ان کھنڈرات کے اندر اب بھی کوئی چیز حرکت کر رہی تھی۔"
        ],
        "prompts": [
            "A vast unexplored tropical jungle with towering trees and thick green vegetation, photorealistic",
            "Sunlight rays barely entering a dense rainforest, mysterious cinematic atmosphere",
            "A narrow jungle trail with mysterious animal eyes visible in distant shadows, realistic",
            "An abandoned path through a dense tropical forest, cinematic adventure photography",
            "Ancient stone ruins covered in giant tree roots and green moss, realistic discovery scene",
            "A mysterious dark entrance inside ancient jungle ruins, suspenseful cinematic photography"
        ]
    },
    {
        "title": "The Dog That Waited Every Day",
        "english": [
            "Every morning, a lonely dog sat outside the same railway station.",
            "He was waiting for someone who never came back.",
            "People passed by, but he never left his place.",
            "Days turned into months, and the dog kept waiting.",
            "One day, a stranger noticed the old photograph near him.",
            "It revealed the heartbreaking reason for his wait."
        ],
        "urdu": [
            "ہر صبح ایک تنہا کتا اسی ریلوے اسٹیشن کے باہر بیٹھتا تھا۔",
            "وہ کسی ایسے شخص کا انتظار کر رہا تھا جو کبھی واپس نہیں آیا۔",
            "لوگ وہاں سے گزرتے رہے لیکن وہ اپنی جگہ سے نہیں ہٹا۔",
            "دن مہینوں میں بدل گئے اور کتا انتظار کرتا رہا۔",
            "ایک دن ایک اجنبی نے اس کے پاس پڑی پرانی تصویر دیکھی۔",
            "اس تصویر نے اس کے انتظار کی دردناک وجہ بتا دی۔"
        ],
        "prompts": [
            "A lonely golden brown dog sitting outside an old railway station, emotional cinematic photography",
            "A loyal golden brown dog looking toward an empty railway platform, soft morning light",
            "People walking past a lonely golden brown dog at a railway station, emotional realistic scene",
            "The same golden brown dog waiting outside a railway station during rainy weather, cinematic",
            "An old photograph lying beside a golden brown dog on a railway station floor, close up",
            "An emotional golden brown dog beside an old photograph at a railway station, warm cinematic light"
        ]
    },
    {
        "title": "The Amazing Intelligence of Octopuses",
        "english": [
            "Deep beneath the ocean lives an incredibly intelligent animal.",
            "The octopus has three hearts and blue blood.",
            "It can solve puzzles and open containers to find food.",
            "Some octopuses even use objects as tools.",
            "Their bodies can change color to hide from danger.",
            "Scientists are still discovering how intelligent they really are."
        ],
        "urdu": [
            "سمندر کی گہرائی میں ایک حیرت انگیز ذہین جانور رہتا ہے۔",
            "آکٹوپس کے تین دل اور نیلا خون ہوتا ہے۔",
            "یہ خوراک تلاش کرنے کے لیے پہیلیاں حل اور ڈبے کھول سکتا ہے۔",
            "کچھ آکٹوپس چیزوں کو اوزار کے طور پر بھی استعمال کرتے ہیں۔",
            "ان کے جسم خطرے سے بچنے کے لیے رنگ بدل سکتے ہیں۔",
            "سائنس دان اب بھی ان کی ذہانت کو سمجھنے کی کوشش کر رہے ہیں۔"
        ],
        "prompts": [
            "A realistic octopus swimming in deep blue ocean water, underwater wildlife documentary",
            "Close up of a beautiful octopus with detailed eyes and tentacles, photorealistic",
            "An octopus opening a glass container underwater, realistic nature documentary photography",
            "An octopus using a shell as a tool on the ocean floor, photorealistic underwater scene",
            "An octopus blending into a colorful coral reef, underwater macro photography",
            "A beautiful intelligent octopus in the mysterious deep ocean, cinematic documentary"
        ]
    },
    {
        "title": "The Mountain Nobody Could Climb",
        "english": [
            "Far beyond the clouds stood a mountain nobody had conquered.",
            "Its cliffs were steep and its weather changed without warning.",
            "Many explorers had tried, but none had reached the summit.",
            "One determined climber decided to attempt the impossible.",
            "After days of climbing, he finally reached the highest ridge.",
            "But the view waiting above the clouds was beyond imagination."
        ],
        "urdu": [
            "بادلوں سے بہت اوپر ایک ایسا پہاڑ تھا جسے کوئی سر نہیں کر سکا تھا۔",
            "اس کی چٹانیں سیدھی تھیں اور موسم اچانک بدل جاتا تھا۔",
            "بہت سے مہم جوؤں نے کوشش کی لیکن کوئی چوٹی تک نہ پہنچا۔",
            "ایک پُرعزم کوہ پیما نے ناممکن کو ممکن بنانے کا فیصلہ کیا۔",
            "کئی دن کی چڑھائی کے بعد وہ آخرکار بلند ترین مقام پر پہنچ گیا۔",
            "لیکن بادلوں کے اوپر کا منظر اس کے تصور سے بھی زیادہ خوبصورت تھا۔"
        ],
        "prompts": [
            "A gigantic remote snowy mountain peak rising above clouds, photorealistic adventure photography",
            "Steep dangerous icy mountain cliffs during a snowstorm, cinematic landscape",
            "An abandoned mountaineering camp on a snowy mountain trail, realistic scene",
            "A lone climber wearing a red jacket climbing a steep snowy mountain, cinematic wide shot",
            "A mountaineer reaching a high snowy ridge above the clouds, photorealistic",
            "Breathtaking sunrise over Himalayan mountain peaks above clouds, cinematic landscape"
        ]
    }
]


# ==========================================
# COMMAND HELPER
# ==========================================

def run(command):
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr[-4000:])

    return result


def clean_output():
    for path in SCENES.glob("*"):
        if path.is_file():
            path.unlink()

    for path in [
        VOICE_FILE,
        MUSIC_FILE,
        SUBTITLE_FILE,
        VIDEO_FILE,
        OUTPUT / "joined.mp4",
        OUTPUT / "concat.txt"
    ]:
        if path.exists():
            path.unlink()


# ==========================================
# UNIQUE STORY SELECTION
# ==========================================

def choose_story():
    run_id = os.getenv("GITHUB_RUN_ID")
    attempt = os.getenv("GITHUB_RUN_ATTEMPT", "1")

    if run_id:
        value = f"{run_id}-{attempt}"
        seed = int(hashlib.sha256(value.encode()).hexdigest(), 16)
        return random.Random(seed).choice(TOPICS)

    return random.choice(TOPICS)


# ==========================================
# IMAGE GENERATION
# ==========================================

def generate_image(prompt, scene_number):
    seed = random.randint(100000, 999999999)

    full_prompt = (
        prompt
        + ", vertical portrait composition, 9:16, "
        "professional cinematic photography, highly detailed, "
        "realistic lighting, no text, no watermark"
    )

    url = IMAGE_ENDPOINT + quote(full_prompt, safe="")

    params = {
        "width": WIDTH,
        "height": HEIGHT,
        "seed": seed,
        "nologo": "true"
    }

    destination = SCENES / f"scene_{scene_number}.jpg"

    last_error = None

    for attempt in range(1, 4):
        try:
            print(
                f"Generating scene {scene_number}/6 "
                f"(attempt {attempt}/3)..."
            )

            response = requests.get(
                url,
                params=params,
                timeout=180,
                headers={"User-Agent": "NatureShortsAutomation/1.0"}
            )

            response.raise_for_status()

            content_type = response.headers.get(
                "Content-Type", ""
            ).lower()

            if "image" not in content_type:
                raise RuntimeError(
                    f"Server did not return an image: {content_type}"
                )

            if len(response.content) < 10000:
                raise RuntimeError("Returned image is too small.")

            destination.write_bytes(response.content)

            with Image.open(destination) as image:
                image.verify()

            with Image.open(destination) as image:
                if image.width < 500 or image.height < 500:
                    raise RuntimeError("Image dimensions are too small.")

            print(f"Scene {scene_number} verified.")
            return destination

        except Exception as error:
            last_error = error
            print(f"Scene {scene_number} failed: {error}")

            if destination.exists():
                destination.unlink()

    raise RuntimeError(
        f"STOP: Scene {scene_number} could not be generated. "
        f"No video will be uploaded. Last error: {last_error}"
    )


def generate_all_images(story):
    images = []

    for number, prompt in enumerate(story["prompts"], start=1):
        image_path = generate_image(prompt, number)
        images.append(image_path)

    if len(images) != 6:
        raise RuntimeError("Not all six images were generated.")

    for image in images:
        if not image.exists() or image.stat().st_size < 10000:
            raise RuntimeError("A scene image is missing or invalid.")

    print("All six scene images successfully verified.")
    return images


# ==========================================
# URDU NARRATION
# ==========================================

async def make_voice(text):
    speech = edge_tts.Communicate(
        text=text,
        voice=VOICE,
        rate="+12%",
        volume="+0%"
    )
    await speech.save(str(VOICE_FILE))


def create_voice(story):
    narration = " ".join(story["urdu"])

    print("Creating Urdu voice-over...")
    asyncio.run(make_voice(narration))

    if not VOICE_FILE.exists() or VOICE_FILE.stat().st_size < 1000:
        raise RuntimeError("Urdu voice-over was not created.")

    return narration


# ==========================================
# SUBTITLES
# ==========================================

def srt_timestamp(seconds):
    milliseconds = int(round(seconds * 1000))

    hours = milliseconds // 3600000
    milliseconds %= 3600000

    minutes = milliseconds // 60000
    milliseconds %= 60000

    seconds_part = milliseconds // 1000
    milliseconds %= 1000

    return (
        f"{hours:02}:{minutes:02}:"
        f"{seconds_part:02},{milliseconds:03}"
    )


def audio_duration(path):
    result = run([
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(path)
    ])

    return float(result.stdout.strip())


def create_subtitles(story, duration):
    interval = duration / 6

    with open(SUBTITLE_FILE, "w", encoding="utf-8") as file:
        for index, sentence in enumerate(story["english"]):
            start = index * interval
            end = (index + 1) * interval

            file.write(
                f"{index + 1}\n"
                f"{srt_timestamp(start)} --> "
                f"{srt_timestamp(end)}\n"
                f"{sentence}\n\n"
            )


# ==========================================
# BACKGROUND MUSIC
# ==========================================

def create_music(duration):
    print("Creating background music...")

    run([
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"sine=frequency=110:duration={duration}",
        "-af", "volume=0.08,lowpass=f=500,afade=t=in:st=0:d=2",
        "-c:a", "libmp3lame",
        "-q:a", "6",
        str(MUSIC_FILE)
    ])


# ==========================================
# CREATE SIX VIDEO SCENES
# ==========================================

def create_video(images, duration):
    print("Rendering six separate scenes...")

    scene_duration = duration / 6
    clips = []

    for index, image in enumerate(images, start=1):
        if not image.exists():
            raise RuntimeError(f"Scene image missing: {image}")

        clip = SCENES / f"clip_{index}.mp4"

        frames = max(1, int(scene_duration * FPS))

        video_filter = (
            "scale=1200:2134,"
            "crop=1080:1920,"
            f"zoompan=z='min(zoom+0.0005,1.08)':"
            "x='iw/2-(iw/zoom/2)':"
            "y='ih/2-(ih/zoom/2)':"
            f"d={frames}:s=1080x1920:fps={FPS},"
            "setsar=1"
        )

        run([
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(image),
            "-vf", video_filter,
            "-t", str(scene_duration),
            "-r", str(FPS),
            "-an",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-pix_fmt", "yuv420p",
            str(clip)
        ])

        if not clip.exists() or clip.stat().st_size < 10000:
            raise RuntimeError(f"Video scene {index} failed.")

        clips.append(clip)

        print(f"Scene {index}/6 rendered.")

    concat_file = OUTPUT / "concat.txt"

    with open(concat_file, "w", encoding="utf-8") as file:
        for clip in clips:
            file.write(f"file '{clip.resolve()}'\n")

    joined = OUTPUT / "joined.mp4"

    run([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_file),
        "-c", "copy",
        str(joined)
    ])

    subtitle_path = str(SUBTITLE_FILE.resolve())
    subtitle_path = subtitle_path.replace("\\", "/")
    subtitle_path = subtitle_path.replace(":", "\\:")

    subtitle_filter = (
        f"subtitles='{subtitle_path}':"
        "force_style='FontName=DejaVu Sans,"
        "FontSize=17,PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,Outline=2,"
        "Shadow=1,Alignment=2,MarginV=170'"
    )

    print("Adding subtitles, narration and music...")

    run([
        "ffmpeg", "-y",
        "-i", str(joined),
        "-i", str(VOICE_FILE),
        "-i", str(MUSIC_FILE),
        "-filter_complex",
        (
            f"[0:v]{subtitle_filter}[v];"
            "[1:a]volume=1.0[voice];"
            "[2:a]volume=0.12[music];"
            "[voice][music]amix=inputs=2:duration=first[a]"
        ),
        "-map", "[v]",
        "-map", "[a]",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        "-movflags", "+faststart",
        str(VIDEO_FILE)
    ])

    if not VIDEO_FILE.exists() or VIDEO_FILE.stat().st_size < 50000:
        raise RuntimeError("Final video failed validation.")

    print("Final video created successfully.")


# ==========================================
# FINAL VIDEO VALIDATION
# ==========================================

def validate_video():
    result = run([
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(VIDEO_FILE)
    ])

    duration = float(result.stdout.strip())

    if duration <= 0:
        raise RuntimeError("Video duration is invalid.")

    print(f"Video duration: {duration:.1f} seconds")

    return duration


# ==========================================
# YOUTUBE UPLOAD
# ==========================================

def upload_video(story):
    client_json = os.getenv("YOUTUBE_CLIENT_JSON")
    refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN")

    if not client_json or not refresh_token:
        raise RuntimeError("YouTube secrets are missing.")

    client_data = json.loads(client_json)
    app_data = client_data.get("installed") or client_data.get("web")

    if not app_data:
        raise RuntimeError("Invalid YouTube OAuth JSON.")

    credentials = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri=app_data["token_uri"],
        client_id=app_data["client_id"],
        client_secret=app_data["client_secret"],
        scopes=[
            "https://www.googleapis.com/auth/youtube.upload"
        ]
    )

    youtube = build(
        "youtube",
        "v3",
        credentials=credentials
    )

    body = {
        "snippet": {
            "title": story["title"][:100],
            "description": (
                story["title"]
                + "\n\nA cinematic short story.\n"
                "#Shorts #Nature #Mystery #Adventure #Science"
            ),
            "tags": [
                "shorts",
                "nature",
                "mystery",
                "adventure",
                "science"
            ],
            "categoryId": "22"
        },
        "status": {
            "privacyStatus": os.getenv(
                "YOUTUBE_PRIVACY_STATUS", "private"
            ),
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

    response = request.execute()

    print("YouTube upload successful.")
    print("Video ID:", response["id"])


# ==========================================
# MAIN
# ==========================================

def main():
    print("======================================")
    print("      NATURE SHORTS AUTOMATION")
    print("======================================")

    clean_output()

    story = choose_story()

    print("Selected story:", story["title"])

    # No video can proceed without six valid images.
    images = generate_all_images(story)

    create_voice(story)

    duration = audio_duration(VOICE_FILE)

    create_subtitles(story, duration)

    create_music(duration)

    create_video(images, duration)

    validate_video()

    # Upload only after every previous step succeeds.
    upload_video(story)

    print("ALL TASKS COMPLETED SUCCESSFULLY.")


if __name__ == "__main__":
    main()

import os
import re
import json
import random
import hashlib
import subprocess
import asyncio
import requests
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

import edge_tts
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


# ==========================================
# SETTINGS
# ==========================================

OUTPUT = Path("output")
SCENES = OUTPUT / "scenes"
OUTPUT.mkdir(exist_ok=True)
SCENES.mkdir(exist_ok=True)

VIDEO_FILE = OUTPUT / "nature_short.mp4"
VOICE_FILE = OUTPUT / "voice.mp3"
MUSIC_FILE = OUTPUT / "music.mp3"
SUBTITLE_FILE = OUTPUT / "subtitles.srt"

VOICE = "ur-PK-UzmaNeural"

WIDTH = 1080
HEIGHT = 1920

IMAGE_MODEL = "https://image.pollinations.ai/prompt/"

# ==========================================
# STORIES
# ==========================================

TOPICS = [
    {
        "title": "The Door Hidden in the Forest",
        "category": "Mystery",
        "english": [
            "Deep inside a forgotten forest, something strange was discovered.",
            "A mysterious wooden door stood between two ancient trees.",
            "Nobody knew who built it or what was hidden behind it.",
            "One explorer slowly reached for its rusty handle.",
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
            "cinematic mysterious deep dark forest, ancient giant trees, thick fog, photorealistic",
            "old mysterious wooden door between two enormous forest trees, cinematic horror atmosphere",
            "close view of ancient wooden door covered in moss, mysterious symbols, realistic photography",
            "lonely explorer wearing dark outdoor jacket approaching an old forest door, cinematic wide shot",
            "cold mist flowing from a half open mysterious door in a dark forest, dramatic lighting",
            "ancient wooden door opening by itself in a foggy forest, mysterious cinematic scene"
        ]
    },
    {
        "title": "What Happens Inside a Black Hole?",
        "category": "Science",
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
            "giant black hole in deep space, glowing accretion disk, realistic astrophotography",
            "scientific visualization of black hole surrounded by stars, cinematic space",
            "powerful black hole bending light and stars, dramatic realistic space scene",
            "spaceship approaching event horizon of enormous black hole, cinematic science fiction",
            "mysterious glowing center of black hole, scientific visualization, deep space",
            "black hole surrounded by cosmic dust and distant galaxies, breathtaking realistic scene"
        ]
    },
    {
        "title": "Lost in the World's Wildest Jungle",
        "category": "Adventure",
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
            "vast unexplored tropical jungle, towering trees, cinematic adventure photography",
            "sunlight rays barely entering dense rainforest, mysterious atmosphere",
            "thick jungle trail with strange animal eyes in distant shadows, cinematic",
            "abandoned narrow path through dense tropical forest, realistic adventure scene",
            "ancient stone ruins covered in giant tree roots and moss, cinematic discovery",
            "dark entrance of ancient jungle ruins with mysterious movement inside, suspenseful"
        ]
    },
    {
        "title": "The Dog That Waited Every Day",
        "category": "Emotional",
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
            "lonely golden brown dog sitting outside old railway station, emotional cinematic photography",
            "loyal dog looking toward railway platform, soft morning light, realistic",
            "people walking past lonely dog at railway station, emotional storytelling scene",
            "same lonely dog waiting on station platform during changing seasons, cinematic",
            "old photograph lying beside a loyal dog on railway station floor, close up",
            "emotional cinematic railway station scene, lonely dog beside old photograph, warm light"
        ]
    },
    {
        "title": "The Amazing Intelligence of Octopuses",
        "category": "Science",
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
            "realistic giant octopus swimming in deep blue ocean, underwater cinematic photography",
            "octopus close up showing detailed eyes and tentacles, underwater documentary",
            "octopus opening a glass container underwater, realistic nature documentary",
            "octopus using a shell as a tool on ocean floor, photorealistic",
            "octopus changing colors and blending into coral reef, underwater macro photography",
            "beautiful intelligent octopus in mysterious deep ocean, cinematic documentary"
        ]
    },
    {
        "title": "The Mountain Nobody Could Climb",
        "category": "Adventure",
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
            "enormous remote snowy mountain peak above clouds, cinematic adventure photography",
            "steep dangerous icy mountain cliffs during storm, realistic landscape",
            "abandoned mountaineering equipment on snowy mountain trail, dramatic scene",
            "lone climber in red jacket climbing steep snowy mountain, cinematic wide shot",
            "mountaineer reaching high snowy ridge above clouds, realistic photography",
            "breathtaking sunrise over Himalayan mountain peaks above clouds, cinematic"
        ]
    }
]


# ==========================================
# UTILITIES
# ==========================================

def run_command(command):
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-3000:])
    return result


def get_font(size):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def clean_old_scenes():
    for file in SCENES.glob("*"):
        if file.is_file():
            file.unlink()


# ==========================================
# STORY SELECTION
# ==========================================

def select_story():
    run_id = os.getenv("GITHUB_RUN_ID", "")
    attempt = os.getenv("GITHUB_RUN_ATTEMPT", "")

    if run_id:
        seed_text = run_id + attempt
        seed = int(hashlib.sha256(seed_text.encode()).hexdigest(), 16)
        rng = random.Random(seed)
        return rng.choice(TOPICS)

    return random.choice(TOPICS)


# ==========================================
# AI IMAGE GENERATION
# ==========================================

def make_ai_image(prompt, index):
    seed = random.randint(100000, 999999999)

    full_prompt = (
        prompt
        + ", vertical 9:16 composition, highly detailed, "
        "photorealistic cinematic film still, no text, no watermark"
    )

    url = IMAGE_MODEL + requests.utils.quote(full_prompt)

    params = {
        "width": WIDTH,
        "height": HEIGHT,
        "seed": seed,
        "nologo": "true"
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=120,
            headers={"User-Agent": "NatureShortsBot/1.0"}
        )

        response.raise_for_status()

        image_path = SCENES / f"scene_{index}.jpg"
        image_path.write_bytes(response.content)

        with Image.open(image_path) as img:
            img.verify()

        return image_path

    except Exception as error:
        print(f"Image generation failed for scene {index}: {error}")
        return make_fallback_image(index, prompt)


def make_fallback_image(index, prompt):
    image = Image.new(
        "RGB",
        (WIDTH, HEIGHT),
        (10 + index * 3, 20 + index * 4, 35 + index * 5)
    )

    draw = ImageDraw.Draw(image)

    for y in range(HEIGHT):
        shade = int(20 + (y / HEIGHT) * 45)
        draw.line(
            (0, y, WIDTH, y),
            fill=(5, shade, min(90, shade + 25))
        )

    title = f"SCENE {index}"
    font = get_font(65)

    draw.text(
        (WIDTH // 2, HEIGHT // 2),
        title,
        font=font,
        fill=(255, 255, 255),
        anchor="mm"
    )

    image = image.filter(ImageFilter.GaussianBlur(1))

    path = SCENES / f"scene_{index}.jpg"
    image.save(path, quality=90)

    return path


def get_scene_images(story):
    images = []

    for index, prompt in enumerate(story["prompts"], start=1):
        print(f"Generating scene {index}/6...")
        images.append(make_ai_image(prompt, index))

    return images


# ==========================================
# URDU VOICE
# ==========================================

async def generate_voice(text):
    communicate = edge_tts.Communicate(
        text=text,
        voice=VOICE,
        rate="+15%",
        volume="+0%"
    )
    await communicate.save(str(VOICE_FILE))


def create_voice(story):
    narration = " ".join(story["urdu"])

    print("Generating Urdu voice-over...")

    asyncio.run(generate_voice(narration))

    return narration


# ==========================================
# SUBTITLES
# ==========================================

def seconds_to_srt(seconds):
    milliseconds = int((seconds % 1) * 1000)
    total = int(seconds)

    hours = total // 3600
    minutes = (total % 3600) // 60
    secs = total % 60

    return (
        f"{hours:02}:{minutes:02}:{secs:02},"
        f"{milliseconds:03}"
    )


def get_audio_duration(path):
    result = run_command([
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(path)
    ])

    return float(result.stdout.strip())


def create_subtitles(story, total_duration):
    segment_duration = total_duration / len(story["english"])

    with open(SUBTITLE_FILE, "w", encoding="utf-8") as file:
        for index, sentence in enumerate(story["english"]):
            start = index * segment_duration
            end = (index + 1) * segment_duration

            file.write(
                f"{index + 1}\n"
                f"{seconds_to_srt(start)} --> "
                f"{seconds_to_srt(end)}\n"
                f"{sentence}\n\n"
            )


# ==========================================
# BACKGROUND MUSIC
# ==========================================

def create_music(duration):
    print("Creating ambient background music...")

    run_command([
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "sine=frequency=110:duration=" + str(duration),
        "-af", "volume=0.10,lowpass=f=400,afade=t=in:st=0:d=2",
        "-c:a", "libmp3lame",
        "-q:a", "6",
        str(MUSIC_FILE)
    ])


# ==========================================
# VIDEO CREATION
# ==========================================

def create_video(images, duration):
    print("Creating six-scene video...")

    scene_duration = duration / len(images)
    clips = []

    for index, image in enumerate(images):
        clip = SCENES / f"clip_{index + 1}.mp4"

        frames = max(1, int(scene_duration * 25))

        zoom_filter = (
            f"scale=1200:2134,"
            f"crop=1080:1920,"
            f"zoompan=z='min(zoom+0.0005,1.08)':"
            f"x='iw/2-(iw/zoom/2)':"
            f"y='ih/2-(ih/zoom/2)':"
            f"d={frames}:s=1080x1920:fps=25,"
            f"setsar=1"
        )

        run_command([
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(image),
            "-vf", zoom_filter,
            "-t", str(scene_duration),
            "-r", "25",
            "-an",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-pix_fmt", "yuv420p",
            str(clip)
        ])

        clips.append(clip)

    concat_file = OUTPUT / "concat.txt"

    with open(concat_file, "w", encoding="utf-8") as file:
        for clip in clips:
            safe_path = str(clip.resolve()).replace("'", "'\\''")
            file.write(f"file '{safe_path}'\n")

    joined = OUTPUT / "joined.mp4"

    run_command([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_file),
        "-c", "copy",
        str(joined)
    ])

    print("Adding English subtitles and Urdu narration...")

    subtitle_path = str(SUBTITLE_FILE.resolve())
    subtitle_path = subtitle_path.replace("\\", "/")
    subtitle_path = subtitle_path.replace(":", "\\:")

    filter_text = (
        f"subtitles='{subtitle_path}':"
        "force_style='FontName=DejaVu Sans,"
        "FontSize=17,PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,Outline=2,"
        "Shadow=1,Alignment=2,MarginV=170'"
    )

    run_command([
        "ffmpeg", "-y",
        "-i", str(joined),
        "-i", str(VOICE_FILE),
        "-i", str(MUSIC_FILE),
        "-filter_complex",
        (
            f"[0:v]{filter_text}[v];"
            "[1:a]volume=1.0[voice];"
            "[2:a]volume=0.12[music];"
            "[voice][music]amix=inputs=2:duration=first[a]"
        ),
        "-map", "[v]",
        "-map", "[a]",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        "-movflags", "+faststart",
        str(VIDEO_FILE)
    ])


# ==========================================
# YOUTUBE UPLOAD
# ==========================================

def upload_to_youtube(story):
    client_json = os.getenv("YOUTUBE_CLIENT_JSON")
    refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN")

    if not client_json or not refresh_token:
        raise RuntimeError(
            "Missing YOUTUBE_CLIENT_JSON or YOUTUBE_REFRESH_TOKEN secret."
        )

    client_data = json.loads(client_json)

    app_data = client_data.get("installed") or client_data.get("web")

    if not app_data:
        raise RuntimeError("Invalid YouTube OAuth client JSON.")

    credentials = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri=app_data["token_uri"],
        client_id=app_data["client_id"],
        client_secret=app_data["client_secret"],
        scopes=["https://www.googleapis.com/auth/youtube.upload"]
    )

    youtube = build(
        "youtube",
        "v3",
        credentials=credentials
    )

    description = (
        f"{story['title']}\n\n"
        "A short story from Nature Shorts.\n"
        "#Nature #Mystery #Adventure #Shorts"
    )

    body = {
        "snippet": {
            "title": story["title"][:100],
            "description": description,
            "tags": [
                "nature",
                "mystery",
                "adventure",
                "science",
                "shorts"
            ],
            "categoryId": "22"
        },
        "status": {
            "privacyStatus": os.getenv(
                "YOUTUBE_PRIVACY_STATUS",
                "private"
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

    print("Upload successful!")
    print("Video ID:", response["id"])


# ==========================================
# MAIN
# ==========================================

def main():
    print("================================")
    print("     NATURE SHORTS AUTOMATION")
    print("================================")

    clean_old_scenes()

    story = select_story()

    print("Selected story:", story["title"])

    images = get_scene_images(story)

    create_voice(story)

    duration = get_audio_duration(VOICE_FILE)

    print("Voice duration:", duration, "seconds")

    create_subtitles(story, duration)

    create_music(duration)

    create_video(images, duration)

    print("Video created:", VIDEO_FILE)

    upload_to_youtube(story)

    print("ALL TASKS COMPLETED!")


if __name__ == "__main__":
    main()

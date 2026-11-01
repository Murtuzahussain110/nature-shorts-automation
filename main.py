import os
import json
import math
import wave
import struct
import asyncio
import datetime
import subprocess
from pathlib import Path
from urllib.parse import quote

import requests
import edge_tts
from PIL import Image, ImageDraw, ImageFont
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ==========================================
# SETTINGS
# ==========================================

OUT = Path("output")
SCENES = OUT / "scenes"
OUT.mkdir(exist_ok=True)
SCENES.mkdir(exist_ok=True)

WIDTH = 1080
HEIGHT = 1920
FPS = 30

# Urdu female voice
VOICE = "ur-PK-UzmaNeural"

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload"
]

# ==========================================
# CONTENT LIBRARY
# Urdu narration + English subtitles
# ==========================================

TOPICS = [

    {
        "category": "Story",
        "title": "The Door Hidden in the Forest",
        "description": "A mysterious fictional adventure story.",
        "sentences": [
            "A young explorer found a strange door deep inside an abandoned forest.",
            "There were no walls around it, only an old wooden door standing between giant trees.",
            "When he slowly opened it, a golden light appeared from the other side.",
            "He stepped closer and heard someone whisper his name.",
            "But when he turned around, the entire forest had disappeared.",
            "Where do you think that mysterious door led?"
        ],
        "urdu": [
            "ایک نوجوان مہم جو کو ایک ویران جنگل کے اندر ایک عجیب دروازہ ملا۔",
            "اس کے اردگرد کوئی دیوار نہیں تھی، صرف ایک پرانا لکڑی کا دروازہ بڑے درختوں کے درمیان کھڑا تھا۔",
            "جیسے ہی اس نے آہستہ سے دروازہ کھولا، دوسری طرف سے سنہری روشنی آنے لگی۔",
            "وہ قریب گیا تو اسے کسی کی آواز سنائی دی جو اس کا نام پکار رہی تھی۔",
            "لیکن جب اس نے پیچھے مڑ کر دیکھا تو پورا جنگل غائب ہو چکا تھا۔",
            "آپ کے خیال میں وہ پراسرار دروازہ کہاں جاتا تھا؟"
        ],
        "prompts": [
            "cinematic photorealistic 3D film scene, young male explorer wearing a dark green adventure jacket discovering an ancient wooden door standing alone in a dense mysterious forest, dramatic fog, realistic human proportions, vertical composition, no text",
            "same young male explorer examining an ancient wooden door surrounded by enormous moss covered trees, cinematic forest atmosphere, realistic 3D movie quality, vertical composition, no text",
            "close view of the same ancient wooden door slowly opening with mysterious golden light pouring through, explorer standing nearby, cinematic realistic 3D film lighting, vertical composition, no text",
            "same young explorer looking frightened as mysterious golden light illuminates his face, dark forest, cinematic close-up, realistic 3D movie quality, vertical composition, no text",
            "same explorer standing in a strange empty glowing landscape after the forest has vanished, mysterious atmosphere, cinematic photorealistic 3D film, vertical composition, no text",
            "mysterious ancient wooden door standing alone in a surreal golden landscape, dramatic cinematic ending, realistic 3D film scene, vertical composition, no text"
        ]
    },

    {
        "category": "Research",
        "title": "What Happens Inside a Black Hole?",
        "description": "A short educational science video about black holes.",
        "sentences": [
            "Imagine falling toward one of the strangest objects in the universe.",
            "A black hole has gravity so powerful that even light cannot escape from inside its event horizon.",
            "As you approach, gravity can stretch objects through a process scientists call spaghettification.",
            "We cannot see inside the event horizon because light cannot travel back out.",
            "Scientists study black holes by observing how they affect nearby stars and gas.",
            "The universe still holds mysteries we are only beginning to understand."
        ],
        "urdu": [
            "ذرا تصور کریں کہ آپ کائنات کی ایک عجیب ترین چیز کی طرف گر رہے ہیں۔",
            "بلیک ہول کی کشش ثقل اتنی طاقتور ہوتی ہے کہ اس کے ایونٹ ہورائزن سے روشنی بھی باہر نہیں نکل سکتی۔",
            "اس کے قریب پہنچنے پر کشش ثقل چیزوں کو لمبا کھینچ سکتی ہے، اس عمل کو اسپگیٹیفیکیشن کہتے ہیں۔",
            "ہم ایونٹ ہورائزن کے اندر نہیں دیکھ سکتے کیونکہ روشنی وہاں سے واپس نہیں آ سکتی۔",
            "سائنس دان قریبی ستاروں اور گیس پر بلیک ہول کے اثرات دیکھ کر اس کا مطالعہ کرتے ہیں۔",
            "کائنات میں اب بھی ایسے راز موجود ہیں جنہیں ہم سمجھنے کی کوشش کر رہے ہیں۔"
        ],
        "prompts": [
            "cinematic scientifically inspired view of a gigantic black hole in deep space with glowing accretion disk, stars and nebula, photorealistic space documentary, vertical composition, no text",
            "scientifically inspired black hole with bright glowing accretion disk and distorted stars caused by gravitational lensing, realistic astronomy visualization, vertical composition, no text",
            "scientific visualization of a spacecraft approaching a black hole with curved light and dramatic gravitational lensing, cinematic realistic space documentary, vertical composition, no text",
            "dark black hole event horizon surrounded by glowing orange and blue accretion disk, detailed realistic space visualization, vertical composition, no text",
            "astronomical observatory telescope looking toward a star field, scientists studying distant galaxies, cinematic photorealistic documentary, vertical composition, no text",
            "beautiful deep space scene with distant galaxies, colorful nebula and stars, breathtaking cinematic science documentary, vertical composition, no text"
        ]
    },

    {
        "category": "Adventure",
        "title": "Lost in the World's Wildest Jungle",
        "description": "A fictional cinematic survival adventure.",
        "sentences": [
            "Imagine waking up alone in a jungle you have never seen before.",
            "The trees are enormous, the river is rushing, and strange sounds surround you.",
            "You find an old wooden bridge, but it is hanging over a deep waterfall.",
            "Suddenly, you notice fresh footprints leading toward a hidden cave.",
            "You enter the cave and discover a mysterious abandoned camp.",
            "Would you stay or keep exploring?"
        ],
        "urdu": [
            "تصور کریں کہ آپ ایک ایسے جنگل میں اکیلے جاگتے ہیں جسے آپ نے پہلے کبھی نہیں دیکھا۔",
            "درخت بہت بڑے ہیں، دریا تیزی سے بہہ رہا ہے اور ہر طرف عجیب آوازیں سنائی دے رہی ہیں۔",
            "آپ کو لکڑی کا ایک پرانا پل ملتا ہے جو ایک گہری آبشار کے اوپر لٹک رہا ہے۔",
            "اچانک آپ کو تازہ قدموں کے نشان نظر آتے ہیں جو ایک چھپی ہوئی غار کی طرف جا رہے ہیں۔",
            "آپ غار میں داخل ہوتے ہیں اور وہاں ایک پراسرار ویران کیمپ دیکھتے ہیں۔",
            "کیا آپ وہاں رکیں گے یا آگے تلاش جاری رکھیں گے؟"
        ],
        "prompts": [
            "cinematic photorealistic 3D adventure film scene, lone young male explorer in outdoor survival clothing waking up in a vast tropical jungle, giant trees and morning mist, vertical composition, no text",
            "same young explorer standing beside a powerful jungle river surrounded by giant tropical trees, dramatic natural lighting, realistic adventure movie, vertical composition, no text",
            "same explorer carefully approaching an old wooden rope bridge above a huge jungle waterfall, cinematic wide perspective, photorealistic 3D movie, vertical composition, no text",
            "close view of muddy footprints leading through dense jungle toward a mysterious dark cave, explorer visible in background, cinematic realism, vertical composition, no text",
            "same explorer entering a mysterious cave with an abandoned old camping site and scattered equipment, dramatic flashlight lighting, realistic 3D adventure film, vertical composition, no text",
            "mysterious abandoned jungle camp inside a cave illuminated by a beam of sunlight, cinematic adventure movie ending, photorealistic, vertical composition, no text"
        ]
    },

    {
        "category": "Story",
        "title": "The Dog That Waited Every Day",
        "description": "A fictional emotional animal story.",
        "sentences": [
            "Every morning, a little dog waited beside an old railway station.",
            "People passed by, but the dog never moved from its favorite spot.",
            "One rainy evening, an elderly man recognized the dog.",
            "It was the same dog he had rescued many years ago.",
            "The man knelt down, and the dog ran into his arms.",
            "Sometimes, loyalty remembers what time cannot erase."
        ],
        "urdu": [
            "ہر صبح ایک چھوٹا سا کتا پرانے ریلوے اسٹیشن کے پاس انتظار کرتا تھا۔",
            "لوگ وہاں سے گزرتے رہتے، لیکن کتا اپنی پسندیدہ جگہ سے نہیں ہٹتا تھا۔",
            "ایک بارش بھری شام ایک بزرگ آدمی نے اس کتے کو پہچان لیا۔",
            "یہ وہی کتا تھا جسے اس نے کئی سال پہلے بچایا تھا۔",
            "آدمی گھٹنوں کے بل بیٹھا اور کتا دوڑ کر اس کی بانہوں میں آ گیا۔",
            "کبھی کبھی وفاداری وہ یاد رکھتی ہے جسے وقت بھی نہیں مٹا سکتا۔"
        ],
        "prompts": [
            "cinematic photorealistic 3D animated film scene, small golden brown dog waiting beside an old quiet railway station, emotional atmosphere, soft morning light, vertical composition, no text",
            "same small golden brown dog sitting alone on railway station platform as commuters walk past, emotional cinematic composition, realistic 3D movie, vertical composition, no text",
            "elderly man in a brown coat standing in gentle rain at an old railway station noticing the same small golden brown dog, cinematic emotional film scene, vertical composition, no text",
            "close-up of elderly man's emotional face recognizing the dog, rainy station background, photorealistic 3D animated movie, vertical composition, no text",
            "same elderly man kneeling down and hugging the happy golden brown dog on the railway platform, warm emotional cinematic lighting, vertical composition, no text",
            "elderly man walking home with the golden brown dog beside him at sunset, beautiful emotional movie ending, realistic 3D animation, vertical composition, no text"
        ]
    },

    {
        "category": "Research",
        "title": "The Amazing Intelligence of Octopuses",
        "description": "An educational wildlife research short.",
        "sentences": [
            "An octopus has three hearts and blue blood.",
            "Two hearts pump blood toward the gills, while the third sends it to the rest of the body.",
            "Its blood is blue because it uses a copper-rich protein called hemocyanin.",
            "Octopuses can solve puzzles and squeeze through surprisingly tiny openings.",
            "They are among the most fascinating animals living in our oceans.",
            "What ocean creature should we explore next?"
        ],
        "urdu": [
            "آکٹوپس کے تین دل ہوتے ہیں اور اس کا خون نیلا ہوتا ہے۔",
            "دو دل خون کو گلپھڑوں کی طرف بھیجتے ہیں جبکہ تیسرا دل باقی جسم کو خون پہنچاتا ہے۔",
            "اس کا خون نیلا ہوتا ہے کیونکہ اس میں تانبے والا ایک پروٹین موجود ہوتا ہے جسے ہیموسائنن کہتے ہیں۔",
            "آکٹوپس مشکل پہیلیاں حل کر سکتا ہے اور بہت چھوٹی جگہوں سے بھی گزر سکتا ہے۔",
            "یہ سمندر میں رہنے والے سب سے دلچسپ جانوروں میں سے ایک ہے۔",
            "آپ اگلی بار کس سمندری جانور کے بارے میں جاننا چاہیں گے؟"
        ],
        "prompts": [
            "photorealistic underwater wildlife documentary, intelligent common octopus resting on a rock in clear blue ocean, detailed skin texture, vertical composition, no text",
            "scientifically inspired realistic octopus underwater with detailed anatomy visualization, blue ocean background, cinematic wildlife documentary, vertical composition, no text",
            "macro close-up of octopus skin and tentacles underwater, beautiful natural blue light, photorealistic marine documentary, vertical composition, no text",
            "octopus exploring a glass puzzle container on ocean research table, realistic scientific documentary scene, vertical composition, no text",
            "majestic octopus swimming through a colorful coral reef, realistic underwater wildlife photography, vertical composition, no text",
            "beautiful deep blue underwater reef with an octopus disappearing into the ocean, cinematic documentary ending, vertical composition, no text"
        ]
    },

    {
        "category": "Adventure",
        "title": "The Mountain Nobody Could Climb",
        "description": "A fictional high-altitude adventure.",
        "sentences": [
            "A mountain explorer decided to climb a peak nobody in his village had reached.",
            "The trail became steeper as clouds covered the rocky mountainside.",
            "A sudden snowstorm forced him to search for shelter.",
            "Inside a small cave, he discovered an old climbing flag.",
            "At sunrise, he finally reached the summit and looked across the endless mountains.",
            "Sometimes the greatest achievement is refusing to give up."
        ],
        "urdu": [
            "ایک پہاڑی مہم جو نے اس چوٹی کو سر کرنے کا فیصلہ کیا جہاں اس کے گاؤں کا کوئی شخص نہیں پہنچا تھا۔",
            "جیسے جیسے بادل پہاڑ کو ڈھانپنے لگے، راستہ مزید مشکل ہوتا گیا۔",
            "اچانک برفانی طوفان آیا اور اسے پناہ تلاش کرنا پڑی۔",
            "ایک چھوٹی غار میں اسے چڑھائی کا ایک پرانا جھنڈا ملا۔",
            "سورج نکلتے ہی وہ آخرکار چوٹی پر پہنچ گیا اور دور تک پھیلے پہاڑوں کو دیکھنے لگا۔",
            "کبھی کبھی سب سے بڑی کامیابی ہمت نہ ہارنا ہوتی ہے۔"
        ],
        "prompts": [
            "cinematic photorealistic 3D adventure movie, brave young male mountain explorer wearing red winter jacket beginning a climb toward an enormous snowy Himalayan peak, vertical composition, no text",
            "same explorer climbing a steep rocky Himalayan mountain trail as dramatic clouds roll over the mountains, realistic cinematic adventure film, vertical composition, no text",
            "same explorer caught in a powerful snowstorm on a high mountain, searching for shelter, dramatic realistic 3D movie scene, vertical composition, no text",
            "same explorer inside a small rocky mountain cave discovering an old faded climbing flag, warm lantern light, cinematic realistic film, vertical composition, no text",
            "same explorer standing on a snowy Himalayan summit at sunrise overlooking endless mountain ranges, breathtaking cinematic landscape, vertical composition, no text",
            "wide cinematic view of the mountain summit glowing at sunrise, explorer standing proudly in the distance, photorealistic adventure movie ending, vertical composition, no text"
        ]
    }
]


# ==========================================
# UTILITIES
# ==========================================

def run_ffmpeg(args):
    subprocess.run(
        ["ffmpeg", "-y"] + [str(x) for x in args],
        check=True
    )


def media_duration(path):
    result = subprocess.check_output([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(path)
    ], text=True).strip()

    return float(result)


def verify_image(path):
    with Image.open(path) as image:
        image.verify()


# ==========================================
# AI IMAGE GENERATION
# ==========================================

def make_ai_image(prompt, path, seed):
    url = (
        "https://image.pollinations.ai/prompt/"
        + quote(prompt, safe="")
    )

    response = requests.get(
        url,
        params={
            "width": 768,
            "height": 1365,
            "seed": seed,
            "nologo": "true"
        },
        headers={
            "User-Agent": "NatureStoriesAutomation/1.0"
        },
        timeout=120
    )

    response.raise_for_status()

    if not response.headers.get(
        "content-type", ""
    ).startswith("image/"):
        raise RuntimeError(
            "AI service did not return an image"
        )

    path.write_bytes(response.content)
    verify_image(path)


def make_fallback_art(path, title, index):
    image = Image.new(
        "RGB",
        (WIDTH, HEIGHT),
        (5, 15 + index * 10, 35 + index * 15)
    )

    draw = ImageDraw.Draw(image)

    for y in range(HEIGHT):
        shade = int(20 + 100 * y / HEIGHT)
        draw.line(
            (0, y, WIDTH, y),
            fill=(3, shade // 2, shade)
        )

    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            58
        )
    except Exception:
        font = ImageFont.load_default()

    draw.multiline_text(
        (75, 1250),
        title,
        font=font,
        fill="white",
        spacing=15
    )

    image.save(path, quality=92)


def get_scene_images(topic):
    images = []
    seed_base = int(
        datetime.date.today().strftime("%Y%m%d")
    )

    for index, prompt in enumerate(topic["prompts"]):
        path = SCENES / f"scene_{index + 1}.jpg"

        try:
            make_ai_image(
                prompt,
                path,
                seed_base + index * 37
            )
            print(
                "AI cinematic scene created:",
                index + 1
            )

        except Exception as error:
            print("AI image failed:", error)
            make_fallback_art(
                path,
                topic["title"],
                index
            )

        images.append(path)

    return images


# ==========================================
# URDU FEMALE VOICE
# ==========================================

async def save_tts(text, path):
    voice = edge_tts.Communicate(
        text,
        VOICE,
        rate="+0%"
    )

    await voice.save(str(path))


def create_voice(sentences):
    clips = []
    clip_lengths = []

    for index, sentence in enumerate(sentences):
        clip = OUT / f"voice_{index + 1}.mp3"

        asyncio.run(
            save_tts(sentence, clip)
        )

        clips.append(clip)
        clip_lengths.append(
            media_duration(clip)
        )

        print("Urdu voice created:", index + 1)

    listing = OUT / "voice_list.txt"

    listing.write_text(
        "".join(
            f"file '{clip.resolve().as_posix()}'\n"
            for clip in clips
        ),
        encoding="utf-8"
    )

    combined = OUT / "voice.mp3"

    run_ffmpeg([
        "-f", "concat",
        "-safe", "0",
        "-i", listing,
        "-c:a", "libmp3lame",
        "-q:a", "3",
        combined
    ])

    return combined, clip_lengths


# ==========================================
# ENGLISH SUBTITLES
# ==========================================

def srt_time(seconds):
    milliseconds = int(round(seconds * 1000))

    hours, milliseconds = divmod(
        milliseconds, 3600000
    )
    minutes, milliseconds = divmod(
        milliseconds, 60000
    )
    secs, milliseconds = divmod(
        milliseconds, 1000
    )

    return (
        f"{hours:02}:{minutes:02}:"
        f"{secs:02},{milliseconds:03}"
    )


def create_captions(sentences, clip_lengths):
    rows = []
    current = 0.0

    for index, (sentence, seconds) in enumerate(
        zip(sentences, clip_lengths), 1
    ):
        rows.extend([
            str(index),
            f"{srt_time(current)} --> "
            f"{srt_time(current + seconds)}",
            sentence,
            ""
        ])

        current += seconds

    (OUT / "captions.srt").write_text(
        "\n".join(rows),
        encoding="utf-8"
    )

    return current


# ==========================================
# ORIGINAL BACKGROUND MUSIC
# ==========================================

def create_original_music(seconds):
    path = OUT / "music.wav"
    sample_rate = 44100

    total_samples = int(
        sample_rate * (seconds + 0.5)
    )

    with wave.open(str(path), "w") as audio:
        audio.setnchannels(2)
        audio.setsampwidth(2)
        audio.setframerate(sample_rate)

        frames = bytearray()

        for sample_index in range(total_samples):
            t = sample_index / sample_rate

            fade = min(
                1.0,
                t / 2.0,
                max(0.0, (seconds - t) / 2.0)
            )

            value = fade * (
                0.035 * math.sin(
                    2 * math.pi * 110 * t
                )
                + 0.022 * math.sin(
                    2 * math.pi * 164.81 * t
                )
                + 0.012 * math.sin(
                    2 * math.pi * 220 * t
                )
            )

            sample = int(
                max(-1.0, min(1.0, value)) * 32767
            )

            frames.extend(
                struct.pack("<hh", sample, sample)
            )

        audio.writeframes(frames)

    return path


# ==========================================
# CINEMATIC CAMERA MOVEMENT
# Still images with zoom movement
# ==========================================

def create_moving_scene(
    image_path,
    output_path,
    seconds,
    index
):
    if index % 2 == 0:
        zoom = "min(zoom+0.0007,1.14)"
    else:
        zoom = "max(1.0,1.14-on*0.0007)"

    video_filter = (
        "scale=1200:2134:"
        "force_original_aspect_ratio=increase,"
        "crop=1200:2134,"
        f"zoompan=z='{zoom}':"
        "x='iw/2-(iw/zoom/2)':"
        "y='ih/2-(ih/zoom/2)':"
        "d=1:"
        "s=1080x1920:"
        "fps=30,"
        "setsar=1,"
        "format=yuv420p"
    )

    run_ffmpeg([
        "-loop", "1",
        "-framerate", FPS,
        "-i", image_path,
        "-vf", video_filter,
        "-t", f"{seconds:.3f}",
        "-r", FPS,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "21",
        "-pix_fmt", "yuv420p",
        output_path
    ])


# ==========================================
# FINAL VIDEO
# ==========================================

def render_video(
    images,
    voice_path,
    clip_lengths,
    total_seconds
):
    scene_videos = []

    for index, image_path in enumerate(images):
        scene_video = (
            OUT / f"scene_video_{index + 1}.mp4"
        )

        create_moving_scene(
            image_path,
            scene_video,
            clip_lengths[index],
            index
        )

        scene_videos.append(scene_video)

        print("Scene video rendered:", index + 1)

    listing = OUT / "scene_video_list.txt"

    listing.write_text(
        "".join(
            f"file '{item.resolve().as_posix()}'\n"
            for item in scene_videos
        ),
        encoding="utf-8"
    )

    silent_video = OUT / "visual.mp4"

    run_ffmpeg([
        "-f", "concat",
        "-safe", "0",
        "-i", listing,
        "-c", "copy",
        silent_video
    ])

    music_path = create_original_music(
        total_seconds
    )

    subtitle_path = (
        OUT / "captions.srt"
    ).resolve().as_posix()

    subtitle_filter = (
        f"subtitles='{subtitle_path}':"
        "force_style='"
        "FontName=DejaVu Sans,"
        "FontSize=17,"
        "Bold=1,"
        "PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00101010,"
        "BorderStyle=1,"
        "Outline=3,"
        "Shadow=1,"
        "Alignment=2,"
        "MarginV=230'"
    )

    final_video = OUT / "short.mp4"

    run_ffmpeg([
        "-i", silent_video,
        "-i", voice_path,
        "-stream_loop", "-1",
        "-i", music_path,

        "-filter_complex",
        f"[0:v]{subtitle_filter}[v];"
        "[1:a]volume=1.0[voice];"
        "[2:a]volume=0.12[music];"
        "[voice][music]amix=inputs=2:"
        "duration=first:"
        "dropout_transition=2[a]",

        "-map", "[v]",
        "-map", "[a]",
        "-t", f"{total_seconds:.3f}",

        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "21",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        final_video
    ])

    return final_video


# ==========================================
# YOUTUBE CONNECTION
# ==========================================

def youtube_service():
    client_json = json.loads(
        os.environ["YOUTUBE_CLIENT_JSON"]
    )

    client = (
        client_json.get("installed")
        or client_json.get("web")
    )

    credentials = Credentials(
        token=None,
        refresh_token=os.environ[
            "YOUTUBE_REFRESH_TOKEN"
        ],
        token_uri=client["token_uri"],
        client_id=client["client_id"],
        client_secret=client["client_secret"],
        scopes=SCOPES
    )

    credentials.refresh(Request())

    return build(
        "youtube",
        "v3",
        credentials=credentials
    )


def upload_video(topic, video_path):
    youtube = youtube_service()

    body = {
        "snippet": {
            "title": topic["title"] + " #Shorts",
            "description": (
                topic["description"]
                + "\n\n"
                + "Discover stories, science, "
                + "adventure and amazing facts."
                + "\n\n"
                + "#Shorts #Stories #Science "
                + "#Adventure #Facts"
            ),
            "tags": [
                "shorts",
                "stories",
                "science",
                "adventure",
                "mystery",
                "facts",
                "nature",
                "documentary"
            ],
            "categoryId": "27"
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
        str(video_path),
        mimetype="video/mp4",
        chunksize=-1,
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
                "YouTube upload:",
                int(status.progress() * 100),
                "%"
            )

    print(
        "YouTube video uploaded. ID:",
        response.get("id")
    )


# ==========================================
# MAIN AUTOMATION
# ==========================================

def main():
    if (
        not os.getenv("YOUTUBE_CLIENT_JSON")
        or not os.getenv("YOUTUBE_REFRESH_TOKEN")
    ):
        raise RuntimeError(
            "YouTube GitHub secrets are missing."
        )

    day_number = datetime.date.today().toordinal()

    topic = TOPICS[
        day_number % len(TOPICS)
    ]

    print("Today's category:", topic["category"])
    print("Today's video:", topic["title"])

    if not (
        len(topic["sentences"])
        == len(topic["urdu"])
        == len(topic["prompts"])
    ):
        raise RuntimeError(
            "Topic sentences, Urdu narration and prompts do not match."
        )

    images = get_scene_images(topic)

    voice_path, clip_lengths = create_voice(
        topic["urdu"]
    )

    total_seconds = create_captions(
        topic["sentences"],
        clip_lengths
    )

    video_path = render_video(
        images,
        voice_path,
        clip_lengths,
        total_seconds
    )

    print("Video created:", video_path)
    print(
        "Duration:",
        round(media_duration(video_path), 1),
        "seconds"
    )

    upload_video(topic, video_path)


if __name__ == "__main__":
    main()
```

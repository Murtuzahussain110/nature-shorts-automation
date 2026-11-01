
import os
import json
import math
import random
import wave
import struct
import asyncio
import datetime
import subprocess
import textwrap
from pathlib import Path
from urllib.parse import quote

import requests
import edge_tts
from PIL import Image, ImageDraw, ImageFont
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

OUT = Path("output")
SCENES = OUT / "scenes"
OUT.mkdir(exist_ok=True)
SCENES.mkdir(exist_ok=True)

WIDTH = 1080
HEIGHT = 1920
FPS = 30
VOICE = "en-US-AriaNeural"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

TOPICS = [
    {
        "title": "Why the Ocean Looks Blue",
        "sentences": [
            "Have you ever wondered why the ocean looks blue?",
            "Water absorbs red light more strongly than blue, while sunlight and the sky also influence the colors we see.",
            "That is one reason deep ocean water often appears beautifully blue.",
            "Nature is full of science hiding in plain sight."
        ],
        "searches": [
            "deep blue ocean sunlight",
            "sun rays underwater ocean",
            "blue ocean waves aerial",
            "clear ocean coastline"
        ],
        "prompts": [
            "photorealistic deep blue ocean from above, sunlight glittering on waves, nature documentary, no text",
            "underwater view looking up at sun rays through clear blue seawater, photorealistic, no text",
            "dramatic close view of deep blue ocean waves sparkling in sunlight, no text",
            "aerial view of vivid blue ocean meeting rugged coastline, photorealistic, no text"
        ]
    },
    {
        "title": "How Waterfalls Are Formed",
        "sentences": [
            "A waterfall forms when flowing water moves over a sudden drop in the land.",
            "Over time, water and the rocks it carries can wear away softer layers of stone.",
            "This erosion can slowly move a waterfall upstream and shape the valley around it.",
            "A beautiful waterfall can tell a story millions of years in the making."
        ],
        "searches": [
            "powerful waterfall forest",
            "water flowing over rocky cliff",
            "waterfall mist green valley",
            "river gorge waterfall landscape"
        ],
        "prompts": [
            "majestic waterfall plunging into a forest pool, cinematic nature documentary, no text",
            "close-up rushing water flowing over layered dark rocks, photorealistic, no text",
            "mist rising from waterfall surrounded by lush green forest, cinematic, no text",
            "aerial river gorge and waterfall cutting through green valley, photorealistic, no text"
        ]
    },
    {
        "title": "The Secret Life of Trees",
        "sentences": [
            "Trees do much more than provide shade and beautiful scenery.",
            "Their leaves use sunlight to help turn water and carbon dioxide into sugars.",
            "Tree roots also help hold soil in place and support forest ecosystems.",
            "A forest is not just a group of trees. It is a living community."
        ],
        "searches": [
            "sunlight through green forest canopy",
            "green leaves sunlight close up",
            "tree roots forest soil",
            "misty dense forest aerial"
        ],
        "prompts": [
            "towering ancient forest with sunlight through green canopy, photorealistic, no text",
            "macro fresh green leaves glowing in sunlight, botanical photography, no text",
            "large tree roots gripping rich forest soil, nature documentary, no text",
            "aerial lush green forest fading into morning mist, photorealistic, no text"
        ]
    },
    {
        "title": "The Power of Glaciers",
        "sentences": [
            "Glaciers are enormous masses of ice that move slowly under their own weight.",
            "As they move, they scrape rock, carry sediment, and reshape mountain valleys.",
            "Glaciers also store a large amount of the world's fresh water.",
            "Their changing size is one sign scientists monitor in a warming climate."
        ],
        "searches": [
            "glacier mountain valley aerial",
            "blue glacier ice closeup",
            "glacier flowing between mountains",
            "snow glacier lake landscape"
        ],
        "prompts": [
            "enormous glacier winding through high mountain valley, photorealistic, no text",
            "detailed blue glacier ice with natural cracks, close-up, no text",
            "aerial glacier flowing between rugged snowy peaks, photorealistic, no text",
            "glacial lake beneath towering snow covered mountains, cinematic, no text"
        ]
    },
    {
        "title": "How Bees Help Nature",
        "sentences": [
            "Bees are tiny animals with an enormous role in many ecosystems.",
            "As they visit flowers for nectar, they transfer pollen between plants.",
            "This helps many plants produce fruits and seeds.",
            "Protecting pollinators helps protect the natural world around us."
        ],
        "searches": [
            "honey bee on flower macro",
            "bee collecting pollen close up",
            "wildflower meadow bees",
            "colorful flowers meadow nature"
        ],
        "prompts": [
            "macro honeybee visiting purple wildflower, realistic wildlife photography, no text",
            "close-up honeybee covered in golden pollen, macro photography, no text",
            "sunlit wildflower meadow alive with pollinators, nature documentary, no text",
            "colorful wildflowers across green meadow at sunrise, photorealistic, no text"
        ]
    }
]


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


def make_ai_image(prompt, path, seed):
    # Free AI image endpoint. Availability can change.
    url = "https://image.pollinations.ai/prompt/" + quote(
        prompt, safe=""
    )

    response = requests.get(
        url,
        params={
            "width": 768,
            "height": 1365,
            "seed": seed,
            "nologo": "true"
        },
        headers={"User-Agent": "NatureShortsAutomation/1.0"},
        timeout=100
    )

    response.raise_for_status()

    if not response.headers.get("content-type", "").startswith("image/"):
        raise RuntimeError("AI service did not return an image")

    path.write_bytes(response.content)
    verify_image(path)


def make_commons_image(search_term, path):
    # Backup image source. No API key required.
    api = "https://commons.wikimedia.org/w/api.php"
    headers = {
        "User-Agent": "NatureShortsAutomation/1.0"
    }

    response = requests.get(
        api,
        params={
            "action": "query",
            "generator": "search",
            "gsrsearch": "filetype:bitmap " + search_term,
            "gsrnamespace": 6,
            "gsrlimit": 10,
            "prop": "imageinfo",
            "iiprop": "url",
            "iiurlwidth": 1200,
            "format": "json"
        },
        headers=headers,
        timeout=35
    )

    response.raise_for_status()

    pages = list(
        response.json().get("query", {}).get("pages", {}).values()
    )
    random.shuffle(pages)

    for page in pages:
        info = page.get("imageinfo", [{}])[0]
        image_url = info.get("thumburl") or info.get("url")

        if not image_url:
            continue

        try:
            image_response = requests.get(
                image_url,
                headers=headers,
                timeout=40
            )
            image_response.raise_for_status()
            path.write_bytes(image_response.content)
            verify_image(path)
            return
        except Exception:
            continue

    raise RuntimeError("No backup image found")


def make_fallback_art(path, title, index):
    image = Image.new(
        "RGB",
        (WIDTH, HEIGHT),
        (5, 30 + index * 12, 65 + index * 10)
    )

    draw = ImageDraw.Draw(image)

    for y in range(HEIGHT):
        shade = int(25 + 100 * y / HEIGHT)
        draw.line(
            (0, y, WIDTH, y),
            fill=(4, shade // 2, shade)
        )

    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            58
        )
    except Exception:
        font = ImageFont.load_default()

    draw.multiline_text(
        (80, 1250),
        textwrap.fill(title, 22),
        font=font,
        fill="white",
        spacing=18
    )

    image.save(path, quality=92)


def get_scene_images(topic):
    images = []
    seed_base = int(datetime.date.today().strftime("%Y%m%d"))

    for index in range(4):
        path = SCENES / f"scene_{index + 1}.jpg"

        try:
            make_ai_image(
                topic["prompts"][index],
                path,
                seed_base + index * 31
            )
            print("AI image generated:", index + 1)

        except Exception as error:
            print("AI image unavailable:", error)

            try:
                make_commons_image(
                    topic["searches"][index],
                    path
                )
                print("Backup image downloaded:", index + 1)

            except Exception as backup_error:
                print("Backup unavailable:", backup_error)
                make_fallback_art(path, topic["title"], index)

        images.append(path)

    return images


async def save_tts(text, path):
    voice = edge_tts.Communicate(
        text,
        VOICE,
        rate="+3%"
    )

    await voice.save(str(path))


def create_voice(sentences):
    clips = []
    clip_lengths = []

    for index, sentence in enumerate(sentences):
        clip = OUT / f"voice_{index + 1}.mp3"

        asyncio.run(save_tts(sentence, clip))

        clips.append(clip)
        clip_lengths.append(media_duration(clip))

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


def srt_time(seconds):
    milliseconds = int(round(seconds * 1000))

    hours, milliseconds = divmod(milliseconds, 3600000)
    minutes, milliseconds = divmod(milliseconds, 60000)
    secs, milliseconds = divmod(milliseconds, 1000)

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
            f"{srt_time(current)} --> {srt_time(current + seconds)}",
            sentence,
            ""
        ])

        current += seconds

    (OUT / "captions.srt").write_text(
        "\n".join(rows),
        encoding="utf-8"
    )

    return current


def create_original_music(seconds):
    # Original synthesized ambient music.
    path = OUT / "music.wav"
    sample_rate = 44100
    total_samples = int(sample_rate * (seconds + 0.2))

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
                0.035 * math.sin(2 * math.pi * 110 * t)
                + 0.022 * math.sin(2 * math.pi * 164.81 * t)
                + 0.012 * math.sin(2 * math.pi * 220 * t)
            )

            sample = int(
                max(-1.0, min(1.0, value)) * 32767
            )

            frames.extend(struct.pack("<hh", sample, sample))

        audio.writeframes(frames)

    return path


def create_moving_scene(image_path, output_path, seconds, index):
    frame_count = max(1, math.ceil(seconds * FPS))

    if index % 2 == 0:
        zoom = "min(zoom+0.0007,1.13)"
    else:
        zoom = "max(1.0,1.13-on/10000)"

    video_filter = (
        "scale=1200:2134:force_original_aspect_ratio=increase,"
        "crop=1200:2134,"
        f"zoompan=z='{zoom}':d={frame_count}:"
        f"s=1080x1920:fps={FPS},"
        "setsar=1,format=yuv420p"
    )

    run_ffmpeg([
        "-loop", "1",
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


def render_video(images, voice_path, total_seconds):
    scene_seconds = total_seconds / len(images)
    scene_videos = []

    for index, image_path in enumerate(images):
        scene_video = OUT / f"scene_video_{index + 1}.mp4"

        create_moving_scene(
            image_path,
            scene_video,
            scene_seconds,
            index
        )

        scene_videos.append(scene_video)

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

    music_path = create_original_music(total_seconds)

    subtitle_path = (
        OUT / "captions.srt"
    ).resolve().as_posix()

    subtitle_filter = (
        f"subtitles='{subtitle_path}':"
        "force_style='FontName=DejaVu Sans,FontSize=17,"
        "Bold=1,PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00101010,BorderStyle=1,"
        "Outline=3,Shadow=1,Alignment=2,MarginV=230'"
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
        "[voice][music]amix=inputs=2:duration=first:"
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
        refresh_token=os.environ["YOUTUBE_REFRESH_TOKEN"],
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
            "title": topic["title"] + " | Nature & Science #Shorts",
            "description": (
                topic["sentences"][0]
                + "\n\nDaily nature, science and travel facts."
                + "\n\n#Shorts #Nature #Science #Travel"
            ),
            "tags": [
                "nature",
                "science",
                "travel",
                "wildlife",
                "facts",
                "shorts"
            ],
            "categoryId": "27"
        },
        "status": {
            "privacyStatus": os.getenv(
                "YOUTUBE_PRIVACY_STATUS", "private"
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

    print("YouTube video uploaded. ID:", response.get("id"))


def main():
    if (
        not os.getenv("YOUTUBE_CLIENT_JSON")
        or not os.getenv("YOUTUBE_REFRESH_TOKEN")
    ):
        raise RuntimeError("YouTube GitHub secrets are missing.")

    # Select a different topic each day.
    topic_index = (
        datetime.date.today().toordinal() % len(TOPICS)
    )

    topic = TOPICS[topic_index]

    print("Today's topic:", topic["title"])

    images = get_scene_images(topic)

    voice_path, clip_lengths = create_voice(
        topic["sentences"]
    )

    total_seconds = create_captions(
        topic["sentences"],
        clip_lengths
    )

    video_path = render_video(
        images,
        voice_path,
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
    

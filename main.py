import os
import json
import math
import random
import re
import html
import subprocess
import asyncio
import time
import requests
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

import edge_tts
from PIL import Image, ImageDraw, ImageFont

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


# ============================================================
# AYAN & COCO - ORIGINAL FAMILY-FRIENDLY URDU CARTOON SHORTS
# All artwork is drawn locally with Pillow; no paid image API.
# Visual format: layered 2.5D motion-comic, not full 3D animation.
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
SCENES_DIR = OUTPUT_DIR / "scenes"
AUDIO_DIR = OUTPUT_DIR / "audio"
for folder in (OUTPUT_DIR, SCENES_DIR, AUDIO_DIR):
    folder.mkdir(parents=True, exist_ok=True)

VIDEO_FILE = OUTPUT_DIR / "tom_jerry_short.mp4"
VOICE_FILE = OUTPUT_DIR / "voice.mp3"
SUBTITLE_FILE = OUTPUT_DIR / "subtitles.srt"
CONCAT_FILE = OUTPUT_DIR / "clips.txt"
AUDIO_CONCAT_FILE = OUTPUT_DIR / "audio.txt"

WIDTH, HEIGHT, FPS = 1080, 1920, 25
VOICE = os.getenv("URDU_VOICE", "ur-PK-UzmaNeural")
BLENDER_SCRIPT = BASE_DIR / "blender" / "render_scene.py"
PRIVACY_DEFAULT = "private"

# Original characters: keep their colors, clothes and proportions consistent.
AYAN = {"jacket": (22, 139, 157), "backpack": (190, 54, 48)}
COCO = {"fur": (232, 123, 47), "cream": (255, 225, 183)}

STORIES = [
    {"title":"Tom & Jerry Urdu Cartoon EP 01 | The Great Cheese Chase","tags":["Tom and Jerry","Urdu cartoon","funny cat and mouse","animated comedy","cartoon shorts"],"scenes":[
        ("جیری نے میز پر رکھا پنیر دیکھا اور چپکے سے اس کی طرف بڑھا۔","Jerry spots a delicious piece of cheese and sneaks closer."),
        ("ٹام نے اسے دیکھ لیا اور خاموشی سے جیری کے پیچھے چل پڑا۔","Tom notices Jerry and quietly follows him."),
        ("جیری نے پنیر اٹھایا تو ٹام نے اچانک چھلانگ لگا دی۔","Jerry grabs the cheese just as Tom makes a surprise leap."),
        ("جیری تیزی سے بھاگا اور ٹام اس کے پیچھے دوڑ پڑا۔","Jerry races away and Tom charges after him."),
        ("ٹام پھسل کر گھومتا ہوا نرم گھاس میں جا گرا۔","Tom slips, spins around and lands in the soft grass."),
        ("جیری پنیر لے کر ہنستا ہوا نکل گیا اور ٹام حیران رہ گیا۔","Jerry escapes with the cheese while Tom looks completely puzzled.")]},
    {"title":"Tom & Jerry Urdu Cartoon EP 02 | The Sneaky Mouse Trick","tags":["Tom and Jerry","Urdu funny cartoon","mouse trick","cat chase","3D animation"],"scenes":[
        ("جیری نے ٹام کے جوتے کے پاس ایک چھوٹا سا پنیر رکھ دیا۔","Jerry leaves a tiny cheese piece beside Tom's foot."),
        ("ٹام نے پنیر دیکھا اور خوشی سے اسے اٹھانے لگا۔","Tom spots the cheese and reaches for it."),
        ("جیری نے ڈوری کھینچی اور ٹام کا پاؤں اوپر اٹھ گیا۔","Jerry pulls a string and Tom's foot pops into the air."),
        ("ٹام توازن کھو بیٹھا اور ایک طرف لڑکھڑانے لگا۔","Tom loses his balance and wobbles from side to side."),
        ("جیری ہنستا ہوا باہر نکلا مگر خود بھی پنیر پر پھسل گیا۔","Jerry laughs, then slips on the cheese himself."),
        ("دونوں ایک دوسرے کو دیکھتے رہے اور پھر شرارت سے مسکرا دیے۔","They stare at each other, then share a mischievous grin.")]},
    {"title":"Tom & Jerry Urdu Cartoon EP 03 | The Runaway Cheese Cart","tags":["Tom and Jerry","Urdu cartoon story","funny chase","3D cartoon","kids entertainment"],"scenes":[
        ("ٹام نے پنیر کا بڑا ٹکڑا اٹھایا اور اسے چھپانے لگا۔","Tom picks up a giant piece of cheese and tries to hide it."),
        ("جیری نے پنیر کو پہیوں والی چھوٹی گاڑی پر رکھ دیا۔","Jerry places the cheese on a tiny toy cart."),
        ("گاڑی تیزی سے چل پڑی اور جیری اس کے پیچھے بھاگا۔","The cart rolls away and Jerry races after it."),
        ("ٹام بھی پنیر پکڑنے کے لیے پوری رفتار سے دوڑا۔","Tom sprints after the runaway cheese."),
        ("گاڑی ایک جھاڑی سے ٹکرائی اور پنیر ہوا میں اچھل گیا۔","The cart hits a bush and the cheese flies into the air."),
        ("پنیر دونوں کے درمیان گرا اور دونوں اسے پکڑنے کو لپکے۔","The cheese lands between them and both leap for it at once.")]},
    {"title":"Tom & Jerry Urdu Cartoon EP 04 | The Balloon Escape","tags":["Tom and Jerry","balloon prank","Urdu cartoon","funny animation","shorts"],"scenes":[
        ("جیری نے رنگین غبارہ دیکھا اور اسے اپنے ساتھ باندھ لیا۔","Jerry finds a bright balloon and ties it to himself."),
        ("ٹام نے جیری کو پکڑنے کے لیے دوڑ لگائی۔","Tom starts running to catch Jerry."),
        ("غبارہ جیری کو ہوا میں اوپر اٹھانے لگا۔","The balloon begins lifting Jerry into the air."),
        ("ٹام نے غبارے کی ڈوری پکڑ لی اور خود بھی اوپر کھنچ گیا۔","Tom grabs the string and gets pulled upward too."),
        ("دونوں درخت کی شاخ کے پاس گھومنے لگے۔","The two spin around beside a tree branch."),
        ("غبارہ پھٹ گیا اور دونوں نرم گھاس پر آ گرے۔","The balloon pops and both tumble onto the soft grass.")]},
    {"title":"Tom & Jerry Urdu Cartoon EP 05 | The Tiny Drum","tags":["Tom and Jerry","funny drum","Urdu animation","cartoon comedy","family shorts"],"scenes":[
        ("جیری کو ایک ننھا ڈھول ملا اور اس نے بجانا شروع کر دیا۔","Jerry finds a tiny drum and starts playing it."),
        ("آواز سن کر ٹام نیند سے جاگ گیا۔","The noise wakes Tom from his nap."),
        ("ٹام نے ڈھول پکڑنے کی کوشش کی مگر جیری بھاگ نکلا۔","Tom tries to grab the drum, but Jerry darts away."),
        ("جیری نے ڈھول بجایا تو ٹام کے قدم خود بخود ناچنے لگے۔","Jerry beats the drum and Tom's feet start dancing."),
        ("ٹام گھومتا رہا اور جھاڑی میں جا گرا۔","Tom spins around and tumbles into a bush."),
        ("جیری نے آخری تھاپ لگائی اور ٹام نے حیرت سے اسے دیکھا۔","Jerry plays one final beat as Tom stares in disbelief.")]},
    {"title":"Tom & Jerry Urdu Cartoon EP 06 | The Fishing Trouble","tags":["Tom and Jerry","fishing comedy","Urdu cartoon","cat mouse chase","animated shorts"],"scenes":[
        ("جیری نے تالاب کے کنارے مچھلی پکڑنے کی چھڑی دیکھی۔","Jerry spots a fishing rod beside the pond."),
        ("ٹام نے چھڑی اٹھائی اور جیری کو چارہ دکھایا۔","Tom picks it up and shows Jerry the bait."),
        ("جیری نے چارہ کھینچا تو ٹام کا توازن بگڑ گیا۔","Jerry tugs the bait and throws Tom off balance."),
        ("ٹام پانی میں گرنے سے بچنے کے لیے اچھلا۔","Tom jumps to avoid falling into the water."),
        ("چھڑی گھوم کر ٹام کے گرد لپٹ گئی۔","The fishing line spins around Tom."),
        ("جیری محفوظ جگہ بیٹھ کر ہنسنے لگا۔","Jerry sits safely nearby and laughs.")]},
    {"title":"Tom & Jerry Urdu Cartoon EP 07 | The Sleepy Cat","tags":["Tom and Jerry","sleepy cat","Urdu cartoon","funny mouse","3D comedy"],"scenes":[
        ("ٹام درخت کے نیچے مزے سے سو رہا تھا۔","Tom is sleeping peacefully under a tree."),
        ("جیری نے آہستہ سے ٹام کی دم کے پاس گھنٹی رکھ دی۔","Jerry quietly places a bell near Tom's tail."),
        ("ہوا چلی تو گھنٹی زور سے بجنے لگی۔","A breeze makes the bell ring loudly."),
        ("ٹام گھبرا کر اچھلا اور ادھر ادھر دیکھنے لگا۔","Tom jumps up in surprise and looks around."),
        ("جیری پتوں کے پیچھے چھپ کر ہنستا رہا۔","Jerry hides behind the leaves and giggles."),
        ("ٹام نے جیری کو دیکھ لیا اور دوبارہ دوڑ شروع ہو گئی۔","Tom spots Jerry and the chase begins again.")]},
    {"title":"Tom & Jerry Urdu Cartoon EP 08 | The Magic Hat","tags":["Tom and Jerry","magic hat prank","Urdu cartoon","funny animation","shorts"],"scenes":[
        ("جیری کو ایک بڑا جادوئی ٹوپی نما ڈبہ ملا۔","Jerry discovers a mysterious magician's hat."),
        ("ٹام نے اندر جھانکا تو جیری غائب ہو گیا۔","Tom peeks inside and Jerry disappears."),
        ("جیری ٹام کے پیچھے سے باہر نکلا اور اسے چونکا دیا۔","Jerry pops out behind Tom and gives him a fright."),
        ("ٹام نے ٹوپی اٹھائی تو اس میں سے رنگین گیندیں نکلیں۔","Tom lifts the hat and colorful balls spill out."),
        ("گیندیں ٹام کے پیروں کے نیچے آ گئیں اور وہ پھسل گیا۔","The balls roll under Tom's feet and he slips."),
        ("جیری نے ٹوپی پہن کر فاتحانہ انداز میں سلام کیا۔","Jerry wears the hat and gives a triumphant little bow.")]},
    {"title":"Tom & Jerry Urdu Cartoon EP 09 | The Garden Race","tags":["Tom and Jerry","garden race","Urdu cartoon","funny chase","family animation"],"scenes":[
        ("جیری نے باغ میں ایک سرخ کھلونا گاڑی دیکھی۔","Jerry finds a little red toy car in the garden."),
        ("وہ گاڑی میں بیٹھا اور تیزی سے آگے نکل گیا۔","He hops in and zooms away."),
        ("ٹام نے دوڑ کر گاڑی کا پیچھا شروع کر دیا۔","Tom runs after the speeding toy car."),
        ("گاڑی پھولوں کے گملوں کے درمیان سے گزری۔","The car zigzags between flower pots."),
        ("ٹام نے چھلانگ لگائی مگر خالی ٹوکری میں جا گرا۔","Tom leaps but lands inside an empty basket."),
        ("جیری گاڑی روک کر ٹام کو دیکھ کر ہنسنے لگا۔","Jerry stops the car and laughs at Tom.")]},
    {"title":"Tom & Jerry Urdu Cartoon EP 10 | The Picnic Surprise","tags":["Tom and Jerry","picnic surprise","Urdu cartoon","funny cat mouse","cartoon shorts"],"scenes":[
        ("جیری نے پکنک کی ٹوکری میں مزیدار سینڈوچ دیکھا۔","Jerry spots a tasty sandwich in a picnic basket."),
        ("ٹام نے ٹوکری اپنے پاس کھینچ لی۔","Tom pulls the basket closer to himself."),
        ("جیری نے چپکے سے ٹوکری کا ڈھکن کھولا۔","Jerry quietly lifts the basket lid."),
        ("ایک سیب لڑھکا اور ٹام اس کے پیچھے بھاگا۔","An apple rolls away and Tom chases it."),
        ("سیب ٹام کے سر سے ٹکرا کر واپس ٹوکری میں جا گرا۔","The apple bounces off Tom's head and lands back in the basket."),
        ("جیری نے سینڈوچ اٹھایا اور دونوں نے پکنک بانٹ لی۔","Jerry grabs the sandwich and the two end up sharing the picnic.")]}
]


def run_command(command):
    result = subprocess.run(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, errors="replace"
    )
    if result.returncode != 0:
        print("\nCOMMAND FAILED:", " ".join(map(str, command)), flush=True)
        if result.stdout:
            print("\n--- COMMAND STDOUT ---\n" + result.stdout[-12000:], flush=True)
        if result.stderr:
            print("\n--- COMMAND STDERR ---\n" + result.stderr[-20000:], flush=True)
        raise subprocess.CalledProcessError(
            result.returncode, command, output=result.stdout, stderr=result.stderr
        )
    return result


def get_duration(path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        check=True, capture_output=True, text=True
    )
    return float(result.stdout.strip())


def clean_text(value):
    value = html.unescape(str(value or ""))
    value = re.sub(r"<[^>]*>", " ", value)
    value = re.sub(r"\s+", " ", value)
    return "".join(ch for ch in value if ch.isprintable() and ch not in "\x00").strip()


def load_font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def gradient_background(scene_no):
    palettes = [
        ((18, 45, 76), (103, 169, 151)),
        ((22, 53, 87), (190, 139, 103)),
        ((24, 64, 89), (112, 174, 159)),
        ((38, 65, 91), (201, 158, 112)),
        ((25, 56, 83), (125, 166, 143)),
        ((17, 37, 70), (93, 117, 159))
    ]
    top, bottom = palettes[(scene_no - 1) % len(palettes)]
    im = Image.new("RGB", (WIDTH, HEIGHT))
    px = im.load()
    for y in range(HEIGHT):
        t = y / (HEIGHT - 1)
        # Smooth vertical color blend.
        t = t * t * (3 - 2 * t)
        c = tuple(int(top[i] * (1-t) + bottom[i] * t) for i in range(3))
        for x in range(WIDTH):
            px[x, y] = c
    return im


def draw_cloud(draw, x, y, scale=1.0):
    col = (235, 240, 232)
    draw.ellipse((x, y+25*scale, x+100*scale, y+80*scale), fill=col)
    draw.ellipse((x+35*scale, y, x+115*scale, y+80*scale), fill=col)
    draw.ellipse((x+75*scale, y+20*scale, x+155*scale, y+80*scale), fill=col)


def draw_landscape(draw, scene_no):
    # Distant mountain layers create depth for the slow camera movement.
    draw.polygon([(0, 790), (210, 440), (420, 790), (650, 390), (930, 800), (1080, 570), (1080, 1300), (0, 1300)], fill=(75, 111, 127))
    draw.polygon([(0, 1000), (260, 620), (520, 1030), (790, 610), (1080, 990), (1080, 1450), (0, 1450)], fill=(48, 91, 94))
    draw.polygon([(0, 1120), (260, 930), (540, 1150), (830, 900), (1080, 1120), (1080, 1920), (0, 1920)], fill=(34, 83, 70))
    draw_cloud(draw, 110, 260, 1.05)
    draw_cloud(draw, 720, 330, 0.72)
    # Sun/moon glow.
    sun_color = (255, 218, 148) if scene_no % 3 else (246, 231, 194)
    draw.ellipse((760, 180, 930, 350), fill=sun_color)
    # Forest trees at both edges.
    for x, h in [(35, 460), (160, 340), (900, 430), (1010, 540)]:
        base = 1330
        draw.rectangle((x+42, base-h//3, x+68, base+120), fill=(91, 58, 43))
        draw.polygon([(x, base-h), (x+55, base-h-100), (x+112, base-h)], fill=(28, 105, 77))
        draw.polygon([(x+5, base-h+115), (x+55, base-h+10), (x+108, base-h+115)], fill=(35, 125, 82))
    # Winding path / river changes by episode scene.
    if scene_no in (2, 4, 6):
        draw.polygon([(380, 1920), (570, 1920), (640, 1370), (480, 1190), (530, 1110), (720, 1920)], fill=(65, 139, 161))
        draw.line([(490, 1920), (540, 1470), (540, 1300)], fill=(166, 213, 211), width=12)
    else:
        draw.polygon([(0, 1920), (0, 1540), (340, 1380), (710, 1470), (1080, 1370), (1080, 1920)], fill=(91, 112, 76))
        draw.polygon([(420, 1920), (670, 1920), (610, 1510), (490, 1430)], fill=(167, 139, 103))


def draw_ayan(draw, x=360, y=1130, scale=1.0, pose=0):
    # Red backpack, teal jacket, navy trousers, friendly face.
    def box(coords): return tuple(int(v*scale) for v in coords)
    draw.ellipse((x-65*scale, y+450*scale, x+160*scale, y+500*scale), fill=(22, 53, 48))
    # backpack behind body
    draw.rounded_rectangle((x-58*scale, y+115*scale, x+75*scale, y+330*scale), radius=int(35*scale), fill=AYAN["backpack"], outline=(112, 39, 39), width=max(2,int(5*scale)))
    # legs
    draw.polygon([(x-25*scale,y+330*scale),(x+45*scale,y+330*scale),(x+35*scale,y+455*scale),(x-10*scale,y+455*scale)], fill=(37,54,82))
    draw.polygon([(x+38*scale,y+330*scale),(x+95*scale,y+330*scale),(x+115*scale,y+450*scale),(x+65*scale,y+455*scale)], fill=(37,54,82))
    draw.ellipse((x-22*scale,y+435*scale,x+45*scale,y+478*scale), fill=(48,42,39))
    draw.ellipse((x+62*scale,y+435*scale,x+135*scale,y+478*scale), fill=(48,42,39))
    # torso and arms
    draw.rounded_rectangle((x-48*scale,y+125*scale,x+100*scale,y+355*scale), radius=int(42*scale), fill=AYAN["jacket"], outline=(13,79,91), width=max(2,int(5*scale)))
    draw.line((x-35*scale,y+180*scale,x-78*scale,y+330*scale), fill=(199,139,101), width=max(18,int(34*scale)))
    arm_end = (x+150*scale,y+210*scale) if pose % 2 == 0 else (x+120*scale,y+335*scale)
    draw.line((x+78*scale,y+180*scale,arm_end[0],arm_end[1]), fill=(199,139,101), width=max(18,int(34*scale)))
    # neck and head
    draw.rectangle((x+4*scale,y+82*scale,x+52*scale,y+150*scale), fill=(190,128,92))
    draw.ellipse((x-22*scale,y-40*scale,x+105*scale,y+112*scale), fill=(204,145,108), outline=(112,72,55), width=max(2,int(4*scale)))
    draw.pieslice((x-28*scale,y-55*scale,x+110*scale,y+85*scale), 180, 360, fill=(48,37,34))
    draw.ellipse((x+66*scale,y+22*scale,x+78*scale,y+37*scale), fill=(28,32,35))
    draw.arc((x+40*scale,y+48*scale,x+85*scale,y+82*scale), 5, 150, fill=(90,48,43), width=max(2,int(3*scale)))


def draw_coco(draw, x=650, y=1390, scale=0.82, pose=0):
    # Same orange fox silhouette in every scene.
    draw.ellipse((x-65*scale,y+130*scale,x+115*scale,y+220*scale), fill=(27,55,45))
    # large fluffy tail
    draw.ellipse((x+65*scale,y+35*scale,x+235*scale,y+170*scale), fill=COCO["fur"], outline=(151,74,35), width=max(2,int(4*scale)))
    draw.ellipse((x+170*scale,y+90*scale,x+245*scale,y+155*scale), fill=COCO["cream"])
    # body
    draw.ellipse((x-70*scale,y+55*scale,x+115*scale,y+190*scale), fill=COCO["fur"], outline=(151,74,35), width=max(2,int(4*scale)))
    draw.ellipse((x-5*scale,y+90*scale,x+65*scale,y+175*scale), fill=COCO["cream"])
    # head and ears
    draw.polygon([(x-55*scale,y+65*scale),(x-48*scale,y-65*scale),(x+15*scale,y+25*scale)], fill=COCO["fur"], outline=(151,74,35))
    draw.polygon([(x+45*scale,y+25*scale),(x+110*scale,y-65*scale),(x+115*scale,y+75*scale)], fill=COCO["fur"], outline=(151,74,35))
    draw.polygon([(x-38*scale,y+25*scale),(x-43*scale,y-28*scale),(x-8*scale,y+22*scale)], fill=(246,174,151))
    draw.polygon([(x+68*scale,y+23*scale),(x+103*scale,y-28*scale),(x+94*scale,y+44*scale)], fill=(246,174,151))
    draw.ellipse((x-70*scale,y+5*scale,x+125*scale,y+135*scale), fill=COCO["fur"], outline=(151,74,35), width=max(2,int(4*scale)))
    draw.ellipse((x-50*scale,y+72*scale,x+108*scale,y+137*scale), fill=COCO["cream"])
    draw.ellipse((x-23*scale,y+45*scale,x-8*scale,y+63*scale), fill=(35,31,29))
    draw.ellipse((x+48*scale,y+45*scale,x+63*scale,y+63*scale), fill=(35,31,29))
    draw.ellipse((x+9*scale,y+87*scale,x+30*scale,y+103*scale), fill=(45,34,31))


def wrap_lines(text, font, max_width, draw):
    words = text.split()
    lines, current = [], ""
    for word in words:
        test = (current + " " + word).strip()
        if draw.textbbox((0,0), test, font=font)[2] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def render_scene(scene_no, caption, story_title):
    im = gradient_background(scene_no)
    draw = ImageDraw.Draw(im)
    draw_landscape(draw, scene_no)
    # Small glowing fireflies / story sparkles.
    random.seed(scene_no * 71)
    for _ in range(22):
        x, y = random.randint(40, 1040), random.randint(420, 1180)
        r = random.randint(3, 8)
        draw.ellipse((x-r,y-r,x+r,y+r), fill=(255, 232, 151))
    draw_ayan(draw, x=340 if scene_no % 2 else 385, y=1130, scale=1.0, pose=scene_no)
    draw_coco(draw, x=660 if scene_no % 2 else 690, y=1400, scale=0.82, pose=scene_no)
    # English subtitles are burned in later from the timed SRT file.
    # Keep the artwork clean so captions are not duplicated.
    # Small episode label.
    small = load_font(26, bold=True)
    draw.text((58,80), "TOM  +  JERRY   •   URDU CARTOON", font=small, fill=(255,248,221))
    return im


async def create_voice_segment(text, destination):
    tts = edge_tts.Communicate(text=text, voice=VOICE, rate="-3%", volume="+0%")
    await tts.save(str(destination))
    if not destination.exists() or destination.stat().st_size < 700:
        raise RuntimeError(f"Voice segment failed: {destination.name}")


def timestamp(seconds):
    ms = int(round(seconds * 1000))
    hours, ms = divmod(ms, 3600000)
    minutes, ms = divmod(ms, 60000)
    secs, ms = divmod(ms, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{ms:03}"


def make_subtitles(story, durations):
    offset = 0.0
    entries = []
    for i, ((urdu, english), duration) in enumerate(zip(story["scenes"], durations), start=1):
        start = max(0, offset + 0.05)
        end = max(start + 0.5, offset + duration - 0.05)
        entries.append(f"{i}\n{timestamp(start)} --> {timestamp(end)}\n{english}\n")
        offset += duration
    SUBTITLE_FILE.write_text("\n".join(entries), encoding="utf-8")



def render_animated_scene_clip(duration, number, scene_index, story_index, story_title):
    """
    Render real frame-to-frame character movement (not a zoom on one still).
    Artwork is procedural and locally generated; no paid image API is used.
    """
    frame_rate = 12
    frame_count = max(2, int(math.ceil(duration * frame_rate)))
    base = gradient_background(scene_index)
    base_draw = ImageDraw.Draw(base)
    draw_landscape(base_draw, scene_index)
    label_font = load_font(26, bold=True)
    base_draw.text((58, 80), "AYAN  +  COCO   •   URDU STORY", font=label_font, fill=(255, 248, 221))

    for frame_no in range(frame_count):
        progress = frame_no / max(1, frame_count - 1)
        phase = progress * math.tau
        frame = base.copy()
        draw = ImageDraw.Draw(frame)

        # Ayan walks forward across the trail; alternating arm pose and body bob
        # make the movement visible from frame to frame.
        ayan_x = 340 + int(115 * math.sin(progress * math.pi * 1.35))
        ayan_y = 1110 + int(18 * math.sin(phase * 2))
        ayan_pose = frame_no % 2
        draw_ayan(draw, x=ayan_x, y=ayan_y, scale=1.0, pose=ayan_pose)

        # Coco bounds alongside Ayan, with a little hop on each stride.
        coco_x = 655 + int(135 * math.sin(progress * math.pi * 1.6 + 0.7))
        coco_y = 1390 - int(38 * abs(math.sin(phase * 1.5)))
        draw_coco(draw, x=coco_x, y=coco_y, scale=0.82, pose=frame_no % 2)

        # Moving dust/sparkles follow their footsteps.
        for puff in range(3):
            px = (ayan_x - 25 + puff * 27 + frame_no * 13) % WIDTH
            py = 1570 + int(12 * math.sin(phase + puff))
            radius = 5 + (puff % 2) * 3
            draw.ellipse((px-radius, py-radius, px+radius, py+radius), fill=(235, 218, 165))

        # A story moment in every episode: a small glowing clue travels ahead.
        clue_x = int(160 + ((progress * 760 + scene_index * 83) % 760))
        clue_y = 980 + int(22 * math.sin(phase * 2))
        glow = 13 + int(4 * (0.5 + 0.5 * math.sin(phase * 3)))
        draw.ellipse((clue_x-glow, clue_y-glow, clue_x+glow, clue_y+glow), fill=(255, 226, 133))
        draw.ellipse((clue_x-4, clue_y-4, clue_x+4, clue_y+4), fill=(255, 255, 226))

        # Episode-specific animated action prop in the rescue/reunion scene.
        if scene_index == 4 and story_index == 0:
            bird_x = int(160 + progress * 690)
            bird_y = 900 - int(48 * math.sin(phase * 2))
            wing = int(18 * math.sin(phase * 5))
            draw.ellipse((bird_x-28, bird_y-14, bird_x+28, bird_y+14), fill=(245, 224, 177))
            draw.polygon([(bird_x+20,bird_y),(bird_x+45,bird_y-8),(bird_x+45,bird_y+8)], fill=(232,151,76))
            draw.arc((bird_x-18,bird_y-30-wing,bird_x+8,bird_y+8), 190, 340, fill=(255,248,220), width=6)
        elif scene_index == 4 and story_index == 1:
            turtle_x = int(190 + progress * 650)
            turtle_y = 1500 + int(8 * math.sin(phase * 3))
            draw.ellipse((turtle_x-42,turtle_y-28,turtle_x+42,turtle_y+28), fill=(91,145,83), outline=(35,83,61), width=5)
            draw.ellipse((turtle_x+30,turtle_y-12,turtle_x+58,turtle_y+12), fill=(111,164,91))
            draw.ellipse((turtle_x+43,turtle_y-7,turtle_x+48,turtle_y-2), fill=(20,35,25))
        elif scene_index == 4 and story_index == 2:
            for spark in range(7):
                sx = int(140 + ((progress * 700 + spark * 113) % 800))
                sy = 780 + int(55 * math.sin(phase * 2 + spark))
                draw.ellipse((sx-6,sy-6,sx+6,sy+6), fill=(255,239,151))

        frame_path = SCENES_DIR / f"scene_{number:02}_frame_{frame_no+1:04}.jpg"
        frame.save(frame_path, "JPEG", quality=88, optimize=True)

    clip_path = OUTPUT_DIR / f"clip_{number}.mp4"
    pattern = SCENES_DIR / f"scene_{number:02}_frame_%04d.jpg"
    run_command([
        "ffmpeg", "-y", "-framerate", str(frame_rate), "-i", str(pattern),
        "-vf", f"fps={FPS},scale={WIDTH}:{HEIGHT}:flags=fast_bilinear,format=yuv420p",
        "-t", f"{duration:.3f}", "-an", "-c:v", "libx264",
        "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p",
        str(clip_path)
    ])
    # Remove temporary frames after the scene has been encoded.
    for frame_path in SCENES_DIR.glob(f"scene_{number:02}_frame_*.jpg"):
        frame_path.unlink()
    return clip_path

def create_scene_clip(image_path, duration, number):
    clip_path = OUTPUT_DIR / f"clip_{number}.mp4"
    frames = max(1, int(math.ceil(duration * FPS)))
    vf = (
        f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={WIDTH}:{HEIGHT},setsar=1,"
        f"zoompan=z='min(zoom+0.0007,1.045)':"
        f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"d={frames}:s={WIDTH}x{HEIGHT}:fps={FPS},format=yuv420p"
    )
    run_command([
        "ffmpeg","-y","-loop","1","-i",str(image_path),
        "-vf",vf,"-t",f"{duration:.3f}","-r",str(FPS),"-an",
        "-c:v","libx264","-preset","veryfast","-crf","22",
        "-pix_fmt","yuv420p",str(clip_path)
    ])
    return clip_path


def join_files(files, list_file, output_file, audio=False):
    lines = []
    for item in files:
        safe = str(item.resolve()).replace("'", "'\\''")
        lines.append(f"file '{safe}'")
    list_file.write_text("\n".join(lines), encoding="utf-8")
    command = ["ffmpeg","-y","-f","concat","-safe","0","-i",str(list_file),"-c","copy",str(output_file)]
    run_command(command)
    return output_file


def create_final_video(silent_video):
    subtitle_path = str(SUBTITLE_FILE.resolve()).replace("\\","/").replace(":","\\:")
    subtitle_filter = (
        f"subtitles='{subtitle_path}':force_style="
        "'FontName=DejaVu Sans,FontSize=21,PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00101820,BorderStyle=1,Outline=3,Shadow=1,"
        "Alignment=2,MarginV=145'"
    )
    # A very quiet generated ambient pad; no copyrighted song is used.
    run_command([
        "ffmpeg","-y","-i",str(silent_video),"-i",str(VOICE_FILE),
        "-f","lavfi","-i","anoisesrc=color=pink:sample_rate=44100:amplitude=0.018",
        "-filter_complex",
        f"[0:v]{subtitle_filter}[v];[1:a]volume=1.0[voice];[2:a]lowpass=f=500,volume=0.10[amb];[voice][amb]amix=inputs=2:duration=first:dropout_transition=2[a]",
        "-map","[v]","-map","[a]","-c:v","libx264","-preset","veryfast",
        "-crf","22","-c:a","aac","-b:a","160k","-shortest",
        "-movflags","+faststart",str(VIDEO_FILE)
    ])
    if not VIDEO_FILE.exists() or VIDEO_FILE.stat().st_size < 15000:
        raise RuntimeError("Final MP4 was not created correctly.")


def make_youtube_description(story):
    tags = " ".join("#" + re.sub(r"[^A-Za-z0-9]", "", t.replace(" ", "")) for t in story["tags"][:5])
    return (
        f"{story['title']}\n\n"
        "Tom & Jerry funny animated cartoon episode with Urdu narration and English subtitles. "
        "A playful cat-and-mouse comedy adventure for cartoon fans.\n\n"
        "SERIES: Tom & Jerry Urdu Cartoon Shorts\n"
        "CATEGORY: Film & Animation\n"
        "LANGUAGE: Urdu voice + English subtitles\n\n"
        "Watch the daily episode and follow for more funny cartoon moments!\n\n"
        f"#TomAndJerry #UrduCartoon #CartoonShorts #FunnyCartoon #Shorts {tags}"
    )[:4500]


# ============================================================
# YOUTUBE OAUTH + UPLOAD
# Kept compatible with the existing GitHub secrets.
# ============================================================

def upload_to_youtube(title, story):
    print("Preparing YouTube upload...")
    client_json = os.getenv("YOUTUBE_CLIENT_JSON")
    refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN")
    if not client_json:
        raise RuntimeError("YOUTUBE_CLIENT_JSON secret is missing.")
    if not refresh_token:
        raise RuntimeError("YOUTUBE_REFRESH_TOKEN secret is missing.")

    client_data = json.loads(client_json)
    client_info = client_data.get("installed") or client_data.get("web")
    if not client_info:
        raise RuntimeError("Invalid YouTube client JSON.")

    credentials = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri=client_info.get("token_uri","https://oauth2.googleapis.com/token"),
        client_id=client_info["client_id"],
        client_secret=client_info["client_secret"],
        scopes=["https://www.googleapis.com/auth/youtube.upload"]
    )
    youtube = build("youtube","v3",credentials=credentials)
    privacy = os.getenv("YOUTUBE_PRIVACY_STATUS", PRIVACY_DEFAULT)
    if privacy not in ("private","unlisted","public"):
        privacy = "private"

    body = {
        "snippet": {
            "title": clean_text(title)[:100],
            "description": make_youtube_description(story),
            "tags": story["tags"] + ["youtube shorts","Tom and Jerry","Urdu voice","English subtitles","animated comedy","family friendly"],
            "categoryId": "1"
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False
        }
    }
    media = MediaFileUpload(str(VIDEO_FILE), mimetype="video/mp4", resumable=True)
    request = youtube.videos().insert(part="snippet,status",body=body,media_body=media)
    response = None
    failures = 0
    while response is None:
        try:
            status, response = request.next_chunk()
            failures = 0
            if status:
                print(f"Upload progress: {int(status.progress()*100)}%")
        except Exception as exc:
            failures += 1
            if failures >= 5:
                raise
            wait = min(60, 5 * (2 ** (failures-1)))
            print(f"Upload connection issue: {exc}. Retrying in {wait}s...")
            time.sleep(wait)

    video_id = response.get("id")
    print("YouTube upload successful.")
    print("Video ID:", video_id)
    print("Privacy:", privacy)
    print("Video URL:", f"https://www.youtube.com/watch?v={video_id}")



def generate_story_with_gemini():
    """Generate one fresh six-scene Urdu/English episode using Gemini."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        print("GEMINI_API_KEY is not set; using the built-in episode list for this run.")
        return None

    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    prompt = """
Create a completely original, family-friendly, funny Tom and Jerry cartoon episode
for a short vertical animated video. The story must have exactly 6 connected scenes
with clear physical actions, a funny escalation, and a satisfying ending.
Return ONLY valid JSON with this exact structure:
{
  "title": "Tom & Jerry Urdu Cartoon EP | short English title",
  "tags": ["Tom and Jerry", "Urdu cartoon", "funny animation", "cartoon shorts"],
  "scenes": [
    {"urdu": "One or two natural Urdu sentences for voice narration.",
     "english": "A concise English subtitle describing the same action."}
  ]
}
Rules:
- Write natural Urdu in Urdu script, not Roman Urdu.
- English subtitles must match the Urdu narration.
- Every scene must describe a visible action that can be animated.
- Keep Tom and Jerry's familiar cat-and-mouse personalities.
- Make each new episode idea distinct; avoid repeating the same cheese chase.
- Keep it suitable for children and families. No violence, danger, or frightening content.
- Exactly 6 scene objects. No markdown fences and no extra commentary.
"""
    response = requests.post(
        url,
        headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
        json={
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.9
            }
        },
        timeout=90
    )
    if response.status_code >= 400:
        raise RuntimeError(
            f"Gemini API request failed ({response.status_code}): {response.text[:3000]}"
        )
    payload = response.json()
    try:
        raw = payload["candidates"][0]["content"]["parts"][0]["text"]
        data = json.loads(raw)
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Gemini returned an invalid story response: {payload}") from exc

    title = clean_text(data.get("title"))
    tags = data.get("tags")
    scenes = data.get("scenes")
    if not title or not isinstance(tags, list) or not isinstance(scenes, list) or len(scenes) != 6:
        raise RuntimeError("Gemini story must contain a title, tags list, and exactly 6 scenes.")
    clean_scenes = []
    for index, scene in enumerate(scenes, start=1):
        if not isinstance(scene, dict):
            raise RuntimeError(f"Gemini scene {index} is not a JSON object.")
        urdu = clean_text(scene.get("urdu"))
        english = clean_text(scene.get("english"))
        if not urdu or not english:
            raise RuntimeError(f"Gemini scene {index} is missing Urdu narration or English subtitles.")
        clean_scenes.append((urdu, english))

    clean_tags = [clean_text(tag) for tag in tags if clean_text(tag)]
    if not clean_tags:
        clean_tags = ["Tom and Jerry", "Urdu cartoon", "funny animation", "cartoon shorts"]
    story = {"title": title[:100], "tags": clean_tags[:12], "scenes": clean_scenes}
    print("Gemini generated a fresh 6-scene episode:", story["title"])
    return story

def main():
    print("\n======================================")
    print("   TOM & JERRY URDU 3D CARTOON SHORTS")
    print("======================================\n")
    # Prefer a fresh Gemini-written episode. Keep the preset list as a safe
    # fallback until the GEMINI_API_KEY GitHub secret has been added.
    story = generate_story_with_gemini()
    if story is None:
        override = os.getenv("STORY_INDEX")
        if override is not None:
            story = STORIES[int(override) % len(STORIES)]
        else:
            day_number = datetime.now(timezone.utc).date().toordinal()
            story = STORIES[day_number % len(STORIES)]
        story_index = STORIES.index(story)
    else:
        story_index = 0
    print("Selected episode:", story["title"])

    for folder in (SCENES_DIR, AUDIO_DIR):
        for old in folder.glob("*"):
            if old.is_file():
                old.unlink()
    for old in OUTPUT_DIR.glob("clip_*.mp4"):
        old.unlink()
    for old in (VIDEO_FILE, VOICE_FILE, SUBTITLE_FILE, CONCAT_FILE, AUDIO_CONCAT_FILE):
        if old.exists():
            old.unlink()

    audio_files, durations = [], []
    story_index = STORIES.index(story)
    for index, (urdu, english) in enumerate(story["scenes"], start=1):
        print(f"Creating Urdu narration for scene {index}/{len(story['scenes'])}...")
        audio_path = AUDIO_DIR / f"voice_{index:02}.mp3"
        asyncio.run(create_voice_segment(urdu, audio_path))
        audio_files.append(audio_path)
        durations.append(get_duration(audio_path))

    # Join voice segments in the same order used to time the English subtitles.
    audio_list = []
    for item in audio_files:
        safe = str(item.resolve()).replace("'", "'\\''")
        audio_list.append(f"file '{safe}'")
    AUDIO_CONCAT_FILE.write_text("\n".join(audio_list), encoding="utf-8")
    run_command([
        "ffmpeg","-y","-f","concat","-safe","0","-i",str(AUDIO_CONCAT_FILE),
        "-c:a","libmp3lame","-q:a","3",str(VOICE_FILE)
    ])

    make_subtitles(story, durations)
    clips = []
    for i, duration in enumerate(durations, start=1):
        clip_path = OUTPUT_DIR / f"clip_{i}.mp4"
        print(f"Rendering 3D Tom & Jerry scene {i}/{len(durations)} with Blender...")
        blender_result = run_command([
            "blender", "-b", "--python-exit-code", "1",
            "--python", str(BLENDER_SCRIPT), "--",
            f"{duration:.3f}", str(i), str(story_index), str(clip_path)
        ])
        # Blender renders numbered PNG frames for compatibility with builds
        # that do not expose FFmpeg as a native render output format.
        frame_pattern = str(clip_path) + ".frame_%04d.png"
        frame_files = sorted(OUTPUT_DIR.glob(f"{clip_path.name}.frame_*.png"))
        if not frame_files:
            print("\nBlender finished without rendering any PNG frames.", flush=True)
            if blender_result.stdout:
                print("\n--- BLENDER OUTPUT ---\n" + blender_result.stdout[-12000:], flush=True)
            if blender_result.stderr:
                print("\n--- BLENDER ERRORS ---\n" + blender_result.stderr[-20000:], flush=True)
            raise RuntimeError(f"Blender did not create PNG frames for scene {i}.")
        run_command([
            "ffmpeg", "-y", "-framerate", "12", "-i", frame_pattern,
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(clip_path)
        ])
        for frame_file in frame_files:
            frame_file.unlink()
        if not clip_path.exists() or clip_path.stat().st_size < 10000:
            raise RuntimeError(f"FFmpeg did not create a usable scene clip {i} at {clip_path}.")
        clips.append(clip_path)
    silent_video = join_files(clips, CONCAT_FILE, OUTPUT_DIR / "silent_video.mp4")
    create_final_video(silent_video)
    upload_to_youtube(story["title"], story)
    print("\nALL TASKS COMPLETED.")


if __name__ == "__main__":
    main()

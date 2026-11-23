"""English-morning edition runner.

Reuses the existing story, animation, subtitles, and YouTube uploader. It speaks
the English dialogue and burns the Urdu translation into the video.
"""
import asyncio
import re

import edge_tts
import main as cartoon


async def create_english_voice_segment(text, destination, speaker="tom"):
    voice = "en-US-GuyNeural" if speaker == "tom" else "en-US-JennyNeural"
    rate = "-3%" if speaker == "tom" else "+5%"
    await edge_tts.Communicate(
        text=text, voice=voice, rate=rate, volume="+0%"
    ).save(str(destination))
    if not destination.exists() or destination.stat().st_size < 700:
        raise RuntimeError(f"English voice segment failed: {destination.name}")


def make_urdu_subtitles(story, durations):
    offset = 0.0
    entries = []
    for index, (scene, duration) in enumerate(zip(story["scenes"], durations), start=1):
        urdu = scene[0]
        start = max(0.0, offset + 0.05)
        end = max(start + 0.5, offset + duration - 0.05)
        entries.append(
            f"{index}\\n{cartoon.timestamp(start)} --> {cartoon.timestamp(end)}\\n{urdu}\\n"
        )
        offset += duration
    cartoon.SUBTITLE_FILE.write_text("\\n".join(entries), encoding="utf-8")


def english_description(story):
    tags = " ".join("#" + re.sub(r"[^A-Za-z0-9]", "", tag.replace(" ", "")) for tag in story["tags"][:5])
    return (
        f"{story['title']}\\n\\n"
        "A funny animated cat-and-mouse adventure with English character voices "
        "and Urdu subtitles. Family-friendly cartoon comedy.\\n\\n"
        "SERIES: Tom & Jerry English Cartoon Shorts\\n"
        "LANGUAGE: English voice + Urdu subtitles\\n\\n"
        f"#TomAndJerry #EnglishCartoon #CartoonShorts #FunnyCartoon #Shorts {tags}"
    )[:4500]


_original_story_generator = cartoon.generate_story_with_gemini


def english_story_generator():
    story = _original_story_generator()
    if story:
        title = story["title"]
        if "English" not in title:
            title = "Tom & Jerry English Cartoon | " + title
        story["title"] = title[:100]
    return story


for preset in cartoon.STORIES:
    preset["title"] = preset["title"].replace("Urdu Cartoon", "English Cartoon").replace("Urdu cartoon", "English cartoon")

cartoon.create_voice_segment = create_english_voice_segment
cartoon.make_subtitles = make_urdu_subtitles
cartoon.make_youtube_description = english_description
cartoon.generate_story_with_gemini = english_story_generator

if __name__ == "__main__":
    print("Starting English-morning cartoon: English voices + Urdu subtitles.")
    cartoon.main()

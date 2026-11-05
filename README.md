# Ayan & Coco — Urdu Cartoon Shorts Automation

This repository generates one original, family-friendly vertical cartoon story Short per scheduled run and uploads it to YouTube as **private** for review.

## What the current version does

- Features two recurring original characters: **Ayan**, a young explorer in a teal jacket with a red backpack, and **Coco**, a small orange fox.
- Uses original artwork drawn locally with Pillow. The initial visual style is a simple layered **2.5D motion-comic**, not full 3D animation.
- Creates six illustrated scenes for a short connected-style adventure.
- Generates Urdu narration with Microsoft Edge TTS using `ur-PK-UzmaNeural`.
- Creates English subtitles timed to the individual Urdu narration segments and burns them into the video.
- Adds gentle camera zoom/pan and a quiet generated ambient audio bed. No third-party music track is included.
- Renders a vertical 1080×1920 MP4 and uploads through YouTube Data API v3.
- Uses no paid image-generation API and needs no character PNG uploads.

## GitHub Actions secrets

Keep these two existing secrets configured in **Settings → Secrets and variables → Actions**:

- `YOUTUBE_CLIENT_JSON`: complete Google OAuth client JSON.
- `YOUTUBE_REFRESH_TOKEN`: refresh token for the Google account that owns the YouTube channel.

Never paste either secret into chat, source code, workflow files, or commit history.

## Upload privacy

The workflow sets `YOUTUBE_PRIVACY_STATUS: private`. The generated Short is uploaded privately so it can be checked manually before publishing. Do not change this to public until the output has been reviewed.

The existing OAuth upload flow and secret names are retained. If the YouTube API rejects the refresh token or OAuth client, check the GitHub Actions log; do not expose credentials when asking for help.

## Schedule

The workflow schedule is `0 13 * * *` (13:00 UTC, which is 18:00 / 6 PM Pakistan time). GitHub may delay scheduled workflow runs. You can also start a run manually from the **Actions** tab.

Generated MP4 and supporting files are saved as a workflow artifact when available.

## Optional manual episode selection

Set an environment variable named `STORY_INDEX` to `0`, `1`, or `2` when running locally to choose one of the included starter stories. If it is not set, the script selects an episode based on the UTC date.

## Requirements and limitations

- Python 3.11
- FFmpeg and FFprobe
- Python dependencies from `requirements.txt`
- Internet access for Edge TTS and YouTube upload

This first version uses procedural illustrations and camera movement. It is not full 3D character animation, and the starter episode library is finite. Review every private upload for visual quality, Urdu pronunciation, subtitle timing, and child-safety before publishing. Automated uploads do not guarantee views, revenue, or monetization eligibility.

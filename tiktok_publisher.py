"""Automatically publish the generated Short to TikTok using Direct Post.

The GitHub Actions workflow obtains a short-lived access token from the
Cloudflare OAuth worker. No TikTok credentials are stored in this script.
"""
import os
import sys
import time
import requests

API = "https://open.tiktokapis.com/v2"


def required(name):
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required GitHub Actions secret/environment value: {name}")
    return value


def main():
    video_path = sys.argv[1] if len(sys.argv) > 1 else "output/daily_story.mp4"
    if not os.path.isfile(video_path):
        raise RuntimeError(f"Video file not found: {video_path}")

    token = required("TIKTOK_ACCESS_TOKEN")
    language = os.getenv("STORY_LANGUAGE", "ur").lower()
    if language not in ("ur", "en"):
        language = "ur"
    title = os.getenv(
        "TIKTOK_POST_TITLE",
        "A new Urdu cartoon story! #UrduCartoon #CartoonShorts #CNFunCartoons"
        if language == "ur"
        else "A new English cartoon story! #EnglishCartoon #CartoonShorts #CNFunCartoons"
    )[:150]
    size = os.path.getsize(video_path)
    if size <= 0:
        raise RuntimeError("Video file is empty")

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    creator = requests.post(
        f"{API}/post/publish/creator_info/query/",
        headers=headers, json={}, timeout=30
    )
    creator.raise_for_status()
    creator_body = creator.json()
    if creator_body.get("error", {}).get("code") != "ok":
        raise RuntimeError("TikTok creator-info check failed: " + str(creator_body.get("error", {})))
    creator_data = creator_body.get("data") or {}
    privacy_options = creator_data.get("privacy_level_options") or []
    # Do not silently publish privately: public auto-posting is the requested behaviour.
    privacy = "PUBLIC_TO_EVERYONE"
    if privacy not in privacy_options:
        raise RuntimeError(
            "TikTok account/app does not currently allow PUBLIC_TO_EVERYONE Direct Post. "
            "Available privacy options: " + ", ".join(privacy_options)
        )

    # TikTok requires 5–64 MB chunks, except a video smaller than 5 MB
    # must be sent as one chunk exactly equal to the full video size.
    min_chunk = 5 * 1024 * 1024
    max_chunk = 64 * 1024 * 1024
    if size < min_chunk:
        chunk_size = size
    else:
        chunk_size = min(max_chunk, size)
    chunks = (size + chunk_size - 1) // chunk_size
    if chunks < 1 or chunks > 1000:
        raise RuntimeError(f"Invalid TikTok chunk count calculated: {chunks}")

    payload = {
        "post_info": {
            "title": title,
            "privacy_level": privacy,
            "disable_comment": False,
            "disable_duet": False,
            "disable_stitch": False,
            "video_cover_timestamp_ms": 1000
        },
        "source_info": {
            "source": "FILE_UPLOAD",
            "video_size": size,
            "chunk_size": chunk_size,
            "total_chunk_count": chunks
        }
    }
    init = requests.post(
        f"{API}/post/publish/video/init/",
        headers=headers, json=payload, timeout=45
    )
    # Preserve TikTok's structured error response; raise_for_status()
    # otherwise hides the API's actionable error code and message in Actions logs.
    if not init.ok:
        try:
            error_body = init.json()
        except ValueError:
            error_body = init.text[:2000]
        raise RuntimeError(
            f"TikTok publish initialization rejected: HTTP {init.status_code}; "
            f"response: {error_body}"
        )
    init_data = init.json()
    if init_data.get("error", {}).get("code") != "ok":
        raise RuntimeError("TikTok publish initialization failed: " + str(init_data.get("error", {})))
    upload_url = init_data["data"]["upload_url"]
    publish_id = init_data["data"]["publish_id"]

    with open(video_path, "rb") as video:
        for index in range(chunks):
            start = index * chunk_size
            end_exclusive = min(start + chunk_size, size)
            block = video.read(end_exclusive - start)
            put_headers = {
                "Content-Type": "video/mp4",
                "Content-Length": str(len(block)),
                "Content-Range": f"bytes {start}-{end_exclusive - 1}/{size}"
            }
            response = requests.put(upload_url, headers=put_headers, data=block, timeout=180)
            if response.status_code not in (200, 201, 206):
                raise RuntimeError(
                    f"TikTok video transfer failed on chunk {index + 1}: "
                    f"HTTP {response.status_code} {response.text[:500]}"
                )

    print("TikTok accepted the video upload request. Checking processing status...")
    for _ in range(18):
        status = requests.post(
            f"{API}/post/publish/status/fetch/",
            headers=headers, json={"publish_id": publish_id}, timeout=30
        )
        status.raise_for_status()
        status_body = status.json()
        if status_body.get("error", {}).get("code") != "ok":
            raise RuntimeError("TikTok status check failed: " + str(status_body.get("error", {})))
        result = status_body.get("data") or {}
        state = result.get("status", "PROCESSING")
        print("TikTok publish status:", state)
        if state == "PUBLISH_COMPLETE":
            print("TikTok post published successfully.")
            return
        if state in ("FAILED", "SEND_TO_USER_INBOX"):
            raise RuntimeError(
                "TikTok did not publish the post. Status: " + state +
                "; details: " + str(result)
            )
        time.sleep(10)
    raise RuntimeError("TikTok is still processing the post. Check TikTok publish status later.")


if __name__ == "__main__":
    main()

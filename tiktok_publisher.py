"""Publish an already-rendered MP4 to TikTok using Content Posting API Direct Post.

Required environment:
  TIKTOK_ACCESS_TOKEN, TIKTOK_CLIENT_KEY, TIKTOK_CLIENT_SECRET
The access token must belong to the account that authorized this app and include
video.publish. Never commit credentials or print them to logs.
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
    client_key = required("TIKTOK_CLIENT_KEY")
    client_secret = required("TIKTOK_CLIENT_SECRET")
    title = os.getenv("TIKTOK_POST_TITLE", "A new cartoon story! #cartoon #kids #story")[:150]
    size = os.path.getsize(video_path)
    if size <= 0:
        raise RuntimeError("Video file is empty")

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    creator = requests.post(
        f"{API}/post/publish/creator_info/query/",
        headers=headers, json={}, timeout=30
    )
    creator.raise_for_status()
    creator_data = creator.json()
    if creator_data.get("error", {}).get("code") != "ok":
        raise RuntimeError("TikTok creator-info check failed: " + str(creator_data.get("error", {})))
    data = creator_data.get("data") or {}
    privacy_options = data.get("privacy_level_options") or []
    if not privacy_options:
        raise RuntimeError("TikTok did not return allowed privacy levels for this account")
    privacy = "SELF_ONLY" if "SELF_ONLY" in privacy_options else privacy_options[0]

    # TikTok Direct Post file upload supports chunked upload. Keep each chunk
    # within the API's documented size range; final chunk may be smaller.
    chunk_size = min(10 * 1024 * 1024, max(5 * 1024 * 1024, size))
    chunks = (size + chunk_size - 1) // chunk_size
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
    init.raise_for_status()
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
                raise RuntimeError(f"TikTok video transfer failed on chunk {index + 1}: HTTP {response.status_code} {response.text[:500]}")

    print("TikTok accepted the video upload request. Checking processing status...")
    status_headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    for _ in range(12):
        status = requests.post(
            f"{API}/post/publish/status/fetch/",
            headers=status_headers, json={"publish_id": publish_id}, timeout=30
        )
        status.raise_for_status()
        status_data = status.json()
        if status_data.get("error", {}).get("code") != "ok":
            raise RuntimeError("TikTok status check failed: " + str(status_data.get("error", {})))
        result = status_data.get("data") or {}
        state = result.get("status", "PROCESSING")
        print("TikTok publish status:", state)
        if state == "PUBLISH_COMPLETE":
            print("TikTok post published successfully.")
            return
        if state in ("FAILED", "SEND_TO_USER_INBOX"):
            raise RuntimeError("TikTok did not publish the post. Status: " + state + "; details: " + str(result))
        time.sleep(10)
    raise RuntimeError("TikTok is still processing the post. Check TikTok Developer publish status later.")

if __name__ == "__main__":
    main()

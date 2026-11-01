"""
AI Video Engine
Checks whether a real video-generation provider is configured.
Does not create fake AI videos or silently replace them with still images.
"""

import os


def generate_video(prompt, output_path):
    token = os.getenv("HF_TOKEN")

    if not token:
        raise RuntimeError(
            "No verified free video-generation provider is configured. "
            "HF_TOKEN is missing. No video was generated."
        )

    raise RuntimeError(
        "Hugging Face token found, but a working video-generation endpoint "
        "has not been configured. No video was generated."
    )


if __name__ == "__main__":
    print("AI Video Engine is ready for provider configuration.")

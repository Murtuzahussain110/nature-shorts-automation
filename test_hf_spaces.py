import inspect
import os
from gradio_client import Client

SPACE = "ByteDance/Hyper-FLUX-8Steps-LoRA"

def main():
    token = os.getenv("HF_TOKEN")
    args = {"verbose": False, "download_files": False}
    params = inspect.signature(Client.__init__).parameters
    if token and "hf_token" in params:
        args["hf_token"] = token
    elif token and "token" in params:
        args["token"] = token
    elif token:
        from huggingface_hub import login
        login(token=token, add_to_git_credential=False)

    print("Checking the previously tested image Space API without generating a test image.", flush=True)
    client = Client(SPACE, **args)
    api = client.view_api(return_format="dict")
    endpoints = api.get("named_endpoints", {})
    if "/process_image" not in endpoints:
        raise RuntimeError("The tested Hyper-FLUX /process_image endpoint is not available.")
    print("IMAGE_PROVIDER_API_READY=" + SPACE, flush=True)
    print("No image-generation credit was spent by this preflight check.", flush=True)

if __name__ == "__main__":
    main()

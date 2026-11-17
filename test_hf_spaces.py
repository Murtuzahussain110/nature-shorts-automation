import json, os, shutil, tempfile, time
from pathlib import Path
import requests
from gradio_client import Client
from PIL import Image

PROMPT = ("A beautifully detailed hand-painted 2D children's storybook illustration, "
          "a small warm orange fox wearing a teal scarf and a small lavender rabbit "
          "wearing a yellow waistcoat discover a tiny glowing star in a moonlit forest, "
          "cinematic composition, expressive characters, rich painterly detail, "
          "portrait 9:16, no text, no watermark")

def spaces():
    url = "https://huggingface.co/api/spaces"
    r = requests.get(url, params={"search":"text-to-image","limit":50,"sort":"likes","direction":-1}, timeout=30)
    r.raise_for_status()
    data = r.json()
    # Only public Gradio Spaces are candidates. Try most popular first.
    return [x for x in data if x.get("sdk") == "gradio" and x.get("id")]

def endpoint_args(spec):
    params = spec.get("parameters", [])
    args = []
    used_prompt = False
    for p in params:
        typ = p.get("type", {})
        comp = typ.get("type", "") if isinstance(typ, dict) else str(typ)
        label = (p.get("parameter_name") or p.get("label") or "").lower()
        if any(k in label for k in ("prompt", "description", "text")) and not used_prompt:
            args.append(PROMPT); used_prompt = True
        elif comp in ("str", "string") and not used_prompt:
            args.append(PROMPT); used_prompt = True
        elif comp in ("float", "int"):
            args.append(p.get("parameter_default", p.get("default", 7)))
        elif comp == "bool":
            args.append(p.get("parameter_default", p.get("default", False)))
        elif comp == "file":
            raise ValueError("endpoint requires an input file")
        else:
            choices = p.get("parameter_choices") or p.get("choices")
            if choices: args.append(choices[0])
            else: args.append(p.get("parameter_default", p.get("default")))
    if not used_prompt:
        raise ValueError("no text prompt input")
    return args

def extract_image(value, dest):
    candidates = value if isinstance(value, (list, tuple)) else [value]
    for item in candidates:
        if isinstance(item, dict):
            for k in ("path", "image", "url", "name"):
                if item.get(k):
                    try: return extract_image(item[k], dest)
                    except Exception: pass
        if isinstance(item, str):
            if item.startswith("http"):
                rr=requests.get(item,timeout=120); rr.raise_for_status(); dest.write_bytes(rr.content)
            else:
                p=Path(item)
                if not p.exists(): continue
                shutil.copyfile(p,dest)
            try:
                im=Image.open(dest); im.verify()
                return
            except Exception:
                dest.unlink(missing_ok=True)
    raise RuntimeError("Space did not return a readable image")

def main():
    candidates=spaces()
    print("Public text-to-image Gradio Spaces discovered:",len(candidates),flush=True)
    errors=[]
    for item in candidates[:25]:
        sid=item["id"]
        try:
            print("Trying Space:",sid,flush=True)
            client=Client(sid,verbose=False,download_files=False)
            api=client.view_api(return_format="dict")
            endpoints=api.get("named_endpoints",{})
            if not endpoints: raise RuntimeError("no named Gradio endpoints")
            for name,spec in endpoints.items():
                try:
                    args=endpoint_args(spec)
                    result=client.predict(*args,api_name=name)
                    out=Path("hf_space_test.png")
                    extract_image(result,out)
                    print("SUCCESS_SPACE="+sid,flush=True)
                    print("SUCCESS_ENDPOINT="+name,flush=True)
                    print("IMAGE_BYTES="+str(out.stat().st_size),flush=True)
                    return
                except Exception as e:
                    errors.append(sid+" "+str(name)+": "+str(e)[:220])
        except Exception as e:
            errors.append(sid+": "+str(e)[:220])
    print("NO_FREE_SPACE_WORKED",flush=True)
    for e in errors[-35:]: print("SPACE_ERROR:",e,flush=True)
    raise SystemExit("No accessible free public image Space generated a test illustration")

if __name__=="__main__": main()

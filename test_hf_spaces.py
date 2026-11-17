import shutil
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
    found = {}
    for query in ("text-to-image", "flux", "stable-diffusion", "image-generation", "sdxl"):
        r = requests.get("https://huggingface.co/api/spaces",
                         params={"search":query,"limit":100,"sort":"likes","direction":-1}, timeout=30)
        r.raise_for_status()
        for item in r.json():
            sid=item.get("id","")
            if item.get("sdk")=="gradio" and sid and not any(x in sid.lower() for x in ("nsfw","porn","nude","adult")):
                found[sid]=item
    return sorted(found.values(),key=lambda x:x.get("likes",0),reverse=True)

def endpoint_args(spec):
    args=[]; used=False
    for p in spec.get("parameters",[]):
        typ=p.get("type",{})
        comp=typ.get("type","") if isinstance(typ,dict) else str(typ)
        label=(p.get("parameter_name") or p.get("label") or "").lower()
        if not used and (comp in ("str","string") or any(k in label for k in ("prompt","text","description"))):
            args.append(PROMPT); used=True
        elif comp in ("float","int"):
            args.append(p.get("parameter_default",p.get("default",7)))
        elif comp=="bool":
            args.append(p.get("parameter_default",p.get("default",False)))
        elif comp=="file":
            raise ValueError("requires file input")
        else:
            choices=p.get("parameter_choices") or p.get("choices")
            args.append(choices[0] if choices else p.get("parameter_default",p.get("default")))
    if not used: raise ValueError("no text prompt input")
    return args

def extract_image(value,dest):
    items=value if isinstance(value,(list,tuple)) else [value]
    for item in items:
        if isinstance(item,dict):
            for key in ("path","image","url","name"):
                if item.get(key):
                    try: return extract_image(item[key],dest)
                    except Exception: pass
        if isinstance(item,str):
            if item.startswith("http"):
                r=requests.get(item,timeout=120); r.raise_for_status(); dest.write_bytes(r.content)
            else:
                p=Path(item)
                if not p.exists(): continue
                shutil.copyfile(p,dest)
            try:
                with Image.open(dest) as im: im.verify()
                return
            except Exception: dest.unlink(missing_ok=True)
    raise RuntimeError("no readable image in output")

def main():
    candidates=spaces()
    print("Public Gradio image Spaces discovered across five searches:",len(candidates),flush=True)
    errors=[]
    for item in candidates[:60]:
        sid=item["id"]
        try:
            print("Trying Space:",sid,"likes:",item.get("likes",0),flush=True)
            client=Client(sid,verbose=False,download_files=False)
            api=client.view_api(return_format="dict")
            endpoints=api.get("named_endpoints",{})
            if not endpoints: raise RuntimeError("no named API endpoints")
            for name,spec in endpoints.items():
                try:
                    args=endpoint_args(spec)
                    result=client.predict(*args,api_name=name)
                    out=Path("hf_space_test.png")
                    extract_image(result,out)
                    if out.stat().st_size<10000: raise RuntimeError("image too small")
                    print("SUCCESS_SPACE="+sid,flush=True)
                    print("SUCCESS_ENDPOINT="+name,flush=True)
                    print("IMAGE_BYTES="+str(out.stat().st_size),flush=True)
                    return
                except Exception as e: errors.append(sid+" "+str(name)+": "+str(e)[:180])
        except Exception as e: errors.append(sid+": "+str(e)[:180])
    print("NO_FREE_SPACE_WORKED",flush=True)
    for e in errors[-45:]: print("SPACE_ERROR:",e,flush=True)
    raise SystemExit("No accessible free public image Space generated a test illustration")

if __name__=="__main__": main()

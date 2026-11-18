import os, json, math, random, subprocess, asyncio, textwrap, shutil, inspect
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
import requests
from gradio_client import Client
import edge_tts
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"output"; IMAGES=OUT/"scenes"; AUDIO=OUT/"audio"
for p in (OUT,IMAGES,AUDIO): p.mkdir(parents=True,exist_ok=True)
W,H,FPS=540,960,12
VOICE_A="ur-PK-UzmaNeural"; VOICE_B="ur-PK-AsadNeural"
STORIES=[
 {"title":"The Lost Star","urdu":"گمشدہ ستارہ","cast":[("Milo","fox","warm orange fox with cream muzzle, teal scarf"),("Pip","rabbit","small lavender rabbit with long ears, yellow waistcoat")],
  "scenes":[("رات کے جنگل میں مِلو کو گھاس پر ایک ننھا چمکتا ستارہ ملا۔","Milo discovers a tiny glowing fallen star in a moonlit forest clearing."),
  ("پِپ نے کہا، ہمیں اسے واپس آسمان تک پہنچانا ہوگا۔","Pip joins Milo; both carefully cradle the glowing star and look toward a distant hill."),
  ("وہ پتھریلے راستے پر چلتے ہوئے پہاڑی کی طرف روانہ ہوئے۔","The two friends climb a winding rocky forest path at night, star glowing between them."),
  ("اچانک تیز ہوا چلی اور ستارہ ان کے ہاتھوں سے نکلنے لگا۔","A strong gust of wind almost blows the glowing star away; the friends reach out urgently."),
  ("مِلو نے پِپ کا ہاتھ پکڑا اور دونوں نے مل کر ستارہ سنبھال لیا۔","Milo and Pip protect the star together against the wind on the hilltop."),
  ("ستارہ آسمان میں واپس چمکا، اور دونوں دوست خوشی سے مسکرائے۔","The star rises back into a beautiful deep-blue starry sky as the two friends smile on the hilltop.") ]},
 {"title":"The Magic Garden","urdu":"جادوئی باغ","cast":[("Nori","bear","small honey-brown bear cub with red backpack"),("Zuzu","bird","bright turquoise little bird with golden beak and tiny blue cap")],
  "scenes":[("نوری کو درختوں کے پیچھے ایک خفیہ دروازہ نظر آیا۔","Nori the bear cub discovers a tiny ornate glowing door hidden in an ancient tree."),
  ("زوزو نے اپنے پروں سے دروازہ کھولا تو روشنی پھیل گئی۔","Zuzu the turquoise bird opens the tiny door and warm magical light spills out."),
  ("دروازے کے پیچھے رنگ برنگے پھولوں کا باغ تھا۔","The friends enter a breathtaking secret garden filled with luminous colorful flowers."),
  ("ایک ننھی تتلی راستہ بھول کر پھولوں میں پھنس گئی تھی۔","A tiny butterfly is tangled gently among oversized flower stems, looking worried."),
  ("دونوں نے احتیاط سے تتلی کو آزاد کر دیا۔","Nori and Zuzu carefully free the butterfly together in the magical garden."),
  ("تتلی اڑی تو پورا باغ جگمگا اٹھا۔","The butterfly flies free and the entire enchanted garden glows with sparkling lights.") ]}
]


def generate_story():
 # Gemini creates one fresh Urdu story and six matching scene descriptions.
 # If no key/quota/network is available, retain the existing safe story fallback.
 key=os.getenv("GEMINI_API_KEY")
 if not key:
  print("GEMINI_API_KEY missing; using built-in story fallback",flush=True)
  return random.choice(STORIES)
 prompt="""Create one original family-friendly Urdu illustrated cartoon short story.
Return ONLY valid JSON with exactly these keys:
title (short English title), urdu (Urdu title),
cast (array of exactly 2 objects with name, species, design),
scenes (array of exactly 6 objects with narration_urdu and visual_en).
Narration must be natural Urdu script, one short sentence per scene, suitable for spoken narration.
visual_en must describe a detailed, specific, visually distinct storybook illustration for that exact moment.
Keep the same two characters, clothing, colors and proportions in all six scenes.
Make the story emotionally engaging with a clear beginning, problem, teamwork and happy ending.
No copyrighted characters, no text inside images, no violence, no generic stock-photo descriptions."""
 try:
  base="https://generativelanguage.googleapis.com/v1beta"
  listing=requests.get(base+"/models",params={"key":key},timeout=45)
  listing.raise_for_status()
  available=listing.json().get("models",[])
  supported=[m for m in available if "generateContent" in m.get("supportedGenerationMethods",[])]
  if not supported:
   raise RuntimeError("This API key has no model that supports generateContent")
  preferred=("gemini-3.1-flash","gemini-3-flash","gemini-2.5-flash","gemini-2.0-flash")
  chosen=None
  for wanted in preferred:
   chosen=next((m for m in supported if m.get("name","").split("/")[-1].startswith(wanted)),None)
   if chosen: break
  if chosen is None:
   chosen=next((m for m in supported if "flash" in m.get("name","").lower()),supported[0])
  model=chosen["name"]
  print("Gemini model selected:",model,flush=True)
  response=requests.post(
   base+"/"+model+":generateContent",
   params={"key":key},
   json={"contents":[{"parts":[{"text":prompt}]}],
         "generationConfig":{"responseMimeType":"application/json","temperature":0.9}},
   timeout=90)
  if not response.ok:
   raise RuntimeError("Gemini "+str(response.status_code)+": "+response.text[:1200])
  payload=response.json()
  raw=payload["candidates"][0]["content"]["parts"][0]["text"].strip()
  if raw.startswith("```"):
   raw=raw.split("\n",1)[1].rsplit("```",1)[0].strip()
  data=json.loads(raw)
  cast=data["cast"]; scenes=data["scenes"]
  if len(cast)!=2 or len(scenes)!=6: raise ValueError("Gemini story must contain 2 characters and 6 scenes")
  normalized={
   "title":str(data["title"])[:80],
   "urdu":str(data["urdu"])[:100],
   "cast":[(str(x["name"]),str(x["species"]),str(x["design"])) for x in cast],
   "scenes":[(str(x["narration_urdu"]),str(x["visual_en"])) for x in scenes]
  }
  if any(not ur.strip() or not en.strip() for ur,en in normalized["scenes"]):
   raise ValueError("Gemini returned an empty scene")
  print("GEMINI STORY READY:",normalized["title"],flush=True)
  return normalized
 except Exception as e:
  print("Gemini story generation unavailable; using built-in story fallback:",str(e),flush=True)
  return random.choice(STORIES)

def run(cmd):
 p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 if p.returncode: raise RuntimeError((p.stderr or p.stdout)[-4000:])
def stamp(s):
 ms=int(s*1000); h,ms=divmod(ms,3600000); m,ms=divmod(ms,60000); sec,ms=divmod(ms,1000)
 return f"{h:02}:{m:02}:{sec:02},{ms:03}"
def wrap(s,n=28):
 words=s.split(); lines=[]; line=""
 for w in words:
  if len((line+" "+w).strip())>n and line: lines.append(line); line=w
  else: line=(line+" "+w).strip()
 if line: lines.append(line)
 return "\n".join(lines[:2])
async def voice(text,path,v):
 await edge_tts.Communicate(text=text,voice=v,rate="-3%").save(str(path))
 if not path.exists() or path.stat().st_size<500: raise RuntimeError("Urdu voice generation failed")
def image_prompt(story,scene_en):
 cast="; ".join(f"{n}: {desc}" for n,kind,desc in story["cast"])
 return ("Premium hand-painted 2D illustrated children's storybook frame, rich detailed environment, expressive consistent cartoon characters, beautiful cinematic composition, soft painterly textures, warm appealing colors, professional animation concept art. "
         f"Recurring character designs must stay exactly consistent: {cast}. "
         f"Scene: {scene_en} "
         "Portrait vertical 9:16 composition, full scene visible, no words, no letters, no captions, no watermark, not 3D, not photorealistic.")
def validate_image(path):
 from PIL import Image
 with Image.open(path) as im:
  im.verify()
 if path.stat().st_size<10000:
  raise RuntimeError("Image provider returned an incomplete image")

def generate_image(prompt,seed,path):
 # Try the existing HF Space first. If its shared ZeroGPU quota is exhausted,
 # use Pollinations' public image endpoint as a second independent provider.
 last=None
 try:
  token=os.getenv("HF_TOKEN")
  client_args={"verbose":False,"download_files":True}
  params=inspect.signature(Client.__init__).parameters
  if token and "hf_token" in params:
   client_args["hf_token"]=token
  elif token and "token" in params:
   client_args["token"]=token
  elif token:
   from huggingface_hub import login
   login(token=token, add_to_git_credential=False)
  client=Client("ByteDance/Hyper-FLUX-8Steps-LoRA",**client_args)
  result=client.predict(1024,576,8,3.5,prompt,float(seed),api_name="/process_image")
  image_result=result[0] if isinstance(result,(list,tuple)) else result
  source=image_result.get("path") if isinstance(image_result,dict) else image_result
  if not source: raise RuntimeError("Hyper-FLUX returned no image path")
  if str(source).startswith("http"):
   response=requests.get(source,timeout=120); response.raise_for_status()
   path.write_bytes(response.content)
  else:
   shutil.copyfile(str(source),path)
  validate_image(path)
  print(f"AI IMAGE READY (Hugging Face): scene seed {seed}, {path.stat().st_size} bytes",flush=True)
  return
 except Exception as e:
  last=e
  print(f"Hugging Face unavailable; trying independent free image provider: {e}",flush=True)

 # Public fallback. It is free to try but may impose its own rate limits;
 # no paid key, subscription, or credits are used.
 endpoint="https://image.pollinations.ai/prompt/"+quote(prompt,safe="")
 params={"width":576,"height":1024,"seed":int(seed),"model":"flux","nologo":"true"}
 try:
  response=None
  for attempt in range(4):
   response=requests.get(endpoint,params=params,headers={"Accept":"image/*","User-Agent":"Mozilla/5.0 UrduStoryAutomation/1.0"},timeout=240)
   if response.status_code not in (429,500,502,503,504): break
   if attempt<3:
    wait=10*(attempt+1)
    print(f"Pollinations temporary HTTP {response.status_code}; retrying in {wait}s",flush=True)
    import time; time.sleep(wait)
  response.raise_for_status()
  content_type=response.headers.get("content-type","").lower()
  if "image" not in content_type:
   raise RuntimeError("Fallback provider did not return an image (content-type: "+content_type+")")
  path.write_bytes(response.content)
  validate_image(path)
  print(f"AI IMAGE READY (Pollinations fallback): scene seed {seed}, {path.stat().st_size} bytes",flush=True)
  return
 except Exception as e:
  raise RuntimeError("Both free image providers failed. Hugging Face: "+str(last)+" | Pollinations: "+str(e))

def upload(video,title,description):
 client=json.loads(os.environ["YOUTUBE_CLIENT_JSON"]); info=client.get("installed") or client.get("web")
 creds=Credentials(None,refresh_token=os.environ["YOUTUBE_REFRESH_TOKEN"],token_uri=info.get("token_uri","https://oauth2.googleapis.com/token"),client_id=info["client_id"],client_secret=info["client_secret"],scopes=["https://www.googleapis.com/auth/youtube.upload"])
 yt=build("youtube","v3",credentials=creds)
 req=yt.videos().insert(part="snippet,status",body={"snippet":{"title":title[:100],"description":description,"tags":["Urdu cartoon","illustrated story","shorts"],"categoryId":"1"},"status":{"privacyStatus":"private","selfDeclaredMadeForKids":False}},media_body=MediaFileUpload(str(video),mimetype="video/mp4",resumable=True))
 response=None
 while response is None: status,response=req.next_chunk()
 print("PRIVATE VIDEO: https://www.youtube.com/watch?v="+response["id"],flush=True)
def main():
 day=datetime.now(timezone.utc).date().toordinal(); story=generate_story()
 for folder in (IMAGES,AUDIO):
  for f in folder.glob("*"):
   if f.is_file(): f.unlink()
 clips=[]; audios=[]; subs=[]; offset=0.0
 for i,(ur,en) in enumerate(story["scenes"],1):
  img=IMAGES/f"scene_{i}.jpg"; generate_image(image_prompt(story,en),day*17+i,img)
  wav=AUDIO/f"voice_{i}.mp3"; asyncio.run(voice(ur,wav,VOICE_A if i%2 else VOICE_B)); audios.append(wav)
  probe=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(wav)],capture_output=True,text=True,check=True)
  dur=max(3.5,float(probe.stdout.strip())+.25)
  clip=OUT/f"clip_{i}.mp4"
  # Gentle Ken Burns movement on each actual AI illustration.
  run(["ffmpeg","-y","-loglevel","error","-loop","1","-i",str(img),"-t",str(dur),"-vf",f"scale=800:1422,zoompan=z='min(zoom+0.0007,1.08)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={int(dur*FPS)}:s={W}x{H}:fps={FPS},format=yuv420p","-an","-c:v","libx264","-preset","veryfast","-crf","23",str(clip)])
  clips.append(clip); subs.append(f"{i}\n{stamp(offset)} --> {stamp(offset+dur)}\n{wrap(ur)}\n"); offset+=dur
 (OUT/"subtitles.srt").write_text("\n".join(subs),encoding="utf-8")
 (OUT/"clips.txt").write_text("\n".join("file '"+str(x.resolve())+"'" for x in clips),encoding="utf-8")
 (OUT/"audio.txt").write_text("\n".join("file '"+str(x.resolve())+"'" for x in audios),encoding="utf-8")
 run(["ffmpeg","-y","-loglevel","error","-f","concat","-safe","0","-i",str(OUT/"clips.txt"),"-c","copy",str(OUT/"silent.mp4")])
 run(["ffmpeg","-y","-loglevel","error","-f","concat","-safe","0","-i",str(OUT/"audio.txt"),"-c:a","libmp3lame","-q:a","4",str(OUT/"voice.mp3")])
 sub=str((OUT/"subtitles.srt").resolve()).replace("\\","/").replace(":","\\:")
 run(["ffmpeg","-y","-loglevel","error","-i",str(OUT/"silent.mp4"),"-i",str(OUT/"voice.mp3"),"-vf",f"subtitles='{sub}':force_style='FontName=Noto Naskh Arabic,FontSize=17,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=1,Alignment=2,MarginV=55'","-map","0:v","-map","1:a","-c:v","libx264","-preset","veryfast","-crf","23","-c:a","aac","-shortest","-movflags","+faststart",str(OUT/"daily_story.mp4")])
 video=OUT/"daily_story.mp4"
 if not video.exists() or video.stat().st_size<50000: raise RuntimeError("Final MP4 validation failed")
 print("AI-ILLUSTRATED VIDEO READY:",video,"STORY:",story["title"],flush=True)
 if os.getenv("YOUTUBE_UPLOAD_ENABLED","").lower()=="true":
  if not os.getenv("YOUTUBE_CLIENT_JSON") or not os.getenv("YOUTUBE_REFRESH_TOKEN"): raise RuntimeError("YouTube OAuth secrets missing")
  upload(video,story["title"]+" | Urdu Cartoon Story #Shorts",f"{story['urdu']}\n\n#UrduStory #Cartoon #Shorts")
if __name__=="__main__": main()

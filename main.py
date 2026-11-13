import os, json, math, random, asyncio, subprocess, textwrap, time
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import edge_tts
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"output"; FRAMES=OUT/"frames"; AUDIO=OUT/"audio"
for p in (OUT,FRAMES,AUDIO): p.mkdir(parents=True,exist_ok=True)
VIDEO=OUT/"daily_story.mp4"; W,H,FPS=540,960,12
VOICE_A="ur-PK-UzmaNeural"; VOICE_B="ur-PK-AsadNeural"
FONTS="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

CAST=[
 ("Milo","لومڑی",(235,235,235),"fox"),("Pip","خرگوش",(225,225,225),"rabbit"),
 ("Zuzu","پرندہ",(245,245,245),"bird"),("Bolt","روبوٹ",(210,210,210),"robot"),
 ("Nori","ریچھ",(230,230,230),"bear"),("Kiki","بلی",(240,240,240),"cat"),
 ("Rolo","ریکون",(215,215,215),"raccoon"),("Tara","ہرن",(245,245,245),"deer"),
 ("Bobo","پینگوئن",(225,225,225),"penguin"),("Luma","چھوٹی ڈریگن",(235,235,235),"dragon"),
 ("Dodo","مینڈک",(220,220,220),"frog"),("Mimi","گلہری",(240,240,240),"squirrel")
]
PLOTS=[
 ("The Lost Star","گمشدہ ستارہ","ایک ننھا ستارہ آسمان سے گر کر جنگل میں آ گیا۔","چلو اسے واپس گھر پہنچاتے ہیں!","ستارہ میرے پاس ہے، مگر راستہ کہاں ہے؟","اسے پہاڑی کی چوٹی تک لے چلو۔","دونوں نے تیز ہوا اور اندھیرے کا مقابلہ کیا۔","اب ستارہ واپس آسمان میں چمکنے لگا!","A fallen star is found in a forest; two unlikely friends carry it up a windy hill and discover it can fly home."),
 ("The Last Cookie","آخری بسکٹ","آخری بسکٹ دیکھ کر دونوں کی آنکھیں چمک اٹھیں۔","یہ بسکٹ میرا ہے، میں نے پہلے دیکھا!","نہیں، میں نے پہلے سونگھا تھا!","بسکٹ اچانک لڑھکتا ہوا ڈھلوان سے نیچے گیا۔","دونوں اس کے پیچھے پھسلتے ہوئے بھاگے۔","آخر میں بسکٹ ٹوٹا تو دونوں نے آدھا آدھا بانٹ لیا۔","Two hungry friends race for the last cookie, chase it downhill, then split it when it breaks in half."),
 ("The Midnight Train","آدھی رات کی ٹرین","پرانے اسٹیشن پر ایک خالی ٹرین خود چل پڑی۔","رکو! میرا دوست ابھی اندر نہیں آیا!","میں آ رہا ہوں، دروازہ بند مت کرنا!","ایک نے چھلانگ لگا کر آخری ڈبہ پکڑ لیا۔","ٹرین سرنگ میں داخل ہوئی تو روشن جگنو راستہ دکھانے لگے۔","ٹرین انہیں جادوئی باغ میں لے آئی۔","A mysterious midnight train leaves the station; friends leap aboard and fireflies guide it to a hidden garden."),
 ("The Tiny Hero","ننھا ہیرو","بارش میں ایک ننھی چڑیا کا گھونسلا گر گیا۔","فکر مت کرو، ہم تمہاری مدد کریں گے۔","لیکن درخت بہت اونچا ہے!","ایک دوست نے دوسرے کو اپنے کندھوں پر اٹھایا۔","تیز ہوا نے شاخ ہلا دی مگر دونوں نے ہمت نہ ہاری۔","گھونسلا محفوظ ہوا اور چڑیا خوشی سے اڑ گئی۔","A nest falls in a storm; two friends work together to return it safely to a high branch."),
 ("The Magic Door","جادوئی دروازہ","پرانے گھر کی دیوار میں ایک چمکتا دروازہ کھلا۔","اس کے پیچھے کیا ہوگا؟","پتا نہیں، مگر ساتھ رہیں گے!","دروازہ انہیں برفیلے پہاڑ پر لے گیا۔","برفانی گولہ ان کے پیچھے لڑھکنے لگا۔","وہ باہر نکلے تو دروازہ ایک ننھے پالتو ڈریگن کا گھر نکلا۔","A glowing door opens to a snowy mountain; friends escape a rolling snowball and meet a tiny dragon."),
 ("The Runaway Balloon","اڑتا ہوا غبارہ","ایک سرخ غبارہ ننھے دوست کو ہوا میں لے گیا۔","مجھے نیچے اتارو!","میری دم پکڑو، میں تمہیں بچاتا ہوں!","دوسرا دوست پتنگ کی ڈور پکڑ کر اوپر چڑھا۔","بادلوں میں دونوں نے ایک دوسرے کا ہاتھ تھام لیا۔","وہ نرم گھاس پر اترے اور غبارہ ایک بچے کو دے دیا۔","A balloon lifts a little friend into the clouds; the other climbs a kite string to rescue them."),
 ("The River Mystery","دریا کا راز","دریا کے بیچ ایک چھوٹا سا چراغ تیر رہا تھا۔","یہ چراغ یہاں کیسے آیا؟","شاید کسی کو ہماری مدد چاہیے!","دونوں لکڑی کے تختے پر بیٹھ کر دریا پار گئے۔","پانی کے نیچے روشنیوں نے خفیہ راستہ دکھایا۔","چراغ ایک ننھی کچھوے کا تھا جو گھر بھول گئی تھی۔","A floating lantern leads friends across a river to a lost baby turtle."),
 ("The Great Mix-Up","الٹی سیدھی دنیا","صبح اٹھے تو سب چیزیں الٹی ہو چکی تھیں۔","میرا گھر چھت پر کیوں ہے؟","اور درخت زمین کے اندر کیوں اگ رہے ہیں؟","دونوں نے عجیب مشین کا بٹن دبایا۔","مشین تیزی سے گھومنے لگی اور چیزیں اڑنے لگیں۔","سب ٹھیک ہوا، مگر ان کے جوتے اب بھی الٹے تھے!","A strange machine flips the world upside down; friends fix it, but their shoes remain backwards.")
]

def font(sz,bold=False):
 p="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else FONTS
 try:return ImageFont.truetype(p,sz)
 except:return ImageFont.load_default()

BG_CACHE={}
def background(scene, seed):
 key=scene
 if key in BG_CACHE: return BG_CACHE[key].copy()
 top=(10,12,15); bot=(75,78,81)
 grad=Image.new("RGB",(1,H))
 grad.putdata([tuple(int(top[k]*(1-y/(H-1))+bot[k]*(y/(H-1))) for k in range(3)) for y in range(H)])
 im=grad.resize((W,H))
 d=ImageDraw.Draw(im)
 if scene%6==0:
  d.ellipse((360,90,500,230),fill=(160,160,155))
 if scene%6 in (0,1):
  for x in range(-20,W,90):
   d.polygon([(x,650),(x+45,380+(x%130)),(x+105,650)],fill=(38,41,44))
   d.rectangle((x+39,620,x+55,840),fill=(25,27,29))
 elif scene%6 in (2,3):
  for x in range(0,W,75):
   h=220+(x*7%230); d.rectangle((x,690-h,x+48,690),fill=(31,34,37))
   for yy in range(710-h,680,48): d.rectangle((x+12,yy,x+23,yy+20),fill=(115,117,115))
 else:
  d.rectangle((0,650,W,H),fill=(27,31,34))
  for x in range(0,W,70): d.ellipse((x,620,x+100,710),fill=(42,47,48))
 for n in range(75):
  x=(n*73+scene*29)%W; y=(n*137+scene*41)%H
  d.point((x,y),fill=(95,96,95))
 BG_CACHE[key]=im.copy()
 return im

def character_layer(kind, x, y, scale, facing=1, mood=0):
 layer=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(layer)
 s=scale; cx=x; cy=y
 # body and head shapes
 body=(cx-42*s,cy-4*s,cx+42*s,cy+100*s)
 head=(cx-52*s,cy-92*s,cx+52*s,cy+10*s)
 fill=(205,207,207,255); dark=(95,98,99,255); gold=(255,210,65,255)
 d.ellipse(body,fill=fill,outline=gold,width=max(2,int(5*s)))
 d.ellipse(head,fill=fill,outline=gold,width=max(2,int(5*s)))
 # species silhouette
 if kind in ("rabbit","deer","cat","fox","squirrel","dragon"):
  ears=2 if kind not in ("fox","squirrel") else 2
  for side in (-1,1):
   ex=cx+side*27*s
   if kind=="rabbit": d.ellipse((ex-13*s,cy-155*s,ex+13*s,cy-68*s),fill=fill,outline=gold,width=max(2,int(5*s)))
   elif kind=="deer": d.line((ex,cy-75*s,ex+side*18*s,cy-155*s,ex+side*33*s,cy-145*s),fill=gold,width=max(3,int(6*s)))
   elif kind=="dragon": d.polygon([(ex-12*s,cy-80*s),(ex,cy-135*s),(ex+15*s,cy-80*s)],fill=fill,outline=gold)
   else: d.polygon([(ex-15*s,cy-70*s),(ex,cy-140*s),(ex+18*s,cy-70*s)],fill=fill,outline=gold)
 if kind=="bird":
  d.polygon([(cx+40*s,cy-55*s),(cx+85*s,cy-40*s),(cx+40*s,cy-27*s)],fill=gold)
 if kind=="robot":
  d.rectangle((cx-43*s,cy-90*s,cx+43*s,cy+8*s),fill=fill,outline=gold,width=max(2,int(5*s)))
  d.line((cx,cy-92*s,cx,cy-125*s),fill=gold,width=max(3,int(5*s)))
 if kind=="penguin":
  d.ellipse((cx-25*s,cy+8*s,cx+25*s,cy+83*s),fill=(65,68,70,255),outline=gold,width=3)
 if kind=="frog":
  d.ellipse((cx-46*s,cy-115*s,cx-8*s,cy-75*s),fill=fill,outline=gold,width=3)
  d.ellipse((cx+8*s,cy-115*s,cx+46*s,cy-75*s),fill=fill,outline=gold,width=3)
 # tail/wings
 if kind in ("fox","cat","raccoon","squirrel","dragon"):
  d.arc((cx+22*s,cy+30*s,cx+115*s,cy+125*s),180,330,fill=gold,width=max(4,int(8*s)))
 if kind in ("bird","penguin"):
  d.polygon([(cx-32*s,cy+10*s),(cx-85*s,cy+55*s),(cx-25*s,cy+55*s)],fill=fill,outline=gold)
 # face
 eye_y=cy-54*s
 for side in (-1,1):
  ex=cx+side*19*s
  d.ellipse((ex-6*s,eye_y-7*s,ex+6*s,eye_y+8*s),fill=(20,22,23,255))
 d.arc((cx-18*s,cy-40*s,cx+18*s,cy-18*s),10,170,fill=(30,30,30,255),width=max(2,int(3*s)))
 # arms and legs; pose varies with mood
 swing=math.sin(mood*math.pi*2)*24*s
 d.line((cx-25*s,cy+28*s,cx-65*s,cy+65*s+swing),fill=gold,width=max(4,int(9*s)))
 d.line((cx+25*s,cy+28*s,cx+65*s,cy+65*s-swing),fill=gold,width=max(4,int(9*s)))
 d.line((cx-18*s,cy+88*s,cx-35*s,cy+135*s),fill=gold,width=max(4,int(10*s)))
 d.line((cx+18*s,cy+88*s,cx+35*s,cy+135*s),fill=gold,width=max(4,int(10*s)))
 # glow outline
 alpha=layer.getchannel("A")
 glow=alpha.filter(ImageFilter.MaxFilter(19)).filter(ImageFilter.GaussianBlur(13))
 halo=Image.new("RGBA",(W,H),(255,194,35,0)); halo.putalpha(glow.point(lambda a:int(a*.55)))
 return Image.alpha_composite(halo,layer)

def draw_frame(scene_no, frame_no, frames, cast, action, seed):
 random.seed(seed+frame_no)
 im=background(scene_no,seed); d=ImageDraw.Draw(im)
 t=frame_no/max(1,frames-1); phase=t*math.tau
 # camera framing changes across shots
 if scene_no%3==0:
  scale1,scale2=1.05,.72; y1,y2=560,670
 elif scene_no%3==1:
  scale1,scale2=.82,1.0; y1,y2=620,580
 else:
  scale1,scale2=.9,.9; y1,y2=570,620
 x1=int(145+45*math.sin(phase*1.2)); x2=int(395-55*math.sin(phase*1.1))
 jump=abs(math.sin(phase*2))*45
 if action in ("run","chase","escape"): x1=int(85+300*t); x2=int(445-260*t)
 elif action=="fall": y1+=int(100*t); y2+=int(120*t)
 elif action=="jump": y1-=int(jump); y2-=int(jump*1.4)
 elif action=="team": x1+=int(25*math.sin(phase)); x2-=int(25*math.sin(phase))
 # ground and cinematic light
 d.ellipse((15,790,525,900),fill=(18,20,22))
 a=character_layer(cast[0][3],x1,y1,scale1,1,t)
 b=character_layer(cast[1][3],x2,y2,scale2,-1,t+.25)
 im=Image.alpha_composite(im.convert("RGBA"),a); im=Image.alpha_composite(im,b)
 d=ImageDraw.Draw(im)
 # animated story object / glowing clue
 ox=int(270+120*math.sin(phase*1.5)); oy=int(420+45*math.cos(phase*2))
 d.ellipse((ox-15,oy-15,ox+15,oy+15),fill=(255,210,70),outline=(255,245,190),width=3)
 # shot number and tiny title slate
 d.rounded_rectangle((24,30,240,75),radius=15,fill=(0,0,0,150),outline=(255,205,55),width=2)
 d.text((40,43),f"SCENE {scene_no}/6",font=font(18,True),fill=(255,222,125))
 return im.convert("RGB")

def run(cmd):
 subprocess.run(cmd,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)

async def make_voice(text,dest,voice):
 await edge_tts.Communicate(text=text,voice=voice,rate="-2%").save(str(dest))
 if not dest.exists() or dest.stat().st_size<500: raise RuntimeError("Voice generation failed: "+dest.name)

def stamp(s):
 ms=int(s*1000); h,ms=divmod(ms,3600000); m,ms=divmod(ms,60000); sec,ms=divmod(ms,1000)
 return f"{h:02}:{m:02}:{sec:02},{ms:03}"

def wrap_caption(s,max_chars=34):
 words=s.split(); lines=[]; line=""
 for w in words:
  test=(line+" "+w).strip()
  if len(test)>max_chars and line: lines.append(line); line=w
  else: line=test
 if line: lines.append(line)
 return "\\N".join(lines[:2])

def render_scene(scene_no, duration, cast, action, seed):
 frames=max(24,int(duration*FPS)); pattern=FRAMES/f"s{scene_no}_%04d.jpg"
 for f in range(frames):
  im=draw_frame(scene_no,f,frames,cast,action,seed)
  im.save(str(FRAMES/f"s{scene_no}_{f+1:04d}.jpg"),quality=82,optimize=True)
 clip=OUT/f"clip_{scene_no}.mp4"
 run(["ffmpeg","-y","-loglevel","error","-framerate",str(FPS),"-i",str(pattern),"-c:v","libx264","-preset","ultrafast","-crf","25","-pix_fmt","yuv420p",str(clip)])
 for p in FRAMES.glob(f"s{scene_no}_*.jpg"): p.unlink()
 return clip

def upload(video,title,description):
 client=json.loads(os.environ["YOUTUBE_CLIENT_JSON"]); info=client.get("installed") or client.get("web")
 creds=Credentials(None,refresh_token=os.environ["YOUTUBE_REFRESH_TOKEN"],token_uri=info.get("token_uri","https://oauth2.googleapis.com/token"),client_id=info["client_id"],client_secret=info["client_secret"],scopes=["https://www.googleapis.com/auth/youtube.upload"])
 yt=build("youtube","v3",credentials=creds)
 req=yt.videos().insert(part="snippet,status",body={"snippet":{"title":title[:100],"description":description,"tags":["Urdu cartoon","animated story","shorts","funny story","cinematic animation"],"categoryId":"1"},"status":{"privacyStatus":"private","selfDeclaredMadeForKids":False}},media_body=MediaFileUpload(str(video),mimetype="video/mp4",resumable=True))
 response=None
 while response is None:
  status,response=req.next_chunk()
  if status: print("Upload:",int(status.progress()*100),"%",flush=True)
 print("PRIVATE VIDEO:", "https://www.youtube.com/watch?v="+response["id"],flush=True)

def main():
 if not os.getenv("YOUTUBE_CLIENT_JSON") or not os.getenv("YOUTUBE_REFRESH_TOKEN"):
  raise RuntimeError("YouTube secrets are missing; add the existing GitHub secrets.")
 day=datetime.now(timezone.utc).date().toordinal()
 override=os.getenv("STORY_INDEX")
 idx=int(override) if override is not None else day
 plot=PLOTS[idx%len(PLOTS)]
 rng=random.Random(day)
 cast=[CAST[(idx*2)%len(CAST)],CAST[(idx*2+5)%len(CAST)]]
 # avoid identical character species
 if cast[0][3]==cast[1][3]: cast[1]=CAST[(idx*2+6)%len(CAST)]
 title,urdu_title,*lines,summary=plot
 actions=["discover","team","run","jump","fall","team"]
 scenes=[
  (0,lines[0],"discover"),(1,lines[1],"team"),(0,lines[2],"run"),
  (1,lines[3],"jump"),(0,lines[4],"fall"),(1,lines[5],"team")
 ]
 print("NEW STORY:",title,"CAST:",cast[0][0],cast[1][0],flush=True)
 for folder in (FRAMES,AUDIO):
  for p in folder.glob("*"):
   if p.is_file(): p.unlink()
 clips=[]; voice_files=[]; subtitles=[]; offset=0.0
 for i,(speaker,dialogue,action) in enumerate(scenes,1):
  voice=AUDIO/f"voice_{i}.mp3"; asyncio.run(make_voice(dialogue,voice,VOICE_A if speaker==0 else VOICE_B)); voice_files.append(voice)
  # fixed 3.2s shots; voices trimmed to shot length in final mix
  duration=3.2
  clip=render_scene(i,duration,cast,action,day+i*17); clips.append(clip)
  # Urdu subtitles match the exact dialogue spoken in this shot.
  subtitles.append(f"{i}\\n{stamp(offset)} --> {stamp(offset+duration)}\\n{wrap_caption(dialogue,30)}\\n"); offset+=duration
 (OUT/"subtitles.srt").write_text("\n".join(subtitles),encoding="utf-8")
 (OUT/"clips.txt").write_text("\n".join("file '"+str(c.resolve())+"'" for c in clips),encoding="utf-8")
 (OUT/"audio.txt").write_text("\n".join("file '"+str(v.resolve())+"'" for v in voice_files),encoding="utf-8")
 run(["ffmpeg","-y","-loglevel","error","-f","concat","-safe","0","-i",str(OUT/"clips.txt"),"-c","copy",str(OUT/"silent.mp4")])
 run(["ffmpeg","-y","-loglevel","error","-f","concat","-safe","0","-i",str(OUT/"audio.txt"),"-c:a","libmp3lame","-q:a","4",str(OUT/"voices.mp3")])
 subtitle=str((OUT/"subtitles.srt").resolve()).replace("\\","/").replace(":","\\:")
 # concise two-line subtitles, quiet original ambient music bed
 run(["ffmpeg","-y","-loglevel","error","-i",str(OUT/"silent.mp4"),"-i",str(OUT/"voices.mp3"),"-f","lavfi","-i","anoisesrc=color=pink:sample_rate=44100:amplitude=0.006","-vf",f"subtitles='{subtitle}':force_style='FontName=DejaVu Sans,FontSize=15,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=1,Alignment=2,MarginV=85'","-filter_complex","[1:a]volume=1.0[v];[2:a]lowpass=f=700,volume=0.08[m];[v][m]amix=inputs=2:duration=first[a]","-map","0:v","-map","[a]","-c:v","libx264","-preset","veryfast","-crf","23","-c:a","aac","-shortest","-movflags","+faststart",str(VIDEO)])
 if not VIDEO.exists() or VIDEO.stat().st_size<10000: raise RuntimeError("Final video failed.")
 desc=f"{summary}\n\nA brand-new Urdu animated mini story featuring {cast[0][0]} and {cast[1][0]}. New characters and a new story every episode.\n\n#UrduStory #AnimatedShorts #Cartoon #Shorts"
 upload(VIDEO,title+" | Urdu Animated Story #Shorts",desc)

if __name__=="__main__": main()

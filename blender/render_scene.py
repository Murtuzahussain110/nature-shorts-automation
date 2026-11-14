import bpy, math, sys
from pathlib import Path
from mathutils import Vector

def get_args():
    a=sys.argv[sys.argv.index("--")+1:]
    if len(a)<7: raise RuntimeError("Expected scene,duration,species1,species2,action,seed,output")
    return int(a[0]),float(a[1]),a[2],a[3],a[4],int(a[5]),Path(a[6])

def material(name,color,emission=0):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    p=m.node_tree.nodes.get("Principled BSDF"); p.inputs["Base Color"].default_value=(*color,1); p.inputs["Roughness"].default_value=.55
    if emission:
        if "Emission Color" in p.inputs: p.inputs["Emission Color"].default_value=(*color,1)
        if "Emission Strength" in p.inputs: p.inputs["Emission Strength"].default_value=emission
    return m

def ball(name,loc,scale,mat,parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,location=loc)
    o=bpy.context.object; o.name=name; o.scale=scale; o.data.materials.append(mat); bpy.ops.object.shade_smooth()
    if parent: o.parent=parent; o.location=loc
    return o

COLORS={"fox":((.95,.32,.08),(.98,.72,.42)),"rabbit":((.82,.70,.80),(.98,.9,.96)),"bird":((.08,.48,.82),(1,.72,.12)),"robot":((.30,.65,.72),(.98,.68,.12)),"bear":((.46,.25,.13),(.85,.65,.44)),"cat":((.78,.58,.32),(.98,.88,.7)),"raccoon":((.35,.4,.5),(.82,.85,.9)),"deer":((.65,.4,.2),(.94,.76,.5)),"penguin":((.14,.22,.32),(.96,.9,.75)),"dragon":((.12,.62,.42),(.98,.52,.24)),"frog":((.28,.7,.22),(.9,.94,.35)),"squirrel":((.65,.3,.12),(.94,.66,.38))}

def make_character(kind,x,scale,label):
    c,b=COLORS.get(kind,COLORS["fox"]); coat=material(label+" coat",c); belly=material(label+" belly",b); dark=material(label+" details",tuple(v*.4 for v in c)); white=material("eye white",(1,1,1)); black=material("pupil",(.015,.02,.03))
    root=bpy.data.objects.new(label+" animated root",None); bpy.context.collection.objects.link(root); root.location=(x,0,0)
    s=scale
    ball(label+" body",(0,0,1.05*s),(.52*s,.38*s,.72*s),coat,root)
    ball(label+" belly",(0,-.34*s,1*s),(.34*s,.055*s,.46*s),belly,root)
    ball(label+" head",(0,-.02*s,2.05*s),(.62*s,.5*s,.58*s),coat,root)
    ball(label+" muzzle",(0,-.48*s,1.91*s),(.29*s,.13*s,.17*s),belly,root)
    ball(label+" nose",(0,-.60*s,1.98*s),(.07*s,.04*s,.05*s),dark,root)
    for side in (-1,1):
        ball(label+" eye",(side*.22*s,-.45*s,2.18*s),(.13*s,.07*s,.15*s),white,root)
        ball(label+" pupil",(side*.22*s,-.51*s,2.18*s),(.055*s,.035*s,.08*s),black,root)
        ear=ball(label+" ear",(side*.39*s,-.01*s,2.55*s),(.17*s,.13*s,.30*s),coat,root)
        if kind=="rabbit": ear.scale.z=.55
    if kind in ("fox","cat","raccoon","squirrel","dragon"):
        tail=ball(label+" tail",(.56*s,.16*s,.78*s),(.20*s,.23*s,.68*s),coat,root); tail.rotation_euler[1]=-.8
    if kind in ("bird","penguin"):
        ball(label+" beak",(0,-.59*s,2*s),(.15*s,.14*s,.12*s),belly,root)
        for side in (-1,1): ball(label+" wing",(side*.48*s,-.05*s,1.2*s),(.14*s,.18*s,.38*s),dark,root)
    arms=[]; legs=[]
    for side in (-1,1):
        arm=ball(label+" arm",(side*.57*s,-.02*s,1.28*s),(.15*s,.16*s,.40*s),coat,root); arm.rotation_euler[1]=side*.4; arms.append(arm)
        leg=ball(label+" leg",(side*.23*s,-.02*s,.36*s),(.17*s,.19*s,.36*s),dark,root); legs.append(leg)
    return root,arms,legs

def animate(parts,sc,action,side):
    root,arms,legs=parts; end=sc.frame_end
    for f in (1,end):
        t=(f-1)/max(1,end-1)
        if action in ("run","chase","escape"): root.location.x=side*(1.2-2.4*t)
        else: root.location.x=side*(1.05+.16*math.sin(t*math.tau))
        root.location.z=(.55*abs(math.sin(t*math.pi)) if action=="jump" else .10*math.sin(t*math.tau*2))
        if action=="fall": root.location.z=-.55*t
        root.keyframe_insert(data_path="location",frame=f)
    for i,o in enumerate(arms):
        for f in (1,end//2,end):
            t=(f-1)/max(1,end-1); o.rotation_euler[1]=(-1 if i==0 else 1)*(.35+.65*math.sin(t*math.tau*2)); o.keyframe_insert(data_path="rotation_euler",frame=f)

def build(scene_no,duration,a,b,action,out):
    bpy.ops.object.select_all(action="SELECT"); bpy.ops.object.delete(use_global=False)
    sc=bpy.context.scene; sc.render.engine="BLENDER_EEVEE"; sc.eevee.taa_render_samples=16
    sc.render.resolution_x=540; sc.render.resolution_y=960; sc.render.resolution_percentage=100; sc.render.fps=12
    sc.frame_start=1; sc.frame_end=max(24,int(duration*12))
    sc.render.image_settings.file_format="FFMPEG"; sc.render.ffmpeg.format="MPEG4"; sc.render.ffmpeg.codec="H264"; sc.render.ffmpeg.constant_rate_factor="MEDIUM"; sc.render.filepath=str(out)
    sc.view_settings.view_transform="Standard"; sc.view_settings.look="Medium High Contrast"
    world=bpy.data.worlds.new("storybook night") if not bpy.data.worlds else bpy.data.worlds[0]; sc.world=world; world.use_nodes=True
    world.node_tree.nodes["Background"].inputs[0].default_value=(.025,.045,.11,1); world.node_tree.nodes["Background"].inputs[1].default_value=.5
    ground=material("deep teal ground",(.035,.16,.18)); bark=material("tree bark",(.19,.09,.055)); leaves=material("forest canopy",(.035,.22,.15)); hill=material("distant hills",(.07,.29,.25)); magic=material("glowing golden story clue",(1,.55,.08),2)
    bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.08)); bpy.context.object.data.materials.append(ground)
    for i in range(7):
        x=(i-3)*2.2
        bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=.15,depth=2,location=(x,1.4,1)); bpy.context.object.data.materials.append(bark)
        ball("rounded tree canopy",(x,1.4,2.3),(.85,.65,1),leaves)
    for i in range(5): ball("rolling hill",((i-2)*2.8,2,.0),(2.2,.65,.65),hill)
    orb=ball("magic story orb",(0,-.4,3.8),(.22,.22,.22),magic)
    for f,x in ((1,-.7),(sc.frame_end,.7)):
        orb.location.x=x; orb.keyframe_insert(data_path="location",frame=f)
    bpy.ops.object.camera_add(location=(0,-14,4.8)); cam=bpy.context.object
    target=Vector((0,0,2.45)); cam.rotation_euler=(target-cam.location).to_track_quat("-Z","Y").to_euler(); cam.data.type="ORTHO"; cam.data.ortho_scale=7.7; sc.camera=cam
    bpy.ops.object.light_add(type="AREA",location=(-4,-6,8)); bpy.context.object.data.energy=950; bpy.context.object.data.shape="DISK"; bpy.context.object.data.size=6
    bpy.ops.object.light_add(type="AREA",location=(4,1,6)); bpy.context.object.data.energy=500; bpy.context.object.data.size=5
    left=make_character(a,-1.05,.78,"hero one"); right=make_character(b,1.05,.72,"hero two")
    animate(left,sc,action,-1); animate(right,sc,action,1)
    sc.frame_set(1); out.parent.mkdir(parents=True,exist_ok=True); bpy.ops.render.render(animation=True)

if __name__=="__main__":
    n,d,a,b,action,seed,out=get_args(); build(n,d,a,b,action,out)

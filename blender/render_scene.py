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
    c,b=COLORS.get(kind,COLORS["fox"])
    coat=material(label+" coat",c); belly=material(label+" belly",b)
    dark=material(label+" details",tuple(v*.35 for v in c))
    white=material(label+" eye whites",(1.0,.97,.88)); black=material(label+" pupils",(.008,.012,.02))
    pink=material(label+" inner ears",(.95,.38,.48))
    root=bpy.data.objects.new(label+" animated root",None); bpy.context.collection.objects.link(root); root.location=(x,0,0)
    s=scale
    # Rounded pear-shaped body, chest and oversized expressive head
    ball(label+" body",(0,0,1.0*s),(.55*s,.43*s,.78*s),coat,root)
    ball(label+" chest",(0,-.365*s,1.0*s),(.37*s,.075*s,.49*s),belly,root)
    ball(label+" head",(0,-.035*s,2.02*s),(.69*s,.53*s,.63*s),coat,root)
    ball(label+" muzzle left",(-.13*s,-.505*s,1.88*s),(.22*s,.16*s,.17*s),belly,root)
    ball(label+" muzzle right",(.13*s,-.505*s,1.88*s),(.22*s,.16*s,.17*s),belly,root)
    ball(label+" nose",(0,-.65*s,1.97*s),(.09*s,.055*s,.065*s),dark,root)
    # Species-specific silhouette
    if kind=="rabbit":
        for side in (-1,1):
            ear=ball(label+" long ear",(side*.32*s,.0,2.78*s),(.19*s,.15*s,.58*s),coat,root)
            ear.rotation_euler[1]=side*-.12
            ball(label+" pink inner ear",(side*.32*s,-.135*s,2.78*s),(.105*s,.025*s,.40*s),pink,root)
    elif kind in ("fox","cat","squirrel","dragon"):
        for side in (-1,1):
            ear=ball(label+" pointed ear",(side*.43*s,-.005*s,2.58*s),(.24*s,.16*s,.38*s),coat,root)
            ear.rotation_euler[1]=side*-.28
            if kind=="fox":
                ball(label+" ear inset",(side*.43*s,-.15*s,2.57*s),(.12*s,.025*s,.23*s),belly,root)
    elif kind=="deer":
        for side in (-1,1):
            antler=ball(label+" antler base",(side*.36*s,.0,2.67*s),(.07*s,.07*s,.32*s),dark,root)
            antler.rotation_euler[1]=side*-.35
            ball(label+" antler tine",(side*.52*s,.0,2.85*s),(.06*s,.06*s,.22*s),dark,root)
    elif kind=="bear":
        for side in (-1,1): ball(label+" round ear",(side*.53*s,-.01*s,2.42*s),(.22*s,.17*s,.23*s),coat,root)
    elif kind=="bird":
        ball(label+" beak",(0,-.69*s,2.0*s),(.19*s,.18*s,.15*s),belly,root)
        for side in (-1,1):
            wing=ball(label+" wing",(side*.55*s,-.02*s,1.25*s),(.20*s,.20*s,.43*s),dark,root)
            wing.rotation_euler[1]=side*.35
    elif kind=="penguin":
        ball(label+" white belly",(0,-.42*s,1.05*s),(.38*s,.075*s,.56*s),belly,root)
        ball(label+" beak",(0,-.67*s,1.98*s),(.14*s,.15*s,.12*s),belly,root)
        for side in (-1,1): ball(label+" flipper",(side*.56*s,-.04*s,1.25*s),(.16*s,.18*s,.48*s),dark,root)
    elif kind=="frog":
        for side in (-1,1):
            ball(label+" raised eye",(side*.39*s,-.30*s,2.48*s),(.23*s,.22*s,.25*s),coat,root)
    elif kind=="robot":
        # A friendly rounded robot face with a chest badge
        ball(label+" chest light",(0,-.45*s,1.25*s),(.16*s,.05*s,.16*s),pink,root)
    # Eyes with highlights and brows for readable expressions
    for side in (-1,1):
        ex=side*.245*s
        ball(label+" eye socket",(ex,-.49*s,2.15*s),(.19*s,.075*s,.22*s),dark,root)
        ball(label+" eye",(ex,-.555*s,2.16*s),(.145*s,.055*s,.17*s),white,root)
        ball(label+" pupil",(ex-side*.025*s,-.603*s,2.15*s),(.075*s,.035*s,.105*s),black,root)
        ball(label+" eye sparkle",(ex-.025*s,-.635*s,2.20*s),(.028*s,.018*s,.035*s),white,root)
        brow=ball(label+" eyebrow",(ex,-.53*s,2.40*s),(.16*s,.045*s,.045*s),dark,root)
        brow.rotation_euler[1]=side*.12
    # Short arms, rounded paws and visible feet
    arms=[]; legs=[]
    for side in (-1,1):
        arm=ball(label+" upper arm",(side*.58*s,-.03*s,1.30*s),(.17*s,.18*s,.38*s),coat,root)
        arm.rotation_euler[1]=side*.45; arms.append(arm)
        ball(label+" paw",(side*.68*s,-.10*s,.98*s),(.19*s,.17*s,.18*s),belly,root)
        leg=ball(label+" leg",(side*.25*s,-.02*s,.34*s),(.19*s,.22*s,.34*s),dark,root); legs.append(leg)
        ball(label+" foot",(side*.27*s,-.16*s,.13*s),(.25*s,.34*s,.14*s),dark,root)
    if kind in ("fox","cat","raccoon","squirrel","dragon"):
        tail=ball(label+" fluffy tail",(.58*s,.22*s,.75*s),(.24*s,.25*s,.72*s),coat,root)
        tail.rotation_euler[1]=-.85
        if kind in ("fox","squirrel"): ball(label+" tail tip",(.92*s,.18*s,.43*s),(.23*s,.24*s,.23*s),belly,root)
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
    sc=bpy.context.scene; sc.render.engine="BLENDER_EEVEE"; sc.eevee.taa_render_samples=32
    sc.render.resolution_x=540; sc.render.resolution_y=960; sc.render.resolution_percentage=100; sc.render.fps=12
    sc.frame_start=1; sc.frame_end=max(24,int(duration*12))
    sc.render.image_settings.file_format="PNG"; sc.render.image_settings.color_mode="RGB"; sc.render.filepath=str(out.parent / (out.stem + "_frame_"))
    sc.view_settings.view_transform="Standard"; sc.view_settings.look="AgX - Medium High Contrast"
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
    bpy.ops.object.light_add(type="AREA",location=(-4,-6,8)); bpy.context.object.data.energy=1200; bpy.context.object.data.shape="DISK"; bpy.context.object.data.size=6
    bpy.ops.object.light_add(type="AREA",location=(4,1,6)); bpy.context.object.data.energy=700; bpy.context.object.data.size=5
    bpy.ops.object.light_add(type="AREA",location=(0,-4,3)); bpy.context.object.data.energy=180; bpy.context.object.data.size=3
    left=make_character(a,-1.05,.78,"hero one"); right=make_character(b,1.05,.72,"hero two")
    animate(left,sc,action,-1); animate(right,sc,action,1)
    sc.frame_set(1); out.parent.mkdir(parents=True,exist_ok=True); bpy.ops.render.render(animation=True)

if __name__=="__main__":
    n,d,a,b,action,seed,out=get_args(); build(n,d,a,b,action,out)

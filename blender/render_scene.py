import bpy
import math
import sys
import subprocess
from pathlib import Path
from mathutils import Vector

# Usage: blender -b --python blender/render_scene.py -- duration scene_no story_index output_path
args = sys.argv[sys.argv.index("--") + 1:]
duration = float(args[0])
scene_no = int(args[1])
story_index = int(args[2])
output_path = args[3]

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

def mat(name, color, rough=0.72, metallic=0.0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    bs = m.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value = (*color, 1)
    bs.inputs["Roughness"].default_value = rough
    bs.inputs["Metallic"].default_value = metallic
    return m

gray = mat("Tom blue gray fur", (0.27,0.32,0.39))
belly = mat("Tom muzzle and belly", (0.78,0.78,0.73))
pink = mat("Ear pink", (0.85,0.43,0.48))
black = mat("Eyes nose pupils", (0.018,0.022,0.03), 0.3)
white = mat("Eye white", (0.96,0.96,0.90), 0.25)
brown = mat("Jerry warm brown", (0.43,0.22,0.105))
tan = mat("Jerry muzzle", (0.82,0.61,0.39))
green = mat("Grass", (0.10,0.28,0.16))
bark = mat("Tree bark", (0.20,0.105,0.055))
leaf = mat("Tree leaves", (0.10,0.31,0.16))
gold = mat("Cheese gold", (1.0,0.57,0.06))
blue = mat("Sky", (0.28,0.55,0.72))
def assign(obj, material):
    obj.data.materials.append(material)
    return obj

def uv(name, loc, scale, material, parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=12, location=loc)
    o=bpy.context.object; o.name=name; o.scale=scale
    bpy.ops.object.shade_smooth(); assign(o,material)
    if parent: o.parent=parent; o.matrix_parent_inverse=parent.matrix_world.inverted()
    return o

def cone(name, loc, radius, depth, material, parent=None, rot=None):
    bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=radius, radius2=0, depth=depth, location=loc)
    o=bpy.context.object; o.name=name
    if rot: o.rotation_euler=rot
    assign(o,material)
    if parent: o.parent=parent; o.matrix_parent_inverse=parent.matrix_world.inverted()
    return o

def cylinder(name, loc, radius, depth, material, parent=None, rot=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=radius, depth=depth, location=loc)
    o=bpy.context.object; o.name=name
    if rot: o.rotation_euler=rot
    assign(o,material)
    if parent: o.parent=parent; o.matrix_parent_inverse=parent.matrix_world.inverted()
    return o

def make_tom():
    root=bpy.data.objects.new("TOM animated character root",None); bpy.context.collection.objects.link(root)
    uv("Tom torso",(0,0,1.05),(.48,.34,.68),gray,root)
    uv("Tom belly",(0,-.285,1.02),(.34,.075,.48),belly,root)
    uv("Tom head",(0,-.02,2.0),(.62,.48,.58),gray,root)
    uv("Tom muzzle",(.0,-.46,1.83),(.42,.16,.23),belly,root)
    uv("Tom nose",(0,-.62,1.91),(.105,.07,.075),pink,root)
    # upright pointed ears
    cone("Tom left ear",(-.43,-.02,2.65),.22,.62,gray,root, (0,-.12,0))
    cone("Tom right ear",(.43,-.02,2.65),.22,.62,gray,root, (0,.12,0))
    cone("Tom inner ear L",(-.43,-.205,2.62),.105,.40,pink,root, (0,-.12,0))
    cone("Tom inner ear R",(.43,-.205,2.62),.105,.40,pink,root, (0,.12,0))
    for x in (-.22,.22):
        uv("Tom eye",(x,-.435,2.12),(.16,.08,.22),white,root)
        uv("Tom pupil",(x,-.505,2.12),(.055,.035,.105),black,root)
    # arms and legs are separate pivots, animated below
    for side in (-1,1):
        arm=bpy.data.objects.new("Tom arm pivot",None); bpy.context.collection.objects.link(arm); arm.parent=root; arm.location=(side*.40,0,1.45)
        cylinder("Tom arm",(side*.55,-.02,1.15),.13,.72,gray,arm,(0,side*.18,0))
        uv("Tom paw",(side*.56,-.04,.77),(.19,.16,.14),belly,arm)
        leg=bpy.data.objects.new("Tom leg pivot",None); bpy.context.collection.objects.link(leg); leg.parent=root; leg.location=(side*.22,0,.52)
        cylinder("Tom leg",(side*.23,0,.23),.16,.58,gray,leg,(0,side*.10,0))
        uv("Tom foot",(side*.25,-.13,-.06),(.27,.34,.13),belly,leg)
    tail=uv("Tom tail",(.52,.18,.75),(.58,.12,.13),gray,root); tail.rotation_euler[1]=-.45
    return root

def make_jerry():
    root=bpy.data.objects.new("JERRY animated character root",None); bpy.context.collection.objects.link(root)
    uv("Jerry body",(0,0,.72),(.30,.25,.48),brown,root)
    uv("Jerry head",(0,-.02,1.42),(.39,.32,.39),brown,root)
    uv("Jerry muzzle",(0,-.31,1.30),(.25,.12,.15),tan,root)
    uv("Jerry nose",(0,-.42,1.36),(.055,.035,.045),black,root)
    for x in (-.30,.30):
        uv("Jerry big ear",(x,-.01,1.76),(.20,.12,.24),brown,root)
        uv("Jerry pink ear",(x,-.12,1.76),(.12,.035,.15),pink,root)
    for x in (-.13,.13):
        uv("Jerry eye",(x,-.29,1.52),(.09,.04,.12),white,root)
        uv("Jerry pupil",(x,-.33,1.52),(.035,.025,.07),black,root)
    for side in (-1,1):
        cylinder("Jerry arm",(side*.34,-.02,.92),.075,.42,tan,root,(0,side*.3,0))
        uv("Jerry hand",(side*.38,-.04,.69),(.11,.10,.10),tan,root)
        cylinder("Jerry leg",(side*.15,0,.25),.09,.38,brown,root,(0,side*.1,0))
        uv("Jerry foot",(side*.16,-.10,.06),(.16,.22,.08),tan,root)
    tail=uv("Jerry tail",(.20,.15,.35),(.46,.045,.05),brown,root); tail.rotation_euler[1]=-.25
    return root

# Bright, simple 3D cartoon set
bpy.ops.mesh.primitive_plane_add(size=200, location=(0,0,-.13)); assign(bpy.context.object,green)
for x in (-5,-3.8,3.8,5):
    cylinder("Forest tree trunk",(x,1.4,1.0),.22,2.2,bark)
    uv("Round tree crown",(x,1.4,2.35),(.85,.78,1.0),leaf)
for x in (-4.7,4.6):
    uv("Distant bush",(x,-.3,.35),(1.1,.65,.45),leaf)

tom=make_tom(); jerry=make_jerry()
tom.location=(-1.25,0,0); jerry.location=(1.2,-.1,0)
# Episode-specific 3D props, each with its own moving gag.
def animate_prop(obj, x_end=1.5, z_end=.4, spin=0.0):
    obj.keyframe_insert(data_path="location", frame=1)
    obj.keyframe_insert(data_path="rotation_euler", frame=1)
    obj.location.x=x_end; obj.location.z=z_end
    obj.rotation_euler.z=spin
    obj.keyframe_insert(data_path="location", frame=max(2,int(duration*12)))
    obj.keyframe_insert(data_path="rotation_euler", frame=max(2,int(duration*12)))

if story_index in (0,1,2,9):
    bpy.ops.mesh.primitive_cube_add(size=.7, location=(0,-.45,.42))
    prop=bpy.context.object; prop.name="Cheese prop"; prop.scale=(.52,.18,.34); assign(prop,gold)
    bevel=prop.modifiers.new("Soft cheese edges","BEVEL"); bevel.width=.12; bevel.segments=3
    animate_prop(prop, 1.55 if scene_no%2 else -1.55, .42, math.pi*.6)
elif story_index==3:
    uv("Floating red balloon",(0,-.5,2.2),(.42,.34,.48),mat("Balloon red",(0.9,.08,.12),.25))
    cylinder("Balloon string",(0,-.5,1.45),.018,1.15,white)
elif story_index==4:
    cylinder("Toy drum",(0,-.45,.65),.42,.38,mat("Drum red",(.72,.12,.12)))
    cylinder("Drum top",(0,-.45,.86),.40,.035,white)
elif story_index==5:
    cylinder("Fishing rod",(0,-.35,1.3),.035,2.1,bark,rot=(0,.1,.9))
    uv("Fishing float",(.7,-.45,.55),(.12,.12,.2),mat("Float red",(.9,.12,.08)))
elif story_index==6:
    uv("Golden bell",(0,-.5,.75),(.28,.25,.30),gold)
    cylinder("Bell clapper",(0,-.5,.43),.045,.18,black)
elif story_index==7:
    cylinder("Magic hat brim",(0,-.45,.42),.62,.12,black)
    cylinder("Magic hat crown",(0,-.45,.85),.38,.78,black)
    uv("Magic hat star",(.25,-.58,1.15),(.12,.04,.12),gold)
elif story_index==8:
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0,-.4,.48))
    cart=bpy.context.object; cart.name="Toy race car"; cart.scale=(.72,.42,.22); assign(cart,mat("Toy car red",(.82,.06,.08),.3))
    for wx in (-.48,.48):
        for wy in (-.28,.28):
            uv("Toy car wheel",(wx,wy,.22),(.16,.10,.16),black)
    animate_prop(cart,1.8,.48,math.pi*2)
# Camera: vertical 9:16 portrait composition
bpy.ops.object.camera_add(location=(0,-12,5.2))
cam=bpy.context.object
target=Vector((0,0,1.25)); direction=target- cam.location
cam.rotation_euler=direction.to_track_quat("-Z","Y").to_euler()
cam.data.type="ORTHO"; cam.data.ortho_scale=8.8
bpy.context.scene.camera=cam

# Soft studio key and fill lights
bpy.ops.object.light_add(type="AREA", location=(-4,-6,8))
key=bpy.context.object; key.data.energy=950; key.data.shape="DISK"; key.data.size=6
bpy.ops.object.light_add(type="AREA", location=(4,-3,4))
fill=bpy.context.object; fill.data.energy=450; fill.data.size=5
bpy.ops.object.light_add(type="AREA", location=(0,4,6))
rim=bpy.context.object; rim.data.energy=700; rim.data.size=4

scene=bpy.context.scene
available_engines = {item.identifier for item in scene.bl_rna.properties["render"].fixed_type.properties["engine"].enum_items}
if "BLENDER_EEVEE_NEXT" in available_engines:
    scene.render.engine = "BLENDER_EEVEE_NEXT"
elif "BLENDER_EEVEE" in available_engines:
    scene.render.engine = "BLENDER_EEVEE"
else:
    scene.render.engine = "CYCLES"
scene.render.resolution_x=720; scene.render.resolution_y=1280; scene.render.resolution_percentage=100
scene.render.fps=12
scene.frame_start=1; scene.frame_end=max(2,int(duration*12))
scene.render.image_settings.file_format="PNG"
scene.render.filepath=str(Path(output_path).with_suffix("")) + "_frame_"
scene.world.color=(.22,.22,.22)
scene.view_settings.view_transform="Standard"
scene.view_settings.look="Medium High Contrast"
scene.display.shading.light="STUDIO"

# Distinct animated action: chase, dodge, jump and reactions
end=scene.frame_end
for frame in (1, max(2,end//2), end):
    t=(frame-1)/max(1,end-1)
    # Tom lunges forward while Jerry darts across the foreground.
    tom.location.x=-1.3 + 1.0*math.sin(t*math.pi*1.4 + scene_no*.35)
    tom.location.z=.10*abs(math.sin(t*math.pi*3))
    tom.rotation_euler[1]=.10*math.sin(t*math.pi*4)
    tom.keyframe_insert(data_path="location",frame=frame)
    tom.keyframe_insert(data_path="rotation_euler",frame=frame)
    jerry.location.x=1.25 - 1.25*math.sin(t*math.pi*1.7 + .4)
    jerry.location.z=.32*abs(math.sin(t*math.pi*4))
    jerry.rotation_euler[1]=-.12*math.sin(t*math.pi*5)
    jerry.keyframe_insert(data_path="location",frame=frame)
    jerry.keyframe_insert(data_path="rotation_euler",frame=frame)
# Animate Tom's arm pivots to add visible running and reaction gestures.
for obj in list(bpy.data.objects):
    if "Tom arm pivot" in obj.name:
        obj.rotation_euler[1]=-.55
        obj.keyframe_insert(data_path="rotation_euler",frame=1)
        obj.rotation_euler[1]=.55
        obj.keyframe_insert(data_path="rotation_euler",frame=max(2,end//2))
        obj.rotation_euler[1]=-.55
        obj.keyframe_insert(data_path="rotation_euler",frame=end)
# Smooth animation interpolation on all animated objects.
for obj in list(bpy.data.objects):
    if obj.animation_data and obj.animation_data.action:
        for fc in obj.animation_data.action.fcurves:
            for kp in fc.keyframe_points: kp.interpolation="BEZIER"

scene.render.image_settings.color_mode="RGB"
scene.camera.data.lens=50
frame_prefix = str(Path(output_path).with_suffix("")) + "_frame_"
scene.render.filepath=frame_prefix
bpy.ops.render.render(animation=True)

# Blender 5 no longer exposes FFmpeg as an image output format.
# Render numbered PNG frames, then encode the scene clip with system FFmpeg.
subprocess.run([
    "ffmpeg", "-y", "-framerate", "12",
    "-i", frame_prefix + "%04d.png",
    "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
    "-pix_fmt", "yuv420p", "-movflags", "+faststart", output_path
], check=True)

for frame in Path(output_path).parent.glob(Path(frame_prefix).name + "*.png"):
    frame.unlink()

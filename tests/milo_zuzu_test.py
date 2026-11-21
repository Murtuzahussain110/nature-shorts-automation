import bpy, math, sys
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:]
out = args[0] if args else "output/milo_zuzu_test.mp4"
frames_dir = "output/frames"
import os
os.makedirs(frames_dir, exist_ok=True)
os.makedirs(os.path.dirname(out) or ".", exist_ok=True)

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

def material(name, color, rough=0.7):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*color, 1)
    m.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = rough
    return m

ORANGE = material("Milo golden orange fur", (0.95, 0.38, 0.055))
CREAM = material("Milo cream muzzle", (1.0, 0.82, 0.58))
GREEN = material("Milo green eyes", (0.12, 0.62, 0.30), 0.25)
PURPLE = material("Zuzu lavender fur", (0.53, 0.32, 0.78))
PINK = material("Zuzu inner ears", (0.98, 0.52, 0.70))
TEAL = material("Zuzu turquoise eyes", (0.08, 0.75, 0.72), 0.25)
DARK = material("Pupils and nose", (0.025, 0.02, 0.035), 0.2)
WHITE = material("Eye whites", (1.0, 0.98, 0.9), 0.2)
YELLOW = material("Yellow scarf", (1.0, 0.78, 0.08))
GRASS = material("Meadow floor", (0.12, 0.43, 0.22))
LEAF = material("Round trees", (0.12, 0.38, 0.19))
BROWN = material("Tree trunks", (0.28, 0.13, 0.07))
RED = material("Berry red", (0.85, 0.08, 0.12))

def parent_local(obj, root, loc, scale=None, rot=None):
    obj.parent = root
    obj.location = loc
    if scale: obj.scale = scale
    if rot: obj.rotation_euler = rot
    return obj

def sphere(name, root, loc, scale, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=16, location=(0,0,0))
    o = bpy.context.object
    o.name = name
    bpy.ops.object.shade_smooth()
    o.data.materials.append(mat)
    return parent_local(o, root, loc, scale)

def cone(name, root, loc, radius, depth, mat, rot=(0,0,0)):
    bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=radius, radius2=0, depth=depth, location=(0,0,0))
    o = bpy.context.object
    o.name = name
    o.data.materials.append(mat)
    return parent_local(o, root, loc, (1,1,1), rot)

def cylinder(name, root, loc, radius, depth, mat, rot=(0,0,0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=radius, depth=depth, location=(0,0,0))
    o = bpy.context.object
    o.name = name
    o.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    return parent_local(o, root, loc, (1,1,1), rot)

# Meadow and simple colorful background
bpy.ops.mesh.primitive_plane_add(size=200, location=(0,0,-0.12))
bpy.context.object.data.materials.append(GRASS)
for x, h in [(-4,2.2),(-3.2,2.8),(3.4,2.4),(4.4,2.0)]:
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=.18, depth=h, location=(x,1,h/2-.1))
    bpy.context.object.data.materials.append(BROWN)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=12, location=(x,1,h+.35))
    bpy.context.object.scale=(.8,.65,.85)
    bpy.context.object.data.materials.append(LEAF)
    bpy.ops.object.shade_smooth()

# Milo: original orange cat, green eyes, blue overalls
milo = bpy.data.objects.new("Milo character rig", None); bpy.context.collection.objects.link(milo)
sphere("Milo body",milo,(0,0,1.02),(.48,.34,.62),ORANGE)
sphere("Milo belly",milo,(0,-.29,1.0),(.31,.07,.43),CREAM)
sphere("Milo head",milo,(0,-.03,1.95),(.62,.48,.56),ORANGE)
sphere("Milo muzzle",milo,(0,-.46,1.77),(.37,.13,.20),CREAM)
sphere("Milo nose",milo,(0,-.58,1.82),(.075,.045,.06),PINK)
for x in (-.23,.23):
    sphere("Milo eye white",milo,(x,-.43,2.08),(.16,.07,.19),WHITE)
    sphere("Milo green iris",milo,(x,-.495,2.07),(.075,.035,.10),GREEN)
    sphere("Milo pupil",milo,(x,-.525,2.07),(.035,.02,.065),DARK)
cone("Milo left ear",milo,(-.42,-.02,2.55),.22,.62,ORANGE,(0,-.12,0))
cone("Milo right ear",milo,(.42,-.02,2.55),.22,.62,ORANGE,(0,.12,0))
# limbs are separate child objects so they can swing
milo_limbs=[]
for side in (-1,1):
    arm=cylinder("Milo arm",milo,(side*.52,-.02,1.32),.115,.66,ORANGE,(0,0,side*.25)); milo_limbs.append((arm,side))
    sphere("Milo paw",milo,(side*.55,-.08,.98),(.16,.15,.13),CREAM)
    leg=cylinder("Milo leg",milo,(side*.22,0,.42),.14,.55,ORANGE,(0,0,0)); milo_limbs.append((leg,-side))
    sphere("Milo foot",milo,(side*.24,-.12,.13),(.23,.28,.12),CREAM)
sphere("Milo tail",milo,(.55,.20,.78),(.58,.10,.11),ORANGE).rotation_euler[1]=-.45

# Zuzu: tiny lavender mouse with turquoise eyes and yellow scarf
zuzu = bpy.data.objects.new("Zuzu character rig", None); bpy.context.collection.objects.link(zuzu)
sphere("Zuzu body",zuzu,(0,0,.63),(.29,.24,.40),PURPLE)
sphere("Zuzu head",zuzu,(0,-.02,1.27),(.38,.31,.36),PURPLE)
sphere("Zuzu muzzle",zuzu,(0,-.30,1.17),(.23,.11,.13),CREAM)
sphere("Zuzu nose",zuzu,(0,-.40,1.21),(.05,.03,.04),DARK)
for x in (-.27,.27):
    sphere("Zuzu round ear",zuzu,(x,-.01,1.58),(.20,.12,.22),PURPLE)
    sphere("Zuzu pink ear",zuzu,(x,-.105,1.58),(.12,.035,.14),PINK)
for x in (-.13,.13):
    sphere("Zuzu eye white",zuzu,(x,-.285,1.34),(.085,.035,.11),WHITE)
    sphere("Zuzu turquoise iris",zuzu,(x,-.32,1.34),(.045,.02,.07),TEAL)
    sphere("Zuzu pupil",zuzu,(x,-.34,1.34),(.022,.012,.04),DARK)
# scarf around neck
sphere("Zuzu yellow scarf",zuzu,(0,-.02,.91),(.32,.27,.10),YELLOW)
sphere("Zuzu scarf tail",zuzu,(.22,-.08,.78),(.11,.08,.25),YELLOW)
for side in (-1,1):
    cylinder("Zuzu leg",zuzu,(side*.13,0,.22),.07,.32,PURPLE)
    sphere("Zuzu foot",zuzu,(side*.14,-.08,.05),(.13,.17,.07),CREAM)
    cylinder("Zuzu arm",zuzu,(side*.31,-.02,.80),.06,.30,PURPLE,(0,0,side*.3))
sphere("Zuzu tail",zuzu,(.20,.16,.35),(.43,.04,.045),PURPLE).rotation_euler[1]=-.2

milo.location=(-1.5,0,0)
zuzu.location=(1.45,-.1,0)

# A bright red berry becomes the comic chase prop
bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=16, location=(0,-.5,.35))
berry=bpy.context.object; berry.name="Rolling red berry"; berry.scale=(.23,.23,.23); berry.data.materials.append(RED)
bpy.ops.object.shade_smooth()

# Animated chase: both characters move across the meadow, hop, and react.
def key(obj, frame, loc=None, rot=None):
    if loc is not None:
        obj.location=loc; obj.keyframe_insert(data_path="location",frame=frame)
    if rot is not None:
        obj.rotation_euler=rot; obj.keyframe_insert(data_path="rotation_euler",frame=frame)

key(milo,1,(-1.5,0,0)); key(milo,18,(-.65,0,.22)); key(milo,34,(.15,0,0))
key(milo,48,(.7,0,.35),(0,0,math.radians(-18)))
key(milo,64,(1.0,0,0),(0,0,math.radians(12)))
key(milo,96,(1.0,0,0),(0,0,0))
key(zuzu,1,(1.45,-.1,0)); key(zuzu,18,(.85,-.1,.12)); key(zuzu,34,(.1,-.1,.30))
key(zuzu,48,(-.55,-.1,.12)); key(zuzu,64,(-.85,-.1,0)); key(zuzu,96,(-.85,-.1,0))
key(berry,1,(0,-.5,.35)); key(berry,18,(.55,-.5,.35),(0,0,0))
key(berry,48,(1.8,-.5,.35),(0,0,math.radians(520)))
key(berry,96,(2.1,-.5,.35),(0,0,math.radians(720)))

# Repeated limb swings give visible running action without camera shake.
for obj, direction in milo_limbs:
    for f, angle in [(1,-.35),(12,.35),(24,-.35),(36,.35),(48,-.35),(60,.35),(72,-.2),(96,0)]:
        obj.rotation_euler[1]=angle*direction
        obj.keyframe_insert(data_path="rotation_euler",frame=f)
# Keep all motion smooth and consistent
for ob in bpy.data.objects:
    if ob.animation_data and ob.animation_data.action:
        for fc in ob.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation="BEZIER"

# Camera stays stable; only the characters and props move.
bpy.ops.object.camera_add(location=(0,-12,4.4))
cam=bpy.context.object
direction=Vector((0,0,1.25))-cam.location
cam.rotation_euler=direction.to_track_quat("-Z","Y").to_euler()
cam.data.type="ORTHO"; cam.data.ortho_scale=7.2
bpy.context.scene.camera=cam

for typ, loc, energy, size in [
    ("AREA",(-4,-5,8),900,6),
    ("AREA",(4,-2,5),500,5),
    ("AREA",(0,4,6),650,4)
]:
    bpy.ops.object.light_add(type=typ,location=loc)
    lamp=bpy.context.object; lamp.data.energy=energy; lamp.data.shape="DISK"; lamp.data.size=size

scene=bpy.context.scene
engines={i.identifier for i in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items}
if "BLENDER_EEVEE_NEXT" in engines: scene.render.engine="BLENDER_EEVEE_NEXT"
elif "BLENDER_EEVEE" in engines: scene.render.engine="BLENDER_EEVEE"
else: scene.render.engine="CYCLES"
scene.render.resolution_x=540; scene.render.resolution_y=960; scene.render.resolution_percentage=100
scene.render.fps=16; scene.frame_start=1; scene.frame_end=96
scene.render.image_settings.file_format="PNG"; scene.render.image_settings.color_mode="RGB"
scene.render.filepath=os.path.join(frames_dir,"frame_")
scene.render.film_transparent=False
scene.world.color=(.32,.48,.65)
scene.view_settings.view_transform="Standard"
scene.camera.data.lens=50
scene.render.image_settings.color_mode="RGB"
scene.render.use_file_extension=True
scene.frame_set(1)
bpy.ops.render.render(animation=True)
print("MILO_ZUZU_TEST_RENDER_COMPLETE")

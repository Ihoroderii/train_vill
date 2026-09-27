"""Render the actual Blender meshes into a 30-item preview contact sheet."""
import bpy, math, json, os, sys
from pathlib import Path
from mathutils import Vector
OUT=Path(os.environ.get('TINY_TRAIN_OUTPUT',str(Path(__file__).resolve().parent)))
bpy.ops.wm.open_mainfile(filepath=str(OUT/'Tiny_Train_Village.blend'))
scene=bpy.context.scene
catalog=json.loads((OUT/'catalog_manifest.json').read_text())['assets']
pick=os.environ.get('TINY_TRAIN_RENDER_ONLY','')
chosen=set(int(s) for s in pick.split(',') if s) if pick else None
scene.render.resolution_x=512;scene.render.resolution_y=512
scene.cycles.samples=24
for a in catalog:bpy.data.collections[a['slug']].hide_render=True
for a in catalog:
    if chosen and a['number'] not in chosen:continue
    coll=bpy.data.collections[a['slug']];root=bpy.data.objects[a['slug']+'_ROOT']
    original=root.location.copy();root.location=(0,0,0);coll.hide_render=False
    bpy.context.view_layer.update()
    pts=[o.matrix_world@Vector(p) for o in coll.objects if o.type=='MESH' for p in o.bound_box]
    lo=Vector(tuple(min(p[i] for p in pts) for i in range(3)))
    hi=Vector(tuple(max(p[i] for p in pts) for i in range(3)))
    center=(lo+hi)/2;span=(hi-lo).length
    cam=scene.camera;cam.location=center+Vector((-6,-8,5.5)).normalized()*max(5,span*3)
    cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
    bpy.context.view_layer.update();inv=cam.matrix_world.inverted()
    projected=[inv@Vector((x,y,z)) for x in (lo.x,hi.x) for y in (lo.y,hi.y) for z in (lo.z,hi.z)]
    w=max(p.x for p in projected)-min(p.x for p in projected)
    h=max(p.y for p in projected)-min(p.y for p in projected)
    cam.data.ortho_scale=max(w,h)*1.23
    scene.render.filepath=str(OUT/'previews'/f"{a['slug']}.png")
    bpy.ops.render.render(write_still=True)
    coll.hide_render=True;root.location=original
    print(f"RENDERED {a['number']:02d}/30: {a['name']}",flush=True)
print('Preview rendering finished',flush=True)

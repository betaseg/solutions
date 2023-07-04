import json
import logging
import os
import sys
from pathlib import Path

import bpy
from mathutils import Color, Matrix

# Get command-line arguments
decimate_ratio = float(sys.argv[-7])
resolution_percentage = int(sys.argv[-6])
in_path = sys.argv[-5].strip()
out_blend_path = sys.argv[-4] if sys.argv[-4] != "None" else None
out_rendering_path = sys.argv[-3] if sys.argv[-3] != "None" else None
include = sys.argv[-2].split(",") if sys.argv[-2] != "None" else None
exclude = sys.argv[-1].split(",") if sys.argv[-1] != "None" else None

scene = bpy.context.scene
main_collection = bpy.data.collections['Collection']

# Remove the default cube object
bpy.data.objects.remove(bpy.data.objects['Cube'])

def red(value):
    return float((value >> 16) & 0xff) / 255. if value is not None else 1.

def green(value):
    return float((value >> 8) & 0xff) / 255. if value is not None else 1.

def blue(value):
    return float(value & 0xff) / 255. if value is not None else 1.

def alpha(value):
    return float((value >> 24) & 0xff) / 255. if value is not None else 1.

def adjust_newly_added_object(file, new_objects):
    bpy.ops.object.shade_smooth()
    if decimate_ratio < 1.0:
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.decimate(ratio=decimate_ratio)
        bpy.ops.object.editmode_toggle()

    attrs = os.path.splitext(file)[0] + "_attrs.json"
    color = None
    if Path(attrs).exists():
        with open(attrs, 'r') as openfile:
            json_object = json.load(openfile)
            color = json_object['color']

    material = bpy.data.materials.new('material')
    material.use_nodes = True
    material.node_tree.nodes.new(type='ShaderNodeBsdfGlass')
    inp = material.node_tree.nodes['Material Output'].inputs['Surface']

    material.node_tree.nodes["Glass BSDF"].inputs[0].default_value = (
        red(color), green(color), blue(color), alpha(color))
    material.node_tree.nodes["Glass BSDF"].inputs[1].default_value = 0.5
    outp = material.node_tree.nodes['Glass BSDF'].outputs['BSDF']
    material.node_tree.links.new(inp, outp)

    for obj_name in new_objects:
        bpy.data.objects[obj_name].active_material = material

    if out_blend_path:
        bpy.ops.wm.save_mainfile(filepath=out_blend_path)
        bpy.ops.wm.open_mainfile(filepath=out_blend_path)

def file_included(file):
    if include and not any(_include in str(file) for _include in include):
        return False
    if exclude and any(_exclude in str(file) for _exclude in exclude):
        return False
    return True

def import_stl(stl_path):
    prior_objects = [object.name for object in bpy.context.scene.objects]
    bpy.ops.import_mesh.stl(filepath=stl_path)
    new_current_objects = [object.name for object in bpy.context.scene.objects]
    new_objects = set(new_current_objects) - set(prior_objects)
    adjust_newly_added_object(stl_path, new_objects)

    # Scale down the imported meshes
    scale_factor = 0.1  # Adjust this value to your desired scale
    for obj_name in new_objects:
        obj = bpy.data.objects[obj_name]
        obj.matrix_world = Matrix.Scale(scale_factor, 4) @ obj.matrix_world

if in_path.endswith('.stl'):
    import_stl(str(Path(in_path).absolute()))
else:
    for subdir, dirs, files in os.walk(in_path):
        for file in files:
            if file.endswith('.stl') and file_included(file):
                import_stl(os.path.join(subdir, file))

# Set world background color
world = bpy.data.worlds['World']
world.use_nodes = True
bg = world.node_tree.nodes['Background']
bg.inputs[0].default_value[:3] = (0.01, 0.01, 0.01)

light = bpy.data.objects['Light']
light.data.type = 'SUN'
light.data.energy = 10

# increase clip end to make sure also bigger datasets are visible
cam_ob = bpy.context.scene.camera
cam_ob.data.clip_end = 30000
cam_ob.data.lens = 45

objects = bpy.context.scene.objects
for obj in objects:
    obj.select_set(obj.type == "MESH")
bpy.ops.view3d.camera_to_view_selected()

area = next(area for area in bpy.context.screen.areas if area.type == 'VIEW_3D')
area.spaces[0].region_3d.view_perspective = 'CAMERA'

# denoising
bpy.context.scene.use_nodes = True


# Render configuration
bpy.context.scene.render.engine = 'CYCLES'
bpy.context.scene.render.resolution_percentage = resolution_percentage
bpy.context.scene.cycles.samples = 512
bpy.context.scene.cycles.preview_samples = 128

if out_blend_path:
    bpy.ops.wm.save_as_mainfile(filepath=out_blend_path)

if out_rendering_path:
    scene.render.filepath = out_rendering_path
    bpy.ops.render.render('INVOKE_DEFAULT', write_still=True)
import json
import logging
import os
import sys
from pathlib import Path

import bpy
from mathutils import Color

# logging.info(str(sys.argv))
decimate_ratio = float(sys.argv[len(sys.argv) - 7])
resolution_percentage = int(sys.argv[len(sys.argv) - 6])
in_path = sys.argv[len(sys.argv) - 5].strip()
out_blend_path = sys.argv[len(sys.argv) - 4]
if out_blend_path == "None":
    out_blend_path = None
out_rendering_path = sys.argv[len(sys.argv) - 3]
if out_rendering_path == "None":
    out_rendering_path = None
include = sys.argv[len(sys.argv) - 2]
if include == "None":
    include = None
else:
    include = include.split(",")
exclude = sys.argv[len(sys.argv) - 1]
if exclude == "None":
    exclude = None
else:
    exclude = exclude.split(",")
scene = bpy.context.scene

main_collection = bpy.data.collections['Collection']
objs = set()

# for obj in main_collection.objects:
#     objs.add( obj.data )
#     bpy.data.objects.remove( obj )
cube = bpy.data.objects['Cube']
bpy.data.objects.remove(cube)


def red(value):
    if value is None:
        return 1.
    return float((value >> 16) & 0xff)/255.


def green(value):
    if value is None:
        return 1.
    return float((value >> 8) & 0xff)/255.


def blue(value):
    if value is None:
        return 1.
    return float(value & 0xff)/255.


def alpha(value):
    if value is None:
        return 1.
    return float((value >> 24) & 0xff)/255.


def adjust_newly_added_object(file, new_objects):
    global obj
    bpy.ops.object.shade_smooth()
    if decimate_ratio < 1.0:
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.decimate(ratio=decimate_ratio)
        bpy.ops.object.editmode_toggle()
    material = bpy.data.materials.new('material')
    material.use_nodes = True
    material.node_tree.nodes.new(type='ShaderNodeBsdfGlass')
    inp = material.node_tree.nodes['Material Output'].inputs['Surface']

    attrs = os.path.splitext(file)[0] + "_attrs.json"
    color = None
    if Path(attrs).exists():
        with open(attrs, 'r') as openfile:
            json_object = json.load(openfile)
            color = json_object['color']
    material.node_tree.nodes["Glass BSDF"].inputs[0].default_value = (red(color), green(color), blue(color), alpha(color))
    print(material.node_tree.nodes["Glass BSDF"].inputs[0].default_value)
    material.node_tree.nodes["Glass BSDF"].inputs[1].default_value = 0.5
    outp = material.node_tree.nodes['Glass BSDF'].outputs['BSDF']
    material.node_tree.links.new(inp, outp)
    for obj_name in new_objects:
        bpy.data.objects[obj_name].active_material = material
    bpy.ops.wm.save_mainfile(filepath=out_blend_path)
    bpy.ops.wm.open_mainfile(filepath=out_blend_path)


def file_included(file):
    if include:
        if not any(_include in str(file) for _include in include):
            return False
    if exclude:
        if any(_exclude in str(file) for _exclude in exclude):
            return False
    return True


def import_stl(stl_path):
    prior_objects = [object.name for object in bpy.context.scene.objects]
    bpy.ops.import_mesh.stl(filepath=stl_path)
    new_current_objects = [object.name for object in bpy.context.scene.objects]
    new_objects = set(new_current_objects) - set(prior_objects)
    adjust_newly_added_object(stl_path, new_objects)


if in_path.endswith('.stl'):
    import_stl(str(Path(in_path).absolute()))
else:
    for subdir, dirs, files in os.walk(in_path):

        file_list = [item for item in files if item.endswith('.stl')]
        logging.info("files : ")
        logging.info(file_list)
        file_list.sort()
        for file in file_list:
            # logging.info(file)
            if file_included(file):
                name = os.path.join(subdir, file)
                import_stl(name)

# focus on data collection
objects = bpy.context.scene.objects
for obj in objects:
    obj.select_set(obj.type == "MESH")
bpy.ops.view3d.camera_to_view_selected()

light = bpy.data.objects['Light']
light.data.type = 'SUN'
light.data.energy = 10

# increase clip end to make sure also bigger datasets are visible
cam_ob = bpy.context.scene.camera
cam_ob.data.clip_end = 30000
cam_ob.data.lens = 45

# show camera view
if bpy.context.screen:
    area = next(area for area in bpy.context.screen.areas if area.type == 'VIEW_3D')
    area.spaces[0].region_3d.view_perspective = 'CAMERA'

if out_blend_path:
    bpy.ops.wm.save_as_mainfile(filepath=out_blend_path)
# bpy.context.window.workspace = bpy.data.workspaces["Rendering"]

# set background color
world = bpy.data.worlds['World']
world.use_nodes = True
bg = world.node_tree.nodes['Background']
bg.inputs[0].default_value[:3] = (0.01, 0.01, 0.01)

# render
# bpy.context.scene.render.resolution_x = w
# bpy.context.scene.render.resolution_y = h
bpy.context.scene.render.resolution_percentage = resolution_percentage
bpy.context.scene.render.engine = 'CYCLES'
if out_rendering_path:
    bpy.context.scene.render.filepath = out_rendering_path
    bpy.ops.wm.save_mainfile(filepath=out_blend_path)
    bpy.ops.wm.open_mainfile(filepath=out_blend_path)
    bpy.ops.render.render('INVOKE_DEFAULT', write_still=True)

bpy.ops.wm.save_as_mainfile(filepath=out_blend_path)

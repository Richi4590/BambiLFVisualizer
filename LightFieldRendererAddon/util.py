import json
import bpy
from mathutils import *
D = bpy.data
C = bpy.context

def delete_object_by_name(name):
    # Check if the object exists
    if name in bpy.data.objects:
        # Set the object as the active object
        bpy.context.view_layer.objects.active = bpy.data.objects[name]

        # Ensure we are in OBJECT mode
        bpy.ops.object.mode_set(mode='OBJECT')

        # Deselect all objects
        bpy.ops.object.select_all(action='DESELECT')

        # Select the object by name
        bpy.data.objects[name].select_set(True)

        # Delete the selected objects
        bpy.ops.object.delete()

def clear_scene_except_lights():
    # Deselect all objects
    bpy.ops.object.select_all(action='DESELECT')

    # Select lights
    bpy.ops.object.select_by_type(type='LIGHT')

    # Invert the selection
    bpy.ops.object.select_all(action='INVERT')

    # Delete the selected objects
    bpy.ops.object.delete()

def getValueFromJSON(json_path, key, sub_key):
    # Load JSON data
    data = json.loads(json_path)

    for k, v in data.items():
        if (k == key):
            for sub_k, sub_v in v.items():
                if (sub_k == sub_key):
                    return sub_v
    
    return None
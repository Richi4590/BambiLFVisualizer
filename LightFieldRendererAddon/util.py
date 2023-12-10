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

def clear_scene():

    if not bpy.context.selected_objects:
        # Create a temporary empty object
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.empty_add()
        bpy.context.view_layer.objects.active = bpy.context.selected_objects[-1]

    bpy.ops.object.mode_set(mode='OBJECT')

    bpy.ops.object.select_all(action='SELECT')

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

def purge_all_addon_property_data(context):
    lfr_props = context.scene.lfr_properties
    # Iterate over the collection and remove all items
    for item in lfr_props.cameras:
        lfr_props.cameras.remove(0)
    
    for item in lfr_props.range_planes_collection:
        lfr_props.range_planes_collection.remove(0)

def delete_objects_in_range_collection(collection_property):
    for item in collection_property:
        if item.plane != None:
            object_name = item.plane.name

            # Check if the object exists in the scene
            obj = bpy.data.objects.get(object_name)
            if obj:
                # Unlink and delete the object
                bpy.data.objects.remove(obj, do_unlink=True)
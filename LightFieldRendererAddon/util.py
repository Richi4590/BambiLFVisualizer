import json
import bpy
from mathutils import *
import os

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
    for collection in bpy.data.collections:
        bpy.data.collections.remove(collection, do_unlink=True)

    # Iterate through all objects in the scene
    for obj in bpy.data.objects:
        bpy.data.objects.remove(obj, do_unlink=True)



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

def link_obj(scene, obj):
    if (scene not in obj.users_collection):
        bpy.context.scene.collection.objects.link(obj)     # Link the obj if not already linked to the scene collection

def append_content_from_blend_file(absolute_filepath, inner_path, content_name):
    #----example: 
    #file_path =  os.path.abspath('Test Blend.blend')  # blend file name
    #inner_path = 'Material'   # type 
    #material_name = 'Material_Name' # name

    #bpy.ops.wm.append(
    #    filepath=os.path.join(file_path, inner_path, material_name),
    #    directory=os.path.join(file_path, inner_path),
    #    filename=material_name
    #    )

    bpy.ops.wm.append(
        filepath=os.path.join(absolute_filepath, inner_path, content_name),
        directory=os.path.join(absolute_filepath, inner_path),
        filename=content_name
        )
    
def get_material_from_blend_file(relative_file_path, material_name):

    current_blend_directory = os.path.dirname(os.path.abspath(__file__))
    absolute_filepath = os.path.join(current_blend_directory, relative_file_path)

    if (material_name not in bpy.data.materials):
        # Append the material from the external blend file
        with bpy.data.libraries.load(absolute_filepath, link=False) as (data_from, data_to):
            if material_name in data_from.materials:
                data_to.materials.append(data_from.materials[0])

        # Get the appended material
        appended_material = bpy.data.materials.get(material_name)

        return appended_material
    
    else:
        return bpy.data.materials.get(material_name)
    
#needed for later
# # Iterate over cameras and set resolutions
# for camera_name, resolution in pixel_resolutions.items():
#     camera = bpy.data.objects.get(camera_name)
    
#     if camera and camera.type == 'CAMERA':
#         bpy.context.scene.camera = camera  # Set the current scene's active camera
#         bpy.context.scene.render.resolution_x = resolution[0]
#         bpy.context.scene.render.resolution_y = resolution[1]
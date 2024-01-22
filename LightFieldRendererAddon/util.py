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

    delete_temp_objects_of_range_rendering(lfr_props)

    delete_rendered_images_data(lfr_props)

def delete_rendered_images_data(lfr_prp):
    for item in lfr_prp.rendered_images:
        lfr_prp.rendered_images.remove(0)

def delete_temp_objects_of_range_rendering(lfr_prp):
    # Iterate through each RangeMeshPropertyGroup in the collection
    for entry in lfr_prp.range_objects:

        if entry.mesh: # Delete the mesh object
            bpy.data.objects.remove(entry.mesh, do_unlink=True)

        if entry.proj_cam: # Delete the projection camera object
            bpy.data.objects.remove(entry.proj_cam, do_unlink=True)

        if entry.view_dir_obj: # Delete the view direction object
            bpy.data.objects.remove(entry.view_dir_obj, do_unlink=True)

        if entry.view_origin_obj: # Delete the view origin object
            bpy.data.objects.remove(entry.view_origin_obj, do_unlink=True)

    for item in lfr_prp.range_objects:
        lfr_prp.range_objects.remove(0)


    for collection in bpy.data.collections:
        # Check if the collection is empty
        if not collection.objects:
            # Remove the empty collection
            bpy.data.collections.remove(collection)

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
    
def set_render_path(relative_file_path):
    current_blend_directory = os.path.dirname(os.path.abspath(__file__))
    absolute_filepath = os.path.join(current_blend_directory, relative_file_path)
    bpy.context.scene.render.filepath = absolute_filepath

def get_absolute_file_path_from_relative_path(relative_file_path):
    current_blend_directory = os.path.dirname(os.path.abspath(__file__))
    absolute_filepath = os.path.join(current_blend_directory, relative_file_path)
    return absolute_filepath

def save_image_to_disk(absolute_folder_path, file_name, image, view_with_image_viewer = False):
    absolute_file_path = absolute_folder_path + file_name
    image.save_render(filepath=absolute_file_path)

    # Open the saved image in the default image viewer
    if (view_with_image_viewer):
        bpy.ops.wm.path_open(filepath=absolute_file_path)

def find_first_file(folder_path, file_extension):
    for filename in os.listdir(folder_path):
        if filename.endswith(file_extension):
            return os.path.join(folder_path, filename)

    return None  # Return None if no matching file is found

def find_file_by_partial_name(folder_path, partial_name):
    for filename in os.listdir(folder_path):
        if partial_name.lower() in filename.lower():
            return os.path.join(folder_path, filename)

    return None  # Return None if no matching file is found


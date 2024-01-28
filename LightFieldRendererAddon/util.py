import ast
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
    lfr_props = bpy.context.scene.lfr_properties

    for collection in bpy.data.collections:
        bpy.data.collections.remove(collection, do_unlink=True)

    # Iterate through all objects in the scene
    for obj in bpy.data.objects:
        if lfr_props.man_rend_cam == obj: #skip manual rendering cam from deletion
            continue

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

    print(os.path.join(absolute_filepath, inner_path, content_name))
    print(os.path.join(absolute_filepath, inner_path))
    print(content_name)
    
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
    bpy.context.scene.render.filepath = absolute_filepath #<- setting the path
    return absolute_filepath

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
    folder_path_fix = folder_path.replace('\\', '/')
    for filename in os.listdir(folder_path_fix):
        if filename.endswith(file_extension):
            return os.path.join(folder_path_fix, filename)

    return None  # Return None if no matching file is found

def find_file_by_partial_name(folder_path, partial_name):
    folder_path_fix = folder_path.replace('\\', '/')
    for filename in os.listdir(folder_path_fix):
        if partial_name.lower() in filename.lower():
            return os.path.join(folder_path_fix, filename)

    return None  # Return None if no matching file is found

def has_file_with_extension(path):
    # Check if the path is a file
    if os.path.isfile(path):
        # Get the file extension
        _, file_extension = os.path.splitext(path)
        # Check if the file extension is not empty
        return bool(file_extension)
    else:
        return False

def is_empty_or_whitespace(s):
    return len(s.strip()) == 0

def is_not_empty_or_whitespace(s):
    return len(s.strip()) > 0

def correctly_set_or_overwrite_path_strings(lfr_prp):

    if is_empty_or_whitespace(lfr_prp.folder_path):
        print(f"No Folder Path set!")
        raise ValueError(f"No Folder Path set! Please specify a folder with images, mask and json file inside!")
    
    if lfr_prp.folder_path.startswith('//'):
        lfr_prp.folder_path = lfr_prp.folder_path.lstrip('/').replace('/', '\\')

    lfr_prp.folder_path = os.path.abspath(lfr_prp.folder_path) # get the absolute path with drive letter in the beginning
    lfr_prp.folder_path = lfr_prp.folder_path + "\\" # add a \ at the end

    lfr_prp.json_path = lfr_prp.folder_path + "\matched_poses.json" # default json file
    absolute_data_path_root = os.path.abspath(os.path.join(lfr_prp.folder_path, ".."))

    absolute_data_path_dem_folder = absolute_data_path_root + "\Data\dem"
    absolute_data_path_dem_file = find_first_file(absolute_data_path_dem_folder, ".glb")
    absolute_data_path_mask = find_file_by_partial_name(lfr_prp.folder_path, "mask")

    lfr_prp.cameras_path = lfr_prp.folder_path
    lfr_prp.dem_path = absolute_data_path_dem_file
    lfr_prp.img_mask = absolute_data_path_mask

    render_path = ""
    if is_not_empty_or_whitespace(lfr_prp.man_render_path):
        if lfr_prp.man_render_path.startswith('//'):
            lfr_prp.man_render_path = lfr_prp.man_render_path.lstrip('\\')
            lfr_prp.man_render_path = os.path.abspath(lfr_prp.man_render_path)

        render_path = lfr_prp.man_render_path
    else:    
        #use local addon folder "Pics"
        # warning: depends on the location of the file the function is stored in!
        render_path = set_render_path("Pics\\") #here the path render path in blender gets set
        print("render_path:", render_path)

    lfr_prp.render_path = render_path #lfr_prp.render_path is only used as a reference if later needed
    
    #only setting the folder path is fine
    # either rendered image get overwritten or they are stored in the render folder individually
    bpy.context.scene.render.filepath = lfr_prp.render_path 

    if is_not_empty_or_whitespace(lfr_prp.man_dem_path):
        if lfr_prp.man_dem_path.startswith('//'):
            lfr_prp.man_dem_path = lfr_prp.man_dem_path.lstrip('\\')
            lfr_prp.man_dem_path = os.path.abspath(lfr_prp.man_dem_path)
            
        lfr_prp.dem_path = lfr_prp.man_dem_path #overwrite the default dem path


    if is_not_empty_or_whitespace(lfr_prp.man_json_path):
        if lfr_prp.man_json_path.startswith('//'):
            lfr_prp.man_json_path = lfr_prp.man_json_path.lstrip('\\')
            lfr_prp.man_json_path = os.path.abspath(lfr_prp.man_json_path)
    
        lfr_prp.json_path = lfr_prp.man_json_path #overwrite the default json path


############# unused but may be useful: ###########
def create_parent(name):
    # Create an empty object to serve as the parent
    parent_obj = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(parent_obj)
    bpy.context.view_layer.objects.active = parent_obj
    bpy.ops.object.select_all(action='DESELECT')
    parent_obj.select_set(True)

    return parent_obj

def add_child(parent, child):
    # Parent the child to the parent
    child.select_set(True)
    bpy.context.view_layer.objects.active = parent
    bpy.ops.object.parent_set(type='OBJECT')

def remove_children(parent):
    bpy.ops.object.mode_set(mode='OBJECT')
    # Remove all children of the parent
    children = [child for child in bpy.data.objects if child.parent == parent]
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = parent
    parent.select_set(True)

    # Select children manually
    for child in children:
        child.select_set(True)

    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

    # Delete the children
    for child in children:
        bpy.data.objects.remove(child, do_unlink=True)

from math import floor
import bpy
from mathutils import *
import numpy as np
from . cameras import create_and_prep_new_camera, create_range_render_camera, set_current_camera_rendering_resolution
from . plane import *
from bpy_extras.image_utils import load_image

import bpy
import numpy as np

def apply_images_and_positions_to_planes_from_range(lfr_prp, start_keyframe_index): 

    cameras_data_arr = lfr_prp.cameras
    cameras_path = lfr_prp.cameras_path
    frame_range = lfr_prp.range_to_interpolate
    end_index = start_keyframe_index + frame_range
    actual_img_count = end_index

    if end_index > len(cameras_data_arr):
        actual_img_count = len(cameras_data_arr) - start_keyframe_index
        end_index = len(cameras_data_arr)-1

    j = 1
    for entry in range(start_keyframe_index, end_index):
        #print(start_keyframe_index, "+ ", j)
        frame_number = start_keyframe_index + j
        camData = cameras_data_arr[frame_number]
        img_path = cameras_path + camData.image_file
        create_and_prep_new_camera(lfr_prp, img_path, lfr_prp.img_mask, frame_number)

        j = j + 1

        if j >= end_index:
            break

def get_image_depending_on_frame(lfr_prp, index): #simple sinlge image application
    cameras_data_arr = lfr_prp.cameras
    cameras_path = lfr_prp.cameras_path

    if index > len(cameras_data_arr):
        index = len(cameras_data_arr)

    camData = cameras_data_arr[index]
    img_path = cameras_path + camData.image_file
    
    return bpy.data.images.load(img_path)

def combine_images(lfr_props):
    range_objects = lfr_props.range_objects
    print(len(range_objects))
    cameras_data_arr = lfr_props.cameras

    half_index = int(floor(len(range_objects) / 2))
    half_cam = range_objects[half_index].proj_cam
    offset_cam_position = (half_cam.location.x, half_cam.location.y - 100, half_cam.location.z)
    
    if lfr_props.range_render_cam is not None:
        bpy.data.objects.remove(lfr_props.range_render_cam, do_unlink=True)
    
    # if available, use manual defined camera instead!
    if lfr_props.man_rend_cam is not None:
        bpy.context.scene.camera = lfr_props.man_rend_cam
    else:
        lfr_props.range_render_cam = create_range_render_camera(offset_cam_position, half_cam.rotation_euler)
        bpy.context.scene.camera = lfr_props.range_render_cam
        set_current_camera_rendering_resolution(lfr_props)


    # Set the image as the active image for rendering
    bpy.context.scene.render.image_settings.file_format = 'PNG'
    bpy.context.scene.render.image_settings.color_mode = 'RGBA'
    bpy.context.scene.render.image_settings.compression = 0  # No compression for lossless PNG
    result_image = None
    rendered_images = []

    lfr_props.projection_mesh_obj.hide_render = True  
    lfr_props.dem_mesh_obj.hide_render = True  

    lfr_props.projection_mesh_obj.hide_viewport = True  
    lfr_props.dem_mesh_obj.hide_viewport = True  

    for entry in range_objects:
        if entry.mesh:
            entry.mesh.hide_render = True    #hide all meshes from rendering
            entry.mesh.hide_viewport = True  #hide all meshes from viewport (eye icon)

    #bpy.data.images.load("abc") # debug

    if bpy.data.images.get('Render Result.001'):
        bpy.data.images.remove(bpy.data.images.get('Render Result.001'), do_unlink=True) 

    if lfr_props.save_rend_images is False:
        if has_file_with_extension(lfr_props.render_path) is False:

            bpy.context.scene.render.filepath = lfr_props.render_path + "Render_Result." + bpy.context.scene.render.image_settings.file_format 

    print("rendering...")
    # Iterate through all mesh objects in the scene
    i = 0
    for entry in range_objects:
        i = i + 1

        if lfr_props.save_rend_images:
            bpy.context.scene.render.filepath = lfr_props.render_path + f"Render_Result_{i}." + bpy.context.scene.render.image_settings.file_format

        entry.mesh.hide_viewport = False  
        entry.mesh.hide_render = False
        # Render the scene to get pixel values
        bpy.ops.render.render(write_still=True)
            
        # Access the 'Render Result' image
        img_path = bpy.context.scene.render.filepath
        rendered_image = bpy.data.images.load(img_path)

        if rendered_image:
            copied_image = bpy.data.images.new(name="CopiedImage_" + str(i), width=rendered_image.size[0], height=rendered_image.size[1])
            copied_image.pixels = rendered_image.pixels[:]
            copied_image.update()
            rendered_images.append(rendered_image)

        entry.mesh.hide_render = True 
        entry.mesh.hide_viewport = True  

    print("done rendering")
    lfr_props.dem_mesh_obj.hide_render = False 
    lfr_props.dem_mesh_obj.hide_viewport = False  
    lfr_props.projection_mesh_obj.hide_render = False  #unhide the main projection mesh  
    lfr_props.projection_mesh_obj.hide_viewport = False  

    result_image = blend_images(rendered_images, 0.5)
    
    return result_image

def blend_images(images, mean_alpha):
    if len(images) == 0:
        raise ValueError("At least one image is required for blending.")

    # Get the dimensions of the first image
    width, height = images[0].size[0], images[0].size[1]

    # Create a new image to store the blended result
    result_image = bpy.data.images.new(name='BlendedImage', width=width, height=height, alpha=True)

    # Initialize arrays to store RGB and alpha values separately
    rgb_values = np.zeros((height, width, 3), dtype=np.float32)
    alpha_values = np.zeros((height, width), dtype=np.float32)

    # Count non-transparent images for normalization
    non_transparent_count = 0

    # Loop through pixels and blend images
    for img in images:
        img_array = np.array(img.pixels[:])
        img_array = img_array.reshape((height, width, 4))

        # Check if the pixel is fully transparent
        alpha_channel = img_array[:, :, 3]
        is_fully_transparent = np.all(alpha_channel == 0)

        if not is_fully_transparent:
            rgb_values += img_array[:, :, :3] * alpha_channel[:, :, None]
            alpha_values += alpha_channel
            non_transparent_count += 1

    # Avoid division by zero
    alpha_values[alpha_values == 0] = 1  # Set zero values to 1 to avoid division by zero

    # Calculate the mean alpha value for blending
    mean_alpha_value = mean_alpha / non_transparent_count

    # Calculate the mean RGB values for blending
    rgb_values /= alpha_values[:, :, None]

    # Apply mean alpha value to the blended result
    alpha_values /= non_transparent_count

    # Combine RGB and alpha values
    result_pixels = np.dstack((rgb_values, alpha_values)).flatten()

    # Set the pixels of the result image
    result_image.pixels = result_pixels

    # Update the result image
    result_image.update()

    return result_image
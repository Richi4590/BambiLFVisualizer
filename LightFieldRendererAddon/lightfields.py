import io
from math import floor
import time
import bpy
from mathutils import *
import numpy as np
from . cameras import createAndPrepareANewCamera, createRangeRenderCamera
from . util import append_content_from_blend_file
from . plane import *
from mathutils import Vector
from bpy_extras.image_utils import load_image

import bgl
import gpu

try:
    from PIL import Image, ImageFilter
except ImportError:
    print("Pillow is not installed. Installing...")
    try:
        import pip
        pip.main(["install", "Pillow"])
        from PIL import Image
        print("Pillow has been successfully installed.")
    except ImportError:
        print("Failed to install Pillow. Please install it manually.")
        raise

def createImgWithShaderAndModifier(rendering_cam, cameras_path, image_name, target_mesh_name):
    image_path = cameras_path + image_name

    # Import the image as a plane
    bpy.ops.import_image.to_plane(files=[{'name': image_path}])

    plane_object = bpy.context.active_object     # Get the newly created mesh object
    bpy.context.view_layer.objects.active = plane_object     # Set the active object to the plane

    # Add and configure Shrinkwrap modifier
    bpy.ops.object.mode_set(mode="OBJECT")     
    bpy.ops.object.shade_smooth(use_auto_smooth=False, auto_smooth_angle=0.523599)
    bpy.ops.object.modifier_add(type='SHRINKWRAP')     
    shrinkwrap_modifier = plane_object.modifiers["Shrinkwrap"]
    shrinkwrap_modifier.target = bpy.data.objects[target_mesh_name]
    shrinkwrap_modifier.wrap_method = "PROJECT"
    shrinkwrap_modifier.wrap_mode = "ABOVE_SURFACE"
    shrinkwrap_modifier.use_positive_direction = True
    shrinkwrap_modifier.use_negative_direction = True
    shrinkwrap_modifier.offset = 0.65 

    #create a couple of subdivisions and temporary set scale
    bpy.ops.object.mode_set(mode="EDIT") 
    bpy.ops.mesh.subdivide(number_cuts=7) 
    plane_object.location = rendering_cam.location
    plane_object.scale = (34, 34, 1)


    return plane_object

def createImgWithShaderAndModifierPos(destination_position, cameras_path, image_name, target_mesh_name):
    image_path = cameras_path + image_name

    # Import the image as a plane
    bpy.ops.import_image.to_plane(files=[{'name': image_path}])

    plane_object = bpy.context.active_object     # Get the newly created mesh object
    bpy.context.view_layer.objects.active = plane_object     # Set the active object to the plane

    # Add and configure Shrinkwrap modifier
    bpy.ops.object.mode_set(mode="OBJECT")     
    bpy.ops.object.shade_smooth(use_auto_smooth=False, auto_smooth_angle=0.523599)
    bpy.ops.object.modifier_add(type='SHRINKWRAP')     
    shrinkwrap_modifier = plane_object.modifiers["Shrinkwrap"]
    shrinkwrap_modifier.target = bpy.data.objects[target_mesh_name]
    shrinkwrap_modifier.wrap_method = "PROJECT"
    shrinkwrap_modifier.wrap_mode = "ABOVE_SURFACE"
    shrinkwrap_modifier.use_positive_direction = True
    shrinkwrap_modifier.use_negative_direction = True
    shrinkwrap_modifier.offset = 0.65 

    #create a couple of subdivisions and temporary set scale
    bpy.ops.object.mode_set(mode="EDIT") 
    bpy.ops.mesh.subdivide(number_cuts=7) 
    plane_object.location = destination_position
    plane_object.scale = (34, 34, 1)


    return plane_object

def blend_images(image1, image2, alpha):
    pixels1 = list(image1.getdata())
    pixels2 = list(image2.getdata())

    blended_pixels = [
        tuple(int(alpha * c1 + (1 - alpha) * c2) for c1, c2 in zip(color1, color2))
        for color1, color2 in zip(pixels1, pixels2)
    ]

    blended_image = Image.new('RGB', image1.size)
    blended_image.putdata(blended_pixels)
    return blended_image

def applyImagesAndPositionsToPlanesFromRange(lfr_prp, start_keyframe_index): #factor is focus

    cameras_data_arr = lfr_prp.cameras
    cameras_path = lfr_prp.cameras_path
    pinhole_frame_obj = lfr_prp.pinhole_frame_obj
    frame_range = lfr_prp.range_to_interpolate
    dem_mesh_obj = lfr_prp.dem_mesh_obj
    end_index = start_keyframe_index + frame_range
    factor = lfr_prp.focus
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
        createAndPrepareANewCamera(lfr_prp, img_path, lfr_prp.img_mask, frame_number)

        j = j + 1

        if j >= end_index:
            break


def applyImagesAndPositionsToPlanesFromRange2(lfr_prp, start_keyframe_index): #factor is focus

    cameras_data_arr = lfr_prp.cameras
    cameras_path = lfr_prp.cameras_path
    pinhole_frame_obj = lfr_prp.pinhole_frame_obj
    frame_range = lfr_prp.range_to_interpolate
    dem_mesh_obj = lfr_prp.dem_mesh_obj
    end_index = start_keyframe_index + frame_range
    factor = lfr_prp.focus
    actual_img_count = end_index

    if end_index > len(cameras_data_arr):
        actual_img_count = len(cameras_data_arr) - start_keyframe_index
        end_index = len(cameras_data_arr)


    #print(len(cameras_data_arr))

    camData = cameras_data_arr[start_keyframe_index]
    img_path = cameras_path + camData.image_file
    img_paths = []

    j = 0
    for entry in range(start_keyframe_index, end_index):
        camData = cameras_data_arr[start_keyframe_index + j]
        img_path = cameras_path + camData.image_file
        img_paths.append(img_path)
        j = j + 1

        if j >= end_index:
            break

    # Load all images into a NumPy array
    images = [bpy.data.images.load(img_path) for img_path in img_paths]

    # Get the size of the first image
    width, height = images[0].size[0], images[0].size[1]

    # Create a new image to store the result
    result_image = bpy.data.images.new("Interpolated Image", width=width, height=height)

    # Initialize the final pixel array
    final_pixels = np.zeros((height, width, 4), dtype=np.float32)

    # Iterate over each image
    for i, img in enumerate(images):
        # Extract the pixel values
        pixels = np.array(img.pixels[:], dtype=np.float32).reshape((height, width, 4))

        # Calculate the offset based on the camera position
        offset = int(i * width * factor)

        # Adjust the offset to ensure it stays within the valid range
        offset = max(-width, min(width, offset))

        # Update the final pixel array with the adjusted pixels
        if offset >= 0:
            final_pixels[:, offset:width, :] += pixels[:, :width - offset, :]
        else:
            final_pixels[:, :width + offset, :] += pixels[:, -offset:width, :]

    # Normalize the final pixel values by the number of images
    final_pixels /= len(images)

    # Flatten the final pixel array
    flattened_pixels = final_pixels.flatten()

    # Use foreach_set to efficiently set pixel values
    result_image.pixels.foreach_set(flattened_pixels)

    # Update the image data
    result_image.update()

    return result_image

def applyImagesAndPositionsToPlanesFromRange3(lfr_prp, start_keyframe_index): #factor is focus

    cameras_data_arr = lfr_prp.cameras
    cameras_path = lfr_prp.cameras_path
    pinhole_frame_obj = lfr_prp.pinhole_frame_obj
    frame_range = lfr_prp.range_to_interpolate
    dem_mesh_obj = lfr_prp.dem_mesh_obj
    projection_mesh_obj = lfr_prp.projection_mesh_obj
    end_index = start_keyframe_index + frame_range
    factor = lfr_prp.focus
    actual_img_count = end_index

    if end_index > len(cameras_data_arr):
        actual_img_count = len(cameras_data_arr) - start_keyframe_index
        end_index = len(cameras_data_arr)

    # Set up the compositing nodes
    bpy.context.scene.use_nodes = True
    tree = bpy.context.scene.node_tree
    links = tree.links

    # Clear default nodes
    for node in tree.nodes:
        tree.nodes.remove(node)
    
    # Create a list to store pixel values
    composite_pixels = []   

    # Add Image nodes for each frame
    image_nodes = []

    j = 0
    for entry in range(start_keyframe_index, end_index):
        frame_number = start_keyframe_index + j
        bpy.context.scene.frame_set(frame_number)

        camData = cameras_data_arr[frame_number]
        img_path = cameras_path + camData.image_file
        frame = bpy.data.images.load(img_path)
        
        image_node = tree.nodes.new(type='CompositorNodeImage')
        image_node.location = (-200, 100 * j)
        image_node.image = frame
        image_nodes.append(image_node)

        j = j + 1

        if j >= end_index:
            break

    # Add Alpha Over nodes to combine images
    alpha_over_nodes = []
    for i in range(1, len(image_nodes)):
        alpha_over_node = tree.nodes.new(type='CompositorNodeAlphaOver')
        alpha_over_node.location = (100, 100 * i)
        links.new(image_nodes[i - 1].outputs["Image"], alpha_over_node.inputs[1])
        links.new(image_nodes[i].outputs["Image"], alpha_over_node.inputs[2])
        alpha_over_nodes.append(alpha_over_node)

    # Set up the output node
    output_node = tree.nodes.new(type='CompositorNodeComposite')
    output_node.location = (400, 0)

    # Retrieve the final composited image data
    composite_image = bpy.context.scene.render.image

    return composite_image

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
    print(half_index)
    half_cam = range_objects[half_index].proj_cam
    print(half_cam.name)
    offset_cam_position = (half_cam.location.x, half_cam.location.y - 100, half_cam.location.z)
    lfr_props.range_render_cam = createRangeRenderCamera(offset_cam_position, half_cam.rotation_euler)
    bpy.context.scene.camera = lfr_props.range_render_cam

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
            entry.mesh.hide_render = True    #hide all meshes
            entry.mesh.hide_viewport = True  

    #bpy.data.images.load("abc") # debug

    if bpy.data.images.get('Render Result.001'):
        bpy.data.images.remove(bpy.data.images.get('Render Result.001'), do_unlink=True) 

    print("doing rendering")
    # Iterate through all mesh objects in the scene
    i = 0
    for entry in range_objects:
        i = i + 1

        entry.mesh.hide_viewport = False  
        entry.mesh.hide_render = False
        # Render the scene to get pixel values
        bpy.ops.render.render(write_still=True)

        #maybe wait for render to complete
            
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
    bpy.context.scene.camera = lfr_props.cam_obj
    
    return result_image

def blend_images(images, mean_alpha):
    if len(images) == 0:
        raise ValueError("At least one image is required for blending.")

    # Get the dimensions of the first image
    width, height = images[0].size[0], images[0].size[1]

    # Create a new image to store the blended result
    result_image = bpy.data.images.new(name='BlendedImage', width=width, height=height)

    # Initialize arrays to store RGB and alpha values separately
    rgb_values = np.zeros((height, width, 3), dtype=np.float32)

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
            rgb_values += img_array[:, :, :3]
            non_transparent_count += 1

    # Avoid division by zero
    if non_transparent_count > 0:
        # Calculate the mean value for blending
        rgb_values /= non_transparent_count

        # Combine RGB and alpha values (ignoring alpha_mask)
        result_image.pixels = np.dstack((rgb_values, np.ones_like(rgb_values[:, :, 0]))).flatten()

    # Update the result image
    result_image.update()

    return result_image
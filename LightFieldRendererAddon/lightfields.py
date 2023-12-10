import bpy
from mathutils import *
from . plane import *

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

D = bpy.data
C = bpy.context

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

def applyImagesAndPositionsToPlanesFromRange(lfr_prp, start_keyframe_index):

    cameras_data_arr = lfr_prp.cameras
    cameras_path = lfr_prp.cameras_path
    pinhole_frame_obj = lfr_prp.pinhole_frame_obj
    frame_range = lfr_prp.range_to_interpolate
    dem_mesh_obj = lfr_prp.dem_mesh_obj
    end_index = start_keyframe_index + frame_range
    range_planes_collection = lfr_prp.range_planes_collection

    if end_index > len(cameras_data_arr):
        end_index = len(cameras_data_arr)

    #print(len(cameras_data_arr))



    j = 0
    for entry in range(start_keyframe_index, end_index):
        print(start_keyframe_index, "+ ", j)
        camData = cameras_data_arr[start_keyframe_index + j]
        img_path = cameras_path + camData.image_file
        frame = bpy.data.images.load(img_path)

        #do something with the images

        if j == 0: # never removing the first pinhole_frame_obj -> reusing it
            update_overlay_material_tex(pinhole_frame_obj, frame)
        else:
            range_planes_collection[j - 1].plane.location = cameras_data_arr[start_keyframe_index + j - 1].location
            update_overlay_material_tex(range_planes_collection[j - 1].plane, frame)


        frame.user_clear()
        bpy.data.images.remove(frame)

        j = j + 1

        if j >= end_index:
            break




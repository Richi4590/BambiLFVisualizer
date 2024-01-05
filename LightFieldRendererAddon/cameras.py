from datetime import datetime
import json
from math import radians
import bpy
from mathutils import *

from . util import *
D = bpy.data
C = bpy.context

def parse_poses(posesUrl, nth_frame):

    posesUrl += "matched_poses.json"

    with open(posesUrl, 'r') as file:
        poses = json.load(file)

    frames = None
    if "images" in poses:
        frames = poses["images"]
    elif "frames" in poses:
        frames = poses["frames"]
    else:
        print("No 'images' or 'frames' found in poses")
        return
    
    cameras = []

    i = 0

    for pose in frames:
        if i % nth_frame == 0:
            quat = Quaternion()

            if len(pose["rotation"]) == 4:
                # Assume we have a quaternion
                quat.x, quat.y, quat.z, quat.w = pose["rotation"]
            elif len(pose["rotation"]) == 3:
                # Assume we have Euler angles

                # IMPORTANT: very likely needs to be changed
                pose["rotation"][1] = pose["rotation"][1] + 180 # hot fix ---------------------------------------<<<
                pose["rotation"][2] = pose["rotation"][2] - 90 # hot fix ---------------------------------------<<<

                euler_angles_radians = [radians(angle) for angle in pose["rotation"]]
                euler = Euler(euler_angles_radians, 'XYZ')
                quat = euler.to_quaternion()

            if "fovy" not in pose:
                print(f"Pose {i} has no 'fovy' property!")
                raise ValueError(f"Pose {i} has no 'fovy' property!")

            if isinstance(pose["fovy"], list):
                pose["fovy"] = pose["fovy"][0]

            if not isinstance(pose["fovy"], (int, float)):
                print(f"Pose {i} has no numeric 'fovy' property!")
                raise ValueError(f"Pose {i} has no numeric 'fovy' property!")

            camera = {
                "fovy": pose["fovy"],
                "aspect": 1.0,
                "near": 0.5,
                "far": 100,
                "position": pose["location"],
                "quaternion": quat,
                "image_file": pose["imagefile"],
                "timestamp": datetime.strptime(pose["timestamp"], "%Y-%m-%dT%H:%M:%S.%f%z")
            }

            cameras.append(camera)

        i += 1

    return cameras


def createCurveDataAndKeyFramesOutOfCameras(lfr_props):
    cameras_collection = lfr_props.cameras
    camera_obj = lfr_props.cam_obj

    bpy.context.scene.render.resolution_x = 1024 # in order to apply this to a specific camera
    bpy.context.scene.render.resolution_y = 1024 # you need to do this bpy.context.scene.camera = camera_obj beforehand!

    # Create a path
    first_cam_location = cameras_collection[0].location
    bpy.ops.curve.primitive_bezier_curve_add(enter_editmode=False, align='WORLD', location=first_cam_location)
    path = bpy.context.active_object
    path.name = "LFR_Path"

    link_obj(bpy.context.scene.collection, path)    

    bpy.context.scene.frame_end = len(cameras_collection)

    # Set keyframes for the camera location
    for i, camera_data in enumerate(cameras_collection):
        frame = i + 1
        # Add a control point for the path
        bpy.ops.object.mode_set(mode='EDIT') # currently selected object is path
        bpy.ops.curve.vertex_add(location=camera_data.location)
        bpy.ops.curve.decimate(ratio=0.3)     # Add Simplify Curve modifier
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.scene.frame_set(frame)

        camera_obj.location = camera_data.location
        camera_obj.rotation_mode = 'QUATERNION'
        camera_obj.rotation_quaternion = camera_data.quaternion
        camera_obj.data.lens = camera_data.fovy  # Set the focal length (not FOV)
        
        camera_obj.keyframe_insert(data_path="location", index=-1)
        camera_obj.keyframe_insert(data_path="rotation_quaternion", index=-1)
        camera_obj.data.keyframe_insert(data_path="lens", index=-1)  # Keyframe for focal length
    
def createAndPrepareANewCamera(lfr_props, full_image_path, full_mask_path, camera_number):
    append_content_from_blend_file('./Assets/projection_material.blend', 'Collection', 'ProjectionGroup') # import the camera group from the blend file
    projection_plane = lfr_props.projection_mesh_obj
    view_origin_obj = None
    view_direction_obj = None

    camera_number_str = str(camera_number)

    #for layer in bpy.context.scene.view_layers:
    #    print(layer.name)

    sub_scene_collection = bpy.data.collections.get('ProjectionGroup') #only one camera at a time should exist with this name
    sub_scene_collection.name = "ProjectionGroup_" + camera_number_str

    camera_obj = None
    for obj in sub_scene_collection.objects:
        if (obj.type == 'CAMERA'):
            camera_obj = obj
            camera_obj.name = 'Camera_' + camera_number_str
        if ('ViewDirection' in obj.name):
            obj.name = 'ViewDirection_' + camera_number_str
            view_direction_obj = obj
        if ('ViewOrigin' in obj.name):
            obj.name = 'ViewOrigin_' + camera_number_str
            view_origin_obj = obj

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = camera_obj
    camera_obj.select_set(True)

    link_obj(bpy.context.scene.collection, camera_obj)    
    #camera_obj.name = 'camera_' + loaded_img.name 

    if (lfr_props.pinhole_view is False):
        # Create a new material and refresh shader attributes
        # each new material corresponds to a specific camera
        if (len(projection_plane.data.materials) >= 2): # -------------- really important, 1x assigned material means len of 1!
            new_material = projection_plane.data.materials[0].copy()
        else:
            new_material = get_material_from_blend_file('Assets\projection_material.blend', 'ProjectionMaterial')

        projection_plane.data.materials.append(new_material)
        projection_plane.active_material_index = len(projection_plane.material_slots) - 1
        new_material.name = camera_number_str

        #if (len(projection_plane.data.materials) >= 2):          
        #    loaded_img = bpy.data.images.load(123)

        # ----------- find nodes
        nodes = new_material.node_tree.nodes     
        base_color_texture_node = None
        mask_texture_node = None
        base_color_texture_node = None
        view_origin_coords_node = None
        view_direction_coords_node = None
        camera_y_rotation_node = None

        #label is the in the UI renamed name. Not the .name attribute!
        for node in nodes:
            #print(node.type) 
            if node.type == 'TEX_IMAGE':
                if node.label == 'MainTexture': 
                    base_color_texture_node = node

                if node.label == 'MaskTexture':
                    mask_texture_node = node

            if node.type == 'COMBXYZ':
                if node.label == 'ViewOriginCoords':
                    view_origin_coords_node = node
                    view_origin_coords_node.name = "ViewOriginCoords"
                if node.label == 'ViewDirectionCoords':
                    view_direction_coords_node = node
                    view_direction_coords_node.name = "ViewDirectionCoords"

            if node.type == 'VALUE':
                if node.label == 'YCameraRotation':
                    camera_y_rotation_node = node
                    camera_y_rotation_node.name = "YCameraRotationValue"

        
        if (base_color_texture_node.image):
            bpy.data.images.remove(base_color_texture_node.image, do_unlink=True)
            base_color_texture_node.image = None

        loaded_img = bpy.data.images.load(full_image_path)
        loaded_mask_img = bpy.data.images.load(full_mask_path)

        base_color_texture_node.image = loaded_img
        mask_texture_node.image = loaded_mask_img
        # ------------

        material_drivers = new_material.node_tree.animation_data.drivers

        # Check if there are any drivers
        if material_drivers:

            input_index = 0  
            for input_socket in view_origin_coords_node.inputs:
                driver_path = f'nodes["{view_origin_coords_node.name}"].inputs[{input_index}].default_value'
                #print("driver path: ", driver_path)
 

                # Check if there's a driver for this input socket
                driver = next((drv for drv in material_drivers if drv.data_path == driver_path), None)
                
                #for drv in material_drivers:
                    #print(drv.data_path)

                if driver:
                    # Access and print information about the driver
                    driver.driver.variables[0].targets[0].id = view_origin_obj
                input_index += 1

            input_index = 0  
            for input_socket in view_direction_coords_node.inputs:
                driver_path = f'nodes["{view_direction_coords_node.name}"].inputs[{input_index}].default_value'
            
                # Check if there's a driver for this input socket
                driver = next((drv for drv in material_drivers if drv.data_path == driver_path), None)
                
                if driver:
                    # Access and print information about the driver
                    driver.driver.variables[0].targets[0].id = view_direction_obj
                
                input_index += 1

            # camera y rotation node driver section
            for driver in material_drivers:
                #print(driver.data_path)
                #print("replicating path: ", f'nodes["{camera_y_rotation_node.name}"].outputs[0].default_value')
                if driver.data_path == f'nodes["{camera_y_rotation_node.name}"].outputs[0].default_value':
                    driver.driver.variables[0].targets[0].id = camera_obj



    return camera_obj

def createMainCamera(lfr_props):
    cameras_collection = lfr_props.cameras
    current_frame_number = bpy.context.scene.frame_current
    cameras_path = lfr_props.cameras_path
    full_img_path = cameras_path + cameras_collection[current_frame_number-1].image_file
    mask_img_path = lfr_props.img_mask
    camera_obj = createAndPrepareANewCamera(lfr_props, full_img_path, mask_img_path, 0)
    camera_obj.name = 'MainCamera'
    bpy.context.scene.camera = camera_obj # Set the active camera in the scene
    lfr_props.cam_obj = camera_obj

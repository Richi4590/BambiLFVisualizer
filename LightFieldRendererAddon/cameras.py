from datetime import datetime
import json
from math import radians
import bpy
from mathutils import *

from . plane import create_giant_projection_plane

from . util import *

try:
    from dateutil import parser
except ImportError:
    print("python-dateutil is not installed. Installing...")
    try:
        import pip
        pip.main(["install", "python-dateutil"])
        from dateutil import parser
        print("python-dateutil has been successfully installed.")
    except ImportError:
        print("Failed to install python-dateutil. Please install it manually.")
        raise

def parse_poses(posesUrl, nth_frame):

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

    total_frames = len(frames)/nth_frame

    for i in range(0, len(frames), nth_frame):
        pose = frames[i]
        quat = Quaternion()

        if "rotation" not in pose or "location" not in pose or "imagefile" not in pose:
            continue

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

        # Remove the colon from the timezone offset
        parsed_date = parser.parse(pose["timestamp"])

        # Define the format string without %z
        format_string = '%Y-%m-%dT%H:%M:%S.%f'


        camera = {
            "fovy": pose["fovy"],
            "aspect": 1.0,
            "near": 0.5,
            "far": 100,
            "position": pose["location"],
            "quaternion": quat,
            "image_file": pose["imagefile"],
            "timestamp": parsed_date
        }

        cameras.append(camera)

        #print(i/nth_frame, " out of ", total_frames)

    return cameras


def create_curve_data_and_key_frames(lfr_props):
    cameras_collection = lfr_props.cameras
    camera_obj = lfr_props.cam_obj

    # Create a path
    first_cam_location = cameras_collection[0].location
    bpy.ops.curve.primitive_bezier_curve_add(enter_editmode=False, align='WORLD', location=first_cam_location)

    path = bpy.context.active_object
    path.name = "LFR_Path"
    link_obj(bpy.context.scene.collection, path)    
    path.hide_render = True

    # Create red material
    material = bpy.data.materials.new(name="RedMaterial")
    material.diffuse_color = (1, 0, 0, 1)  # Set the color to red

    path_data = path.data
    path_data.materials.append(material)
    path_data.bevel_depth = 0.1 # Set the thickness (bevel depth) of the curve


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
        camera_obj.rotation_mode = 'XYZ'
        camera_obj.rotation_euler = Quaternion(camera_data.quaternion).to_euler()
        camera_obj.data.lens = camera_data.fovy  # Set the focal length (not FOV)
         
        camera_obj.keyframe_insert(data_path="location", index=-1)
        camera_obj.keyframe_insert(data_path="rotation_euler", index=-1)
        camera_obj.data.keyframe_insert(data_path="lens", index=-1)  # Keyframe for focal length
    
    # slight offset so that when viewing the cameras perspective in the viewport
    # we wont see clippings of the red line (even if visible, the red path is excluded during rendering)
    path.location = (path.location.x, path.location.y - 1.0, path.location.z)

def create_and_prep_new_camera(lfr_props, full_image_path, full_mask_path, camera_number):
    current_blend_directory = os.path.dirname(os.path.abspath(__file__)) 
    append_content_from_blend_file(os.path.abspath(current_blend_directory + '/Assets/projection_material.blend'), 'Collection', 'ProjectionGroup') # import the camera group from the blend file

    projection_plane = None
    range_obj_set = None


    if camera_number == 0:
        projection_plane = lfr_props.projection_mesh_obj
    else:
        range_obj_set = lfr_props.range_objects.add()
        range_obj_set.mesh = create_giant_projection_plane(lfr_props.dem_mesh_obj)
        range_obj_set.mesh.location = (range_obj_set.mesh.location.x, range_obj_set.mesh.location.y - (0.01 * camera_number), range_obj_set.mesh.location.z)

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
            if range_obj_set:
                range_obj_set.proj_cam = camera_obj
                range_obj_set.proj_cam.location = lfr_props.cameras[camera_number].location
                range_obj_set.original_location = camera_obj.location
                range_obj_set.proj_cam.rotation_mode = 'QUATERNION'
                range_obj_set.proj_cam.rotation_quaternion = lfr_props.cameras[camera_number].quaternion
                range_obj_set.proj_cam.data.lens = lfr_props.cameras[camera_number].fovy  # Set the focal length (not FOV)
            
        if ('ViewDirection' in obj.name):
            obj.name = 'ViewDirection_' + camera_number_str
            view_direction_obj = obj
            if range_obj_set:
                range_obj_set.view_dir_obj = view_direction_obj
        if ('ViewOrigin' in obj.name):
            obj.name = 'ViewOrigin_' + camera_number_str
            view_origin_obj = obj
            if range_obj_set:
                range_obj_set.view_origin_obj = view_origin_obj

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = camera_obj
    camera_obj.select_set(True)

    link_obj(bpy.context.scene.collection, camera_obj)    
    #camera_obj.name = 'camera_' + loaded_img.name 

    # Create a new material and refresh shader attributes
    # each new material corresponds to a specific camera
    # if (len(projection_plane.data.materials) >= 2): # -------------- really important, 1x assigned material means len of 1!
    #     new_material = projection_plane.data.materials[0].copy()
    # else:
    new_material = get_material_from_blend_file('Assets\projection_material.blend', 'ProjectionMaterial')

    if projection_plane:
        projection_plane.data.materials.append(new_material)
        projection_plane.active_material_index = len(projection_plane.material_slots) - 1
    else:
        range_obj_set.mesh.data.materials.append(new_material)
        range_obj_set.mesh.active_material_index = len(range_obj_set.mesh.material_slots) - 1
        
    new_material.name = camera_number_str

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

def create_main_camera(lfr_props):
    cameras_collection = lfr_props.cameras
    current_frame_number = bpy.context.scene.frame_current
    cameras_path = lfr_props.cameras_path
    full_img_path = cameras_path + cameras_collection[current_frame_number-1].image_file
    mask_img_path = lfr_props.img_mask
    camera_obj = create_and_prep_new_camera(lfr_props, full_img_path, mask_img_path, 0)
    camera_obj.name = 'MainCamera'
    bpy.context.scene.camera = camera_obj # Set the active camera in the scene
    lfr_props.cam_obj = camera_obj

def create_range_render_camera(position, ref_cam_euler_rotation):
    bpy.ops.object.select_all(action='DESELECT')
    # Create a new camera
    bpy.ops.object.camera_add(location=position)
    new_camera = bpy.context.object
    new_camera.name = "Range_Render_Camera"

    # Set the new camera's rotation to match the reference camera
    rotation_matrix = ref_cam_euler_rotation.to_matrix()
    new_camera.rotation_euler = rotation_matrix.to_euler()

    return new_camera

def set_current_camera_rendering_resolution(lfr_props, x = None, y = None):
    # in order to apply this to a specific camera
    # you need to do this bpy.context.scene.camera = camera_obj beforehand!
    if (x is None or y is None or
        x <= 0 or y <= 0):
        bpy.context.scene.render.resolution_x = lfr_props.rend_res_x 
        bpy.context.scene.render.resolution_y = lfr_props.rend_res_y 
    else:
        bpy.context.scene.render.resolution_x = x
        bpy.context.scene.render.resolution_y = y

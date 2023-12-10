from datetime import datetime
import json
from math import radians
import bpy
from mathutils import *
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

def createCurveDataAndKeyFramesOutOfCameras(cameras_collection):
    bpy.ops.object.mode_set(mode='OBJECT')
    # Create a follower camera object
    bpy.ops.object.camera_add(location=cameras_collection[0].location[:])  # Convert to tuple
    camera_obj = bpy.context.active_object
    bpy.context.scene.camera = camera_obj # Set the active camera in the scene
    bpy.context.scene.collection.objects.link(camera_obj)     # Link the camera to the scene

    # Create a path
    first_cam_location = cameras_collection[0].location
    bpy.ops.curve.primitive_bezier_curve_add(enter_editmode=False, align='WORLD', location=first_cam_location)
    path = bpy.context.active_object
    path.name = "LFR_Path"

    # Link the path to the scene
    bpy.context.scene.collection.objects.link(path)
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
    return camera_obj
    
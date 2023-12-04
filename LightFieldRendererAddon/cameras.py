from datetime import datetime
import json
from math import radians
import bpy
from mathutils import *
D = bpy.data
C = bpy.context

def parse_poses(posesUrl):

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

    positions = []
    cameras = []
    i = 0

    for pose in frames:
        quat = Quaternion()

        if len(pose["rotation"]) == 4:
            # Assume we have a quaternion
            quat.x, quat.y, quat.z, quat.w = pose["rotation"]
        elif len(pose["rotation"]) == 3:
            # Assume we have Euler angles
            euler = Euler(pose["rotation"], 'XYZ')
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
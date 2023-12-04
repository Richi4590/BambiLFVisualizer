import datetime
from math import radians
import bpy
from mathutils import *
D = bpy.data
C = bpy.context

def parse_poses(poses):

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
        pos = pose["location"]

        quat = Quaternion()

        if len(pose["rotation"]) == 4:
            # Assume we have a quaternion
            quat.x, quat.y, quat.z, quat.w = pose["rotation"]
        elif len(pose["rotation"]) == 3:
            # Assume we have Euler angles
            euler = (radians(angle) for angle in pose["rotation"])
            quat = Quaternion(euler=euler)

        positions.append(pos)

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
            "position": pos,
            "quaternion": quat,
            "image_file": pose["imagefile"],
            "timestamp": datetime.strptime(pose["timestamp"], "%Y-%m-%dT%H:%M:%S.%f%z")
        }

        cameras.append(camera)

        i += 1

    return cameras
import math
import os
import bmesh
import bpy
from mathutils import *
D = bpy.data
C = bpy.context

def import_dem(dem_path, rotation):

    if not dem_path.lower().endswith((".glb", ".gltf")):
        print("Invalid file format. Supported formats are .glb and .gltf.")
        return None

    bpy.ops.import_scene.gltf(
        filepath=dem_path
    )
    obj = bpy.context.active_object
    bpy.context.view_layer.objects.active = obj

    # Check if an object was imported
    if obj:
        # Convert rotation from degrees to radians
        rotation_radians = [math.radians(deg) for deg in rotation]
        # Ensure the rotation mode is set to Euler
        obj.rotation_mode = 'XYZ'
        # Set the rotation of the imported object
        obj.rotation_euler = rotation_radians
        #bpy.ops.object.origin_set(type='GEOMETRY_ORIGIN', center='BOUNDS')
        bpy.ops.object.shade_smooth(use_auto_smooth=False, auto_smooth_angle=0.523599)

        return obj
    else:
        return None
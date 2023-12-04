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
        bpy.ops.object.origin_set(type='GEOMETRY_ORIGIN', center='BOUNDS')

        return obj.name
    else:
        return None

    # Switch to Edit mode to access the mesh data
    #bpy.ops.object.mode_set(mode='EDIT')

    # Get the BMesh from the mesh data
    #bm = bmesh.from_edit_mesh(obj.data)

    # Optionally, you can manipulate the mesh here if needed

    # Return to Object mode
    #bpy.ops.object.mode_set(mode='OBJECT')
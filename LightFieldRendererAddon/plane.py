import math
import time
import bpy
from mathutils import *
from . util import *
D = bpy.data
C = bpy.context

def create_giant_projection_plane(source_obj):
    # Check if the source object exists
    if source_obj:
        # Duplicate the source object
        new_obj = source_obj.copy()    
        new_obj.data = source_obj.data.copy()
        new_obj.name = "Plane"
        bpy.context.collection.objects.link(new_obj)

        bpy.ops.object.select_all(action='DESELECT')
        new_obj.select_set(True)    
        bpy.context.view_layer.objects.active = new_obj
        
        offset_vector = Vector((0.0, -0.1, 0.0))
        new_obj.location += offset_vector

        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')

        ##### remove materials
        for material_slot in range(len(new_obj.material_slots)):
            new_obj.active_material_index = material_slot
            bpy.ops.object.material_slot_remove()

        # plane with no material
        #-each time a new camera gets generated, a new material gets assigned to this plane (camera.py)

        # Update the new object
        new_obj.data.update()
        return new_obj

def update_projection_material_tex(material, img_texture): 


    for image_data in bpy.data.images:
        if image_data == img_texture:
            continue

        if image_data.users == 0:
            bpy.data.images.remove(image_data, do_unlink=True)

    nodes = material.node_tree.nodes # Get the shader nodes of the material
    base_color_texture_node = None

    for node in nodes:
        if node.type == 'TEX_IMAGE':
            if node.label == 'MainTexture': #label is the in the UI renamed name. Not the .name attribute!
                    base_color_texture_node = node

    # Assign the new image
    base_color_texture_node.image = img_texture

    # if is_rendering() is False:
    #     bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True) #memory cleanup during brushing
    # # Iterate through all image data blocks


            
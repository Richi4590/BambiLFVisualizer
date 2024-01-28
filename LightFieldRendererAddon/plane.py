import math
import time
import bpy
from mathutils import *
from . util import *
D = bpy.data
C = bpy.context

def create_singular_giant_plane(source_obj, full_image_path, full_mask_path):
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
        
        offset_vector = Vector((0.0, -4.0, 0.0))
        new_obj.location += offset_vector

        ##### remove materials
        for material_slot in range(len(new_obj.material_slots)):
            new_obj.active_material_index = material_slot
            bpy.ops.object.material_slot_remove()

        # Create a new material for the new object
        new_material = bpy.data.materials.new(name="overlay")
        new_material.blend_method = 'CLIP'
        new_obj.data.materials.append(new_material)

        # Use the new material in all material slots
        for material_slot in new_obj.material_slots:
            material_slot.material = new_material

        # Set up the material nodes for the new material
        new_material.use_nodes = True
        new_tree = new_material.node_tree
        new_tree.nodes.clear()
        #####

        # Create nodes
        tex_coord_node = new_tree.nodes.new(type='ShaderNodeTexCoord')
        mapping_node = new_tree.nodes.new(type='ShaderNodeMapping')
        image_texture_node = new_tree.nodes.new(type='ShaderNodeTexImage')
        mask_texture_node = new_tree.nodes.new(type='ShaderNodeTexImage')
        principled_node = new_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
        material_output_node = new_tree.nodes.new(type='ShaderNodeOutputMaterial')

        mapping_node.vector_type = 'TEXTURE' # set mapping type to texture
        rotation_radians = [math.radians(deg) for deg in (90, 0, 0)]
        mapping_node.inputs[2].default_value = rotation_radians

        # Link nodes
        links = new_material.node_tree.links
        links.new(tex_coord_node.outputs["Generated"], mapping_node.inputs[0])
        links.new(mapping_node.outputs[0], image_texture_node.inputs[0])
        links.new(mapping_node.outputs[0], mask_texture_node.inputs[0])
        links.new(image_texture_node.outputs["Color"], principled_node.inputs["Base Color"])
        links.new(mask_texture_node.outputs["Color"], principled_node.inputs["Alpha"])
        links.new(principled_node.outputs["BSDF"], material_output_node.inputs["Surface"])

        # Set up image texture
        image_texture_node.image = bpy.data.images.load(full_image_path)
        image_texture_node.name = "base_color_frame_texture"
        mask_texture_node.image = bpy.data.images.load(full_mask_path)
        image_texture_node.extension = 'CLIP'
        mask_texture_node.extension = 'CLIP'

        # Update the new object
        new_obj.data.update()
        return new_obj

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

def create_overlay_material(plane_obj, img_path, mask_img_path):
    
    obj = plane_obj

    # Check if the object has a material
    if len(obj.data.materials) > 0:

        if "overlay" not in obj.data.materials:
            new_material = bpy.data.materials.new(name="overlay")
            new_material.use_nodes = True  # If True, the material will use the node editor
            link_obj(bpy.context.scene.collection, obj)    
            obj.data.materials.clear()
            obj.data.materials.append(new_material)

        new_material.blend_method = 'CLIP'

        # Assume the object has only one material (change index if multiple materials)
        active_material = obj.data.materials[0] #new material

        # Clear all existing nodes from the material node tree
        for node in active_material.node_tree.nodes:
            active_material.node_tree.nodes.remove(node)

        # Define the file paths for your two textures
        base_color_texture_path = img_path
        alpha_texture_path = mask_img_path

        # Create two texture nodes and load the textures
        base_color_texture_node = active_material.node_tree.nodes.new(type='ShaderNodeTexImage')
        base_color_texture_node.location = (0, 0)
        base_color_texture_node.image = bpy.data.images.load(base_color_texture_path)
        base_color_texture_node.name = "base_color_frame_texture"

        alpha_texture_node = active_material.node_tree.nodes.new(type='ShaderNodeTexImage')
        alpha_texture_node.location = (350, 0)
        alpha_texture_node.image = bpy.data.images.load(alpha_texture_path)

        # Create a Principled BSDF shader node
        principled_shader_node = active_material.node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
        principled_shader_node.location = (850, 0)

        # Create an Output Material node
        material_output_node = active_material.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
        material_output_node.location = (1200, 0)

        # Link nodes in the material node tree
        active_material.node_tree.links.new(base_color_texture_node.outputs["Color"], principled_shader_node.inputs["Base Color"])
        active_material.node_tree.links.new(alpha_texture_node.outputs["Color"], principled_shader_node.inputs["Alpha"])
        active_material.node_tree.links.new(principled_shader_node.outputs["BSDF"], material_output_node.inputs["Surface"])

        print(f"Material '{active_material.name}' updated successfully with two textures.")
    else:
        print("No material assigned to the active object.")

def update_overlay_material_path(plane_obj, img_path):
    
    obj = plane_obj

    # Check if the object has a material
    if len(obj.data.materials) > 0:
        for mat in obj.data.materials:
            if "overlay" in mat.name:
                active_material = obj.data.materials[0] #new material

                nodes = active_material.node_tree.nodes                 # Get the shader nodes of the material
                #alpha_texture_path = mask_img_path
                base_color_texture_node = nodes.get('base_color_frame_texture')

                loaded_img = bpy.data.images.load(img_path)
                
                if base_color_texture_node.image:
                    bpy.data.images.remove(base_color_texture_node.image, do_unlink=True)
                    base_color_texture_node.image = None
                
                base_color_texture_node.image = loaded_img

def update_overlay_material_tex(plane_obj, img_texture): 
    obj = plane_obj
    # Check if the object has a material
    if len(obj.data.materials) > 0:
        for mat in obj.data.materials:
            if "overlay" in mat.name:
                active_material = obj.data.materials[0] #new material

                nodes = active_material.node_tree.nodes                 # Get the shader nodes of the material
                #alpha_texture_path = mask_img_path
                base_color_texture_node = nodes.get('base_color_frame_texture')
                
                if base_color_texture_node.image != img_texture:
                    bpy.data.images.remove(base_color_texture_node.image, do_unlink=True)
                    base_color_texture_node.image = None
                
                base_color_texture_node.image = img_texture

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


            
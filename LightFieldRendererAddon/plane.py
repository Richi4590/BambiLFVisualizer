import bpy
from mathutils import *
D = bpy.data
C = bpy.context

def create_parent(name):
    # Create an empty object to serve as the parent
    parent_obj = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(parent_obj)
    bpy.context.view_layer.objects.active = parent_obj
    bpy.ops.object.select_all(action='DESELECT')
    parent_obj.select_set(True)

    return parent_obj

def add_child(parent, child):
    # Parent the child to the parent
    child.select_set(True)
    bpy.context.view_layer.objects.active = parent
    bpy.ops.object.parent_set(type='OBJECT')

def remove_children(parent):
    bpy.ops.object.mode_set(mode='OBJECT')
    # Remove all children of the parent
    children = [child for child in bpy.data.objects if child.parent == parent]
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = parent
    parent.select_set(True)

    # Select children manually
    for child in children:
        child.select_set(True)

    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

    # Delete the children
    for child in children:
        bpy.data.objects.remove(child, do_unlink=True)

def create_overlay_material(plane_obj, img_path, mask_img_path):
    
    obj = plane_obj

    # Check if the object has a material
    if len(obj.data.materials) > 0:

        if "overlay" not in obj.data.materials:
            new_material = bpy.data.materials.new(name="overlay")
            new_material.use_nodes = True  # If True, the material will use the node editor
            bpy.context.scene.collection.objects.link(obj)
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
                
                if base_color_texture_node.image:
                    bpy.data.images.remove(base_color_texture_node.image, do_unlink=True)
                    base_color_texture_node.image = None
                
                base_color_texture_node.image = img_texture
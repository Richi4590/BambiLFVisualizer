bl_info = {
    "name": "Light Field Renderer",
    "author": "Serban Richardo & Schmalzer Lukas",
    "version": (0, 1),
    "blender": (4, 0, 0),
    "location": "View3D > Toolbar > LFR",
    "description": "Load, view, render and adjust light field rendering of a dataset",
    "warning": "",
    "wiki_url": "",
    "category": "",
}

import addon_utils
import bpy

from . lightfields import createImgWithShaderAndModifier
from . dem import *
from . util import *
from . cameras import *

class CameraDataPropertyGroup(bpy.types.PropertyGroup):
    fovy: bpy.props.FloatProperty(name="Field of View")
    aspect: bpy.props.FloatProperty(name="Aspect Ratio")
    near: bpy.props.FloatProperty(name="Near")
    far: bpy.props.FloatProperty(name="Far")

    position: bpy.props.FloatVectorProperty(
        name="Position",
        default=(0.0, 0.0, 0.0),
        size=3,
    )
    quaternion: bpy.props.FloatVectorProperty(
        name="Quaternion",
        default=(0.0, 0.0, 0.0, 1.0),
        size=4,
    )
    image_file: bpy.props.StringProperty(
        name="Image File",
        default="",
    )
    timestamp: bpy.props.StringProperty(
        name="Timestamp",
        default="",
    )

#maybe irrelevant
class CurveDataPropertyGroup(bpy.types.PropertyGroup):
    curve_name: bpy.props.StringProperty()
    curve: bpy.props.PointerProperty(type=bpy.types.Object)

class LFRProperties(bpy.types.PropertyGroup):
    cameras: bpy.props.CollectionProperty(type=CameraDataPropertyGroup)
    curve_data: bpy.props.CollectionProperty(type=CurveDataPropertyGroup) #maybe irrelevant
    dem_mesh_obj: bpy.props.PointerProperty(type=bpy.types.Object)
    cam_obj: bpy.props.PointerProperty(type=bpy.types.Object)
    pinhole_frame_obj: bpy.props.PointerProperty(type=bpy.types.Object) # when only watchin 1 frame at a time, its only 1x plane, 
                                                                    # no need to destroy and create another one each new keyframe
    pinhole_view: bpy.props.BoolProperty(default=True)
    
    # amount of frames to be used to "interpolate"
    frames_to_interpolate: bpy.props.IntProperty(
        default=0,
        min=0,
        max=100
    )

    #focus value for the interpolation
    focus: bpy.props.IntProperty(
        default=0,
        min=-50,
        max=50
    )  


    folder_path: bpy.props.StringProperty(
        name="Folder Path",
        subtype='DIR_PATH',
        default="",
    )

    #debug default should be empty for all
    dem_path: bpy.props.StringProperty(
        name="DEM Path",
        subtype='FILE_PATH',
        default="E:/u_Semester_Project/Data/Parkplatz_1ms/Data/dem/dem_mesh_r2.glb", 
    )

    cameras_path: bpy.props.StringProperty(
        name="CAMERAS Path",
        subtype='FILE_PATH',
        default="E:/u_Semester_Project/Data/Parkplatz_1ms/Frames_T/", 
    )

class LoadLFRDataOperator(bpy.types.Operator):
    bl_idname = "wm.load_data"
    bl_label = "Load LFR Data"

    def execute(self, context):
        if post_frame_change_handler in bpy.app.handlers.frame_change_post:
            bpy.app.handlers.frame_change_post.remove(post_frame_change_handler)

        util.clear_scene_except_lights()
        lfr_props = context.scene.lfr_properties
        lfr_props.dem_mesh_obj = dem.import_dem(lfr_props.dem_path, rotation=(0, 0, 0)) #euler rotation

        cameras_collection = lfr_props.cameras
        cameras_collection.clear()

        # Add a new camera data item to the collection
        camerasData = parse_poses(lfr_props.cameras_path)

        #print(camerasData[0]["fovy"]) #debug

        #takes the camera dataset and loads it into the lfr_properties.cameras (cameras_collection)
        if (camerasData is not None):
            for camData in camerasData:
                camQuaternion = [camData["quaternion"].x, camData["quaternion"].y, camData["quaternion"].z, camData["quaternion"].w]
                camTimeStamp = camData["timestamp"].isoformat()
                pos = camData["position"]

                # 0 = X, 1 = Y, 2 = Z
                # blender uses XZY 
                z_temp = pos[2]
                pos[2] = pos[1]
                pos[1] = z_temp * -1

                new_camera = cameras_collection.add()
                new_camera.fovy = camData["fovy"]
                new_camera.aspect = camData["aspect"]
                new_camera.near = camData["near"]
                new_camera.far = camData["far"]
                new_camera.position = pos
                new_camera.quaternion = camQuaternion
                new_camera.image_file = camData["image_file"]
                new_camera.timestamp = camTimeStamp

            #print(lfr_props.cameras) #debug

            lfr_props.cam_obj = createCurveDataAndKeyFramesOutOfCameras(cameras_collection) # rendering camera gets generated inside
            #print(lfr_props.cam_obj.name) #debug
            bpy.app.handlers.frame_change_post.append(post_frame_change_handler)
            lfr_props.pinhole_frame_obj = createImgWithShaderAndModifier(lfr_props.cam_obj, lfr_props.cameras_path, lfr_props.cameras[0].image_file, lfr_props.dem_mesh_obj.name) #create a plane once
            bpy.context.scene.frame_set(0) # set to frame 0 again, triggers post_frame_change_handler() once

            #print(cameras_collection[0].quaternion[0], cameras_collection[0].quaternion[1], cameras_collection[0].quaternion[2]) #debug

            bpy.ops.object.mode_set(mode="OBJECT")    
            bpy.ops.object.select_all(action='DESELECT') # deselect everything
            bpy.data.objects[lfr_props.cam_obj.name].select_set(True) # have camera selected after loading
        return {'FINISHED'}

#---------------------------------
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

def  setNewTexture(plane_obj, img_path):
    material = plane_obj.data.materials[0]

    # Check if the material has a texture node
    if material and material.use_nodes:
        texture_node = None
        for node in material.node_tree.nodes:
            if node.type == 'TEX_IMAGE':
                texture_node = node
                break

        # Update the texture image
        if texture_node:
            texture_node.image = bpy.data.images.load(img_path)
        else:
            print("No image texture node found in the material.")

def post_frame_change_handler(scene): #executes after a new keyframe loaded
    current_frame_number = scene.frame_current
    lfr_prp = scene.lfr_properties

    if current_frame_number < len(lfr_prp.cameras):
        if lfr_prp.pinhole_view:
            lfr_prp.pinhole_frame_obj.location = lfr_prp.cam_obj.location
            full_img_path = lfr_prp.cameras_path + lfr_prp.cameras[current_frame_number].image_file
            setNewTexture(lfr_prp.pinhole_frame_obj, full_img_path)
        #else
            #remove_children(lfr_prp.frames_root_obj) #remove any object in parent if any exist at all
            #child_frame = createImgWithShaderAndModifier(lfr_prp.cam_obj, lfr_prp.cameras_path, lfr_prp.cameras[current_frame_number].image_file, lfr_prp.dem_mesh_obj.name)
            #add_child(lfr_prp.frames_root_obj, child_frame)

#---------------------------------
class LFRPanel(bpy.types.Panel):
    bl_label = "Light Field Renderer"
    bl_idname = "PT_Bambi_LFR"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "LFR"

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        addon_props = context.scene.lfr_properties
        layout.prop(addon_props, "folder_path", text="Set Data Path")
        layout.prop(addon_props, "dem_path", text="Set DEM Path") # Debug
        layout.prop(addon_props, "cameras_path", text="Set Cameras Path") # Debug
        row = layout.row()
        row.operator("wm.load_data", text="Load LFR Data")
        layout.prop(addon_props, "frames_to_interpolate", text="Amount of frames to interpolate")
        layout.prop(addon_props, "focus", text="Focus")
        layout.prop(addon_props, "pinhole_view", text="View as pinhole?")


class SubPanelA(bpy.types.Panel):
    bl_label = "SubPanel Test A"
    bl_idname = "PT_Bambi_LFR_Pan_A"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Subpanel A"
    bl_parent_id = "PT_Bambi_LFR" # important in order to make a subpanel!
    bl_options = {"DEFAULT_CLOSED"}
        
    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.label(text="This is Panel A", icon="HEART")
            
            
def register():
    addon_utils.enable('io_import_images_as_planes', default_set=True, persistent=True, handle_error=None)
    bpy.utils.register_class(CameraDataPropertyGroup)
    bpy.utils.register_class(CurveDataPropertyGroup)
    bpy.utils.register_class(LFRProperties)
    bpy.types.Scene.lfr_properties = bpy.props.PointerProperty(type=LFRProperties)
    bpy.utils.register_class(LoadLFRDataOperator)
    bpy.utils.register_class(LFRPanel)
    bpy.utils.register_class(SubPanelA)


def unregister():
    addon_utils.disable('io_import_images_as_planes', default_set=False, handle_error=None)
    bpy.utils.unregister_class(CameraDataPropertyGroup)
    bpy.utils.unregister_class(CurveDataPropertyGroup)
    bpy.utils.unregister_class(LFRProperties)
    del bpy.types.Scene.lfr_properties
    bpy.utils.unregister_class(LoadLFRDataOperator)
    bpy.utils.unregister_class(LFRPanel)
    bpy.utils.unregister_class(SubPanelA)
    if post_frame_change_handler in bpy.app.handlers.frame_change_post:
        bpy.app.handlers.frame_change_post.remove(post_frame_change_handler)

    
if __name__ == "__main__":
    register()
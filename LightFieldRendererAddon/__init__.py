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

from . lightfields import *
from . dem import *
from . util import *
from . cameras import *
from . plane import *
from . properties import *

class LoadLFRDataOperator(bpy.types.Operator):
    bl_idname = "wm.load_data"
    bl_label = "Load LFR Data"

    def execute(self, context):

        if post_frame_change_handler in bpy.app.handlers.frame_change_post:
            bpy.app.handlers.frame_change_post.remove(post_frame_change_handler)

        util.clear_scene()
        bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True) #slight memory clean up
        purge_all_addon_property_data(context)

        lfr_prp = context.scene.lfr_properties
        lfr_prp.view_range_of_images = False

        absolute_data_path_root = os.path.abspath(os.path.join(lfr_prp.main_imgs_path, "..")).replace("\\", "/")
        absolute_data_path_dem_folder = absolute_data_path_root + "/Data/dem"
        absolute_data_path_dem_file = find_first_file(absolute_data_path_dem_folder, ".glb")
        absolute_data_path_mask = find_file_by_partial_name(lfr_prp.main_imgs_path, "mask")

        lfr_prp.cameras_path = lfr_prp.main_imgs_path
        lfr_prp.dem_path = absolute_data_path_dem_file
        lfr_prp.img_mask = absolute_data_path_mask

        lfr_prp.dem_mesh_obj = dem.import_dem(lfr_prp.dem_path, rotation=(0, 0, 0)) #euler rotation

        lfr_prp.render_path = get_absolute_file_path_from_relative_path("Pics\\") #with one \ its unterminated string
        set_render_path("Pics\Render Result.png")

        cameras_collection = lfr_prp.cameras
        cameras_collection.clear()

        # Add a new camera data item to the collection
        camerasData = parse_poses(lfr_prp.cameras_path, lfr_prp.every_nth_frame)

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
                new_camera.location = pos
                new_camera.quaternion = camQuaternion
                new_camera.image_file = camData["image_file"]
                new_camera.timestamp = camTimeStamp

            if (context.scene.frame_current > len(cameras_collection)-1): 
                bpy.context.scene.frame_set(1)

            #print(lfr_props.cameras) #debug
            initStartupObjects(self, context) # generates main camera and potentially a projection plane

            createCurveDataAndKeyFramesOutOfCameras(lfr_prp) # rendering camera gets generated inside

            #print(lfr_props.cam_obj.name) #debug
            bpy.app.handlers.frame_change_post.append(post_frame_change_handler) 

            bpy.context.scene.frame_set(1)

            #print(cameras_collection[0].quaternion[0], cameras_collection[0].quaternion[1], cameras_collection[0].quaternion[2]) #debug

            bpy.ops.object.mode_set(mode="OBJECT")    
            bpy.ops.object.select_all(action='DESELECT') # deselect everything
            bpy.data.objects[lfr_prp.cam_obj.name].select_set(True) # have camera selected after loading
        return {'FINISHED'}

class RenderRangeOfImagesOperator(bpy.types.Operator):
    bl_idname = "wm.render_image_range"
    bl_label = "Render Image Range"

    def execute(self, context):
        lfr_prp = context.scene.lfr_properties
        current_frame_number = context.scene.frame_current-1

        lfr_prp.view_range_of_images = False

        #----
        if post_frame_change_handler in bpy.app.handlers.frame_change_post:
            bpy.app.handlers.frame_change_post.remove(post_frame_change_handler)

        applyImagesAndPositionsToPlanesFromRange(lfr_prp, current_frame_number)
        offset_proj_cameras_with_focus(lfr_prp, current_frame_number) #reposition cameras depending on focus
        result_image = combine_images(lfr_prp)
        bpy.app.handlers.frame_change_post.append(post_frame_change_handler) 
        #----
        save_image_to_disk(lfr_prp.render_path, "combined_range_image.png", result_image, True)
        delete_temp_objects_of_range_rendering(lfr_prp)
        
        return {'FINISHED'}
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
        layout.prop(addon_props, "main_imgs_path", text="Set Folder Path") 
        #layout.prop(addon_props, "dem_path", text="Set DEM Path") # Debug
        #layout.prop(addon_props, "cameras_path", text="Set Cameras Path") # Debug
        layout.prop(addon_props, "every_nth_frame", text="Use every n frame")
        row = layout.row()
        row.operator("wm.load_data", text="Load LFR Data")
        layout.prop(addon_props, "range_to_interpolate", text="Amount of frames to interpolate")
        layout.prop(addon_props, "focus", text="Focus")
        row = layout.row()
        layout.prop(addon_props, "view_range_of_images", text="View range of images?")
        row.operator("wm.render_image_range", text="Render Range of Images")


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
    bpy.utils.register_class(RangeMeshPropertyGroup)
    bpy.utils.register_class(CameraDataPropertyGroup)
    bpy.utils.register_class(ImagePropertyGroup)
    bpy.utils.register_class(LFRProperties)
    bpy.types.Scene.lfr_properties = bpy.props.PointerProperty(type=LFRProperties)
    bpy.utils.register_class(LoadLFRDataOperator)
    bpy.utils.register_class(RenderRangeOfImagesOperator)
    bpy.utils.register_class(LFRPanel)
    bpy.utils.register_class(SubPanelA)


def unregister():
    addon_utils.disable('io_import_images_as_planes', default_set=False, handle_error=None)
    bpy.utils.unregister_class(RangeMeshPropertyGroup)
    bpy.utils.unregister_class(CameraDataPropertyGroup)
    bpy.utils.unregister_class(ImagePropertyGroup)
    bpy.utils.unregister_class(LFRProperties)
    del bpy.types.Scene.lfr_properties
    bpy.utils.unregister_class(LoadLFRDataOperator)
    bpy.utils.unregister_class(RenderRangeOfImagesOperator)
    bpy.utils.unregister_class(LFRPanel)
    bpy.utils.unregister_class(SubPanelA)
    if post_frame_change_handler in bpy.app.handlers.frame_change_post:
        bpy.app.handlers.frame_change_post.remove(post_frame_change_handler)

    
if __name__ == "__main__":
    register()
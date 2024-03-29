bl_info = {
    "name": "Light Field Renderer",
    "author": "Serban Richardo & Schmalzer Lukas",
    "version": (0, 9),
    "blender": (4, 0, 0),
    "location": "View3D > Toolbar > LFR",
    "description": "Load, view, render and adjust light field rendering of a dataset",
    "warning": "",
    "wiki_url": "",
    "category": "",
}

import re
import addon_utils
import bpy
from . cameras import *
from . dem import *
from . lightfields import *
from . plane import *
from . properties import *
from . util import clear_scene

class LoadLFRDataOperator(bpy.types.Operator):
    bl_idname = "wm.load_data"
    bl_label = "Load LFR Data"

    def execute(self, context):
        bpy.data.scenes["Scene"].render.use_lock_interface = True

        if pre_frame_change_handler in bpy.app.handlers.frame_change_pre:
            bpy.app.handlers.frame_change_pre.remove(pre_frame_change_handler)

        clear_scene()
        bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True) #slight memory clean up
        purge_all_addon_property_data(context)

        lfr_prp = context.scene.lfr_properties
        lfr_prp.view_range_of_images = False

        correctly_set_or_overwrite_path_strings(lfr_prp)

        lfr_prp.dem_mesh_obj = import_dem(lfr_prp.dem_path, rotation=(0, 0, 0)) #euler rotation

        cameras_collection = lfr_prp.cameras
        cameras_collection.clear()

        # Add a new camera data item to the collection
        cameras_data = parse_poses(lfr_prp.json_path, lfr_prp.every_nth_frame)

        #takes the camera dataset and loads it into the lfr_properties.cameras (cameras_collection)
        if (cameras_data is not None):
            for camData in cameras_data:
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

            init_startup_objs(self, context) # generates main camera and potentially a projection plane
            create_curve_data_and_key_frames(lfr_prp) # rendering camera gets generated inside
            bpy.app.handlers.frame_change_pre.append(pre_frame_change_handler) 
            bpy.context.scene.frame_set(1)

            bpy.ops.object.mode_set(mode="OBJECT")    
            bpy.ops.object.select_all(action='DESELECT') # deselect everything
            bpy.data.objects[lfr_prp.cam_obj.name].select_set(True) # have camera selected after loading
        return {'FINISHED'}

def render_cleanup_memory(scene):
    current_frame_number = scene.frame_current

    if current_frame_number == 0:
        bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=False, do_recursive=False) #slight memory clean up

    #if current_frame_number % 250 == 0:
        #print("purging!!")
        #bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=False, do_recursive=False) #slight memory clean up

class RenderRangeOfImagesOperator(bpy.types.Operator):
    bl_idname = "wm.render_image_range"
    bl_label = "Render Image Range"

    def execute(self, context):
        lfr_prp = context.scene.lfr_properties
        current_frame_number = context.scene.frame_current-1

        lfr_prp.view_range_of_images = False

        #----
        if pre_frame_change_handler in bpy.app.handlers.frame_change_pre:
            bpy.app.handlers.frame_change_pre.remove(pre_frame_change_handler)

        apply_images_and_positions_to_planes_from_range(lfr_prp, current_frame_number)
        offset_proj_cameras_with_focus(lfr_prp, current_frame_number) #reposition cameras depending on focus
        result_image = combine_images(lfr_prp)
        bpy.app.handlers.frame_change_pre.append(pre_frame_change_handler) 
        #----
        save_image_to_disk(lfr_prp.render_path, "combined_range_image.png", result_image, True)
        delete_temp_objects_of_range_rendering(lfr_prp)
        
        return {'FINISHED'}

class RenderFromCurrentKeyFrameOperator(bpy.types.Operator):
    bl_idname = "wm.render_from_keyframe"
    bl_label = "Render From Current KeyFrame"

    def execute(self, context):   
        lfr_props = context.scene.lfr_properties
        current_frame_number = context.scene.frame_current-1
        end_key_Frame = context.scene.frame_end
        print("rendering...")

        if lfr_props.render_as_animation is True:
            bpy.context.scene.render.image_settings.file_format = 'FFMPEG'
            bpy.context.scene.render.ffmpeg.format = 'MPEG4'
            bpy.context.scene.render.ffmpeg.codec = 'H264'
            bpy.context.scene.render.filepath = lfr_props.render_path + "Render_Result_Video.mp4"

            # Iterate through the keyframes and render them
            for i in range(current_frame_number, end_key_Frame):
                bpy.context.scene.frame_set(i)
                bpy.ops.render.render(animation=True)
        else:
            bpy.context.scene.render.image_settings.file_format = 'JPEG'

            if lfr_props.save_rend_images is False:
                if has_file_with_extension(lfr_props.render_path) is False:
                    bpy.context.scene.render.filepath = lfr_props.render_path + "Render_Result." + bpy.context.scene.render.image_settings.file_format 

            # Iterate through the keyframes and render them
            for i in range(current_frame_number, end_key_Frame):
                bpy.context.scene.frame_set(i)
                if lfr_props.save_rend_images:
                    bpy.context.scene.render.filepath = lfr_props.render_path + f"Render_Result_{i}." + bpy.context.scene.render.image_settings.file_format

                bpy.ops.render.render(write_still=True)

        print("done rendering")
        bpy.context.scene.frame_set(current_frame_number) #set back to initial key-frame
        return {'FINISHED'}

class OpenRenderFolderOperator(bpy.types.Operator):
    bl_idname = "wm.open_render_folder"
    bl_label = "Open Render Folder"

    def execute(self, context):

        render_output_path = bpy.context.scene.render.filepath
        file_type_regex = r"\.[^.\\/]+$"

        # Check if the path has a file at the end with regex (excludes folder paths)
        if re.search(file_type_regex, render_output_path):
            # removes the /Render Result.png from the path
            render_output_path = os.path.abspath(os.path.join(bpy.context.scene.render.filepath, "..")) 
            render_output_path = render_output_path.replace("\\", "/") # replace \ to /

        # Open the file explorer with the render output folder (Windows)
        if render_output_path:
            os.startfile(render_output_path)
        
        return {'FINISHED'}
    
class ClearRenderFolderOperator(bpy.types.Operator):
    bl_idname = "wm.clear_render_folder"
    bl_label = "Clear Render Folder"

    def execute(self, context):

        render_output_folder = bpy.context.scene.render.filepath
        allowed_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.mp4', '.avi', '.mkv']

        file_type_regex = r"\.[^.\\/]+$"

        # Check if the path has a file at the end with regex (excludes folder paths)
        if re.search(file_type_regex, render_output_folder):
        # removes the /Render Result.png from the path
            render_output_folder = os.path.abspath(os.path.join(bpy.context.scene.render.filepath, "..")) 
            render_output_folder = render_output_folder.replace("\\", "/") # replace \ to /

        # Clear the contents of the folder
        if os.path.exists(render_output_folder) and os.path.isdir(render_output_folder):
            for filename in os.listdir(render_output_folder):
                file_path = os.path.join(render_output_folder, filename)
                try:
                    if os.path.isfile(file_path):
                         # Check if the file has an allowed extension
                        _, file_extension = os.path.splitext(filename)
                        if file_extension.lower() in allowed_extensions:
                            os.remove(file_path)
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")
        else:
            print(f"Folder '{render_output_folder}' does not exist or is not a directory.")
        
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
        layout.prop(addon_props, "folder_path", text="Set Folder Path") 
        layout.prop(addon_props, "every_nth_frame", text="Use every n frame")
        row = layout.row()
        row.operator("wm.load_data", text="Load LFR Data")
        row = layout.row()
        row.prop(addon_props, "range_to_interpolate", text="Amount of frames to interpolate")
        row.prop(addon_props, "focus", text="Focus")
        row = layout.row()
        row.prop(addon_props, "view_range_of_images", text="View range of images?")
        row = layout.row()
        row.operator("wm.render_image_range", text="Render Range of Images")
        layout.operator("wm.render_from_keyframe", text="Render Images From Current KeyFrame")


class AdditionalOptionsPanel(bpy.types.Panel):
    bl_label = "Additional Options"
    bl_idname = "PT_Bambi_LFR_Opt_Panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Additional_Options"
    bl_parent_id = "PT_Bambi_LFR" # important in order to make a subpanel!
    bl_options = {"DEFAULT_CLOSED"}
        
    def draw(self, context):
        layout = self.layout
        row = layout.row()
        addon_props = context.scene.lfr_properties
        layout.prop_search(addon_props, "man_rend_cam", context.scene, "objects", icon='OBJECT_DATA')
        row = layout.row(align=True)
        row.prop(addon_props, "rend_res_x", text="Rendering Resolution X") 
        row.prop(addon_props, "rend_res_y", text="Rendering Resolution Y")
        row = layout.row(align=True)
        row.prop(addon_props, "save_rend_images", text="Save Rendered Images Individually?") 
        row.prop(addon_props, "render_as_animation", text="Render as video?")
        row.operator("wm.open_render_folder", text="Open Render Folder")
        row.operator("wm.clear_render_folder", text="Clear Render Folder Content")
        row = layout.row(align=False)
        layout.prop(addon_props, "man_render_path", text="Set Render Folder")  
        layout.prop(addon_props, "man_dem_path", text="Set DEM File Path Manually") 
        layout.prop(addon_props, "man_json_path", text="Set JSON File Path Manually") 
     
def register():
    addon_utils.enable('io_import_images_as_planes', default_set=True, persistent=True, handle_error=None)
    bpy.utils.register_class(RangeMeshPropertyGroup)
    bpy.utils.register_class(CameraDataPropertyGroup)
    bpy.utils.register_class(ImagePropertyGroup)
    bpy.utils.register_class(LFRProperties)
    bpy.types.Scene.lfr_properties = bpy.props.PointerProperty(type=LFRProperties)
    bpy.utils.register_class(LoadLFRDataOperator)
    bpy.utils.register_class(RenderRangeOfImagesOperator)
    bpy.utils.register_class(OpenRenderFolderOperator)
    bpy.utils.register_class(ClearRenderFolderOperator)
    bpy.utils.register_class(RenderFromCurrentKeyFrameOperator)
    bpy.utils.register_class(LFRPanel)
    bpy.utils.register_class(AdditionalOptionsPanel)

    bpy.app.handlers.frame_change_pre.append(pre_frame_change_handler)


def unregister():        
    addon_utils.disable('io_import_images_as_planes', default_set=False, handle_error=None)

    bpy.utils.unregister_class(RangeMeshPropertyGroup)
    bpy.utils.unregister_class(CameraDataPropertyGroup)
    bpy.utils.unregister_class(ImagePropertyGroup)
    bpy.utils.unregister_class(LFRProperties)
    del bpy.types.Scene.lfr_properties
    bpy.utils.unregister_class(LoadLFRDataOperator)
    bpy.utils.unregister_class(RenderRangeOfImagesOperator)
    bpy.utils.unregister_class(OpenRenderFolderOperator)
    bpy.utils.unregister_class(ClearRenderFolderOperator)
    bpy.utils.unregister_class(RenderFromCurrentKeyFrameOperator)
    bpy.utils.unregister_class(LFRPanel)
    bpy.utils.unregister_class(AdditionalOptionsPanel)

    if pre_frame_change_handler in bpy.app.handlers.frame_change_pre:
        bpy.app.handlers.frame_change_pre.remove(pre_frame_change_handler)

if __name__ == "__main__":
    register()
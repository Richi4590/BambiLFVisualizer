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

import bpy
from . dem import *
from . util import *

class FolderPathAddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

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
        default="E:/u_Semester_Project/Data/Parkplatz_1ms/Frames_T/matched_poses.json", 
    )

class LoadLFRDataOperator(bpy.types.Operator):
    bl_idname = "wm.load_data"
    bl_label = "Load LFR Data"

    def execute(self, context):
        util.clear_scene_except_lights()
        dem.import_dem(context.preferences.addons[__name__].preferences.dem_path, rotation=(90, 0, 0)) #euler rotation
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
          
        addon_prefs = context.preferences.addons[__name__].preferences
        layout.prop(addon_prefs, "folder_path", text="Set Data Path")
        layout.prop(addon_prefs, "dem_path", text="Set DEM Path") # Debug
        layout.prop(addon_prefs, "cameras_path", text="Set Cameras Path") # Debug
        row = layout.row()
        row.operator("wm.load_data", text="Load LFR Data")

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
    bpy.utils.register_class(FolderPathAddonPreferences)
    bpy.utils.register_class(LoadLFRDataOperator)
    bpy.utils.register_class(LFRPanel)
    bpy.utils.register_class(SubPanelA)


def unregister():
    bpy.utils.unregister_class(FolderPathAddonPreferences)
    bpy.utils.unregister_class(LoadLFRDataOperator)
    bpy.utils.unregister_class(LFRPanel)
    bpy.utils.unregister_class(SubPanelA)

    
if __name__ == "__main__":
    register()
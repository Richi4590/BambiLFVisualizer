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
        dem.import_dem(context.scene.lfr_properties.dem_path, rotation=(0, 0, 0)) #euler rotation

        lfr_properties = context.scene.lfr_properties
        cameras_collection = lfr_properties.cameras
        cameras_collection.clear()

        # Add a new camera data item to the collection
        camerasData = parse_poses(context.scene.lfr_properties.cameras_path)

        #print(camerasData[0]["fovy"])

        if (camerasData is not None):
            for camData in camerasData:
                # Assuming camData["quaternion"] is a Quaternion
                camQuaternion = [camData["quaternion"].x, camData["quaternion"].y, camData["quaternion"].z, camData["quaternion"].w]
                # Assuming camData["timestamp"] is a datetime object
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

            print(lfr_properties.cameras)
            createCurveDataOutOfCameras(cameras_collection)
            print(cameras_collection[0].quaternion[0], cameras_collection[0].quaternion[1], cameras_collection[0].quaternion[2])

            # for camera_data in cameras_collection:
            #     bpy.ops.object.camera_add(location=camera_data.position)
            #     new_camera = bpy.context.active_object
            #     new_camera.data.lens = camera_data.fovy
            #     new_camera.data.clip_start = camera_data.near
            #     new_camera.data.clip_end = camera_data.far
            #     new_camera.data.sensor_fit = 'HORIZONTAL'  # or 'VERTICAL', depending on your needs
            #     new_camera.data.lens_unit = 'FOV'

            #     # Convert FloatVectorProperty to Quaternion
            #     quaternion_data = Quaternion(camera_data.quaternion)

            #     # Convert quaternion to Euler
            #     euler_rotation = quaternion_data.to_euler('XYZ')
            #     new_camera.rotation_euler = euler_rotation

            #     # Set any other properties you need
            #     new_camera.name = camera_data.image_file


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
        layout.prop(addon_props, "folder_path", text="Set Data Path")
        layout.prop(addon_props, "dem_path", text="Set DEM Path") # Debug
        layout.prop(addon_props, "cameras_path", text="Set Cameras Path") # Debug
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
    bpy.utils.register_class(CameraDataPropertyGroup)
    bpy.utils.register_class(CurveDataPropertyGroup)
    bpy.utils.register_class(LFRProperties)
    bpy.types.Scene.lfr_properties = bpy.props.PointerProperty(type=LFRProperties)
    bpy.utils.register_class(LoadLFRDataOperator)
    bpy.utils.register_class(LFRPanel)
    bpy.utils.register_class(SubPanelA)


def unregister():
    bpy.utils.unregister_class(CameraDataPropertyGroup)
    bpy.utils.unregister_class(CurveDataPropertyGroup)
    bpy.utils.unregister_class(LFRProperties)
    del bpy.types.Scene.lfr_properties
    bpy.utils.unregister_class(LoadLFRDataOperator)
    bpy.utils.unregister_class(LFRPanel)
    bpy.utils.unregister_class(SubPanelA)

    
if __name__ == "__main__":
    register()
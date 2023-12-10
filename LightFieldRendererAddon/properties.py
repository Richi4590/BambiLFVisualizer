import bpy
from mathutils import *
from .lightfields import createImgWithShaderAndModifierPos
from . util import *
from . lightfields import *

D = bpy.data
C = bpy.context

class PlanePropertyGroup(bpy.types.PropertyGroup):
    plane: bpy.props.PointerProperty(type=bpy.types.Object)

class CameraDataPropertyGroup(bpy.types.PropertyGroup):
    fovy: bpy.props.FloatProperty(name="Field of View")
    aspect: bpy.props.FloatProperty(name="Aspect Ratio")
    near: bpy.props.FloatProperty(name="Near")
    far: bpy.props.FloatProperty(name="Far")

    location: bpy.props.FloatVectorProperty(
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

def checkIfPinhole(self, context):
    lfr_prp = context.scene.lfr_properties
    isPinholeView = lfr_prp.pinhole_view

    if isPinholeView:
        delete_objects_in_range_collection(context.scene.lfr_properties.range_planes_collection)
        for item in lfr_prp.range_planes_collection:
            lfr_prp.range_planes_collection.remove(0)

    else:
        cameras_path = lfr_prp.cameras_path
        dem_mesh_obj = lfr_prp.dem_mesh_obj
        camExampleData = lfr_prp.cameras[0]

        for i in range(1, 100):
            new_plane = lfr_prp.range_planes_collection.add()
            new_plane.plane = createImgWithShaderAndModifier(lfr_prp.cam_obj, cameras_path, camExampleData.image_file, dem_mesh_obj.name)
            new_plane.plane.name = "range_plane_" + str(i)

    bpy.data.objects[lfr_prp.cam_obj.name].select_set(True) # have camera selected after loading

def onPinholeValueChange(self, context):

    checkIfPinhole(self, context)
    bpy.context.scene.frame_set(context.scene.frame_current)

class LFRProperties(bpy.types.PropertyGroup):
    cameras: bpy.props.CollectionProperty(type=CameraDataPropertyGroup)
    dem_mesh_obj: bpy.props.PointerProperty(type=bpy.types.Object)
    cam_obj: bpy.props.PointerProperty(type=bpy.types.Object)
    pinhole_frame_obj: bpy.props.PointerProperty(type=bpy.types.Object) # when only watchin 1 frame at a time, its only 1x plane, 
                                                                    # no need to destroy and create another one each new keyframe
    pinhole_view: bpy.props.BoolProperty(
        default=True,
        update=onPinholeValueChange) #triggered when toggling pinhole
    
    # amount of frames to be used to "interpolate"
    every_nth_frame: bpy.props.IntProperty(
        default=1,
        min=1,
        max=100
    )

    # amount of frames to be used to "interpolate"
    range_to_interpolate: bpy.props.IntProperty(
        default=1,
        min=1,
        max=100
    )

    #focus value for the interpolation
    focus: bpy.props.IntProperty(
        default=0,
        min=-50,
        max=50
    )  

    range_planes_collection: bpy.props.CollectionProperty(type=PlanePropertyGroup)

    folder_path: bpy.props.StringProperty(
        name="Folder Path",
        subtype='DIR_PATH',
        default="",
    )

    #debug default should be empty for all
    dem_path: bpy.props.StringProperty(
        name="DEM Path",
        subtype='FILE_PATH',
        default="E:/u_Semester_Project/Data/dem/dem_mesh_r2.glb", 
    )

    cameras_path: bpy.props.StringProperty(
        name="CAMERAS Path",
        subtype='FILE_PATH',
        default="E:/u_Semester_Project/Parkplatz_1ms/Frames_T/", 
    )
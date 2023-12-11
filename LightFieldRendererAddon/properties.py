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

def onPinholeValueChange(self, context):
    lfr_prp = context.scene.lfr_properties
    bpy.context.scene.frame_set(context.scene.frame_current)
    bpy.data.objects[lfr_prp.cam_obj.name].select_set(True) # have camera selected after loading

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

    folder_path: bpy.props.StringProperty(
        name="Folder Path",
        subtype='DIR_PATH',
        default="",
    )

    #debug default should be empty for all
    dem_path: bpy.props.StringProperty(
        name="DEM Path",
        subtype='FILE_PATH',
        default="E:/u_Semester_Project/Data/Parkplatz_1ms/Data/dem/", 
    )

    cameras_path: bpy.props.StringProperty(
        name="CAMERAS Path",
        subtype='FILE_PATH',
        default="E:/u_Semester_Project/Data/Parkplatz_1ms/Frames_T/", 
    )
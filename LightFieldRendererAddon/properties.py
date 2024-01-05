import math
import bpy
from mathutils import *

from . cameras import createMainCamera
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
    isPinholeView = lfr_prp.pinhole_view

    current_frame_number = context.scene.frame_current-1
    full_img_path = lfr_prp.cameras_path + lfr_prp.cameras[current_frame_number].image_file
    mask_img_path = "E:/u_Semester_Project/Data/Parkplatz_1ms/Frames_T/mask_T.png"

    if isPinholeView: # works well
        # delete all projection cameras from its collection if it exists and delete collection too
        lfr_prp.pinhole_frame_obj = createImgWithShaderAndModifier(lfr_prp.cam_obj, lfr_prp.cameras_path, lfr_prp.cameras[0].image_file, lfr_prp.dem_mesh_obj.name) #create a plane once
        create_overlay_material(lfr_prp.pinhole_frame_obj, full_img_path, mask_img_path)

        if (lfr_prp.projection_mesh_obj):
            lfr_prp.projection_mesh_obj.hide_viewport = True  
    else:
        if (lfr_prp.pinhole_frame_obj is not None):
            bpy.data.objects.remove(lfr_prp.pinhole_frame_obj, do_unlink=True) 

        if (lfr_prp.projection_mesh_obj is None):
            create_singular_giant_projection_plane(lfr_prp.dem_mesh_obj)


        img_tex = get_image_epending_on_frame(lfr_prp, current_frame_number)
        update_projection_material_tex(lfr_prp.projection_mesh_obj.data.materials[0], img_tex)
        lfr_prp.projection_mesh_obj.hide_viewport = False
        # create all projection cameras (inside its own collection)

    bpy.context.scene.frame_set(context.scene.frame_current)
    bpy.data.objects[lfr_prp.cam_obj.name].select_set(True) # have camera selected after loading

def initStartupObjects(self, context):
    lfr_prp = context.scene.lfr_properties
    isPinholeView = lfr_prp.pinhole_view

    if isPinholeView: # works well
        createMainCamera(lfr_prp) # only gets created once
    else:
        lfr_prp.projection_mesh_obj = create_singular_giant_projection_plane(lfr_prp.dem_mesh_obj)
        createMainCamera(lfr_prp) # only gets created once

    bpy.context.scene.frame_set(context.scene.frame_current)
    bpy.data.objects[lfr_prp.cam_obj.name].select_set(True) # have camera selected after loading

def onAnyValueChange(self, context):
    lfr_prp = context.scene.lfr_properties
    bpy.context.scene.frame_set(context.scene.frame_current)
    bpy.data.objects[lfr_prp.cam_obj.name].select_set(True) # have camera selected after loading

def post_frame_change_handler(scene): #executes after a new keyframe loaded
    current_frame_number = scene.frame_current
    lfr_prp = scene.lfr_properties

    if current_frame_number >= 1 and current_frame_number < len(lfr_prp.cameras):
        if lfr_prp.pinhole_view:
            lfr_prp.pinhole_frame_obj.location = lfr_prp.cam_obj.location
            full_img_path = lfr_prp.cameras_path + lfr_prp.cameras[current_frame_number].image_file 
            update_overlay_material_path(lfr_prp.pinhole_frame_obj, full_img_path)  
            #createNewUV(lfr_prp.dem_mesh_obj) 
        else:
            if (lfr_prp.projection_mesh_obj):
                img_tex = applyImagesAndPositionsToPlanesFromRange(lfr_prp, current_frame_number)
                #img_tex = get_image_epending_on_frame(lfr_prp, current_frame_number)
                update_projection_material_tex(lfr_prp.projection_mesh_obj.data.materials[0], img_tex)
            else:
                create_singular_giant_projection_plane(lfr_prp.dem_mesh_obj)
            

class LFRProperties(bpy.types.PropertyGroup):
    cameras: bpy.props.CollectionProperty(type=CameraDataPropertyGroup)
    dem_mesh_obj: bpy.props.PointerProperty(type=bpy.types.Object)
    cam_obj: bpy.props.PointerProperty(type=bpy.types.Object)
    pinhole_frame_obj: bpy.props.PointerProperty(type=bpy.types.Object) 
    projection_mesh_obj: bpy.props.PointerProperty(type=bpy.types.Object) 

    pinhole_view: bpy.props.BoolProperty(
        default=True,
        update=onPinholeValueChange) #triggered when toggling pinhole
    
    img_mask: bpy.props.StringProperty(
        name="Masking Image"
    )

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
    focus: bpy.props.FloatProperty(
        default=0.0,
        min=-100.0,
        max=100.0,
        update=onAnyValueChange #triggered when changing focus
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
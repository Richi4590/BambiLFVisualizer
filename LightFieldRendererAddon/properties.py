import math
import bpy
from mathutils import *

from . cameras import create_main_camera, set_current_camera_rendering_resolution
from . util import *
from . lightfields import *

D = bpy.data
C = bpy.context

class ImagePropertyGroup(bpy.types.PropertyGroup):
    image: bpy.props.PointerProperty(type=bpy.types.Object)

class RangeMeshPropertyGroup(bpy.types.PropertyGroup):
    mesh: bpy.props.PointerProperty(type=bpy.types.Object)
    proj_cam: bpy.props.PointerProperty(type=bpy.types.Object)
    view_dir_obj: bpy.props.PointerProperty(type=bpy.types.Object)
    view_origin_obj: bpy.props.PointerProperty(type=bpy.types.Object)
    original_location: bpy.props.FloatVectorProperty(
        name="Original Location",
        default=(0.0, 0.0, 0.0),
        subtype='TRANSLATION',
        size=3,  # Size of the vector (3 for XYZ)
    )

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

def on_view_range_of_images_value_change(self, context):
    lfr_prp = context.scene.lfr_properties
    view_range_of_images = lfr_prp.view_range_of_images
    current_frame_number = context.scene.frame_current

    if view_range_of_images: 
        apply_images_and_positions_to_planes_from_range(lfr_prp, current_frame_number)
    else:
        delete_temp_objects_of_range_rendering(lfr_prp)
        delete_rendered_images_data(lfr_prp)
        bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True) #slight memory clean up

def init_startup_objs(self, context):
    lfr_prp = context.scene.lfr_properties

    lfr_prp.projection_mesh_obj = create_giant_projection_plane(lfr_prp.dem_mesh_obj)
    create_main_camera(lfr_prp) # only gets created once

    set_current_camera_rendering_resolution(lfr_prp)

    if (lfr_prp.projection_mesh_obj is None):
        lfr_prp.projection_mesh_obj = create_giant_projection_plane(lfr_prp.dem_mesh_obj)

    bpy.context.scene.frame_set(context.scene.frame_current)
    bpy.data.objects[lfr_prp.cam_obj.name].select_set(True) # have camera selected after loading

def on_focus_value_change(self, context):
    current_frame_number = context.scene.frame_current
    lfr_prp = context.scene.lfr_properties
    offset_proj_cameras_with_focus(lfr_prp, current_frame_number)

def offset_proj_cameras_with_focus(lfr_prp, current_frame_number):
    projection_objects = lfr_prp.range_objects

    #main camera
    orig_main_cam_location = lfr_prp.cameras[current_frame_number].location
    new_location = (orig_main_cam_location[0], orig_main_cam_location[1] + lfr_prp.focus, orig_main_cam_location[2])
    lfr_prp.cam_obj.location = new_location

    for entry in projection_objects:
        new_location = (entry.original_location.x, entry.original_location.y + lfr_prp.focus, entry.original_location.z)
        entry.proj_cam.location = new_location

def post_frame_change_handler(scene): #executes after a new keyframe loaded
    current_frame_number = scene.frame_current
    lfr_prp = scene.lfr_properties

    if current_frame_number >= 1 and current_frame_number < len(lfr_prp.cameras):
        
        if (lfr_prp.cam_obj):
            bpy.ops.object.transform_apply(location=True)

        if lfr_prp.projection_mesh_obj:
            #img_tex = applyImagesAndPositionsToPlanesFromRange(lfr_prp, current_frame_number)
            img_tex = get_image_depending_on_frame(lfr_prp, current_frame_number)
            update_projection_material_tex(lfr_prp.projection_mesh_obj.data.materials[0], img_tex)
        else:
            lfr_prp.projection_mesh_obj = create_giant_projection_plane(lfr_prp.dem_mesh_obj)

class LFRProperties(bpy.types.PropertyGroup):
    cameras: bpy.props.CollectionProperty(type=CameraDataPropertyGroup)
    dem_mesh_obj: bpy.props.PointerProperty(type=bpy.types.Object)
    cam_obj: bpy.props.PointerProperty(type=bpy.types.Object)
    pinhole_frame_obj: bpy.props.PointerProperty(type=bpy.types.Object) 
    projection_mesh_obj: bpy.props.PointerProperty(type=bpy.types.Object) 
    range_objects: bpy.props.CollectionProperty(type=RangeMeshPropertyGroup)
    range_render_cam: bpy.props.PointerProperty(type=bpy.types.Object)
    rendered_images: bpy.props.CollectionProperty(type=ImagePropertyGroup)
    
    view_range_of_images: bpy.props.BoolProperty(
        default=True,
        update=on_view_range_of_images_value_change
    ) 

    img_mask: bpy.props.StringProperty(
        name="Masking Image"
    )

    # amount of frames to be used to "interpolate"
    every_nth_frame: bpy.props.IntProperty(
        default=5,
        min=1,
        max=100
    )

    # amount of frames to be used to "interpolate"
    range_to_interpolate: bpy.props.IntProperty(
        default=1,
        min=1,
        max=200
    )

    #focus value for the interpolation
    focus: bpy.props.FloatProperty(
        default=0.0,
        update=on_focus_value_change #triggered when changing focus
    )  

    folder_path: bpy.props.StringProperty(
        name="Fold path",
        subtype="DIR_PATH"
    )

    #the following paths will be applied automatically 
    #or overwritten by the manually specified paths 
    dem_path: bpy.props.StringProperty(
        name="DEM Path",
        subtype="FILE_PATH"
    )

    cameras_path: bpy.props.StringProperty(
        name="CAMERAS Path",
        subtype="FILE_PATH"
    )

    render_path: bpy.props.StringProperty(
        name="Default Render Path",
        subtype="DIR_PATH"
    )

    json_path: bpy.props.StringProperty(
        name="Default JSON Path",
        subtype="FILE_PATH"
    )

    #properties in the addon options panel
    man_rend_cam: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Manual Rendering Camera",
        description="Select the camera you want to use for the rendering"
    )

    save_rend_images: bpy.props.BoolProperty(
        default=False
    ) 

    rend_res_x: bpy.props.IntProperty(
        name="Pixel Width",
        description="Enter the pixel width",
        default=1024,
        min=1
    )

    rend_res_y: bpy.props.IntProperty(
        name="Pixel Height",
        description="Enter the pixel height",
        default=1024,
        min=1
    )

    man_render_path: bpy.props.StringProperty(
        name="Default Render Path",
        subtype="DIR_PATH"
    )

    man_dem_path: bpy.props.StringProperty(
        name="Default Render Path",
        subtype="FILE_PATH"
    )

    man_json_path: bpy.props.StringProperty(
        name="Default Render Path",
        subtype="FILE_PATH"
    )
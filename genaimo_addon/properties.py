import bpy
import os

from bpy.props import (
    BoolProperty,
    EnumProperty,
    FloatProperty,
    PointerProperty,
    StringProperty,
    IntProperty,
    CollectionProperty,
)
from bpy.types import (
    PropertyGroup,
)

# 이미지 경로 설정
GENAIMO_IMAGES_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data", "images")

# def load_motion_images():
#     """Motion Library 이미지들을 동적으로 로드"""
#     motion_images = {}
#     motion_ids = ["124", "125", "126", "127", "128", "134", "135", "136"]
    
#     print(f"Loading images from: {GENAIMO_IMAGES_DIR}")
    
#     for motion_id in motion_ids:
#         image_path = os.path.join(GENAIMO_IMAGES_DIR, f"YJ_{motion_id}_001.gif")
#         if os.path.exists(image_path):
#             motion_images[motion_id] = image_path
#             print(f"Found image: {image_path}")
#         else:
#             print(f"Warning: Image not found: {image_path}")
    
#     print(f"Loaded {len(motion_images)} motion images")
#     return motion_images

# 전역 변수로 이미지 정보 저장
#MOTION_LIBRARY_IMAGES = load_motion_images()

# def define_props():
#     bpy.types.Scene.text_input = bpy.props.StringProperty(name="Text", default="a person walks forward.")
#     bpy.types.Scene.frames_input = bpy.props.IntProperty(name="numbers of frames", default=8, min=8, max=200)
#     bpy.types.Scene.start_frame_input = bpy.props.IntProperty(name="start frame", default=1, min=1)
#     bpy.types.Scene.use_length_estimator = bpy.props.BoolProperty(name="use length estimator", default=True)
#     bpy.types.Scene.api_key = bpy.props.StringProperty(
#         name="API Key",
#         description="API key used for making request to Genaimo API server.",
#         subtype='PASSWORD',
#     )
# def clear_props():
#     if hasattr(bpy.types.Scene, "text_input"):
#         del bpy.types.Scene.text_input
#     if hasattr(bpy.types.Scene, "frames_input"):
#         del bpy.types.Scene.frames_input
#     if hasattr(bpy.types.Scene, "start_frame_input"):
#         del bpy.types.Scene.start_frame_input
#     if hasattr(bpy.types.Scene, "use_length_estimator"):
#         del bpy.types.Scene.use_length_estimator
#     if hasattr(bpy.types.Scene, "api_key"):
#         del bpy.types.Scene.api_key
  



class PG_GenaimoProperties(PropertyGroup):
    
    
    # Main Properties
    api_key: StringProperty(name="API Key", subtype='PASSWORD')
    api_secret: StringProperty(name="API Secret", subtype='PASSWORD')
    
    
    # Text to Motion Properties
    text_input: StringProperty(name="Text", default="a person walks forward.")
    frames_input: IntProperty(name="numbers of frames", default=8, min=8, max=200)
    start_frame_input: IntProperty(name="start frame", default=1, min=1)
    use_length_estimator: BoolProperty(name="Auto", default=True)
    
    # Motion List pagination
    motion_list_page: IntProperty(name="Motion List Page", default=0, min=0)
    motion_list_items_per_page: IntProperty(name="Items Per Page", default=3, min=1, max=3)
    
    # API Key edit mode
    show_api_edit: BoolProperty(name="Show API Edit", default=False)
    
    # Stylize properties # 식별자, 표시이름, 설명
    stylize_opt: EnumProperty(
        name="Style",
        items=[
            ("GLIDER", "Glider", ""),
            ("BEND_BOTH_ARMS", "Bend Both Arms", ""),
            ("LEAN_FORWARD", "Lean Forward", ""),
            ("MOVE_CAREFULLY", "Move Carefully", ""),
            ("DINO","Dino", ""),
            ("TILT_HEAD_UP", "Tilt Head Up", ""),
            ("ELDERLY", "Elderly", ""),
            ("ON_A_CALL", "On a Call", ""),
            ("KAWAI", "Kawai", ""),
            ("LIFTED_LEFT_ARM", "Lifted Left Arm", ""),
            ("LIFTED_RIGHT_ARM", "Lifted Right Arm", ""),
            ("ANGRY","Angry", ""),
            ("DEPRESSED","Depressed", ""),
            ("ELEGANT","Elegant", ""),
            ("ROBOT_LIKE","Robot Like", ""),
            ("SHY","Shy", ""),
        ],
        default="GLIDER",
    )
    use_all_frames: BoolProperty(name="Use all frames", default=True)
    stylized_start_frame_input: IntProperty(name="start frame", default=1, min=1)
    stylized_end_frame_input: IntProperty(name="end frame", default=1, min=1)
    
    # Motion Library Properties
    show_motion_library: BoolProperty(name="Show Motion Library", default=True)
    motion_search: StringProperty(name="Search Motions", default="")
  
  
def define_props():
    # Register property classes
    for cls in PROPERTY_CLASSES:
        try:
            bpy.utils.register_class(cls)
        except ValueError:
            # Class already registered, skip
            pass
    
    # Register PointerProperty
    try:
        bpy.types.Scene.genaimo_scene_properties = PointerProperty(
            type=PG_GenaimoProperties)
    except ValueError:
        # Already registered, skip
        pass

def clear_props():
    # Remove PointerProperty first
    if hasattr(bpy.types.Scene, "genaimo_scene_properties"):
        del bpy.types.Scene.genaimo_scene_properties
    
    # Unregister property classes
    for cls in reversed(PROPERTY_CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except (ValueError, RuntimeError):
            # Class not registered or already unregistered, skip
            pass  

class GenaimoPreferences(bpy.types.AddonPreferences):
    # this must match the add-on name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = "genaimo_addon"

    api_key: StringProperty(
        name="API Key",
        description="API key used for making request to Genaimo API server.",
        subtype='PASSWORD',
    )
    api_secret: StringProperty(
        name="API Secret",
        description="API secret used for making request to Genaimo API server.",
        subtype='PASSWORD',
    )

    def draw(self, context):
        layout = self.layout
        layout.operator("genaimo.open_developer_portal", icon="LINKED")
        layout.prop(self, "api_key")
        layout.prop(self, "api_secret")

PROPERTY_CLASSES = [PG_GenaimoProperties, GenaimoPreferences]
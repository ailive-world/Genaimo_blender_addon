import os
import platform
import numpy as np
from enum import Enum
import bpy



MeshyAI_BoneName = [
       "Hips", "LeftUpLeg", "RightUpLeg",
       "Spine02", "LeftLeg", "RightLeg",
       "Spine01", "LeftFoot", "RightFoot",
       "Spine", "LeftToeBase", "RightToeBase",
       "neck", "LeftShoulder", "RightShoulder",
       "Head", "LeftArm", "RightArm",
       "LeftForeArm", "RightForeArm", "LeftHand",
       "RightHand",
    ]

GMO_BoneName = ["pelvis", "thigh_l", "thigh_r", "spine_01", "calf_l", "calf_r", "spine_02", "foot_l", "foot_r", "spine_03", "ball_l", "ball_r", "neck_01", "clavicle_l", "clavicle_r", "head", "upperarm_l", "upperarm_r", "lowerarm_l", "lowerarm_r", "hand_l", "hand_r"];

GMO_GLB_FILE =  os.path.join(os.path.dirname(os.path.realpath(__file__)),"data", "model", "dummy-g-mo.glb")

GENAIMO_ICON_DIR =  os.path.join(os.path.dirname(os.path.realpath(__file__)),"data", "icon")
GENAIMO_IMAGES_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data", "images_png")

# Custom icon loading disabled for cross-platform compatibility
# ICONS_DICT = bpy.utils.previews.new()
# ICONS_DICT.load("custom_icon", os.path.join(GENAIMO_ICON_DIR, "genaimo_icon.png"), 'IMAGE')
ICONS_DICT = {}  # Empty dict for compatibility

# Motion Library 이미지들을 프리뷰로 로드 (개발 기간상 임시 비활성화)
# MOTION_LIBRARY_IMAGES = {}
# motion_ids = ["124", "125", "126", "127", "128", "134", "135", "136"]

# print(f"Loading motion library images from: {GENAIMO_IMAGES_DIR}")

# for motion_id in motion_ids:
#     image_path = os.path.join(GENAIMO_IMAGES_DIR, f"YJ_{motion_id}_001.png")
#     if os.path.exists(image_path):
#         try:
#             # 프리뷰로 로드
#             icon_name = f"motion_{motion_id}"
#             ICONS_DICT.load(icon_name, image_path, 'IMAGE')
#             MOTION_LIBRARY_IMAGES[motion_id] = icon_name
#             print(f"Loaded PNG preview for motion {motion_id}: {icon_name}")
#             print(f"  Icon ID: {ICONS_DICT[icon_name].icon_id if icon_name in ICONS_DICT else 'NOT FOUND'}")
#         except Exception as e:
#             print(f"Error loading preview for motion {motion_id}: {e}")
#     else:
#         print(f"PNG image not found: {image_path}")

# print(f"Total motion previews loaded: {len(MOTION_LIBRARY_IMAGES)}")
# print(f"MOTION_LIBRARY_IMAGES: {MOTION_LIBRARY_IMAGES}")
# print(f"ICONS_DICT keys: {list(ICONS_DICT.keys())}")

# Motion Library 비활성화 시 빈 딕셔너리로 초기화
MOTION_LIBRARY_IMAGES = {}

class EXPORT_TYPE(Enum):
    FBX = "fbx"
    OBJ = "obj"


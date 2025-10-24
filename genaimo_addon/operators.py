import bpy
from . import ADDON_KEY
import json
import requests
import webbrowser

from .blender import (
    json_retarget, 
    motion_to_json
)
from .globals import (
    GMO_GLB_FILE
)


class OP_LOAD_AVATAR(bpy.types.Operator):  
    bl_idname = "genaimo.load_avatar"
    bl_label = "Load Avatar"
    
    def execute(self, context):
        bpy.ops.import_scene.gltf(
            filepath=GMO_GLB_FILE, 
            bone_shape_scale_factor=0.01
        )
        return {'FINISHED'}

    

class OP_GENAIMO_GENERATE(bpy.types.Operator):  # No change needed here
    bl_idname = "genaimo.generate"
    bl_label = "Generate"

    def execute(self, context):
        
        local_mode = False
        
        d_text = context.scene.genaimo_scene_properties.text_input
        
        d_use_length_estimator = context.scene.genaimo_scene_properties.use_length_estimator
        
        if d_use_length_estimator:
            d_sec = str(0)
        else: # currently use only length estimator
            frames_input = context.scene.genaimo_scene_properties.frames_input
            current_fps = context.scene.render.fps
            model_fps = 20 
            d_sec = str(int(frames_input / current_fps * model_fps))
            
        if not d_text:
            d_text = "a person walks forward."
            
        
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
            
            
        if local_mode:
            try : 
                
                data = {
                    "text": d_text,
                    "sec": d_sec,

                    }
                response = requests.post(
                    "http://localhost:8080/gent2m/",
                    data=json.dumps(data),
                    headers={'Content-type': 'application/json'})
                json_data = response.json()
                
                num_samples = len(json_data)
                
                # 현재 batch를 구분하기 위한 timestamp 생성
                from datetime import datetime
                batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                
                for i in range(num_samples):
                    action = json_retarget(json_data[i], start_frame=context.scene.genaimo_scene_properties.start_frame_input)  # currently use one
                    
                    if action:
                        action["genaimo_batch_id"] = batch_id
                        action["genaimo_batch_index"] = i
                        action["genaimo_prompt"] = d_text  # 입력받은 텍스트 저장           
            
            except ValueError:
                self.report({'ERROR'}, f"JSON Errors")

                    
            
        else:    
            try :
                
                data = {
                    "prompt": d_text,
                }
                
                # Get API key from Preferences (permanent storage)
                preferences = context.preferences
                addon = preferences.addons.get(ADDON_KEY)
                addon_prefs = getattr(addon, "preferences", None)
                api_key = (addon_prefs.api_key or "").strip() if addon_prefs else ""
                api_secret = (addon_prefs.api_secret or "").strip() if addon_prefs else ""
                
                # Validate API credentials
                if not api_key or not api_secret:
                    self.report({'ERROR'}, "API key or secret is empty. Please configure in addon preferences.")
                    return {'CANCELLED'}
                
                headers = {
                    'g-api-key': api_key,
                    'g-api-secret': api_secret,
                    'Content-Type': 'application/json'
                }
                
                response = requests.post(
                    "https://genaimo.ailive.world/gateway/b2c/model/motion",
                    data=json.dumps(data),  
                    headers=headers)
                
                json_dict = response.json()
                success = json_dict["success"]
                if not success:
                    match json_dict['error']:
                        case "MOTION_GENERATION_FAILED":
                            self.report({'ERROR'}, "Currently Service is not available. Please contact to Genaimo Discord.")
                        case "CREDIT_INFORMATION_NOT_EXIST":
                            self.report({'ERROR'}, "Credit information not exist")
                        case "INSUFFICIENT_CREDIT":
                            self.report({'ERROR'}, "Insufficient credit. Please check your credit information.")
                        case "INVALID_API_KEY":
                            self.report({'ERROR'}, "API key is incorrect")
                        case "INVALID_API_SECRET":
                            self.report({'ERROR'}, "API secret is incorrect")
                        case _:
                            self.report({'ERROR'}, f"JSON Errors: {json_dict['error']}")
                    
                    return {'CANCELLED'}
                
                json_data = json_dict['data']['motion_dicts']
                
                num_samples = int(json_dict['data']['num_motions'])
                
                # 현재 batch를 구분하기 위한 timestamp 생성
                from datetime import datetime
                batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                for i in range(num_samples):
                    action = json_retarget(json_data[i], start_frame=context.scene.genaimo_scene_properties.start_frame_input)  # currently use one
                    
                    # action에 batch_id, batch_index, prompt를 custom property로 저장
                    if action:
                        action["genaimo_batch_id"] = batch_id
                        action["genaimo_batch_index"] = i
                        action["genaimo_prompt"] = d_text  # 입력받은 텍스트 저장           

            except requests.exceptions.RequestException as e:
                self.report({'ERROR'}, f"Network error: {str(e)}")
                return {'CANCELLED'}
            
            except ValueError as e:
                self.report({'ERROR'}, f"Invalid JSON response: {str(e)}")
                return {'CANCELLED'}
            
            except KeyError as e:
                self.report({'ERROR'}, f"Missing data in server response: {str(e)}")
                return {'CANCELLED'}
            
            except Exception as e:
                self.report({'ERROR'}, f"Unexpected error: {str(e)}")
                return {'CANCELLED'}
        
        return {'FINISHED'}
    

class OP_GENAIMO_GENERATE_STYLIZED(bpy.types.Operator):  # No change needed here
    bl_idname = "genaimo.generate_stylized"
    bl_label = "Generate"

    def execute(self, context):
        
        # TO DO : Motion -> JSON 변환 
        
        # Step 1 ) get index from stylized_opt  
        d_stylized_opt = context.scene.genaimo_scene_properties.stylize_opt
        
        # 현재 선택된 액션 가져오기
        armature = None
        for obj in context.scene.objects:
            if obj.type == 'ARMATURE':
                armature = obj
                break
        
        current_action = armature.animation_data.action if armature and armature.animation_data else None
        
        # 현재 액션의 프롬프트 가져오기
        original_prompt = ""
        if current_action and "genaimo_prompt" in current_action:
            original_prompt = current_action["genaimo_prompt"]
        
        # 스타일 이름 가져오기 (EnumProperty에서)
        props = context.scene.genaimo_scene_properties
        style_name = props.bl_rna.properties['stylize_opt'].enum_items[d_stylized_opt].name
        
        motion_json_data = motion_to_json()
        
        
        match style_name:
            case "Glider":
                style_id = 0
            case "Bend Both Arms":
                style_id = 6
            case "Lean Forward":
                style_id = 9
            case "Move Carefully":
                style_id = 14
            case "Dino":
                style_id = 20
            case "Tilt Head Up":
                style_id = 46
            case "Elderly":
                style_id = 52
            case "On a Call":
                style_id = 55
            case "Kawai":
                style_id = 59
            case "Lifted Left Arm":
                style_id = 64
            case "Lifted Right Arm":
                style_id = 65
            case "Angry":
                style_id = 100
            case "Depressed":
                style_id = 103
            case "Elegant":
                style_id = 104
            case "Robot Like":
                style_id = 111
            case "Shy":
                style_id = 113
            case _:
                raise ValueError(f"Invalid style : {style_name}")
        
        

        # Step 2 ) get json from stylized_opt_index
        
    
        data = {"style_id": style_id, "motion": motion_json_data}       
        
        
        try :
            # Get API key from Preferences (permanent storage)
            preferences = context.preferences
            addon = preferences.addons.get(ADDON_KEY)
            addon_prefs = getattr(addon, "preferences", None)
            api_key = (addon_prefs.api_key or "").strip() if addon_prefs else ""
            api_secret = (addon_prefs.api_secret or "").strip() if addon_prefs else ""
            
            # Validate API credentials
            if not api_key or not api_secret:
                self.report({'ERROR'}, "API key or secret is empty. Please configure in addon preferences.")
                return {'CANCELLED'}
            
            headers = {
                'g-api-key': api_key,
                'g-api-secret': api_secret,
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                "https://genaimo.ailive.world/gateway/b2c/model/stylize",
                data=json.dumps(data),  
                headers=headers)
            
            json_dict = response.json()
            success = json_dict["success"]
            if not success:
                match json_dict['error']:
                    case "MOTION_GENERATION_FAILED":
                        self.report({'ERROR'}, "Currently Service is not available. Please contact to Genaimo Discord.")
                    case "CREDIT_INFORMATION_NOT_EXIST":
                        self.report({'ERROR'}, "Credit information not exist")
                    case "INSUFFICIENT_CREDIT":
                        self.report({'ERROR'}, "Insufficient credit. Please check your credit information.")
                    case _:
                        self.report({'ERROR'}, f"JSON Errors: {json_dict['error']}")
                return {'CANCELLED'}
            
            json_data = json_dict['data']['stylized_motion']
            
            # Stylize는 단일 모션이므로 batch_id만 추가
            from datetime import datetime
            batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            action = json_retarget(json_data, start_frame=context.scene.genaimo_scene_properties.start_frame_input)  # currently use one
            
            # action에 batch_id와 프롬프트를 custom property로 저장
            if action:
                action["genaimo_batch_id"] = batch_id
                action["genaimo_batch_index"] = 0
                
                # 원본 프롬프트 + 스타일 이름으로 새 프롬프트 생성
                if original_prompt:
                    combined_prompt = f"{original_prompt} ({style_name})"
                else:
                    combined_prompt = f"Stylized ({style_name})"
                action["genaimo_prompt"] = combined_prompt

        except requests.exceptions.RequestException as e:
            self.report({'ERROR'}, f"Network error: {str(e)}")
            return {'CANCELLED'}
        
        except ValueError as e:
            self.report({'ERROR'}, f"Invalid JSON response: {str(e)}")
            return {'CANCELLED'}
        
        except KeyError as e:
            self.report({'ERROR'}, f"Missing data in server response: {str(e)}")
            return {'CANCELLED'}
        
        except Exception as e:
            self.report({'ERROR'}, f"Unexpected error: {str(e)}")
            return {'CANCELLED'}

     
        return {'FINISHED'}
    
class OP_GenaimoOpenDeveloperPortal(bpy.types.Operator):
    """Open Genaimo Developer Portal in browser"""
    bl_idname = "genaimo.open_developer_portal"
    bl_label = "Open Developer Portal"

    def execute(self, context):
       
        
        webbrowser.open('https://docs.ailive.world/docs/genaimo_api')
        return {'FINISHED'}


class OP_GenaimoOpenLicenseLink(bpy.types.Operator):
    """Open License Link"""
    bl_idname = "genaimo.open_license"
    bl_label = "License"

    def execute(self, context):
        
        
        webbrowser.open('https://docs.ailive.world/docs/Motion_License')
        return {'FINISHED'}


class OP_GenaimoOpenWebsiteLink(bpy.types.Operator):
    """Open Website Link"""
    bl_idname = "genaimo.open_website"
    bl_label = "Website"

    def execute(self, context):
        webbrowser.open('https://genaimo.ailive.world/')
        return {'FINISHED'}


class OP_GenaimoOpenDocsLink(bpy.types.Operator):
    """Open Documentation Link"""
    bl_idname = "genaimo.open_docs"
    bl_label = "Documentation"

    def execute(self, context):
        webbrowser.open('https://docs.ailive.world/')
        return {'FINISHED'}

class OP_GenaimoOpenDiscordLink(bpy.types.Operator):
    """Open Discord Link"""
    bl_idname = "genaimo.open_discord"
    bl_label = "Discord"
    bl_description = "Join Genaimo Discord community"

    def execute(self, context):
        webbrowser.open('https://discord.com/invite/8Yj4pMYsJN')
        return {'FINISHED'}

class OP_GenaimoSaveApiKey(bpy.types.Operator):
    """Save API Key to Preferences"""
    bl_idname = "genaimo.save_api_key"
    bl_label = "Save API Key"

    def execute(self, context):
        preferences = context.preferences
        addon = preferences.addons.get(ADDON_KEY)
        addon_prefs = getattr(addon, "preferences", None)
        
        if not addon_prefs:
            self.report({'ERROR'}, "Failed to access addon preferences")
            return {'CANCELLED'}
        
        api_key = addon_prefs.api_key
        api_secret = addon_prefs.api_secret
        
        # Preferences는 이미 수정되었으므로 디스크에만 저장
        try:
            bpy.ops.wm.save_userpref()
            print(f"API Key saved to preferences: key={bool(api_key)}, secret={bool(api_secret)}")
        except Exception as e:
            print(f"Failed to save user preferences: {e}")
            self.report({'ERROR'}, f"Failed to save: {str(e)}")
            return {'CANCELLED'}
        
        # 저장 후 편집 모드 종료
        context.scene.genaimo_scene_properties.show_api_edit = False
        
        self.report({'INFO'}, "API Key saved successfully")
        return {'FINISHED'}

class OP_GenaimoEditApiKey(bpy.types.Operator):
    """Edit API Key"""
    bl_idname = "genaimo.edit_api_key"
    bl_label = "Edit API Key"
    bl_description = "Edit API key and secret"
    
    def execute(self, context):
        scene_props = context.scene.genaimo_scene_properties
        # 편집 모드 토글
        scene_props.show_api_edit = not scene_props.show_api_edit
        return {'FINISHED'}

class OP_GenaimoSelectAction(bpy.types.Operator):
    """Select Animation Action"""
    bl_idname = "genaimo.select_action"
    bl_label = "Select Action"

    action_name: bpy.props.StringProperty(name="Action Name")

    def execute(self, context):
        # Armature 찾기
        armature = None
        for obj in bpy.context.scene.objects:
            if obj.type == 'ARMATURE':
                armature = obj
                break
        
        if armature is None:
            self.report({'ERROR'}, "No armature found")
            return {'CANCELLED'}
        
        # 액션 찾기
        action = bpy.data.actions.get(self.action_name)
        if action is None:
            self.report({'ERROR'}, f"Action '{self.action_name}' not found")
            return {'CANCELLED'}
        
        # 액션 적용
        if not armature.animation_data:
            armature.animation_data_create()
        
        armature.animation_data.action = action
        
        # 프레임 범위 설정
        bpy.context.scene.frame_start = int(action.frame_range[0])
        bpy.context.scene.frame_end = int(action.frame_range[1])
        
        self.report({'INFO'}, f"Selected action: {self.action_name}")
        return {'FINISHED'}

class OP_GenaimoDeleteAction(bpy.types.Operator):
    """Delete Animation Action"""
    bl_idname = "genaimo.delete_action"
    bl_label = "Delete Action"

    action_name: bpy.props.StringProperty(name="Action Name")

    def execute(self, context):
        # 액션 찾기
        action = bpy.data.actions.get(self.action_name)
        if action is None:
            self.report({'ERROR'}, f"Action '{self.action_name}' not found")
            return {'CANCELLED'}
        
        # 현재 적용된 액션인지 확인
        current_action = None
        for obj in bpy.context.scene.objects:
            if obj.type == 'ARMATURE' and obj.animation_data:
                if obj.animation_data.action == action:
                    current_action = obj
                    break
        
        # 현재 적용된 액션이면 제거
        if current_action:
            current_action.animation_data.action = None
        
        # 액션 삭제
        bpy.data.actions.remove(action)
        
        self.report({'INFO'}, f"Deleted action: {self.action_name}")
        return {'FINISHED'}

class OP_GenaimoPlayAction(bpy.types.Operator):
    """Play Animation Action"""
    bl_idname = "genaimo.play_action"
    bl_label = "Play Action"

    action_name: bpy.props.StringProperty(name="Action Name")

    def execute(self, context):
        # Armature 찾기
        armature = None
        for obj in bpy.context.scene.objects:
            if obj.type == 'ARMATURE':
                armature = obj
                break
        
        if armature is None:
            self.report({'ERROR'}, "No armature found")
            return {'CANCELLED'}
        
        # 액션 찾기
        action = bpy.data.actions.get(self.action_name)
        if action is None:
            self.report({'ERROR'}, f"Action '{self.action_name}' not found")
            return {'CANCELLED'}
        
        # 액션 적용
        if not armature.animation_data:
            armature.animation_data_create()
        
        armature.animation_data.action = action
        
        # 프레임 범위 설정 및 재생
        bpy.context.scene.frame_start = int(action.frame_range[0])
        bpy.context.scene.frame_end = int(action.frame_range[1])
        bpy.context.scene.frame_current = int(action.frame_range[0])
        
        # 애니메이션 재생
        bpy.ops.screen.animation_play()
        
        self.report({'INFO'}, f"Playing action: {self.action_name}")
        return {'FINISHED'}

class OP_GenaimoStopAnimation(bpy.types.Operator):
    """Stop Animation"""
    bl_idname = "genaimo.stop_animation"
    bl_label = "Stop Animation"

    def execute(self, context):
        # 애니메이션 정지
        bpy.ops.screen.animation_cancel()
        
        self.report({'INFO'}, "Animation stopped")
        return {'FINISHED'}

class OP_GenaimoDeleteBatch(bpy.types.Operator):
    """Delete Entire Batch"""
    bl_idname = "genaimo.delete_batch"
    bl_label = "Delete Batch"
    bl_description = "Delete all motions in this batch"
    
    batch_id: bpy.props.StringProperty(name="Batch ID", default="")
    
    def execute(self, context):
        # 해당 batch_id를 가진 모든 액션 찾기
        actions_to_delete = []
        
        for action in bpy.data.actions:
            if "genaimo_batch_id" in action and action["genaimo_batch_id"] == self.batch_id:
                actions_to_delete.append(action)
        
        # 액션 삭제
        deleted_count = 0
        for action in actions_to_delete:
            bpy.data.actions.remove(action)
            deleted_count += 1
        
        self.report({'INFO'}, f"Deleted {deleted_count} motions from batch {self.batch_id}")
        return {'FINISHED'}

# Motion Library 관련 Operator들 (개발 기간상 임시 비활성화)
# class OP_GenaimoToggleMotionLibrary(bpy.types.Operator):
#     """Open Motion Library Browser Window"""
#     bl_idname = "genaimo.toggle_motion_library"
#     bl_label = "Explore Motion Library"

#     def execute(self, context):
#         # 팝업 윈도우로 Motion Library 열기
#         return context.window_manager.invoke_props_dialog(self, width=800)
        
#     def draw(self, context):
#         from .globals import MOTION_LIBRARY_IMAGES, ICONS_DICT
        
#         layout = self.layout
        
#         # 헤더
#         header_box = layout.box()
#         header_row = header_box.row(align=True)
#         header_row.label(text="Motion Library Browser", icon="LIBRARY_DATA_DIRECT")
        
#         # 필터 버튼들
#         filter_row = header_box.row(align=True)
#         filter_row.label(text="Filters:")
#         filter_row.operator("genaimo.motion_filter_all", text="All")
#         filter_row.operator("genaimo.motion_filter_walk", text="Walk")
#         filter_row.operator("genaimo.motion_filter_run", text="Run")
#         filter_row.operator("genaimo.motion_filter_dance", text="Dance")
        
#         layout.separator()
        
#         # 메인 그리드 영역
#         grid_box = layout.box()
        
#         # 3개씩 한 줄로 이미지 그리드 표시 (크기 줄임)
#         motion_ids = list(MOTION_LIBRARY_IMAGES.keys())
#         for i in range(0, len(motion_ids), 3):
#             row = grid_box.row(align=True)
#             row.alignment = 'CENTER'
            
#             # 한 줄에 최대 3개 이미지
#             for j in range(3):
#                 if i + j < len(motion_ids):
#                     motion_id = motion_ids[i + j]
                    
#                     # 이미지 박스
#                     motion_box = row.box()
#                     motion_box.scale_y = 1.0  # 스케일 감소
                    
#                     # 이미지 표시
#                     image_col = motion_box.column(align=True)
                    
#                     # 프리뷰 아이콘 이름 가져오기
#                     icon_name = MOTION_LIBRARY_IMAGES.get(motion_id)
                    
#                     if icon_name and icon_name in ICONS_DICT:
#                         # 프리뷰 아이콘으로 이미지 표시
#                         image_row = image_col.row(align=True)
#                         image_row.alignment = 'CENTER'
                        
#                         try:
#                             # template_icon 사용 (scale 값 크게 감소)
#                             image_row.template_icon(icon_value=ICONS_DICT[icon_name].icon_id, scale=3.0)
#                         except Exception as e:
#                             print(f"Error displaying icon for motion {motion_id}: {e}")
#                             image_row.label(text=f"Motion {motion_id}", icon="IMAGE_DATA")
#                     else:
#                         # 아이콘이 없는 경우
#                         image_col.label(text=f"Motion {motion_id}", icon="ERROR")
                    
#                     # 모션 이름
#                     name_row = image_col.row(align=True)
#                     name_row.alignment = 'CENTER'
#                     name_row.label(text=f"Motion {motion_id}")
                    
#                     # 버튼들
#                     button_row = image_col.row(align=True)
#                     button_row.scale_y = 1.0
                    
#                     # 웹사이트 열기 버튼
#                     op = button_row.operator("genaimo.open_motion_website", text="View", icon="ZOOM_ALL")
#                     op.motion_id = motion_id
                    
#                     # 향후 다운로드 버튼
#                     download_op = button_row.operator("genaimo.download_motion", text="Apply", icon="IMPORT")
#                     download_op.motion_id = motion_id
#                 else:
#                     row.separator()
        
#         layout.separator()
        
#         # 하단 정보
#         info_row = layout.row(align=True)
#         info_row.label(text="Click 'View' to open motion in browser", icon="INFO")
#         info_row.separator()
#         info_row.label(text=f"Total: {len(motion_ids)} motions", icon="LIBRARY_DATA_DIRECT")

# class OP_GenaimoOpenMotionWebsite(bpy.types.Operator):
#     """Open Motion in Website"""
#     bl_idname = "genaimo.open_motion_website"
#     bl_label = "View Motion"
#     bl_description = "Open motion in Genaimo website"
    
#     motion_id: bpy.props.StringProperty(name="Motion ID", default="672")

#     def execute(self, context):
#         url = f"https://genaimo.ailive.world/explore?motionId={self.motion_id}"
#         webbrowser.open(url)
        
#         self.report({'INFO'}, f"Opening motion {self.motion_id} in browser")
#         return {'FINISHED'}

# class OP_GenaimoMotionFilter(bpy.types.Operator):
#     """Filter Motions by Category"""
#     bl_idname = "genaimo.motion_filter_all"
#     bl_label = "All Motions"
#     bl_description = "Show all motions"

#     def execute(self, context):
#         self.report({'INFO'}, "Showing all motions")
#         return {'FINISHED'}

# class OP_GenaimoMotionFilterWalk(bpy.types.Operator):
#     """Filter Walking Motions"""
#     bl_idname = "genaimo.motion_filter_walk"
#     bl_label = "Walk Motions"
#     bl_description = "Show walking motions"

#     def execute(self, context):
#         self.report({'INFO'}, "Showing walking motions")
#         return {'FINISHED'}

# class OP_GenaimoMotionFilterRun(bpy.types.Operator):
#     """Filter Running Motions"""
#     bl_idname = "genaimo.motion_filter_run"
#     bl_label = "Run Motions"
#     bl_description = "Show running motions"

#     def execute(self, context):
#         self.report({'INFO'}, "Showing running motions")
#         return {'FINISHED'}

# class OP_GenaimoMotionFilterDance(bpy.types.Operator):
#     """Filter Dance Motions"""
#     bl_idname = "genaimo.motion_filter_dance"
#     bl_label = "Dance Motions"
#     bl_description = "Show dance motions"

#     def execute(self, context):
#         self.report({'INFO'}, "Showing dance motions")
#         return {'FINISHED'}

class OP_GenaimoMotionListPageUp(bpy.types.Operator):
    """Previous Page"""
    bl_idname = "genaimo.motion_list_page_up"
    bl_label = "Previous Page"
    bl_description = "Go to previous page"
    
    def execute(self, context):
        props = context.scene.genaimo_scene_properties
        if props.motion_list_page > 0:
            props.motion_list_page -= 1
        return {'FINISHED'}

class OP_GenaimoMotionListPageDown(bpy.types.Operator):
    """Next Page"""
    bl_idname = "genaimo.motion_list_page_down"
    bl_label = "Next Page"
    bl_description = "Go to next page"
    
    def execute(self, context):
        props = context.scene.genaimo_scene_properties
        props.motion_list_page += 1
        return {'FINISHED'}

# class OP_GenaimoDownloadMotion(bpy.types.Operator):
#     """Download Motion (Future Feature)"""
#     bl_idname = "genaimo.download_motion"
#     bl_label = "Download Motion"
#     bl_description = "Download motion data (Coming soon)"
    
#     motion_id: bpy.props.StringProperty(name="Motion ID", default="")

#     def execute(self, context):
#         self.report({'INFO'}, f"Download feature coming soon for motion {self.motion_id}")
#         return {'FINISHED'}
    

    
OPERATORS = [
    OP_LOAD_AVATAR,
    OP_GENAIMO_GENERATE,
    OP_GENAIMO_GENERATE_STYLIZED,
    OP_GenaimoOpenDeveloperPortal,
    OP_GenaimoOpenLicenseLink,
    OP_GenaimoOpenWebsiteLink,
    OP_GenaimoOpenDocsLink,
    OP_GenaimoOpenDiscordLink,
    OP_GenaimoSaveApiKey,
    OP_GenaimoEditApiKey,
    OP_GenaimoSelectAction,
    OP_GenaimoDeleteAction,
    OP_GenaimoPlayAction,
    OP_GenaimoStopAnimation,
    OP_GenaimoDeleteBatch,
    OP_GenaimoMotionListPageUp,
    OP_GenaimoMotionListPageDown,
    # Motion Library 관련 Operator들 (개발 기간상 임시 비활성화)
    # OP_GenaimoToggleMotionLibrary,
    # OP_GenaimoOpenMotionWebsite,
    # OP_GenaimoMotionFilter,
    # OP_GenaimoMotionFilterWalk,
    # OP_GenaimoMotionFilterRun,
    # OP_GenaimoMotionFilterDance,
    # OP_GenaimoDownloadMotion
]
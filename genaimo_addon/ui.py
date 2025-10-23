import bpy 
import os
#from properties import *

from .globals import ICONS_DICT, MOTION_LIBRARY_IMAGES

class GenaimoPanelBase(bpy.types.Panel):
    
    
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Genaimo'
    bl_options = {'HEADER_LAYOUT_EXPAND'}

# API panel 

class B_PT_GenaimoAllowInternetAccessPanel(GenaimoPanelBase, bpy.types.Panel):
    bl_idname = "B_PT_GenaimoAllowInternetAccessPanel"
    bl_label = "Genaimo"

    @ classmethod
    def poll(self, context):
        # only show panel if internet access is not allowed
        return not bpy.app.online_access

    def draw(self, context):
        layout = self.layout
        _label_multiline(
            context, "Allow Online Access must be enabled to use this extension. "
            "Enable it in Edit > Preferences > System > Network > Allow Online Access", layout)

class B_PT_GenaimoConfigureApiKeyPanel(GenaimoPanelBase, bpy.types.Panel):
    bl_idname = "B_PT_GenaimoConfigureApiKeyPanel"
    bl_label = "Genaimo"
    bl_options = {"DEFAULT_CLOSED"}  # 기본적으로 접혀있음

    @ classmethod
    def poll(self, context):
        # 항상 표시하되, 온라인 접근이 가능할 때만
        return bpy.app.online_access

    def draw(self, context):
        layout = self.layout
        
        # API 설정 상태 확인
        try:
            preferences = context.preferences
            addon_prefs = preferences.addons[__package__].preferences
            
            # Preferences만 확인
            has_key = bool(addon_prefs.api_key if addon_prefs else "")
            has_secret = bool(addon_prefs.api_secret if addon_prefs else "")
            
            # API 설정 상태 표시
            if has_key and has_secret and not context.scene.genaimo_scene_properties.show_api_edit:
                # API가 설정된 경우 - 최소화된 뷰
                status_row = layout.row()
                status_row.label(text="API Configured", icon="CHECKMARK")
                
                # 수정 버튼 (눌러야 입력 폼이 보임)
                edit_row = layout.row()
                edit_row.scale_y = 0.8
                edit_row.operator("genaimo.edit_api_key", text="Edit API Key", icon="PREFERENCES")
                
            else:
                # API가 설정되지 않았거나 편집 모드인 경우 - 전체 입력 폼 표시
                if not (has_key and has_secret):
                    status_row = layout.row()
                    status_row.label(text="API Not Configured", icon="ERROR")
                
                layout.label(
                    text="Configure API Key",
                    icon="INFO")
                col = layout.column(align=True)
                col.operator("genaimo.open_developer_portal", icon="LINKED")
                col.separator()
                
                # Preferences를 직접 표시 및 수정
                if addon_prefs:
                    col.prop(addon_prefs, "api_key")
                    col.prop(addon_prefs, "api_secret")
                
                # 저장 및 취소 버튼
                button_row = col.row(align=True)
                button_row.operator("genaimo.save_api_key", icon="KEYINGSET")
                if has_key and has_secret:
                    # 편집 모드일 때만 취소 버튼 표시
                    button_row.operator("genaimo.edit_api_key", text="Cancel", icon="CANCEL")
                
        except (KeyError, AttributeError) as e:
            # 오류 발생 시 기본 입력 폼 표시
            layout.label(text="Error loading preferences", icon="ERROR")
            layout.label(text=str(e))

 
            

# charater panel
class B_PT_GenaimoCharacterPanel(GenaimoPanelBase):  # Class name corrected with _PT_ prefix
    bl_label = "Load an Avatar"
    bl_idname = "B_PT_GenaimoCharacterPanel"
    
    @ classmethod
    def poll(self, context):
        # Show panel if API key and API secret are both set in Preferences
        try:
            preferences = context.preferences
            addon_prefs = preferences.addons[__package__].preferences
            
            # Only check Preferences (permanent storage)
            has_key = bool(addon_prefs.api_key if addon_prefs else "")
            has_secret = bool(addon_prefs.api_secret if addon_prefs else "")
            
            return has_key and has_secret and bpy.app.online_access
        except (KeyError, AttributeError):
            return False
    
    def draw(self, context):
        layout = self.layout
        
        layout.operator("genaimo.load_avatar")
        
        
# T2M panel 

class B_PT_GenaimoMotionListPanel(GenaimoPanelBase, bpy.types.Panel):
    # bl_parent_id를 제거하여 독립된 패널로 만듦
    bl_label = "Motion List"
    #bl_options = {"DEFAULT_CLOSED"}
    
    @ classmethod
    def poll(self, context):
        # Show panel if API key and API secret are both set in Preferences
        try:
            preferences = context.preferences
            addon_prefs = preferences.addons[__package__].preferences
            
            # Only check Preferences (permanent storage)
            has_key = bool(addon_prefs.api_key if addon_prefs else "")
            has_secret = bool(addon_prefs.api_secret if addon_prefs else "")
            
            return has_key and has_secret and bpy.app.online_access
        except (KeyError, AttributeError):
            return False

    def draw(self, context):
        layout = self.layout
        props = context.scene.genaimo_scene_properties
        
        # 현재 Armature 찾기
        armature = None
        for obj in bpy.context.scene.objects:
            if obj.type == 'ARMATURE':
                armature = obj
                break
        
        if armature is None:
            layout.label(text="No armature found", icon="ERROR")
            return
        
        # 현재 액션 표시
        current_action = armature.animation_data.action if armature.animation_data else None
        if current_action:
            layout.label(text=f"Current: {current_action.name}", icon="PLAY")
        
        layout.separator()
        
        # 액션 리스트 표시
        actions = bpy.data.actions
        if not actions:
            layout.label(text="No actions available", icon="INFO")
            return
        
        # batch_id별로 그룹핑
        batch_groups = {}
        ungrouped_actions = []
        
        for action in actions:
            if "genaimo_batch_id" in action:
                batch_id = action["genaimo_batch_id"]
                if batch_id not in batch_groups:
                    batch_groups[batch_id] = []
                batch_groups[batch_id].append(action)
            else:
                ungrouped_actions.append(action)
        
        # Batch별로 표시 (최신 batch가 위에)
        sorted_batch_ids = sorted(batch_groups.keys(), reverse=True)
        
        # 페이지네이션 적용
        items_per_page = props.motion_list_items_per_page
        current_page = props.motion_list_page
        total_batches = len(sorted_batch_ids)
        total_pages = max(1, (total_batches + items_per_page - 1) // items_per_page)
        
        # 페이지 범위 계산
        start_idx = current_page * items_per_page
        end_idx = min(start_idx + items_per_page, total_batches)
        visible_batch_ids = sorted_batch_ids[start_idx:end_idx]
        
        
        # 현재 페이지의 배치들만 표시
        for batch_id in visible_batch_ids:
            batch_actions = batch_groups[batch_id]
            
            # Batch 내 액션들을 index 순서대로 정렬
            batch_actions.sort(key=lambda a: a.get("genaimo_batch_index", 0))
            
            # Batch의 프롬프트 가져오기 (첫 번째 액션에서)
            batch_prompt = batch_actions[0].get("genaimo_prompt", f"Batch {batch_id}") if batch_actions else f"Batch {batch_id}"
            
            # Batch 헤더
            box = layout.box()
            header_row = box.row(align=True)
            header_row.label(text=batch_prompt, icon="WORDWRAP_ON")
            
            # Batch 전체 삭제 버튼
            if hasattr(bpy.ops, 'genaimo') and hasattr(bpy.ops.genaimo, 'delete_batch'):
                op = header_row.operator("genaimo.delete_batch", text="", icon="TRASH")
                op.batch_id = batch_id
            
            # 모션 선택 버튼들
            motion_row = box.row(align=True)
            
            for i, action in enumerate(batch_actions):
                batch_index = action.get("genaimo_batch_index", 0)
                
                # 현재 선택된 액션인지 확인
                is_selected = current_action and current_action.name == action.name
                
                # 선택 버튼
                if hasattr(bpy.ops, 'genaimo') and hasattr(bpy.ops.genaimo, 'select_action'):
                    col = motion_row.column(align=True)
                    col.scale_y = 1.2
                    
                    # 선택된 액션은 다른 스타일
                    if is_selected:
                        op = col.operator("genaimo.select_action", text=f"{batch_index+1}", depress=True)
                    else:
                        op = col.operator("genaimo.select_action", text=f"{batch_index+1}")
                    op.action_name = action.name
        
        # 그룹화되지 않은 액션들 표시
        if ungrouped_actions:
            layout.separator()
            layout.label(text="Ungrouped Actions", icon="SOLO_OFF")
            
            for action in ungrouped_actions:
                row = layout.row(align=True)
                
                # 액션 선택 버튼
                if hasattr(bpy.ops, 'genaimo') and hasattr(bpy.ops.genaimo, 'select_action'):
                    if current_action and current_action.name == action.name:
                        op = row.operator("genaimo.select_action", text=action.name, icon="RADIOBUT_ON")
                        op.action_name = action.name
                    else:
                        op = row.operator("genaimo.select_action", text=action.name)
                        op.action_name = action.name
                else:
                    if current_action and current_action.name == action.name:
                        row.label(text=f"● {action.name}", icon="RADIOBUT_ON")
                    else:
                        row.label(text=action.name)
                
                # 액션 삭제 버튼
                if hasattr(bpy.ops, 'genaimo') and hasattr(bpy.ops.genaimo, 'delete_action'):
                    op = row.operator("genaimo.delete_action", text="", icon="X")
                    op.action_name = action.name
                else:
                    row.enabled = False
                    row.operator("genaimo.delete_action", text="", icon="X")
        
        # 네비게이션 컨트롤 (아래쪽)
        if total_pages > 1:
            layout.separator()
            
            # 범위 정보
            range_row = layout.row(align=True)
            range_row.label(text=f"{start_idx + 1}-{end_idx} of {total_batches}")
            
            # 네비게이션 버튼
            nav_row = layout.row(align=True)
            nav_row.scale_y = 0.8
            
            # 이전 페이지 버튼
            if current_page > 0:
                nav_row.operator("genaimo.motion_list_page_up", text="◀", icon="TRIA_LEFT")
            else:
                prev_col = nav_row.column()
                prev_col.enabled = False
                prev_col.operator("genaimo.motion_list_page_up", text="◀", icon="TRIA_LEFT")
            
            # 다음 페이지 버튼
            if current_page < total_pages - 1:
                nav_row.operator("genaimo.motion_list_page_down", text="▶", icon="TRIA_RIGHT")
            else:
                next_col = nav_row.column()
                next_col.enabled = False
                next_col.operator("genaimo.motion_list_page_down", text="▶", icon="TRIA_RIGHT")
        
        layout.separator()
        
        # 액션 정보 표시
        if current_action:
            info_row = layout.row()
            info_row.label(text=f"Frames: {int(current_action.frame_range[0])}-{int(current_action.frame_range[1])}", icon="TIME")
            
            # 액션 재생 버튼
            play_row = layout.row(align=True)
            if hasattr(bpy.ops, 'genaimo') and hasattr(bpy.ops.genaimo, 'play_action'):
                op = play_row.operator("genaimo.play_action", text="Play", icon="PLAY")
                op.action_name = current_action.name
            else:
                play_row.enabled = False
                play_row.operator("genaimo.play_action", text="Play", icon="PLAY")
            
            if hasattr(bpy.ops, 'genaimo') and hasattr(bpy.ops.genaimo, 'stop_animation'):
                play_row.operator("genaimo.stop_animation", text="Stop", icon="SNAP_FACE_CENTER")
            else:
                play_row.enabled = False
                play_row.operator("genaimo.stop_animation", text="Stop", icon="SNAP_FACE_CENTER")
        
            

class B_PT_GenaimoAdvancedOptionsPanel(GenaimoPanelBase, bpy.types.Panel):
    bl_parent_id = "B_PT_GenaimoUIPanel"
    bl_label = "Advanced Options"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        
        layout = self.layout
        col = layout.column(align=True)
        col.label(text = "Durations") # if it's 0 we're gonna use length estimato
        col.prop(context.scene.genaimo_scene_properties, "use_length_estimator")

        if not context.scene.genaimo_scene_properties.use_length_estimator:
            
            
            
            col.prop(context.scene.genaimo_scene_properties, "frames_input")
            
            col.prop(context.scene.genaimo_scene_properties, "start_frame_input")
            # row = col.row()
            # split = row.split(factor=0.6)
            # col = split.column()
            # col.prop(context.scene.genaimo_scene_properties,
            #         context.scene.genaimo_scene_properties.duration_unit)
            # split = split.split()
            # col = split.column()
            # col.prop(context.scene.genaimo_scene_properties, "duration_unit")

        # layout.label(text = "frames") # if it's 0 we're gonna use length estimator
        # layout.row().prop(context.scene.genaimo_scene_properties, "use_length_estimator")
        
        # layout.row().prop(context.scene.genaimo_scene_properties, "frames_input")
        # layout.label(text = "start frame") # if it's 0 we're gonna use length estimator
        # layout.row().prop(context.scene.genaimo_scene_properties, "start_frame_input")


class B_PT_GenaimoUIPanel(GenaimoPanelBase, bpy.types.Panel):  # Class name corrected with _PT_ prefix
    bl_label = "Text to Motion"
    bl_idname = "B_PT_GenaimoUIPanel"

    @ classmethod
    def poll(self, context):
        # Show panel if API key and API secret are both set in Preferences
        try:
            preferences = context.preferences
            addon_prefs = preferences.addons[__package__].preferences
            
            # Only check Preferences (permanent storage)
            has_key = bool(addon_prefs.api_key if addon_prefs else "")
            has_secret = bool(addon_prefs.api_secret if addon_prefs else "")
            
            return has_key and has_secret and bpy.app.online_access
        except (KeyError, AttributeError):
            return False

    def draw(self, context):
        layout = self.layout
        active_object = bpy.context.active_object
        if not active_object or active_object.type != 'ARMATURE':
            layout.label(
                text="Select an armature", icon="ERROR")
            return

        
        layout.row().prop(context.scene.genaimo_scene_properties, "text_input")
        
        # layout.label(text = "frames") # if it's 0 we're gonna use length estimator
        # layout.row().prop(context.scene.genaimo_scene_properties, "use_length_estimator")
        
        # layout.row().prop(context.scene.genaimo_scene_properties, "frames_input")
        # layout.label(text = "start frame") # if it's 0 we're gonna use length estimator
        # layout.row().prop(context.scene.genaimo_scene_properties, "start_frame_input")
        
        # Generate 버튼과 Motion Library 버튼을 한 줄에 배치
        button_row = layout.row(align=True)
        button_row.operator("genaimo.generate", icon="PLAY")
        
        layout.separator()
        
        # Motion Library 버튼 (개발 기간상 임시 비활성화)
        # library_row = layout.row(align=True)
        # library_row.scale_y = 1.2
        # library_row.operator("genaimo.toggle_motion_library", text="Explore Motion Library", icon="LIBRARY_DATA_DIRECT") 
  



class B_PT_GenaimoStylizePanel(GenaimoPanelBase, bpy.types.Panel):
    #bl_parent_id = "B_PT_GenaimoPanel"
    bl_label = "Stylize"
    bl_options = {"DEFAULT_CLOSED"}
    
    
    @ classmethod
    def poll(self, context):
        # Show panel if API key and API secret are both set in Preferences
        try:
            preferences = context.preferences
            addon_prefs = preferences.addons[__package__].preferences
            
            # Only check Preferences (permanent storage)
            has_key = bool(addon_prefs.api_key if addon_prefs else "")
            has_secret = bool(addon_prefs.api_secret if addon_prefs else "")
            
            return has_key and has_secret and bpy.app.online_access
        except (KeyError, AttributeError):
            return False

    def draw(self, context):
        layout = self.layout
        active_object = bpy.context.active_object
        if not active_object or active_object.type != 'ARMATURE':
            layout.label(
                text="Select an armature", icon="ERROR")
            return

        col = layout.column(align=True)
        col.prop(context.scene.genaimo_scene_properties, "stylize_opt")
        col.operator("genaimo.generate_stylized", icon="MODIFIER") 
        

class B_PT_GenaimoStylizeAdvancedOptionsPanel(GenaimoPanelBase, bpy.types.Panel):
    bl_parent_id = "B_PT_GenaimoStylizePanel"
    bl_label = "Advanced Options"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        
        layout = self.layout
        col = layout.column(align=True)
        col.label(text = "Anim range") # if it's 0 we're gonna use length estimato
        col.prop(context.scene.genaimo_scene_properties, "use_all_frames")

        if not context.scene.genaimo_scene_properties.use_all_frames:
            
            col.prop(context.scene.genaimo_scene_properties, "stylized_start_frame_input")
            col.prop(context.scene.genaimo_scene_properties, "stylized_end_frame_input")

    
class B_PT_GenaimoInfoPanel(GenaimoPanelBase, bpy.types.Panel):
    #bl_parent_id = "B_PT_GenaimoPanel"
    bl_label = "Genaimo Info"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        #_label_multiline(
        #    context, "All generated animations are licensed under", layout)
        #layout.operator("genaimo.open_license", icon="LINKED")
        
        col = layout.column(align=True)
        row = col.row(align=True)
        row.operator("genaimo.open_license")
        row.operator("genaimo.open_website")
        row = col.row(align=True)
        row.operator("genaimo.open_docs")
        row.operator("genaimo.open_discord")

# Motion Library Panel은 이제 팝업 윈도우로 대체됨 (operators.py 참조)


import textwrap
def _label_multiline(context, text, parent):
    # https://b3d.interplanety.org/en/multiline-text-in-blender-interface-panels/
    chars = int(context.region.width / 7)   # 7 pix on 1 character
    wrapper = textwrap.TextWrapper(width=chars)
    text_lines = wrapper.wrap(text=text)
    for text_line in text_lines:
        parent.label(text=text_line)



UI_CLASSES = [
    B_PT_GenaimoAllowInternetAccessPanel,
    B_PT_GenaimoConfigureApiKeyPanel,
    B_PT_GenaimoCharacterPanel,
    B_PT_GenaimoUIPanel,
    B_PT_GenaimoAdvancedOptionsPanel,
    B_PT_GenaimoStylizePanel,
    B_PT_GenaimoStylizeAdvancedOptionsPanel,
    B_PT_GenaimoMotionListPanel,  # 독립된 패널로 이동
    B_PT_GenaimoInfoPanel,
]
import bpy 
from mathutils import Quaternion, Vector, Euler, Matrix
from .globals import (
    MeshyAI_BoneName,
    GMO_BoneName,
    GMO_GLB_FILE
)


def init_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)


def get_initial_global_rot(armature, bone_names):
    rot_arr = []

    for bone_name in bone_names:
        if bone_name in armature.pose.bones:
            pbone = armature.pose.bones[bone_name]

            mat_world = armature.matrix_world @ pbone.matrix
            global_quat = mat_world.to_quaternion()

            rot_arr.append(global_quat)
        else:
            rot_arr.append(Quaternion())
    
    return rot_arr


def get_initial_global_pos(armature, bone_names):
    pos_arr = []
    
    for bone_name in bone_names:
        if bone_name in armature.pose.bones:
            pbone = armature.pose.bones[bone_name]
            
            # 본의 월드 위치 가져오기
            mat_world = armature.matrix_world @ pbone.matrix
            global_pos = mat_world.to_translation()
            
            pos_arr.append(global_pos)
        else:
            # 누락된 본에 대해서는 기본값
            pos_arr.append(Vector((0, 0, 0)))
    
    return pos_arr


def get_initial_rot(armature, bone_names):
    rot_arr = []
    
    for bone_name in bone_names:
        if bone_name in armature.pose.bones:
            pbone = armature.pose.bones[bone_name]
            # bone.rotation과 동일 - 본의 로컬 회전
            rot_arr.append(pbone.matrix.to_quaternion())
        else:
            rot_arr.append(Quaternion((1, 0, 0, 0)))
    
    return rot_arr


def get_initial_pos(armature, bone_names):
    pos_arr = []
    
    for bone_name in bone_names:
        if bone_name in armature.pose.bones:
            pbone = armature.pose.bones[bone_name]
            # bone.position과 동일 - 본의 로컬 위치
            pos_arr.append(pbone.matrix.to_translation())
        else:
            pos_arr.append(Vector((0, 0, 0)))
    
    return pos_arr



def convert_json_to_blender(json_quat):
    w, x, y, z = json_quat
    quat = Quaternion((w, x, z, -y))
    return quat

def convert_json_position_to_blender(json_pos):
    x, y, z = json_pos
    return Vector((x, -z, y))

def convert_blender_to_json(blender_quat):
    """Blender 쿼터니언을 JSON 형식으로 변환"""
    w, x, y, z = blender_quat
    return Quaternion((w, x, -z, y))

def convert_blender_position_to_json(blender_pos):
    """Blender 위치를 JSON 형식으로 변환"""
    x, y, z = blender_pos
    return Vector((x, z, -y))


# 기존 액션을 이어쓸 때 시작 프레임의 pelvis 기준(이미 추가하신 created_action/FCurve 조회 활용)
def get_pelvis_base_from_existing(action, bone_name="pelvis"):
    loc_x = action.fcurves.find(f'pose.bones["{bone_name}"].location', index=0)
    loc_y = action.fcurves.find(f'pose.bones["{bone_name}"].location', index=1)
    loc_z = action.fcurves.find(f'pose.bones["{bone_name}"].location', index=2)
    if not (loc_x and loc_y and loc_z):
        return Vector((0,0,0))
    # 기존 액션의 마지막 키프레임 값 활용
    last_x = loc_x.keyframe_points[-1].co[1] if loc_x.keyframe_points else 0.0
    last_y = loc_y.keyframe_points[-1].co[1] if loc_y.keyframe_points else 0.0
    last_z = loc_z.keyframe_points[-1].co[1] if loc_z.keyframe_points else 0.0
    return Vector((last_x, last_y, last_z))


def fix_fps_motion(json_data,current_fps=None):
    """
    JSON 애니메이션 데이터를 현재 Blender FPS에 맞게 리샘플링
    
    Args:
        json_data: 원본 JSON 데이터
        
    Returns:
        dict: FPS가 조정된 JSON 데이터
    """
    from mathutils import Quaternion, Vector
    import math
    
    current_fps = bpy.context.scene.render.fps if current_fps is None else current_fps
    model_fps = json_data.get("Framerate", 20)
    
    # FPS가 같으면 그대로 반환
    if current_fps == model_fps:
        return json_data
    
    #print(f"FPS 조정: {model_fps} -> {current_fps}")
    
    # 원본 데이터
    original_frames = json_data["AnimationData"]
    if not original_frames:
        return json_data
    
    # 시간 기반으로 데이터 정리
    time_data = []
    for frame_data in original_frames:
        frame_num = frame_data["Frame"]
        time_seconds = (frame_num - 1) / model_fps  # 0-based 시간
        time_data.append({
            'time': time_seconds,
            'position': Vector(frame_data["RootPosition"]),
            'rotations': [Quaternion((q[0], q[1], q[2], q[3])) for q in frame_data["Rotation"]]
        })
    
    # 새로운 프레임 데이터 생성
    new_animation_data = []
    total_duration = time_data[-1]['time']  # 마지막 프레임 시간
    new_frame_count = int(total_duration * current_fps) + 1
    
    for new_frame in range(1, new_frame_count + 1):
        new_time = (new_frame - 1) / current_fps
        
        # 보간할 데이터 찾기
        interpolated_data = interpolate_frame_data(time_data, new_time)
        
        # JSON 형태로 변환
        frame_data = {
            "Frame": new_frame,
            "RootPosition": [interpolated_data['position'].x, interpolated_data['position'].y, interpolated_data['position'].z],
            "Rotation": []
        }
        
        for quat in interpolated_data['rotations']:
            frame_data["Rotation"].append([quat.w, quat.x, quat.y, quat.z])
        
        new_animation_data.append(frame_data)
    
    # 새로운 JSON 데이터 생성
    new_json_data = json_data.copy()
    new_json_data["Framerate"] = current_fps
    new_json_data["AnimationData"] = new_animation_data
    
    #print(f"프레임 수: {len(original_frames)} -> {len(new_animation_data)}")
    
    return new_json_data


def interpolate_frame_data(time_data, target_time):
    """
    주어진 시간에서 프레임 데이터를 보간
    
    Args:
        time_data: 시간별 데이터 리스트
        target_time: 보간할 목표 시간
        
    Returns:
        dict: 보간된 position과 rotations
    """
    from mathutils import Quaternion, Vector
    
    # 경계 처리
    if target_time <= time_data[0]['time']:
        return time_data[0]
    if target_time >= time_data[-1]['time']:
        return time_data[-1]
    
    # 보간할 두 프레임 찾기
    for i in range(len(time_data) - 1):
        if time_data[i]['time'] <= target_time <= time_data[i + 1]['time']:
            t1, t2 = time_data[i]['time'], time_data[i + 1]['time']
            frame1, frame2 = time_data[i], time_data[i + 1]
            
            # 보간 비율 계산
            if t2 - t1 == 0:
                alpha = 0.0
            else:
                alpha = (target_time - t1) / (t2 - t1)
            
            # 위치 선형 보간
            interpolated_position = frame1['position'].lerp(frame2['position'], alpha)
            
            # 회전 Slerp 보간
            interpolated_rotations = []
            for j in range(len(frame1['rotations'])):
                quat1 = frame1['rotations'][j]
                quat2 = frame2['rotations'][j]
                # 쿼터니언이 정규화되어 있는지 확인
                quat1.normalize()
                quat2.normalize()
                interpolated_quat = quat1.slerp(quat2, alpha)
                interpolated_rotations.append(interpolated_quat)
            
            return {
                'position': interpolated_position,
                'rotations': interpolated_rotations
            }
    
    # 기본값 반환 (발생하지 않아야 함)
    return time_data[0]

def json_retarget(json_data, glb_file=GMO_GLB_FILE,start_frame=1,export=None):
    # FPS 조정
    json_data = fix_fps_motion(json_data)
        
    use_gmo_model = True
    BoneName = GMO_BoneName if use_gmo_model else MeshyAI_BoneName
    
    # start frame으로 먼저 세팅 
    
    bpy.context.scene.frame_start = start_frame
    
    initialRot = {}
    initialGlobalRot = {}
    initialPos = {}
    initialGlobalPos = {}
    inverseRootGlobalRot = None
    Title = json_data.get("Title", None)
    Data = json_data.get("AnimationData", None) # currently use only first data
    FrameRate = json_data.get("Framerate", None)

    if Data is not None and FrameRate is not None and len(Data) > 0:
        Time = round(len(Data) / FrameRate, 2)
    else:
        Time = 0

    scale_factor = 100

    armature = None
    for obj in bpy.context.scene.objects:
        if obj.type == 'ARMATURE':
            armature = obj
            break

    if armature is None:
        print("Armature 객체를 찾을 수 없습니다.")
    else:
        bpy.context.view_layer.objects.active = armature
        bpy.ops.object.mode_set(mode='POSE')
        
        for pb in armature.pose.bones:
            pb.bone.select = True
        bpy.ops.pose.transforms_clear()

        bpy.context.view_layer.update()

        initialPos = get_initial_pos(armature, BoneName)
        initialRot = get_initial_rot(armature, BoneName)
        
        initialGlobalPos = get_initial_global_pos(armature, BoneName)
        initialGlobalRot = get_initial_global_rot(armature, BoneName)
        
        
        # 루트 본의 글로벌 초기 회전 역행렬만 저장
        if len(initialGlobalRot) > 0:
            inverseRootGlobalRot = initialGlobalRot[0].inverted()

        bpy.ops.object.mode_set(mode='OBJECT')
        
        

    # Armature 오브젝트, pose bones 가져오기
    armature = None
    for obj in bpy.context.scene.objects:
        if obj.type == 'ARMATURE':
            armature = obj
            break
    if armature is None:
        raise Exception("Armature 오브젝트를 찾을 수 없습니다.")
        


    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')
    pose_bones = armature.pose.bones
    initial_pelvis_pos_x = pose_bones['pelvis'].location.x
    initial_pelvis_pos_y = pose_bones['pelvis'].location.y
    initial_pelvis_pos_z = pose_bones['pelvis'].location.z
    # 기존 애니메이션 데이터가 있으면 사용, 없으면 새로 생성
    if not armature.animation_data:
        armature.animation_data_create()
    
    # 기존 액션이 있으면 사용, 없으면 새로 생성
    if False : # armature.animation_data.action:
        action = armature.animation_data.action
        created_action = False
    else:
        action = bpy.data.actions.new(name=Title[:60])
        armature.animation_data.action = action
        created_action = True
        
    if armature.animation_data and armature.animation_data.action:
        pelvis_base = get_pelvis_base_from_existing(armature.animation_data.action)
    else:
        pelvis_base = pose_bones['pelvis'].location.copy()

    BoneParent = [-1, 0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 9, 9, 12, 13, 14, 16, 17, 18, 19, 20, 22, 23, 20, 25, 26, 20, 28, 29, 20, 31, 32, 20, 34, 35, 21, 37, 38, 21, 40, 41, 21, 43, 44, 21, 46, 47, 21, 49, 50];


    for bone_name in BoneName:
        if bone_name not in pose_bones:
            print(f"본 {bone_name} 없음")
            continue
        pb = pose_bones[bone_name]
        bone_index = BoneName.index(bone_name)
        if created_action:
            # FCurve 경로 문자열
            fc_loc_x = action.fcurves.new(data_path=f'pose.bones["{bone_name}"].location', index=0)
            fc_loc_y = action.fcurves.new(data_path=f'pose.bones["{bone_name}"].location', index=1)
            fc_loc_z = action.fcurves.new(data_path=f'pose.bones["{bone_name}"].location', index=2)
            fc_rot_w = action.fcurves.new(data_path=f'pose.bones["{bone_name}"].rotation_quaternion', index=0)
            fc_rot_x = action.fcurves.new(data_path=f'pose.bones["{bone_name}"].rotation_quaternion', index=1)
            fc_rot_y = action.fcurves.new(data_path=f'pose.bones["{bone_name}"].rotation_quaternion', index=2)
            fc_rot_z = action.fcurves.new(data_path=f'pose.bones["{bone_name}"].rotation_quaternion', index=3)
        else:
            # FCurve 경로 문자열
            fc_loc_x = action.fcurves.find(data_path=f'pose.bones["{bone_name}"].location', index=0)
            fc_loc_y = action.fcurves.find(data_path=f'pose.bones["{bone_name}"].location', index=1)
            fc_loc_z = action.fcurves.find(data_path=f'pose.bones["{bone_name}"].location', index=2)
            fc_rot_w = action.fcurves.find(data_path=f'pose.bones["{bone_name}"].rotation_quaternion', index=0)
            fc_rot_x = action.fcurves.find(data_path=f'pose.bones["{bone_name}"].rotation_quaternion', index=1)
            fc_rot_y = action.fcurves.find(data_path=f'pose.bones["{bone_name}"].rotation_quaternion', index=2)
            fc_rot_z = action.fcurves.find(data_path=f'pose.bones["{bone_name}"].rotation_quaternion', index=3)
        
        # 키프레임 삽입 반복
        for frame_data in Data:
            frame_number = frame_data["Frame"]
            blender_frame = frame_number + start_frame - 1
            
            # 위치 데이터 (Hips만) - scale 적용
            if bone_index == 0:  # Hips
                pos = frame_data["RootPosition"]
                # Unity 좌표계를 Blender 좌표계로 변환하고 scale 적용
                blender_pos = convert_json_position_to_blender(pos)
                offset = Vector((0, 0, -93))
                
                if inverseRootGlobalRot is not None:
                    blender_pos = inverseRootGlobalRot @ blender_pos
                    offset = inverseRootGlobalRot @ offset
                
                # TypeScript와 동일한 간단한 계산
                
                final_pos = Vector((
                    blender_pos.x * scale_factor + offset.x,
                    blender_pos.y * scale_factor + offset.y,
                    blender_pos.z * scale_factor + offset.z ,
                ))
                final_pos.x += pelvis_base.x
                final_pos.y += pelvis_base.y
                final_pos.z += pelvis_base.z
                fc_loc_x.keyframe_points.insert(frame=blender_frame, value=final_pos.x)
                fc_loc_y.keyframe_points.insert(frame=blender_frame, value=final_pos.y)
                fc_loc_z.keyframe_points.insert(frame=blender_frame, value=final_pos.z)

            # 회전 데이터
            rot = frame_data["Rotation"]
            
            if bone_index < len(rot):
                q = rot[bone_index]
                json_quat = Quaternion((q[0], q[1], q[2], q[3]))
                blender_quat = convert_json_to_blender(json_quat)

                # 여기에 추가
                temp_num = bone_index
                temp_parent_num = bone_index
                temp_parent_quat = Quaternion((1, 0, 0, 0))  # identity

                while BoneName[BoneParent[temp_num]] == "":
                    temp_parent_num = BoneParent[temp_num]
                    if temp_parent_num < len(rot):
                        q = rot[temp_parent_num]
                        temp_quat2 = convert_json_to_blender(Quaternion((q[0], q[1], q[2], q[3])))
                        temp_parent_quat = temp_parent_quat @ temp_quat2
                    temp_num = temp_parent_num

                identity_quat = Quaternion((1, 0, 0, 0))
                
                if temp_parent_quat != identity_quat:
                    blender_quat = blender_quat @ temp_parent_quat 
                    
                if bone_index < len(initialGlobalRot):
                     parent_rotation = initialGlobalRot[bone_index]
                    
                     if BoneParent[bone_index] == -1:
                         correct_quat = parent_rotation.inverted() @ blender_quat @ parent_rotation
    #                     correct_quat = correct_quat @ ROT_CORRECTION.to_quaternion()
                         correct_quat = correct_quat
                         blender_quat = correct_quat
                     else:
                         correct_quat = parent_rotation.inverted() @ blender_quat @ parent_rotation
                         blender_quat = correct_quat          

                # initialRotation 체크 - 인덱스 기반 접근
                if bone_index >= len(initialRot):
                    continue

                local_rotation = initialRot[bone_index]

                blender_quat.normalize()
                
                fc_rot_w.keyframe_points.insert(frame=blender_frame, value=blender_quat.w)
                fc_rot_x.keyframe_points.insert(frame=blender_frame, value=blender_quat.x)
                fc_rot_y.keyframe_points.insert(frame=blender_frame, value=blender_quat.y)
                fc_rot_z.keyframe_points.insert(frame=blender_frame, value=blender_quat.z)
            else:
                # 기본값
                fc_rot_w.keyframe_points.insert(frame=blender_frame, value=1)
                fc_rot_x.keyframe_points.insert(frame=blender_frame, value=0)
                fc_rot_y.keyframe_points.insert(frame=blender_frame, value=0)
                fc_rot_z.keyframe_points.insert(frame=blender_frame, value=0)

            
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.scene.render.fps =  FrameRate
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = len(Data) + start_frame - 1

    #print("애니메이션 액션 생성 완료")
    
    # 생성된 action 반환
    return action



def motion_to_json(start_frame=1, end_frame=None):
    """
    현재 캐릭터의 모션을 JSON 형태로 변환
    
    Args:
        start_frame: 시작 프레임
        end_frame: 끝 프레임 (None일 경우 액션의 끝까지)
    
    Returns:
        dict: JSON 형태의 애니메이션 데이터
    """
    import json
    from mathutils import Quaternion, Vector
    
    # Armature 객체 찾기
    armature = None
    for obj in bpy.context.scene.objects:
        if obj.type == 'ARMATURE':
            armature = obj
            break
    
    if armature is None:
        raise Exception("Armature 객체를 찾을 수 없습니다.")
    
    # 액션이 없으면 빈 데이터 반환
    if not armature.animation_data or not armature.animation_data.action:
        return {
            "Title": "Empty Motion",
            "Framerate": bpy.context.scene.render.fps,
            "AnimationData": []
        }
    
    action = armature.animation_data.action
    
    # end_frame이 None이면 액션의 끝 프레임 사용
    if end_frame is None:
        end_frame = int(action.frame_range[1])
    
    # 프레임 범위 설정
    frame_start = max(start_frame, int(action.frame_range[0]))
    frame_end = min(end_frame, int(action.frame_range[1]))
    
    # Bone 이름과 부모 관계 (json_retarget와 동일)
    BoneName = GMO_BoneName
    BoneParent = [-1, 0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 9, 9, 12, 13, 14, 16, 17, 18, 19, 20, 22, 23, 20, 25, 26, 20, 28, 29, 20, 31, 32, 20, 34, 35, 21, 37, 38, 21, 40, 41, 21, 43, 44, 21, 46, 47, 21, 49, 50]

    # 초기 위치/회전 및 글로벌 회전 저장 (json_retarget와 동일 베이스)
    initial_pos = get_initial_pos(armature, BoneName)
    initial_rot = get_initial_rot(armature, BoneName)
    initialGlobalRot = get_initial_global_rot(armature, BoneName)

    inverseRootGlobalRot = None
    if len(initialGlobalRot) > 0:
        inverseRootGlobalRot = initialGlobalRot[0].inverted()

    # json_retarget에서 사용한 scale/offset/pelvis_base를 역적용하기 위한 값
    scale_factor = 100
    offset0 = Vector((0, 0, -93))
    pelvis_base = get_pelvis_base_from_existing(action, bone_name="pelvis")
    
    # 애니메이션 데이터 배열
    animation_data = []
    
    # 각 프레임에 대해 데이터 추출
    for frame in range(frame_start, frame_end + 1):
        # 프레임 설정
        bpy.context.scene.frame_set(frame)
        
        frame_data = {
            "Frame": frame - start_frame + 1,  # 상대 프레임 번호
            "RootPosition": [0.0, 0.0, 0.0],
            "Rotation": []
        }
        
        # 각 본에 대한 회전 데이터 추출
        for bone_index, bone_name in enumerate(BoneName):
            if bone_name in armature.pose.bones:
                pb = armature.pose.bones[bone_name]
                # 현재 로컬 회전 (json_retarget에서 최종 키된 로컬 쿼터니언과 동일 축을 가정)
                current_local_rot = pb.rotation_quaternion.copy()
                current_local_rot.normalize()

                # json_retarget에서 적용되었던 parent_rotation 보정을 역적용
                # forward: correct = parent_rotation.inverted() @ blender_quat @ parent_rotation
                # invert:  pre_parent = parent_rotation @ current_local_rot @ parent_rotation.inverted()
                if bone_index < len(initialGlobalRot):
                    parent_rotation = initialGlobalRot[bone_index]
                else:
                    parent_rotation = Quaternion((1, 0, 0, 0))

                pre_parent_rot = parent_rotation @ current_local_rot @ parent_rotation.inverted()

                # temp_parent_quat의 영향은 JSON 생성시 상위 무명 본 보정을 위해 곱해졌음.
                # 현재 리그에선 대부분 명명됨을 가정하고, 역변환에선 이를 생략(==identity)합니다.
                blender_space_rot_pre_temp = pre_parent_rot

                # Blender → JSON 좌표계로 변환
                json_quat = convert_blender_to_json(blender_space_rot_pre_temp)
                
                # Root Position (Hips 본의 위치)
                if bone_index == 0:  # Hips
                    # forward에서 fcurve에 기록된 값(final_pos)을 현재 pb.location으로 간주하고 역변환
                    final_pos = pb.location.copy()

                    # pelvis_base 제거
                    rel = final_pos - pelvis_base

                    if inverseRootGlobalRot is not None:
                        # forward: rel = (inverseRootGlobalRot @ blender_pos) * s + (inverseRootGlobalRot @ offset0)
                        # invert:  blender_pos = inverseRootGlobalRot.inverted() @ ((rel - (inverseRootGlobalRot @ offset0)) / s)
                        rotated_offset = inverseRootGlobalRot @ offset0
                        blender_pos_unscaled = (rel - rotated_offset) / scale_factor
                        blender_pos = inverseRootGlobalRot.inverted() @ blender_pos_unscaled
                    else:
                        blender_pos = (rel - offset0) / scale_factor

                    # Blender → JSON 좌표계로 변환
                    json_pos = convert_blender_position_to_json(blender_pos)
                    frame_data["RootPosition"] = [json_pos.x, json_pos.y, json_pos.z]
                
                # 회전 데이터 추가
                frame_data["Rotation"].append([
                    json_quat.w, json_quat.x, json_quat.y, json_quat.z
                ])
            else:
                # 본이 없는 경우 기본값 (identity quaternion)
                frame_data["Rotation"].append([1.0, 0.0, 0.0, 0.0])
        
        animation_data.append(frame_data)
    
    # JSON 데이터 구성
    json_data = {
        "Title": action.name,
        "Framerate": bpy.context.scene.render.fps,
        "AnimationData": animation_data
    }
    
    json_data = fix_fps_motion(json_data,current_fps=20)
    
    return json_data
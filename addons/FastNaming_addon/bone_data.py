"""
AutoNaming_addon - 骨骼命名规范种子数据

本模块存放内置的默认命名规范，供首次安装时填充到偏好设置中。
每个规范包含 name 与 bones 列表，每个 bone 含 name/category/side 三个字段。

约定：
- 对于成对出现的骨骼（左右对称），仅在数据中定义 LEFT 一侧。
  渲染预制按钮时由面板调用 mirror_name() 自动生成 RIGHT 一侧的按钮。
- side 字段取值：
  - "NONE"：中线骨骼（如脊柱、头），不镜像
  - "LEFT"：左侧骨骼（如左臂），渲染时自动镜像生成右侧按钮
  - "RIGHT"：用户自定义时也可显式声明为右侧（面板仍会镜像出左侧按钮）
"""

# 身体部位显示顺序（用于面板分组排序）
# 面板按此顺序渲染各分组的折叠 box；未在此列表中的 category（如用户自定义的 "Custom"）追加到末尾
CATEGORY_ORDER = ["Root", "Spine", "Head", "Arm", "Hand", "Leg", "Foot"]


# 默认命名规范的种子数据
# 包含 4 套常用规范：通用短名规范（默认）、Mixamo、Blender Rigify、Unreal/Maya
DEFAULT_CONVENTIONS = [
    {
        # 通用短名规范：使用 _L/_R 后缀，简洁跨引擎通用
        "name": "Generic Short",
        "bones": [
            # Root - 根与胯部
            {"name": "root",     "category": "Root",  "side": "NONE"},
            {"name": "hips",     "category": "Root",  "side": "NONE"},
            # Spine - 脊柱链
            {"name": "spine_01", "category": "Spine", "side": "NONE"},
            {"name": "spine_02", "category": "Spine", "side": "NONE"},
            {"name": "spine_03", "category": "Spine", "side": "NONE"},
            {"name": "chest",    "category": "Spine", "side": "NONE"},
            {"name": "neck",     "category": "Spine", "side": "NONE"},
            # Head - 头部
            {"name": "head",  "category": "Head", "side": "NONE"},
            {"name": "jaw",   "category": "Head", "side": "NONE"},
            {"name": "eye_L", "category": "Head", "side": "LEFT"},
            # Arm - 手臂
            {"name": "shoulder_L",  "category": "Arm",  "side": "LEFT"},
            {"name": "upper_arm_L", "category": "Arm",  "side": "LEFT"},
            {"name": "forearm_L",   "category": "Arm",  "side": "LEFT"},
            # Hand - 手部（含手指链）
            {"name": "hand_L",      "category": "Hand", "side": "LEFT"},
            {"name": "thumb_01_L",  "category": "Hand", "side": "LEFT"},
            {"name": "thumb_02_L",  "category": "Hand", "side": "LEFT"},
            {"name": "thumb_03_L",  "category": "Hand", "side": "LEFT"},
            {"name": "index_01_L",  "category": "Hand", "side": "LEFT"},
            {"name": "index_02_L",  "category": "Hand", "side": "LEFT"},
            {"name": "index_03_L",  "category": "Hand", "side": "LEFT"},
            {"name": "middle_01_L", "category": "Hand", "side": "LEFT"},
            {"name": "middle_02_L", "category": "Hand", "side": "LEFT"},
            {"name": "middle_03_L", "category": "Hand", "side": "LEFT"},
            {"name": "ring_01_L",   "category": "Hand", "side": "LEFT"},
            {"name": "ring_02_L",   "category": "Hand", "side": "LEFT"},
            {"name": "ring_03_L",   "category": "Hand", "side": "LEFT"},
            {"name": "pinky_01_L",  "category": "Hand", "side": "LEFT"},
            {"name": "pinky_02_L",  "category": "Hand", "side": "LEFT"},
            {"name": "pinky_03_L",  "category": "Hand", "side": "LEFT"},
            # Leg - 腿部
            {"name": "leg_L",  "category": "Leg",  "side": "LEFT"},
            {"name": "shin_L", "category": "Leg",  "side": "LEFT"},
            # Foot - 脚部
            {"name": "foot_L", "category": "Foot", "side": "LEFT"},
            {"name": "toe_L",  "category": "Foot", "side": "LEFT"},
        ],
    },
    {
        # Mixamo 规范：使用 Left/Right 前缀，无分隔符
        "name": "Mixamo",
        "bones": [
            # Root
            {"name": "Hips",          "category": "Root",  "side": "NONE"},
            # Spine
            {"name": "Spine",         "category": "Spine", "side": "NONE"},
            {"name": "Spine1",        "category": "Spine", "side": "NONE"},
            {"name": "Spine2",        "category": "Spine", "side": "NONE"},
            {"name": "Neck",          "category": "Spine", "side": "NONE"},
            # Head
            {"name": "Head",          "category": "Head",  "side": "NONE"},
            {"name": "LeftEye",       "category": "Head",  "side": "LEFT"},
            # Arm
            {"name": "LeftShoulder",  "category": "Arm",   "side": "LEFT"},
            {"name": "LeftArm",       "category": "Arm",   "side": "LEFT"},
            {"name": "LeftForeArm",   "category": "Arm",   "side": "LEFT"},
            # Hand
            {"name": "LeftHand",         "category": "Hand", "side": "LEFT"},
            {"name": "LeftHandThumb1",   "category": "Hand", "side": "LEFT"},
            {"name": "LeftHandThumb2",   "category": "Hand", "side": "LEFT"},
            {"name": "LeftHandThumb3",   "category": "Hand", "side": "LEFT"},
            {"name": "LeftHandIndex1",   "category": "Hand", "side": "LEFT"},
            {"name": "LeftHandIndex2",   "category": "Hand", "side": "LEFT"},
            {"name": "LeftHandIndex3",   "category": "Hand", "side": "LEFT"},
            {"name": "LeftHandMiddle1",  "category": "Hand", "side": "LEFT"},
            {"name": "LeftHandMiddle2",  "category": "Hand", "side": "LEFT"},
            {"name": "LeftHandMiddle3",  "category": "Hand", "side": "LEFT"},
            {"name": "LeftHandRing1",    "category": "Hand", "side": "LEFT"},
            {"name": "LeftHandRing2",    "category": "Hand", "side": "LEFT"},
            {"name": "LeftHandRing3",    "category": "Hand", "side": "LEFT"},
            {"name": "LeftHandPinky1",   "category": "Hand", "side": "LEFT"},
            {"name": "LeftHandPinky2",   "category": "Hand", "side": "LEFT"},
            {"name": "LeftHandPinky3",  "category": "Hand", "side": "LEFT"},
            # Leg
            {"name": "LeftUpLeg",     "category": "Leg",  "side": "LEFT"},
            {"name": "LeftLeg",       "category": "Leg",  "side": "LEFT"},
            # Foot
            {"name": "LeftFoot",      "category": "Foot", "side": "LEFT"},
            {"name": "LeftToeBase",   "category": "Foot", "side": "LEFT"},
        ],
    },
    {
        # Blender Rigify 规范：使用 .L/.R 后缀
        "name": "Rigify",
        "bones": [
            # Root
            {"name": "torso",        "category": "Root",  "side": "NONE"},
            {"name": "hips",         "category": "Root",  "side": "NONE"},
            # Spine
            {"name": "spine",        "category": "Spine", "side": "NONE"},
            {"name": "chest",        "category": "Spine", "side": "NONE"},
            {"name": "neck",         "category": "Spine", "side": "NONE"},
            # Head
            {"name": "head",         "category": "Head",  "side": "NONE"},
            # Arm
            {"name": "shoulder.L",   "category": "Arm",   "side": "LEFT"},
            {"name": "upper_arm.L",  "category": "Arm",   "side": "LEFT"},
            {"name": "forearm.L",    "category": "Arm",   "side": "LEFT"},
            # Hand
            {"name": "hand.L",       "category": "Hand",  "side": "LEFT"},
            {"name": "thumb.01.L",   "category": "Hand", "side": "LEFT"},
            {"name": "thumb.02.L",   "category": "Hand", "side": "LEFT"},
            {"name": "thumb.03.L",   "category": "Hand", "side": "LEFT"},
            {"name": "f_index.01.L", "category": "Hand", "side": "LEFT"},
            {"name": "f_index.02.L", "category": "Hand", "side": "LEFT"},
            {"name": "f_index.03.L", "category": "Hand", "side": "LEFT"},
            {"name": "f_middle.01.L","category": "Hand", "side": "LEFT"},
            {"name": "f_middle.02.L","category": "Hand", "side": "LEFT"},
            {"name": "f_middle.03.L","category": "Hand", "side": "LEFT"},
            {"name": "f_ring.01.L",  "category": "Hand", "side": "LEFT"},
            {"name": "f_ring.02.L",  "category": "Hand", "side": "LEFT"},
            {"name": "f_ring.03.L",  "category": "Hand", "side": "LEFT"},
            {"name": "f_pinky.01.L", "category": "Hand", "side": "LEFT"},
            {"name": "f_pinky.02.L", "category": "Hand", "side": "LEFT"},
            {"name": "f_pinky.03.L", "category": "Hand", "side": "LEFT"},
            # Leg
            {"name": "thigh.L",      "category": "Leg",  "side": "LEFT"},
            {"name": "shin.L",       "category": "Leg",  "side": "LEFT"},
            # Foot
            {"name": "foot.L",       "category": "Foot", "side": "LEFT"},
            {"name": "toe.L",        "category": "Foot", "side": "LEFT"},
        ],
    },
    {
        # Unreal/Maya 规范：使用 _l/_r 后缀
        "name": "Unreal",
        "bones": [
            # Root
            {"name": "root",         "category": "Root",  "side": "NONE"},
            {"name": "pelvis",       "category": "Root",  "side": "NONE"},
            # Spine
            {"name": "spine_01",     "category": "Spine", "side": "NONE"},
            {"name": "spine_02",     "category": "Spine", "side": "NONE"},
            {"name": "spine_03",     "category": "Spine", "side": "NONE"},
            {"name": "neck_01",      "category": "Spine", "side": "NONE"},
            # Head
            {"name": "head",         "category": "Head",  "side": "NONE"},
            # Arm
            {"name": "clavicle_l",   "category": "Arm",   "side": "LEFT"},
            {"name": "upperarm_l",  "category": "Arm",   "side": "LEFT"},
            {"name": "lowerarm_l",   "category": "Arm",   "side": "LEFT"},
            # Hand
            {"name": "hand_l",       "category": "Hand",  "side": "LEFT"},
            # Leg
            {"name": "thigh_l",      "category": "Leg",   "side": "LEFT"},
            {"name": "calf_l",       "category": "Leg",   "side": "LEFT"},
            # Foot
            {"name": "foot_l",       "category": "Foot",  "side": "LEFT"},
            {"name": "ball_l",       "category": "Foot",  "side": "LEFT"},
        ],
    },
]

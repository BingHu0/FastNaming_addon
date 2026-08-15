"""
自动命名插件 - 骨骼命名操作算子模块

本模块包含骨骼命名相关的全部功能：

1. 匹配工具函数（模块级）：
   - mirror_name(name): 将一侧骨骼名镜像为对侧名（_L↔_R、.L↔.R、Left↔Right、_l↔_r）
   - normalize_bone_name(name): 规范化骨骼名（去前缀/转小写/统一分隔符/提取侧别）
   - match_bone_to_convention(bone_name, convention_bones): 4 级匹配算法
   - ensure_default_conventions(addon_prefs): 首次安装时填充默认规范
   - get_convention_enum_items(self, context): 动态构建规范下拉选项
   - collect_target_bones(context): 依据当前模式收集待命名骨骼
   - apply_bone_rename(armature, current, new): 安全重命名骨骼（区分模式）

2. 操作算子：
   - BONE_OT_name_selected_bone: 模式1核心 - 重命名激活选中骨骼为指定名
   - BONE_OT_add_preset: 添加自定义预制按钮（弹窗）
   - BONE_OT_remove_preset: 删除指定索引的预制按钮
   - BONE_OT_add_convention: 创建空的新规范
   - BONE_OT_remove_convention: 删除一个规范
   - BONE_OT_import_convention: 从 JSON 文件导入规范
   - BONE_OT_auto_name_skeleton: 模式2主算子（弹规范选择窗 → 匹配 → 未匹配弹手动映射）
   - BONE_OT_manual_map_bones: 手动映射对话框
"""

# 标准库
import json
import re
import os
from typing import Optional, List, Tuple

# Blender API
import bpy
from bpy.props import StringProperty, IntProperty, EnumProperty
from bpy.types import Operator

# 插件内部
from ..config import __addon_name__
from ..preference.AddonPreferences import AutoNamingPreferences, BoneNameItem, SIDE_ENUM_ITEMS
from ..bone_data import DEFAULT_CONVENTIONS, CATEGORY_ORDER
from ....common.i18n.i18n import i18n


# ============================================================
# 一、匹配与工具函数
# ============================================================


def mirror_name(name: str) -> str:
    """
    将一侧骨骼名镜像为对侧名。

    支持的对称模式：
    - 后缀 _L ↔ _R  （如 upper_arm_L → upper_arm_R）
    - 后缀 _l ↔ _r  （如 upperarm_l → upperarm_r）
    - 后缀 .L ↔ .R  （如 upper_arm.L → upper_arm.R）
    - 后缀 .l ↔ .r  （如 upper_arm.l → upper_arm.r）
    - 前缀 Left ↔ Right （如 LeftArm → RightArm）
    - 前缀 left ↔ right
    - 单独后缀 Left ↔ Right （如 arm_Left → arm_Right）
    - 单独后缀 left ↔ right

    若名称不包含任何侧别标记，原样返回（无法镜像）。
    """
    if not name:
        return name

    # 优先级 1：Left/Right 前缀
    if name.startswith('Left'):
        return 'Right' + name[4:]
    if name.startswith('left'):
        return 'right' + name[4:]
    if name.startswith('Right'):
        return 'Left' + name[5:]
    if name.startswith('right'):
        return 'left' + name[5:]

    # 优先级 2：_L / _R / .L / .R / _l / _r 等后缀
    # 用单一正则匹配末尾的侧别标记
    m = re.search(r'([_.])([LlRr])$', name)
    if m:
        sep = m.group(1)
        side_char = m.group(2)
        # 翻转侧别字符
        flip = {'L': 'R', 'R': 'L', 'l': 'r', 'r': 'l'}[side_char]
        return name[:m.start()] + sep + flip

    # 优先级 3：以 _left / _right / _Left / _Right 结尾
    for orig, repl in [('_Left', '_Right'), ('_left', '_right'),
                       ('_Right', '_Left'), ('_right', '_left')]:
        if name.endswith(orig):
            return name[:-len(orig)] + repl

    # 优先级 4：以 Left / Right 结尾（无下划线分隔，如 handLeft）
    for orig, repl in [('Left', 'Right'), ('Right', 'Left'),
                       ('left', 'right'), ('right', 'left')]:
        if name.endswith(orig) and len(name) > len(orig):
            return name[:-len(orig)] + repl

    # 无任何侧别标记，无法镜像
    return name


# 常见前缀（Rigify/Mixamo/生成器等使用的命名前缀）
_BONE_PREFIXES = [
    'mixamorig:',     # Mixamo 默认前缀
    'mixamorig1:',
    'DEF-',           # Rigify 变形骨骼
    'DEF_',            # 变形骨骼
    'ORG-',            # Rigify 组织骨骼
    'ORG_',            # 组织骨骼
    'MCH-',            # Rigify 机制骨骼
    'MCH_',            # 机制骨骼
    'CTRL-',           # 控制骨骼
    'ctrl_',
    'c_',              # 控制简写
    'C_',              # 控制大写
    'def_',
    'org_',
    'mch_',
]

# 侧别后缀模式（用于规范化时剥离侧别）


def normalize_bone_name(name: str) -> Tuple[str, str]:
    """
    规范化骨骼名用于匹配，并提取侧别。

    处理步骤：
    1. 去除常见前缀（mixamorig:, DEF-, ORG-, ctrl_, c_ 等）
    2. 替换分隔符 .:- 为下划线 _
    3. 转小写
    4. 提取并剥离侧别后缀

    返回：(规范化后的名称, 侧别标识)
    侧别标识取值：
    - 'LEFT'：检测到左侧标记（_L, .L, _l, Left, _left）
    - 'RIGHT'：检测到右侧标记
    - 'NONE'：未检测到侧别
    """
    if not name:
        return ('', 'NONE')

    result = name

    # 1. 去除常见前缀
    for prefix in _BONE_PREFIXES:
        if result.startswith(prefix):
            result = result[len(prefix):]
            break

    # 2. 替换分隔符 . :- 为 _
    result = re.sub(r'[.:\-]', '_', result)

    # 3. 转小写
    result = result.lower()

    # 4. 提取侧别
    side = 'NONE'

    # 4.1 后缀形式 _L / .L / _l / .l
    m = re.search(r'[_.]([lr])$', result)
    if m:
        side_char = m.group(1)
        side = 'LEFT' if side_char == 'l' else 'RIGHT'
        result = result[:m.start()]

    # 4.2 前缀形式 leftxxx / rightxxx
    if side == 'NONE':
        m = re.match(r'^(left|right)(.+)$', result)
        if m:
            side = 'LEFT' if m.group(1) == 'left' else 'RIGHT'
            result = m.group(2)

    # 4.3 后缀形式 xxx_left / xxx_right / xxxleft / xxxright
    if side == 'NONE':
        m = re.search(r'[_]?(left|right)$', result)
        if m:
            side = 'LEFT' if m.group(1) == 'left' else 'RIGHT'
            result = result[:m.start()]

    # 去除首尾下划线
    result = result.strip('_')

    return (result, side)


def match_bone_to_convention(bone_name: str, convention_bones) -> Optional[Tuple[BoneNameItem, str]]:
    """
    匹配算法：在规范骨骼列表中查找最匹配的项。

    匹配优先级（从高到低）：
    1. 规范化后完全匹配（去前缀+转小写+剥离侧别后名称相等）
    2. 子串包含匹配（规范名的规范化形式是骨骼规范化名的子串，或反之）
    3. 父子层级启发式（仅 root→hips / 顶层→head，由调用方实现，本函数只做名称匹配）

    返回：
        (匹配到的 BoneNameItem, 应使用的目标名称) 元组；
        其中目标名称根据骨骼实际侧别对规范项的 name 做侧别翻转得到。
        若无匹配，返回 None。
    """
    if not bone_name or not convention_bones:
        return None

    bone_norm, bone_side = normalize_bone_name(bone_name)

    # 阶段1：完全匹配（含侧别剥离后比对）
    for item in convention_bones:
        item_norm, item_side = normalize_bone_name(item.name)
        if item_norm and item_norm == bone_norm:
            # 决定最终目标名：若骨骼在右侧而规范项定义在左侧，则镜像
            target_name = _decide_target_name(item, bone_side)
            return (item, target_name)

    # 阶段2：子串包含匹配
    best_match = None
    best_score = 0
    for item in convention_bones:
        item_norm, item_side = normalize_bone_name(item.name)
        if not item_norm:
            continue
        if item_norm in bone_norm or bone_norm in item_norm:
            # 较长的子串优先
            score = len(item_norm)
            if score > best_score:
                best_score = score
                best_match = item

    if best_match is not None:
        target_name = _decide_target_name(best_match, bone_side)
        return (best_match, target_name)

    # 阶段3：层级启发式由调用方在外部处理
    return None


def _decide_target_name(item: BoneNameItem, bone_side: str) -> str:
    """
    根据骨骼实际侧别与规范项的侧别，决定最终使用的目标名。

    规则：
    - 若规范项 side=NONE，目标名直接为 item.name
    - 若规范项 side=LEFT 且骨骼在右侧，目标名为 mirror_name(item.name)
    - 若规范项 side=RIGHT 且骨骼在左侧，目标名为 mirror_name(item.name)
    - 否则目标名为 item.name
    """
    if item.side == 'NONE' or bone_side == 'NONE':
        return item.name
    if item.side == bone_side:
        return item.name
    # 侧别不同，需要镜像
    return mirror_name(item.name)


def ensure_default_conventions(addon_prefs) -> None:
    """
    若 bone_conventions 列表为空，从 bone_data.DEFAULT_CONVENTIONS 填充默认规范。
    在面板 draw 与算子 invoke 中调用，确保用户首次使用时能看到内置规范。
    """
    if len(addon_prefs.bone_conventions) > 0:
        return

    for conv_data in DEFAULT_CONVENTIONS:
        new_conv = addon_prefs.bone_conventions.add()
        new_conv.convention_name = conv_data["name"]
        for bone_data in conv_data["bones"]:
            bone_item = new_conv.bones.add()
            bone_item.name = bone_data["name"]
            bone_item.category = bone_data["category"]
            bone_item.side = bone_data["side"]


def get_convention_enum_items(self, context):
    """
    动态构建 EnumProperty 选项列表（从 addon_prefs.bone_conventions）。
    返回 [(identifier, name, description), ...] 列表。
    identifier 使用规范的索引字符串，便于 execute 时解析。
    """
    addon_prefs = context.preferences.addons[__addon_name__].preferences
    items = []
    for i, conv in enumerate(addon_prefs.bone_conventions):
        items.append((str(i), conv.convention_name, f"使用 {conv.convention_name} 规范"))
    if not items:
        # 没有任何规范时显示占位项
        items.append(("-1", i18n("(No conventions)"), i18n("请先在偏好设置中添加规范")))
    return items


def collect_target_bones(context) -> List[Tuple[object, str]]:
    """
    依据当前模式收集待命名的骨骼。

    返回：(armature_object, bone_current_name) 元组列表
        armature_object: bpy.types.Object（类型为 ARMATURE）
        bone_current_name: 该骨骼的当前名称字符串

    模式判定：
    - OBJECT：选中 Armature 对象 → 全部 bones
    - POSE：context.selected_pose_bones（仅选中的）
    - EDIT_ARMATURE：context.selected_editable_bones（仅选中的）
    """
    armature_obj = context.active_object
    if armature_obj is None or armature_obj.type != 'ARMATURE':
        return []

    mode = context.mode  # 'OBJECT', 'POSE', 'EDIT_ARMATURE'
    bones: List[Tuple[object, str]] = []

    if mode == 'OBJECT':
        # 物体模式：处理整个 armature 的所有 bones
        for bone in armature_obj.data.bones:
            bones.append((armature_obj, bone.name))
    elif mode == 'POSE':
        # 姿态模式：仅处理选中的 pose bones
        for pbone in context.selected_pose_bones or []:
            bones.append((armature_obj, pbone.name))
    elif mode == 'EDIT_ARMATURE':
        # 编辑模式：仅处理选中的 edit bones
        for ebone in context.selected_editable_bones or []:
            bones.append((armature_obj, ebone.name))

    return bones


def apply_bone_rename(armature_obj, current_name: str, new_name: str) -> bool:
    """
    安全重命名一根骨骼。

    依据 armature 当前的模式选择正确的骨骼集合：
    - EDIT 模式：使用 armature.data.edit_bones
    - 其他模式：使用 armature.data.bones

    返回 True 表示成功重命名，False 表示未找到或失败。
    """
    if not new_name or not current_name:
        return False

    if armature_obj.mode == 'EDIT':
        bone = armature_obj.data.edit_bones.get(current_name)
    else:
        bone = armature_obj.data.bones.get(current_name)

    if bone is None:
        return False

    if bone.name == new_name:
        return True  # 已经是目标名，视为成功

    bone.name = new_name
    return True


def find_hierarchy_match(armature_obj, bone, convention_bones) -> Optional[Tuple[BoneNameItem, str]]:
    """
    层级启发式匹配（仅 3 条规则）：
    - Armature 的根骨骼（无父级）→ 规范中 category="Root" 的第一个项（优先 "hips"）
    - 沿脊柱向上最末端骨骼（无子骨骼的脊柱链顶）→ 规范中 name 含 "head" 的项
    - 其余未匹配 → 返回 None

    bone 参数在 EDIT 模式下是 EditBone，其他模式下是 Bone；两者都有 use_connect/parent 属性。
    """
    # 规则1：根骨骼
    if bone.parent is None:
        # 查找规范中名为 hips 或 category=Root 的第一个项
        for item in convention_bones:
            item_norm, _ = normalize_bone_name(item.name)
            if item_norm == 'hips':
                return (item, item.name)
        # 没有 hips 则取第一个 Root 分类的项
        for item in convention_bones:
            if item.category == 'Root':
                return (item, item.name)

    # 规则2：脊柱顶端 = 头
    # 启发式条件：无子骨骼，且父链中包含 spine/chest
    if len(bone.children) == 0 and bone.parent is not None:
        # 沿父链向上查找是否包含 spine 关键词
        ancestor = bone.parent
        is_spine_chain = False
        depth = 0
        while ancestor is not None and depth < 10:
            anc_norm, _ = normalize_bone_name(ancestor.name)
            if 'spine' in anc_norm or 'chest' in anc_norm or 'torso' in anc_norm:
                is_spine_chain = True
                break
            ancestor = ancestor.parent
            depth += 1

        if is_spine_chain:
            # 查找规范中 name 含 head 的项
            for item in convention_bones:
                item_norm, _ = normalize_bone_name(item.name)
                if item_norm == 'head':
                    return (item, item.name)

    # 无匹配
    return None


# ============================================================
# 二、操作算子
# ============================================================


class BONE_OT_name_selected_bone(Operator):
    """
    模式1核心算子：将当前激活的选中骨骼重命名为指定名称。
    被所有预制按钮复用，通过 bone_name 参数传入目标名。
    """
    '''命名选中骨骼'''
    bl_idname = "armature.name_selected_bone"
    bl_label = i18n("Name Selected Bone")
    bl_options = {'REGISTER', 'UNDO'}

    # 目标骨骼名（由按钮传入）
    bone_name: StringProperty()

    @classmethod
    def poll(cls, context):
        # 必须在 pose/edit 模式下且选中至少一根骨骼
        if context.mode not in {'POSE', 'EDIT_ARMATURE'}:
            return False
        if context.mode == 'POSE':
            return bool(context.selected_pose_bones)
        if context.mode == 'EDIT_ARMATURE':
            return bool(context.selected_editable_bones)
        return False

    def execute(self, context):
        armature_obj = context.active_object
        if armature_obj is None or armature_obj.type != 'ARMATURE':
            self.report({'WARNING'}, i18n("No active armature"))
            return {'CANCELLED'}

        # 获取激活骨骼（pose bones / edit bones 依据模式）
        if context.mode == 'POSE':
            active = context.active_pose_bone
            current_name = active.name if active else None
        elif context.mode == 'EDIT_ARMATURE':
            active = context.active_bone
            current_name = active.name if active else None
        else:
            self.report({'WARNING'}, i18n("Must be in Pose or Edit mode"))
            return {'CANCELLED'}

        if not current_name:
            self.report({'WARNING'}, i18n("No active bone selected"))
            return {'CANCELLED'}

        if not self.bone_name:
            self.report({'WARNING'}, i18n("Target bone name is empty"))
            return {'CANCELLED'}

        # 应用重命名
        if apply_bone_rename(armature_obj, current_name, self.bone_name):
            self.report({'INFO'}, i18n(f"Bone renamed to {self.bone_name}"))
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, i18n("Failed to rename bone"))
            return {'CANCELLED'}


class BONE_OT_add_preset(Operator):
    """
    添加自定义预制按钮（弹窗输入 name/category/side）。
    新条目会追加到当前激活的规范中。
    """
    '''添加骨骼预制按钮'''
    bl_idname = "armature.add_bone_preset"
    bl_label = i18n("Add Bone Preset")
    bl_options = {'REGISTER', 'UNDO'}

    # 弹窗输入的字段
    new_name: StringProperty(
        name=i18n("Bone Name"),
        description=i18n("Target bone name (e.g. head, upper_arm_L)"),
        default=""
    )
    new_category: StringProperty(
        name=i18n("Category"),
        description=i18n("Body part category (e.g. Head, Arm, Custom)"),
        default="Custom"
    )
    new_side: EnumProperty(
        name=i18n("Side"),
        description=i18n("Bone side; LEFT/RIGHT auto-mirror opposite buttons in panel"),
        items=SIDE_ENUM_ITEMS,
        default='NONE'
    )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "new_name")
        layout.prop(self, "new_category")
        layout.prop(self, "new_side")

    def execute(self, context):
        if not self.new_name:
            self.report({'WARNING'}, i18n("Bone name cannot be empty"))
            return {'CANCELLED'}

        addon_prefs = context.preferences.addons[__addon_name__].preferences
        assert isinstance(addon_prefs, AutoNamingPreferences)
        ensure_default_conventions(addon_prefs)

        # 索引越界保护
        if not (0 <= addon_prefs.active_bone_convention_index < len(addon_prefs.bone_conventions)):
            self.report({'WARNING'}, i18n("No active convention"))
            return {'CANCELLED'}

        conv = addon_prefs.bone_conventions[addon_prefs.active_bone_convention_index]
        new_item = conv.bones.add()
        new_item.name = self.new_name
        new_item.category = self.new_category
        new_item.side = self.new_side

        self.report({'INFO'}, i18n(f"Added preset: {self.new_name}"))
        return {'FINISHED'}


class BONE_OT_remove_preset(Operator):
    """删除指定索引的预制按钮"""
    '''删除骨骼预制按钮'''
    bl_idname = "armature.remove_bone_preset"
    bl_label = i18n("Remove Bone Preset")
    bl_options = {'REGISTER', 'UNDO'}

    # 要删除的骨骼项索引
    index: IntProperty()

    def execute(self, context):
        addon_prefs = context.preferences.addons[__addon_name__].preferences
        assert isinstance(addon_prefs, AutoNamingPreferences)

        if not (0 <= addon_prefs.active_bone_convention_index < len(addon_prefs.bone_conventions)):
            self.report({'WARNING'}, i18n("No active convention"))
            return {'CANCELLED'}

        conv = addon_prefs.bone_conventions[addon_prefs.active_bone_convention_index]
        if 0 <= self.index < len(conv.bones):
            conv.bones.remove(self.index)
            return {'FINISHED'}
        self.report({'WARNING'}, i18n("Invalid index"))
        return {'CANCELLED'}


class BONE_OT_add_convention(Operator):
    """创建空的新规范"""
    '''添加命名规范'''
    bl_idname = "armature.add_convention"
    bl_label = i18n("Add Convention")
    bl_options = {'REGISTER', 'UNDO'}

    convention_name: StringProperty(
        name=i18n("Convention Name"),
        description=i18n("Name for new convention"),
        default="New Convention"
    )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "convention_name")

    def execute(self, context):
        addon_prefs = context.preferences.addons[__addon_name__].preferences
        assert isinstance(addon_prefs, AutoNamingPreferences)

        new_conv = addon_prefs.bone_conventions.add()
        new_conv.convention_name = self.convention_name

        # 切换激活规范到新建项
        addon_prefs.active_bone_convention_index = len(addon_prefs.bone_conventions) - 1

        self.report({'INFO'}, i18n(f"Added convention: {self.convention_name}"))
        return {'FINISHED'}


class BONE_OT_remove_convention(Operator):
    """删除一个规范"""
    '''删除命名规范'''
    bl_idname = "armature.remove_convention"
    bl_label = i18n("Remove Convention")
    bl_options = {'REGISTER', 'UNDO'}

    index: IntProperty()

    def execute(self, context):
        addon_prefs = context.preferences.addons[__addon_name__].preferences
        assert isinstance(addon_prefs, AutoNamingPreferences)

        if 0 <= self.index < len(addon_prefs.bone_conventions):
            addon_prefs.bone_conventions.remove(self.index)
            # 修正激活索引
            if addon_prefs.active_bone_convention_index >= len(addon_prefs.bone_conventions):
                addon_prefs.active_bone_convention_index = max(0, len(addon_prefs.bone_conventions) - 1)
            return {'FINISHED'}
        self.report({'WARNING'}, i18n("Invalid index"))
        return {'CANCELLED'}


class BONE_OT_import_convention(Operator):
    """从 JSON 文件导入命名规范"""
    '''导入命名规范'''
    bl_idname = "armature.import_convention"
    bl_label = i18n("Import Convention")
    bl_options = {'REGISTER', 'UNDO'}

    # 文件浏览器选择的路径
    filepath: StringProperty(subtype='FILE_PATH')
    # 文件过滤器
    filter_glob: StringProperty(default="*.json", options={'HIDDEN'})

    def invoke(self, context, event):
        # 弹出文件浏览器
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        if not self.filepath or not os.path.exists(self.filepath):
            self.report({'WARNING'}, i18n("File not found"))
            return {'CANCELLED'}

        # 读取 JSON
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            self.report({'ERROR'}, f"JSON parse error: {e}")
            return {'CANCELLED'}

        # 校验格式
        if not isinstance(data, dict) or 'name' not in data or 'bones' not in data:
            self.report({'WARNING'}, i18n("Invalid convention JSON format"))
            return {'CANCELLED'}

        # 追加到偏好设置
        addon_prefs = context.preferences.addons[__addon_name__].preferences
        assert isinstance(addon_prefs, AutoNamingPreferences)

        new_conv = addon_prefs.bone_conventions.add()
        new_conv.convention_name = data.get('name', 'Imported Convention')

        bones_data = data.get('bones', [])
        if not isinstance(bones_data, list):
            self.report({'WARNING'}, i18n("Invalid bones list"))
            return {'CANCELLED'}

        valid_sides = {'NONE', 'LEFT', 'RIGHT'}
        for bone_data in bones_data:
            if not isinstance(bone_data, dict) or 'name' not in bone_data:
                continue
            bone_item = new_conv.bones.add()
            bone_item.name = bone_data['name']
            bone_item.category = bone_data.get('category', 'Custom')
            side = bone_data.get('side', 'NONE').upper()
            if side not in valid_sides:
                side = 'NONE'
            bone_item.side = side

        # 切换激活规范到导入项
        addon_prefs.active_bone_convention_index = len(addon_prefs.bone_conventions) - 1

        self.report({'INFO'}, i18n(f"Imported convention: {new_conv.convention_name} ({len(new_conv.bones)} bones)"))
        return {'FINISHED'}


class BONE_OT_auto_name_skeleton(Operator):
    """
    模式2主算子。

    流程：
    1. invoke: 弹出规范选择窗口（EnumProperty 动态构建自 bone_conventions）
    2. execute:
       a. 收集目标骨骼列表（依模式判定）
       b. 对每根骨骼运行 match_bone_to_convention（含层级启发式）
       c. 已匹配的立即重命名
       d. 未匹配的写入 scene.bone_manual_map_items
       e. 若有未匹配项，通过定时器延迟打开 BONE_OT_manual_map_bones 对话框
    """
    bl_idname = "armature.auto_name_skeleton"
    bl_label = i18n("One-Click Bone Naming")
    # 鼠标悬停时显示的说明（只说明按钮操作，不解释原理）
    bl_description = i18n("Auto-name bones in selected armature by chosen convention")
    bl_options = {'REGISTER', 'UNDO'}

    # 规范选择（动态 items）
    selected_convention: EnumProperty(
        name=i18n("Convention"),
        description=i18n("Choose naming convention for this operation"),
        items=get_convention_enum_items
    )

    @classmethod
    def poll(cls, context):
        # 物体模式下选中 Armature / 姿态·编辑模式下选中骨骼
        armature_obj = context.active_object
        if armature_obj is None or armature_obj.type != 'ARMATURE':
            return False
        if context.mode == 'OBJECT':
            return True
        if context.mode == 'POSE':
            return bool(context.selected_pose_bones)
        if context.mode == 'EDIT_ARMATURE':
            return bool(context.selected_editable_bones)
        return False

    def invoke(self, context, event):
        addon_prefs = context.preferences.addons[__addon_name__].preferences
        assert isinstance(addon_prefs, AutoNamingPreferences)
        ensure_default_conventions(addon_prefs)

        # 若无规范可用，直接报错
        if len(addon_prefs.bone_conventions) == 0:
            self.report({'WARNING'}, i18n("No conventions available; please add one in preferences"))
            return {'CANCELLED'}

        # 弹出规范选择对话框
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "selected_convention")
        # 显示提示信息
        layout.label(text=i18n("Unmatched bones will be opened in manual mapping dialog"))

    def execute(self, context):
        addon_prefs = context.preferences.addons[__addon_name__].preferences
        assert isinstance(addon_prefs, AutoNamingPreferences)

        # 解析规范索引
        try:
            conv_index = int(self.selected_convention)
        except (ValueError, TypeError):
            self.report({'WARNING'}, i18n("Invalid convention selection"))
            return {'CANCELLED'}

        if not (0 <= conv_index < len(addon_prefs.bone_conventions)):
            self.report({'WARNING'}, i18n("Convention not found"))
            return {'CANCELLED'}

        conv = addon_prefs.bone_conventions[conv_index]
        if len(conv.bones) == 0:
            self.report({'WARNING'}, i18n("Selected convention has no bones"))
            return {'CANCELLED'}

        # 收集目标骨骼
        target_bones = collect_target_bones(context)
        if not target_bones:
            self.report({'WARNING'}, i18n("No bones to rename"))
            return {'CANCELLED'}

        # 按骨骼所属 armature 分组处理（一般只有一个 armature，但支持多选）
        matched_count = 0
        unmatched_list = []  # [(armature_obj, current_name)]

        # 用于层级启发式：每个 armature 维护一次 bone 集合
        for armature_obj, bone_name in target_bones:
            # 名称匹配
            result = match_bone_to_convention(bone_name, conv.bones)
            # 名称未匹配则尝试层级启发式
            if result is None:
                if armature_obj.mode == 'EDIT':
                    bone = armature_obj.data.edit_bones.get(bone_name)
                else:
                    bone = armature_obj.data.bones.get(bone_name)
                if bone is not None:
                    result = find_hierarchy_match(armature_obj, bone, conv.bones)

            if result is not None:
                _, target_name = result
                if apply_bone_rename(armature_obj, bone_name, target_name):
                    matched_count += 1
                else:
                    unmatched_list.append((armature_obj, bone_name))
            else:
                unmatched_list.append((armature_obj, bone_name))

        # 处理未匹配项：写入 scene.bone_manual_map_items，并打开手动映射对话框
        scene = context.scene
        scene.bone_manual_map_items.clear()

        for armature_obj, bone_name in unmatched_list:
            item = scene.bone_manual_map_items.add()
            item.current_name = bone_name
            item.new_name = bone_name  # 默认填入当前名，便于用户在原基础上修改
            item.armature_name = armature_obj.name

        unmatched_count = len(unmatched_list)

        # 报告结果
        if unmatched_count > 0:
            self.report({'INFO'}, i18n(f"Renamed {matched_count} bones, {unmatched_count} unmatched - opening manual map dialog"))
            # 通过定时器延迟打开手动映射对话框，避免在 execute 中嵌套调用算子导致上下文问题
            def open_manual_map():
                try:
                    bpy.ops.armature.manual_map_bones('INVOKE_DEFAULT')
                except Exception as e:
                    print(f"Failed to open manual map dialog: {e}")
                return None  # 仅执行一次
            bpy.app.timers.register(open_manual_map, first_interval=0.05)
        else:
            self.report({'INFO'}, i18n(f"Renamed {matched_count} bones, no unmatched"))

        return {'FINISHED'}


class BONE_OT_manual_map_bones(Operator):
    """
    手动映射未匹配骨骼对话框。

    从 scene.bone_manual_map_items 读取未匹配骨骼列表（每条含 current_name/new_name/armature_name），
    弹窗显示每行一个原骨骼名 + 可编辑新名输入框。
    用户确认后批量应用 new_name 重命名。
    """
    '''手动映射骨骼'''
    bl_idname = "armature.manual_map_bones"
    bl_label = i18n("Manual Bone Mapping")
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        # 仅当场景中存在未匹配项时可用
        return len(context.scene.bone_manual_map_items) > 0

    def invoke(self, context, event):
        # 较宽的对话框以容纳两列
        return context.window_manager.invoke_props_dialog(self, width=500)

    def draw(self, context):
        layout = self.layout
        items = context.scene.bone_manual_map_items

        if len(items) == 0:
            layout.label(text=i18n("No unmatched bones"))
            return

        # 表头
        header = layout.row()
        header.label(text=i18n("Current Name"))
        header.label(text=i18n("New Name"))

        # 列表
        for item in items:
            row = layout.row(align=True)
            # 当前名只读展示
            row.label(text=item.current_name)
            # 新名可编辑（绑定到 CollectionProperty 项的字段）
            row.prop(item, "new_name", text="")

    def execute(self, context):
        items = context.scene.bone_manual_map_items
        applied_count = 0
        skipped_count = 0

        for item in items:
            if not item.new_name or item.new_name == item.current_name:
                skipped_count += 1
                continue

            armature_obj = bpy.data.objects.get(item.armature_name)
            if armature_obj is None or armature_obj.type != 'ARMATURE':
                skipped_count += 1
                continue

            if apply_bone_rename(armature_obj, item.current_name, item.new_name):
                applied_count += 1
            else:
                skipped_count += 1

        # 清理临时数据
        items.clear()

        self.report({'INFO'}, i18n(f"Applied {applied_count} renames, skipped {skipped_count}"))
        return {'FINISHED'}

    def cancel(self, context):
        """用户取消对话框时清理临时数据，避免残留到下次会话"""
        context.scene.bone_manual_map_items.clear()

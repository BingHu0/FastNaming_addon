"""
自动命名插件 - 骨骼命名面板模块

本模块定义骨骼命名功能在Blender界面中显示的面板：
1. BoneNamingPanel: 骨骼命名主面板（含模式1与模式2）

# 面板位置：
    3D视图 → 右侧边栏 → Fast Naming标签 → Bone Naming 面板
# 概念区分：
    - bl_category（标签页名） = "Fast Naming"            → 翻译：快速命名（容器标签，与插件名统一）
    - bl_label   （面板标题） = "Bone Naming"             → 翻译：骨骼命名（本面板自身的标题）

显示条件：
    当激活对象为 Armature（任何模式：物体/姿态/编辑）时显示

模式1：单骨骼命名
    选中一根骨骼后，点击面板上按身体部位分组的预制按钮即可对该骨骼命名。
    规范中 side=LEFT/RIGHT 的骨骼会自动镜像生成对侧按钮。

模式2：整副骨骼自动命名
    物体模式下对整个 Armature 操作；姿态/编辑模式下对选中骨骼操作。
    点击按钮后弹出规范选择窗口，未匹配骨骼自动转入手动映射对话框。
"""

import bpy

# 插件内部
from ..config import __addon_name__
from ..bone_data import CATEGORY_ORDER
from ..operators.BoneOperators import (
    ensure_default_conventions,
    mirror_name,
    BONE_OT_name_selected_bone,
    BONE_OT_add_preset,
    BONE_OT_auto_name_skeleton,
)
from .AddonPanels import BasePanel
from ..preference.AddonPreferences import AutoNamingPreferences
from ....common.i18n.i18n import i18n
from ....common.types.framework import reg_order


def _group_bones_by_category(bones_collection) -> dict:
    """
    将规范骨骼列表按 category 字段分组。
    返回 {category: [BoneNameItem, ...]} 字典。
    """
    groups = {}
    for item in bones_collection:
        cat = item.category if item.category else "Custom"
        groups.setdefault(cat, []).append(item)
    return groups


def _sorted_categories(groups: dict) -> list:
    """
    返回排序后的 category 列表：
    - 先按 CATEGORY_ORDER 中定义的顺序
    - 未在 CATEGORY_ORDER 中的 category（如用户自定义的 Custom）按字母序追加到末尾
    """
    ordered = [c for c in CATEGORY_ORDER if c in groups]
    extras = sorted([c for c in groups.keys() if c not in CATEGORY_ORDER])
    return ordered + extras


@reg_order(10)
class BoneNamingPanel(BasePanel, bpy.types.Panel):
    """
    骨骼命名面板

    继承自 BasePanel（获取公共属性：space/region/category）和 bpy.types.Panel。

    @reg_order(10) 使其注册顺序晚于 AutoNamingPanel（@reg_order(0)），
    从而在 UI 中显示在 AutoNamingPanel 下方。
    """
    bl_label = i18n("Bone Naming")
    bl_idname = "BONE_PT_one_click_object_naming"

    @classmethod
    def poll(cls, context: bpy.types.Context):
        """
        始终返回 True，让面板标题始终显示（即使用户未选中骨架）。
        具体功能内容在 draw() 中根据上下文条件决定是否渲染。
        """
        return True

    @classmethod
    def description(cls, context, panel):
        """
        鼠标悬停在面板标题上时显示的说明文字。
        支持 \\n 多行；每行通过 i18n() 单独翻译，便于维护。
        """
        return "\n".join([
            i18n("Mode 1: Select a bone, click preset buttons to name it"),
            i18n("Mode 2: Select armature, choose convention, click button"),
            i18n("Add custom presets via 'Add Preset' button"),
            i18n("Unmatched bones will open manual mapping dialog"),
        ])

    def draw(self, context: bpy.types.Context):
        """
        绘制骨骼命名面板。

        - 若激活对象不是 Armature：仅显示提示文字（让用户知道功能存在但不显示具体 UI）
        - 若激活对象是 Armature：渲染完整的模式1/模式2 功能
        """
        layout = self.layout
        obj = context.active_object

        # 条件不满足：仅显示提示信息，不显示具体功能
        if obj is None or obj.type != 'ARMATURE':
            layout.label(text=i18n("Select an armature to enable bone naming"), icon='INFO')
            layout.label(text=i18n("Mode 1: Single bone naming by preset buttons"), icon='NONE')
            layout.label(text=i18n("Mode 2: One-Click Bone Naming all bones by convention"), icon='NONE')
            return

        # 条件满足：渲染完整功能
        addon_prefs = context.preferences.addons[__addon_name__].preferences
        assert isinstance(addon_prefs, AutoNamingPreferences)
        # 首次访问时填充默认规范
        ensure_default_conventions(addon_prefs)

        scene = context.scene

        # ============================================================
        # 模式1：单骨骼命名
        # ============================================================
        layout.label(text=i18n("Mode 1: Single Bone Naming"))

        # 显示当前激活骨骼名（如果在 pose/edit 模式）
        active_bone_name = None
        if context.mode == 'POSE' and context.active_pose_bone:
            active_bone_name = context.active_pose_bone.name
        elif context.mode == 'EDIT_ARMATURE' and context.active_bone:
            active_bone_name = context.active_bone.name

        if active_bone_name:
            layout.label(text=i18n("Active: ") + active_bone_name, icon='BONE_DATA')
        elif context.mode == 'OBJECT':
            layout.label(text=i18n("Switch to Pose/Edit mode to name single bone"), icon='INFO')

        # 规范选择下拉（决定预制按钮来源）
        if len(addon_prefs.bone_conventions) == 0:
            layout.label(text=i18n("No conventions; please add one in preferences"), icon='ERROR')
        else:
            # 修正越界索引
            idx = addon_prefs._active_index()
            if idx < 0 or idx >= len(addon_prefs.bone_conventions):
                addon_prefs.active_bone_convention_index = "0"
                idx = 0
            # 渲染为下拉框（EnumProperty 自动显示规范名称）
            layout.prop(addon_prefs, "active_bone_convention_index", text=i18n("Convention"))

            current_conv = addon_prefs.bone_conventions[idx]

            # 按部位分组渲染预制按钮
            groups = _group_bones_by_category(current_conv.bones)
            sorted_cats = _sorted_categories(groups)

            for category in sorted_cats:
                # 折叠 box：用 Scene 上的 bone_expand_<Category> BoolProperty 存展开状态
                expand_prop_name = f"bone_expand_{category}"
                # 防御：预定义部位已在 __init__.py 中注册 BoolProperty；
                # 用户自定义的 category（如 "MyCustom"）没有对应 Scene 属性，默认始终展开
                has_expand_prop = hasattr(scene, expand_prop_name)
                expanded = getattr(scene, expand_prop_name, True) if has_expand_prop else True

                box = layout.box()
                header_row = box.row()
                # 折叠头：仅对预定义部位渲染折叠按钮；自定义部位渲染一个圆点占位
                if has_expand_prop:
                    header_row.prop(
                        scene, expand_prop_name,
                        icon_only=True, emboss=False,
                        icon='DISCLOSURE_TRI_DOWN' if expanded else 'DISCLOSURE_TRI_RIGHT'
                    )
                else:
                    header_row.label(text="", icon='DOT')
                header_row.label(text=i18n(category))

                if expanded:
                    # 用 grid_flow 自动换行布局预制按钮
                    flow = box.grid_flow(row_major=True, columns=2, align=True)
                    for item in groups[category]:
                        # 始终渲染原按钮
                        op = flow.operator(
                            BONE_OT_name_selected_bone.bl_idname,
                            text=item.name, icon='BONE_DATA'
                        )
                        op.bone_name = item.name
                        # 若 side != NONE，额外渲染镜像按钮
                        if item.side != 'NONE':
                            mirrored = mirror_name(item.name)
                            # 仅当镜像后名称不同时才渲染（避免重复按钮）
                            if mirrored != item.name:
                                op_m = flow.operator(
                                    BONE_OT_name_selected_bone.bl_idname,
                                    text=mirrored, icon='BONE_DATA'
                                )
                                op_m.bone_name = mirrored

            # 添加自定义预制按钮
            layout.separator()
            layout.operator(BONE_OT_add_preset.bl_idname, text=i18n("Add Preset"), icon='ADD')

        # ============================================================
        # 模式2：整副骨骼自动命名
        # ============================================================
        layout.separator()
        layout.label(text=i18n("Mode 2: One-Click Bone Naming"))

        # 模式提示
        if context.mode == 'OBJECT':
            layout.label(text=i18n("Will rename ALL bones in selected armature"), icon='INFO')
        elif context.mode == 'POSE':
            layout.label(text=i18n("Will rename SELECTED pose bones only"), icon='INFO')
        elif context.mode == 'EDIT_ARMATURE':
            layout.label(text=i18n("Will rename SELECTED edit bones only"), icon='INFO')

        # 自动命名按钮（依据模式显示不同图标）
        if context.mode == 'OBJECT':
            icon = 'ARMATURE_DATA'
        else:
            icon = 'GROUP_BONE'
        layout.operator(BONE_OT_auto_name_skeleton.bl_idname, text=i18n("One-Click Bone Naming"), icon=icon)

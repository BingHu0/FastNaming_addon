"""
快速命名插件 - UI面板模块

本模块定义插件在Blender界面中显示的面板：
1. BasePanel: 基础面板类（抽象类），定义公共属性
2. AutoNamingPanel: 自动命名功能面板

Blender 面板开发核心概念：
- Panel: 面板类，继承自bpy.types.Panel
- bl_space_type: 面板显示的空间（VIEW_3D表示3D视图）
- bl_region_type: 面板显示的区域（UI表示右侧边栏）
- bl_category: 面板所在的标签页名称（Fast Naming，中文翻译为「快速命名」）
- bl_label: 面板标题（One-Click Object Naming，与标签页名不同）
- bl_idname: 面板唯一标识符
- draw方法: 定义面板的UI内容
- poll方法: 决定面板是否显示
"""

import bpy

from ..config import __addon_name__
from ..operators.AddonOperators import (
    BatchRenameOperator,
    ApplyAsDefaultOperator,
    InsertVariableOperator,
    ClearTemplateOperator,
    AddCustomVariablePanelOperator,
)
from ....common.i18n.i18n import i18n
from ....common.types.framework import reg_order

# 内置名称片段列表（内部key, 双语按钮文本i18n key, 单独说明i18n key）
BUILTIN_VARIABLES = [
    ("num",  "{num} - Sequence",       "num_desc"),
    ("type", "{type} - Object Type",   "type_desc"),
    ("name", "{name} - Original Name", "name_desc"),
    ("date", "{date} - Date",          "date_desc"),
    ("time", "{time} - Time",          "time_desc"),
]

# 间隔符列表（按钮显示文本i18n key, 实际插入的字面量字符）
SEPARATORS = [
    ("Underscore _", "_"),
    ("Hyphen -",     "-"),
    ("Space",        " "),
]


class BasePanel(object):
    """
    基础面板类 - 抽象类

    定义所有面板共有的属性：
    - bl_space_type: 在3D视图中显示
    - bl_region_type: 在右侧边栏显示
    - bl_category: 在"Fast Naming"标签页中显示（中文翻译为「快速命名」）
    """
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = i18n("Fast Naming")

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return True


@reg_order(0)
class AutoNamingPanel(BasePanel, bpy.types.Panel):
    """
    自动命名功能面板

    继承自BasePanel（获取公共属性）和bpy.types.Panel（获取面板功能）。

    @reg_order(0) 装饰器：
    - 用于控制面板的注册顺序
    - 数值越小，面板显示越靠前

    用户看到的位置：
        3D视图 → 右侧边栏 → Fast Naming标签页 → One-Click Object Naming面板
    """
    bl_label = i18n("One-Click Object Naming")
    bl_idname = "SCENE_PT_auto_naming"

    @classmethod
    def description(cls, context, panel):
        return "\n".join([
            i18n("1. Select objects to rename"),
            i18n("2. Click name snippet buttons to build template"),
            i18n("3. Click 'Apply' to rename"),
            i18n("Or enable auto-naming for newly created objects in preferences"),
        ])

    def draw(self, context: bpy.types.Context):
        addon_prefs = context.preferences.addons[__addon_name__].preferences
        scene = context.scene
        layout = self.layout

        # ================================================================
        # 第一部分：命名模板展示 + 名称片段按钮
        # ================================================================
        layout.label(text=i18n("Naming Template"))

        # 模板显示框（可手动微调）
        template_box = layout.box()
        template_box.prop(scene, "temp_naming_template", text="")

        # 清空按钮
        row_clear = layout.row()
        row_clear.operator(ClearTemplateOperator.bl_idname, text=i18n("Clear Template"), icon='X')

        layout.separator()

        # ================================================================
        # 二级菜单：内置名称片段（外层盒子 + 台头）
        # ================================================================
        builtin_box = layout.box()
        builtin_box.label(text=i18n("Built-in Name Snippets:"))

        for var_key, var_label_key, var_desc_key in BUILTIN_VARIABLES:
            row = builtin_box.row(align=True)
            split = row.split(factor=0.4)
            # 左列：按钮
            col_left = split.column(align=True)
            op = col_left.operator(
                InsertVariableOperator.bl_idname,
                text=i18n(var_label_key),
                icon='PRESET'
            )
            op.variable_name = var_key
            # 右列：单独说明
            col_right = split.column(align=True)
            col_right.label(text=i18n(var_desc_key))

        # ================================================================
        # 三级菜单：间隔符（在内置名称片段盒子里再嵌一个小盒子 + 台头）
        # ================================================================
        sep_box = builtin_box.box()
        sep_box.label(text=i18n("Separator:"))
        sep_row = sep_box.row(align=True)
        for label_key, literal in SEPARATORS:
            op = sep_row.operator(
                InsertVariableOperator.bl_idname,
                text=i18n(label_key),
                icon='TRACKING'
            )
            op.variable_name = ""
            op.literal = literal

        # ================================================================
        # {name} 临时片段输入框：模板中每个 {name} 对应一个输入框
        # 注意：draw() 是只读方法，绝不在这里 add()/remove()，否则触发重绘中断造成UI消失
        # 集合大小同步放在 InsertVariableOperator / ClearTemplateOperator 中完成
        # ================================================================
        name_count = scene.temp_naming_template.count("{name}")
        if name_count > 0:
            name_box = layout.box()
            name_box.label(text=i18n("Temporary Name Snippet"), icon='INFO')
            for i in range(name_count):
                if i < len(scene.temp_name_snippets):
                    name_box.prop(scene.temp_name_snippets[i], "value",
                                  text=i18n("Name Snippet Value") + f" {i + 1}")
            name_box.label(text=i18n("Lost after Blender restart"), icon='NONE')

        layout.separator()

        # ================================================================
        # 自定义名称片段按钮
        # ================================================================
        if addon_prefs.custom_variables:
            layout.label(text=i18n("Custom Name Snippets:"))
            custom_grid = layout.grid_flow(row_major=True, columns=3, align=True)
            for var in addon_prefs.custom_variables:
                if var.name:
                    op = custom_grid.operator(
                        InsertVariableOperator.bl_idname,
                        text="{" + var.name + "}",
                        icon='PRESET'
                    )
                    op.variable_name = var.name

        # 添加自定义名称片段按钮
        layout.separator()
        row_add = layout.row(align=True)
        row_add.operator(
            AddCustomVariablePanelOperator.bl_idname,
            text=i18n("Add Custom Name Snippet"),
            icon='ADD'
        )

        # 起始序号和序号位数
        row = layout.row()
        row.prop(scene, "temp_start_number")
        row.prop(scene, "temp_number_padding")

        layout.separator()

        # ================================================================
        # 第二部分：默认设置
        # ================================================================
        layout.label(text=i18n("Default Settings"))
        layout.prop(addon_prefs, "auto_naming_enabled", text=i18n("Enable One-Click Object Naming on Create"))

        layout.separator()

        # ================================================================
        # 第三部分：操作按钮
        # ================================================================
        row = layout.row(align=True)
        row.operator(BatchRenameOperator.bl_idname, text=i18n("Batch Rename"), icon='FILE_TEXT')
        row.operator(ApplyAsDefaultOperator.bl_idname, text=i18n("Apply as Default"), icon='SETTINGS')

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return True

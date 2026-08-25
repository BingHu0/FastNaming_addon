"""
自动命名插件 - 偏好设置模块

本模块定义插件的偏好设置类：
1. CustomVariableItem: 自定义变量项（PropertyGroup）
2. BoneNameItem: 单根骨骼命名项（PropertyGroup）
3. BoneConvention: 一套命名规范（PropertyGroup，内含骨骼列表）
4. ManualMapItem: 模式2未匹配骨骼的手动映射项（PropertyGroup）
5. AutoNamingPreferences: 插件偏好设置类（AddonPreferences）

Blender 偏好设置开发核心概念：
- AddonPreferences: 插件偏好设置基类，继承自bpy.types.AddonPreferences
- PropertyGroup: 属性组，用于定义可重复的属性集合
- 嵌套 CollectionProperty: PropertyGroup 内可以包含另一个 PropertyGroup 的集合
- bl_idname: 必须设置为插件的包名，用于标识偏好设置属于哪个插件
- draw方法: 定义偏好设置面板的UI布局
"""

# 导入 Blender Python API
import bpy
# 导入属性类型定义
from bpy.props import StringProperty, IntProperty, BoolProperty, EnumProperty, CollectionProperty
# 导入类型定义
from bpy.types import AddonPreferences, PropertyGroup

# 导入插件配置
from ..config import __addon_name__
# 导入国际化翻译函数
from ....common.i18n.i18n import i18n


def _get_convention_enum_items(self, context):
    """
    模块级回调函数：为 active_bone_convention_index EnumProperty 动态生成选项。
    Blender EnumProperty 的 items 参数接受 (self, context) -> list 形式的可调用对象。
    此处 self 即 AutoNamingPreferences 实例，可直接访问 self.bone_conventions。
    """
    items = []
    for i, conv in enumerate(self.bone_conventions):
        items.append((str(i), conv.convention_name, f"使用 {conv.convention_name} 规范"))
    if not items:
        items.append(("-1", i18n("(No conventions)"), i18n("请先在偏好设置中添加规范")))
    return items


class CustomVariableItem(PropertyGroup):
    """
    自定义名称片段项 - PropertyGroup

    PropertyGroup 是 Blender 中用于定义可重复属性集合的类。
    在这里用于存储用户自定义的名称片段名称和值。

    使用方法：
        在偏好设置中添加多个自定义名称片段，每个片段包含name和value两个属性。
    """

    # 片段名称（不含花括号）
    name: StringProperty(
        name=i18n("Snippet Name"),
        description=i18n("Custom snippet name (without braces, e.g. my_var)"),
        default="custom_var"
    )

    # 片段值
    value: StringProperty(
        name=i18n("Snippet Value"),
        description=i18n("Value to replace this snippet with"),
        default=""
    )


# 侧别枚举项（用于骨骼命名）
# 三元组格式: (内部值, 显示名, 描述)
SIDE_ENUM_ITEMS = [
    ('NONE',  i18n("None"),  i18n("Center bone (no left/right distinction)")),
    ('LEFT',  i18n("Left"),  i18n("Left-side bone (auto-mirror right button in panel)")),
    ('RIGHT', i18n("Right"), i18n("Right-side bone (auto-mirror left button in panel)")),
]


class BoneNameItem(PropertyGroup):
    """
    单根骨骼命名项 - PropertyGroup

    存储一个骨骼的目标命名信息，作为命名规范集合中的一个条目。

    字段说明：
    - name: 骨骼的目标名称（如 "head"、"upper_arm_L"）
    - category: 身体部位分类（如 "Head"、"Arm"），用于面板分组
    - side: 侧别（NONE/LEFT/RIGHT），决定面板是否镜像生成对侧按钮
    """

    # 骨骼的目标名称
    name: StringProperty(
        name=i18n("Bone Name"),
        description=i18n("Target bone name"),
        default=""
    )

    # 身体部位分类（用于面板分组渲染）
    category: StringProperty(
        name=i18n("Category"),
        description=i18n("Body part category (e.g. Head, Arm), used for panel grouping"),
        default="Custom"
    )

    # 侧别
    side: EnumProperty(
        name=i18n("Side"),
        description=i18n("Bone side; LEFT/RIGHT auto-mirror opposite buttons in panel"),
        items=SIDE_ENUM_ITEMS,
        default='NONE'
    )


class BoneConvention(PropertyGroup):
    """
    命名规范 - PropertyGroup

    一套完整的命名规范，包含规范名与一组骨骼项。

    嵌套集合示例：
        convention.convention_name = "Generic Short"
        convention.bones[0].name = "hips"
        convention.bones[0].category = "Root"
        convention.bones[0].side = 'NONE'
    """

    # 规范名称（如 "Generic Short"、"Mixamo"）
    convention_name: StringProperty(
        name=i18n("Convention Name"),
        description=i18n("Display name for this naming convention"),
        default="New Convention"
    )

    # 规范包含的骨骼项集合（嵌套 CollectionProperty）
    bones: CollectionProperty(
        type=BoneNameItem,
        name=i18n("Bones")
    )

    # 当前激活的骨骼项索引（用于偏好设置 UI 列表）
    active_bone_index: IntProperty(
        name=i18n("Active Bone Index"),
        description=i18n("Currently active bone item index in preferences panel"),
        default=0
    )


class TempNameSnippetItem(PropertyGroup):
    """
    临时名称片段项 - PropertyGroup

    用于存储模板中每个 {name} 占位符对应的临时覆盖值。
    挂在 Scene 上，会话级保存，重启 Blender 后失效。

    字段说明：
    - value: 用户为该 {name} 填入的临时片段值
    """

    value: StringProperty(
        name=i18n("Name Snippet Value"),
        description=i18n("Temporary override for {name}; lost on restart"),
        default=""
    )


class ManualMapItem(PropertyGroup):
    """
    手动映射项 - PropertyGroup

    模式2中未匹配骨骼的临时记录项，挂在 Scene 上用于在手动映射对话框中传递数据。

    字段说明：
    - current_name: 原骨骼名（只读展示）
    - new_name: 用户在弹窗中输入的新名称
    - armature_name: 所属 Armature 对象名（用于在 execute 中定位骨骼）
    """

    current_name: StringProperty(
        name=i18n("Current Name"),
        description=i18n("Original name of unmatched bone"),
        default=""
    )

    new_name: StringProperty(
        name=i18n("New Name"),
        description=i18n("User-specified new name for this bone"),
        default=""
    )

    armature_name: StringProperty(
        name=i18n("Armature"),
        description=i18n("Name of the Armature object containing this bone"),
        default=""
    )


class AutoNamingPreferences(AddonPreferences):
    """
    插件偏好设置类 - AddonPreferences

    继承自bpy.types.AddonPreferences，定义插件的全局配置选项。

    关键概念：
        - bl_idname: 必须设置为插件的包名（__addon_name__）
        - 属性定义: 使用bpy.props中的类型定义配置项
        - draw方法: 绘制偏好设置面板的UI

    用户打开方式：
        编辑 → 偏好设置 → 插件 → 找到本插件 → 点击齿轮图标 → 偏好设置
    """

    # 必须设置为插件包名，否则Blender无法识别这是哪个插件的偏好设置
    bl_idname = __addon_name__

    """
    以下是插件的配置属性定义

    Blender属性类型：
    - StringProperty: 字符串属性
    - IntProperty: 整数属性
    - BoolProperty: 布尔属性（开关）
    - CollectionProperty: 集合属性（可包含多个项）

    每个属性的参数：
    - name: 显示名称（用户看到的标签）
    - description: 描述（鼠标悬停时显示的提示）
    - default: 默认值
    - min/max: 数值属性的范围限制
    """

    # 命名模板 - 用户定义的命名格式
    naming_template: StringProperty(
        name=i18n("Naming Template"),
        description=i18n("Default naming template with variables like {num}, {type}, {name}, {date}, {time}"),
        default="{type}_{num}"
    )

    # 起始序号 - 序号从哪个数字开始
    start_number: IntProperty(
        name=i18n("Start Number"),
        description=i18n("Starting number for auto-numbering"),
        default=1,
        min=0,
        max=999999
    )

    # 序号位数 - 数字填充位数
    number_padding: IntProperty(
        name=i18n("Number Padding"),
        description=i18n("Digit count for number padding (0 = no padding)"),
        default=3,
        min=0,
        max=10
    )

    # 自动命名开关 - 是否启用创建对象时自动命名
    auto_naming_enabled: BoolProperty(
        name=i18n("One-Click Object Naming Enabled"),
        description=i18n("Auto-name objects on creation"),
        default=False
    )

    # 自定义名称片段列表 - 用户添加的自定义名称片段
    custom_variables: CollectionProperty(
        type=CustomVariableItem,
        name=i18n("Custom Name Snippets")
    )

    # 骨骼命名规范集合 - 用户可用的一组命名规范
    bone_conventions: CollectionProperty(
        type=BoneConvention,
        name=i18n("Bone Conventions")
    )

    # 当前激活的命名规范索引（面板下拉选择）
    # 使用 EnumProperty 以显示规范名称而非数字编号
    active_bone_convention_index: EnumProperty(
        name=i18n("Active Convention"),
        description=i18n("Currently selected naming convention"),
        items=_get_convention_enum_items,
        default=None
    )

    def _active_index(self) -> int:
        """便捷方法：返回当前激活规范的整数索引"""
        try:
            val = self.active_bone_convention_index
            if val is None:
                return 0
            return int(val)
        except (ValueError, TypeError):
            return 0

    def draw(self, context: bpy.types.Context):
        """
        draw方法 - 绘制偏好设置面板的UI

        使用bpy.types.UILayout来构建界面布局：
        - layout.label(): 添加文本标签
        - layout.prop(): 添加属性控件（如输入框、开关、滑块等）
        - layout.row(): 创建水平行
        - layout.box(): 创建带边框的容器
        - layout.separator(): 添加分隔线
        - layout.operator(): 添加操作按钮
        """
        # 获取布局对象
        layout = self.layout

        # === 一键命名物体功能新增翻译 ===
        # 第一部分：基本设置
        layout.label(text=i18n("One-Click Object Naming Settings"))
        # 自动命名开关
        layout.prop(self, "auto_naming_enabled")
        # 命名模板输入框
        layout.prop(self, "naming_template")
        # 起始序号和序号位数放在同一行
        row = layout.row()
        row.prop(self, "start_number")
        row.prop(self, "number_padding")

        # 添加分隔线
        layout.separator()

        # 第二部分：自定义名称片段
        layout.label(text=i18n("Custom Name Snippets:"))
        # 遍历所有自定义名称片段，逐个显示
        for i, item in enumerate(self.custom_variables):
            # 使用box容器包裹每个片段
            box = layout.box()
            row = box.row()
            # 显示片段名称输入框
            row.prop(item, "name")
            # 显示片段值输入框
            row.prop(item, "value")
            # 添加删除按钮，传入索引参数
            row.operator("preferences.remove_custom_variable", text="", icon='X').index = i

        # 添加自定义名称片段按钮
        layout.operator("preferences.add_custom_variable", text=i18n("Add Custom Name Snippet"))

        # 添加分隔线
        layout.separator()

        # 第三部分：骨骼命名规范管理
        layout.label(text=i18n("Bone Conventions"))

        # 规范列表（每行一个规范，可编辑名称 + 删除按钮）
        for i, conv in enumerate(self.bone_conventions):
            box = layout.box()
            row = box.row()
            # 规范名称编辑框
            row.prop(conv, "convention_name", text="")
            # 删除规范按钮
            row.operator("armature.remove_convention", text="", icon='X').index = i

            # 仅对当前激活规范显示其骨骼列表
            if str(i) == self.active_bone_convention_index:
                # 遍历规范内所有骨骼项
                for j, bone in enumerate(conv.bones):
                    bone_row = box.row()
                    bone_row.prop(bone, "name", text="")
                    bone_row.prop(bone, "category", text="")
                    bone_row.prop(bone, "side", text="")
                    # 删除骨骼项按钮
                    bone_row.operator("armature.remove_bone_preset", text="", icon='X').index = j

                # 添加骨骼项按钮
                box.operator("armature.add_bone_preset", text=i18n("Add Bone"), icon='ADD')

        # 添加规范 + 导入 JSON + 导出 JSON 按钮放同一行
        row = layout.row(align=True)
        row.operator("armature.add_convention", text=i18n("Add Convention"), icon='ADD')
        row.operator("armature.import_convention", text=i18n("Import Convention"), icon='IMPORT')
        row.operator("armature.export_convention", text=i18n("Export Convention"), icon='EXPORT')

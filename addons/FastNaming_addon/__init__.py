import bpy

from .config import __addon_name__
from .i18n.dictionary import dictionary
from ...common.class_loader import auto_load
from ...common.class_loader.auto_load import add_properties, remove_properties
from ...common.i18n.dictionary import common_dictionary
from ...common.i18n.i18n import i18n, load_dictionary

# 必须在导入其他模块（触发类定义）之前加载字典，
# 否则类定义中的 i18n() 调用（如 bl_description、bl_label、Property 的 name/description）
# 会使用空的 __dictionary__，返回英文原文并被永久固化为类属性。
load_dictionary(dictionary)

from .operators.AddonOperators import register_auto_naming_handler, unregister_auto_naming_handler
# 引入 ManualMapItem 用于 Scene 上的 bone_manual_map_items 集合
from .preference.AddonPreferences import ManualMapItem
# 引入 TempNameSnippetItem 用于 Scene 上的 temp_name_snippets 集合
from .preference.AddonPreferences import TempNameSnippetItem

bl_info = {
    "name": "Fast Naming",
    "author": "BING",
    "blender": (5, 2, 0),
    "version": (0, 0, 3),
    "description": "这个是一个自动命名插件，用于快速命名对象和骨骼。",
    "warning": "此插件未进行过系统测试，可能存在一些未知问题。",
    "doc_url": "[documentation url]",
    "tracker_url": "3317877311@qq.com",
    "support": "COMMUNITY",
    "category": "Object"
}

_addon_properties = {
    bpy.types.Scene: {
        "temp_naming_template": bpy.props.StringProperty(
            name=i18n("Temporary Naming Template"),
            description=i18n("Temporary naming template for this session"),
            default=""
        ),
        "temp_name_snippets": bpy.props.CollectionProperty(
            type=TempNameSnippetItem,
            name=i18n("Temporary Name Snippets")
        ),
        "temp_start_number": bpy.props.IntProperty(
            name=i18n("Start Number"),
            description=i18n("Starting number for the {num} variable"),
            default=1,
            min=0,
            max=999999
        ),
        "temp_number_padding": bpy.props.IntProperty(
            name=i18n("Number Padding"),
            description=i18n("Digit count for {num} padding (0 for no padding, 3 for 001)"),
            default=3,
            min=0,
            max=10
        ),
        # ============================================================
        # 骨骼命名功能 - Scene 临时属性
        # ============================================================
        # 模式1 面板分组的折叠展开状态（每个 category 一个 BoolProperty）
        "bone_expand_Root":  bpy.props.BoolProperty(default=True),
        "bone_expand_Spine": bpy.props.BoolProperty(default=True),
        "bone_expand_Head":  bpy.props.BoolProperty(default=True),
        "bone_expand_Arm":   bpy.props.BoolProperty(default=True),
        "bone_expand_Hand":  bpy.props.BoolProperty(default=False),
        "bone_expand_Leg":   bpy.props.BoolProperty(default=True),
        "bone_expand_Foot":  bpy.props.BoolProperty(default=False),
        # 模式2 未匹配骨骼的临时映射列表（用于手动映射对话框传递数据）
        "bone_manual_map_items": bpy.props.CollectionProperty(type=ManualMapItem),
        # 导出规范对话框的临时选中状态（位掩码，跨两次 execute 调用持久化）
        "temp_export_mask": bpy.props.IntProperty(default=0),
    },
}


def register():
    auto_load.init()
    auto_load.register()
    add_properties(_addon_properties)

    load_dictionary(dictionary)
    bpy.app.translations.register(__addon_name__, common_dictionary)

    register_auto_naming_handler()

    print("{} addon is installed.".format(__addon_name__))


def unregister():
    bpy.app.translations.unregister(__addon_name__)
    unregister_auto_naming_handler()
    auto_load.unregister()
    remove_properties(_addon_properties)
    print("{} addon is uninstalled.".format(__addon_name__))
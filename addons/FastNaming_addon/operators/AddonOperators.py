"""
自动命名插件 - 操作算子模块

本模块包含：
1. NamingTool: 命名工具类，负责变量解析、模板处理、序号生成
2. 各种操作算子(Operator): 用户在界面上点击的按钮功能
3. 自动命名监听器: 监听场景变化，自动为新创建的对象命名

Blender 插件开发核心概念：
- Operator: 操作算子，对应界面上的按钮，用户点击后执行特定操作
- Handler: 事件监听器，在特定事件发生时自动触发
- @persistent: 装饰器，使handler在加载新文件后仍然保持活跃
"""

# 导入正则表达式模块，用于解析模板中的变量
import re
# 导入日期时间模块，用于生成日期和时间变量
from datetime import datetime

# 导入Blender Python API
import bpy
# 导入持久化装饰器，用于handler
from bpy.app.handlers import persistent

# 导入插件配置和偏好设置
from ..config import __addon_name__
from ..preference.AddonPreferences import AutoNamingPreferences
# 导入国际化翻译函数
from ....common.i18n.i18n import i18n


class NamingTool:
    """
    命名工具类 - 提供自动命名所需的核心功能
    
    包含三个静态方法：
    1. get_variable_values: 获取所有可用变量的值
    2. parse_template: 解析命名模板，替换变量为实际值
    3. get_next_number: 获取下一个可用的序号
    """

    @staticmethod # 静态方法，无需实例化即可调用
    def get_variable_values(obj=None, num=1, addon_prefs=None, scene=None):
        """
        获取所有命名变量的值

        参数：
            obj: Blender对象，用于获取对象相关信息
            num: 当前序号
            addon_prefs: 插件偏好设置，包含自定义名称片段和序号位数设置
            scene: 当前场景（用于读取 {name} 临时覆盖值）

        返回：
            字典，包含所有变量名和对应的值
        """
        values = {}

        # 获取对象相关变量
        if obj:
            # {name} - 对象原名称（{name} 的多实例临时覆盖在 parse_template 中逐个处理）
            values['name'] = obj.name
            # {type} - 对象类型（首字母大写）
            if hasattr(obj, 'type'):
                values['type'] = obj.type.capitalize()
            elif hasattr(obj.data, 'type'):
                values['type'] = obj.data.type.capitalize()
            else:
                values['type'] = 'Object'
        else:
            # 如果没有对象，使用默认值
            values['name'] = 'Unknown'
            values['type'] = 'Object'

        # 获取日期时间变量
        now = datetime.now()
        values['date'] = now.strftime('%Y-%m-%d')  # {date} - 当前日期
        values['time'] = now.strftime('%H-%M-%S')  # {time} - 当前时间

        # 处理序号变量和自定义变量
        if addon_prefs:
            # 获取序号位数设置
            padding = addon_prefs.number_padding
            if padding > 0:
                # 如果设置了位数，用0填充（如 001, 002）
                values['num'] = str(num).zfill(padding)
            else:
                # 否则直接使用数字（如 1, 2）
                values['num'] = str(num)

            # 添加用户自定义变量
            for var in addon_prefs.custom_variables:
                if var.name:
                    values[var.name] = var.value
        else:
            # 如果没有偏好设置，直接使用数字
            values['num'] = str(num)

        return values

    @staticmethod
    def parse_template(template, obj=None, num=1, addon_prefs=None, scene=None):
        """
        解析命名模板，将变量替换为实际值

        参数：
            template: 命名模板字符串，如 "{type}_{num}"
            obj: Blender对象
            num: 当前序号
            addon_prefs: 插件偏好设置
            scene: 当前场景（用于 {name} 临时覆盖值）

        返回：
            解析后的名称字符串
        """
        # 如果模板为空，返回默认名称
        if not template:
            return "Untitled"

        # 获取所有变量的值
        values = NamingTool.get_variable_values(obj, num, addon_prefs, scene)
        result = template

        # {name} 特殊处理：逐个替换每个 {name} 占位符
        # 当模板中有多个 {name} 时，每个使用 temp_name_snippets 中对应的临时覆盖值
        if scene and hasattr(scene, 'temp_name_snippets'):
            snippets = scene.temp_name_snippets
            name_count = result.count('{name}')
            for i in range(name_count):
                if i < len(snippets) and snippets[i].value:
                    replacement = snippets[i].value
                elif obj:
                    replacement = obj.name
                else:
                    replacement = 'Unknown'
                result = result.replace('{name}', replacement, 1)  # 每次只替换第一个
        else:
            # 无 scene 时，所有 {name} 统一使用对象原名
            name_value = obj.name if obj else 'Unknown'
            result = result.replace('{name}', name_value)

        # 从 values 中移除 'name'，避免下方通用替换再次处理
        values.pop('name', None)

        # 将模板中的 {变量名} 替换为实际值
        for key, value in values.items():
            placeholder = '{' + key + '}'
            result = result.replace(placeholder, value)

        # 清理未定义的变量（移除未替换的 {xxx}）
        remaining_vars = re.findall(r'\{(\w+)\}', result)
        for var in remaining_vars:
            result = result.replace('{' + var + '}', '')

        # 去除首尾空格
        return result.strip()

    @staticmethod
    def get_next_number(template, start_number=1):
        """
        获取下一个可用的序号
        
        参数：
            template: 命名模板，检查是否包含 {num} 变量
            start_number: 起始序号
        
        返回：
            下一个可用的序号（不与现有对象名称冲突）
        """
        used_numbers = set()
        # 检查模板中是否包含序号变量
        pattern = re.compile(r'\{num\}')
        has_num = pattern.search(template)

        # 如果模板中没有序号变量，直接返回起始序号
        if not has_num:
            return start_number

        # 遍历所有对象，收集已使用的序号
        for obj in bpy.data.objects:
            # 匹配名称末尾的数字（如 Cube_001 中的 001）
            match = re.search(r'_(\d+)$', obj.name)
            if match:
                used_numbers.add(int(match.group(1)))

        # 找到第一个未使用的序号
        num = start_number
        while num in used_numbers:
            num += 1

        return num


class BatchRenameOperator(bpy.types.Operator):
    """
    批量重命名操作算子

    Blender Operator 是插件中最常用的交互方式，用户点击按钮后执行。
    bl_idname: 操作的唯一标识符，格式为 "category.name"
    bl_label: 界面上显示的标签名称
    bl_description: 鼠标悬停时显示的说明（只说明按钮操作，不解释原理）
    bl_options: 操作选项，REGISTER表示在信息面板显示，UNDO表示支持撤销
    """
    bl_idname = "object.batch_rename"
    bl_label = i18n("Batch Rename")
    # 鼠标悬停时显示的说明（只说明按钮操作，不解释原理）
    bl_description = i18n("Rename all selected objects using current template")
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        """
        poll方法 - 决定操作是否可用

        如果返回True，按钮会被启用；返回False，按钮变灰不可点击。
        这里要求至少选中一个对象。
        """
        return len(context.selected_objects) > 0

    def execute(self, context: bpy.types.Context):
        """
        execute方法 - 操作的核心逻辑

        优先使用场景中的临时模板（用户通过按钮插入的），
        如为空则回退到偏好设置中的默认模板。
        """
        addon_prefs = bpy.context.preferences.addons[__addon_name__].preferences
        assert isinstance(addon_prefs, AutoNamingPreferences)

        scene = context.scene
        # 优先使用场景中的临时模板，回退到偏好设置默认模板
        template = scene.temp_naming_template if scene.temp_naming_template else addon_prefs.naming_template
        selected_objects = context.selected_objects

        if not template:
            self.report({'WARNING'}, i18n("Naming template is empty"))
            return {'CANCELLED'}

        start_num = addon_prefs.start_number
        num = NamingTool.get_next_number(template, start_num)

        for i, obj in enumerate(selected_objects):
            new_name = NamingTool.parse_template(template, obj, num + i, addon_prefs, scene)
            if new_name:
                obj.name = new_name

        self.report({'INFO'}, i18n(f"Renamed {len(selected_objects)} objects"))
        return {'FINISHED'}


class InsertVariableOperator(bpy.types.Operator):
    """
    插入名称片段到命名模板操作算子

    用户点击名称片段按钮时，将对应占位符（如 {num}）追加到
    场景的临时命名模板中。
    """
    bl_idname = "object.insert_variable"
    bl_label = i18n("Insert Name Snippet")
    bl_description = i18n("Insert a name snippet placeholder into the naming template")
    bl_options = {'REGISTER'}

    # 要插入的名称片段名（不含花括号），如 "num", "type", "custom_var"
    variable_name: bpy.props.StringProperty(
        name=i18n("Snippet Name"),
        description=i18n("Snippet name to insert (without braces)"),
        default=""
    )

    def execute(self, context: bpy.types.Context):
        scene = context.scene
        var_placeholder = "{" + self.variable_name + "}"
        current = scene.temp_naming_template
        scene.temp_naming_template = current + var_placeholder

        # 如果插入的是 {name}，同步调整 temp_name_snippets 集合大小
        if self.variable_name == 'name':
            name_count = scene.temp_naming_template.count("{name}")
            while len(scene.temp_name_snippets) < name_count:
                scene.temp_name_snippets.add()
            while len(scene.temp_name_snippets) > name_count:
                scene.temp_name_snippets.remove(len(scene.temp_name_snippets) - 1)

        return {'FINISHED'}


class ClearTemplateOperator(bpy.types.Operator):
    """
    清空命名模板操作算子
    """
    bl_idname = "object.clear_template"
    bl_label = i18n("Clear Template")
    bl_description = i18n("Clear the current naming template")
    bl_options = {'REGISTER'}

    def execute(self, context: bpy.types.Context):
        scene = context.scene
        scene.temp_naming_template = ""
        # 同步清空所有临时名称片段
        scene.temp_name_snippets.clear()
        return {'FINISHED'}


class AddCustomVariablePanelOperator(bpy.types.Operator):
    """
    从面板添加自定义名称片段操作算子

    使用 invoke_props_dialog 弹出对话框，
    让用户输入片段名和值，然后添加到偏好设置的自定义名称片段列表中。
    """
    bl_idname = "object.add_custom_variable_panel"
    bl_label = i18n("Add Custom Name Snippet")
    bl_description = i18n("Add a custom name snippet from the panel")
    bl_options = {'REGISTER'}

    new_name: bpy.props.StringProperty(
        name=i18n("Snippet Name"),
        description=i18n("Custom snippet name (without braces, e.g. my_var)"),
        default=""
    )

    new_value: bpy.props.StringProperty(
        name=i18n("Snippet Value"),
        description=i18n("Value to replace this snippet with"),
        default=""
    )

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "new_name")
        layout.prop(self, "new_value")

    def execute(self, context: bpy.types.Context):
        if not self.new_name:
            self.report({'WARNING'}, i18n("Snippet name cannot be empty"))
            return {'CANCELLED'}

        addon_prefs = context.preferences.addons[__addon_name__].preferences
        assert isinstance(addon_prefs, AutoNamingPreferences)

        item = addon_prefs.custom_variables.add()
        item.name = self.new_name
        item.value = self.new_value

        self.report({'INFO'}, i18n(f"Custom name snippet '{self.new_name}' added"))
        return {'FINISHED'}


class AddCustomVariableOperator(bpy.types.Operator):
    """
    添加自定义名称片段操作算子

    在偏好设置中添加一个新的自定义名称片段。
    """
    '''添加自定义名称片段'''
    bl_idname = "preferences.add_custom_variable"
    bl_label = i18n("Add Custom Name Snippet")

    def execute(self, context: bpy.types.Context):
        """执行添加自定义变量"""
        addon_prefs = context.preferences.addons[__addon_name__].preferences
        assert isinstance(addon_prefs, AutoNamingPreferences)
        # 在自定义变量列表中添加一个新项
        addon_prefs.custom_variables.add()
        return {'FINISHED'}


class RemoveCustomVariableOperator(bpy.types.Operator):
    """
    删除自定义名称片段操作算子

    从偏好设置中删除指定索引的自定义名称片段。
    """
    '''删除自定义名称片段'''
    bl_idname = "preferences.remove_custom_variable"
    bl_label = i18n("Remove Custom Name Snippet")

    # 要删除的变量索引
    index: bpy.props.IntProperty()

    def execute(self, context: bpy.types.Context):
        """执行删除自定义变量"""
        addon_prefs = context.preferences.addons[__addon_name__].preferences
        assert isinstance(addon_prefs, AutoNamingPreferences)
        # 根据索引删除变量
        addon_prefs.custom_variables.remove(self.index)
        return {'FINISHED'}


class ApplyAsDefaultOperator(bpy.types.Operator):
    """
    应用为默认设置操作算子
    
    将面板中的临时设置保存为偏好设置中的默认值。
    """
    '''将当前设置应用为默认值'''
    bl_idname = "preferences.apply_as_default"
    bl_label = i18n("Apply as Default")

    def execute(self, context: bpy.types.Context):
        """执行应用为默认设置"""
        addon_prefs = context.preferences.addons[__addon_name__].preferences
        assert isinstance(addon_prefs, AutoNamingPreferences)

        # 获取场景中的临时设置
        scene = context.scene
        if hasattr(scene, 'temp_naming_template'):
            addon_prefs.naming_template = scene.temp_naming_template
        if hasattr(scene, 'temp_start_number'):
            addon_prefs.start_number = scene.temp_start_number
        if hasattr(scene, 'temp_number_padding'):
            addon_prefs.number_padding = scene.temp_number_padding

        self.report({'INFO'}, i18n("Settings applied as default"))
        return {'FINISHED'}


# 全局变量，用于自动命名功能
auto_naming_handler = None      # handler注册后的引用
_tracked_objects = set()        # 已跟踪的对象名称集合（用于检测新对象）
_initialized = False            # 是否已经初始化（首次运行时需要扫描现有对象）
_pending_renames = []           # 待重命名队列（延迟执行重命名）


def delayed_rename():
    """
    延迟重命名函数
    
    为什么需要延迟执行？
    在depsgraph_update_post handler执行期间，Blender处于特殊状态，
    对象的name属性是只读的，不能直接修改。
    
    解决方案：
    1. 在handler中收集需要重命名的对象和新名称
    2. 使用bpy.app.timers.register()注册一个定时器
    3. 定时器在handler执行完毕后运行，可以正常修改对象名称
    
    返回None表示定时器只执行一次，返回数字表示再次执行的间隔。
    """
    global _pending_renames

    # 如果没有待重命名的对象，直接返回
    if not _pending_renames:
        return None

    # 复制待重命名列表并清空（防止重复处理）
    pending = _pending_renames[:]
    _pending_renames.clear()

    # 遍历待重命名的对象
    for obj_name, new_name in pending:
        # 通过名称查找对象（因为对象可能在延迟期间被删除）
        obj = bpy.data.objects.get(obj_name)
        if obj and new_name and new_name != obj.name:
            obj.name = new_name

    # 返回None表示定时器执行完毕后不再重复
    return None


@persistent
def scene_update_handler(scene, depsgraph):
    """
    场景更新事件监听器
    
    Blender事件处理机制：
    - depsgraph_update_post: 在依赖图更新后触发
    - 这是检测对象创建的常用方式（因为没有专门的object_created事件）
    
    参数：
        scene: 当前场景对象
        depsgraph: 依赖图，包含本次更新的所有变更信息
    
    @persistent装饰器的作用：
    - 默认情况下，handler在加载新文件时会被自动移除
    - 添加@persistent后，handler会在加载新文件后仍然保持活跃
    """
    global _initialized, _pending_renames

    # 检查插件是否已安装
    addon_prefs = bpy.context.preferences.addons.get(__addon_name__)
    if not addon_prefs:
        return

    # 获取偏好设置
    prefs = addon_prefs.preferences
    assert isinstance(prefs, AutoNamingPreferences)

    # 如果未启用自动命名，直接返回
    if not prefs.auto_naming_enabled:
        return

    # 初始化阶段：首次运行时扫描所有现有对象
    if not _initialized:
        for obj in scene.objects:
            _tracked_objects.add(obj.name)
        _initialized = True
        return

    # 获取命名模板
    template = prefs.naming_template
    if not template:
        return

    # 方式1：通过depsgraph.updates检测新增对象
    new_objects = []
    for update in depsgraph.updates:
        # 检查更新的是否是对象
        if isinstance(update.id, bpy.types.Object):
            obj = update.id
            # 检查是否是新对象（不在已跟踪列表中）
            if obj.name not in _tracked_objects:
                new_objects.append(obj)

    # 方式2：备用方案，如果depsgraph方式没检测到，直接比较对象列表
    if not new_objects:
        current_objects = set(scene.objects.keys())
        new_object_names = current_objects - _tracked_objects
        for obj_name in sorted(new_object_names):
            obj = scene.objects.get(obj_name)
            if obj:
                new_objects.append(obj)

    # 如果找到了新对象，准备重命名
    if new_objects:
        # 获取下一个可用序号
        num = NamingTool.get_next_number(template, prefs.start_number)
        # 遍历新对象，生成新名称
        for obj in sorted(new_objects, key=lambda o: o.name):
            new_name = NamingTool.parse_template(template, obj, num, prefs, scene)
            if new_name and new_name != obj.name:
                # 将重命名任务加入队列（不直接执行）
                _pending_renames.append((obj.name, new_name))
            num += 1

        # 如果有待执行的重命名，注册定时器延迟执行
        if _pending_renames:
            # first_interval=0.01 表示0.01秒后执行
            bpy.app.timers.register(delayed_rename, first_interval=0.01)

    # 更新已跟踪对象列表
    current_objects = set(scene.objects.keys())
    _tracked_objects.clear()
    _tracked_objects.update(current_objects)


def register_auto_naming_handler():
    """
    注册自动命名监听器
    
    在插件启用时调用，将scene_update_handler添加到depsgraph_update_post列表中。
    """
    global auto_naming_handler, _initialized
    if auto_naming_handler is None:
        _initialized = False
        _tracked_objects.clear()
        _pending_renames.clear()
        # 将handler添加到事件列表
        auto_naming_handler = bpy.app.handlers.depsgraph_update_post.append(scene_update_handler)


def unregister_auto_naming_handler():
    """
    注销自动命名监听器
    
    在插件禁用时调用，从depsgraph_update_post列表中移除handler。
    """
    global auto_naming_handler, _initialized
    if auto_naming_handler is not None:
        # 从事件列表中移除handler
        bpy.app.handlers.depsgraph_update_post.remove(scene_update_handler)
        auto_naming_handler = None
    _initialized = False
    _tracked_objects.clear()
    _pending_renames.clear()
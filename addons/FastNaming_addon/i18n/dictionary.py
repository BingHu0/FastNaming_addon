from FastNaming_addon.common.i18n.dictionary import preprocess_dictionary

dictionary = {
    "zh_CN": {
        # === 快速命名插件翻译 ===
        # bl_category：侧边栏标签页名称（英文 Fast Naming，中文翻译为「快速命名」）
        ("*", "Fast Naming"): "快速命名",
        # bl_label：面板标题（保持不变）
        ("*", "One-Click Object Naming"): "物体一键命名",

        # === 名称片段相关翻译（术语：变量 → 名称片段） ===
        # 面板 section label
        ("*", "Built-in Name Snippets:"): "内置名称片段:",
        ("*", "Custom Name Snippets:"): "自定义名称片段:",
        ("*", "Custom Name Snippets"): "自定义名称片段",
        # 按钮
        ("*", "Add Custom Name Snippet"): "添加自定义名称片段",
        ("*", "Remove Custom Name Snippet"): "删除自定义名称片段",
        ("*", "Insert Name Snippet"): "插入名称片段",
        ("*", "Clear Template"): "清空模板",
        # 属性字段
        ("*", "Snippet Name"): "片段名称",
        ("*", "Snippet Value"): "片段值",
        ("*", "Name Snippet Value"): "片段值",
        # 属性/算子悬停说明
        ("*", "Insert a name snippet placeholder into the naming template"): "向命名模板插入一个名称片段占位符",
        ("*", "Clear the current naming template"): "清空当前命名模板",
        ("*", "Add a custom name snippet from the panel"): "从面板添加自定义名称片段",
        ("*", "Snippet name to insert (without braces)"): "要插入的片段名（不含花括号）",
        ("*", "Snippet name cannot be empty"): "片段名不能为空",
        ("*", "Custom snippet name (without braces, e.g. my_var)"): "自定义片段名（不含花括号，如 my_var）",
        ("*", "Value to replace this snippet with"): "该片段要替换的值",
        ("*", "Click variable buttons to build template"): "2. 点击名称片段按钮构建模板",
        ("*", "2. Click name snippet buttons to build template"): "2. 点击名称片段按钮构建模板",

        # 内置名称片段按钮双语显示
        ("*", "{num} - Sequence"): "序号{num}",
        ("*", "{type} - Object Type"): "对象类型{type}",
        ("*", "{name} - Original Name"): "原名称{name}",
        ("*", "{date} - Date"): "日期{date}",
        ("*", "{time} - Time"): "时间{time}",

        # 内置名称片段单独说明
        ("*", "num_desc"): "自动递增序号，如 001、002，受起始序号与位数控制",
        ("*", "type_desc"): "对象类型，如 Mesh=网格、Light=灯光、Camera=摄像机",
        ("*", "name_desc"): "对象原名或下方临时片段；点击后可在下方展开输入临时覆盖值",
        ("*", "date_desc"): "当前日期，格式 YYYY-MM-DD，如 2026-08-15",
        ("*", "time_desc"): "当前时间，格式 HH-MM-SS，如 14-30-55",

        # {name} 临时片段输入框
        ("*", "Temporary Name Snippet"): "临时名称片段",
        ("*", "Temporary Name Snippets"): "临时名称片段",
        ("*", "Temporary override for {name}; lost on restart"): "{name} 的临时覆盖值；重启后失效",
        ("*", "Lost after Blender restart"): "重启 Blender 后失效",

        # === 通用属性翻译 ===
        ("*", "Temporary Settings"): "临时设置",
        ("*", "Temporary Naming Template"): "临时命名模板",
        ("*", "Start Number"): "起始序号",
        ("*", "Number Padding"): "序号位数",
        ("*", "Temporary naming template for this session"): "本次会话的临时命名模板",
        ("*", "Starting number for the {num} variable"): "{num} 变量的起始序号",
        ("*", "Digit count for {num} padding (0 for no padding, 3 for 001)"): "{num} 的填充位数（0 不填充，3 → 001）",
        ("*", "Default Settings"): "默认设置",
        ("*", "Enable Auto Naming on Create"): "创建对象时自动命名",
        ("Operator", "Batch Rename"): "批量重命名",
        ("Operator", "Apply as Default"): "设为默认",
        ("*", "Naming Template"): "命名模板",
        ("*", "Auto Naming Enabled"): "启用自动命名",
        ("*", "Naming template is empty"): "命名模板为空",
        ("*", "Settings applied as default"): "设置已应用为默认",
        ("*", "Enable One-Click Object Naming on Create"): "创建对象时一键命名物体",

        # === 骨骼命名功能翻译 ===
        # 面板标题与分区
        ("*", "Bone Naming"): "骨骼命名",
        ("*", "Mode 1: Single Bone Naming"): "模式1：单骨骼命名",
        ("*", "Mode 2: One-Click Bone Naming"): "模式2：骨骼一键命名",
        ("*", "Active: "): "当前骨骼：",
        ("*", "Switch to Pose/Edit mode to name single bone"): "请切换到姿态/编辑模式以使用单骨骼命名",
        ("*", "No conventions; please add one in preferences"): "无可用规范；请在偏好设置中添加一个",
        ("*", "Convention"): "命名规范",
        ("*", "Add Preset"): "添加预制按钮",
        ("*", "Will rename ALL bones in selected armature"): "将重命名所选骨架的全部骨骼",
        ("*", "Will rename SELECTED pose bones only"): "仅重命名选中的姿态骨骼",
        ("*", "Will rename SELECTED edit bones only"): "仅重命名选中的编辑骨骼",
        ("*", "Unmatched bones will be opened in manual mapping dialog"): "未匹配的骨骼将弹出手动映射对话框",

        # 面板悬停说明（description 方法）- Bone Naming
        ("*", "Mode 1: Select a bone, click preset buttons to name it"): "模式1：选中一根骨骼，点击预制按钮即可命名",
        ("*", "Mode 2: Select armature, choose convention, click button"): "模式2：选中骨架，选择规范，点击按钮一键命名",
        ("*", "Add custom presets via 'Add Preset' button"): "通过「添加预制按钮」添加自定义命名",
        ("*", "Unmatched bones will open manual mapping dialog"): "未匹配的骨骼将打开手动映射对话框",
        # 不满足条件时面板内的提示文字
        ("*", "Select an armature to enable bone naming"): "请选中一个骨架以启用骨骼命名",
        ("*", "Mode 1: Single bone naming by preset buttons"): "模式1：通过预制按钮命名单个骨骼",
        ("*", "Mode 2: One-Click Bone Naming all bones by convention"): "模式2：按规范一键命名所有骨骼",

        # 面板悬停说明（description 方法）- One-Click Object Naming
        ("*", "1. Select objects to rename"): "1. 选择要重命名的对象",
        ("*", "2. Set template using {num}/{type}/{name}/{date}/{time}"): "2. 设置模板（可用变量 {num}/{type}/{name}/{date}/{time}）",
        ("*", "3. Click 'Apply' to rename"): "3. 点击「应用」按钮重命名",
        ("*", "Or enable auto-naming for newly created objects in preferences"): "或在偏好设置中开启「创建对象时自动命名」",

        # 算子标签
        ("Operator", "Name Selected Bone"): "命名选中骨骼",
        ("Operator", "Add Bone Preset"): "添加骨骼预制按钮",
        ("Operator", "Remove Bone Preset"): "删除骨骼预制按钮",
        ("Operator", "Add Convention"): "添加命名规范",
        ("Operator", "Remove Convention"): "删除命名规范",
        ("Operator", "Import Convention"): "导入命名规范",
        ("Operator", "One-Click Bone Naming"): "骨骼一键命名",
        ("Operator", "Manual Bone Mapping"): "手动骨骼映射",
        # 算子悬停说明（bl_description）
        ("Operator", "Rename all selected objects using current template"): "使用当前模板重命名所有选中对象",
        ("Operator", "Auto-name bones in selected armature by chosen convention"): "按所选规范自动命名选中骨架中的所有骨骼",

        # 属性字段标签
        ("*", "Bone Name"): "骨骼名称",
        ("*", "Category"): "部位",
        # 属性悬停说明（description）- 骨骼命名相关
        ("*", "Target bone name (e.g. head, upper_arm_L)"): "骨骼的目标命名（如 head、upper_arm_L）",
        ("*", "Body part category (e.g. Head, Arm, Custom)"): "身体部位分类（如 Head、Arm、Custom）",
        ("*", "Bone side; LEFT/RIGHT auto-mirror opposite buttons in panel"): "骨骼侧别；LEFT/RIGHT 会在面板自动镜像生成对侧按钮",
        ("*", "Name for new convention"): "新规范的名称",
        ("*", "Choose naming convention for this operation"): "选择本次命名使用的命名规范",
        # 属性悬停说明（description）- 偏好设置相关
        ("*", "Custom variable name (without braces, e.g. my_var)"): "自定义变量名称（不含花括号，如 my_var）",
        ("*", "Value to replace this variable with"): "该变量要替换的值",
        ("*", "Center bone (no left/right distinction)"): "中线骨骼（不区分左右）",
        ("*", "Left-side bone (auto-mirror right button in panel)"): "左侧骨骼（渲染时自动镜像生成右侧按钮）",
        ("*", "Right-side bone (auto-mirror left button in panel)"): "右侧骨骼（渲染时自动镜像生成左侧按钮）",
        ("*", "Target bone name"): "骨骼的目标命名",
        ("*", "Body part category (e.g. Head, Arm), used for panel grouping"): "身体部位分类（如 Head、Arm），用于面板分组显示",
        ("*", "Display name for this naming convention"): "命名规范的显示名称",
        ("*", "Currently active bone item index in preferences panel"): "偏好设置面板中当前激活的骨骼项索引",
        ("*", "Original name of unmatched bone"): "未匹配骨骼的原始名称",
        ("*", "User-specified new name for this bone"): "用户为该骨骼指定的新名称",
        ("*", "Name of the Armature object containing this bone"): "该骨骼所属的 Armature 对象名",
        ("*", "Default naming template with variables like {num}, {type}, {name}, {date}, {time}"): "默认命名模板，支持变量如 {num}, {type}, {name}, {date}, {time}",
        ("*", "Starting number for auto-numbering"): "自动编号的起始数字",
        ("*", "Digit count for number padding (0 = no padding)"): "序号的数字位数（0表示不填充）",
        ("*", "Auto-name objects on creation"): "创建对象时自动命名",
        ("*", "Index of the currently selected convention in bone naming panel"): "当前在骨骼命名面板中选中的命名规范索引",
        ("*", "Side"): "侧别",
        ("*", "None"): "无",
        ("*", "Left"): "左",
        ("*", "Right"): "右",
        ("*", "Convention Name"): "规范名称",
        ("*", "Bones"): "骨骼列表",
        ("*", "Active Bone Index"): "激活骨骼索引",
        ("*", "Bone Conventions"): "骨骼命名规范",
        ("*", "Active Convention"): "当前规范",
        ("*", "Add Bone"): "添加骨骼",
        ("*", "Current Name"): "当前名称",
        ("*", "New Name"): "新名称",
        ("*", "Armature"): "骨架",

        # 身体部位分组
        ("*", "Root"): "根与胯部",
        ("*", "Spine"): "脊柱",
        ("*", "Head"): "头部",
        ("*", "Arm"): "手臂",
        ("*", "Hand"): "手部",
        ("*", "Leg"): "腿部",
        ("*", "Foot"): "脚部",
        ("*", "Custom"): "自定义",

        # 报告消息（静态部分；含变量的动态消息回退为英文）
        ("*", "No active armature"): "未激活骨架",
        ("*", "Must be in Pose or Edit mode"): "必须在姿态或编辑模式下",
        ("*", "No active bone selected"): "未选中激活骨骼",
        ("*", "Target bone name is empty"): "目标骨骼名为空",
        ("*", "Failed to rename bone"): "骨骼重命名失败",
        ("*", "Bone name cannot be empty"): "骨骼名不能为空",
        ("*", "No active convention"): "无激活规范",
        ("*", "Invalid index"): "无效索引",
        ("*", "File not found"): "文件未找到",
        ("*", "Invalid convention JSON format"): "无效的规范 JSON 格式",
        ("*", "Invalid bones list"): "无效的骨骼列表",
        ("*", "No conventions available; please add one in preferences"): "无可用规范；请在偏好设置中添加一个",
        ("*", "Invalid convention selection"): "无效的规范选择",
        ("*", "Convention not found"): "规范未找到",
        ("*", "Selected convention has no bones"): "所选规范没有骨骼",
        ("*", "No bones to rename"): "没有可命名的骨骼",
        ("*", "No unmatched bones"): "无未匹配骨骼",
    }
}

dictionary = preprocess_dictionary(dictionary)

dictionary["zh_HANS"] = dictionary["zh_CN"]
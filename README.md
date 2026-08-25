# Fast Naming

> 一个用于 Blender 的**自动命名插件**，帮助你在 3D 视图侧边栏里**快速、批量地命名对象与骨骼**。
> A Blender add-on for quickly and consistently naming objects and armature bones.

- 中文界面 / English UI（内置简体中文翻译，随 Blender 语言自动切换）
- 插件版本 / Add-on Version：**0.0.3**
- 支持 Blender：**5.2.0+**（最低支持 5.2.0，未进行更低版本测试）
- 许可证 / License：GPL-3.0-or-later

---

## 功能特性 / Features

插件在 **3D 视图 → 右侧边栏（按 `N`）→ “Fast Naming / 快速命名” 标签页** 下提供两个面板：

### 1. 物体一键命名（One-Click Object Naming）

用“命名模板 + 变量”的方式批量重命名选中的物体，并支持创建物体时自动命名。

- **命名模板**：由变量占位符拼成，例如 `{type}_{num}`。面板里点按钮即可插入片段，也可手动微调。
- **内置名称片段**：`{num}`、`{type}`、`{name}`、`{date}`、`{time}`。
- **自定义名称片段**：在偏好设置或面板里添加自己的 `{变量}`（如 `{material}`），重命名时会被替换成你设的值。
- **`{name}` 临时覆盖**：模板里每出现一个 `{name}`，面板会展开一个输入框让你临时填值；该值仅本次会话有效，重启 Blender 后失效。
- **序号控制**：可设置起始序号（Start Number）与位数（Number Padding，`0`=不补零，`3`=`001`）。
- **批量重命名（Batch Rename）**：用当前模板重命名所有选中对象；序号自动从“已有对象中未占用的最小数字”开始。
- **设为默认（Apply as Default）**：把当前面板里的模板/序号设置保存为偏好设置默认值。
- **创建时自动命名**：在偏好设置中开启后，新创建的对象会按默认模板自动命名（实验性，详见下方“备注”）。

### 2. 骨骼命名（Bone Naming）

针对 Armature，提供两种模式，并内置多套常用命名规范。

- **模式 1 · 单骨骼命名**：选中骨架并进入 **姿态 / 编辑模式**，选中一根骨骼，在面板里按身体部位（Root / Spine / Head / Arm / Hand / Leg / Foot）分组点击预制按钮即可命名。标注了 `LEFT` 的骨骼会**在面板自动镜像出右侧按钮**。
- **模式 2 · 骨骼一键命名**：
  - **物体模式**选中骨架 → 点击“骨骼一键命名”→ 选择一套规范 → 自动按名称匹配并重命名**全部**骨骼；
  - **姿态 / 编辑模式** → 仅对**选中**的骨骼重命名。
  - 匹配不上的骨骼会弹出**手动映射对话框**，逐根输入新名。
- **内置命名规范（4 套）**，开箱即用：
  | 规范 | 后缀风格 | 示例 |
  |---|---|---|
  | Generic Short | `_L` / `_R` | `upper_arm_L`, `head` |
  | Mixamo | `Left` / `Right` 前缀 | `LeftArm`, `Head` |
  | Rigify | `.L` / `.R` | `upper_arm.L`, `head` |
  | Unreal | `_l` / `_r` | `upperarm_l`, `root` |
- **自定义规范**：在偏好设置里 **Add Convention / Add Bone** 增删，或 **Import Convention** 从 JSON 文件导入（见下方格式）。
- **匹配算法**：① 规范化后完全匹配（去前缀、转小写、剥离侧别）→ ② 子串包含匹配 → ③ 层级启发式（根骨骼→hips、脊柱顶端→head）。左右侧会自动镜像处理。

---

## 安装 / Installation

1. 点击[Releases（版本发布）](https://github.com/BingHu0/FastNaming_addon/releases)下载`FastNaming_addon.zip`。
2. Blender → **编辑 (Edit) → 偏好设置 (Preferences) → 插件 (Add-ons) → 安装 (Install…)**。
3. 选择`FastNaming_addon.zip`，安装后勾选启用 **Fast Naming**。
4. 侧边栏（按`N`）出现 “Fast Naming / 快速命名” 标签页即成功。

> **扩展方式（Blender 5.2+）**：也可通过 **Edit → Preferences → Extensions → Install from Disk** 选择本仓库根目录（含 `blender_manifest.toml`）安装。扩展清单 `id` 已正确设为 `FastNaming_addon`。

---

## 使用说明 / Usage

### 物体命名

1. 在 3D 视图选中要重命名的对象。
2. 打开侧边栏 `N` → **Fast Naming / 快速命名** → **One-Click Object Naming / 物体一键命名**。
3. 点击名称片段按钮（如 `{type}`、`{num}`）拼出模板，或直接在模板框里输入，例如 `Prop_{name}_{num}`。
4. 若用到 `{name}`，在展开的“临时名称片段”输入框里填写覆盖值。
5. 点 **Batch Rename / 批量重命名** 完成。

想让以后新建的物体自动套用模板：打开插件偏好设置，开启 **Enable One-Click Object Naming on Create / 创建对象时一键命名物体**，并设置默认模板与序号。

### 骨骼命名

1. 选中骨架对象，进入 **姿态模式** 或 **编辑模式**。
2. 侧边栏 → **Fast Naming / 快速命名** → **Bone Naming / 骨骼命名**。
3. **模式 1（单骨骼）**：选中一根骨骼，在对应部位分组下点预制按钮（如 `upper_arm_L`）；左侧骨骼会自动出现 `upper_arm_R` 镜像按钮。也可用 **Add Preset** 增加自定义按钮。
4. **模式 2（一键命名）**：切到**物体模式**选中骨架 → 点 **One-Click Bone Naming / 骨骼一键命名** → 选择规范（Generic Short / Mixamo / Rigify / Unreal）→ 确认。未匹配的骨骼会弹出手动映射对话框，逐根输入新名后确认。

### 变量速查

| 变量 | 含义 | 示例 |
|---|---|---|
| `{num}` | 自动递增序号，受起始序号与位数控制 | `001`, `002`（位数=3） |
| `{type}` | 对象类型，首字母大写 | `Mesh`, `Light`, `Camera` |
| `{name}` | 对象原名；可在面板临时覆盖 | `Cube`（或你填的值） |
| `{date}` | 当前日期 `YYYY-MM-DD` | `2026-08-15` |
| `{time}` | 当前时间 `HH-MM-SS` | `14-30-55` |
| `{自定义名}` | 你在偏好设置/面板添加的自定义片段 | 由你定义 |

> 模板中出现的**未定义** `{变量}` 会被自动清空（例如写错变量名）。

### 命名规范 JSON 格式（Import Convention）

```json
{
  "name": "My Convention",
  "bones": [
    { "name": "hips",     "category": "Root",  "side": "NONE" },
    { "name": "head",     "category": "Head",  "side": "NONE" },
    { "name": "upper_arm_L", "category": "Arm", "side": "LEFT" }
  ]
}
```

- `category`：用于面板分组（`Root`/`Spine`/`Head`/`Arm`/`Hand`/`Leg`/`Foot`/`Custom`）。
- `side`：`NONE` / `LEFT` / `RIGHT`；`LEFT`/`RIGHT` 会在面板自动镜像出对侧按钮。

---

## 偏好设置 / Preferences

**编辑 → 偏好设置 → 插件 → Fast Naming → 齿轮图标（Preferences）**

- One-Click Object Naming Settings：默认模板、起始序号、位数、是否创建时自动命名。
- Custom Name Snippets：管理自定义名称片段。
- Bone Conventions：管理骨骼命名规范（增删规范、增删骨骼项、导入 JSON）。

---

## 目录结构 / Project Structure

```
FastNaming_addon/
├── __init__.py                 # 入口，注册/注销插件（传统插件模式）
├── blender_manifest.toml       # 扩展清单（id = FastNaming_addon，Blender 扩展方式安装用）
├── addons/
│   ├── __init__.py
│   └── FastNaming_addon/       # 插件主体
│       ├── __init__.py         # 注册逻辑 + Scene 临时属性
│       ├── config.py           # 插件包名
│       ├── bone_data.py        # 内置命名规范种子数据
│       ├── operators/          # 操作算子（重命名、插入变量、自动命名监听器…）
│       ├── panels/             # UI 面板（物体命名 / 骨骼命名）
│       ├── preference/         # 偏好设置与 PropertyGroup
│       └── i18n/              # 翻译字典（zh_CN）
└── common/                     # 通用框架：类自动加载、i18n、类型
```

---

## 国际化 / i18n

内置**简体中文（zh_CN）**翻译。Blender 语言设为简体中文时界面自动切换；默认显示英文。翻译集中在 `addons/FastNaming_addon/i18n/dictionary.py`。

---

## 备注 / Remarks
此插件未进行过系统测试，可能存在一些未知问题。

---

## 许可证 / License

GPL-3.0-or-later。

## 联系 / Contact

如有反馈与建议欢迎投递到邮箱：3317877311@qq.com。也欢迎在仓库提交 Issue。

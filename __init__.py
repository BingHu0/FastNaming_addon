from .addons.FastNaming_addon import register as addon_register, unregister as addon_unregister

bl_info = {
    "name": 'Fast Naming',
    "author": 'BING',
    "blender": (5, 2, 0),
    "version": (0, 0, 2),
    "description": '这个是一个自动命名插件，用于快速命名对象和骨骼。',
    "warning": '此插件未进行过系统测试，可能存在一些未知问题。',
    "doc_url": '[documentation url]',
    "tracker_url": '3317877311@qq.com',
    "support": 'COMMUNITY',
    "category": 'Object'
}

def register():
    addon_register()

def unregister():
    addon_unregister()

    
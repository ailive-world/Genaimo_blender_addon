bl_info = {
    "name": "Genaimo Blender tools",
    "author": "AiLIVE Co., Ltd.",
    "version": (1, 0),
    "blender": (3, 6, 0),
    "location": "3DView Port > Object",
    "description": "genaimo blender addon.",
    "website": "https://genaimo.ailive.world/",
    "category": "Object",
}


if "bpy" in locals():
    import importlib
    if "genaimo_addon" in locals():
        importlib.reload(genaimo_addon)
    else:
        from . import genaimo_addon
else:
    import bpy
    from . import genaimo_addon

def register():
    genaimo_addon.register()

def unregister():
    genaimo_addon.unregister()
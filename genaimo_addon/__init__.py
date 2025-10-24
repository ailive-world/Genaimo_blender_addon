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

import bpy
import importlib

def _compute_addon_key(pkg: str) -> str:
    # extensions: "bl_ext.user_default.genaimo_addon[.sub...]"
    if pkg.startswith("bl_ext."):
        return ".".join(pkg.split(".")[:3])
    # legacy: "genaimo_addon[.sub...]"
    return pkg.split(".")[0]

ADDON_KEY = _compute_addon_key(__package__)

class GenaimoPreferences(bpy.types.AddonPreferences):
    bl_idname = ADDON_KEY           
    api_key: bpy.props.StringProperty(name="API Key")
    api_secret: bpy.props.StringProperty(name="API Secret", subtype='PASSWORD')

    def draw(self, context):
        col = self.layout.column()
        col.prop(self, "api_key")
        col.prop(self, "api_secret")


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
    bpy.utils.register_class(GenaimoPreferences)
    genaimo_addon.register()

def unregister():
    try:
        genaimo_addon.unregister()
    finally:
        bpy.utils.unregister_class(GenaimoPreferences)
import bpy 
from . import (
    properties,
    ui,
    operators,
)



def register():
    # Register properties first
    try:
        properties.define_props()
    except ValueError as e:
        print(f"Warning: Some properties already registered: {e}")
    
    # Register operators
    for operator in operators.OPERATORS:
        try:
            bpy.utils.register_class(operator)
        except ValueError:
            # Class already registered, skip
            pass

    # Register UI classes
    for ui_class in ui.UI_CLASSES:
        try:
            bpy.utils.register_class(ui_class)
        except ValueError:
            # Class already registered, skip
            pass


    #subscribe to changes of the shape keys and call the function to update the joint locations
    # bpy.msgbus.subscribe_rna(
    #     key =  bpy.types.ShapeKey, #will check for all the properties changes in ShapeKeys. We are mostly interested in .value and .mute
    #     owner=handle_shape_key_change,
    #     args=(1, 2, 3),
    #     notify=shape_key_change
    # )
    
def unregister():
    # Unregister UI classes first
    for ui_class in ui.UI_CLASSES:
        try:
            bpy.utils.unregister_class(ui_class)
        except (ValueError, RuntimeError):
            # Class not registered or already unregistered, skip
            pass

    # Unregister operators
    for operator in operators.OPERATORS:
        try:
            bpy.utils.unregister_class(operator)
        except (ValueError, RuntimeError):
            # Class not registered or already unregistered, skip
            pass

    # Clear properties last
    properties.clear_props()

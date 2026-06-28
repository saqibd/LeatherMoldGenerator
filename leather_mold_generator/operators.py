"""
operators.py

Blender operators for the Leather Mold Generator.
"""

import bpy


class OBJECT_OT_GenerateLeatherMold(bpy.types.Operator):
    """Generate a leather mold from the selected object."""

    bl_idname = "object.generate_leather_mold"
    bl_label = "Generate Mold"
    bl_description = "Generate a leather mold from the selected object"

    def execute(self, context):

        active_object = context.active_object

        if active_object is None:
            self.report(
                {'ERROR'},
                "Please select an STL object first."
            )
            return {'CANCELLED'}

        self.report(
            {'INFO'},
            f"Selected object: {active_object.name}"
        )

        # Geometry generation will be added in Version 0.2

        return {'FINISHED'}


classes = (
    OBJECT_OT_GenerateLeatherMold,
)


def register():

    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
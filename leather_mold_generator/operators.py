"""
operators.py

Blender operators for the Leather Mold Generator.
"""

import bpy

from .mold_generator import MoldGenerator


class OBJECT_OT_GenerateLeatherMold(bpy.types.Operator):
    """Generate a leather mold from the selected object."""

    bl_idname = "object.generate_leather_mold"
    bl_label = "Generate Mold"
    bl_description = "Generate a leather mold from the selected object"

    def execute(self, context):

        try:
            generator = MoldGenerator(context)
            generator.generate()
        except ValueError as error:
            self.report({'ERROR'}, str(error))
            return {'CANCELLED'}

        self.report({'INFO'}, "Mold master created successfully.")
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
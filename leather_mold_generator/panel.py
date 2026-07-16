"""
panel.py

User interface for the Leather Mold Generator.
"""

import bpy


class VIEW3D_PT_LeatherMoldPanel(bpy.types.Panel):
    """Main UI panel."""

    bl_label = "Leather Mold Generator"
    bl_idname = "VIEW3D_PT_leather_mold_generator"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Leather Mold"

    def draw(self, context):

        layout = self.layout
        settings = context.scene.leather_mold

        # ----------------------------
        # Leather Settings
        # ----------------------------

        leather_box = layout.box()
        leather_box.label(text="Leather Settings")

        leather_box.prop(settings, "leather_thickness")
        leather_box.prop(settings, "clearance")

        # ----------------------------
        # Block Settings
        # ----------------------------

        block_box = layout.box()
        block_box.label(text="Block Settings")

        block_box.prop(settings, "side_margin")
        block_box.prop(settings, "front_back_margin")
        block_box.prop(settings, "bottom_thickness")
        block_box.prop(settings, "top_clearance")
        block_box.prop(settings, "cavity_tolerance")
        block_box.prop(settings, "draft_angle")

        # ----------------------------
        # Generate Button
        # ----------------------------

        layout.separator()

        layout.operator(
            "object.generate_leather_mold",
            icon='MOD_BOOLEAN'
        )


classes = (
    VIEW3D_PT_LeatherMoldPanel,
)


def register():

    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
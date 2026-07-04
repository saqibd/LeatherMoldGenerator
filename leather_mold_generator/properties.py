"""
properties.py

Blender Property Groups for the Leather Mold Generator.
"""

import bpy
from bpy.types import PropertyGroup
from bpy.props import FloatProperty, PointerProperty


class LeatherMoldProperties(PropertyGroup):
    """Settings used by the Leather Mold Generator."""

    leather_thickness: FloatProperty(
        name="Leather Thickness",
        description="Thickness of the leather in millimeters",
        default=2.0,
        min=0.5,
        max=10.0,
        precision=2,
        unit='LENGTH',
    )

    clearance: FloatProperty(
        name="Clearance",
        description="Additional clearance between the mold and leather",
        default=0.5,
        min=0.0,
        max=5.0,
        precision=2,
        unit='LENGTH',
    )

    side_margin: FloatProperty(
        name="Side Margin",
        description="Margin added to both sides of the mold master width",
        default=10.0,
        min=0.0,
        unit='LENGTH',
    )

    front_back_margin: FloatProperty(
        name="Front / Back Margin",
        description="Margin added to front and back of the mold master depth",
        default=10.0,
        min=0.0,
        unit='LENGTH',
    )

    bottom_thickness: FloatProperty(
        name="Bottom Thickness",
        description="Additional thickness added below the mold master",
        default=20.0,
        min=0.0,
        unit='LENGTH',
    )

    top_clearance: FloatProperty(
        name="Top Clearance",
        description="Additional clearance added above the mold master",
        default=5.0,
        min=0.0,
        unit='LENGTH',
    )


def register():
    """Register Blender properties."""

    bpy.utils.register_class(LeatherMoldProperties)

    bpy.types.Scene.leather_mold = PointerProperty(
        type=LeatherMoldProperties
    )


def unregister():
    """Unregister Blender properties."""

    del bpy.types.Scene.leather_mold

    bpy.utils.unregister_class(LeatherMoldProperties)
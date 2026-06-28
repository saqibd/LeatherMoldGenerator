bl_info = {
    "name": "Leather Mold Generator",
    "author": "Shaikh Najam",
    "version": (0, 1, 0),
    "blender": (5, 1, 0),
    "location": "View3D > Sidebar > Leather Mold",
    "description": "Generate leather molds from STL models.",
    "category": "Object",
}

from . import operators
from . import panel
from . import properties


def register():
    """Register all Blender classes."""
    properties.register()
    operators.register()
    panel.register()


def unregister():
    """Unregister all Blender classes."""
    panel.unregister()
    operators.unregister()
    properties.unregister()
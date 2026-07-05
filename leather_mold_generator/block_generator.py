"""
block_generator.py

Create and manage block geometry for the Leather Mold workflow.
"""

from __future__ import annotations

import bpy

from mathutils import Vector

from .collection_manager import CollectionManager
from .constants import LEATHER_MOLD_COLLECTION_NAME, MOLD_BLOCK_OBJECT_NAME


class BlockGenerator:
    """Generate the block object used by the leather mold workflow."""

    def __init__(self, context: bpy.types.Context) -> None:
        """Initialize the block generator.

        Args:
            context: Active Blender context used for all operations.
        """
        self.context = context

    def create_block(
        self,
        mold_master: bpy.types.Object,
    ) -> bpy.types.Object:
        """Create a cube block and move it into the Leather Mold collection.

        The block dimensions are set using the current scene settings.

        Args:
            mold_master: The mold master object used to position the block.

        Returns:
            The newly created cube object.

        Raises:
            ValueError: If the cube could not be created.
        """
        collection_manager = CollectionManager(self.context)
        collection_manager.delete_object(
            MOLD_BLOCK_OBJECT_NAME,
            delete_copies=True,
        )

        bpy.ops.mesh.primitive_cube_add()

        block = self.context.active_object
        if block is None:
            raise ValueError("Failed to create block object.")

        block.name = MOLD_BLOCK_OBJECT_NAME

        self.size_block(block, mold_master)
        self.position_block(block, mold_master)

        leather_mold_collection = collection_manager.get_or_create_collection(
            LEATHER_MOLD_COLLECTION_NAME
        )
        collection_manager.move_object_to_collection(block, leather_mold_collection)
        self.add_boolean_modifier(block, mold_master)
        self.apply_boolean_modifier(block)

        return block

    def add_boolean_modifier(
        self,
        block: bpy.types.Object,
        mold_master: bpy.types.Object,
    ) -> None:
        """Add an unapplied Boolean difference modifier to the block."""
        modifier = block.modifiers.new("Mold_Cavity", "BOOLEAN")
        modifier.operation = "DIFFERENCE"
        modifier.object = mold_master

    def apply_boolean_modifier(
        self,
        block: bpy.types.Object,
    ) -> None:
        """Apply the existing Mold_Cavity boolean modifier to the block."""
        modifier = block.modifiers.get("Mold_Cavity")
        if modifier is None:
            raise ValueError("Boolean modifier 'Mold_Cavity' not found.")

        bpy.ops.object.mode_set(mode="OBJECT")
        for obj in self.context.selected_objects:
            obj.select_set(False)
        block.select_set(True)
        self.context.view_layer.objects.active = block

        bpy.ops.object.modifier_apply(modifier="Mold_Cavity")

        mold_master = block.modifiers[0].object if block.modifiers else None
        if mold_master is not None:
            mold_master.hide_viewport = True
            mold_master.hide_render = True
            print("===== MOLD MASTER VISIBILITY =====")
            print(f"Mold_Master found : {mold_master.name}")
            print(f"Viewport hidden   : {mold_master.hide_viewport}")
            print(f"Render hidden     : {mold_master.hide_render}")
            print("================================")

    def position_block(
        self,
        block: bpy.types.Object,
        mold_master: bpy.types.Object,
    ) -> None:
        """Position the block at the world-space center of the mold master.

        Args:
            block: The block object to position.
            mold_master: The mold master object that defines the center.
        """
        corners = [
            mold_master.matrix_world @ Vector(corner)
            for corner in mold_master.bound_box
        ]

        min_x = min(c.x for c in corners)
        min_y = min(c.y for c in corners)
        min_z = min(c.z for c in corners)
        max_x = max(c.x for c in corners)
        max_y = max(c.y for c in corners)
        max_z = max(c.z for c in corners)

        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2

        settings = getattr(self.context.scene, "leather_mold", None)
        bottom_thickness = (
            settings.bottom_thickness if settings is not None else 0.0
        )
        top_clearance = settings.top_clearance if settings is not None else 0.0

        _, _, model_height = self.get_bounding_box_dimensions(mold_master)
        block_height = (
            model_height + bottom_thickness + top_clearance
        )

        block_bottom = min_z - bottom_thickness
        block.location.x = center_x
        block.location.y = center_y
        block.location.z = block_bottom + (block_height / 2)

    def size_block(
        self,
        block: bpy.types.Object,
        mold_master: bpy.types.Object,
    ) -> None:
        """Size the block to match the mold master's bounding-box dimensions.

        Args:
            block: The block object to size.
            mold_master: The mold master object used for size measurements.
        """
        settings = getattr(self.context.scene, "leather_mold", None)
        width, depth, height = self.get_bounding_box_dimensions(mold_master)

        if settings is None:
            block.scale = (
                width / 2.0,
                depth / 2.0,
                height / 2.0,
            )
            return

        block_width = width + (2 * settings.side_margin)
        block_depth = depth + (2 * settings.front_back_margin)
        block_height = (
            height
            + settings.bottom_thickness
            + settings.top_clearance
        )

        block.scale = (
            block_width / 2.0,
            block_depth / 2.0,
            block_height / 2.0,
        )

    def get_bounding_box_dimensions(
        self,
        mold_master: bpy.types.Object,
    ) -> tuple[float, float, float]:
        """Return the world-space dimensions of the mold master's bounding box.

        Args:
            mold_master: The mold master object used for dimension calculation.

        Returns:
            Tuple containing width, depth, and height.
        """
        corners = [
            mold_master.matrix_world @ Vector(corner)
            for corner in mold_master.bound_box
        ]

        min_x = min(c.x for c in corners)
        min_y = min(c.y for c in corners)
        min_z = min(c.z for c in corners)
        max_x = max(c.x for c in corners)
        max_y = max(c.y for c in corners)
        max_z = max(c.z for c in corners)

        width = max_x - min_x
        depth = max_y - min_y
        height = max_z - min_z

        return width, depth, height

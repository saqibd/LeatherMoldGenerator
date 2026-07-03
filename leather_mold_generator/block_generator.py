"""
block_generator.py

Create and manage block geometry for the Leather Mold workflow.
"""

from __future__ import annotations

import bpy

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

    def create_block(self) -> bpy.types.Object:
        """Create a cube block and move it into the Leather Mold collection.

        The block dimensions are set using the current scene settings.

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

        settings = getattr(self.context.scene, "leather_mold", None)
        if settings is not None:
            block.dimensions = (
                settings.block_width,
                settings.block_depth,
                settings.block_height,
            )
            self.context.view_layer.update()

        leather_mold_collection = collection_manager.get_or_create_collection(
            LEATHER_MOLD_COLLECTION_NAME
        )
        collection_manager.move_object_to_collection(block, leather_mold_collection)

        return block

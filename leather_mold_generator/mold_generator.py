"""
mold_generator.py

Orchestration layer for the Leather Mold Generator workflow.
"""

from __future__ import annotations

import bpy

from .block_generator import BlockGenerator
from .collection_manager import CollectionManager


class MoldGenerator:
    """Coordinate mold generation workflow across specialized modules."""

    def __init__(self, context: bpy.types.Context) -> None:
        """Initialize the generator with a Blender context.

        Args:
            context: Active Blender context used for all operations.
        """
        self.context = context

    def generate(self) -> bpy.types.Object:
        """Run the mold generation workflow.

        Returns:
            The duplicated mold master object.

        Raises:
            ValueError: If no object is active in the context.
        """
        if self.context.active_object is None:
            raise ValueError("No active object selected.")

        collection_manager = CollectionManager(self.context)
        mold_master = collection_manager.duplicate_active_object()

        block_generator = BlockGenerator(self.context)
        mold_block = block_generator.create_block(mold_master)

        return mold_master

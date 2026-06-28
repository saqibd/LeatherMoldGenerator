"""
collection_manager.py

Collection and object duplication helpers for the Leather Mold Generator.
"""

from __future__ import annotations

import bpy

LEATHER_MOLD_COLLECTION_NAME = "Leather Mold"
MOLD_MASTER_OBJECT_NAME = "Mold_Master"


class CollectionManager:
    """Manage collections, object duplication, and selection state."""

    def __init__(self, context: bpy.types.Context) -> None:
        """Initialize the manager with a Blender context.

        Args:
            context: Active Blender context used for all operations.
        """
        self.context = context

    def get_or_create_collection(self, name: str) -> bpy.types.Collection:
        """Return an existing collection or create and link a new one.

        Args:
            name: Name of the collection to find or create.

        Returns:
            The existing or newly created collection.
        """
        collection = bpy.data.collections.get(name)
        if collection is not None:
            return collection

        collection = bpy.data.collections.new(name)
        self.context.scene.collection.children.link(collection)
        return collection

    def duplicate_active_object(self) -> bpy.types.Object:
        """Duplicate the active object and prepare it as the mold master.

        Returns:
            The duplicated mold master object.

        Raises:
            ValueError: If no object is active in the context.
        """
        source_object = self.context.active_object
        if source_object is None:
            raise ValueError("No active object to duplicate.")

        self._remove_existing_master()

        duplicate = source_object.copy()
        if source_object.data is not None:
            duplicate.data = source_object.data.copy()

        duplicate.name = MOLD_MASTER_OBJECT_NAME

        leather_mold_collection = self.get_or_create_collection(
            LEATHER_MOLD_COLLECTION_NAME
        )
        self._move_object_to_collection(duplicate, leather_mold_collection)
        self._make_active(duplicate)

        return duplicate

    def _remove_existing_master(self) -> None:
        """Delete any existing object named ``Mold_Master``."""
        existing_master = bpy.data.objects.get(MOLD_MASTER_OBJECT_NAME)
        if existing_master is None:
            return

        mesh_data = existing_master.data
        bpy.data.objects.remove(existing_master, do_unlink=True)

        if isinstance(mesh_data, bpy.types.Mesh) and mesh_data.users == 0:
            bpy.data.meshes.remove(mesh_data)

    def _move_object_to_collection(
        self,
        obj: bpy.types.Object,
        collection: bpy.types.Collection,
    ) -> None:
        """Move an object into a single collection.

        Args:
            obj: Object to relocate.
            collection: Destination collection.
        """
        for user_collection in list(obj.users_collection):
            user_collection.objects.unlink(obj)

        if obj not in collection.objects:
           collection.objects.link(obj)

    def _make_active(self, obj: bpy.types.Object) -> None:
        """Deselect all objects, select the target, and make it active.

        Args:
            obj: Object to select and activate.
        """
        for selected_object in self.context.selected_objects:
            selected_object.select_set(False)

        obj.select_set(True)
        self.context.view_layer.objects.active = obj

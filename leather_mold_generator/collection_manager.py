"""
collection_manager.py

Collection and object duplication helpers for the Leather Mold Generator.
"""

from __future__ import annotations

import bpy

from .constants import LEATHER_MOLD_COLLECTION_NAME, MOLD_MASTER_OBJECT_NAME


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

        self.delete_object(MOLD_MASTER_OBJECT_NAME)

        duplicate = source_object.copy()
        if source_object.data is not None:
            duplicate.data = source_object.data.copy()

        duplicate.name = MOLD_MASTER_OBJECT_NAME

        leather_mold_collection = self.get_or_create_collection(
            LEATHER_MOLD_COLLECTION_NAME
        )
        self.move_object_to_collection(duplicate, leather_mold_collection)
        self._make_active(duplicate)

        return duplicate

    def move_object_to_collection(
        self,
        obj: bpy.types.Object,
        collection: bpy.types.Collection,
    ) -> None:
        """Move an object into a single collection.

        Args:
            obj: Object to relocate.
            collection: Destination collection.
        """
        self._move_object_to_collection(obj, collection)

    def delete_object(self, object_name: str, delete_copies: bool = False) -> None:
        """Delete a named object and its unused mesh datablock.

        Args:
            object_name: Name of the object to delete.
            delete_copies: If True, also delete numbered copies.
        """
        if delete_copies:
            object_names = [
                name
                for name in bpy.data.objects.keys()
                if name == object_name or name.startswith(f"{object_name}.")
            ]

            for name in object_names:
                obj = bpy.data.objects.get(name)
                if obj is None:
                    continue

                mesh_data = obj.data
                bpy.data.objects.remove(obj, do_unlink=True)

                if isinstance(mesh_data, bpy.types.Mesh) and mesh_data.users == 0:
                    bpy.data.meshes.remove(mesh_data)

            return

        obj = bpy.data.objects.get(object_name)
        if obj is None:
            return

        mesh_data = obj.data
        bpy.data.objects.remove(obj, do_unlink=True)

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

        try:
            collection.objects.link(obj)
        except RuntimeError:
            # Object is already linked to this collection.
            pass

    def _make_active(self, obj: bpy.types.Object) -> None:
        """Deselect all objects, select the target, and make it active.

        Args:
            obj: Object to select and activate.
        """
        for selected_object in self.context.selected_objects:
            selected_object.select_set(False)

        obj.select_set(True)
        self.context.view_layer.objects.active = obj

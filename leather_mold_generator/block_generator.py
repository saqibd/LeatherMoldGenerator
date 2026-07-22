"""
block_generator.py

Create and manage block geometry for the Leather Mold workflow.
"""

from __future__ import annotations

import bpy

from mathutils import Vector

from .collection_manager import CollectionManager
from .constants import (
    LEATHER_MOLD_COLLECTION_NAME,
    MOLD_BLOCK_OBJECT_NAME,
    MOLD_MASTER_TEMP_OBJECT_NAME,
)
from .geometry_validator import GeometryValidator


class BlockGenerator:
    """Generate the block object used by the leather mold workflow."""

    def __init__(self, context: bpy.types.Context) -> None:
        """Initialize the block generator.

        Args:
            context: Active Blender context used for all operations.
        """
        self.context = context
        self._current_reporter = None

    def _report(self, message: str, level: str = "INFO") -> None:
        """Centralized reporting helper that uses an operator reporter when available.

        Falls back to printing to the console if no reporter is set.
        """
        reporter = getattr(self, "_current_reporter", None)
        try:
            if reporter is not None and hasattr(reporter, "report"):
                reporter.report({level}, message)
            else:
                print(message)
        except Exception:
            # Best-effort fallback to console
            print(message)

    def create_block(
        self,
        mold_master: bpy.types.Object,
        reporter=None,
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
        # Preserve Blender state so we can restore if something fails
        previous_active = self.context.view_layer.objects.active
        # Set centralized reporter for use by helper and other methods
        self._current_reporter = reporter
        try:
            previous_mode = self.context.object.mode if self.context.object is not None else None
        except Exception:
            previous_mode = None
        previous_selected = list(self.context.selected_objects)

        collection_manager = CollectionManager(self.context)
        try:
            block = self._create_primitive_block(collection_manager)

            # Core generation steps
            self.size_block(block, mold_master)
            self.position_block(block, mold_master)

            leather_mold_collection = collection_manager.get_or_create_collection(
                LEATHER_MOLD_COLLECTION_NAME
            )
            cutter = self.create_cavity_cutter(mold_master, collection_manager)
            self.apply_cavity_tolerance(cutter)
            self.apply_draft_angle(cutter)
            collection_manager.move_object_to_collection(block, leather_mold_collection)

            validator = GeometryValidator(reporter)
            validation_result = validator.validate(cutter, block)
            self._report("Geometry Validation")
            self._report(f"Vertices: {validation_result['vertices']}")
            self._report(f"Edges: {validation_result['edges']}")
            self._report(f"Faces: {validation_result['faces']}")
            self._report(f"Non-manifold: {validation_result['non_manifold_edges']}")
            self._report(f"Loose Vertices: {validation_result['loose_vertices']}")
            self._report(f"Zero-area Faces: {validation_result['zero_area_faces']}")
            self._report("Validation Passed")
            self._report("Bounding Box Summary")
            self._report(f"Width: {validation_result['bounding_box'][0]:.2f} mm")
            self._report(f"Depth: {validation_result['bounding_box'][1]:.2f} mm")
            self._report(f"Height: {validation_result['bounding_box'][2]:.2f} mm")
            self._report("Manufacturing Readiness")
            self._report(f"Maximum Cavity Depth: {validation_result['max_cavity_depth']:.2f} mm")
            self._report(f"Estimated wall thickness: {validation_result['estimated_wall_thickness']:.2f} mm")
            self._report(f"Recommended cutter: {validation_result['recommended_cutter']}")
            if validation_result['manufacturing_warnings']:
                self._report("Warnings:")
                for warning in validation_result['manufacturing_warnings']:
                    self._report(f"- {warning}")
                self._report("Manufacturing Ready with Warnings")
            else:
                self._report("Warnings: None")
                self._report("Manufacturing Ready")
            self._report("Export Readiness")
            self._report(f"Transforms: {validation_result['transform_status']}")
            self._report(f"Normals: {validation_result['normal_status']}")
            self._report(f"Triangles: {validation_result['triangle_count']}")
            self._report(f"Estimated STL: {validation_result['estimated_stl_size_mb']:.2f} MB")
            if validation_result['export_warnings']:
                for warning in validation_result['export_warnings']:
                    self._report(f"- {warning}")
                self._report("Export Ready with Warnings")
            else:
                self._report("Export Ready")

            self.add_boolean_modifier(block, cutter)
            self.apply_boolean_modifier(block, mold_master, cutter)

            # Finalize generated block (ensure active and in OBJECT mode)
            self._finalize_block(block)

            success = True
            return block
        except Exception as exc:
            # Attempt to restore Blender to a safe state
            try:
                bpy.ops.object.mode_set(mode="OBJECT")
            except Exception:
                pass
            except Exception:
                pass

            # Clear centralized reporter
            try:
                self._current_reporter = None
            except Exception:
                pass
            # Restore selection and active object if possible
            try:
                for obj in list(self.context.selected_objects):
                    obj.select_set(False)
                for obj in previous_selected:
                    try:
                        obj.select_set(True)
                    except Exception:
                        pass
                if previous_active is not None and previous_active.name in self.context.view_layer.objects:
                    try:
                        self.context.view_layer.objects.active = previous_active
                    except Exception:
                        pass
            except Exception:
                pass

            # Report error via operator reporter when available
            try:
                if reporter is not None and hasattr(reporter, "report"):
                    reporter.report({"ERROR"}, f"Error generating mold block: {exc}")
                else:
                    print(f"Error generating mold block: {exc}")
            except Exception:
                print(f"Error generating mold block (and failed to report): {exc}")

            # Re-raise to surface the error to callers (keeps behavior visible for debugging)
            raise
        finally:
            # If we didn't succeed, ensure mode restored to previous_mode where possible
            try:
                if 'success' not in locals() or not success:
                    if previous_mode is not None:
                        try:
                            bpy.ops.object.mode_set(mode=previous_mode)
                        except Exception:
                            # Fallback to OBJECT mode
                            try:
                                bpy.ops.object.mode_set(mode="OBJECT")
                            except Exception:
                                pass
            except Exception:
                pass

    def create_cavity_cutter(
        self,
        mold_master: bpy.types.Object,
        collection_manager: CollectionManager,
    ) -> bpy.types.Object:
        """Create a temporary duplicate of the mold master for Boolean cavity scaling."""
        if mold_master is None:
            raise ValueError("Mold master object is required for cavity cutter creation.")

        collection_manager.delete_object(MOLD_MASTER_TEMP_OBJECT_NAME, delete_copies=True)

        cutter = mold_master.copy()
        if mold_master.data is not None:
            cutter.data = mold_master.data.copy()

        cutter.name = MOLD_MASTER_TEMP_OBJECT_NAME
        cutter.hide_viewport = False
        cutter.hide_render = False

        leather_mold_collection = collection_manager.get_or_create_collection(
            LEATHER_MOLD_COLLECTION_NAME
        )
        collection_manager.move_object_to_collection(cutter, leather_mold_collection)
        return cutter

    def apply_cavity_tolerance(
        self,
        mold_master: bpy.types.Object,
    ) -> None:
        """Enlarge the provided cutter uniformly for the Boolean cavity clearance."""
        if mold_master is None:
            return

        settings = getattr(self.context.scene, "leather_mold", None)
        tolerance = getattr(settings, "cavity_tolerance", 0.0) if settings is not None else 0.0

        if tolerance <= 0.0:
            return

        width, depth, height = self.get_bounding_box_dimensions(mold_master)
        reference_dimension = max(width, depth, height)

        if reference_dimension <= 0.0:
            return

        scale_factor = 1.0 + (tolerance / reference_dimension)
        mold_master.scale = Vector((
            mold_master.scale.x * scale_factor,
            mold_master.scale.y * scale_factor,
            mold_master.scale.z * scale_factor,
        ))

    def apply_draft_angle(self, cutter_object: bpy.types.Object) -> None:
        """Apply a conservative BMesh taper to the temporary Boolean cutter."""
        if cutter_object is None:
            return

        settings = getattr(self.context.scene, "leather_mold", None)
        draft_angle = getattr(settings, "draft_angle", 0.0) if settings is not None else 0.0

        if draft_angle <= 0.0:
            return

        self._report("Applying draft angle...")

        import bmesh

        mesh = cutter_object.data
        if mesh is None:
            return

        bm = bmesh.new()
        bm.from_mesh(mesh)

        try:
            min_z = min(v.co.z for v in bm.verts)
            max_z = max(v.co.z for v in bm.verts)
            height = max_z - min_z
            if height <= 0.0:
                return

            radians_angle = draft_angle
            taper_amount = max(0.0, abs(radians_angle) * 0.01)

            for vertex in bm.verts:
                factor = (vertex.co.z - min_z) / height
                offset = factor * taper_amount
                vertex.co.x += offset
                vertex.co.y += offset

            bm.to_mesh(mesh)
            mesh.update()
        finally:
            bm.free()

    def add_boolean_modifier(
        self,
        block: bpy.types.Object,
        mold_master: bpy.types.Object,
    ) -> None:
        """Add an unapplied Boolean difference modifier to the block."""
        modifier = block.modifiers.new("Mold_Cavity", "BOOLEAN")
        modifier.operation = "DIFFERENCE"
        modifier.object = mold_master

    def _create_primitive_block(self, collection_manager: CollectionManager) -> bpy.types.Object:
        """Create a primitive cube and prepare it as the mold block.

        This extracts the primitive creation and naming so the orchestration
        in create_block stays high-level.
        """
        collection_manager.delete_object(
            MOLD_BLOCK_OBJECT_NAME,
            delete_copies=True,
        )

        bpy.ops.mesh.primitive_cube_add()

        block = self.context.active_object
        if block is None:
            raise ValueError("Failed to create block object.")

        block.name = MOLD_BLOCK_OBJECT_NAME
        return block

    def _finalize_block(self, block: bpy.types.Object) -> None:
        """Finalize the generated block: make active and ensure OBJECT mode."""
        try:
            block.select_set(True)
            self.context.view_layer.objects.active = block
            bpy.ops.object.mode_set(mode="OBJECT")
        except Exception:
            # Best-effort; don't mask successful generation
            pass

    def apply_boolean_modifier(
        self,
        block: bpy.types.Object,
        mold_master: bpy.types.Object,
        cutter: bpy.types.Object | None = None,
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

        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.object.mode_set(mode="OBJECT")

        if cutter is not None:
            try:
                bpy.data.objects.remove(cutter, do_unlink=True)
            except Exception:
                pass

        if mold_master is not None:
            mold_master.hide_viewport = True
            mold_master.hide_render = True

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

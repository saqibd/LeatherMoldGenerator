"""
geometry_validator.py

Non-destructive geometry inspection for the Leather Mold workflow.
"""

from __future__ import annotations

import math

import bpy
import bmesh
from mathutils import Vector


class GeometryValidator:
    """Inspect mesh geometry without modifying it."""

    def __init__(self, reporter=None) -> None:
        """Store an optional reporter for validation output."""
        self._current_reporter = reporter

    def validate(self, obj: bpy.types.Object | None, block_obj: bpy.types.Object | None = None) -> dict:
        """Return structured validation information for the supplied mesh object."""
        if obj is None or obj.type != 'MESH' or obj.data is None:
            return {
                "vertices": 0,
                "edges": 0,
                "faces": 0,
                "non_manifold_edges": 0,
                "loose_vertices": 0,
                "zero_area_faces": 0,
                "bounding_box": (0.0, 0.0, 0.0),
                "draft_angle": 0.0,
                "cavity_tolerance": 0.0,
                "max_cavity_depth": 0.0,
                "estimated_wall_thickness": 0.0,
                "min_edge_length": 0.0,
                "cutter_diameter": 3.0,
                "manufacturing_warnings": [],
                "recommended_cutter": "3.0 mm Ball End",
                "manufacturing_ready": False,
                "transform_warnings": [],
                "transform_status": "PASS",
                "triangle_count": 0,
                "inverted_face_count": 0,
                "normal_status": "PASS",
                "estimated_stl_size_mb": 0.0,
                "export_warnings": [],
                "export_ready": True,
            }

        settings = getattr(bpy.context.scene, "leather_mold", None)
        draft_angle = getattr(settings, "draft_angle", 0.0) if settings is not None else 0.0
        cavity_tolerance = getattr(settings, "cavity_tolerance", 0.0) if settings is not None else 0.0

        bm = bmesh.new()
        try:
            bm.from_mesh(obj.data)
            geometry_result = self._validate_geometry(obj, bm)
            manufacturing_result = self._validate_manufacturing(
                bm,
                block_obj,
                geometry_result["bounding_box"],
            )
            export_result = self._validate_export(obj, bm)

            return {
                **geometry_result,
                **manufacturing_result,
                **export_result,
                "draft_angle": draft_angle,
                "cavity_tolerance": cavity_tolerance,
                "manufacturing_ready": not manufacturing_result["manufacturing_warnings"],
                "export_ready": not export_result["export_warnings"],
            }
        finally:
            bm.free()

    def _validate_geometry(self, obj: bpy.types.Object, bm: bmesh.types.BMesh) -> dict:
        """Collect core mesh geometry statistics without changing the mesh."""
        vertices = len(bm.verts)
        edges = len(bm.edges)
        faces = len(bm.faces)

        non_manifold_edges = 0
        for edge in bm.edges:
            if len(edge.link_faces) != 2:
                non_manifold_edges += 1

        loose_vertices = sum(1 for vertex in bm.verts if len(vertex.link_edges) == 0)

        zero_area_faces = 0
        for face in bm.faces:
            area = face.calc_area()
            if area <= 1e-12:
                zero_area_faces += 1

        min_x = min((obj.matrix_world @ vertex.co).x for vertex in bm.verts) if vertices else 0.0
        max_x = max((obj.matrix_world @ vertex.co).x for vertex in bm.verts) if vertices else 0.0
        min_y = min((obj.matrix_world @ vertex.co).y for vertex in bm.verts) if vertices else 0.0
        max_y = max((obj.matrix_world @ vertex.co).y for vertex in bm.verts) if vertices else 0.0
        min_z = min((obj.matrix_world @ vertex.co).z for vertex in bm.verts) if vertices else 0.0
        max_z = max((obj.matrix_world @ vertex.co).z for vertex in bm.verts) if vertices else 0.0

        bounding_box = (
            max_x - min_x,
            max_y - min_y,
            max_z - min_z,
        )

        return {
            "vertices": vertices,
            "edges": edges,
            "faces": faces,
            "non_manifold_edges": non_manifold_edges,
            "loose_vertices": loose_vertices,
            "zero_area_faces": zero_area_faces,
            "bounding_box": bounding_box,
        }

    def _validate_manufacturing(
        self,
        bm: bmesh.types.BMesh,
        block_obj: bpy.types.Object | None,
        bounding_box: tuple[float, float, float],
    ) -> dict:
        """Collect manufacturing-oriented validation details without changing the mesh."""
        max_cavity_depth = bounding_box[2]
        estimated_wall_thickness = 0.0
        manufacturing_warnings = []

        if block_obj is not None and block_obj.type == 'MESH' and block_obj.data is not None:
            block_bbox = self._get_bounding_box_dimensions(block_obj)
            thickness_candidates = []
            for block_dimension, cavity_dimension in zip(block_bbox, bounding_box):
                if block_dimension > cavity_dimension:
                    thickness_candidates.append((block_dimension - cavity_dimension) / 2.0)
                else:
                    thickness_candidates.append(0.0)
            estimated_wall_thickness = min(thickness_candidates) if thickness_candidates else 0.0

        if estimated_wall_thickness < 2.0:
            manufacturing_warnings.append(
                "WARNING: Estimated wall thickness may be too thin for machining."
            )

        min_edge_length = 0.0
        if len(bm.edges):
            min_edge_length = min(edge.calc_length() for edge in bm.edges)
            if min_edge_length < 1.5:
                manufacturing_warnings.append(
                    "WARNING: Very small geometric features detected. A smaller cutter may be required."
                )

        return {
            "max_cavity_depth": max_cavity_depth,
            "estimated_wall_thickness": estimated_wall_thickness,
            "min_edge_length": min_edge_length,
            "cutter_diameter": 3.0,
            "manufacturing_warnings": manufacturing_warnings,
            "recommended_cutter": "3.0 mm Ball End",
        }

    def _validate_export(self, obj: bpy.types.Object, bm: bmesh.types.BMesh) -> dict:
        """Collect export-readiness validation details without changing the mesh."""
        transform_warnings = []
        location = obj.location
        rotation = obj.rotation_euler
        scale = obj.scale
        if not all(math.isclose(value, 0.0, abs_tol=1e-6) for value in (location.x, location.y, location.z)):
            transform_warnings.append("WARNING: Object location is not at the origin.")
        if not all(math.isclose(value, 0.0, abs_tol=1e-6) for value in (rotation.x, rotation.y, rotation.z)):
            transform_warnings.append("WARNING: Object rotation is not identity.")
        if not all(math.isclose(value, 1.0, abs_tol=1e-4) for value in (scale.x, scale.y, scale.z)):
            transform_warnings.append("WARNING: Object scale should be applied before export.")

        face_orientation_result = self._validate_face_orientation(obj, bm)
        triangle_count = sum(max(0, len(face.verts) - 2) for face in bm.faces)
        estimated_stl_size_mb = (triangle_count * 50.0) / (1024.0 * 1024.0)

        export_warnings = list(transform_warnings)
        if face_orientation_result["inverted_face_count"] > 0:
            export_warnings.append("WARNING: Inverted face normals detected.")

        return {
            "transform_warnings": transform_warnings,
            "transform_status": "WARNING" if transform_warnings else "PASS",
            "triangle_count": triangle_count,
            "inverted_face_count": face_orientation_result["inverted_face_count"],
            "normal_status": face_orientation_result["normal_status"],
            "estimated_stl_size_mb": estimated_stl_size_mb,
            "export_warnings": export_warnings,
        }

    def _validate_face_orientation(self, obj: bpy.types.Object, bm: bmesh.types.BMesh) -> dict:
        """Detect likely inverted face orientations without changing the mesh."""
        inverted_face_count = 0
        object_center = self._get_object_center(obj, bm)
        if object_center is None:
            return {
                "inverted_face_count": 0,
                "normal_status": "PASS",
            }

        for face in bm.faces:
            face_center = Vector(face.calc_center_median())
            face_normal = Vector(face.normal)
            vector_to_center = object_center - face_center
            if face_normal.dot(vector_to_center) > 0.0:
                inverted_face_count += 1

        return {
            "inverted_face_count": inverted_face_count,
            "normal_status": "WARNING" if inverted_face_count > 0 else "PASS",
        }

    def _get_bounding_box_dimensions(self, obj: bpy.types.Object | None) -> tuple[float, float, float]:
        """Return the world-space bounding box dimensions for an object."""
        if obj is None or obj.type != 'MESH' or obj.data is None:
            return (0.0, 0.0, 0.0)

        bm = bmesh.new()
        try:
            bm.from_mesh(obj.data)
            if not bm.verts:
                return (0.0, 0.0, 0.0)

            min_x = min((obj.matrix_world @ vertex.co).x for vertex in bm.verts)
            max_x = max((obj.matrix_world @ vertex.co).x for vertex in bm.verts)
            min_y = min((obj.matrix_world @ vertex.co).y for vertex in bm.verts)
            max_y = max((obj.matrix_world @ vertex.co).y for vertex in bm.verts)
            min_z = min((obj.matrix_world @ vertex.co).z for vertex in bm.verts)
            max_z = max((obj.matrix_world @ vertex.co).z for vertex in bm.verts)

            return (
                max_x - min_x,
                max_y - min_y,
                max_z - min_z,
            )
        finally:
            bm.free()

    def _get_object_center(self, obj: bpy.types.Object | None, bm: bmesh.types.BMesh | None = None) -> Vector | None:
        """Return the world-space center of an object's bounding box as a Vector."""
        if obj is None or obj.type != 'MESH' or obj.data is None:
            return None

        if bm is None:
            bm = bmesh.new()
            try:
                bm.from_mesh(obj.data)
            except Exception:
                return None

        if not bm.verts:
            return None

        world_vertices = [Vector(obj.matrix_world @ vertex.co) for vertex in bm.verts]
        min_x = min(vertex.x for vertex in world_vertices)
        max_x = max(vertex.x for vertex in world_vertices)
        min_y = min(vertex.y for vertex in world_vertices)
        max_y = max(vertex.y for vertex in world_vertices)
        min_z = min(vertex.z for vertex in world_vertices)
        max_z = max(vertex.z for vertex in world_vertices)

        corners = [
            Vector((min_x, min_y, min_z)),
            Vector((max_x, min_y, min_z)),
            Vector((min_x, max_y, min_z)),
            Vector((max_x, max_y, min_z)),
            Vector((min_x, min_y, max_z)),
            Vector((max_x, min_y, max_z)),
            Vector((min_x, max_y, max_z)),
            Vector((max_x, max_y, max_z)),
        ]
        center = Vector((0.0, 0.0, 0.0))
        for corner in corners:
            center += corner
        return center / len(corners)

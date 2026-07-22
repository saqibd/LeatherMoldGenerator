"""
geometry_validator.py

Non-destructive geometry inspection for the Leather Mold workflow.
"""

from __future__ import annotations

import math

import bpy
import bmesh


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
            }

        settings = getattr(bpy.context.scene, "leather_mold", None)
        draft_angle = getattr(settings, "draft_angle", 0.0) if settings is not None else 0.0
        cavity_tolerance = getattr(settings, "cavity_tolerance", 0.0) if settings is not None else 0.0

        bm = bmesh.new()
        try:
            bm.from_mesh(obj.data)

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
            if edges:
                min_edge_length = min(edge.calc_length() for edge in bm.edges)
                if min_edge_length < 1.5:
                    manufacturing_warnings.append(
                        "WARNING: Very small geometric features detected. A smaller cutter may be required."
                    )

            return {
                "vertices": vertices,
                "edges": edges,
                "faces": faces,
                "non_manifold_edges": non_manifold_edges,
                "loose_vertices": loose_vertices,
                "zero_area_faces": zero_area_faces,
                "bounding_box": bounding_box,
                "draft_angle": draft_angle,
                "cavity_tolerance": cavity_tolerance,
                "max_cavity_depth": max_cavity_depth,
                "estimated_wall_thickness": estimated_wall_thickness,
                "min_edge_length": min_edge_length,
                "cutter_diameter": 3.0,
                "manufacturing_warnings": manufacturing_warnings,
                "recommended_cutter": "3.0 mm Ball End",
                "manufacturing_ready": not manufacturing_warnings,
            }
        finally:
            bm.free()

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

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

    def validate(self, obj: bpy.types.Object | None) -> dict:
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

            min_x = min(vertex.co.x for vertex in bm.verts) if vertices else 0.0
            max_x = max(vertex.co.x for vertex in bm.verts) if vertices else 0.0
            min_y = min(vertex.co.y for vertex in bm.verts) if vertices else 0.0
            max_y = max(vertex.co.y for vertex in bm.verts) if vertices else 0.0
            min_z = min(vertex.co.z for vertex in bm.verts) if vertices else 0.0
            max_z = max(vertex.co.z for vertex in bm.verts) if vertices else 0.0

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
                "draft_angle": draft_angle,
                "cavity_tolerance": cavity_tolerance,
            }
        finally:
            bm.free()

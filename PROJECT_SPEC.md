# Leather Mold Generator

## Project Overview

Leather Mold Generator is a Blender 5.1+ add-on that creates leather-forming molds from 3D models such as STL files.

The project is intended for leather craftsmen, product designers, CNC users, and 3D printing enthusiasts who need accurate male and female molds for wet-forming leather.

---

## Primary Objectives

- Import and analyze STL models.
- Automatically orient the model for mold generation.
- Generate a male mold.
- Generate a female mold.
- Apply configurable leather thickness compensation.
- Support draft angles.
- Add alignment pins.
- Add bolt holes.
- Add vent grooves.
- Export printable STL files.

---

## Supported Software

- Blender 5.1+
- Python 3.x (Bundled with Blender)

---

## Project Architecture

UI

- panel.py

User Actions

- operators.py

Properties

- properties.py

Geometry Generation

- mold_generator.py

Shared Utilities

- utils.py

---

## Coding Principles

- Keep UI separate from modeling logic.
- Operators should call functions instead of containing geometry code.
- Utility functions belong in utils.py.
- Geometry generation belongs in mold_generator.py.
- Keep functions small and reusable.
- Write readable and well-documented code.

---

## Future Features

- Automatic model orientation
- Leather shrinkage compensation
- Configurable mold dimensions
- Split molds
- Registration pins
- Vent channels
- CNC export
- 3D-print optimized mold generation

---

## Project Status

Version: 0.1.0

Status: Foundation
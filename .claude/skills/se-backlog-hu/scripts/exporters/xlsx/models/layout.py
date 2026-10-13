"""Configuración de layout y estructura del Excel."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ColumnSpec:
    """Especificación de una columna: letra, ancho y header."""
    letter: str
    width: float
    header: str


@dataclass(frozen=True)
class Layout:
    """Configuración de layout del spreadsheet."""
    sheet_name: str = "Tareas"

    # Filas clave
    row_loop: int = 2
    row_estimated_by: int = 3
    row_table_header: int = 4
    row_table_subheader: int = 5
    row_first_data: int = 6

    # Columnas A..N
    columns: tuple[ColumnSpec, ...] = (
        ColumnSpec("A", 12, "Release"),
        ColumnSpec("B", 34, "User Story"),
        ColumnSpec("C", 18, "Block"),
        ColumnSpec("D", 46, "Activities"),
        ColumnSpec("E", 16, "Activity Type"),
        ColumnSpec("F", 10, "Role"),
        ColumnSpec("G", 10, "Level"),
        ColumnSpec("H", 6, "%"),
        ColumnSpec("I", 10, "Hours"),
        ColumnSpec("J", 10, "Risk"),
        ColumnSpec("K", 10, "H+Risk"),
        ColumnSpec("L", 26, "Approach"),
        ColumnSpec("M", 26, "Risk notes"),
        ColumnSpec("N", 10, "Historic")
    )

    # Merges / bloques superiores
    loop: str = "C1"
    estimated_by: str = "C2"
    merge_project: str = "D3:G3"
    team_persons_text: str = "L1"
    team_persons_value: str = "M1"
    team_weeks_text: str = "L2"
    team_weeks_value: str = "M2"
    
    # Ancho de columnas adicionales (fuera de la tabla principal)
    column_p_width: float = 20
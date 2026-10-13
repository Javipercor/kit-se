"""Cálculo de altura de fila para la columna de actividades."""

from __future__ import annotations

import textwrap


def calculate_height_for_activities_column(
    text: str | None,
    column_width: float = 46,  # Columna D
    base_height: float = 16,   # altura de 1 línea
    line_height: float = 16,   # incremento por línea extra
    padding_lines: int = 0,    # pon 1 si sueles quedarte corto
    max_height: float = 409,   # límite práctico Excel
) -> float:
    """Calcula la altura de la fila en función del contenido y el ancho de la columna."""
    if not text:
        return base_height

    s = str(text).replace("\r\n", "\n").replace("\r", "\n")

    # Ajusta caracteres útiles aproximados por margen interno en Excel
    usable_chars = max(1, int(column_width * 0.92))

    total_lines = 0
    for paragraph in s.split("\n"):
        wrapped = textwrap.wrap(
            paragraph,
            width=usable_chars,
            break_long_words=True,
            break_on_hyphens=True,
            replace_whitespace=False,
            drop_whitespace=False,
        )
        total_lines += max(1, len(wrapped))

    total_lines += padding_lines

    height = base_height + max(0, total_lines - 1) * line_height
    return min(max_height, height)

"""Helpers para construir fórmulas de Excel de forma tipada."""

from __future__ import annotations

from ..config.constants import Env


def sum_range(column: str, start_row: int, end_row: int) -> str:
    return f"=SUM({column}{start_row}:{column}{end_row})"


def average_divided_by_two(column: str, start_row: int, end_row: int) -> str:
    return f"{sum_range(column, start_row, end_row)}/{Env.AVERAGE_DIVISOR}"


def role_hours_formula(start_row: int, end_row: int, percent_reference: str) -> str:
    return f"=SUM(I{start_row}:I{end_row})*{percent_reference}"


def subheader_hours_formula(start_row: int, end_row: int) -> str:
    return sum_range("I", start_row, end_row)


def subheader_risk_formula(start_row: int, end_row: int) -> str:
    return sum_range("K", start_row, end_row)

def meeting_hours_formula(multiplier: float, column_refs: list[str], output_row: int) -> str:
    """Calcula horas de reuniones basado en semanas de equipo.
    
    Args:
        multiplier: Horas de reunión (ej: 0.75 para sprint, 1.25 para dailies)
        column_refs: Lista de columnas con las semanas (ej: ["R"] para Dev, ["R", "U"] para PM)
        output_row: Fila donde se calcula
    
    Returns:
        Fórmula que multiplica horas de reunión por semanas del equipo, redondeada hacia arriba
    """
    if len(column_refs) == 1:
        # Para Dev/DS: referencia a columna específica
        column_ref = f"${column_refs[0]}${output_row}"
    else:
        # Para PM: MAX de múltiples columnas
        refs = ",".join([f"${col}${output_row}" for col in column_refs])
        column_ref = f"MAX({refs})"
    
    return f"={multiplier}*{column_ref}"

def hours_with_risk_formula(hours_cell: str, risk_cell: str) -> str:
    return f"={hours_cell}*(1+1/6*{risk_cell})"

def team_hours_formula(first_row: int, last_row: int, roles: str | tuple[str, ...], multiplier_column: str, output_row: int, column: str = "I") -> str:
    """Suma las horas de un equipo específico basado en el rol en la columna F.
    
    Args:
        first_row: Primera fila de datos
        last_row: Última fila de datos
        roles: Rol o roles a filtrar (ej: "DEV", ("DEV", "ARCHITECT"))
        multiplier_column: Columna que contiene el multiplicador (ej: "Q" para Dev, "T" para DS)
        output_row: Fila donde se está renderizando para referenciar el multiplicador
        column: Columna a sumar (por defecto "I" para horas, "K" para horas+riesgo)
    
    Returns:
        Fórmula SUMIF que suma valores donde el rol coincide, redondeada hacia arriba
    """
    if isinstance(roles, str):
        roles = (roles,)
    
    # Construir suma de SUMIF para cada rol
    sumif_parts = [
        f"SUMIF(F{first_row}:F{last_row},\"{role}\",{column}{first_row}:{column}{last_row})"
        for role in roles
    ]
    sumif_expression = "+".join(sumif_parts)
    
    return (
        f"=ROUNDUP(({sumif_expression})/"
        f"${multiplier_column}${output_row}/{Env.HOURS_PER_WEEK},0)"
    )

def dev_team_hours_formula(first_row: int, last_row: int, output_row: int) -> str:
    """Suma las horas del equipo Dev (rol = "DEV" o "ARCHITECT")."""
    return team_hours_formula(first_row, last_row, ("DEV", "ARCHITECT"), "Q", output_row, "I")

def dev_team_risk_formula(first_row: int, last_row: int, output_row: int) -> str:
    """Suma las horas+riesgo del equipo Dev (rol = "DEV" o "ARCHITECT")."""
    return team_hours_formula(first_row, last_row, ("DEV", "ARCHITECT"), "Q", output_row, "K")

def ds_team_hours_formula(first_row: int, last_row: int, output_row: int) -> str:
    """Suma las horas del equipo DS (rol = "DS")."""
    return team_hours_formula(first_row, last_row, "DS", "T", output_row, "I")

def ds_team_risk_formula(first_row: int, last_row: int, output_row: int) -> str:
    """Suma las horas+riesgo del equipo DS (rol = "DS")."""
    return team_hours_formula(first_row, last_row, "DS", "T", output_row, "K")

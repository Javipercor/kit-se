"""Constantes de configuración para el generador de Excel."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Env:
    """Valores constantes usados en fórmulas y configuraciones."""

    HOURS_PER_WEEK: int = 32
    TEAM_MULTIPLIER_CELL: str = "M1"
    AVERAGE_DIVISOR: int = 2

    PROJECT_PLACEHOLDER: str = "PROYECTO XXX"
    LOOP_LABEL: str = "LOOP:"
    ESTIMATED_BY_LABEL: str = "Estimado por:"

    ACTIVITY_TYPE_LABEL: str = "Activity Type"
    ROLE_LABEL: str = "Role"
    LEVEL_LABEL: str = "Level"
    RISK_LABEL: str = "Risk"
    APPROACH_LABEL: str = "Approach"
    RISK_NOTES_LABEL: str = "Risk notes"
    PERCENT_PLACEHOLDER: str = "0%"

    PERCENT_TESTING_UNIT: str = "$J$1"
    PERCENT_TESTING_E2E: str = "$G$1"
    PERCENT_DEVOPS: str = "$G$2"
    PERCENT_PM: str = "$J$2"

    QA_LABEL: str = "QA"
    QA_PERCENT: str = "10%"
    DOP_LABEL: str = "DOP"
    DOP_PERCENT: str = "5%"
    TESTING_LABEL: str = "Testing"
    TESTING_PERCENT: str = "10%"
    PM_LABEL: str = "PM"
    PM_PERCENT: str = "20%"

    MEETINGS_SPRINT_HOURS: float = 0.75
    MEETINGS_DAILY_HOURS: float = 1.25

    PHASE_WEEKS_COLUMN: str = "Q"
    COLUMN_P_WIDTH: float = 20

    EXCLUDED_ROLE_KEYWORDS: tuple[str, ...] = (
        "Arquitectura",
        "DevOps",
        "Documentación",
        "Manuales",
        "Formación",
        "Reuniones"
    )

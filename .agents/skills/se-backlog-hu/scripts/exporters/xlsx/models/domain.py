"""Modelo de dominio - Estructuras de datos del JSON."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Union


FormulaValue = Union[float, str]


@dataclass(frozen=True)
class Activity:
    """Una actividad dentro de un bloque."""
    name: str
    activity_type: str
    role: str
    level: str
    hours: FormulaValue  # Número o fórmula
    risk: int | None  # None si es reunión
    hours_with_risk_formula: str | None = None  # Fórmula para K (H+Risk). Si es None, se calcula automáticamente


@dataclass(frozen=True)
class Block:
    """Un bloque contiene una lista de actividades."""
    name: str
    activities: tuple[Activity, ...]


@dataclass(frozen=True)
class UserStory:
    """Una user story contiene fase, título y bloques."""
    phase: str
    title: str
    blocks: tuple[Block, ...]


@dataclass(frozen=True)
class InputModel:
    """Modelo raíz del JSON cargado."""
    user_stories: tuple[UserStory, ...]

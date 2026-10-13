"""Paleta de colores centralizada."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Colors:
    HEADER_BLUE: str = "2F5597"
    ROW_BLUE: str = "5B9BD5"
    ROW_BLUE_ALT: str = "4472C4"
    BLOCK_LIGHT: str = "D9E1F2"
    ORANGE: str = "F4B183"
    YELLOW: str = "FFFF00"
    WHITE: str = "FFFFFF"
    BORDER_GRAY: str = "BFBFBF"

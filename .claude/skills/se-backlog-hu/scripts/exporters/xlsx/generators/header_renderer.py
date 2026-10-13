"""Renderer para la sección de cabecera del Excel."""

from __future__ import annotations

from openpyxl.styles import Alignment, Font
from openpyxl.worksheet.worksheet import Worksheet

from ..config.constants import Env
from ..models import Layout
from ..styles import Styles
from ..utils import WorksheetStyler


class HeaderRenderer:
    """Renderiza la sección de header del Excel (LOOP, proyecto, equipo)."""

    def __init__(self, layout: Layout, styles: Styles) -> None:
        self._layout = layout
        self._styles = styles

    def render(self, ws: Worksheet) -> None:
        """Renderiza el header en el worksheet."""
        styler = WorksheetStyler(ws, self._styles)

        styler.merge_and_style(
            self._layout.merge_project,
            value=Env.PROJECT_PLACEHOLDER,
            font=Font(name="Calibri", size=11, bold=True, color="FFFFFF"),
            fill=self._styles.fill_orange,
            alignment=Alignment(horizontal="left", vertical="center"),
        )

        items = {
            self._layout.loop: Env.LOOP_LABEL,
            self._layout.estimated_by: Env.ESTIMATED_BY_LABEL,
            "F1": Env.QA_LABEL,
            "G1": Env.QA_PERCENT,
            "F2": Env.DOP_LABEL,
            "G2": Env.DOP_PERCENT,
            "I1": Env.TESTING_LABEL,
            "J1": Env.TESTING_PERCENT,
            "I2": Env.PM_LABEL,
            "J2": Env.PM_PERCENT,
        }
        for addr, value in items.items():
            styler.set_cell(addr, value=value, font=self._styles.small_font, alignment=self._styles.center)

        ws.row_dimensions[1].height = 18
        ws.row_dimensions[2].height = 18
        ws.row_dimensions[3].height = 18

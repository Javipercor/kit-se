"""Builder para crear el Workbook Excel."""

from __future__ import annotations

from typing import cast

from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet

from ..models import InputModel, Layout
from ..styles import Styles
from .header_renderer import HeaderRenderer
from .json_rows_renderer import JsonRowsRenderer
from .table_renderer import TableRenderer


class ExcelReportBuilder:
    """Construye un Workbook Excel a partir de un InputModel."""

    def __init__(self, layout: Layout, styles: Styles) -> None:
        self._layout = layout
        self._styles = styles

    def build(self, model: InputModel) -> Workbook:
        """
        Construye y retorna un Workbook completamente formateado.

        Args:
            model: InputModel con los datos a incluir

        Returns:
            Workbook de openpyxl con el reporte completo
        """
        workbook = Workbook()
        ws = cast(Worksheet, workbook.active)
        ws.title = self._layout.sheet_name

        HeaderRenderer(self._layout, self._styles).render(ws)
        TableRenderer(self._layout, self._styles).render(ws, model)

        renderer = JsonRowsRenderer(self._layout, self._styles)
        renderer.render(ws, model, start_row=self._layout.row_table_subheader)

        return workbook


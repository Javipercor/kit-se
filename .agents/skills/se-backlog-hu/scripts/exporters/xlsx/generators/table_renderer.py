"""Renderer para cabecera y columnas de la tabla principal."""

from __future__ import annotations

from openpyxl.styles import Alignment
from openpyxl.worksheet.worksheet import Worksheet

from ..models import InputModel, Layout
from ..styles import Styles
from ..utils import WorksheetStyler


class TableRenderer:
    """Renderiza la cabecera y estructura de la tabla de datos."""

    def __init__(self, layout: Layout, styles: Styles) -> None:
        self._layout = layout
        self._styles = styles

    def _configure_columns(self, ws: Worksheet) -> None:
        """Configura el ancho de las columnas según el layout."""
        for col in self._layout.columns:
            ws.column_dimensions[col.letter].width = col.width
        ws.column_dimensions["P"].width = self._layout.column_p_width
        ws.column_dimensions["Q"].width = 12
        ws.column_dimensions["R"].width = 12
        ws.column_dimensions["S"].width = 12
        ws.column_dimensions["T"].width = 12
        ws.column_dimensions["U"].width = 12
        ws.column_dimensions["V"].width = 12

    def _render_header_row(self, ws: Worksheet) -> None:
        """Renderiza la fila de headers de la tabla."""
        s = self._styles
        styler = WorksheetStyler(ws, s)
        r = self._layout.row_table_header

        for col in self._layout.columns:
            styler.set_cell(
                f"{col.letter}{r}",
                value=col.header,
                font=s.header_font_white,
                fill=s.fill_header_blue,
                alignment=s.center,
                border=s.thin_border,
            )
        ws.row_dimensions[r].height = 22
    
    def render(self, ws: Worksheet, model: InputModel) -> None:
        """Configura columnas y renderiza headers."""
        self._configure_columns(ws)
        self._render_header_row(ws)
        self._render_summary_headers(ws)
        ws.freeze_panes = f"A{self._layout.row_first_data}"
    
    def _render_summary_headers(self, ws: Worksheet) -> None:
        """Renderiza los headers de resumen (filas 1-2, columnas P-V)."""
        s = self._styles
        styler = WorksheetStyler(ws, s)
        
        # Fila 1: Merge Q1:S1 con "Dev" y T1:V1 con "DS"
        ws.merge_cells("Q1:S1")
        styler.set_cell(
            "Q1",
            value="Dev",
            font=s.header_font_white,
            fill=s.fill_header_blue,
            alignment=s.center,
            border=s.thin_border,
        )
        
        ws.merge_cells("T1:V1")
        styler.set_cell(
            "T1",
            value="DS",
            font=s.header_font_white,
            fill=s.fill_header_blue,
            alignment=s.center,
            border=s.thin_border,
        )
        
        # Fila 2: Headers para cada columna
        headers_row2 = {
            "P2": "Fase",
            "Q2": "Equipo",
            "R2": "Semanas\nHours",
            "S2": "Semanas\nH+Risk",
            "T2": "Equipo",
            "U2": "Semanas\nHours",
            "V2": "Semanas\nH+Risk",
        }
        
        for cell, value in headers_row2.items():
            styler.set_cell(
                cell,
                value=value,
                font=s.header_font_white,
                fill=s.fill_header_blue,
                alignment=Alignment(horizontal="center", vertical="center", wrap_text=True),
                border=s.thin_border,
            )
        
        ws.row_dimensions[1].height = 22
        ws.row_dimensions[2].height = 30

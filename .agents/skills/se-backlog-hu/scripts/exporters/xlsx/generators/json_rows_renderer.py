"""Renderer que convierte el InputModel en filas de Excel."""

from __future__ import annotations

from typing import Optional

from openpyxl.styles import Font
from openpyxl.worksheet.worksheet import Worksheet

from ..config.constants import Env
from ..models import Activity, Block, InputModel, Layout, UserStory
from ..styles import Styles
from ..utils import WorksheetStyler
from ..utils.formulas import (
    average_divided_by_two,
    meeting_hours_formula,
    role_hours_formula,
    subheader_hours_formula,
    subheader_risk_formula,
    hours_with_risk_formula,
    dev_team_hours_formula,
    dev_team_risk_formula,
    ds_team_hours_formula,
    ds_team_risk_formula,
)
from ..utils.height_calc import calculate_height_for_activities_column


def create_meetings_user_story(phase: str, output_row: int) -> UserStory:
    """Crea una historia de usuario sintética para Reuniones (Sprint y Dailies).
    
    Las reuniones definen su fórmula de K (H+Risk) directamente en la Activity.
    """
    activities = [
         Activity(
            name="Tiempo para reuniones (sprint review) 0.75h x semana",
            activity_type="Meeting",
            role="PM",
            level="N3",
            hours=meeting_hours_formula(Env.MEETINGS_SPRINT_HOURS, ["R", "U"], output_row),
            risk=None,
            hours_with_risk_formula=meeting_hours_formula(Env.MEETINGS_SPRINT_HOURS, ["S", "V"], output_row)
        ),
        Activity(
            name="Tiempo para reuniones (sprint review) 0.75h x semana",
            activity_type="Meeting",
            role="ARCHITECT",
            level="N4",
            hours=meeting_hours_formula(Env.MEETINGS_SPRINT_HOURS, ["R"], output_row),
            risk=None,
            hours_with_risk_formula=meeting_hours_formula(Env.MEETINGS_SPRINT_HOURS, ["S"], output_row)
        ),
        Activity(
            name="Tiempo para reuniones (sprint review) 0.75h x semana",
            activity_type="Meeting",
            role="DS",
            level="N4",
            hours=meeting_hours_formula(Env.MEETINGS_SPRINT_HOURS, ["U"], output_row),
            risk=None,
            hours_with_risk_formula=meeting_hours_formula(Env.MEETINGS_SPRINT_HOURS, ["V"], output_row),
        ),
        Activity(
            name="Tiempo para reuniones (dailies, weeklies, etc) 1.25h x semana",
            activity_type="Meeting",
            role="PM",
            level="N3",
            hours=meeting_hours_formula(Env.MEETINGS_DAILY_HOURS, ["R", "U"], output_row),
            risk=None,
            hours_with_risk_formula=meeting_hours_formula(Env.MEETINGS_DAILY_HOURS, ["S", "V"], output_row)
        ),
        Activity(
            name="Tiempo para reuniones (dailies, weeklies, etc) 1.25h x semana",
            activity_type="Meeting",
            role="DEV",
            level="N3",
            hours=meeting_hours_formula(Env.MEETINGS_DAILY_HOURS, ["R"], output_row),
            risk=None,
            hours_with_risk_formula=meeting_hours_formula(Env.MEETINGS_DAILY_HOURS, ["S"], output_row),
        ),
        Activity(
            name="Tiempo para reuniones (dailies, weeklies, etc) 1.25h x semana",
            activity_type="Meeting",
            role="DS",
            level="N3",
            hours=meeting_hours_formula(Env.MEETINGS_DAILY_HOURS, ["U"], output_row),
            risk=None,
            hours_with_risk_formula=meeting_hours_formula(Env.MEETINGS_DAILY_HOURS, ["V"], output_row),
        )
    ]

    blocks = [Block(name="Reuniones", activities=tuple(activities))]
    return UserStory(phase=phase, title=f"Reuniones {phase}", blocks=tuple(blocks))


class JsonRowsRenderer:
    """Convierte InputModel (JSON) en filas Excel."""

    def __init__(self, layout: Layout, styles: Styles) -> None:
        self._layout = layout
        self._styles = styles

    def render(self, ws: Worksheet, model: InputModel, start_row: Optional[int] = None) -> int:
        current_row = start_row if start_row is not None else self._layout.row_first_data
        first_data_row = current_row

        phases_dict: dict[str, list[UserStory]] = {}
        for user_story in model.user_stories:
            phases_dict.setdefault(user_story.phase, []).append(user_story)

        phase_output_row = 3
        phase_index = 0

        for phase, stories in phases_dict.items():
            phase_start_row = current_row
            phase_color = self._styles.fill_row_blue if phase_index % 2 == 0 else self._styles.fill_row_blue_alt

            for user_story in stories:
                current_row = self._render_user_story(ws, current_row, user_story, phase_color)

            phase_end_row = current_row - 1
            self._render_phase_weeks(ws, phase_output_row, phase, phase_start_row, phase_end_row)

            meetings_us = create_meetings_user_story(phase, phase_output_row)
            current_row = self._render_user_story(ws, current_row, meetings_us, phase_color)

            phase_output_row += 1
            phase_index += 1

        last_data_row = current_row - 1
        self._update_average_formula(ws, "I", first_data_row, last_data_row)
        self._update_average_formula(ws, "K", first_data_row, last_data_row)

        return current_row

    def _render_user_story(self, ws: Worksheet, row_index: int, us: UserStory, phase_color=None) -> int:
        if phase_color is None:
            phase_color = self._styles.fill_row_blue

        subheader_row = row_index
        row_index = self._render_subheader_row(ws, row_index, us, phase_color)

        first_data_row = row_index
        row_index = self._render_user_story_activities(ws, row_index, us, phase_color)
        last_data_row = row_index - 1

        styler = WorksheetStyler(ws, self._styles)
        hours_formula = subheader_hours_formula(first_data_row, last_data_row)
        styler.set_cell(
            f"I{subheader_row}",
            value=hours_formula,
            font=Font(name="Calibri", size=9, bold=True, color="FFFFFF"),
            fill=phase_color,
            alignment=self._styles.center,
            border=self._styles.thin_border,
        )

        hours_formula = subheader_risk_formula(first_data_row, last_data_row)
        styler.set_cell(
            f"K{subheader_row}",
            value=hours_formula,
            font=Font(name="Calibri", size=9, bold=True, color="FFFFFF"),
            fill=phase_color,
            alignment=self._styles.center,
            border=self._styles.thin_border,
        )

        return row_index

    def _update_average_formula(self, ws: Worksheet, column: str, first_data_row: int, last_data_row: int) -> None:
        styler = WorksheetStyler(ws, self._styles)
        formula = average_divided_by_two(column, first_data_row, last_data_row)
        styler.set_cell(
            f"{column}{self._layout.row_estimated_by}",
            value=formula,
            font=Font(name="Calibri", size=9),
            alignment=self._styles.center,
            border=self._styles.thin_border,
        )

    def _render_phase_weeks(self, ws: Worksheet, output_row: int, phase: str, first_row: int, last_row: int) -> None:
        styler = WorksheetStyler(ws, self._styles)

        # Columna P: nombre de la fase
        styler.set_cell(
            f"P{output_row}",
            value=phase,
            font=Font(name="Calibri", size=9, bold=True),
            alignment=self._styles.center,
            border=self._styles.thin_border,
        )

        # Dev Team - Columna Q: número "1"
        styler.set_cell(
            f"Q{output_row}",
            value=1,
            font=Font(name="Calibri", size=9),
            alignment=self._styles.center,
            border=self._styles.thin_border,
        )

        # Dev Team - Columna R: suma de horas del equipo Dev
        dev_hours = dev_team_hours_formula(first_row, last_row, output_row)
        styler.set_cell(
            f"R{output_row}",
            value=dev_hours,
            font=Font(name="Calibri", size=9),
            alignment=self._styles.center,
            border=self._styles.thin_border,
            number_format="0.00",
        )

        # Dev Team - Columna S: suma de horas+riesgo del equipo Dev
        dev_risk = dev_team_risk_formula(first_row, last_row, output_row)
        styler.set_cell(
            f"S{output_row}",
            value=dev_risk,
            font=Font(name="Calibri", size=9),
            alignment=self._styles.center,
            border=self._styles.thin_border,
            number_format="0.00",
        )

        # DS Team - Columna T: número "1"
        styler.set_cell(
            f"T{output_row}",
            value=1,
            font=Font(name="Calibri", size=9),
            alignment=self._styles.center,
            border=self._styles.thin_border,
        )

        # DS Team - Columna U: suma de horas del equipo DS
        ds_hours = ds_team_hours_formula(first_row, last_row, output_row)
        styler.set_cell(
            f"U{output_row}",
            value=ds_hours,
            font=Font(name="Calibri", size=9),
            alignment=self._styles.center,
            border=self._styles.thin_border,
            number_format="0.00",
        )

        # DS Team - Columna V: suma de horas+riesgo del equipo DS
        ds_risk = ds_team_risk_formula(first_row, last_row, output_row)
        styler.set_cell(
            f"V{output_row}",
            value=ds_risk,
            font=Font(name="Calibri", size=9),
            alignment=self._styles.center,
            border=self._styles.thin_border,
            number_format="0.00",
        )

    def _render_subheader_row(self, ws: Worksheet, row_index: int, us: UserStory, phase_color=None) -> int:
        if phase_color is None:
            phase_color = self._styles.fill_row_blue

        s = self._styles
        styler = WorksheetStyler(ws, s)
        r = row_index

        styler.apply_range(
            f"A{r}:N{r}",
            font=Font(name="Calibri", size=9, bold=True, color="FFFFFF"),
            fill=phase_color,
            border=s.thin_border,
        )

        styler.apply_range(f"A{r}:B{r}", alignment=s.left)
        styler.apply_range(f"C{r}:N{r}", alignment=s.center)

        user_story_title = us.title

        values = {
            f"A{r}": us.phase,
            f"B{r}": user_story_title,
            f"D{r}": user_story_title,
            f"E{r}": Env.ACTIVITY_TYPE_LABEL,
            f"F{r}": Env.ROLE_LABEL,
            f"G{r}": Env.LEVEL_LABEL,
            f"I{r}": 0,
            f"J{r}": Env.RISK_LABEL,
            f"K{r}": 0,
            f"L{r}": Env.APPROACH_LABEL,
            f"M{r}": Env.RISK_NOTES_LABEL,
            f"N{r}": Env.PERCENT_PLACEHOLDER,
        }
        for addr, value in values.items():
            styler.set_cell(addr, value=value)

        ws.row_dimensions[r].height = calculate_height_for_activities_column(user_story_title)
        return row_index + 1

    def _render_data_row(
        self,
        ws: Worksheet,
        row_index: int,
        us: UserStory,
        block: Block,
        activity_name: str,
        activity_type: str,
        role: str,
        level: str,
        percent: str | object,
        hours: int | str | object,
        risk: int | None,
        hours_with_risk_formula_str: str | object,
        phase_color=None,
    ) -> None:
        """Método auxiliar para renderizar una fila de datos con la estructura común."""
        if phase_color is None:
            phase_color = self._styles.fill_row_blue

        s = self._styles
        styler = WorksheetStyler(ws, s)

        # Columnas A y B: fase y título de US
        for col_letter in ("A", "B"):
            styler.set_cell(
                f"{col_letter}{row_index}",
                value=us.phase if col_letter == "A" else us.title,
                font=Font(name="Calibri", size=9, color="FFFFFF"),
                fill=phase_color,
                alignment=s.left_no_wrap,
                border=s.thin_border,
            )

        # Columna C: nombre del bloque
        styler.set_cell(
            f"C{row_index}",
            value=block.name,
            font=Font(name="Calibri", size=9),
            fill=s.fill_block_light,
            alignment=s.left,
            border=s.thin_border,
        )

        # Columnas D-N: datos de la actividad
        mapping: dict[str, object] = {
            f"D{row_index}": activity_name,
            f"E{row_index}": activity_type,
            f"F{row_index}": role,
            f"G{row_index}": level,
            f"H{row_index}": percent,
            f"I{row_index}": hours,
            f"J{row_index}": risk,
            f"K{row_index}": hours_with_risk_formula_str,
            f"L{row_index}": "",
            f"M{row_index}": "",
            f"N{row_index}": "",
        }

        for addr, value in mapping.items():
            col_letter = addr[0]
            alignment = s.center if col_letter in ("E", "F", "G", "H", "I", "J", "K", "N") else s.left
            styler.set_cell(
                addr,
                value=value,
                font=Font(name="Calibri", size=9),
                fill=s.fill_white,
                alignment=alignment,
                border=s.thin_border,
            )

        styler.set_cell(f"I{row_index}", number_format="0.00")
        styler.set_cell(f"J{row_index}", number_format="0")
        styler.set_cell(f"K{row_index}", number_format="0.00")

        ws.row_dimensions[row_index].height = calculate_height_for_activities_column(activity_name)

    def _render_user_story_activities(self, ws: Worksheet, row_index: int, us: UserStory, phase_color=None) -> int:
        if phase_color is None:
            phase_color = self._styles.fill_row_blue

        s = self._styles
        styler = WorksheetStyler(ws, s)

        for block in us.blocks:
            for col_letter in ("A", "B"):
                styler.set_cell(
                    f"{col_letter}{row_index}",
                    value=us.phase if col_letter == "A" else us.title,
                    font=Font(name="Calibri", size=9, color="FFFFFF"),
                    fill=phase_color,
                    alignment=s.left_no_wrap,
                    border=s.thin_border,
                )

            for col_letter in ("C", "D"):
                styler.set_cell(
                    f"{col_letter}{row_index}",
                    value=block.name,
                    font=Font(name="Calibri", size=9),
                    fill=s.fill_block_light,
                    alignment=s.left,
                    border=s.thin_border,
                )

            for col_letter in ("E", "F", "G", "H", "I", "J", "K", "L", "M", "N"):
                styler.set_cell(
                    f"{col_letter}{row_index}",
                    value="",
                    font=Font(name="Calibri", size=9),
                    fill=s.fill_block_light,
                    alignment=s.center,
                    border=s.thin_border,
                )

            ws.row_dimensions[row_index].height = 16
            row_index += 1

            for act in block.activities:
                # Usar la fórmula K definida en la Activity, o calcular la estándar
                k_formula = act.hours_with_risk_formula if act.hours_with_risk_formula is not None else hours_with_risk_formula(f"I{row_index}", f"J{row_index}")
                
                self._render_data_row(
                    ws,
                    row_index,
                    us,
                    block,
                    activity_name=act.name,
                    activity_type=act.activity_type,
                    role=act.role,
                    level=act.level,
                    percent="",
                    hours=act.hours,
                    risk=act.risk,
                    hours_with_risk_formula_str=k_formula,
                    phase_color=phase_color,
                )
                row_index += 1

            if block.activities:
                last_act = block.activities[-1]
                activities_start_row = row_index - len(block.activities)
                activities_end_row = row_index - 1

                should_exclude = any(keyword in us.title for keyword in Env.EXCLUDED_ROLE_KEYWORDS)

                if not should_exclude:
                    self._render_data_row(
                        ws, row_index, us, block,
                        activity_name="Testing (Unit)",
                        activity_type="Testing",
                        role=last_act.role,
                        level="N2",
                        percent=f"={Env.PERCENT_TESTING_UNIT}",
                        hours=role_hours_formula(activities_start_row, activities_end_row, Env.PERCENT_TESTING_UNIT),
                        risk=0,
                        hours_with_risk_formula_str=hours_with_risk_formula(f"I{row_index}", f"J{row_index}"),
                        phase_color=phase_color,
                    )
                    row_index += 1
                    
                    self._render_data_row(
                        ws, row_index, us, block,
                        activity_name="Testing (End to End, Plan de pruebas)",
                        activity_type="Testing",
                        role="QA",
                        level="N2",
                        percent=f"={Env.PERCENT_TESTING_E2E}",
                        hours=role_hours_formula(activities_start_row, activities_end_row, Env.PERCENT_TESTING_E2E),
                        risk=0,
                        hours_with_risk_formula_str=hours_with_risk_formula(f"I{row_index}", f"J{row_index}"),
                        phase_color=phase_color,
                    )
                    row_index += 1
                    
                    self._render_data_row(
                        ws, row_index, us, block,
                        activity_name="DevOps Assistance",
                        activity_type="Assistance",
                        role="DEVOPS",
                        level="N3",
                        percent=f"={Env.PERCENT_DEVOPS}",
                        hours=role_hours_formula(activities_start_row, activities_end_row, Env.PERCENT_DEVOPS),
                        risk=0,
                        hours_with_risk_formula_str=hours_with_risk_formula(f"I{row_index}", f"J{row_index}"),
                        phase_color=phase_color,
                    )
                    row_index += 1

                # No añadir Scrum Master para el bloque de Reuniones
                if block.name != "Reuniones":
                    self._render_data_row(
                        ws, row_index, us, block,
                        activity_name="Scrum Master",
                        activity_type="Management",
                        role="PM",
                        level="N3",
                        percent=f"={Env.PERCENT_PM}",
                        hours=role_hours_formula(activities_start_row, activities_end_row, Env.PERCENT_PM),
                        risk=0,
                        hours_with_risk_formula_str=hours_with_risk_formula(f"I{row_index}", f"J{row_index}"),
                        phase_color=phase_color,
                    )
                    row_index += 1

        return row_index

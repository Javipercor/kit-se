"""Parser y reglas del contrato de backlog (proposal/6.0-backlog.md)."""
from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

H1 = "# Backlog técnico-funcional"
H2_CAT = "## Catálogo preliminar de épicas y HUs"
H2_DET = "## Backlog detallado"
H2_SUM = "## Resumen de esfuerzo (control de consistencia)"
H5_ORDER = ["Enfoque técnico", "Criterios de aceptación", "Dependencias", "Tareas"]

EPIC_RE = re.compile(r"^### EPIC (\d+) - (.+?)\s*$")
HU_RE = re.compile(r"^#### HU (\d+)\.(\d+) - (.+?)\s*$")
H5_RE = re.compile(r"^##### (.+?)\s*$")
STORY_RE = re.compile(r"^\**Como\**\s+(.+?),\s*\**quiero\**\s+(.+?),\s*\**para\**\s+(.+?)\s*$", re.I)
PHASE_RE = re.compile(r"^[*-] \*\*(Fase .+?)\*\*\s*$")
ROLE_RE = re.compile(r"^[*-] \*\*(.+?)\*\*\s*$")
TASK_RE = re.compile(r"^\s{2,}[*-] (.+?) \*\*(\d+)h, (N[1-4])\*\*\s*$")
BULLET_RE = re.compile(r"^[*-] \S")

DEFAULT_CFG = {
    "roles": ["Architect", "Backend", "Frontend", "DS", "DataEng", "DevOps", "UI/UX", "QA"],
    "devops_only_roles": ["DevOps"],
    "forbidden_story_roles": ["arquitecto", "backend", "frontend", "devops", "qa", "desarrollador", "developer", "sistema"],
    "min_criteria": 3, "max_criteria": 7, "min_hours": 1, "max_hours": 16,
    "fixed_epics": {"first": "Arquitectura", "penultimate": "DevOps", "last": "Documentacion y Entregables"},
}


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    return re.sub(r"\s+", " ", "".join(c for c in s if not unicodedata.combining(c))).strip().lower()


def load_config(start: Path) -> dict:
    for d in [start.resolve(), *start.resolve().parents]:
        f = d / "se.config.json"
        if f.is_file():
            return {**DEFAULT_CFG, **json.loads(f.read_text(encoding="utf-8")).get("backlog", {})}
    return DEFAULT_CFG


@dataclass
class Task:
    role: str
    text: str
    hours: int
    level: str
    line: int


@dataclass
class HU:
    epic: int
    num: int
    title: str
    line: int
    body: list = field(default_factory=list)          # (lineno, text) antes de H5
    subs: dict = field(default_factory=dict)          # nombre -> [(lineno, text)]
    sub_order: list = field(default_factory=list)
    story: str | None = None
    actor: str | None = None
    phase: str | None = None
    tasks: list = field(default_factory=list)

    @property
    def placeholder(self) -> bool:
        return norm(self.title) == "no aplica"

    @property
    def hours(self) -> int:
        return sum(t.hours for t in self.tasks)


@dataclass
class Epic:
    num: int
    title: str
    line: int
    hus: list = field(default_factory=list)

    @property
    def hours(self) -> int:
        return sum(h.hours for h in self.hus)


def split_sections(lines: list[str]) -> dict:
    """Devuelve {heading_h2: [(lineno, text)]} y la lista ordenada de H2."""
    sections, order, cur = {}, [], None
    for i, l in enumerate(lines, 1):
        if l.startswith("## ") and not l.startswith("### "):
            cur = l.rstrip()
            order.append((cur, i))
            sections[cur] = []
        elif cur:
            sections[cur].append((i, l.rstrip("\n")))
    return {"sections": sections, "order": order}


def parse_epics(section: list, errors: list, label: str) -> list[Epic]:
    epics: list[Epic] = []
    hu = None
    sub = None
    for n, l in section:
        if m := EPIC_RE.match(l):
            epics.append(Epic(int(m[1]), m[2], n))
            hu, sub = None, None
        elif m := HU_RE.match(l):
            if not epics:
                errors.append(f"[{label}] L{n}: HU fuera de una EPIC")
                continue
            hu = HU(int(m[1]), int(m[2]), m[3], n)
            epics[-1].hus.append(hu)
            sub = None
        elif m := H5_RE.match(l):
            if not hu:
                errors.append(f"[{label}] L{n}: subsección fuera de una HU")
                continue
            sub = m[1]
            hu.subs[sub] = []
            hu.sub_order.append(sub)
        elif l.startswith("#"):
            errors.append(f"[{label}] L{n}: heading no permitido '{l[:60]}'")
        elif hu is None:
            if l.strip() and epics:
                pass  # descripción breve de EPIC permitida
            elif l.strip():
                errors.append(f"[{label}] L{n}: texto fuera de EPIC/HU")
        elif sub is None:
            hu.body.append((n, l))
        else:
            hu.subs[sub].append((n, l))
    for e in epics:
        for h in e.hus:
            content = [(n, t) for n, t in h.body if t.strip()]
            for n, t in content:
                if (m := STORY_RE.match(t)) and h.story is None:
                    h.story, h.actor = t.strip(), m[1].strip("* ")
                elif (m := PHASE_RE.match(t)):
                    if h.phase:
                        errors.append(f"[{label}] HU {h.epic}.{h.num}: más de una fase")
                    h.phase = m[1]
                elif h.placeholder and h.story is None:
                    h.story = t.strip()
                else:
                    errors.append(f"[{label}] L{n}: línea no reconocida en HU {h.epic}.{h.num}: '{t[:60]}'")
    return epics


def parse_tasks(h: HU, cfg: dict, errors: list) -> None:
    role = None
    for n, t in h.subs.get("Tareas", []):
        if not t.strip():
            continue
        if (m := TASK_RE.match(t)):
            if role is None:
                errors.append(f"L{n}: tarea sin rol en HU {h.epic}.{h.num}")
                continue
            h.tasks.append(Task(role, m[1], int(m[2]), m[3], n))
        elif (m := ROLE_RE.match(t)):
            role = m[1]
            if role not in cfg["roles"]:
                errors.append(f"L{n}: rol '{role}' no permitido (permitidos: {', '.join(cfg['roles'])})")
        else:
            errors.append(f"L{n}: línea de tareas inválida en HU {h.epic}.{h.num}: '{t.strip()[:60]}' "
                          "(formato: '* **Rol**' y '  * Descripción **8h, N2**')")


def render_summary(epics: list[Epic], roles: list[str]) -> str:
    total = sum(e.hours for e in epics)
    by_role = {r: 0 for r in roles}
    for e in epics:
        for h in e.hus:
            for t in h.tasks:
                by_role[t.role] = by_role.get(t.role, 0) + t.hours
    out = [H2_SUM, "", "### Total global", "", f"* **Total: {total}h**"]
    out += [f"* {r}: {v}h" for r, v in by_role.items() if v]
    out += ["", "### Horas por épica, HU y rol", ""]
    for e in epics:
        out.append(f"* **EPIC {e.num} - {e.title}: {e.hours}h**")
        for h in e.hus:
            hr = {}
            for t in h.tasks:
                hr[t.role] = hr.get(t.role, 0) + t.hours
            parts = ", ".join(f"{r} {v}h" for r, v in hr.items())
            out.append(f"  * HU {h.epic}.{h.num} - {h.title}: {h.hours}h" + (f" ({parts})" if parts else ""))
    return "\n".join(out) + "\n"

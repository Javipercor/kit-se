"""Utilidades comunes de requisitos: configuración, registro, matriz y HUs."""
from __future__ import annotations

import json
import re
from pathlib import Path

DEFAULT = {
    "id_pattern": r"^RQ-\d{3}$",
    "inline_id_regex": r"\b(?:RQ-HU-\d{3}|RQ-\d{3})\b",
    "types": {"funcional": ["Funcional"],
              "tecnico": ["No funcional", "Datos", "IA/Analítica", "Integración", "Seguridad", "Privacidad",
                          "Infraestructura", "Operación", "Calidad/Testing", "Restricción tecnológica"],
              "otros": ["Contractual/Entregable", "Gestión"]},
    "coverage_required": ["funcional", "tecnico"],
    "states": ["Evidenciado", "Inferido", "A confirmar", "Fuera de alcance"],
    "priorities": ["Obligatorio", "Deseable", "Opcional", "A confirmar"],
    "chunk_lines": 80,
    "dedupe": {"backend": "lexico", "lexico": {"alta": 0.8, "revisar": 0.5},
               "max_rq_por_capacidad": 8, "max_capacidades_por_hu": 2},
}
HU_HEAD = re.compile(r"^### (HU-[A-Z][A-Z0-9]{1,5}-\d{2})\. (.+?)\s*$")
REQ_LINE = re.compile(r"^\*\*Requisitos:\*\*\s+(.+?)\s*$")
TRANS_LINE = re.compile(r"^\*\*Requisitos transversales:\*\*\s+(.+?)\s*$")


def load_config(start: Path) -> dict:
    for d in [start.resolve(), *start.resolve().parents]:
        f = d / "se.config.json"
        if f.is_file():
            return {**DEFAULT, **json.loads(f.read_text(encoding="utf-8")).get("requirements", {})}
    return DEFAULT


def all_types(cfg: dict) -> list[str]:
    return [t for ts in cfg["types"].values() for t in ts]


def category(cfg: dict, tipo: str) -> str | None:
    for cat, ts in cfg["types"].items():
        if tipo in ts:
            return cat
    return None


def registry_path(opp: Path) -> Path:
    return opp / "proposal/_meta/registro-requisitos.json"


def load_registry(opp: Path) -> dict:
    reg = registry_path(opp)
    if not reg.exists():
        return {"requisitos": [], "capacidades": [], "descartados": [], "decisiones": []}
    data = json.loads(reg.read_text(encoding="utf-8"))
    for k in ("requisitos", "capacidades", "descartados", "decisiones"):
        data.setdefault(k, [])
    return data


def load_requirements(opp: Path) -> tuple[list[dict], str]:
    """Devuelve requisitos y su origen: registro JSON o, en su defecto, la matriz Markdown."""
    reg = registry_path(opp)
    if reg.exists():
        return json.loads(reg.read_text(encoding="utf-8")).get("requisitos", []), "registro"
    matrix = opp / "proposal/2-requirements-matrix.md"
    if not matrix.exists():
        return [], "ninguno"
    rows, header = [], None
    for line in matrix.read_text(encoding="utf-8").splitlines():
        if not line.strip().startswith("|"):
            header = None if not line.strip() else header
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if header is None:
            header = [c.lower() for c in cells]
            continue
        if set(cells[0]) <= {"-", ":", " "}:
            continue
        if "id" in header and "tipo" in header:
            r = dict(zip(header, cells))
            rows.append({"id": r.get("id", "").strip("`"), "texto": r.get("requisito", ""), "tipo": r.get("tipo", ""),
                         "estado": r.get("estado", ""), "motivo_exclusion": r.get("notas / riesgo", "")})
    return [r for r in rows if r["id"]], "matriz"


def section2(text: str) -> list[str]:
    lines = text.splitlines()
    start = next((i for i, l in enumerate(lines) if re.match(r"^## 2\. ", l)), None)
    if start is None:
        return []
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    return lines[start + 1:end]


def hu_links(text: str, cfg: dict) -> tuple[dict[str, list[str]], list[str]]:
    """HU -> IDs de requisitos y lista de requisitos transversales de la sección 2."""
    rx = re.compile(cfg["inline_id_regex"])
    hus, trans, cur = {}, [], None
    for l in section2(text):
        s = l.strip()
        if m := TRANS_LINE.match(s):
            trans += rx.findall(m[1])
        elif m := HU_HEAD.match(l):
            cur = m[1]
            hus[cur] = []
        elif cur and (m := REQ_LINE.match(s)):
            hus[cur] += rx.findall(m[1])
    return hus, trans

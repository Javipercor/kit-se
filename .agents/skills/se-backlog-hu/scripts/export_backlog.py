#!/usr/bin/env python3
"""Exporta proposal/6.0-backlog.md a Azure DevOps (CSV) y al Excel de horas, sin LLM.

Uso: uv run --group se export_backlog.py [--formato todos|json|ado|xlsx] [--backlog RUTA] [--salida DIR]

El backlog se lee con el mismo parser que valida el contrato (backlog_lib), así que la
conversión es determinista: no hace falta pasar por PDF ni por Azure AI Foundry.

Genera en `--salida` (por defecto se.config.json → exportacion.salida = proposal/exports):
  backlog-ado.json         contrato canónico de tools/backlog_to_ado (features → user_stories → tasks)
  backlog-ado-import.csv   CSV de importación de Azure DevOps Boards
  backlog-xlsx.json        contrato canónico de tools/backlog_to_xlsx (userStories → blocks → activities)
  backlog-horas.xlsx       Excel de horas con fórmulas y estilos del equipo

Los mapeos rol del kit → perfil ADO, bloque, tipo de actividad, rol Excel y riesgo por nivel
están en se.config.json → exportacion. Exit 1 si el backlog no es válido o un mapeo produce
un valor que el contrato de destino no admite.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from backlog_lib import H2_DET, load_config, norm, parse_epics, parse_tasks, split_sections  # noqa: E402

DEFAULT_EXPORT = {"salida": "proposal/exports", "ado_perfil_por_rol": {}, "xlsx_bloque_por_rol": {},
                  "xlsx_tipo_por_rol": {}, "xlsx_rol_por_rol": {}, "xlsx_riesgo_por_nivel": {},
                  "xlsx_epica_documentacion": {"bloque": "Documentación", "tipo": "Documents"}}


def export_config(root: Path) -> tuple[dict, dict]:
    for d in [root.resolve(), *root.resolve().parents]:
        f = d / "se.config.json"
        if f.is_file():
            data = json.loads(f.read_text(encoding="utf-8"))
            return {**DEFAULT_EXPORT, **data.get("exportacion", {})}, data.get("backlog", {})
    return DEFAULT_EXPORT, {}


def enums(schema_path: Path) -> dict:
    """Valores admitidos por los esquemas de destino."""
    s = json.loads(schema_path.read_text(encoding="utf-8"))
    out = {}

    def walk(node, key=""):
        if isinstance(node, dict):
            if "enum" in node:
                out[key] = node["enum"]
            for k, v in node.items():
                walk(v, k if k not in ("items", "properties") else key)
        elif isinstance(node, list):
            for v in node:
                walk(v, key)
    walk(s)
    return out


def section_lines(h, name: str) -> list[str]:
    return [t.strip() for _, t in h.subs.get(name, []) if t.strip()]


def bullets(lines: list[str]) -> list[str]:
    return [l[2:].strip() for l in lines if l[:2] in ("* ", "- ")]


def load_epics(path: Path) -> tuple[list, list[str]]:
    cfg = load_config(path.parent)
    sp = split_sections(path.read_text(encoding="utf-8").splitlines())
    if H2_DET not in sp["sections"]:
        return [], ["no hay backlog detallado (## Backlog detallado): ejecuta antes la etapa 'continuar'"]
    errors: list[str] = []
    epics = parse_epics(sp["sections"][H2_DET], errors, "detalle")
    for e in epics:
        for h in e.hus:
            parse_tasks(h, cfg, errors)
    return epics, errors


def to_ado(epics: list, exp: dict, allowed: dict) -> tuple[dict, list[str]]:
    errs, features = [], []
    profiles = allowed.get("profile", [])
    for e in epics:
        stories = []
        for h in e.hus:
            if h.placeholder:
                continue
            desc = "\n\n".join(x for x in [h.story or "", " ".join(section_lines(h, "Enfoque técnico"))] if x)
            tasks = []
            for t in h.tasks:
                prof = exp["ado_perfil_por_rol"].get(t.role, "General")
                if profiles and prof not in profiles:
                    errs.append(f"rol {t.role} → perfil ADO '{prof}' no admitido ({', '.join(profiles)})")
                tasks.append({"title": t.text[:250], "description": f"{t.text} · {t.hours}h · {t.level} · {t.role}",
                              "profile": prof})
            stories.append({"title": f"HU {h.epic}.{h.num} - {h.title}", "description": desc,
                            "acceptance_criteria": bullets(section_lines(h, "Criterios de aceptación")), "tasks": tasks})
        features.append({"title": f"EPIC {e.num} - {e.title}", "description": "", "user_stories": stories})
    return {"features": features}, errs


def to_xlsx(epics: list, exp: dict, backlog_cfg: dict, allowed: dict) -> tuple[dict, list[str]]:
    errs, out = [], []
    doc_epic = norm(backlog_cfg.get("fixed_epics", {}).get("last", "Documentacion y Entregables"))
    default_phase = backlog_cfg.get("default_phase", "Fase única")
    block_order = allowed.get("name", [])
    for e in epics:
        is_doc = norm(e.title) == doc_epic
        for h in e.hus:
            if h.placeholder:
                continue
            blocks: dict[str, list] = {}
            for t in h.tasks:
                if is_doc:
                    block, atype = exp["xlsx_epica_documentacion"]["bloque"], exp["xlsx_epica_documentacion"]["tipo"]
                else:
                    block = exp["xlsx_bloque_por_rol"].get(t.role, "Backend")
                    atype = exp["xlsx_tipo_por_rol"].get(t.role, "Backend")
                role = exp["xlsx_rol_por_rol"].get(t.role, "DEV")
                risk = int(exp["xlsx_riesgo_por_nivel"].get(t.level, 0))
                for field, value in (("name", block), ("activityType", atype), ("role", role), ("level", t.level)):
                    if allowed.get(field) and value not in allowed[field]:
                        errs.append(f"HU {h.epic}.{h.num}: {field} '{value}' no admitido por el Excel ({', '.join(allowed[field])})")
                blocks.setdefault(block, []).append({"name": t.text, "activityType": atype, "role": role,
                                                     "level": t.level, "hours": t.hours, "risk": risk})
            ordered = sorted(blocks.items(), key=lambda kv: block_order.index(kv[0]) if kv[0] in block_order else 99)
            out.append({"phase": h.phase or default_phase, "title": f"{h.epic}.{h.num}. {h.title}",
                        "blocks": [{"name": b, "activities": a} for b, a in ordered]})
    return {"userStories": out}, errs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--formato", choices=["todos", "json", "ado", "xlsx"], default="todos")
    ap.add_argument("--backlog", default="proposal/6.0-backlog.md")
    ap.add_argument("--salida")
    a = ap.parse_args()
    path = Path(a.backlog)
    if not path.exists():
        print(f"KO: no existe {path}")
        return 1
    exp, backlog_cfg = export_config(path.parent)
    out = Path(a.salida or exp["salida"])
    epics, errors = load_epics(path)
    if errors:
        print("KO backlog no válido para exportar:")
        for e in errors:
            print(f"  - {e}")
        return 1
    ado_json, e1 = to_ado(epics, exp, enums(HERE / "exporters/ado/schema.json"))
    xlsx_json, e2 = to_xlsx(epics, exp, backlog_cfg, enums(HERE / "exporters/xlsx/schema.json"))
    if e1 + e2:
        print("KO mapeos no válidos (revisa se.config.json → exportacion):")
        for e in sorted(set(e1 + e2)):
            print(f"  - {e}")
        return 1
    out.mkdir(parents=True, exist_ok=True)
    written = []
    if a.formato in ("todos", "json", "ado"):
        (out / "backlog-ado.json").write_text(json.dumps(ado_json, ensure_ascii=False, indent=2), encoding="utf-8")
        written.append("backlog-ado.json")
    if a.formato in ("todos", "json", "xlsx"):
        (out / "backlog-xlsx.json").write_text(json.dumps(xlsx_json, ensure_ascii=False, indent=2), encoding="utf-8")
        written.append("backlog-xlsx.json")
    if a.formato in ("todos", "ado"):
        from exporters.ado import AdoCsvExporter, BacklogJsonLoader
        model = BacklogJsonLoader().load_from_dict(ado_json)
        summary = AdoCsvExporter().export(model, out / "backlog-ado-import.csv")
        written.append(f"backlog-ado-import.csv ({summary.row_count} filas)")
    if a.formato in ("todos", "xlsx"):
        try:
            from exporters.xlsx.generators import ExcelReportBuilder
            from exporters.xlsx.models import Layout
            from exporters.xlsx.styles import StyleFactory
            from exporters.xlsx.utils import InputJsonLoader
        except ModuleNotFoundError as exc:
            print(f"KO: falta {exc.name} en el entorno (ejecuta /se-init)")
            return 1
        tmp = out / "backlog-xlsx.json"
        if not tmp.exists():
            tmp.write_text(json.dumps(xlsx_json, ensure_ascii=False, indent=2), encoding="utf-8")
        model = InputJsonLoader().load(tmp)
        ExcelReportBuilder(Layout(), StyleFactory.create()).build(model).save(out / "backlog-horas.xlsx")
        written.append("backlog-horas.xlsx")
    total = sum(t.hours for e in epics for h in e.hus for t in h.tasks)
    print(f"OK exportado en {out}: {', '.join(written)} · {sum(len(e.hus) for e in epics)} HUs · {total}h")
    return 0


if __name__ == "__main__":
    sys.exit(main())

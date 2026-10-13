#!/usr/bin/env python3
"""Valida proposal/6.0-backlog.md contra el contrato del kit.

Uso: uv run --group se validate_backlog.py <6.0-backlog.md> [--require-final] [--require-summary]
  sin flags         : catálogo preliminar válido (y detalle/resumen si existen)
  --require-final   : exige backlog detallado completo
  --require-summary : exige resumen y que coincida con las tareas
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from backlog_lib import (H1, H2_CAT, H2_DET, H2_SUM, H5_ORDER, BULLET_RE, load_config, norm,  # noqa: E402
                         parse_epics, parse_tasks, render_summary, split_sections)


def check_structure(epics, cfg, label, errors):
    if not epics:
        errors.append(f"[{label}] sin EPICs")
        return
    for i, e in enumerate(epics, 1):
        if e.num != i:
            errors.append(f"[{label}] EPIC {e.num} debería ser EPIC {i}")
        for j, h in enumerate(e.hus, 1):
            if h.epic != e.num or h.num != j:
                errors.append(f"[{label}] HU {h.epic}.{h.num} debería ser HU {e.num}.{j}")
        if not e.hus:
            errors.append(f"[{label}] EPIC {e.num} sin HUs")
    fx = cfg["fixed_epics"]
    if norm(epics[0].title) != norm(fx["first"]):
        errors.append(f"[{label}] la primera EPIC debe ser '{fx['first']}'")
    if len(epics) >= 3:
        if norm(epics[-2].title) != norm(fx["penultimate"]):
            errors.append(f"[{label}] la penúltima EPIC debe ser '{fx['penultimate']}'")
        if norm(epics[-1].title) != norm(fx["last"]):
            errors.append(f"[{label}] la última EPIC debe ser '{fx['last']}'")
    else:
        errors.append(f"[{label}] se requieren al menos las 3 EPICs estructurales")
    fixed = {norm(fx["first"]), norm(fx["penultimate"]), norm(fx["last"])}
    forbidden = [norm(r) for r in cfg["forbidden_story_roles"]]
    seen_titles = {}
    for e in epics:
        for h in e.hus:
            tag = f"[{label}] HU {h.epic}.{h.num}"
            if h.placeholder:
                if norm(e.title) not in fixed:
                    errors.append(f"{tag}: 'No aplica' solo se permite en EPICs estructurales")
                if len(e.hus) > 1:
                    errors.append(f"{tag}: una EPIC con 'No aplica' no puede tener más HUs")
                continue
            if not h.story:
                errors.append(f"{tag}: falta historia 'Como <rol>, quiero <x>, para <y>.'")
            elif h.actor:
                a = f" {norm(h.actor)} "
                bad = [r for r in forbidden if f" {r} " in a]
                if bad:
                    errors.append(f"{tag}: rol técnico en la historia ('{h.actor}')")
            if not h.phase:
                errors.append(f"{tag}: falta bullet de fase '* **Fase ...**'")
            key = norm(h.title)
            if key in seen_titles:
                errors.append(f"{tag}: título duplicado con HU {seen_titles[key]}")
            seen_titles[key] = f"{h.epic}.{h.num}"


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) > 1:
        print(__doc__)
        return 2
    path = Path(args[0] if args else "proposal/6.0-backlog.md")
    req_final = "--require-final" in sys.argv or "--require-summary" in sys.argv
    req_sum = "--require-summary" in sys.argv
    cfg = load_config(path.parent)
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    errors: list[str] = []

    if not lines or lines[0].strip() != H1:
        errors.append(f"La primera línea debe ser '{H1}'")
    for i, l in enumerate(lines, 1):
        if l.lstrip().startswith("|"):
            errors.append(f"L{i}: tablas no permitidas")
        if l.lstrip().startswith("```"):
            errors.append(f"L{i}: bloques de código no permitidos")
        if "<!--" in l:
            errors.append(f"L{i}: comentarios no permitidos")
    sp = split_sections(lines)
    order = [h for h, _ in sp["order"]]
    allowed = [H2_CAT, H2_DET, H2_SUM]
    for h in order:
        if h not in allowed:
            errors.append(f"H2 no permitido: '{h}'")
    present = [h for h in allowed if h in order]
    if [h for h in order if h in allowed] != present:
        errors.append("Orden de secciones H2 incorrecto")
    if H2_CAT not in order:
        errors.append(f"Falta '{H2_CAT}'")
        return report(path, errors)

    cat = parse_epics(sp["sections"][H2_CAT], errors, "catálogo")
    check_structure(cat, cfg, "catálogo", errors)
    for e in cat:
        for h in e.hus:
            if h.subs:
                errors.append(f"[catálogo] HU {h.epic}.{h.num}: el catálogo no admite subsecciones")

    det = None
    if H2_DET in order:
        det = parse_epics(sp["sections"][H2_DET], errors, "detalle")
        check_structure(det, cfg, "detalle", errors)
        sig = lambda eps: [(e.num, e.title, [(h.num, h.title, h.story, h.phase) for h in e.hus]) for e in eps]
        if sig(cat) != sig(det):
            errors.append("El detalle no replica exactamente EPICs, HUs, historias y fases del catálogo")
        devops_title = norm(cfg["fixed_epics"]["penultimate"])
        for e in det:
            for h in e.hus:
                tag = f"[detalle] HU {h.epic}.{h.num}"
                if h.placeholder:
                    if h.subs:
                        errors.append(f"{tag}: un placeholder 'No aplica' no lleva subsecciones")
                    continue
                for s in h.sub_order:
                    if s not in H5_ORDER:
                        errors.append(f"{tag}: subsección no permitida '{s}'")
                known = [s for s in h.sub_order if s in H5_ORDER]
                if known != sorted(known, key=H5_ORDER.index):
                    errors.append(f"{tag}: subsecciones fuera de orden ({' → '.join(H5_ORDER)})")
                for req in ("Criterios de aceptación", "Tareas"):
                    if req not in h.subs:
                        errors.append(f"{tag}: falta '##### {req}'")
                crit = [t for _, t in h.subs.get("Criterios de aceptación", []) if BULLET_RE.match(t)]
                if "Criterios de aceptación" in h.subs and not cfg["min_criteria"] <= len(crit) <= cfg["max_criteria"]:
                    errors.append(f"{tag}: {len(crit)} criterios (rango {cfg['min_criteria']}-{cfg['max_criteria']})")
                if "Dependencias" in h.subs and not any(t.strip() for _, t in h.subs["Dependencias"]):
                    errors.append(f"{tag}: '##### Dependencias' vacía (elimínala si no hay dependencias reales)")
                parse_tasks(h, cfg, errors)
                if "Tareas" in h.subs and not h.tasks:
                    errors.append(f"{tag}: sin tareas")
                for t in h.tasks:
                    if not cfg["min_hours"] <= t.hours <= cfg["max_hours"]:
                        errors.append(f"L{t.line}: {t.hours}h fuera de rango {cfg['min_hours']}-{cfg['max_hours']}h")
                    if t.role in cfg["devops_only_roles"] and norm(e.title) != devops_title:
                        errors.append(f"L{t.line}: tareas '{t.role}' solo en la EPIC '{cfg['fixed_epics']['penultimate']}'")
    elif req_final:
        errors.append(f"Falta '{H2_DET}' (requerido por --require-final)")

    if H2_SUM in order:
        if det is None:
            errors.append("Hay resumen sin backlog detallado")
        else:
            current = "\n".join([H2_SUM] + [t for _, t in sp["sections"][H2_SUM]]).strip()
            expected = render_summary(det, cfg["roles"]).strip()
            if [l.strip() for l in current.splitlines() if l.strip()] != [l.strip() for l in expected.splitlines() if l.strip()]:
                errors.append("El resumen no coincide con las tareas: regenera con effort_summary.py --write")
    elif req_sum:
        errors.append(f"Falta '{H2_SUM}' (requerido por --require-summary)")

    return report(path, errors, det)


def report(path, errors, det=None) -> int:
    if errors:
        print(f"KO {path}")
        for e in errors:
            print(f"  - {e}")
        return 1
    stage = "catálogo preliminar" if det is None else "backlog detallado"
    print(f"OK {path} ({stage})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

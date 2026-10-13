#!/usr/bin/env python3
"""Calcula el resumen de esfuerzo a partir de las tareas del backlog detallado.

Uso:
  uv run --group se effort_summary.py <6.0-backlog.md>          # imprime el resumen
  uv run --group se effort_summary.py <6.0-backlog.md> --write  # lo escribe/reemplaza en el fichero
  uv run --group se effort_summary.py <6.0-backlog.md> --csv    # tabla CSV epic;hu;rol;horas para hojas de cálculo
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from backlog_lib import H2_DET, H2_SUM, load_config, parse_epics, parse_tasks, render_summary, split_sections  # noqa: E402


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) > 1:
        print(__doc__)
        return 2
    path = Path(args[0] if args else "proposal/6.0-backlog.md")
    cfg = load_config(path.parent)
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    sp = split_sections(lines)
    if H2_DET not in sp["sections"]:
        print("Para calcular el resumen de esfuerzo es necesario que exista un backlog detallado previo con tareas en proposal.")
        return 1
    errors: list[str] = []
    epics = parse_epics(sp["sections"][H2_DET], errors, "detalle")
    for e in epics:
        for h in e.hus:
            parse_tasks(h, cfg, errors)
    if errors:
        print("Corrige el backlog antes de calcular el resumen:")
        for e in errors:
            print(f"  - {e}")
        return 1
    if "--csv" in sys.argv:
        print("epic;hu;rol;horas")
        for e in epics:
            for h in e.hus:
                for t in h.tasks:
                    print(f"EPIC {e.num} - {e.title};HU {h.epic}.{h.num} - {h.title};{t.role};{t.hours}")
        return 0
    summary = render_summary(epics, cfg["roles"])
    if "--write" not in sys.argv:
        print(summary)
        return 0
    start = next((n for h, n in sp["order"] if h == H2_SUM), None)
    body = lines[: start - 1] if start else lines
    while body and not body[-1].strip():
        body.pop()
    path.write_text("\n".join(body) + "\n\n" + summary, encoding="utf-8")
    print(f"Resumen escrito en {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

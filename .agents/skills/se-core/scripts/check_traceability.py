#!/usr/bin/env python3
"""Cruza IDs entre artefactos de proposal/ y genera un informe de trazabilidad.

Uso: uv run --group se check_traceability.py [raíz] [--strict]
--strict: exit 1 si hay requisitos sin cobertura, HUs sin spec/backlog o referencias huérfanas.
"""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

PATTERNS = {
    "RQ": re.compile(r"\bRQ-(?:HU-)?\d{2,4}\b"),
    "HU": re.compile(r"\bHU-[A-Z][A-Z0-9]{1,9}-\d{2,3}\b"),
    "F": re.compile(r"\bF-\d{3}\b"),
    "SRC": re.compile(r"\bSRC-\d{2,3}\b"),
    "Q": re.compile(r"\bQ-\d{3}\b"),
}
PLACEHOLDER = re.compile(r"<[a-záéíóúñ _/.-]{3,40}>|\bTODO\b|\bXXX\b", re.I)


def doc_kind(rel: str) -> str:
    name = rel.split("/")[-1]
    if rel.startswith("specs/"):
        return "spec"
    for prefix, kind in [("2-requirements", "matriz"), ("3-questions", "preguntas"), ("HU-Enfoque-Funcional", "funcional"),
                         ("HU-Enfoque-Tecnico", "tecnico"), ("HU-Enfoque-Técnico", "tecnico"), ("DATA-", "datos"),
                         ("IA-", "ia"), ("APP-", "aplicacion"), ("6.0-backlog", "backlog")]:
        if name.startswith(prefix):
            return kind
    return "otro"


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) > 1:
        print(__doc__)
        return 2
    root = Path(args[0] if args else ".").resolve()
    prop = root / "proposal"
    if not prop.is_dir():
        print("ERROR: no existe proposal/")
        return 2

    docs = {}
    for p in sorted(prop.rglob("*.md")):
        rel = p.relative_to(prop).as_posix()
        if rel.startswith(("_meta/", "checklists/")):
            continue
        docs[rel] = p.read_text(encoding="utf-8", errors="replace")

    refs: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))  # id -> kind -> docs
    for rel, text in docs.items():
        for _, rx in PATTERNS.items():
            for m in rx.findall(text):
                refs[m][doc_kind(rel)].add(rel)

    def defined(kind: str, rx: re.Pattern) -> set[str]:
        out = set()
        for rel, text in docs.items():
            if doc_kind(rel) == kind:
                out |= set(rx.findall(text))
        return out

    rq_defined = defined("matriz", PATTERNS["RQ"])
    hu_defined = {m for rel, t in docs.items() if doc_kind(rel) == "funcional"
                  for m in re.findall(r"^#{2,4}\s+(HU-[A-Z][A-Z0-9]{1,9}-\d{2,3})", t, re.M)}
    q_defined = defined("preguntas", PATTERNS["Q"])
    src_defined = defined("datos", PATTERNS["SRC"])

    design_kinds = {"funcional", "tecnico", "datos", "ia", "aplicacion", "spec"}
    rq_uncovered = sorted(r for r in rq_defined if not (set(refs[r]) & design_kinds))
    hu_no_spec = sorted(h for h in hu_defined if "spec" not in refs[h]) if any(doc_kind(r) == "spec" for r in docs) else []
    hu_no_backlog = sorted(h for h in hu_defined if "backlog" not in refs[h]) if any(doc_kind(r) == "backlog" for r in docs) else []

    orphans = []
    for ident, kinds in refs.items():
        if ident.startswith("RQ-HU-"):
            continue
        if ident.startswith("RQ-") and rq_defined and ident not in rq_defined:
            orphans.append((ident, kinds))
        elif ident.startswith("HU-") and hu_defined and ident not in hu_defined:
            orphans.append((ident, kinds))
        elif ident.startswith("Q-") and q_defined and ident not in q_defined:
            orphans.append((ident, kinds))
        elif ident.startswith("SRC-") and src_defined and ident not in src_defined:
            orphans.append((ident, kinds))

    lines = [f"# Informe de trazabilidad", "", f"> **Fecha:** {date.today().isoformat()}", "", "## Resumen", "",
             "| Indicador | Valor |", "| --- | --- |",
             f"| Requisitos en matriz | {len(rq_defined)} |",
             f"| Requisitos sin cobertura de diseño | {len(rq_uncovered)} |",
             f"| HUs funcionales | {len(hu_defined)} |",
             f"| HUs sin spec | {len(hu_no_spec)} |",
             f"| HUs sin backlog | {len(hu_no_backlog)} |",
             f"| Referencias huérfanas | {len(orphans)} |", "",
             "## `A confirmar` y restos de plantilla por documento", "",
             "| Documento | `A confirmar` | Restos de plantilla |", "| --- | ---: | ---: |"]
    for rel, text in docs.items():
        lines.append(f"| `{rel}` | {len(re.findall(r'A confirmar', text))} | {len(PLACEHOLDER.findall(text))} |")
    lines += ["", "## Requisitos sin cobertura", ""] + ([f"- `{r}`" for r in rq_uncovered] or ["- Ninguno"])
    lines += ["", "## HUs sin spec", ""] + ([f"- `{h}`" for h in hu_no_spec] or ["- Ninguna o no hay specs"])
    lines += ["", "## HUs sin reflejo en backlog", ""] + ([f"- `{h}`" for h in hu_no_backlog] or ["- Ninguna o no hay backlog"])
    lines += ["", "## Referencias huérfanas", ""]
    lines += [f"- `{i}` usado en {', '.join(sorted({d for s in k.values() for d in s}))}" for i, k in sorted(orphans)] or ["- Ninguna"]
    lines += ["", "## Matriz RQ → documentos", "", "| Requisito | Documentos |", "| --- | --- |"]
    for r in sorted(rq_defined):
        lines.append(f"| `{r}` | {', '.join(sorted(k for k in refs[r] if k != 'matriz')) or '—'} |")

    out = prop / "_meta/traceability-report.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"informe: {out}")
    print(f"RQ sin cobertura: {len(rq_uncovered)} · HU sin spec: {len(hu_no_spec)} · HU sin backlog: {len(hu_no_backlog)} · huérfanas: {len(orphans)}")
    problems = rq_uncovered or hu_no_spec or hu_no_backlog or orphans
    return 1 if ("--strict" in sys.argv and problems) else 0


if __name__ == "__main__":
    sys.exit(main())

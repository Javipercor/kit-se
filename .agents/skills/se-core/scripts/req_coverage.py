#!/usr/bin/env python3
"""Cobertura de requisitos por las historias de usuario.

Uso:
  uv run --group se req_coverage.py [raíz] [--doc HU-Enfoque-Funcional-x.md] [--section13]

Regla: todo requisito de las categorías de `coverage_required` (por defecto funcional y
técnico) debe estar ligado a al menos una HU (línea `**Requisitos:**`) o declarado en
`**Requisitos transversales:**` de la sección 2, salvo que su estado sea `Fuera de alcance`
con motivo. Fuente de requisitos: proposal/_meta/registro-requisitos.json o, si no existe,
proposal/2-requirements-matrix.md.

--section13 imprime la tabla de la sección 13.1 lista para el documento.
Escribe proposal/_meta/cobertura-<slug>.md. Exit 1 si hay huecos o errores.
"""
from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from reqlib import category, hu_links, load_config, load_requirements  # noqa: E402


def find_doc(opp: Path, given: str | None) -> Path | None:
    if given:
        p = Path(given)
        return p if p.is_absolute() or p.exists() else opp / "proposal" / given
    docs = sorted((opp / "proposal").glob("HU-Enfoque-Funcional*.md"))
    return docs[0] if len(docs) == 1 else None


def compute(opp: Path, doc: Path) -> dict:
    cfg = load_config(opp)
    reqs, source = load_requirements(opp)
    hus, trans = hu_links(doc.read_text(encoding="utf-8"), cfg)
    errors, warnings = [], []
    by_id = {r["id"]: r for r in reqs}
    covered: dict[str, list[str]] = {r["id"]: [] for r in reqs}
    for hu, ids in hus.items():
        if not ids:
            errors.append(f"{hu} no está ligada a ningún requisito")
        for i in ids:
            if i.startswith("RQ-HU-"):
                continue
            if i not in by_id:
                errors.append(f"{hu} referencia {i}, que no existe en el {source}")
            else:
                covered[i].append(hu)
    for i in trans:
        if i in by_id:
            covered[i].append("Transversal")
        elif not i.startswith("RQ-HU-"):
            errors.append(f"Requisito transversal {i} no existe en el {source}")
    required = set(cfg["coverage_required"])
    gaps, excluded, exempt = [], [], []
    for r in reqs:
        cat = category(cfg, r.get("tipo", ""))
        if cat is None:
            warnings.append(f"{r['id']}: tipo '{r.get('tipo')}' no configurado; se exige cobertura")
            cat = "funcional"
        out = r.get("estado") == "Fuera de alcance"
        if out:
            excluded.append(r)
            if not (r.get("motivo_exclusion") or "").strip():
                errors.append(f"{r['id']} está fuera de alcance sin motivo")
            if covered[r["id"]]:
                warnings.append(f"{r['id']} está fuera de alcance pero ligado a {', '.join(covered[r['id']])}")
        elif cat in required and not covered[r["id"]]:
            gaps.append(r)
        elif cat not in required and not covered[r["id"]]:
            exempt.append(r)
    for r in gaps:
        errors.append(f"{r['id']} ({r.get('tipo')}) sin HU: {r.get('texto', '')[:90]}")
    cap_of = {r["id"]: r.get("capacidad", "") for r in reqs}
    max_caps = cfg.get("dedupe", {}).get("max_capacidades_por_hu", 2)
    hu_caps = {}
    for hu, ids in hus.items():
        cs = sorted({cap_of.get(i, "") for i in ids} - {"", "TRANSVERSAL"})
        hu_caps[hu] = cs
        if len(cs) > max_caps:
            warnings.append(f"{hu} mezcla {len(cs)} capacidades ({', '.join(cs)}); probablemente deba dividirse")
    in_scope = [r for r in reqs if r.get("estado") != "Fuera de alcance" and category(cfg, r.get("tipo", "")) in required]
    pct = 100.0 if not in_scope else round(100 * (len(in_scope) - len(gaps)) / len(in_scope), 1)
    return {"cfg": cfg, "source": source, "reqs": reqs, "hus": hus, "trans": trans, "covered": covered,
            "hu_caps": hu_caps, "gaps": gaps, "excluded": excluded, "exempt": exempt, "errors": errors, "warnings": warnings, "pct": pct}


def section13(res: dict) -> str:
    out = ["| Requisito | Descripción | Tipo | Estado | Cobertura en este documento |", "| --- | --- | --- | --- | --- |"]
    for r in res["reqs"]:
        cov = ", ".join(res["covered"][r["id"]]) or ("Fuera de alcance: " + r.get("motivo_exclusion", "") if r.get("estado") == "Fuera de alcance" else "—")
        out.append(f"| `{r['id']}` | {r.get('texto', '').replace('|', '/')} | {r.get('tipo', '')} | {r.get('estado', '')} | {cov.replace('|', '/')} |")
    return "\n".join(out) + "\n"


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--doc")
    ap.add_argument("--section13", action="store_true")
    a = ap.parse_args()
    opp = Path(a.root).resolve()
    given = a.doc
    doc = find_doc(opp, given)
    if not doc or not doc.exists():
        print("ERROR: indica el documento funcional con --doc (no encontrado o hay varios)")
        return 2
    res = compute(opp, doc)
    if res["source"] == "ninguno":
        print("AVISO: no hay registro ni matriz de requisitos; la cobertura no es verificable")
        return 0
    if a.section13:
        print(section13(res))
        return 0
    slug = re.sub(r"^HU-Enfoque-Funcional-?", "", doc.stem) or "default"
    lines = [f"# Cobertura de requisitos · `{doc.name}`", "", f"> **Fecha:** {date.today().isoformat()} · **Fuente:** {res['source']}", "",
             f"- Requisitos: {len(res['reqs'])} · cobertura exigida: {res['pct']} % · huecos: {len(res['gaps'])} · "
             f"fuera de alcance: {len(res['excluded'])} · no exigidos sin HU: {len(res['exempt'])}",
             f"- HUs: {len(res['hus'])} · transversales: {', '.join(res['trans']) or 'ninguno'}", ""]
    if res["errors"]:
        lines += ["## Errores", ""] + [f"- {e}" for e in res["errors"]] + [""]
    if res["warnings"]:
        lines += ["## Avisos", ""] + [f"- {w}" for w in res["warnings"]] + [""]
    if any(res["hu_caps"].values()):
        cap_hus: dict[str, list[str]] = {}
        for hu, cs in res["hu_caps"].items():
            for c in cs:
                cap_hus.setdefault(c, []).append(hu)
        lines += ["## Capacidad → HUs", "", "| Capacidad | HUs |", "| --- | --- |"]
        lines += [f"| {c} | {', '.join(h)} |" for c, h in sorted(cap_hus.items())] + [""]
    lines += ["## Requisito → HUs", "", section13(res)]
    if res["excluded"]:
        lines += ["## Fuera de alcance (requieren aprobación humana)", ""]
        lines += [f"- `{r['id']}`: {r.get('texto', '')[:100]} — motivo: {r.get('motivo_exclusion', '')}" for r in res["excluded"]]
    out = opp / f"proposal/_meta/cobertura-{slug}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    status = "OK" if not res["errors"] else "KO"
    print(f"{status} cobertura {res['pct']} % · huecos {len(res['gaps'])} · fuera de alcance {len(res['excluded'])} → {out}")
    for e in res["errors"]:
        print(f"  - {e}")
    for w in res["warnings"]:
        print(f"  ! {w}")
    return 0 if not res["errors"] else 1


if __name__ == "__main__":
    sys.exit(main())

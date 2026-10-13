#!/usr/bin/env python3
"""Barrido exhaustivo de requisitos, página a página, y registro consolidado.

Subcomandos (todos reciben [raíz]):
  plan      Crea/actualiza el plan: una unidad por página (o fragmento de texto) de cada
            documento del manifiesto. Si un documento cambia, sus unidades vuelven a pendientes.
  next      Muestra las siguientes unidades pendientes con su texto, imagen y plantilla JSON.
            Opciones: --batch N (defecto 5), --doc RUTA (solo un documento).
  status    Progreso del barrido y errores de las unidades ya revisadas.
  findings  Lista los hallazgos (H-xxxxxxxx) y los pendientes de consolidar → hallazgos.md.
  check     Valida el registro contra los hallazgos, el barrido y la consolidación (req_dedupe lint).
  matrix    Genera proposal/2-requirements-matrix.md desde el registro.

Ficheros en proposal/_meta/:
  req-scan/plan.json               plan de unidades
  req-scan/units/<unidad>.json     resultado de revisar cada unidad (lo escribe el agente)
  req-scan/hallazgos.md            hallazgos y pendientes de consolidar
  registro-requisitos.json         requisitos consolidados (lo mantiene el agente)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "se-core/scripts"))
from reqlib import all_types, load_config, registry_path  # noqa: E402

MARKER = re.compile(r"^--- (página|diapositiva|hoja) (.+?) ---$", re.M)


def paths(opp: Path) -> dict:
    base = opp / "proposal/_meta/req-scan"
    return {"base": base, "plan": base / "plan.json", "units": base / "units",
            "manifest": opp / "proposal/_meta/corpus-manifest.json", "registry": registry_path(opp)}


def safe(uid: str) -> str:
    return re.sub(r"[^\w.-]+", "_", uid)


def segments(text: str, chunk: int) -> list[tuple[str, str]]:
    """Devuelve [(localizador, texto)] por página/diapositiva/hoja o por fragmentos de líneas."""
    parts = MARKER.split(text)
    out = []
    if len(parts) > 1:
        for kind, label, body in zip(parts[1::3], parts[2::3], parts[3::3]):
            prefix = {"página": "p.", "diapositiva": "diap.", "hoja": "hoja"}[kind]
            lines = body.splitlines()
            if len(lines) <= chunk * 2 or kind != "hoja":
                out.append((f"{prefix} {label}", body))
            else:
                for k in range(0, len(lines), chunk):
                    out.append((f"{prefix} {label}, filas {k + 1}-{min(k + chunk, len(lines))}", "\n".join(lines[k:k + chunk])))
        return out
    lines = text.splitlines()
    for k in range(0, max(len(lines), 1), chunk):
        out.append((f"líneas {k + 1}-{min(k + chunk, len(lines))}", "\n".join(lines[k:k + chunk])))
    return out


def build_units(opp: Path, cfg: dict) -> list[dict]:
    p = paths(opp)
    if not p["manifest"].exists():
        raise SystemExit("ERROR: ejecuta antes inventory_corpus.py")
    manifest = json.loads(p["manifest"].read_text(encoding="utf-8"))
    units = []
    for f in manifest["files"]:
        if f.get("kind") == "muestra-datos":
            continue
        images = {pg["n"]: pg.get("image") for pg in f.get("flagged_pages", [])}
        tables = {pg["n"]: pg.get("tables", []) for pg in f.get("flagged_pages", [])}
        if f.get("text_path"):
            text = (opp / f["text_path"]).read_text(encoding="utf-8")
            for idx, (loc, body) in enumerate(segments(text, cfg["chunk_lines"])):
                n = int(m[1]) if (m := re.match(r"(?:p\.|diap\.) (\d+)$", loc)) else None
                units.append({"id": f"{f['path']}#{idx + 1:04d}", "doc": f["path"], "loc": loc, "sha": f["sha256"],
                              "text_path": f["text_path"], "segment": idx, "chars": len(body.strip()),
                              "image": images.get(n) if n else None, "tables": tables.get(n, []) if n else []})
        elif f.get("image"):
            units.append({"id": f"{f['path']}#0001", "doc": f["path"], "loc": "imagen", "sha": f["sha256"],
                          "text_path": None, "segment": None, "chars": 0, "image": f["image"], "tables": []})
        else:
            units.append({"id": f"{f['path']}#0001", "doc": f["path"], "loc": "documento no legible", "sha": f["sha256"],
                          "text_path": None, "segment": None, "chars": 0, "image": None, "tables": [],
                          "ilegible": f.get("method", "")})
    return units


def load_plan(opp: Path) -> list[dict]:
    p = paths(opp)["plan"]
    if not p.exists():
        raise SystemExit("ERROR: no hay plan; ejecuta 'req_scan.py plan [raíz]'")
    return json.loads(p.read_text(encoding="utf-8"))["units"]


def unit_text(opp: Path, u: dict, cfg: dict) -> str:
    if not u.get("text_path"):
        return ""
    text = (opp / u["text_path"]).read_text(encoding="utf-8")
    return segments(text, cfg["chunk_lines"])[u["segment"]][1]


def read_unit(opp: Path, u: dict) -> dict | None:
    f = paths(opp)["units"] / f"{safe(u['id'])}.json"
    if not f.exists():
        return None
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {"_error": f"JSON inválido: {exc}"}


def validate_unit(u: dict, data: dict, cfg: dict) -> list[str]:
    if "_error" in data:
        return [data["_error"]]
    errs = []
    if data.get("unidad") != u["id"]:
        errs.append("campo 'unidad' no coincide")
    if data.get("revisado") is not True:
        errs.append("'revisado' debe ser true")
    if u.get("image") and data.get("leido_como_imagen") is not True:
        errs.append("la unidad tiene imagen y no consta leída como imagen")
    if u.get("ilegible") or (u.get("chars", 0) == 0 and not u.get("image")):
        if not (data.get("notas") or "").strip():
            errs.append("unidad sin contenido legible: explica la limitación en 'notas'")
    types, prios = all_types(cfg), cfg["priorities"]
    for k, r in enumerate(data.get("requisitos", []), 1):
        if not (r.get("texto") or "").strip():
            errs.append(f"requisito {k}: falta 'texto'")
        if r.get("tipo") not in types:
            errs.append(f"requisito {k}: tipo '{r.get('tipo')}' no válido")
        if not (r.get("cita") or "").strip():
            errs.append(f"requisito {k}: falta 'cita'")
        for fld in ("accion", "objeto"):
            if not (r.get(fld) or "").strip():
                errs.append(f"requisito {k}: falta '{fld}' (forma canónica)")
        if r.get("prioridad") and r["prioridad"] not in prios:
            errs.append(f"requisito {k}: prioridad '{r['prioridad']}' no válida")
    return errs


def hallazgo_id(uid: str, texto: str) -> str:
    return "H-" + hashlib.sha1(f"{uid}|{texto.strip()}".encode()).hexdigest()[:8]


def collect(opp: Path, cfg: dict) -> tuple[list[dict], dict, list[dict]]:
    plan = load_plan(opp)
    findings, pending, bad = [], [], {}
    for u in plan:
        data = read_unit(opp, u)
        if data is None:
            pending.append(u)
            continue
        errs = validate_unit(u, data, cfg)
        if errs:
            bad[u["id"]] = errs
            continue
        for r in data.get("requisitos", []):
            findings.append({"id": hallazgo_id(u["id"], r["texto"]), "unidad": u["id"], "doc": u["doc"], "loc": u["loc"],
                             "via_imagen": bool(data.get("leido_como_imagen")), **r})
    return findings, bad, pending


# ---------------------------------------------------------------- subcomandos

def cmd_plan(opp: Path, a, cfg: dict) -> int:
    p = paths(opp)
    new = build_units(opp, cfg)
    old = json.loads(p["plan"].read_text(encoding="utf-8"))["units"] if p["plan"].exists() else []
    new_ids = {u["id"]: u for u in new}
    stale = [u for u in old if u["id"] not in new_ids or new_ids[u["id"]]["sha"] != u["sha"]]
    if stale:
        dest = p["units"] / "_obsoletos" / datetime.now().strftime("%Y%m%d-%H%M%S")
        for u in stale:
            f = p["units"] / f"{safe(u['id'])}.json"
            if f.exists():
                dest.mkdir(parents=True, exist_ok=True)
                shutil.move(str(f), dest / f.name)
    p["units"].mkdir(parents=True, exist_ok=True)
    p["plan"].write_text(json.dumps({"generado": datetime.now().isoformat(timespec="seconds"), "units": new},
                                    ensure_ascii=False, indent=2), encoding="utf-8")
    docs = len({u["doc"] for u in new})
    img = sum(1 for u in new if u.get("image"))
    print(f"plan: {len(new)} unidades en {docs} documentos ({img} con imagen) · invalidadas por cambios: {len(stale)}")
    return 0


def cmd_next(opp: Path, a, cfg: dict) -> int:
    plan = load_plan(opp)
    todo = [u for u in plan if read_unit(opp, u) is None and (not a.doc or u["doc"] == a.doc)]
    if not todo:
        print("No quedan unidades pendientes" + (f" en {a.doc}" if a.doc else "") + ".")
        return 0
    units_dir = paths(opp)["units"]
    print(f"Pendientes: {len(todo)}. Mostrando {min(a.batch, len(todo))}.\n")
    for u in todo[: a.batch]:
        print(f"=== UNIDAD {u['id']} · {u['doc']} · {u['loc']}")
        if u.get("image"):
            print(f"IMAGEN (leer obligatoriamente): {u['image']}")
        for t in u.get("tables", []):
            print(f"TABLA: {t}")
        if u.get("ilegible"):
            print(f"SIN TEXTO NI IMAGEN: {u['ilegible']}")
        body = unit_text(opp, u, cfg).strip()
        print("--- texto ---")
        print(body[:12000] if body else "(sin texto extraído)")
        tpl = {"unidad": u["id"], "revisado": True, "leido_como_imagen": bool(u.get("image")),
               "requisitos": [{"texto": "", "actor": "", "accion": "", "objeto": "", "condicion": "",
                               "tipo": "Funcional", "cita": "", "prioridad": "Obligatorio"}], "notas": ""}
        print(f"--- escribir en: {(units_dir / (safe(u['id']) + '.json')).relative_to(opp)}")
        print(json.dumps(tpl, ensure_ascii=False))
        print()
    return 0


def cmd_status(opp: Path, a, cfg: dict) -> int:
    plan = load_plan(opp)
    findings, bad, pending = collect(opp, cfg)
    done = len(plan) - len(pending) - len(bad)
    print(f"barrido: {done}/{len(plan)} unidades revisadas · pendientes {len(pending)} · con errores {len(bad)} · hallazgos {len(findings)}")
    per_doc: dict[str, list[int]] = {}
    for u in plan:
        d = per_doc.setdefault(u["doc"], [0, 0])
        d[1] += 1
        if u not in pending and u["id"] not in bad:
            d[0] += 1
    for doc, (ok, total) in per_doc.items():
        print(f"  {'✓' if ok == total else '·'} {doc}: {ok}/{total}")
    for uid, errs in bad.items():
        print(f"  ! {uid}: {'; '.join(errs)}")
    return 0 if not pending and not bad else 1


def load_registry(opp: Path) -> dict:
    from reqlib import load_registry as _lr
    return _lr(opp)


def cmd_findings(opp: Path, a, cfg: dict) -> int:
    findings, bad, pending = collect(opp, cfg)
    reg = load_registry(opp)
    assigned = {h for r in reg.get("requisitos", []) for h in r.get("hallazgos", [])} | {d["hallazgo"] for d in reg.get("descartados", [])}
    todo = [f for f in findings if f["id"] not in assigned]
    lines = ["# Hallazgos del barrido de requisitos", "", f"> Generado: {date.today().isoformat()} · hallazgos: {len(findings)} · "
             f"pendientes de consolidar: {len(todo)} · unidades pendientes: {len(pending)}", ""]

    def table(rows):
        out = ["| Hallazgo | Tipo | Prioridad | Texto | Cita | Origen |", "| --- | --- | --- | --- | --- | --- |"]
        for f in rows:
            via = ", imagen" if f["via_imagen"] else ""
            out.append(f"| `{f['id']}` | {f['tipo']} | {f.get('prioridad', '')} | {f['texto'].replace('|', '/')} | "
                       f"{f['cita'].replace('|', '/')[:120]} | `{f['doc']}` {f['loc']}{via} |")
        return out
    lines += ["## Pendientes de consolidar", ""] + (table(todo) if todo else ["Ninguno."]) + [""]
    lines += ["## Todos los hallazgos", ""] + table(findings)
    out = paths(opp)["base"] / "hallazgos.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"hallazgos: {len(findings)} · pendientes de consolidar: {len(todo)} → {out}")
    return 0


def cmd_check(opp: Path, a, cfg: dict) -> int:
    findings, bad, pending = collect(opp, cfg)
    reg = load_registry(opp)
    errs = []
    if pending:
        errs.append(f"barrido incompleto: {len(pending)} unidades pendientes")
    if bad:
        errs.append(f"{len(bad)} unidades con errores (ver 'status')")
    fids = {f["id"] for f in findings}
    seen: dict[str, str] = {}
    rx = re.compile(cfg["id_pattern"])
    ids = [r.get("id", "") for r in reg.get("requisitos", [])]
    for d in sorted({i for i in ids if ids.count(i) > 1}):
        errs.append(f"ID duplicado: {d}")
    for r in reg.get("requisitos", []):
        rid = r.get("id", "?")
        if not rx.match(rid):
            errs.append(f"{rid}: no cumple el patrón {cfg['id_pattern']}")
        if not (r.get("texto") or "").strip():
            errs.append(f"{rid}: falta 'texto'")
        if r.get("tipo") not in all_types(cfg):
            errs.append(f"{rid}: tipo '{r.get('tipo')}' no válido")
        if r.get("estado") not in cfg["states"]:
            errs.append(f"{rid}: estado '{r.get('estado')}' no válido")
        if r.get("prioridad") not in cfg["priorities"]:
            errs.append(f"{rid}: prioridad '{r.get('prioridad')}' no válida")
        if r.get("estado") == "Fuera de alcance" and not (r.get("motivo_exclusion") or "").strip():
            errs.append(f"{rid}: fuera de alcance sin 'motivo_exclusion'")
        hs = r.get("hallazgos", [])
        if not hs and r.get("estado") != "Inferido":
            errs.append(f"{rid}: sin hallazgos de origen (solo admisible si estado = Inferido, con 'notas')")
        if not hs and r.get("estado") == "Inferido" and not (r.get("notas") or "").strip():
            errs.append(f"{rid}: inferido sin justificación en 'notas'")
        for h in hs:
            if h not in fids:
                errs.append(f"{rid}: hallazgo {h} no existe (¿documento modificado? vuelve a revisar)")
            elif h in seen:
                errs.append(f"{h} asignado a {seen[h]} y a {rid}")
            seen[h] = rid
    for d in reg.get("descartados", []):
        h = d.get("hallazgo")
        if h not in fids:
            errs.append(f"descartado {h} no existe")
        elif h in seen:
            errs.append(f"{h} está asignado a {seen[h]} y descartado")
        if not (d.get("motivo") or "").strip():
            errs.append(f"descartado {h} sin motivo")
        seen[h] = "descartado"
    unassigned = sorted(fids - set(seen))
    if unassigned:
        errs.append(f"{len(unassigned)} hallazgos sin consolidar: {', '.join(unassigned[:12])}{' …' if len(unassigned) > 12 else ''}")
    from req_dedupe import lint  # noqa: E402  (mismo directorio)
    lerrs, lwarns = lint(opp, cfg, findings, reg)
    errs += lerrs
    for w in lwarns:
        print(f"  ! {w}")
    if errs:
        print("KO registro de requisitos")
        for e in errs:
            print(f"  - {e}")
        return 1
    print(f"OK registro: {len(reg['requisitos'])} requisitos · {len(reg['capacidades'])} capacidades · "
          f"{len(reg['descartados'])} descartados · {len(reg['decisiones'])} decisiones · {len(fids)} hallazgos")
    return 0


def cmd_matrix(opp: Path, a, cfg: dict) -> int:
    if cmd_check(opp, a, cfg) != 0 and not a.force:
        print("Corrige el registro antes de generar la matriz (o usa --force para un borrador)")
        return 1
    findings, _, _ = collect(opp, cfg)
    by_h = {f["id"]: f for f in findings}
    reg = load_registry(opp)
    rows = ["# Matriz de requisitos", "",
            f"> **Estado:** borrador · **Versión:** 0.1 · **Fecha:** {date.today().isoformat()} · **Fuentes:** `proposal/_meta/registro-requisitos.json` (generada con `req_scan.py matrix`; no editar a mano)", "",
            "## Capacidades", "", "| Capacidad | Nombre | Descripción | Nº requisitos |", "| --- | --- | --- | ---: |"]
    for c in reg["capacidades"]:
        n = sum(r.get("capacidad") == c["id"] for r in reg["requisitos"])
        rows.append(f"| {c['id']} | {c['nombre']} | {c.get('descripcion', '').replace('|', '/')} | {n} |")
    n_t = sum(r.get("capacidad") == "TRANSVERSAL" for r in reg["requisitos"])
    rows += [f"| TRANSVERSAL | Requisitos técnicos transversales | Aplican a toda la solución | {n_t} |", "",
             "## Requisitos", "",
             "| ID | Requisito | Tipo | Capacidad | Origen | Prioridad | Estado | Notas / riesgo |",
             "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in reg.get("requisitos", []):
        origin: dict[str, list[str]] = {}
        for h in r.get("hallazgos", []):
            f = by_h.get(h)
            if f:
                loc = f["loc"] + (" (imagen)" if f["via_imagen"] else "")
                if loc not in origin.setdefault(f["doc"], []):
                    origin[f["doc"]].append(loc)
        src = "; ".join(f"`{d}` {', '.join(l)}" for d, l in origin.items()) or "Inferido"
        notes = " ".join(x for x in [r.get("notas", ""), ("Motivo: " + r["motivo_exclusion"]) if r.get("motivo_exclusion") else ""] if x)
        text = r["texto"] + ("".join(f"<br>· {d}" for d in r.get("detalles", [])))
        rows.append(f"| {r['id']} | {text.replace('|', '/')} | {r['tipo']} | {r.get('capacidad', '—')} | {src} | {r['prioridad']} | {r['estado']} | {notes.replace('|', '/')} |")
    rows += ["", "## Resumen por tipo", "", "| Tipo | Nº | Obligatorios | A confirmar | Fuera de alcance |", "| --- | ---: | ---: | ---: | ---: |"]
    for t in all_types(cfg):
        rs = [r for r in reg.get("requisitos", []) if r["tipo"] == t]
        if rs:
            rows.append(f"| {t} | {len(rs)} | {sum(r['prioridad'] == 'Obligatorio' for r in rs)} | "
                        f"{sum(r['estado'] == 'A confirmar' for r in rs)} | {sum(r['estado'] == 'Fuera de alcance' for r in rs)} |")
    rows += ["", f"Hallazgos descartados como no requisitos: {len(reg.get('descartados', []))} (ver `proposal/_meta/registro-requisitos.json`)."]
    out = opp / "proposal/2-requirements-matrix.md"
    out.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(f"matriz: {out} ({len(reg.get('requisitos', []))} requisitos)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["plan", "next", "status", "findings", "check", "matrix"])
    ap.add_argument("root", nargs="?", default=".", help="raíz del workspace (por defecto, el directorio actual)")
    ap.add_argument("--batch", type=int, default=5)
    ap.add_argument("--doc")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    opp = Path(a.root).resolve()
    cfg = load_config(opp)
    return {"plan": cmd_plan, "next": cmd_next, "status": cmd_status, "findings": cmd_findings,
            "check": cmd_check, "matrix": cmd_matrix}[a.cmd](opp, a, cfg)


if __name__ == "__main__":
    sys.exit(main())

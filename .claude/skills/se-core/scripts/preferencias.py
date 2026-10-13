#!/usr/bin/env python3
"""Catálogo de preferencias tecnológicas y de arquitectura (se.preferencias.json).

Uso (desde la raíz del repositorio, con `uv run --group se`):
  preferencias.py listar  [--ambito AMBITO]
  preferencias.py fijar   --ambito AMBITO --valor VALOR --nivel obligatoria|preferente|evitar|prohibida
                          --motivo TEXTO --por NOMBRE [--alias "a; b"] [--aplica-si TEXTO]
                          [--alternativas "x; y"] [--origen organizacion|cliente|propuesta]
  preferencias.py quitar  PREF-NN --por NOMBRE --motivo TEXTO
  preferencias.py validar

Niveles:
  obligatoria  se usa salvo excepción aceptada por una persona
  preferente   opción por defecto; apartarse exige motivo y alternativas (y aceptación humana)
  evitar       solo con una excepción justificada
  prohibida    solo con excepción aceptada por una persona

`fijar` y `quitar` son acciones humanas: además de cambiar el catálogo registran una decisión
humana en el registro de decisiones, así que todo cambio de preferencias queda trazado.
`validar` comprueba el esquema y avisa de preferencias sin decisión que las respalde
(editadas a mano), salvo las de origen `organizacion`, que vienen del catálogo base del kit.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from decisiones import load_cfg, norm, read_events, record, root_of, split_list, state  # noqa: E402

ORIGENES = ["organizacion", "cliente", "propuesta"]


def path(root: Path) -> Path:
    return root / "se.preferencias.json"


def load(root: Path) -> dict:
    f = path(root)
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {"version": 1, "preferencias": []}


def save(root: Path, data: dict) -> None:
    path(root).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def validate(root: Path) -> tuple[list[str], list[str]]:
    cfg = load_cfg(root)
    prefs = load(root)["preferencias"]
    errs, warns, seen = [], [], set()
    backed = {d.get("preferencia") for d in state(read_events(root)).values() if d["estado"] == "aceptada"}
    for p in prefs:
        pid = p.get("id", "?")
        if pid in seen:
            errs.append(f"ID duplicado: {pid}")
        seen.add(pid)
        for k in ("ambito", "valor", "nivel", "motivo"):
            if not str(p.get(k, "")).strip():
                errs.append(f"{pid}: falta '{k}'")
        if p.get("nivel") not in cfg["niveles_preferencia"]:
            errs.append(f"{pid}: nivel '{p.get('nivel')}' no válido")
        if cfg["ambitos_tecnologicos"] and p.get("ambito") not in cfg["ambitos_tecnologicos"]:
            errs.append(f"{pid}: ámbito '{p.get('ambito')}' no válido")
        if pid not in backed and p.get("origen") != "organizacion":
            warns.append(f"{pid}: sin decisión humana que la respalde (¿editada a mano? usa `fijar`)")
    obligatorias: dict[str, list[str]] = {}
    for p in prefs:
        if p.get("nivel") == "obligatoria":
            obligatorias.setdefault(p.get("ambito"), []).append(p.get("valor"))
    for amb, vals in obligatorias.items():
        if len(vals) > 1:
            errs.append(f"ámbito {amb}: varias obligatorias ({', '.join(vals)}); deja una o usa 'aplica_si'")
    return errs, warns


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    ls = sub.add_parser("listar")
    ls.add_argument("--ambito")
    f = sub.add_parser("fijar")
    for k in ("ambito", "valor", "nivel", "motivo", "por"):
        f.add_argument(f"--{k}", required=True)
    f.add_argument("--alias", default="")
    f.add_argument("--aplica-si", default="")
    f.add_argument("--alternativas", default="")
    f.add_argument("--origen", choices=ORIGENES, default="propuesta")
    q = sub.add_parser("quitar")
    q.add_argument("id")
    q.add_argument("--por", required=True)
    q.add_argument("--motivo", required=True)
    sub.add_parser("validar")
    a = ap.parse_args()
    root = root_of(Path("."))
    cfg = load_cfg(root)
    data = load(root)
    prefs = data["preferencias"]

    if a.cmd == "listar":
        rows = [p for p in prefs if not a.ambito or p["ambito"] == a.ambito]
        for p in rows:
            extra = f" · si {p['aplica_si']}" if p.get("aplica_si") else ""
            print(f"{p['id']} {p['nivel']:<11} {p['ambito']:<22} {p['valor']}{extra} — {p.get('motivo', '')}")
        print(f"({len(rows)} preferencias)")
        return 0

    if a.cmd == "fijar":
        if a.nivel not in cfg["niveles_preferencia"]:
            print(f"KO: nivel no válido ({', '.join(cfg['niveles_preferencia'])})")
            return 1
        if cfg["ambitos_tecnologicos"] and a.ambito not in cfg["ambitos_tecnologicos"]:
            print(f"KO: ámbito no válido ({', '.join(cfg['ambitos_tecnologicos'])})")
            return 1
        existing = next((p for p in prefs if p["ambito"] == a.ambito and norm(p["valor"]) == norm(a.valor)), None)
        pid = existing["id"] if existing else f"PREF-{max([int(p['id'][5:]) for p in prefs] + [0]) + 1:02d}"
        entry = {"id": pid, "ambito": a.ambito, "valor": a.valor, "nivel": a.nivel, "motivo": a.motivo,
                 "alias": split_list(a.alias), "aplica_si": a.aplica_si, "alternativas_aceptables": split_list(a.alternativas),
                 "origen": a.origen}
        before = dict(existing) if existing else None
        if existing:
            existing.update(entry)
        else:
            prefs.append(entry)
        save(root, data)
        area = "arquitectura" if a.ambito == "patron-arquitectura" else "tecnologia"
        verb = "actualizada" if before else "fijada"
        did = record(root, origen="humano", autor=a.por, area=area, titulo=f"Preferencia {verb}: {a.ambito} = {a.valor} ({a.nivel})",
                     decision=f"{pid}: {a.ambito} = {a.valor}, nivel {a.nivel}" + (f", aplica si {a.aplica_si}" if a.aplica_si else ""),
                     motivo=a.motivo, preferencia=pid, ambito=a.ambito, valor=a.valor, es_preferencia=True,
                     alternativas=split_list(a.alternativas), tipo="decision")
        print(f"{pid} {verb} · decisión {did}")
        return 0

    if a.cmd == "quitar":
        p = next((x for x in prefs if x["id"] == a.id), None)
        if not p:
            print(f"KO: {a.id} no existe")
            return 1
        prefs.remove(p)
        save(root, data)
        did = record(root, origen="humano", autor=a.por, area="tecnologia", titulo=f"Preferencia retirada: {p['ambito']} = {p['valor']}",
                     decision=f"Se retira {a.id} ({p['nivel']})", motivo=a.motivo, preferencia=a.id, es_preferencia=True, tipo="decision")
        print(f"{a.id} retirada · decisión {did}")
        return 0

    errs, warns = validate(root)
    for w in warns:
        print(f"  ! {w}")
    if errs:
        print("KO preferencias")
        for e in errs:
            print(f"  - {e}")
        return 1
    print(f"OK preferencias: {len(prefs)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

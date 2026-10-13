#!/usr/bin/env python3
"""Registro de decisiones del kit SE: humanas y de agentes, inmutable y trazable.

Uso (desde la raíz del repositorio, con `uv run --group se`):
  decisiones.py registrar --origen agente|humano --autor NOMBRE --area AREA --titulo T --decision D
                          --motivo M [--fase F] [--tipo decision|supuesto|excepcion] [--impacto alto|medio|bajo]
                          [--alternativas "A; B"] [--evidencia "RQ-001, Q-003, RFP/x.pdf p. 4"]
                          [--afecta "HU-PLV-01, ADR-02"] [--ambito AMBITO --valor VALOR]
                          [--preferencia PREF-02] [--excepcion-de PREF-05] [--sustituye D-004]
  decisiones.py aceptar  D-NNN --por NOMBRE [--nota TEXTO]
  decisiones.py rechazar D-NNN --por NOMBRE --motivo TEXTO
  decisiones.py comentar D-NNN --origen agente|humano --autor NOMBRE --nota TEXTO
  decisiones.py listar   [--estado E] [--origen O] [--area A] [--pendientes]
  decisiones.py ver      D-NNN
  decisiones.py check    [--gate]      integridad, referencias y cumplimiento de preferencias
  decisiones.py render                 regenera proposal/_meta/decisiones.md

Modelo:
- Todo se guarda como eventos en proposal/_meta/decisiones/eventos.jsonl, encadenados por hash:
  nada se edita ni se borra; un cambio de opinión es una decisión nueva que `--sustituye` a otra.
- Origen `agente` → estado `propuesta`. Origen `humano` → `aceptada`. Una propuesta pasa a
  `aceptada` o `rechazada` solo con `aceptar`/`rechazar`, que son acciones humanas.
- Al aceptar una decisión que sustituye a otra, la anterior pasa a `sustituida`.
- Las decisiones con `--ambito`/`--valor` (elección tecnológica o de arquitectura) se validan
  contra se.preferencias.json.
- `check --gate` falla si hay propuestas de impacto alto pendientes de aceptación.
Tras cada escritura se regenera proposal/_meta/decisiones.md.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

DEFAULT = {
    "areas": ["alcance", "requisitos", "funcional", "datos", "ia", "arquitectura", "tecnologia", "integracion",
              "seguridad", "despliegue", "estimacion", "proceso"],
    "areas_impacto_alto": ["alcance", "arquitectura", "tecnologia", "seguridad", "estimacion"],
    "ambitos_tecnologicos": [],
    "niveles_preferencia": ["obligatoria", "preferente", "evitar", "prohibida"],
}
TIPOS = ["decision", "supuesto", "excepcion"]
ESTADOS = ["propuesta", "aceptada", "rechazada", "sustituida"]
ID_RX = re.compile(r"\bD-\d{3}\b")
NEGACION = re.compile(r"descart|no se (usa|utiliza|recomienda)|evitar|prohib|alternativa|frente a|en lugar de", re.I)


# ------------------------------------------------------------------ utilidades

def root_of(start: Path) -> Path:
    for d in [start.resolve(), *start.resolve().parents]:
        if (d / "proposal").is_dir() or (d / "se.config.json").is_file():
            return d
    return start.resolve()


def load_cfg(root: Path) -> dict:
    f = root / "se.config.json"
    data = json.loads(f.read_text(encoding="utf-8")).get("decisiones", {}) if f.exists() else {}
    return {**DEFAULT, **data}


def log_path(root: Path) -> Path:
    return root / "proposal/_meta/decisiones/eventos.jsonl"


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", (s or "").lower())
    return re.sub(r"\s+", " ", "".join(c for c in s if not unicodedata.combining(c))).strip()


def split_list(s: str | None) -> list[str]:
    return [x.strip() for x in re.split(r"[;,]\s*", s or "") if x.strip()]


def canonical(ev: dict) -> str:
    return json.dumps({k: v for k, v in ev.items() if k != "hash"}, ensure_ascii=False, sort_keys=True)


def read_events(root: Path) -> list[dict]:
    f = log_path(root)
    if not f.exists():
        return []
    return [json.loads(line) for line in f.read_text(encoding="utf-8").splitlines() if line.strip()]


def append(root: Path, ev: dict) -> dict:
    events = read_events(root)
    ev = {"seq": len(events) + 1, "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
          **ev, "prev": events[-1]["hash"] if events else ""}
    ev["hash"] = hashlib.sha256(canonical(ev).encode()).hexdigest()
    f = log_path(root)
    f.parent.mkdir(parents=True, exist_ok=True)
    with f.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(ev, ensure_ascii=False) + "\n")
    return ev


def state(events: list[dict]) -> dict[str, dict]:
    """Proyección actual de las decisiones a partir de los eventos."""
    ds: dict[str, dict] = {}
    for ev in events:
        did = ev.get("id")
        if ev["evento"] == "registrar":
            ds[did] = {**ev["datos"], "id": did, "estado": "aceptada" if ev["actor"]["tipo"] == "humano" else "propuesta",
                       "origen": ev["actor"]["tipo"], "autor": ev["actor"]["nombre"], "fecha": ev["ts"],
                       "aceptada_por": ev["actor"]["nombre"] if ev["actor"]["tipo"] == "humano" else "",
                       "historial": [ev]}
            if ds[did]["estado"] == "aceptada" and ds[did].get("sustituye") in ds:
                ds[ds[did]["sustituye"]]["estado"] = "sustituida"
        elif did in ds:
            d = ds[did]
            d["historial"].append(ev)
            if ev["evento"] == "aceptar":
                d["estado"], d["aceptada_por"] = "aceptada", ev["actor"]["nombre"]
                if d.get("sustituye") in ds:
                    ds[d["sustituye"]]["estado"] = "sustituida"
            elif ev["evento"] == "rechazar":
                d["estado"] = "rechazada"
    return ds


def load_prefs(root: Path) -> list[dict]:
    f = root / "se.preferencias.json"
    return json.loads(f.read_text(encoding="utf-8")).get("preferencias", []) if f.exists() else []


def matches(pref: dict, valor: str) -> bool:
    v = norm(valor)
    terms = [norm(pref.get("valor", ""))] + [norm(a) for a in pref.get("alias", [])]
    return any(t and (t in v or v in t) for t in terms)


# ------------------------------------------------------------------ comprobaciones

def chain_errors(events: list[dict]) -> list[str]:
    errs, prev = [], ""
    for i, ev in enumerate(events, 1):
        if ev.get("seq") != i:
            errs.append(f"evento {i}: secuencia alterada (seq={ev.get('seq')})")
        if ev.get("prev") != prev:
            errs.append(f"evento {i}: la cadena no enlaza con el anterior (¿se borró o reordenó un evento?)")
        if hashlib.sha256(canonical(ev).encode()).hexdigest() != ev.get("hash"):
            errs.append(f"evento {i} ({ev.get('id')}): hash no coincide (¿se editó a mano?)")
        prev = ev.get("hash", "")
    return errs


def preference_findings(ds: dict[str, dict], prefs: list[dict]) -> tuple[list[str], list[str]]:
    errs, warns = [], []
    vigentes = [d for d in ds.values() if d["estado"] in ("propuesta", "aceptada") and not d.get("es_preferencia")]
    exc = {}
    for d in vigentes:
        if d.get("excepcion_de"):
            exc.setdefault(d["excepcion_de"], []).append(d)
    by_amb: dict[str, list[dict]] = {}
    for p in prefs:
        by_amb.setdefault(p.get("ambito", ""), []).append(p)

    def human_exception(pid: str) -> bool:
        return any(e["estado"] == "aceptada" for e in exc.get(pid, []))

    for d in vigentes:
        amb, val = d.get("ambito"), d.get("valor")
        if not amb or not val or d.get("tipo") == "excepcion":
            continue
        for p in by_amb.get(amb, []):
            hit, lvl, pid = matches(p, val), p.get("nivel"), p.get("id")
            if lvl == "obligatoria" and not hit and not human_exception(pid):
                errs.append(f"{d['id']} elige '{val}' en {amb}, pero {pid} obliga a '{p['valor']}': "
                            f"registra una excepción (--tipo excepcion --excepcion-de {pid}) y que la acepte una persona")
            elif lvl == "prohibida" and hit and not human_exception(pid):
                errs.append(f"{d['id']} elige '{val}', prohibido por {pid}: requiere excepción aceptada por una persona")
            elif lvl == "evitar" and hit and not exc.get(pid):
                warns.append(f"{d['id']} elige '{val}', a evitar según {pid}: justifícalo con una excepción")
            elif lvl == "preferente" and not hit:
                if not d.get("alternativas") or not d.get("motivo"):
                    errs.append(f"{d['id']} se aparta de {pid} ('{p['valor']}') sin motivo ni alternativas")
                elif d["estado"] == "propuesta":
                    warns.append(f"{d['id']} se aparta de {pid} ('{p['valor']}'): pendiente de aceptación humana")
    chosen = {d.get("ambito") for d in vigentes if d.get("ambito")}
    for p in prefs:
        if p.get("nivel") == "obligatoria" and p.get("ambito") not in chosen:
            warns.append(f"{p['id']} ({p['ambito']} = {p['valor']}) es obligatoria y aún no hay decisión registrada en ese ámbito")
    return errs, warns


def doc_findings(root: Path, ds: dict[str, dict], prefs: list[dict]) -> tuple[list[str], list[str]]:
    errs, warns = [], []
    prop = root / "proposal"
    if not prop.exists():
        return errs, warns
    docs = [p for p in prop.rglob("*.md") if "_meta" not in p.parts]
    excepted = {d["excepcion_de"] for d in ds.values() if d.get("excepcion_de") and d["estado"] == "aceptada"}
    for doc in docs:
        rel = doc.relative_to(root)
        for n, line in enumerate(doc.read_text(encoding="utf-8").splitlines(), 1):
            for did in ID_RX.findall(line):
                if did not in ds:
                    errs.append(f"{rel}:{n} cita {did}, que no existe en el registro")
                elif ds[did]["estado"] in ("rechazada", "sustituida"):
                    warns.append(f"{rel}:{n} cita {did}, que está {ds[did]['estado']}")
            if NEGACION.search(line):
                continue
            for p in prefs:
                if p.get("nivel") == "prohibida" and p.get("id") not in excepted and matches_text(p, line):
                    warns.append(f"{rel}:{n} menciona '{p['valor']}' (prohibida por {p['id']}) sin excepción aceptada")
        if doc.name.startswith("APP-Diseno"):
            text = doc.read_text(encoding="utf-8")
            for m in re.finditer(r"^### (ADR-\d{2})\.(.*?)(?=^### |^## |\Z)", text, re.M | re.S):
                if not ID_RX.search(m[0]):
                    warns.append(f"{rel}: {m[1]} no cita la decisión D-NNN que lo respalda")
    return errs, warns


def matches_text(pref: dict, line: str) -> bool:
    ln = f" {norm(line)} "
    terms = [norm(pref.get("valor", ""))] + [norm(a) for a in pref.get("alias", [])]
    return any(t and re.search(rf"(?<![\w-]){re.escape(t)}(?![\w-])", ln) for t in terms)


def pending_high(ds: dict[str, dict]) -> list[dict]:
    return [d for d in ds.values() if d["estado"] == "propuesta" and d.get("impacto") == "alto"]


# ------------------------------------------------------------------ vista Markdown

def render(root: Path) -> Path:
    ds = state(read_events(root))
    prefs = load_prefs(root)
    out = root / "proposal/_meta/decisiones.md"
    out.parent.mkdir(parents=True, exist_ok=True)

    def row(d):
        tec = f"{d.get('ambito')} = {d.get('valor')}" if d.get("ambito") else ""
        return (f"| {d['id']} | {d['estado']} | {d['origen']} ({d['autor']}) | {d.get('area', '')} | {d.get('impacto', '')} | "
                f"{d['titulo'].replace('|', '/')} | {tec.replace('|', '/')} | {d.get('aceptada_por', '')} |")
    head = ["| ID | Estado | Origen | Área | Impacto | Título | Tecnología | Aceptada por |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    humanas = [d for d in ds.values() if d["estado"] == "aceptada"]
    pend = [d for d in ds.values() if d["estado"] == "propuesta"]
    lines = ["# Registro de decisiones (kit SE)", "",
             f"> Generado desde `proposal/_meta/decisiones/eventos.jsonl` el {datetime.now().date().isoformat()}. "
             "No editar a mano: usa `decisiones.py`.", "",
             "## Decisiones vigentes (aceptadas)", "", "Prevalecen sobre cualquier otra fuente salvo una decisión posterior que las sustituya.", ""]
    lines += (head + [row(d) for d in humanas]) if humanas else ["Ninguna."]
    lines += ["", "## Pendientes de aceptación", ""]
    lines += (head + [row(d) for d in sorted(pend, key=lambda x: (x.get("impacto") != "alto", x["id"]))]) if pend else ["Ninguna."]
    if prefs:
        lines += ["", "## Preferencias activas (`se.preferencias.json`)", "", "| ID | Ámbito | Valor | Nivel | Motivo |", "| --- | --- | --- | --- | --- |"]
        lines += [f"| {p['id']} | {p['ambito']} | {p['valor']} | {p['nivel']} | {p.get('motivo', '').replace('|', '/')} |" for p in prefs]
    lines += ["", "## Detalle", ""]
    for d in sorted(ds.values(), key=lambda x: x["id"]):
        lines += [f"### {d['id']}. {d['titulo']}", "",
                  f"- **Estado:** {d['estado']} · **Origen:** {d['origen']} ({d['autor']}) · **Fecha:** {d['fecha'][:10]} · "
                  f"**Tipo:** {d.get('tipo')} · **Área:** {d.get('area')} · **Impacto:** {d.get('impacto')} · **Fase:** {d.get('fase') or '—'}",
                  f"- **Decisión:** {d['decision']}", f"- **Motivo:** {d.get('motivo') or '—'}"]
        for k, lab in (("alternativas", "Alternativas consideradas"), ("evidencia", "Evidencia"), ("afecta", "Afecta a")):
            if d.get(k):
                lines.append(f"- **{lab}:** {', '.join(d[k])}")
        if d.get("ambito"):
            lines.append(f"- **Tecnología / enfoque:** {d['ambito']} = {d['valor']}"
                         + (f" (preferencia {d['preferencia']})" if d.get("preferencia") else ""))
        for k, lab in (("excepcion_de", "Excepción a"), ("sustituye", "Sustituye a")):
            if d.get(k):
                lines.append(f"- **{lab}:** {d[k]}")
        hist = [f"{e['ts'][:16].replace('T', ' ')} {e['evento']} por {e['actor']['nombre']} ({e['actor']['tipo']})"
                + (f": {e.get('nota')}" if e.get("nota") else "") for e in d["historial"]]
        lines += ["- **Historial:** " + " · ".join(hist), ""]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


# ------------------------------------------------------------------ API para otros scripts

def record(root: Path, *, origen: str, autor: str, area: str, titulo: str, decision: str, motivo: str = "",
           impacto: str | None = None, cfg: dict | None = None, **extra) -> str:
    cfg = cfg or load_cfg(root)
    ds = state(read_events(root))
    did = f"D-{len(ds) + 1:03d}"
    datos = {"tipo": extra.pop("tipo", "decision"), "area": area, "titulo": titulo, "decision": decision, "motivo": motivo,
             "impacto": impacto or ("alto" if area in cfg["areas_impacto_alto"] else "medio"), **{k: v for k, v in extra.items() if v}}
    append(root, {"evento": "registrar", "id": did, "actor": {"tipo": origen, "nombre": autor}, "datos": datos})
    render(root)
    return did


# ------------------------------------------------------------------ CLI

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("registrar")
    r.add_argument("--origen", choices=["agente", "humano"], required=True)
    r.add_argument("--autor", required=True)
    r.add_argument("--area", required=True)
    r.add_argument("--titulo", required=True)
    r.add_argument("--decision", required=True)
    r.add_argument("--motivo", default="")
    r.add_argument("--fase", default="")
    r.add_argument("--tipo", choices=TIPOS, default="decision")
    r.add_argument("--impacto", choices=["alto", "medio", "bajo"])
    for k in ("alternativas", "evidencia", "afecta", "ambito", "valor", "preferencia", "excepcion-de", "sustituye"):
        r.add_argument(f"--{k}", default="")
    for name in ("aceptar", "rechazar"):
        s = sub.add_parser(name)
        s.add_argument("id")
        s.add_argument("--por", required=True)
        s.add_argument("--nota", default="")
        if name == "rechazar":
            s.add_argument("--motivo", required=True)
    c = sub.add_parser("comentar")
    c.add_argument("id")
    c.add_argument("--origen", choices=["agente", "humano"], required=True)
    c.add_argument("--autor", required=True)
    c.add_argument("--nota", required=True)
    ls = sub.add_parser("listar")
    ls.add_argument("--estado", choices=ESTADOS)
    ls.add_argument("--origen", choices=["agente", "humano"])
    ls.add_argument("--area")
    ls.add_argument("--pendientes", action="store_true")
    v = sub.add_parser("ver")
    v.add_argument("id")
    ck = sub.add_parser("check")
    ck.add_argument("--gate", action="store_true")
    sub.add_parser("render")
    a = ap.parse_args()

    root = root_of(Path("."))
    cfg = load_cfg(root)
    events = read_events(root)
    ds = state(events)

    if a.cmd == "registrar":
        errs = []
        if a.area not in cfg["areas"]:
            errs.append(f"área '{a.area}' no válida ({', '.join(cfg['areas'])})")
        if bool(a.ambito) != bool(a.valor):
            errs.append("--ambito y --valor van juntos")
        if a.ambito and cfg["ambitos_tecnologicos"] and a.ambito not in cfg["ambitos_tecnologicos"]:
            errs.append(f"ámbito '{a.ambito}' no válido ({', '.join(cfg['ambitos_tecnologicos'])})")
        if a.tipo == "excepcion" and not a.excepcion_de:
            errs.append("una excepción necesita --excepcion-de PREF-NN")
        if a.excepcion_de and a.excepcion_de not in {p["id"] for p in load_prefs(root)}:
            errs.append(f"{a.excepcion_de} no existe en se.preferencias.json")
        if a.sustituye and a.sustituye not in ds:
            errs.append(f"{a.sustituye} no existe")
        if a.origen == "agente" and not a.motivo:
            errs.append("una decisión de agente necesita --motivo")
        if errs:
            print("KO\n  - " + "\n  - ".join(errs))
            return 1
        did = record(root, origen=a.origen, autor=a.autor, area=a.area, titulo=a.titulo, decision=a.decision,
                     motivo=a.motivo, impacto=a.impacto, cfg=cfg, tipo=a.tipo, fase=a.fase,
                     alternativas=split_list(a.alternativas), evidencia=split_list(a.evidencia), afecta=split_list(a.afecta),
                     ambito=a.ambito, valor=a.valor, preferencia=a.preferencia, excepcion_de=a.excepcion_de, sustituye=a.sustituye)
        estado = "aceptada" if a.origen == "humano" else "propuesta"
        print(f"{did} registrada ({estado})")
        perrs, pwarns = preference_findings(state(read_events(root)), load_prefs(root))
        for m in [x for x in perrs + pwarns if x.startswith(did)]:
            print(f"  ! {m}")
        return 0

    if a.cmd in ("aceptar", "rechazar", "comentar"):
        if a.id not in ds:
            print(f"KO: {a.id} no existe")
            return 1
        if a.cmd != "comentar" and ds[a.id]["estado"] != "propuesta":
            print(f"KO: {a.id} está {ds[a.id]['estado']}; solo se aceptan o rechazan propuestas")
            return 1
        ev = {"evento": {"aceptar": "aceptar", "rechazar": "rechazar", "comentar": "comentar"}[a.cmd], "id": a.id,
              "actor": {"tipo": "humano" if a.cmd != "comentar" else a.origen, "nombre": getattr(a, "por", None) or a.autor},
              "nota": (a.motivo if a.cmd == "rechazar" else "") + (" · " if a.cmd == "rechazar" and a.nota else "") + (a.nota or "")}
        append(root, ev)
        render(root)
        print(f"{a.id}: {a.cmd} registrado")
        return 0

    if a.cmd == "listar":
        rows = [d for d in ds.values()
                if (not a.estado or d["estado"] == a.estado) and (not a.origen or d["origen"] == a.origen)
                and (not a.area or d.get("area") == a.area) and (not a.pendientes or d["estado"] == "propuesta")]
        for d in sorted(rows, key=lambda x: x["id"]):
            tec = f" [{d['ambito']} = {d['valor']}]" if d.get("ambito") else ""
            print(f"{d['id']} {d['estado']:<10} {d['origen']:<7} {d.get('impacto', ''):<5} {d.get('area', ''):<12} {d['titulo']}{tec}")
        print(f"({len(rows)} decisiones)")
        return 0

    if a.cmd == "ver":
        d = ds.get(a.id)
        if not d:
            print(f"KO: {a.id} no existe")
            return 1
        print(json.dumps({k: v for k, v in d.items() if k != "historial"}, ensure_ascii=False, indent=2))
        for e in d["historial"]:
            print(f"  {e['ts']} {e['evento']} · {e['actor']['nombre']} ({e['actor']['tipo']}) {e.get('nota', '')}")
        return 0

    if a.cmd == "render":
        print(f"→ {render(root)}")
        return 0

    # check
    errs = chain_errors(events)
    prefs = load_prefs(root)
    pe, pw = preference_findings(ds, prefs)
    de, dw = doc_findings(root, ds, prefs)
    errs += pe + de
    warns = pw + dw
    if a.gate:
        for d in pending_high(ds):
            errs.append(f"{d['id']} ({d.get('area')}, impacto alto) pendiente de aceptación: {d['titulo']}")
    for w in warns:
        print(f"  ! {w}")
    if errs:
        print("KO decisiones")
        for e in errs:
            print(f"  - {e}")
        return 1
    print(f"OK decisiones: {len(ds)} · aceptadas {sum(d['estado'] == 'aceptada' for d in ds.values())} · "
          f"pendientes {sum(d['estado'] == 'propuesta' for d in ds.values())} · eventos {len(events)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

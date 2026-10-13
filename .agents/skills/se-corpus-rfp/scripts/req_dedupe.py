#!/usr/bin/env python3
"""Agrupa hallazgos parecidos para consolidarlos sin duplicados ni pérdidas.

Uso:
  uv run --group se req_dedupe.py groups [raíz]   genera grupos de candidatos a consolidar
  uv run --group se req_dedupe.py lint   [raíz]   valida decisiones, duplicados y capacidades

`groups` compara los hallazgos aún sin consolidar entre sí y contra los requisitos ya
existentes (para no crear RQ nuevos que repiten uno anterior). Solo compara elementos de la
misma categoría (funcional / técnico / otros) y con objeto de negocio en común, salvo
similitud muy alta. Similitud léxica: máximo entre la similitud del texto (TF-IDF sobre raíces y
trigramas, sin dependencias) y la media de texto y coincidencia de objeto de negocio; así
se detectan paráfrasis ("lista priorizada" / "ranking") cuando el objeto coincide.
Con `dedupe.backend = "azure"` se añade la similitud por embeddings (caché en
req-scan/embeddings.jsonl): un par es candidato si lo es por cualquiera de las dos vías.
Los conflictos de valores se detectan siempre comparando números (los embeddings no los
distinguen). Si el backend falla se continúa en modo léxico con aviso.

Salidas: proposal/_meta/req-scan/grupos.json (acumulativo) y grupos.md (pendientes).

Cada grupo exige una decisión en `decisiones` del registro:
  duplicado | refinamiento | complementario | conflicto | distinto | mixto
`lint` (también lo ejecuta `req_scan.py check`) comprueba que las decisiones existen y son
coherentes con la consolidación, que no quedan RQ casi idénticos sin justificar, y que las
capacidades están bien formadas.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import sys
import unicodedata
from collections import Counter
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "se-core/scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from reqlib import category, load_config, load_registry  # noqa: E402
from embeddings import dot, get_embedder  # noqa: E402

RELATIONS = ["duplicado", "refinamiento", "complementario", "conflicto", "distinto", "mixto"]
STOP = set("""el la los las un una unos unas de del al a en y e o u que se su sus por para con sin como
cual cuales debe deben debera deberan podra podran puede pueden poder sistema solucion plataforma
herramienta aplicacion ser sera seran estar cada lo le les este esta estos estas ese esa mediante
todo toda todos todas otro otra mas muy entre sobre segun asi tambien desde hasta cuando donde
permitir permita permitira necesario necesaria requiere requerira usuario usuarios""".split())
SUFFIXES = ("aciones", "acion", "amientos", "amiento", "imientos", "imiento", "mente", "adores", "ador",
            "adas", "ados", "idas", "idos", "ada", "ado", "ida", "ido", "ando", "iendo", "ales", "al",
            "ar", "er", "ir", "es", "s", "a", "o", "e")
NUM = re.compile(r"\d+(?:[.,]\d+)?")


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s.lower()) if not unicodedata.combining(c))


def stem(w: str) -> str:
    for suf in SUFFIXES:
        if len(w) > len(suf) + 3 and w.endswith(suf):
            return w[: -len(suf)]
    return w


def stems(s: str) -> list[str]:
    return [stem(w) for w in re.findall(r"[a-z0-9]+", strip_accents(s)) if w not in STOP and not w.isdigit()]


def numbers(s: str) -> set[str]:
    return {n.replace(",", ".") for n in NUM.findall(s)}


def features(s: str) -> Counter:
    st = stems(s)
    f = Counter(st)
    for w in st:
        p = f"_{w}_"
        for i in range(len(p) - 2):
            f["#" + p[i:i + 3]] += 0.3
    return f


def tfidf(docs: list[Counter]) -> list[dict]:
    n = len(docs)
    df = Counter(k for d in docs for k in d)
    vecs = []
    for d in docs:
        v = {k: tf * (math.log((n + 1) / (df[k] + 1)) + 1) for k, tf in d.items()}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        vecs.append({k: x / norm for k, x in v.items()})
    return vecs


def cos(a: dict, b: dict) -> float:
    if len(a) > len(b):
        a, b = b, a
    return sum(x * b.get(k, 0.0) for k, x in a.items())


def canon(f: dict) -> str:
    return " ".join(f.get(k, "") or "" for k in ("accion", "objeto", "condicion", "texto"))


def nodes(opp: Path, cfg: dict, findings: list[dict], reg: dict) -> tuple[list[dict], list[dict]]:
    """Nodos comparables: hallazgos sin consolidar y requisitos existentes."""
    by_h = {f["id"]: f for f in findings}
    assigned = {h for r in reg["requisitos"] for h in r.get("hallazgos", [])} | {d["hallazgo"] for d in reg["descartados"]}
    pending = [{"id": f["id"], "kind": "hallazgo", "cat": category(cfg, f["tipo"]) or "funcional", "text": canon(f),
                "objeto": f.get("objeto", ""), "data": f} for f in findings if f["id"] not in assigned]
    existing = []
    for r in reg["requisitos"]:
        hs = [by_h[h] for h in r.get("hallazgos", []) if h in by_h]
        existing.append({"id": r["id"], "kind": "requisito", "cat": category(cfg, r.get("tipo", "")) or "funcional",
                         "text": " ".join([r.get("texto", "")] + [canon(h) for h in hs]),
                         "objeto": " ".join(h.get("objeto", "") for h in hs) or r.get("texto", ""), "data": r})
    return pending, existing


def thresholds(dcfg: dict) -> tuple[dict, dict]:
    lex = dcfg.get("lexico") or {"alta": dcfg.get("alta", 0.8), "revisar": dcfg.get("revisar", 0.5)}
    emb = dcfg.get(dcfg.get("backend", "lexico"), {}) or {}
    return lex, {"alta": emb.get("alta", 0.85), "revisar": emb.get("revisar", 0.72)}


def engine(opp: Path, dcfg: dict):
    emb, msg = get_embedder(opp, dcfg)
    if msg.startswith("AVISO"):
        print(msg)
    return emb, msg


def embed_safe(emb, texts: list[str]) -> list | None:
    if emb is None or not texts:
        return None
    try:
        return emb.embed(texts)
    except Exception as exc:  # noqa: BLE001
        print(f"AVISO: fallo al calcular embeddings ({exc}); se usa el modo léxico")
        return None


def pair_hint(a: dict, b: dict, sim: float, oj: float, alta: float, e: float | None = None, e_alta: float = 1.1,
              e_rev: float = 1.1) -> str:
    na, nb = numbers(a["text"]), numbers(b["text"])
    if na and nb and na != nb and (max(sim, oj) >= alta * 0.8 or (e is not None and e >= e_alta - 0.1)):
        return "posible conflicto (valores distintos)"
    if sim >= alta or (e is not None and e >= e_alta):
        return "duplicado probable"
    if oj >= 0.5:
        return "mismo objeto de negocio, redacción distinta: posible duplicado o refinamiento"
    if e is not None and e >= e_rev:
        return "significado parecido con otras palabras: posible duplicado o refinamiento"
    sa, sb = set(stems(a["text"])), set(stems(b["text"]))
    if sa and sb and (sa < sb or sb < sa):
        return "posible refinamiento"
    return "revisar"


def build_groups(opp: Path, cfg: dict, findings: list[dict], reg: dict, emb=None) -> tuple[list[dict], list[dict]]:
    lex, eth = thresholds(cfg["dedupe"])
    pending, existing = nodes(opp, cfg, findings, reg)
    allnodes = pending + existing
    vecs = tfidf([features(n["text"]) for n in allnodes])
    evecs = embed_safe(emb, [n["text"] for n in allnodes])
    obj = [set(stems(n["objeto"])) for n in allnodes]
    parent = list(range(len(allnodes)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    pairs = []
    for i in range(len(pending)):
        for j in range(i + 1, len(allnodes)):
            a, b = allnodes[i], allnodes[j]
            if a["cat"] != b["cat"]:
                continue
            text = cos(vecs[i], vecs[j])
            oj = len(obj[i] & obj[j]) / len(obj[i] | obj[j]) if obj[i] | obj[j] else 0.0
            sim = max(text, 0.5 * text + 0.5 * oj)
            e = dot(evecs[i], evecs[j]) if evecs else None
            lex_ok = sim >= lex["revisar"] and (bool(obj[i] & obj[j]) or text >= lex["alta"])
            if not lex_ok and not (e is not None and e >= eth["revisar"]):
                continue
            pairs.append((i, j, round(sim, 3), round(text, 3), round(oj, 2), None if e is None else round(e, 3)))
            parent[find(i)] = find(j)
    comps: dict[int, list[int]] = {}
    for i in range(len(allnodes)):
        comps.setdefault(find(i), []).append(i)
    groups, singles = [], []
    for members in comps.values():
        if not any(m < len(pending) for m in members):
            continue
        if len(members) == 1:
            singles.append(allnodes[members[0]])
            continue
        ids = sorted(allnodes[m]["id"] for m in members)
        gid = "G-" + hashlib.sha1("|".join(ids).encode()).hexdigest()[:8]
        ps = [{"a": allnodes[i]["id"], "b": allnodes[j]["id"], "similitud": s, "texto": t, "objeto": oj, "embedding": e,
               "pista": pair_hint(allnodes[i], allnodes[j], t, oj, lex["alta"], e, eth["alta"], eth["revisar"])}
              for i, j, s, t, oj, e in pairs if i in members and j in members]
        groups.append({"id": gid, "miembros": ids, "pares": sorted(ps, key=lambda p: -p["similitud"]),
                       "detalle": {allnodes[m]["id"]: _summary(allnodes[m]) for m in members}})
    return groups, singles


def _summary(n: dict) -> dict:
    d = n["data"]
    if n["kind"] == "requisito":
        return {"tipo": d.get("tipo"), "texto": d.get("texto"), "capacidad": d.get("capacidad", ""), "estado": d.get("estado")}
    return {k: d.get(k, "") for k in ("tipo", "texto", "actor", "accion", "objeto", "condicion", "doc", "loc")}


def groups_path(opp: Path) -> Path:
    return opp / "proposal/_meta/req-scan/grupos.json"


def cmd_groups(opp: Path) -> int:
    from req_scan import collect
    cfg = load_config(opp)
    findings, bad, pending_units = collect(opp, cfg)
    if pending_units or bad:
        print(f"AVISO: barrido incompleto ({len(pending_units)} pendientes, {len(bad)} con errores); los grupos serán parciales")
    reg = load_registry(opp)
    emb, backend = engine(opp, cfg["dedupe"])
    groups, singles = build_groups(opp, cfg, findings, reg, emb)
    gp = groups_path(opp)
    store = json.loads(gp.read_text(encoding="utf-8")) if gp.exists() else {"hallazgos_considerados": [], "grupos": {}}
    for g in groups:
        store["grupos"][g["id"]] = {k: g[k] for k in ("miembros", "pares")}
    store["backend"] = backend if not backend.startswith("AVISO") else "lexico (fallback)"
    store["hallazgos_considerados"] = sorted(set(store["hallazgos_considerados"]) | {f["id"] for f in findings})
    gp.write_text(json.dumps(store, ensure_ascii=False, indent=2), encoding="utf-8")
    decided = {d["grupo"] for d in reg["decisiones"]}
    lines = ["# Grupos de requisitos a consolidar", "", f"> Generado: {date.today().isoformat()} · similitud: {store['backend']} · grupos nuevos: {len(groups)} · "
             f"hallazgos sin similares: {len(singles)}", "",
             "Para cada grupo decide la relación (ver `references/consolidacion.md`), actualiza el registro y anota la decisión.", ""]
    for g in groups:
        state = "decidido" if g["id"] in decided else "PENDIENTE"
        lines += [f"## {g['id']} · {state}", "", "| Elemento | Tipo | Texto | Forma canónica / capacidad | Origen |", "| --- | --- | --- | --- | --- |"]
        for mid in g["miembros"]:
            d = g["detalle"][mid]
            if mid.startswith("H-"):
                can = " · ".join(x for x in [d["actor"], d["accion"], d["objeto"], d["condicion"]] if x)
                lines.append(f"| `{mid}` | {d['tipo']} | {d['texto']} | {can} | `{d['doc']}` {d['loc']} |")
            else:
                lines.append(f"| `{mid}` (existente) | {d['tipo']} | {d['texto']} | {d['capacidad']} · {d['estado']} | registro |")
        lines += ["", "Pares: " + "; ".join(f"`{p['a']}`↔`{p['b']}` léx {p['similitud']}"
                                + (f" · emb {p['embedding']}" if p.get("embedding") is not None else "")
                                + f" ({p['pista']})" for p in g["pares"]), ""]
    if singles:
        lines += ["## Hallazgos sin similares", "", "Cada uno da lugar a un requisito propio (o se descarta con motivo).", ""]
        lines += [f"- `{n['id']}` ({n['data']['tipo']}): {n['data']['texto']}" for n in singles]
    out = gp.with_name("grupos.md")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"grupos: {len(groups)} ({sum(g['id'] not in decided for g in groups)} pendientes de decisión) · "
          f"sin similares: {len(singles)} → {out}")
    big = [g for g in groups if len(g["miembros"]) > 12]
    if big:
        print(f"AVISO: {len(big)} grupos con más de 12 elementos; el umbral 'revisar' es probablemente demasiado bajo "
              f"(los parecidos se encadenan). Súbelo en se.config.json o recalibra con menor --recall.")
    return 0


def lint(opp: Path, cfg: dict, findings: list[dict], reg: dict, emb="auto") -> tuple[list[str], list[str]]:
    th = cfg["dedupe"]
    lex, eth = thresholds(th)
    if emb == "auto":
        emb, _ = engine(opp, th)
    errs, warns = [], []
    fids = {f["id"] for f in findings}
    h2rq = {h: r["id"] for r in reg["requisitos"] for h in r.get("hallazgos", [])}
    rq = {r["id"]: r for r in reg["requisitos"]}
    gp = groups_path(opp)
    store = json.loads(gp.read_text(encoding="utf-8")) if gp.exists() else None

    # 1. agrupación al día
    if fids and store is None:
        errs.append("no se han generado grupos de similares: ejecuta req_dedupe.py groups antes de consolidar")
        store = {"hallazgos_considerados": [], "grupos": {}}
    new = fids - set(store["hallazgos_considerados"])
    if new and gp.exists():
        errs.append(f"{len(new)} hallazgos nuevos no pasaron por req_dedupe.py groups")

    # 2. decisiones
    decisions = {}
    for d in reg["decisiones"]:
        g = d.get("grupo")
        if g in decisions:
            errs.append(f"decisión duplicada para {g}")
        decisions[g] = d
        if g not in store["grupos"]:
            errs.append(f"decisión sobre grupo desconocido {g}")
            continue
        rel = d.get("relacion")
        if rel not in RELATIONS:
            errs.append(f"{g}: relación '{rel}' no válida ({', '.join(RELATIONS)})")
            continue
        if rel != "duplicado" and not (d.get("motivo") or "").strip():
            errs.append(f"{g}: la relación '{rel}' exige 'motivo'")
        members = store["grupos"][g]["miembros"]
        targets = {m if not m.startswith("H-") else h2rq.get(m) for m in members}
        targets.discard(None)
        if rel in ("duplicado", "refinamiento") and len(targets) > 1:
            errs.append(f"{g}: '{rel}' pero los elementos acaban en {', '.join(sorted(targets))}; deben fusionarse en uno")
        if rel in ("complementario", "distinto", "conflicto") and len(targets) < 2:
            errs.append(f"{g}: '{rel}' pero todo se fusionó en {', '.join(targets) or 'nada'}")
        if rel == "refinamiento":
            for t in targets:
                if t in rq and not rq[t].get("detalles"):
                    warns.append(f"{g}: refinamiento en {t} sin 'detalles'; ¿se perdió la versión menos específica?")
        if rel == "conflicto":
            q = d.get("pregunta", "")
            if not re.fullmatch(r"Q-\d{3}", q or ""):
                errs.append(f"{g}: un conflicto exige 'pregunta' (Q-NNN) al cliente")
            else:
                qf = opp / "proposal/3-questions-for-client.md"
                if qf.exists() and q not in qf.read_text(encoding="utf-8"):
                    errs.append(f"{g}: la pregunta {q} no figura en 3-questions-for-client.md")
            for t in targets:
                if t in rq and rq[t].get("estado") != "A confirmar":
                    errs.append(f"{g}: {t} está en conflicto y su estado debe ser 'A confirmar'")
    for g in store["grupos"]:
        if g not in decisions and any(m in fids for m in store["grupos"][g]["miembros"]):
            errs.append(f"grupo {g} sin decisión de consolidación")

    # 3. RQ casi idénticos sin justificar
    justified = set()
    for g, d in decisions.items():
        if d.get("relacion") in ("complementario", "conflicto", "distinto", "mixto") and g in store["grupos"]:
            ts = {m if not m.startswith("H-") else h2rq.get(m) for m in store["grupos"][g]["miembros"]} - {None}
            justified |= {frozenset((a, b)) for a in ts for b in ts if a != b}
    by_h = {f["id"]: f for f in findings}
    reqs = reg["requisitos"]
    rtexts = [" ".join([r.get("texto", "")] + [canon(by_h[h]) for h in r.get("hallazgos", []) if h in by_h]) for r in reqs]
    vecs = tfidf([features(t) for t in rtexts])
    evecs = embed_safe(emb, rtexts)
    for i in range(len(reqs)):
        for j in range(i + 1, len(reqs)):
            a, b = reqs[i], reqs[j]
            if category(cfg, a.get("tipo", "")) != category(cfg, b.get("tipo", "")):
                continue
            s = cos(vecs[i], vecs[j])
            e = dot(evecs[i], evecs[j]) if evecs else None
            if (s >= lex["alta"] or (e is not None and e >= eth["alta"])) and frozenset((a["id"], b["id"])) not in justified:
                how = f"léx {s:.2f}" + (f", emb {e:.2f}" if e is not None else "")
                errs.append(f"{a['id']} y {b['id']} son casi idénticos ({how}) sin decisión que justifique mantenerlos separados")

    # 4. capacidades
    caps = {}
    for c in reg["capacidades"]:
        cid = c.get("id", "")
        if not re.fullmatch(r"CAP-\d{2}", cid):
            errs.append(f"capacidad con ID no válido: '{cid}'")
        if cid in caps:
            errs.append(f"capacidad duplicada: {cid}")
        if not (c.get("nombre") or "").strip():
            errs.append(f"{cid}: falta 'nombre'")
        caps[cid] = c
    names = Counter(strip_accents(c.get("nombre", "")).strip() for c in reg["capacidades"])
    for n, k in names.items():
        if n and k > 1:
            errs.append(f"varias capacidades con el mismo nombre: '{n}'")
    count = Counter()
    func = Counter()
    for r in reqs:
        cat = category(cfg, r.get("tipo", ""))
        cap = r.get("capacidad", "")
        if r.get("estado") == "Fuera de alcance" and not cap:
            continue
        if cat == "funcional" and cap not in caps:
            errs.append(f"{r['id']}: requisito funcional sin capacidad válida ('{cap}')")
        elif cat == "tecnico" and cap not in caps and cap != "TRANSVERSAL":
            errs.append(f"{r['id']}: requisito técnico sin capacidad ni TRANSVERSAL ('{cap}')")
        elif cat == "otros" and cap and cap not in caps and cap != "TRANSVERSAL":
            errs.append(f"{r['id']}: capacidad desconocida '{cap}'")
        if cap in caps:
            count[cap] += 1
            func[cap] += cat == "funcional"
    for cid in caps:
        if not func[cid]:
            errs.append(f"{cid}: capacidad sin requisitos funcionales; si es técnica, usa TRANSVERSAL o intégrala en otra")
        if count[cid] > th["max_rq_por_capacidad"]:
            warns.append(f"{cid}: {count[cid]} requisitos; probablemente agrupa varias capacidades, considera dividirla")
    return errs, warns


def cmd_lint(opp: Path) -> int:
    from req_scan import collect
    cfg = load_config(opp)
    findings, _, _ = collect(opp, cfg)
    errs, warns = lint(opp, cfg, findings, load_registry(opp))
    for w in warns:
        print(f"  ! {w}")
    if errs:
        print("KO consolidación")
        for e in errs:
            print(f"  - {e}")
        return 1
    print("OK consolidación")
    return 0


def main() -> int:
    if len(sys.argv) not in (2, 3) or sys.argv[1] not in ("groups", "lint"):
        print(__doc__)
        return 2
    opp = Path(sys.argv[2] if len(sys.argv) == 3 else ".").resolve()
    return cmd_groups(opp) if sys.argv[1] == "groups" else cmd_lint(opp)


if __name__ == "__main__":
    sys.exit(main())

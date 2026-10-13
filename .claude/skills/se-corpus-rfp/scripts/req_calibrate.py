#!/usr/bin/env python3
"""Calibra los umbrales de similitud con consolidaciones ya hechas.

Uso:
  uv run --group se req_calibrate.py [workspace ...] [--precision 0.9] [--recall 0.95] [--write-config]

Toma como datos etiquetados los registros de requisitos de una o varias oportunidades:
dos hallazgos de la misma categoría asignados al mismo RQ son un par "fusionar"; asignados
a RQ distintos, un par "separar". Para cada medida (léxica y, si está configurado, el
backend de embeddings) propone:
  alta     menor umbral con precisión >= --precision (pares por encima: casi seguro fusionar)
  revisar  mayor umbral con recall >= --recall (por debajo apenas quedan pares a fusionar)

Escribe proposal/_meta/req-scan/calibracion.md en la primera oportunidad y, con
--write-config, guarda los umbrales en se.config.json.
Usa pocas oportunidades consolidadas con cuidado: los umbrales son tan buenos como esas decisiones.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "se-core/scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from reqlib import category, load_config, load_registry  # noqa: E402
from req_dedupe import canon, cos, engine, embed_safe, features, stems, tfidf  # noqa: E402
from embeddings import dot  # noqa: E402

MAX_PAIRS = 60000
MIN_POS = 15


def labeled_pairs(opp: Path, cfg: dict, emb) -> list[tuple[bool, float, float | None]]:
    from req_scan import collect
    findings, _, _ = collect(opp, cfg)
    reg = load_registry(opp)
    h2rq = {h: r["id"] for r in reg["requisitos"] for h in r.get("hallazgos", [])}
    items = [f for f in findings if f["id"] in h2rq]
    texts = [canon(f) for f in items]
    vecs = tfidf([features(t) for t in texts])
    objs = [set(stems(f.get("objeto", ""))) for f in items]
    evecs = embed_safe(emb, texts)
    cats = [category(cfg, f["tipo"]) for f in items]
    idx = [(i, j) for i in range(len(items)) for j in range(i + 1, len(items)) if cats[i] == cats[j]]
    pos = [p for p in idx if h2rq[items[p[0]]["id"]] == h2rq[items[p[1]]["id"]]]
    neg = [p for p in idx if h2rq[items[p[0]]["id"]] != h2rq[items[p[1]]["id"]]]
    random.Random(7).shuffle(neg)
    neg = neg[: max(0, MAX_PAIRS - len(pos))]
    out = []
    for label, ps in ((True, pos), (False, neg)):
        for i, j in ps:
            t = cos(vecs[i], vecs[j])
            u = objs[i] | objs[j]
            oj = len(objs[i] & objs[j]) / len(u) if u else 0.0
            e = dot(evecs[i], evecs[j]) if evecs else None
            out.append((label, max(t, 0.5 * t + 0.5 * oj), e))
    return out


def calibrate(scores: list[tuple[bool, float]], precision: float, recall: float) -> dict:
    pos = sorted(s for lab, s in scores if lab)
    neg = sorted(s for lab, s in scores if not lab)
    if not pos:
        return {"pos": 0, "neg": len(neg)}
    cands = sorted({round(s, 3) for _, s in scores})

    def stats(t):
        tp = sum(s >= t for s in pos)
        fp = sum(s >= t for s in neg)
        return tp, fp, (tp / (tp + fp) if tp + fp else 1.0), tp / len(pos)
    alta = next((t for t in cands if stats(t)[2] >= precision), None)
    revisar = max((t for t in cands if stats(t)[3] >= recall), default=None)
    pct = lambda xs, q: xs[min(len(xs) - 1, int(q * len(xs)))] if xs else None  # noqa: E731
    res = {"pos": len(pos), "neg": len(neg), "alta": alta, "revisar": revisar,
           "pos_p05": pct(pos, 0.05), "pos_p50": pct(pos, 0.5), "neg_p50": pct(neg, 0.5), "neg_p95": pct(neg, 0.95)}
    if alta is not None:
        tp, fp, p, r = stats(alta)
        res["alta_info"] = f"precisión {p:.2f}, recall {r:.2f}"
    if revisar is not None:
        tp, fp, p, r = stats(revisar)
        res["revisar_info"] = f"recall {r:.2f}, pares a revisar {tp + fp} ({fp} acabarían separados)"
    return res


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("opps", nargs="*", default=["."], help="workspaces consolidados (por defecto, el actual)")
    ap.add_argument("--precision", type=float, default=0.9)
    ap.add_argument("--recall", type=float, default=0.95)
    ap.add_argument("--write-config", action="store_true")
    a = ap.parse_args()
    opps = [Path(o).resolve() for o in a.opps]
    cfg = load_config(opps[0])
    dcfg = cfg["dedupe"]
    emb, backend = engine(opps[0], dcfg)
    data = []
    for o in opps:
        e = emb
        if emb is not None and o != opps[0]:
            e, _ = engine(o, dcfg)
        data += labeled_pairs(o, cfg, e)
    results = {"lexico": calibrate([(lab, s) for lab, s, _ in data], a.precision, a.recall)}
    if any(e is not None for _, _, e in data):
        results[dcfg["backend"]] = calibrate([(lab, e) for lab, _, e in data if e is not None], a.precision, a.recall)
    lines = ["# Calibración de umbrales de similitud", "",
             f"> Fecha: {date.today().isoformat()} · oportunidades: {len(opps)} · similitud: {backend} · "
             f"objetivo: precisión ≥ {a.precision} en `alta`, recall ≥ {a.recall} en `revisar`", ""]
    ok = True
    for name, r in results.items():
        lines += [f"## {name}", "", f"- Pares fusionados: {r['pos']} · pares separados: {r['neg']}"]
        if r["pos"] < MIN_POS:
            lines.append(f"- Datos insuficientes (mínimo {MIN_POS} pares fusionados): no se proponen umbrales")
            ok = False
            continue
        lines += [f"- Fusionados: p05 {r['pos_p05']:.3f} · mediana {r['pos_p50']:.3f}",
                  f"- Separados: mediana {r['neg_p50']:.3f} · p95 {r['neg_p95']:.3f}",
                  f"- **alta = {r['alta']}** ({r.get('alta_info', 'no alcanzable')})",
                  f"- **revisar = {r['revisar']}** ({r.get('revisar_info', 'no alcanzable')})", ""]
        load = r.get("revisar_info", "")
        if "pares a revisar" in load and int(load.split("pares a revisar ")[1].split()[0]) > 5 * r["pos"]:
            lines.append("- Aviso: el umbral `revisar` genera mucha carga de revisión y grupos encadenados; "
                         "prueba con un --recall menor (p. ej. 0.9).")
        if r["alta"] is not None and r["revisar"] is not None and r["revisar"] > r["alta"]:
            lines.append("- Aviso: revisar > alta; la medida separa mal. Revisa la calidad de la consolidación.")
    out = opps[0] / "proposal/_meta/req-scan/calibracion.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[4:]))
    print(f"→ {out}")
    if a.write_config and ok:
        conf = next((d / "se.config.json" for d in [opps[0], *opps[0].parents] if (d / "se.config.json").is_file()), None)
        if conf is None:
            print("No se encontró se.config.json")
            return 1
        full = json.loads(conf.read_text(encoding="utf-8"))
        dd = full.setdefault("requirements", {}).setdefault("dedupe", {})
        for name, r in results.items():
            if r.get("alta") is not None and r.get("revisar") is not None:
                dd.setdefault(name, {}).update({"alta": r["alta"], "revisar": min(r["revisar"], r["alta"])})
        conf.write_text(json.dumps(full, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"umbrales guardados en {conf}")
    elif a.write_config:
        print("No se guardan umbrales: datos insuficientes")
    return 0


if __name__ == "__main__":
    sys.exit(main())

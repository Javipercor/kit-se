#!/usr/bin/env python3
"""Gate de aprobación de historias de usuario del documento HU-Enfoque-Funcional.

Uso:
  uv run --group se hu_gate.py status  <HU-Enfoque-Funcional-*.md>
  uv run --group se hu_gate.py approve <HU-Enfoque-Funcional-*.md> [--by "Nombre"]
  uv run --group se hu_gate.py check   <HU-Enfoque-Funcional-*.md>

status  : propuesta | aprobada | modificada, y cobertura de requisitos
approve : valida las HUs de la sección 2 y la cobertura de requisitos (todo requisito
          funcional y técnico ligado a una HU, transversal o fuera de alcance con motivo),
          guarda la instantánea (HUs + transversales + exclusiones) en
          proposal/_meta/hu-aprobadas-<slug>.json y marca el documento "HUs aprobadas".
          Solo debe ejecutarse tras aprobación explícita de una persona.
check   : exit 1 si no hay aprobación o si la sección 2 cambió desde la aprobación.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "se-core/scripts"))
from req_coverage import compute  # noqa: E402
from decisiones import record as record_decision  # noqa: E402

HU_HEAD = re.compile(r"^### (HU-[A-Z][A-Z0-9]{1,5}-\d{2})\. (.+?)\s*$")
FIELDS = {"como": re.compile(r"^\*\*Como\*\*\s+(.+?),?\s*$"),
          "quiero": re.compile(r"^\*\*quiero\*\*\s+(.+?),?\s*$"),
          "para": re.compile(r"^\*\*para\*\*\s+(.+?)\.?\s*$"),
          "requisitos": re.compile(r"^\*\*Requisitos:\*\*\s+(.+?)\s*$")}
TRANS = re.compile(r"^\*\*Requisitos transversales:\*\*\s+(.+?)\s*$")
TECH_ACTORS = re.compile(r"\b(arquitect\w*|desarrollador\w*|developer|devops|backend|frontend|data scientist|"
                         r"cient[ií]fico de datos|ingeniero de datos|qa|tester|sistema)\b", re.I)


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", s)).strip()


def section2(text: str) -> list[str]:
    lines = text.splitlines()
    start = next((i for i, l in enumerate(lines) if re.match(r"^## 2\. ", l)), None)
    if start is None:
        return []
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    return lines[start + 1:end]


def parse(text: str) -> tuple[list[dict], list[str]]:
    hus, errors, cur = [], [], None
    for l in section2(text):
        if TRANS.match(l.strip()):
            continue
        if m := HU_HEAD.match(l):
            cur = {"id": m[1], "titulo": norm(m[2])}
            hus.append(cur)
            continue
        if cur is None:
            continue
        for k, rx in FIELDS.items():
            if (m := rx.match(l.strip())) and k not in cur:
                cur[k] = norm(m[1])
    if not hus:
        errors.append("La sección 2 no contiene historias '### HU-<ACR>-NN. <Nombre>'")
    ids = [h["id"] for h in hus]
    for d in sorted({i for i in ids if ids.count(i) > 1}):
        errors.append(f"ID duplicado: {d}")
    acr = {i.split("-")[1] for i in ids}
    if len(acr) > 1:
        errors.append(f"Acrónimos distintos en las HUs: {', '.join(sorted(acr))}")
    for h in hus:
        for k in ("como", "quiero", "para", "requisitos"):
            if k not in h:
                errors.append(f"{h['id']}: falta la línea '**{k.capitalize() if k != 'requisitos' else 'Requisitos:'}**'")
        if "como" in h and TECH_ACTORS.search(h["como"]):
            errors.append(f"{h['id']}: el actor debe ser un rol de negocio ('{h['como']}')")
        if "requisitos" in h and not re.search(r"\b(RQ-(HU-)?\d{3}|R[FT]-?\d+|RNF-?\d+)", h["requisitos"]):
            errors.append(f"{h['id']}: '**Requisitos:**' no referencia ningún requisito")
    return hus, errors


def transversales(text: str) -> str:
    return " ".join(norm(m[1]) for l in section2(text) if (m := TRANS.match(l.strip())))


def exclusions(cov: dict | None) -> list[dict]:
    if not cov:
        return []
    return [{"id": r["id"], "motivo": norm(r.get("motivo_exclusion", ""))} for r in cov["excluded"]]


def coverage(doc: Path) -> dict | None:
    opp = doc.resolve().parent.parent
    cov = compute(opp, doc)
    return None if cov["source"] == "ninguno" else cov


def digest(hus: list[dict], trans: str = "", excl: list | None = None) -> str:
    payload = {"hus": hus, "transversales": trans, "exclusiones": excl or []}
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def snapshot_path(doc: Path) -> Path:
    slug = re.sub(r"^HU-Enfoque-Funcional-?", "", doc.stem) or "default"
    return doc.parent / "_meta" / f"hu-aprobadas-{slug}.json"


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in {"status", "approve", "check"}:
        print(__doc__)
        return 2
    cmd = sys.argv[1]
    if len(sys.argv) > 2 and not sys.argv[2].startswith("--"):
        doc = Path(sys.argv[2])
    else:
        found = sorted(Path("proposal").glob("HU-Enfoque-Funcional*.md"))
        if len(found) != 1:
            print("ERROR: indica el documento funcional (no hay uno único en proposal/)")
            return 2
        doc = found[0]
    text = doc.read_text(encoding="utf-8")
    hus, errors = parse(text)
    cov = coverage(doc)
    trans, excl = transversales(text), exclusions(cov)
    snap = snapshot_path(doc)
    approved = json.loads(snap.read_text(encoding="utf-8")) if snap.exists() else None
    state = "propuesta" if not approved else ("aprobada" if approved["hash"] == digest(hus, trans, excl) else "modificada")
    cov_line = ("cobertura: sin baseline de requisitos (no verificable)" if cov is None else
                f"cobertura: {cov['pct']} % · huecos {len(cov['gaps'])} · fuera de alcance {len(cov['excluded'])} · errores {len(cov['errors'])}")

    if cmd == "status":
        print(f"estado: {state} · HUs: {len(hus)}" + (f" · aprobadas el {approved['fecha']} por {approved['aprobado_por']}" if approved else ""))
        if state == "modificada":
            old = {h["id"]: h for h in approved["hus"]}
            new = {h["id"]: h for h in hus}
            for i in sorted(old.keys() | new.keys()):
                if i not in new:
                    print(f"  - eliminada: {i}")
                elif i not in old:
                    print(f"  - nueva: {i}")
                elif old[i] != new[i]:
                    print(f"  - cambiada: {i}")
            if approved.get("transversales", "") != trans:
                print("  - cambiados los requisitos transversales")
            if approved.get("exclusiones", []) != excl:
                print("  - cambiadas las exclusiones (fuera de alcance)")
        print(cov_line)
        for e in (cov or {}).get("errors", []):
            print(f"  ! {e}")
        for e in errors:
            print(f"  ! {e}")
        return 0

    if cmd == "approve":
        if cov is not None:
            errors += [f"cobertura: {e}" for e in cov["errors"]]
        if errors:
            print("KO: no se puede aprobar")
            for e in errors:
                print(f"  - {e}")
            return 1
        by = sys.argv[sys.argv.index("--by") + 1] if "--by" in sys.argv else "usuario"
        version = (approved or {}).get("version", 0) + 1
        data = {"documento": doc.name, "version": version, "fecha": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "aprobado_por": by, "hash": digest(hus, trans, excl), "hus": hus, "transversales": trans,
                "exclusiones": excl, "cobertura_pct": None if cov is None else cov["pct"]}
        snap.parent.mkdir(parents=True, exist_ok=True)
        snap.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        new_text = re.sub(r"(\*\*Estado:\*\*) [^·\n]+", r"\1 HUs aprobadas ", text, count=1)
        doc.write_text(new_text, encoding="utf-8")
        print(f"OK: {len(hus)} HUs aprobadas (v{version}) → {snap}")
        did = record_decision(doc.resolve().parent.parent, origen="humano", autor=by, area="alcance",
                              titulo=f"Aprobación de HUs v{version} ({doc.name})",
                              decision=f"Se aprueban {len(hus)} HUs: " + ", ".join(h["id"] for h in hus)
                              + (f"; fuera de alcance: {', '.join(e['id'] for e in excl)}" if excl else ""),
                              motivo="Gate de aprobación del enfoque funcional", fase="1",
                              afecta=[h["id"] for h in hus] + [e["id"] for e in excl],
                              evidencia=[str(snap.relative_to(doc.resolve().parent.parent))])
        print(f"decisión registrada: {did}")
        print(cov_line)
        if excl:
            print("  exclusiones aprobadas: " + ", ".join(e["id"] for e in excl))
        return 0

    if state != "aprobada":
        print(f"KO: HUs en estado '{state}'" + (" (ejecuta 'status' para ver cambios y vuelve a aprobar)" if state == "modificada" else ""))
        return 1
    print(f"OK: sección 2 coincide con la aprobación v{approved['version']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

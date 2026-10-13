#!/usr/bin/env python3
"""Valida specs de features en proposal/specs/.

Uso: uv run --group se validate_spec.py [raíz]
Comprueba índice, estructura de cada spec.md, criterios AC-FNNN-NN en formato
Dado/Cuando/Entonces, trazabilidad a HU y coherencia índice ↔ carpetas.
"""
from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

HEADINGS = ["1. Resumen", "2. Trazabilidad", "3. Alcance", "4. Comportamiento", "5. Criterios De Aceptación",
            "6. Contratos", "7. Requisitos De IA", "8. Requisitos No Funcionales", "9. Telemetría",
            "10. Casos Límite Y Errores", "11. Dependencias Y Preguntas Abiertas", "12. Definition Of Ready"]
AC = re.compile(r"^- \*\*(AC-F(\d{3})-\d{2})\*\* (.+)$", re.M)
PH = re.compile(r"<(?!br)[^<>\n]{2,80}>|AAAA-MM-DD|\bTODO\b")


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c)).lower().strip()


def main() -> int:
    if len(sys.argv) > 2:
        print(__doc__)
        return 2
    specs = Path(sys.argv[1] if len(sys.argv) == 2 else ".").resolve() / "proposal/specs"
    errors: list[str] = []
    index = specs / "README.md"
    if not index.exists():
        print("KO: falta proposal/specs/README.md")
        return 1
    idx_ids = set(re.findall(r"^\|\s*(F-\d{3})\s*\|", index.read_text(encoding="utf-8"), re.M))
    dirs = {d.name[:5]: d for d in specs.iterdir() if d.is_dir() and re.match(r"F-\d{3}-", d.name)}
    for missing in sorted(idx_ids - dirs.keys()):
        errors.append(f"{missing} está en el índice pero no tiene carpeta (válido solo en modo índice)")
    for extra in sorted(dirs.keys() - idx_ids):
        errors.append(f"{extra} tiene carpeta pero no está en el índice")
    for fid, d in sorted(dirs.items()):
        f = d / "spec.md"
        if not f.exists():
            errors.append(f"{d.name}: falta spec.md")
            continue
        text = f.read_text(encoding="utf-8")
        if not re.match(rf"^# {fid}\. .+", text):
            errors.append(f"{fid}: el título debe ser '# {fid}. <Nombre>'")
        if not re.search(r"^> \*\*Estado:\*\*", text, re.M):
            errors.append(f"{fid}: falta cabecera de control")
        heads = [norm(h) for h in re.findall(r"^## (.+)$", text, re.M)]
        pos = -1
        for h in HEADINGS:
            try:
                i = heads.index(norm(h))
            except ValueError:
                errors.append(f"{fid}: falta '## {h}'")
                continue
            if i < pos:
                errors.append(f"{fid}: '## {h}' fuera de orden")
            pos = max(pos, i)
        acs = AC.findall(text)
        if len(acs) < 3:
            errors.append(f"{fid}: se requieren ≥ 3 criterios AC-{fid.replace('-', '')}-NN (hay {len(acs)})")
        for ac_id, num, body in acs:
            if f"F-{num}" != fid:
                errors.append(f"{fid}: {ac_id} no corresponde a la feature")
            b = norm(body)
            if not (b.startswith("dado") and "cuando" in b and "entonces" in b):
                errors.append(f"{fid}: {ac_id} no sigue Dado/Cuando/Entonces")
        if not re.search(r"HU-[A-Z][A-Z0-9]{1,9}-\d{2}", text):
            errors.append(f"{fid}: sin trazabilidad a HU-<ACR>-NN")
        ph = set(PH.findall(re.sub(r"```.*?```", "", text, flags=re.S)))
        if ph:
            errors.append(f"{fid}: restos de plantilla {sorted(ph)[:5]}")
    if errors:
        print("KO specs")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"OK specs: {len(dirs)} features")
    return 0


if __name__ == "__main__":
    sys.exit(main())

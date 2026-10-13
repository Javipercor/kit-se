#!/usr/bin/env python3
"""Valida un artefacto Markdown contra un spec JSON de skill.

Uso: uv run --group se validate_doc.py <documento.md> <spec.json> [--section N]

--section N valida solo la sección `## N.` del documento (hasta la siguiente `## `); si su
primer párrafo empieza por `No aplica`, basta con eso. Con --section no se comprueban título
ni cabecera de control.

spec.json admite:
  title_regex            regex del H1
  headings               headings obligatorios, en orden (comparación sin tildes ni mayúsculas)
  require_control_block  exige la cabecera "> **Estado:** ..."
  patterns               [{regex, min, message}] patrones que deben aparecer al menos `min` veces
  forbidden              [{regex, message}] patrones prohibidos (fuera de bloques de código)
  min_mermaid            nº mínimo de bloques ```mermaid
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

PLACEHOLDER = re.compile(r"<(?!br\s*/?>|/?(?:sub|sup|b|i|em|strong)>)[^<>\n]{2,80}>|AAAA-MM-DD|\bTODO\b|\bXXX\b|\bTBD\b")


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s).strip().lower()


def strip_code(text: str) -> str:
    return re.sub(r"```.*?```", "", text, flags=re.S)


def main() -> int:
    args = sys.argv[1:]
    section = None
    if "--section" in args:
        i = args.index("--section")
        section = args[i + 1] if i + 1 < len(args) else None
        args = args[:i] + args[i + 2:]
    if len(args) != 2 or ("--section" in sys.argv and not section):
        print(__doc__)
        return 2
    doc, spec_path = Path(args[0]), Path(args[1])
    text = doc.read_text(encoding="utf-8")
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    if section:
        m = re.search(rf"^## {re.escape(section)}\. .*?(?=^## |\Z)", text, re.M | re.S)
        if not m:
            print(f"KO {doc}\n  - Sección '## {section}.' ausente")
            return 1
        text = m[0]
        body = "\n".join(text.splitlines()[1:]).strip()
        if re.match(r"^(\*\*)?No aplica", body):
            print(f"OK {doc} §{section} (No aplica)")
            return 0
        spec = {k: v for k, v in spec.items() if k not in ("title_regex", "require_control_block")}
    errors: list[str] = []
    lines = text.splitlines()
    prose = strip_code(text)

    h1 = next((l for l in lines if l.startswith("# ")), "")
    first = next((l for l in lines if l.strip()), "")
    if spec.get("title_regex") and not (re.match(spec["title_regex"], h1) or re.match(spec["title_regex"], first)):
        errors.append(f"Título no cumple `{spec['title_regex']}`: '{h1 or first}'")

    if spec.get("require_control_block") and not re.search(r"^> \*\*Estado:\*\*", text, re.M):
        errors.append("Falta la cabecera de control '> **Estado:** ...'")

    heads = [(i, norm(l)) for i, l in enumerate(lines) if re.match(r"^#{2,4} ", l)]
    pos = -1
    for h in spec.get("headings", []):
        target = norm(h)
        found = next((i for i, l in heads if l == target and i > pos), None)
        if found is None:
            exists = any(l == target for _, l in heads)
            errors.append(f"Heading {'fuera de orden' if exists else 'ausente'}: '{h}'")
        else:
            pos = found

    for p in spec.get("patterns", []):
        n = len(re.findall(p["regex"], text, re.M | re.I))
        if n < p.get("min", 1):
            errors.append(f"{p['message']} (encontrados {n}, mínimo {p.get('min', 1)})")

    for p in spec.get("forbidden", []):
        if re.search(p["regex"], prose, re.M | re.I):
            errors.append(p["message"])

    if text.count("```mermaid") < spec.get("min_mermaid", 0):
        errors.append(f"Se requieren al menos {spec['min_mermaid']} diagramas mermaid")

    ph = sorted(set(PLACEHOLDER.findall(prose)))
    if ph:
        errors.append("Restos de plantilla: " + ", ".join(ph[:10]))
    if len(re.findall(r"^\s*```", text, re.M)) % 2:
        errors.append("Bloques de código o Mermaid sin cerrar (número impar de ```)")

    if errors:
        print(f"KO {doc}")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"OK {doc}" + (f" §{section}" if section else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())

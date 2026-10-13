#!/usr/bin/env python3
"""Prepara el workspace del kit SE en la raíz del repositorio sin sobrescribir nada.

Uso: uv run init_workspace.py [raíz] [--no-deps] [--embeddings] [--no-uv]

1. Carpetas: RFP/, data-samples/, templates/, proposal/ (+ _meta, checklists, specs) y
   proposal/_meta/se-pipeline-state.md. Si el kit está instalado de forma global y el
   repositorio no tiene se.config.json ni se.preferencias.json, copia los del kit.
2. Entorno Python con uv (salvo --no-uv):
   - sin pyproject.toml → `uv init --bare --no-workspace` (solo crea pyproject.toml)
   - sin .venv → `uv venv` (`uv run` usa siempre el entorno del proyecto, aunque haya otro activado)
   - dependencias del kit en el grupo `se` de pyproject.toml (`uv add --group se …`), para no
     mezclarlas con las del proyecto ni con las de otros kits; --embeddings añade además el
     SDK de Azure OpenAI. --no-deps omite este paso.
Los scripts del kit se ejecutan después con `uv run --group se <script>`.
Exit 3 si uv no está instalado (el layout se crea igualmente).
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from datetime import date
from pathlib import Path

DIRS = [
    "RFP", "data-samples", "templates",
    "proposal", "proposal/_meta", "proposal/_meta/corpus", "proposal/_meta/data-profiles",
    "proposal/_meta/cambios", "proposal/checklists", "proposal/specs",
]
PHASES = [
    ("0 Corpus", "0..3-*.md"),
    ("1 Funcional", "HU-Enfoque-Funcional-*.md"),
    ("2 Fuentes de datos", "DATA-Analisis-Fuentes-*.md"),
    ("3 IA / DS", "HU-Enfoque-Tecnico-&-Arquitectura-*.md §29"),
    ("4 Técnico", "HU-Enfoque-Tecnico-&-Arquitectura-*.md"),
    ("5 Aplicación", "APP-Diseno-*.md"),
    ("6 Specs", "specs/F-*/spec.md"),
    ("7 Backlog", "6.0-backlog.md"),
]
DEFAULT_PY = {"group": "se", "deps": ["pandas", "pyarrow", "openpyxl", "pdfplumber", "pypdf", "python-docx", "python-pptx"],
              "embeddings_deps": ["openai", "azure-identity"]}


def resolve_root(arg: str) -> Path:
    p = Path(arg).resolve()
    if p.is_file():
        p = p.parent
    if p.name in {"RFP", "proposal", "templates", "data-samples"}:
        p = p.parent
    return p


def py_config(root: Path) -> dict:
    for d in [root, *root.parents]:
        f = d / "se.config.json"
        if f.is_file():
            return {**DEFAULT_PY, **json.loads(f.read_text(encoding="utf-8")).get("python", {})}
    return DEFAULT_PY


def layout(root: Path) -> list[str]:
    created = []
    for d in DIRS:
        if not (root / d).exists():
            (root / d).mkdir(parents=True)
            created.append(d)
    state = root / "proposal/_meta/se-pipeline-state.md"
    if not state.exists():
        rows = "\n".join(f"| {f} | A confirmar | pendiente | `{a}` | - | |" for f, a in PHASES)
        state.write_text(
            "# Estado del pipeline (kit SE)\n\n"
            f"> **Creado:** {date.today().isoformat()}\n\n"
            "## Perfil del proyecto\n\n"
            "- Componente analítico / IA: A confirmar\n"
            "- Desarrollo de aplicación: A confirmar\n"
            "- Stack: A confirmar\n\n"
            "## Fases\n\n"
            "| Fase | Aplica | Estado | Artefacto | Última actualización | Notas |\n"
            "| --- | --- | --- | --- | --- | --- |\n"
            f"{rows}\n",
            encoding="utf-8",
        )
        created.append("proposal/_meta/se-pipeline-state.md")
    return created


def group_deps(pyproject: Path, group: str) -> set[str]:
    """Nombres de paquetes ya declarados en [dependency-groups].<group>."""
    text = pyproject.read_text(encoding="utf-8")
    try:
        import tomllib
        data = tomllib.loads(text)
        items = data.get("dependency-groups", {}).get(group, [])
    except ModuleNotFoundError:  # Python 3.10: lectura aproximada
        m = re.search(rf"^\[dependency-groups\][\s\S]*?^{re.escape(group)}\s*=\s*\[([\s\S]*?)\]", text, re.M)
        items = re.findall(r'"([^"]+)"', m[1]) if m else []
    return {re.split(r"[<>=!~ \[;]", str(i), maxsplit=1)[0].lower() for i in items}


def uv(args: list[str], root: Path) -> bool:
    print("$ uv " + " ".join(args))
    r = subprocess.run(["uv", *args], cwd=root, capture_output=True, text=True)
    out = (r.stdout + r.stderr).strip()
    if out:
        print("  " + "\n  ".join(out.splitlines()[-6:]))
    return r.returncode == 0


def setup_uv(root: Path, cfg: dict, deps: bool, embeddings: bool) -> int:
    if not shutil.which("uv"):
        print("ERROR: uv no está instalado. Instálalo (https://docs.astral.sh/uv/getting-started/installation/) "
              "y vuelve a ejecutar la inicialización.")
        return 3
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        print("pyproject.toml: ya existe (no se modifica salvo el grupo de dependencias del kit)")
    elif not uv(["init", "--bare", "--no-workspace"], root):
        if not uv(["init", "--bare", "--no-workspace", "--name", "propuesta-se"], root):
            print("ERROR: no se pudo ejecutar uv init")
            return 1
    venv = root / ".venv"
    if venv.exists():
        print(".venv: ya existe")
    elif not uv(["venv"], root):
        print("ERROR: no se pudo ejecutar uv venv")
        return 1
    if deps:
        group = cfg["group"]
        wanted = list(cfg["deps"]) + (list(cfg["embeddings_deps"]) if embeddings else [])
        missing = [d for d in wanted if d.lower() not in group_deps(pyproject, group)]
        if missing:
            if not uv(["add", "--group", group, *missing], root):
                print(f"ERROR: no se pudieron añadir las dependencias al grupo '{group}'")
                return 1
        else:
            print(f"grupo '{group}': dependencias ya declaradas")
    print(f"Ejecuta los scripts del kit con: uv run --group {cfg['group']} <script>")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--no-deps", action="store_true", help="no añadir dependencias del kit")
    ap.add_argument("--embeddings", action="store_true", help="añadir también el SDK de Azure OpenAI")
    ap.add_argument("--no-uv", action="store_true", help="solo carpetas, sin pyproject ni entorno")
    a = ap.parse_args()
    root = resolve_root(a.root)
    root.mkdir(parents=True, exist_ok=True)
    created = layout(root)
    defaults = Path(__file__).resolve().parents[3] / "se" / "defaults"   # instalación global del kit
    for name in ("se.config.json", "se.preferencias.json"):
        if defaults.joinpath(name).exists() and not any((d / name).exists() for d in [root, *root.parents]):
            shutil.copy2(defaults / name, root / name)
            created.append(name)
    print(f"workspace: {root}")
    print("carpetas creadas: " + (", ".join(created) if created else "ninguna (ya existían)"))
    return 0 if a.no_uv else setup_uv(root, py_config(root), not a.no_deps, a.embeddings)


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Instala o desinstala el kit SE en un repositorio que puede tener otros kits.

Uso:
  uv run scripts/install.py --tool opencode|claude|codex|all [<destino>] [--force]
  uv run scripts/install.py --uninstall [<destino>]

Solo toca elementos con prefijo se-:
  opencode : .opencode/agents/se-*.md, .opencode/commands/se-*.md, .opencode/plugins/se-tools.js (herramientas),
             .agents/skills/se-*/, .agents/se/
  claude   : .claude/agents/se-*.md, .claude/commands/se-*.md, .claude/skills/se-*/, .claude/se/,
             .claude/se-lider-proyecto.md, servidor "se-tools" en .mcp.json (herramientas)
  codex    : .codex/agents/se-*.toml, .codex/se-lider-proyecto.md, .agents/skills/se-*/, .agents/se/,
             bloque [mcp_servers.se-tools] en .codex/config.toml
  todos    : se.config.json, se.preferencias.json (solo si no existe) y un bloque delimitado (<!-- se-kit:inicio --> … <!-- se-kit:fin -->)
             en AGENTS.md (OpenCode, Codex) y CLAUDE.md (Claude Code). El resto del fichero no se toca.

se.config.json existente: se conservan tus valores y solo se añaden claves nuevas
(--force lo reemplaza entero). Sin <destino> solo regenera las variantes en el kit.
--uninstall borra los elementos se-* y los bloques; conserva se.config.json, se.preferencias.json y el workspace
(RFP/, data-samples/, proposal/).
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent
TOOLS = {
    "opencode": {"items": [".opencode/agents/se-*.md", ".opencode/commands/se-*.md", ".opencode/plugins/se-*.js",
                           ".agents/skills/se-*", ".agents/se"],
                 "blocks": ["AGENTS.md"]},
    "claude": {"items": [".claude/agents/se-*.md", ".claude/commands/se-*.md", ".claude/skills/se-*", ".claude/se",
                         ".claude/se-lider-proyecto.md"],
               "blocks": ["CLAUDE.md"]},
    "codex": {"items": [".codex/agents/se-*.toml", ".codex/se-lider-proyecto.md", ".agents/skills/se-*", ".agents/se"],
              "blocks": ["AGENTS.md"]},
}
BLOCK = re.compile(r"\n*<!-- se-kit:inicio.*?<!-- se-kit:fin -->\n?", re.S)
TOML_BLOCK = re.compile(r"\n*# se-kit:inicio.*?# se-kit:fin\n?", re.S)
MCP_NAME = "se-tools"
MCP_CLAUDE = {"command": "uv", "args": ["run", "--group", "se", ".claude/se/tools/se_mcp.py"]}
CODEX_TOML = ('# se-kit:inicio · servidor MCP del kit SE (gestionado por scripts/install.py)\n'
              '[mcp_servers.se-tools]\ncommand = "uv"\nargs = ["run", "--group", "se", ".agents/se/tools/se_mcp.py"]\n'
              '# se-kit:fin\n')


def put_mcp_json(dst: Path) -> str:
    f = dst / ".mcp.json"
    data = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    data.setdefault("mcpServers", {})[MCP_NAME] = MCP_CLAUDE
    f.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return "servidor se-tools registrado"


def drop_mcp_json(dst: Path) -> None:
    f = dst / ".mcp.json"
    if f.exists():
        data = json.loads(f.read_text(encoding="utf-8"))
        data.get("mcpServers", {}).pop(MCP_NAME, None)
        if not data.get("mcpServers"):
            data.pop("mcpServers", None)
        f.unlink() if not data else f.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def put_codex_toml(dst: Path) -> str:
    f = dst / ".codex/config.toml"
    f.parent.mkdir(parents=True, exist_ok=True)
    text = f.read_text(encoding="utf-8") if f.exists() else ""
    text = TOML_BLOCK.sub("\n", text).strip("\n")
    f.write_text((text + "\n\n" if text else "") + CODEX_TOML, encoding="utf-8")
    return "bloque MCP se-tools escrito"


def drop_codex_toml(dst: Path) -> None:
    f = dst / ".codex/config.toml"
    if f.exists():
        text = TOML_BLOCK.sub("\n", f.read_text(encoding="utf-8")).strip("\n")
        f.unlink() if not text.strip() else f.write_text(text + "\n", encoding="utf-8")
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc")


def remove(base: Path, pattern: str) -> int:
    n = 0
    for p in base.glob(pattern):
        shutil.rmtree(p) if p.is_dir() else p.unlink()
        n += 1
    return n


def copy(pattern: str, dst: Path) -> int:
    remove(dst, pattern)
    n = 0
    for p in SRC.glob(pattern):
        target = dst / p.relative_to(SRC)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(p, target, ignore=IGNORE) if p.is_dir() else shutil.copy2(p, target)
        n += 1
    return n


def put_block(path: Path, block: str) -> str:
    if not path.exists():
        path.write_text(block, encoding="utf-8")
        return "creado"
    text = path.read_text(encoding="utf-8")
    if BLOCK.search(text):
        path.write_text(BLOCK.sub("\n\n" + block, text, count=1).lstrip("\n"), encoding="utf-8")
        return "bloque actualizado"
    path.write_text(text.rstrip("\n") + "\n\n" + block, encoding="utf-8")
    return "bloque añadido"


def drop_block(path: Path) -> None:
    if path.exists():
        text = BLOCK.sub("\n", path.read_text(encoding="utf-8")).strip("\n")
        path.unlink() if not text.strip() else path.write_text(text + "\n", encoding="utf-8")


def merge(user: dict, kit: dict) -> dict:
    for k, v in kit.items():
        if k not in user:
            user[k] = v
        elif isinstance(v, dict) and isinstance(user[k], dict):
            merge(user[k], v)
    return user


def install(tools: list[str], dst: Path, force: bool) -> None:
    items = list(dict.fromkeys(i for t in tools for i in TOOLS[t]["items"]))
    blocks = list(dict.fromkeys(b for t in tools for b in TOOLS[t]["blocks"]))
    copied = sum(copy(i, dst) for i in items)
    for b in blocks:
        print(f"{b}: {put_block(dst / b, (SRC / 'scripts/blocks' / b).read_text(encoding='utf-8'))}")
    if "claude" in tools:
        print(f".mcp.json: {put_mcp_json(dst)}")
    if "codex" in tools:
        print(f".codex/config.toml: {put_codex_toml(dst)}")
    cfg, kit_cfg = dst / "se.config.json", json.loads((SRC / "se.config.json").read_text(encoding="utf-8"))
    if cfg.exists() and not force:
        merged = merge(json.loads(cfg.read_text(encoding="utf-8")), kit_cfg)
        cfg.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("se.config.json: conservados tus valores, añadidas claves nuevas")
    else:
        shutil.copy2(SRC / "se.config.json", cfg)
    prefs = dst / "se.preferencias.json"
    if not prefs.exists():  # catálogo base de la organización; nunca se sobrescribe
        shutil.copy2(SRC / "se.preferencias.json", prefs)
        print("se.preferencias.json: copiado el catálogo base del kit")
    else:
        print("se.preferencias.json: se conserva el existente")
    print(f"Kit SE instalado para {', '.join(tools)} en {dst} ({copied} elementos)")


def uninstall(dst: Path) -> None:
    pats = list(dict.fromkeys(i for t in TOOLS.values() for i in t["items"]))
    n = sum(remove(dst, p) for p in pats)
    for b in ("AGENTS.md", "CLAUDE.md"):
        drop_block(dst / b)
    drop_mcp_json(dst)
    drop_codex_toml(dst)
    print(f"Kit SE desinstalado de {dst}: {n} elementos y bloques de AGENTS.md/CLAUDE.md. "
          "Se conservan se.config.json, se.preferencias.json y el workspace.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tool", choices=[*TOOLS, "all"])
    ap.add_argument("--uninstall", action="store_true")
    ap.add_argument("dest", nargs="?", default=str(SRC))
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    dst = Path(a.dest).expanduser().resolve()
    if a.uninstall:
        if dst == SRC:
            print("No se desinstala de la propia carpeta del kit")
            return 1
        uninstall(dst)
        return 0
    if not a.tool:
        ap.error("indica --tool o --uninstall")
    tools = list(TOOLS) if a.tool == "all" else [a.tool]
    targets = [t for t in tools if t != "opencode"]
    if targets:
        subprocess.run([sys.executable, str(SRC / "scripts/sync_agents.py"), "--target",
                        "all" if len(targets) > 1 else targets[0]], check=True)
    if dst == SRC:
        print(f"Kit preparado para: {', '.join(tools)} (en {SRC})")
        return 0
    dst.mkdir(parents=True, exist_ok=True)
    install(tools, dst, a.force)
    return 0


if __name__ == "__main__":
    sys.exit(main())

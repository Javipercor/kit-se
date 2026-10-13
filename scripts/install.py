#!/usr/bin/env python3
"""Instala o desinstala el kit SE, en un repositorio o de forma global, sin tocar otros kits.

Uso:
  uv run scripts/install.py --tool opencode|claude|codex|all [<repositorio>] [--force] [--opencode-plugin]
  uv run scripts/install.py --tool opencode|claude|codex|all --global [--home DIR] [--opencode-plugin]
  uv run scripts/install.py --uninstall [<repositorio>]
  uv run scripts/install.py --uninstall --global [--home DIR]

En los tres harness el kit se instala igual: agentes, comandos y skills (que enseñan el
método y el uso de las herramientas), reglas en un bloque delimitado de AGENTS.md / CLAUDE.md
y el servidor MCP `se-tools` con las herramientas deterministas.

Por repositorio (solo elementos con prefijo se-; lo de otros kits no se toca):
  opencode : .opencode/agents/se-*.md, .opencode/commands/se-*.md, .agents/skills/se-*/, .agents/se/,
             MCP "se-tools" en .opencode/opencode.json, bloque en AGENTS.md
  claude   : .claude/agents/se-*.md, .claude/commands/se-*.md, .claude/skills/se-*/, .claude/se/,
             .claude/se-lider-proyecto.md, MCP "se-tools" en .mcp.json, bloque en CLAUDE.md
  codex    : .codex/agents/se-*.toml, .codex/se-lider-proyecto.md, .agents/skills/se-*/, .agents/se/,
             MCP en un bloque de .codex/config.toml, bloque en AGENTS.md
  todos    : se.config.json (fusiona claves nuevas) y se.preferencias.json (solo si no existe)

Global (--global; para todos tus repositorios, en tu carpeta personal):
  opencode : ~/.config/opencode/{agents,commands}/se-*, ~/.agents/skills/se-*/, ~/.agents/se/,
             MCP en ~/.config/opencode/opencode.json, bloque en ~/.config/opencode/AGENTS.md
  claude   : ~/.claude/{agents,commands,skills}/se-*, ~/.claude/se/, ~/.claude/se-lider-proyecto.md,
             MCP de ámbito usuario (claude mcp add-json --scope user, o ~/.claude.json), bloque en ~/.claude/CLAUDE.md
  codex    : ~/.codex/agents/se-*.toml, ~/.codex/se-lider-proyecto.md, ~/.agents/skills/se-*/, ~/.agents/se/,
             MCP en ~/.codex/config.toml, bloque en ~/.codex/AGENTS.md
  Las rutas de las instrucciones se reescriben a rutas absolutas. La configuración por defecto
  (se.config.json, se.preferencias.json) queda en <...>/se/defaults/ y /se-init la copia a cada repositorio.

--opencode-plugin instala además el plugin .opencode/plugins/se-tools.js (alternativa nativa
de OpenCode 2 al MCP; normalmente no hace falta). --uninstall conserva configuración y workspace.
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
    "opencode": {"items": [".opencode/agents/se-*.md", ".opencode/commands/se-*.md", ".agents/skills/se-*", ".agents/se"],
                 "blocks": ["AGENTS.md"]},
    "claude": {"items": [".claude/agents/se-*.md", ".claude/commands/se-*.md", ".claude/skills/se-*", ".claude/se",
                         ".claude/se-lider-proyecto.md"],
               "blocks": ["CLAUDE.md"]},
    "codex": {"items": [".codex/agents/se-*.toml", ".codex/se-lider-proyecto.md", ".agents/skills/se-*", ".agents/se"],
              "blocks": ["AGENTS.md"]},
}
PLUGIN = ".opencode/plugins/se-*.js"
BLOCK = re.compile(r"\n*<!-- se-kit:inicio.*?<!-- se-kit:fin -->\n?", re.S)
TOML_BLOCK = re.compile(r"\n*# se-kit:inicio.*?# se-kit:fin\n?", re.S)
MCP_NAME = "se-tools"
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc")
TEXT_SUFFIXES = {".md", ".toml", ".json", ".js"}


class Layout:
    """Dónde va cada cosa: en un repositorio (rutas relativas) o global (carpeta personal)."""

    def __init__(self, dst: Path, is_global: bool):
        self.dst, self.is_global = dst, is_global
        h = dst
        self.map = ({".opencode/agents": h / ".config/opencode/agents", ".opencode/commands": h / ".config/opencode/commands",
                     ".opencode/plugins": h / ".config/opencode/plugins", ".agents": h / ".agents",
                     ".claude": h / ".claude", ".codex": h / ".codex"} if is_global else {})
        self.blocks = ({"opencode": h / ".config/opencode/AGENTS.md", "claude": h / ".claude/CLAUDE.md",
                        "codex": h / ".codex/AGENTS.md"} if is_global else
                       {"opencode": dst / "AGENTS.md", "claude": dst / "CLAUDE.md", "codex": dst / "AGENTS.md"})

    def target(self, rel: str) -> Path:
        for prefix, base in sorted(self.map.items(), key=lambda kv: -len(kv[0])):
            if rel == prefix or rel.startswith(prefix + "/"):
                return base / rel[len(prefix):].lstrip("/")
        return self.dst / rel

    def server(self, tool: str) -> Path:
        base = ".claude/se/tools/se_mcp.py" if tool == "claude" else ".agents/se/tools/se_mcp.py"
        return self.target(base)

    def server_arg(self, tool: str) -> str:
        p = self.server(tool)
        return str(p) if self.is_global else str(p.relative_to(self.dst))

    def rewrite(self, text: str) -> str:
        """En global, las rutas relativas de las instrucciones pasan a absolutas."""
        if not self.is_global:
            return text
        for rel in (".agents/skills/", ".agents/se/", ".claude/skills/", ".claude/se/", ".claude/se-lider-proyecto.md",
                    ".codex/se-lider-proyecto.md"):
            abs_path = str(self.target(rel.rstrip("/"))) + ("/" if rel.endswith("/") else "")
            text = re.sub(r"(?<![\w./~-])" + re.escape(rel), abs_path.replace("\\", "/"), text)
        return text


# ------------------------------------------------------------------ ficheros

def remove(layout: Layout, pattern: str) -> int:
    t = layout.target(pattern)
    n = 0
    for p in t.parent.glob(t.name) if t.parent.exists() else []:
        shutil.rmtree(p) if p.is_dir() else p.unlink()
        n += 1
    return n


def copy(layout: Layout, pattern: str) -> int:
    remove(layout, pattern)
    n = 0
    for p in SRC.glob(pattern):
        target = layout.target(str(p.relative_to(SRC)))
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(p, target, ignore=IGNORE) if p.is_dir() else shutil.copy2(p, target)
        files = [target] if target.is_file() else [f for f in target.rglob("*") if f.is_file()]
        for f in files:
            if layout.is_global and f.suffix in TEXT_SUFFIXES:
                f.write_text(layout.rewrite(f.read_text(encoding="utf-8")), encoding="utf-8")
        n += 1
    return n


def put_block(path: Path, block: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
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


# ------------------------------------------------------------------ registro del MCP

def json_entry(path: Path, keys: tuple[str, ...], value: dict | None) -> str:
    """Pone (o quita, con value=None) data[k1][k2]… en un JSON, sin tocar el resto."""
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return f"no se pudo leer {path} (¿JSON con comentarios?): registra el MCP a mano (ver README)"
    elif value is None:
        return "nada que quitar"
    else:
        data = {}
    container, name = keys[0], keys[1]  # siempre dos niveles: {"mcp"|"mcpServers": {nombre: …}}
    if value is None:
        data.get(container, {}).pop(name, None)
        if container in data and not data[container]:
            data.pop(container)
        if path.name != ".claude.json" and (not data or data == {"$schema": "https://opencode.ai/config.json"}):
            path.unlink()
            return "eliminado"
    else:
        data.setdefault(container, {})[name] = value
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return "actualizado"


def codex_block(path: Path, server: str | None) -> str:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    text = TOML_BLOCK.sub("\n", text).strip("\n")
    if server is not None:
        block = ("# se-kit:inicio · servidor MCP del kit SE (gestionado por scripts/install.py)\n"
                 f'[mcp_servers.{MCP_NAME}]\ncommand = "uv"\nargs = ["run", "--no-project", {json.dumps(server)}]\n'
                 "# se-kit:fin\n")
        text = (text + "\n\n" if text else "") + block
    if not text.strip():
        path.unlink(missing_ok=True)
        return "eliminado"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")
    return "actualizado"


def register_mcp(layout: Layout, tool: str, add: bool) -> str:
    server = layout.server_arg(tool)
    cmd = ["uv", "run", "--no-project", server]
    if tool == "opencode":
        cfg = layout.dst / ".config/opencode/opencode.json" if layout.is_global else layout.dst / ".opencode/opencode.json"
        entry = {"type": "local", "command": cmd, "enabled": True}
        if add and not cfg.exists():
            cfg.parent.mkdir(parents=True, exist_ok=True)
            cfg.write_text(json.dumps({"$schema": "https://opencode.ai/config.json"}) + "\n", encoding="utf-8")
        return f"{cfg}: " + json_entry(cfg, ("mcp", MCP_NAME), entry if add else None)
    if tool == "codex":
        cfg = layout.target(".codex/config.toml")
        return f"{cfg}: " + codex_block(cfg, server if add else None)
    entry = {"type": "stdio", "command": "uv", "args": cmd[1:]}
    if not layout.is_global:
        return f"{layout.dst / '.mcp.json'}: " + json_entry(layout.dst / ".mcp.json", ("mcpServers", MCP_NAME),
                                                          entry if add else None)
    if shutil.which("claude"):
        args = (["claude", "mcp", "add-json", "--scope", "user", MCP_NAME, json.dumps(entry)] if add
                else ["claude", "mcp", "remove", "--scope", "user", MCP_NAME])
        r = subprocess.run(args, capture_output=True, text=True)
        if r.returncode == 0:
            return f"claude mcp ({'add-json' if add else 'remove'} --scope user): ok"
    return f"{layout.dst / '.claude.json'}: " + json_entry(layout.dst / ".claude.json", ("mcpServers", MCP_NAME),
                                                           entry if add else None)


# ------------------------------------------------------------------ instalar / desinstalar

def install(tools: list[str], layout: Layout, force: bool, plugin: bool) -> None:
    items = list(dict.fromkeys(i for t in tools for i in TOOLS[t]["items"]))
    if plugin and "opencode" in tools:
        items.append(PLUGIN)
    copied = sum(copy(layout, i) for i in items)
    for t in tools:
        block = (SRC / "scripts/blocks" / ("CLAUDE.md" if t == "claude" else "AGENTS.md")).read_text(encoding="utf-8")
        print(f"{layout.blocks[t]}: {put_block(layout.blocks[t], layout.rewrite(block))}")
        print(f"MCP ({t}) → {register_mcp(layout, t, add=True)}")
    if layout.is_global:
        dirs = ([layout.target(".claude/se/defaults")] if "claude" in tools else []) + \
               ([layout.target(".agents/se/defaults")] if set(tools) & {"opencode", "codex"} else [])
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
            shutil.copy2(SRC / "se.config.json", d / "se.config.json")
            if not (d / "se.preferencias.json").exists():
                shutil.copy2(SRC / "se.preferencias.json", d / "se.preferencias.json")
        print("configuración por defecto en se/defaults/ (la copia /se-init a cada repositorio)")
    else:
        cfg, kit_cfg = layout.dst / "se.config.json", json.loads((SRC / "se.config.json").read_text(encoding="utf-8"))
        if cfg.exists() and not force:
            merged = merge(json.loads(cfg.read_text(encoding="utf-8")), kit_cfg)
            cfg.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print("se.config.json: conservados tus valores, añadidas claves nuevas")
        else:
            shutil.copy2(SRC / "se.config.json", cfg)
        prefs = layout.dst / "se.preferencias.json"
        if not prefs.exists():
            shutil.copy2(SRC / "se.preferencias.json", prefs)
            print("se.preferencias.json: copiado el catálogo base del kit")
    print(f"Kit SE instalado ({'global' if layout.is_global else 'repositorio'}) para {', '.join(tools)} "
          f"en {layout.dst} ({copied} elementos)")


def uninstall(layout: Layout, tools: list[str]) -> None:
    pats = list(dict.fromkeys(i for t in tools for i in TOOLS[t]["items"])) + [PLUGIN]
    n = sum(remove(layout, p) for p in pats)
    for t in tools:
        drop_block(layout.blocks[t])
        print(f"MCP ({t}) → {register_mcp(layout, t, add=False)}")
    for rel in (".agents/skills", ".agents", ".opencode/agents", ".opencode/commands", ".opencode/plugins",
                ".claude/agents", ".claude/commands", ".claude/skills", ".codex/agents"):
        d = layout.target(rel)
        if d.is_dir() and not any(d.iterdir()):  # solo carpetas que hayan quedado vacías
            d.rmdir()
    print(f"Kit SE desinstalado de {layout.dst}: {n} elementos. Se conservan la configuración y el workspace.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tool", choices=[*TOOLS, "all"])
    ap.add_argument("--uninstall", action="store_true")
    ap.add_argument("--global", dest="is_global", action="store_true", help="instalar en la carpeta personal")
    ap.add_argument("--home", default=str(Path.home()), help="carpeta personal para --global (pruebas)")
    ap.add_argument("--opencode-plugin", action="store_true", help="instalar también el plugin nativo de OpenCode 2")
    ap.add_argument("dest", nargs="?")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    tools = list(TOOLS) if a.tool in (None, "all") else [a.tool]
    if a.is_global:
        layout = Layout(Path(a.home).expanduser().resolve(), True)
    else:
        dst = Path(a.dest or SRC).expanduser().resolve()
        layout = Layout(dst, False)
    if a.uninstall:
        if not a.is_global and layout.dst == SRC:
            print("No se desinstala de la propia carpeta del kit")
            return 1
        uninstall(layout, tools)
        return 0
    if not a.tool:
        ap.error("indica --tool o --uninstall")
    targets = [t for t in tools if t != "opencode"]
    if targets:
        subprocess.run([sys.executable, str(SRC / "scripts/sync_agents.py"), "--target",
                        "all" if len(targets) > 1 else targets[0]], check=True)
    if not a.is_global and layout.dst == SRC:
        print(f"Kit preparado para: {', '.join(tools)} (en {SRC})")
        return 0
    layout.dst.mkdir(parents=True, exist_ok=True)
    install(tools, layout, a.force, a.opencode_plugin)
    return 0


if __name__ == "__main__":
    sys.exit(main())

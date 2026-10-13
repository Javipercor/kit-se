#!/usr/bin/env python3
"""Genera las variantes de Claude Code y Codex a partir de la fuente OpenCode.

Fuente de verdad:
  .opencode/agents/*.md     agentes (frontmatter OpenCode + cuerpo)
  .opencode/commands/*.md   comandos
  .agents/skills/se-*/      skills (OpenCode y Codex las leen aquí)
  .agents/se/REGLAS.md      reglas comunes del kit
  se.config.json           herramientas Claude y sandbox Codex por agente

Genera:
  .claude/agents/se-*.md, .claude/commands/se-*.md, .claude/skills/se-*/, .claude/se/REGLAS.md,
  .claude/se-lider-proyecto.md
  .codex/agents/*.toml, .codex/se-lider-proyecto.md

Uso: uv run scripts/sync_agents.py [--target claude|codex|all] [--check]
"""
from __future__ import annotations

import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEAD = "se-lider-proyecto"


def split_fm(text: str) -> tuple[str, str]:
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    return (m[1], m[2].lstrip("\n")) if m else ("", text)


def fm_value(fm: str, key: str) -> str | None:
    m = re.search(rf"^{key}:\s*(.+)$", fm, re.M)
    if not m:
        return None
    v = m[1].strip()
    return json.loads(v) if v.startswith('"') else v


def to_claude(text: str) -> str:
    return text.replace(".agents/skills/", ".claude/skills/").replace(".agents/se/", ".claude/se/")


def toml_str(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)


def build(out: Path) -> None:
    cfg = json.loads((ROOT / "se.config.json").read_text(encoding="utf-8"))["agents"]
    (out / ".claude/agents").mkdir(parents=True)
    (out / ".claude/commands").mkdir(parents=True)
    (out / ".codex/agents").mkdir(parents=True)

    for f in sorted((ROOT / ".opencode/agents").glob("*.md")):
        name = f.stem
        fm, body = split_fm(f.read_text(encoding="utf-8"))
        desc = fm_value(fm, "description") or name
        meta = cfg.get(name, {})
        if name == LEAD:
            # En Claude Code y Codex la sesión principal actúa como líder (los subagentes no anidan).
            (out / ".claude/se-lider-proyecto.md").write_text(to_claude(body), encoding="utf-8")
            (out / ".codex/se-lider-proyecto.md").write_text(body, encoding="utf-8")
            continue
        tools = meta.get("claude_tools", "Read, Grep, Glob, Write, Edit, Bash")
        (out / f".claude/agents/{name}.md").write_text(
            f"---\nname: {name}\ndescription: {toml_str(desc)}\ntools: {tools}\n---\n\n{to_claude(body)}", encoding="utf-8")
        if "'''" in body:
            raise SystemExit(f"{f}: el cuerpo no puede contener ''' (TOML)")
        (out / f".codex/agents/{name}.toml").write_text(
            f"name = {toml_str(name)}\n"
            f"description = {toml_str(desc)}\n"
            f"sandbox_mode = {toml_str(meta.get('codex_sandbox', 'workspace-write'))}\n"
            f"developer_instructions = '''\n{body.rstrip()}\n'''\n", encoding="utf-8")

    for f in sorted((ROOT / ".opencode/commands").glob("*.md")):
        fm, body = split_fm(f.read_text(encoding="utf-8"))
        desc = fm_value(fm, "description") or f.stem
        agent = fm_value(fm, "agent")
        if agent and agent != LEAD:
            body = f"Delega en el subagente `{agent}`:\n\n{body}"
        else:
            body = f"Lee `.claude/se/REGLAS.md` y `.claude/se-lider-proyecto.md` y actúa como `{LEAD}`:\n\n{body}"
        (out / f".claude/commands/{f.name}").write_text(
            f"---\ndescription: {toml_str(desc)}\nargument-hint: [instrucciones]\n---\n\n{to_claude(body)}", encoding="utf-8")

    for sk in sorted((ROOT / ".agents/skills").glob("se-*")):
        shutil.copytree(sk, out / ".claude/skills" / sk.name, ignore=shutil.ignore_patterns("__pycache__"))
    (out / ".claude/se").mkdir(parents=True)
    (out / ".claude/se/REGLAS.md").write_text(to_claude((ROOT / ".agents/se/REGLAS.md").read_text(encoding="utf-8")),
                                              encoding="utf-8")
    shutil.copytree(ROOT / ".agents/se/tools", out / ".claude/se/tools", ignore=shutil.ignore_patterns("__pycache__"))
    for md in (out / ".claude/skills").rglob("*.md"):
        md.write_text(to_claude(md.read_text(encoding="utf-8")), encoding="utf-8")


def remove(base: Path, pattern: str) -> None:
    for p in base.glob(pattern):
        shutil.rmtree(p) if p.is_dir() else p.unlink()


def snapshot(base: Path) -> dict[str, bytes]:
    files = {}
    for sub in (".claude", ".codex"):
        d = base / sub
        if d.exists():
            for p in d.rglob("*"):
                if p.is_file() and "__pycache__" not in p.parts and any(x.startswith("se") for x in p.relative_to(d).parts):
                    files[p.relative_to(base).as_posix()] = p.read_bytes()
    return files


def target_arg() -> str:
    if "--target" in sys.argv:
        i = sys.argv.index("--target")
        t = sys.argv[i + 1] if i + 1 < len(sys.argv) else ""
        if t not in {"claude", "codex", "all"}:
            raise SystemExit("--target debe ser claude, codex o all")
        return t
    return "all"


def main() -> int:
    target = target_arg()
    subs = {"claude": (".claude",), "codex": (".codex",), "all": (".claude", ".codex")}[target]
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        build(tmpdir)
        if "--check" in sys.argv:
            new = {k: v for k, v in snapshot(tmpdir).items() if k.startswith(subs)}
            old = {k: v for k, v in snapshot(ROOT).items() if k.startswith(subs)}
            if new != old:
                diff = sorted(set(new) ^ set(old) | {k for k in new.keys() & old.keys() if new[k] != old[k]})
                print("DESACTUALIZADO: " + ", ".join(diff[:20]))
                return 1
            print("OK: variantes al día")
            return 0
        # Solo se borran elementos del kit (prefijo se-); lo de otros kits no se toca.
        if ".claude" in subs:
            for pat in (".claude/agents/se-*", ".claude/commands/se-*", ".claude/skills/se-*", ".claude/se",
                        ".claude/se-lider-proyecto.md"):
                remove(ROOT, pat)
        if ".codex" in subs:
            for pat in (".codex/agents/se-*", ".codex/se-lider-proyecto.md"):
                remove(ROOT, pat)
        for sub in subs:
            shutil.copytree(tmpdir / sub, ROOT / sub, dirs_exist_ok=True)
    print(f"Generado ({target}): " + ", ".join(subs))
    return 0


if __name__ == "__main__":
    sys.exit(main())

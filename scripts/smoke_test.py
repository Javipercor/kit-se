#!/usr/bin/env python3
"""Prueba rápida del kit: instala en un directorio temporal y ejecuta los scripts principales.

Uso: uv run scripts/smoke_test.py
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent
BACKLOG = """# Backlog técnico-funcional

## Catálogo preliminar de épicas y HUs

### EPIC 1 - Arquitectura

#### HU 1.1 - Arquitectura validada

Como Responsable de negocio, quiero una arquitectura validada, para asegurar la viabilidad.

* **Fase única - Implementación del caso de uso**

### EPIC 2 - DevOps

#### HU 2.1 - Despliegue operativo

Como Responsable de negocio, quiero la solución desplegada, para usarla con garantías.

* **Fase única - Implementación del caso de uso**

### EPIC 3 - Documentacion y Entregables

#### HU 3.1 - No aplica

No aplica en esta prueba.

## Backlog detallado

### EPIC 1 - Arquitectura

#### HU 1.1 - Arquitectura validada

Como Responsable de negocio, quiero una arquitectura validada, para asegurar la viabilidad.

* **Fase única - Implementación del caso de uso**

##### Criterios de aceptación

* Criterio uno.
* Criterio dos.
* Criterio tres.

##### Tareas

* **Architect**
  * Diseñar arquitectura objetivo **8h, N2**

### EPIC 2 - DevOps

#### HU 2.1 - Despliegue operativo

Como Responsable de negocio, quiero la solución desplegada, para usarla con garantías.

* **Fase única - Implementación del caso de uso**

##### Criterios de aceptación

* Criterio uno.
* Criterio dos.
* Criterio tres.

##### Tareas

* **DevOps**
  * Pipeline CI/CD **6h, N2**

### EPIC 3 - Documentacion y Entregables

#### HU 3.1 - No aplica

No aplica en esta prueba.
"""


CWD: list[Path] = []
FOREIGN = {"AGENTS.md": "# Otro kit\n\nRegla X del otro kit.\n", "CLAUDE.md": "@otro-kit.md\n",
           ".opencode/agents/otro-agente.md": "---\ndescription: otro\n---\nOtro.\n",
           ".opencode/commands/pipeline.md": "---\ndescription: pipeline de otro kit\n---\nOtro.\n",
           ".agents/skills/otra-skill/SKILL.md": "---\nname: otra-skill\n---\n",
           ".claude/agents/otro.md": "otro\n", ".codex/agents/otro.toml": "name = \"otro\"\n"}


def run(*cmd: str, ok: bool = True) -> None:
    r = subprocess.run([sys.executable, *cmd], capture_output=True, text=True, cwd=CWD[0] if CWD else None)
    status = "OK " if (r.returncode == 0) == ok else "KO "
    print(f"{status} {' '.join(Path(c).name if '/' in c else c for c in cmd)}")
    if status.startswith("KO"):
        print(r.stdout, r.stderr)
        raise SystemExit(1)


def check_coexistence(ws: Path, installed: bool) -> None:
    for rel, content in FOREIGN.items():
        text = (ws / rel).read_text(encoding="utf-8")
        assert content.strip() in text, f"se alteró {rel} del otro kit"
    for b in ("AGENTS.md", "CLAUDE.md"):
        n = (ws / b).read_text(encoding="utf-8").count("se-kit:inicio")
        assert n == (1 if installed else 0), f"{b}: {n} bloques SE"
    SE = [".opencode/agents/se-lider-proyecto.md", ".opencode/commands/se-pipeline.md", ".agents/skills/se-core/SKILL.md",
          ".agents/se/REGLAS.md", ".claude/agents/se-analista-corpus.md", ".claude/se/REGLAS.md",
          ".codex/agents/se-analista-corpus.toml", ".codex/se-lider-proyecto.md"]
    for rel in SE:
        assert (ws / rel).exists() == installed, f"{rel}: {'falta' if installed else 'sobra'}"


def tools_check(ws: Path) -> None:
    """Registro de herramientas, servidor MCP (JSON-RPC por stdio), exportación y diagramas."""
    reg = str(ws / ".agents/se/tools/se_tools.py")
    out = subprocess.run([sys.executable, reg, "list"], capture_output=True, text=True, cwd=ws)
    names = {t["name"] for t in json.loads(out.stdout)}
    assert {"se_barrido_requisitos", "se_exportar_backlog", "se_diagrama_azure"} <= names
    assert not any("aprobar" in n or "aceptar" in n or "fijar" in n for n in names), "acción humana expuesta"
    r = subprocess.run([sys.executable, reg, "call", "se_validar_backlog", '{"resumen": true}'], capture_output=True, text=True, cwd=ws)
    assert json.loads(r.stdout)["ok"], r.stdout
    r = subprocess.run([sys.executable, reg, "call", "se_barrido_requisitos", '{"accion": "borrar"}'], capture_output=True, text=True, cwd=ws)
    assert not json.loads(r.stdout)["ok"]
    msgs = [{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18", "capabilities": {},
             "clientInfo": {"name": "smoke", "version": "1"}}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "se_trazabilidad", "arguments": {}}}]
    r = subprocess.run([sys.executable, str(ws / ".agents/se/tools/se_mcp.py")], input="\n".join(json.dumps(m) for m in msgs) + "\n",
                       capture_output=True, text=True, cwd=ws, timeout=300)
    replies = {m["id"]: m for m in map(json.loads, r.stdout.splitlines())}
    assert replies[1]["result"]["serverInfo"]["name"] == "se-tools"
    assert len(replies[2]["result"]["tools"]) == len(names)
    assert "content" in replies[3]["result"]
    print(f"OK  herramientas del kit: {len(names)} (registro, MCP por stdio)")
    try:
        import openpyxl  # noqa: F401
        r = subprocess.run([sys.executable, reg, "call", "se_exportar_backlog", '{"formato": "todos"}'], capture_output=True, text=True, cwd=ws)
        assert json.loads(r.stdout)["ok"], r.stdout
        assert (ws / "proposal/exports/backlog-ado-import.csv").exists() and (ws / "proposal/exports/backlog-horas.xlsx").exists()
        print("OK  exportación a Azure DevOps (CSV) y Excel de horas")
    except ImportError:
        print("-- openpyxl no disponible: se omite la exportación a Excel")
    try:
        import drawpyo  # noqa: F401
        spec = ws / ".agents/skills/se-diagrama-azure/assets/ejemplo.json"
        r = subprocess.run([sys.executable, reg, "call", "se_diagrama_azure", json.dumps({"especificacion": str(spec)})],
                           capture_output=True, text=True, cwd=ws)
        assert json.loads(r.stdout)["ok"], r.stdout
        print("OK  diagrama draw.io de arquitectura Azure")
    except ImportError:
        print("-- drawpyo no disponible: se omite el diagrama")


def global_flow() -> None:
    """Instalación global en una carpeta personal simulada, uso desde un repositorio y desinstalación."""
    with tempfile.TemporaryDirectory() as tmp:
        home, repo = Path(tmp) / "home", Path(tmp) / "repo"
        (home / ".config/opencode").mkdir(parents=True)
        (home / ".config/opencode/opencode.json").write_text('{"mcp": {"otro": {"type": "local", "command": ["x"]}}}')
        (home / ".claude.json").write_text('{"numStartups": 3, "mcpServers": {"otro": {"command": "x"}}}')
        run(str(SRC / "scripts/install.py"), "--tool", "all", "--global", "--home", str(home))
        for rel in (".config/opencode/agents/se-lider-proyecto.md", ".config/opencode/commands/se-pipeline.md",
                    ".agents/skills/se-herramientas/SKILL.md", ".agents/se/tools/se_mcp.py", ".agents/se/defaults/se.config.json",
                    ".claude/skills/se-core/SKILL.md", ".claude/se/tools/se_mcp.py", ".claude/agents/se-analista-corpus.md",
                    ".codex/agents/se-analista-corpus.toml", ".config/opencode/AGENTS.md", ".claude/CLAUDE.md", ".codex/AGENTS.md"):
            assert (home / rel).exists(), rel
        skill = (home / ".agents/skills/se-corpus-rfp/SKILL.md").read_text(encoding="utf-8")
        assert f"{home}/.agents/skills/se-corpus-rfp/scripts/req_scan.py" in skill, "rutas no reescritas"
        assert f"{home}/.agents/se/REGLAS.md" in (home / ".codex/AGENTS.md").read_text(encoding="utf-8")
        oc = json.loads((home / ".config/opencode/opencode.json").read_text(encoding="utf-8"))["mcp"]
        assert set(oc) == {"otro", "se-tools"} and oc["se-tools"]["command"][-1] == f"{home}/.agents/se/tools/se_mcp.py"
        cj = json.loads((home / ".claude.json").read_text(encoding="utf-8"))
        assert cj["numStartups"] == 3 and set(cj["mcpServers"]) == {"otro", "se-tools"}
        assert "[mcp_servers.se-tools]" in (home / ".codex/config.toml").read_text(encoding="utf-8")
        repo.mkdir()
        r = subprocess.run([sys.executable, str(home / ".agents/skills/se-core/scripts/init_workspace.py"), "--no-uv"],
                           cwd=repo, capture_output=True, text=True)
        assert r.returncode == 0 and (repo / "se.config.json").exists(), r.stdout + r.stderr
        msgs = [{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}},
                {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "se_trazabilidad", "arguments": {}}}]
        r = subprocess.run([sys.executable, str(home / ".claude/se/tools/se_mcp.py")], cwd=repo, capture_output=True, text=True,
                           input="\n".join(json.dumps(m) for m in msgs) + "\n", timeout=300)
        assert json.loads(r.stdout.splitlines()[1])["result"]["structuredContent"]["exit_code"] in (0, 1), r.stdout
        run(str(SRC / "scripts/install.py"), "--uninstall", "--global", "--home", str(home))
        assert not (home / ".agents/skills/se-core").exists() and not (home / ".claude/se").exists()
        assert json.loads((home / ".config/opencode/opencode.json").read_text(encoding="utf-8")) == {"mcp": {"otro": {"type": "local", "command": ["x"]}}}
        assert json.loads((home / ".claude.json").read_text(encoding="utf-8")) == {"numStartups": 3, "mcpServers": {"otro": {"command": "x"}}}
        assert not (home / ".codex/config.toml").exists() and not (home / ".claude/CLAUDE.md").exists()
    print("OK  instalación global (instalar, usar desde un repositorio, desinstalar)")


def uv_flow() -> None:
    """/se-init con uv: pyproject, .venv y ejecución con uv run (sin dependencias, para no requerir red)."""
    import shutil
    if not shutil.which("uv"):
        print("-- uv no instalado: se omite la prueba de uv")
        return
    with tempfile.TemporaryDirectory() as tmp:
        ws = Path(tmp) / "repo"
        ws.mkdir()
        init = str(SRC / ".agents/skills/se-core/scripts/init_workspace.py")
        for _ in range(2):  # idempotente
            r = subprocess.run(["uv", "run", init, "--no-deps"], cwd=ws, capture_output=True, text=True)
            assert r.returncode == 0, r.stdout + r.stderr
        assert (ws / "pyproject.toml").exists() and (ws / ".venv").exists(), "uv init / uv venv no se ejecutaron"
        r = subprocess.run(["uv", "run", str(SRC / ".agents/skills/se-core/scripts/check_traceability.py")],
                           cwd=ws, capture_output=True, text=True)
        assert r.returncode == 0, r.stdout + r.stderr
    print("OK  /se-init con uv (uv init, uv venv, uv run)")


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        ws = Path(tmp) / "ws"
        for rel, content in FOREIGN.items():  # otro kit ya instalado en el repositorio
            (ws / rel).parent.mkdir(parents=True, exist_ok=True)
            (ws / rel).write_text(content, encoding="utf-8")
        (ws / ".mcp.json").write_text('{"mcpServers": {"otro": {"command": "otro-mcp"}}}', encoding="utf-8")
        (ws / ".codex").mkdir(parents=True, exist_ok=True)
        (ws / ".codex/config.toml").write_text('model = "otro"\n', encoding="utf-8")
        run(str(SRC / "scripts/install.py"), "--tool", "all", str(ws))
        run(str(SRC / "scripts/install.py"), "--tool", "all", str(ws))  # idempotente
        mcp = json.loads((ws / ".mcp.json").read_text(encoding="utf-8"))["mcpServers"]
        assert set(mcp) == {"otro", "se-tools"}, mcp
        toml = (ws / ".codex/config.toml").read_text(encoding="utf-8")
        assert toml.count("[mcp_servers.se-tools]") == 1 and 'model = "otro"' in toml, toml
        oc = json.loads((ws / ".opencode/opencode.json").read_text(encoding="utf-8"))
        assert oc["mcp"]["se-tools"]["command"][:3] == ["uv", "run", "--no-project"], oc
        assert not (ws / ".opencode/plugins/se-tools.js").exists(), "el plugin solo con --opencode-plugin"
        check_coexistence(ws, installed=True)
        sk = ws / ".agents/skills"
        opp = ws
        CWD.append(ws)  # los scripts trabajan sobre el directorio actual, sin ruta
        run(str(sk / "se-core/scripts/init_workspace.py"))
        (opp / "RFP/pliego.md").write_text("# Pliego\n\nRequisito de prueba.\n", encoding="utf-8")
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, PageBreak
            from reportlab.lib.styles import getSampleStyleSheet
            st = getSampleStyleSheet()
            SimpleDocTemplate(str(opp / "RFP/anexo.pdf"), pagesize=A4).build([
                Paragraph("Texto de prueba. " * 40, st["Normal"]), PageBreak(),
                Table([["Requisito", "SLA"], ["Disponibilidad", "99,5 %"], ["Latencia", "2 s"]], style=[("GRID", (0, 0), (-1, -1), 0.5, "black")])])
        except ImportError:
            print("-- reportlab no instalado: se omite la prueba de PDF")
        run(str(sk / "se-core/scripts/inventory_corpus.py"))
        run(str(sk / "se-core/scripts/inventory_corpus.py"), "--check")
        try:
            import pandas  # noqa: F401
            (opp / "data-samples/demo.csv").write_text("id,email\n1,a@b.com\n2,c@d.com\n", encoding="utf-8")
            run(str(sk / "se-analisis-fuentes-datos/scripts/profile_dataset.py"))
        except ImportError:
            print("-- pandas no instalado: se omite el perfilado")
        rs = str(sk / "se-corpus-rfp/scripts/req_scan.py")
        run(rs, "plan")
        run(rs, "status", ok=False)
        import json as _json
        plan = _json.loads((opp / "proposal/_meta/req-scan/plan.json").read_text(encoding="utf-8"))["units"]
        for u in plan:
            data = {"unidad": u["id"], "revisado": True, "leido_como_imagen": bool(u.get("image")), "notas": "prueba",
                    "requisitos": [{"texto": "Consultar clientes", "accion": "consultar", "objeto": "clientes",
                                    "tipo": "Funcional", "cita": "Requisito de prueba",
                                    "prioridad": "Obligatorio"}] if u["doc"].endswith("pliego.md") else []}
            f = opp / "proposal/_meta/req-scan/units" / (__import__("re").sub(r"[^\w.-]+", "_", u["id"]) + ".json")
            f.write_text(_json.dumps(data, ensure_ascii=False), encoding="utf-8")
        run(rs, "status")
        run(rs, "check", ok=False)
        run(rs, "findings")
        run(str(sk / "se-corpus-rfp/scripts/req_dedupe.py"), "groups")
        hid = __import__("re").search(r"`(H-[0-9a-f]{8})`", (opp / "proposal/_meta/req-scan/hallazgos.md").read_text(encoding="utf-8"))[1]
        (opp / "proposal/_meta/registro-requisitos.json").write_text(_json.dumps({
            "capacidades": [{"id": "CAP-01", "nombre": "Consultar clientes", "descripcion": "prueba"}], "requisitos": [
            {"id": "RQ-001", "texto": "Consultar clientes", "tipo": "Funcional", "prioridad": "Obligatorio",
             "estado": "Evidenciado", "capacidad": "CAP-01", "hallazgos": [hid], "notas": ""}],
            "descartados": [], "decisiones": []}), encoding="utf-8")
        run(rs, "check")
        run(rs, "matrix")
        run(str(sk / "se-corpus-rfp/scripts/req_calibrate.py"))
        hu = opp / "proposal/HU-Enfoque-Funcional-demo.md"
        hu.write_text("# HU-Enfoque-Funcional. Demo\n\n> **Estado:** HUs en revisión · **Versión:** 0.1 · **Fecha:** 2026-01-01 · **Fuentes:** `RFP/pliego.md`\n\n"
                      "## 1. Contexto\n\nContexto.\n\n## 2. Historia De Usuario\n\n### HU-DEM-01. Consulta\n\n"
                      "**Como** Gestor comercial,\n**quiero** consultar clientes,\n**para** planificar visitas.\n\n**Requisitos:** RQ-001\n", encoding="utf-8")
        g = str(sk / "se-hu-enfoque-funcional/scripts/hu_gate.py")
        run(str(sk / "se-core/scripts/validate_doc.py"), str(hu), str(sk / "se-hu-enfoque-funcional/assets/spec-hu.json"))
        run(g, "check", str(hu), ok=False)
        run(str(sk / "se-core/scripts/req_coverage.py"), "--doc", str(hu))
        run(g, "approve", str(hu), "--by", "smoke")
        run(g, "check", str(hu))
        run(g, "status")  # localiza el documento funcional sin ruta
        bl = opp / "proposal/6.0-backlog.md"
        bl.write_text(BACKLOG, encoding="utf-8")
        v = str(sk / "se-backlog-hu/scripts/validate_backlog.py")
        run(v, str(bl), "--require-final")
        run(v, str(bl), "--require-summary", ok=False)
        run(str(sk / "se-backlog-hu/scripts/effort_summary.py"), str(bl), "--write")
        run(v, str(bl), "--require-summary")
        run(v, "--require-summary")  # ruta por defecto proposal/6.0-backlog.md
        tools_check(ws)
        run(str(sk / "se-core/scripts/check_traceability.py"))
        dec, pref = str(sk / "se-core/scripts/decisiones.py"), str(sk / "se-core/scripts/preferencias.py")
        run(pref, "fijar", "--ambito", "cloud", "--valor", "Azure", "--nivel", "obligatoria", "--motivo", "partner", "--por", "smoke")
        run(dec, "registrar", "--origen", "agente", "--autor", "se-arquitecto-solucion", "--area", "tecnologia",
            "--titulo", "Nube", "--decision", "AWS", "--motivo", "cliente", "--ambito", "cloud", "--valor", "AWS")
        run(dec, "check", ok=False)
        run(dec, "registrar", "--origen", "agente", "--autor", "se-arquitecto-solucion", "--area", "tecnologia", "--tipo",
            "excepcion", "--excepcion-de", "PREF-01", "--titulo", "Excepción", "--decision", "AWS", "--motivo", "mandato del cliente")
        run(dec, "check", "--gate", ok=False)
        for d in ("D-003", "D-004"):  # D-001 = aprobación de HUs, D-002 = preferencia
            run(dec, "aceptar", d, "--por", "smoke")
        run(dec, "check", "--gate")
        run(pref, "validar")
        assert (opp / "proposal/_meta/decisiones.md").exists()
        vd = str(sk / "se-core/scripts/validate_doc.py")
        tec_tpl, ia_spec = str(sk / "se-hu-enfoque-tecnico/assets/template.md"), str(sk / "se-enfoque-ia-datos/assets/spec.json")
        run(vd, tec_tpl, ia_spec, "--section", "29", ok=False)  # la plantilla aún tiene restos
        tec = opp / "proposal/HU-Enfoque-Tecnico-&-Arquitectura-demo.md"
        tec.write_text("# HU-Enfoque-Tecnico-&-Arquitectura. Demo\n\n## 28. Riesgos Tecnicos\n\nNinguno.\n\n"
                       "## 29. Enfoque De IA Y Ciencia De Datos\n\nNo aplica: sin componente analítico.\n", encoding="utf-8")
        run(vd, str(tec), ia_spec, "--section", "29")
        for s in ("se-hu-enfoque-funcional", "se-hu-enfoque-tecnico", "se-analisis-fuentes-datos", "se-diseno-aplicacion"):
            run(str(sk / "se-core/scripts/validate_doc.py"), str(sk / s / "assets/template.md"), str(sk / s / "assets/spec.json"), ok=False)
        CWD.clear()
        run(str(SRC / "scripts/install.py"), "--uninstall", str(ws))
        check_coexistence(ws, installed=False)
        assert json.loads((ws / ".mcp.json").read_text(encoding="utf-8")) == {"mcpServers": {"otro": {"command": "otro-mcp"}}}
        assert "se-tools" not in (ws / ".codex/config.toml").read_text(encoding="utf-8")
        assert not (ws / ".opencode/opencode.json").exists()
        assert not (ws / ".opencode/plugins/se-tools.js").exists()
        assert (ws / "proposal/6.0-backlog.md").exists(), "la desinstalación no debe tocar el workspace"
        print("OK  convivencia con otro kit (instalar, reinstalar, desinstalar)")
    uv_flow()
    global_flow()
    run(str(SRC / "scripts/sync_agents.py"), "--check")
    print("Smoke test superado")
    return 0


if __name__ == "__main__":
    sys.exit(main())

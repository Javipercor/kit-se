#!/usr/bin/env python3
"""Herramientas del kit SE: registro único para el plugin de OpenCode y el servidor MCP.

Uso:
  uv run --group se se_tools.py list                      # definiciones (JSON) de todas las herramientas
  uv run --group se se_tools.py call <nombre> '<json>'    # ejecuta una herramienta y devuelve JSON
                                                          # {"ok": bool, "exit_code": int, "output": str}
Opciones de call: --root DIR (raíz del workspace; por defecto, el directorio actual o SE_WORKSPACE).

Cada herramienta envuelve un script determinista del kit con argumentos tipados (JSON Schema).
Las acciones humanas (aprobar HUs, aceptar o rechazar decisiones, registrar decisiones humanas,
fijar o quitar preferencias) NO se exponen como herramientas: solo existen como scripts, y en
OpenCode piden confirmación siempre. Así un agente no puede ejecutarlas a través de una herramienta.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

SKILLS = Path(__file__).resolve().parents[2] / "skills"   # .agents/skills o .claude/skills
TIMEOUT = 900


def script(skill: str, name: str) -> str:
    return str(SKILLS / skill / "scripts" / name)


@dataclass
class Tool:
    name: str
    description: str
    properties: dict
    build: Callable[[dict], list[str]]
    required: tuple[str, ...] = ()

    def schema(self) -> dict:
        return {"type": "object", "properties": self.properties, "required": list(self.required),
                "additionalProperties": False}


def flag(cond, *values) -> list[str]:
    return list(values) if cond else []


def opt(name: str, value) -> list[str]:
    return [name, str(value)] if value not in (None, "", []) else []


def lst(value) -> str:
    return "; ".join(value) if isinstance(value, list) else (value or "")


S = {"type": "string"}
B = {"type": "boolean"}
I = {"type": "integer"}
SPECS = {
    "funcional": ("se-hu-enfoque-funcional", "spec.json", None),
    "funcional-hus": ("se-hu-enfoque-funcional", "spec-hu.json", None),
    "datos": ("se-analisis-fuentes-datos", "spec.json", None),
    "tecnico": ("se-hu-enfoque-tecnico", "spec.json", None),
    "ia-seccion29": ("se-enfoque-ia-datos", "spec.json", "29"),
    "aplicacion": ("se-diseno-aplicacion", "spec.json", None),
}


def _validate_doc(a: dict) -> list[str]:
    skill, spec, section = SPECS[a["tipo"]]
    return [script("se-core", "validate_doc.py"), a["documento"], str(SKILLS / skill / "assets" / spec)] + \
        (["--section", section] if section else [])


def _register(a: dict) -> list[str]:
    cmd = [script("se-core", "decisiones.py"), "registrar", "--origen", "agente"]
    for key in ("autor", "area", "titulo", "decision", "motivo", "fase", "tipo", "impacto", "ambito", "valor",
                "preferencia", "excepcion_de", "sustituye"):
        cmd += opt("--" + key.replace("_", "-"), a.get(key))
    for key in ("alternativas", "evidencia", "afecta"):
        cmd += opt("--" + key, lst(a.get(key)))
    return cmd


TOOLS = [
    Tool("se_init_workspace",
         "Kit SE · Prepara el workspace en la raíz del repositorio: carpetas RFP/, data-samples/, templates/, "
         "proposal/; uv init y uv venv si faltan; dependencias del kit en el grupo 'se' de pyproject.toml.",
         {"embeddings": B | {"description": "Añadir también el SDK de Azure OpenAI"},
          "sin_dependencias": B | {"description": "No añadir dependencias"}},
         lambda a: [script("se-core", "init_workspace.py")] + flag(a.get("embeddings"), "--embeddings")
         + flag(a.get("sin_dependencias"), "--no-deps")),
    Tool("se_inventario_corpus",
         "Kit SE · Inventaría RFP/: texto por página, páginas visuales a PNG y tablas a Markdown (incremental).",
         {"render": {"type": "string", "enum": ["auto", "all", "none"]}, "completo": B},
         lambda a: [script("se-core", "inventory_corpus.py")] + opt("--render", a.get("render"))
         + flag(a.get("completo"), "--full")),
    Tool("se_barrido_requisitos",
         "Kit SE · Barrido página a página de requisitos: plan, next (siguientes unidades con texto e imagen), "
         "status, findings, check (consolidación) y matrix (genera 2-requirements-matrix.md).",
         {"accion": {"type": "string", "enum": ["plan", "next", "status", "findings", "check", "matrix"]},
          "lote": I | {"description": "Unidades por lote en 'next'"},
          "documento": S | {"description": "Limitar 'next' a un documento (ruta relativa)"}},
         lambda a: [script("se-corpus-rfp", "req_scan.py"), a["accion"]] + opt("--batch", a.get("lote"))
         + opt("--doc", a.get("documento")), ("accion",)),
    Tool("se_agrupar_requisitos",
         "Kit SE · Agrupa hallazgos parecidos (groups) o valida decisiones, duplicados y capacidades (lint).",
         {"accion": {"type": "string", "enum": ["groups", "lint"]}},
         lambda a: [script("se-corpus-rfp", "req_dedupe.py"), a["accion"]], ("accion",)),
    Tool("se_calibrar_similitud",
         "Kit SE · Propone umbrales de similitud a partir de consolidaciones ya hechas (no escribe la configuración).",
         {"workspaces": {"type": "array", "items": S}, "precision": {"type": "number"}, "recall": {"type": "number"}},
         lambda a: [script("se-corpus-rfp", "req_calibrate.py"), *(a.get("workspaces") or [])]
         + opt("--precision", a.get("precision")) + opt("--recall", a.get("recall"))),
    Tool("se_cobertura_requisitos",
         "Kit SE · Cobertura requisitos → HUs (y tabla 13.1 con seccion13).",
         {"documento": S, "seccion13": B},
         lambda a: [script("se-core", "req_coverage.py")] + opt("--doc", a.get("documento"))
         + flag(a.get("seccion13"), "--section13")),
    Tool("se_estado_hus",
         "Kit SE · Estado de aprobación de las HUs (propuesta, aprobada, modificada) y cobertura. "
         "La aprobación no es una herramienta: la decide una persona.",
         {"documento": S},
         lambda a: [script("se-hu-enfoque-funcional", "hu_gate.py"), "status"] + ([a["documento"]] if a.get("documento") else [])),
    Tool("se_validar_documento",
         "Kit SE · Valida un documento contra la estructura de su skill.",
         {"documento": S, "tipo": {"type": "string", "enum": list(SPECS)}},
         _validate_doc, ("documento", "tipo")),
    Tool("se_trazabilidad", "Kit SE · Trazabilidad entre artefactos: IDs huérfanos, HUs sin spec o backlog.",
         {"estricto": B}, lambda a: [script("se-core", "check_traceability.py")] + flag(a.get("estricto"), "--strict")),
    Tool("se_validar_specs", "Kit SE · Valida proposal/specs (índice, estructura y criterios de aceptación).",
         {}, lambda a: [script("se-spec-feature", "validate_spec.py")]),
    Tool("se_perfilar_datos", "Kit SE · Perfila las muestras de data-samples/ (tipos, nulos, claves, PII enmascarada).",
         {"fichero": S, "max_filas": I},
         lambda a: [script("se-analisis-fuentes-datos", "profile_dataset.py")] + opt("--file", a.get("fichero"))
         + opt("--max-rows", a.get("max_filas"))),
    Tool("se_validar_backlog", "Kit SE · Valida proposal/6.0-backlog.md contra su contrato.",
         {"final": B, "resumen": B},
         lambda a: [script("se-backlog-hu", "validate_backlog.py")] + flag(a.get("final"), "--require-final")
         + flag(a.get("resumen"), "--require-summary")),
    Tool("se_resumen_esfuerzo", "Kit SE · Calcula el resumen de esfuerzo del backlog (escribir lo añade al documento).",
         {"escribir": B}, lambda a: [script("se-backlog-hu", "effort_summary.py")] + flag(a.get("escribir"), "--write")),
    Tool("se_exportar_backlog",
         "Kit SE · Exporta el backlog detallado, sin LLM, a CSV de importación de Azure DevOps y al Excel de horas "
         "(proposal/exports/).",
         {"formato": {"type": "string", "enum": ["todos", "json", "ado", "xlsx"]}},
         lambda a: [script("se-backlog-hu", "export_backlog.py")] + opt("--formato", a.get("formato"))),
    Tool("se_diagrama_azure",
         "Kit SE · Genera un diagrama draw.io de arquitectura Azure con iconos oficiales desde una especificación JSON.",
         {"especificacion": S | {"description": "Ruta al JSON (ver skill se-diagrama-azure)"},
          "salida": S, "validar": B},
         lambda a: [script("se-diagrama-azure", "drawio_azure.py"), a["especificacion"]] + opt("--salida", a.get("salida"))
         + flag(a.get("validar"), "--validar"), ("especificacion",)),
    Tool("se_decisiones",
         "Kit SE · Consulta el registro de decisiones: listar, ver una, o check (integridad, preferencias; gate bloquea "
         "si hay propuestas de impacto alto pendientes). Aceptar y rechazar son acciones humanas y no están aquí.",
         {"accion": {"type": "string", "enum": ["listar", "ver", "check"]}, "id": S, "pendientes": B, "gate": B},
         lambda a: [script("se-core", "decisiones.py"), a["accion"]] + ([a["id"]] if a["accion"] == "ver" and a.get("id") else [])
         + flag(a["accion"] == "listar" and a.get("pendientes"), "--pendientes")
         + flag(a["accion"] == "check" and a.get("gate"), "--gate"), ("accion",)),
    Tool("se_registrar_decision_agente",
         "Kit SE · Registra una decisión o supuesto del agente (queda en estado 'propuesta' hasta que una persona la acepte).",
         {"autor": S, "area": S, "titulo": S, "decision": S, "motivo": S, "fase": S,
          "tipo": {"type": "string", "enum": ["decision", "supuesto", "excepcion"]},
          "impacto": {"type": "string", "enum": ["alto", "medio", "bajo"]},
          "alternativas": {"type": "array", "items": S}, "evidencia": {"type": "array", "items": S},
          "afecta": {"type": "array", "items": S}, "ambito": S, "valor": S, "preferencia": S,
          "excepcion_de": S, "sustituye": S},
         _register, ("autor", "area", "titulo", "decision", "motivo")),
    Tool("se_preferencias", "Kit SE · Lista o valida las preferencias tecnológicas y de arquitectura. Fijarlas es una acción humana.",
         {"accion": {"type": "string", "enum": ["listar", "validar"]}, "ambito": S},
         lambda a: [script("se-core", "preferencias.py"), a["accion"]]
         + opt("--ambito", a.get("ambito") if a["accion"] == "listar" else None), ("accion",)),
]
BY_NAME = {t.name: t for t in TOOLS}


def definitions() -> list[dict]:
    return [{"name": t.name, "description": t.description, "inputSchema": t.schema()} for t in TOOLS]


def check_args(tool: Tool, args: dict) -> str | None:
    if not isinstance(args, dict):
        return "los argumentos deben ser un objeto JSON"
    for r in tool.required:
        if args.get(r) in (None, ""):
            return f"falta el argumento obligatorio '{r}'"
    for k, v in args.items():
        prop = tool.properties.get(k)
        if prop is None:
            return f"argumento desconocido '{k}'"
        if "enum" in prop and v not in prop["enum"]:
            return f"'{k}' debe ser uno de: {', '.join(prop['enum'])}"
    return None


def call(name: str, args: dict, root: str | None = None) -> dict:
    tool = BY_NAME.get(name)
    if tool is None:
        return {"ok": False, "exit_code": 2, "output": f"herramienta desconocida: {name}"}
    err = check_args(tool, args)
    if err:
        return {"ok": False, "exit_code": 2, "output": err}
    cwd = Path(root or os.environ.get("SE_WORKSPACE") or Path.cwd())
    cmd = [sys.executable, *tool.build(args)]
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        return {"ok": False, "exit_code": 124, "output": f"tiempo agotado ({TIMEOUT}s)"}
    out = (r.stdout + ("\n" + r.stderr if r.stderr.strip() else "")).strip()
    return {"ok": r.returncode == 0, "exit_code": r.returncode, "output": out[-60000:]}


def main() -> int:
    argv = sys.argv[1:]
    root = None
    if "--root" in argv:
        i = argv.index("--root")
        root = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    if argv[:1] == ["list"]:
        print(json.dumps(definitions(), ensure_ascii=False))
        return 0
    if argv[:1] == ["call"] and len(argv) in (2, 3):
        args = json.loads(argv[2]) if len(argv) == 3 else {}
        res = call(argv[1], args, root)
        print(json.dumps(res, ensure_ascii=False))
        return 0 if res["ok"] else 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Servidor MCP (stdio) del kit SE: expone las herramientas de se_tools.py a Claude Code y Codex.

Uso: uv run --no-project se_mcp.py      (lo lanza el harness como servidor MCP por stdio)

Implementa el subconjunto de MCP que necesita un servidor de herramientas: initialize,
tools/list, tools/call y ping, con JSON-RPC 2.0 por stdio (un mensaje por línea). No depende
del paquete `mcp`, para no atarse a una versión concreta de su API.
El workspace es el directorio de trabajo con el que el cliente lanza el servidor (la raíz del
repositorio) o la variable SE_WORKSPACE.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from se_tools import call, definitions  # noqa: E402

SUPPORTED = ["2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05"]
SERVER = {"name": "se-tools", "title": "Kit SE (Solutions Engineering)", "version": "1.0.0"}
INSTRUCTIONS = ("Herramientas deterministas del kit SE (diseño de propuestas): requisitos, cobertura, validadores, "
                "decisiones, exportación del backlog y diagramas. Úsalas solo para trabajo del kit SE.")


def reply(msg_id, result=None, error=None) -> None:
    out = {"jsonrpc": "2.0", "id": msg_id}
    if error is not None:
        out["error"] = error
    else:
        out["result"] = result
    sys.stdout.write(json.dumps(out, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def handle(msg: dict) -> None:
    method, msg_id, params = msg.get("method"), msg.get("id"), msg.get("params") or {}
    if msg_id is None:  # notificación (initialized, cancelled…): sin respuesta
        return
    if method == "initialize":
        requested = params.get("protocolVersion")
        reply(msg_id, {"protocolVersion": requested if requested in SUPPORTED else SUPPORTED[1],
                       "capabilities": {"tools": {"listChanged": False}},
                       "serverInfo": SERVER, "instructions": INSTRUCTIONS})
    elif method == "ping":
        reply(msg_id, {})
    elif method == "tools/list":
        reply(msg_id, {"tools": definitions()})
    elif method == "tools/call":
        res = call(params.get("name", ""), params.get("arguments") or {})
        reply(msg_id, {"content": [{"type": "text", "text": res["output"] or ("OK" if res["ok"] else "KO")}],
                       "structuredContent": res, "isError": not res["ok"]})
    else:
        reply(msg_id, error={"code": -32601, "message": f"método no soportado: {method}"})


def main() -> int:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            reply(None, error={"code": -32700, "message": "JSON no válido"})
            continue
        try:
            handle(msg)
        except Exception as exc:  # noqa: BLE001 - el servidor no debe caerse por una herramienta
            reply(msg.get("id"), error={"code": -32603, "message": str(exc)})
    return 0


if __name__ == "__main__":
    sys.exit(main())

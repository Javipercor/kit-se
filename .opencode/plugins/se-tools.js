// Plugin de OpenCode 2 del kit SE (Solutions Engineering).
// Registra como herramientas nativas las definidas en .agents/se/tools/se_tools.py (mismo registro
// que el servidor MCP de Claude Code), y las ejecuta con `uv run --group se`.
// Las acciones humanas (aprobar HUs, aceptar/rechazar decisiones, fijar preferencias) no se exponen.
import { execFile, execFileSync } from "node:child_process"
import { fileURLToPath } from "node:url"
import path from "node:path"

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..")
const REGISTRY = path.join(ROOT, ".agents", "se", "tools", "se_tools.py")
const RUNNERS = [["run", "--group", "se"], ["run"]] // sin grupo si /se-init se hizo sin dependencias

function definitions() {
  for (const runner of RUNNERS) {
    try {
      const out = execFileSync("uv", [...runner, REGISTRY, "list"], { cwd: ROOT, encoding: "utf8", timeout: 120000 })
      return { runner, tools: JSON.parse(out) }
    } catch {}
  }
  return { runner: RUNNERS[0], tools: [] }
}

function call(runner, name, args) {
  return new Promise((resolve) => {
    execFile("uv", [...runner, REGISTRY, "call", name, JSON.stringify(args ?? {}), "--root", ROOT],
      { cwd: ROOT, encoding: "utf8", timeout: 900000, maxBuffer: 16 * 1024 * 1024 },
      (error, stdout, stderr) => {
        try {
          resolve(JSON.parse(stdout))
        } catch {
          resolve({ ok: false, exit_code: error?.code ?? 1, output: (stdout || "") + (stderr || String(error ?? "")) })
        }
      })
  })
}

export default {
  id: "se-kit.tools",
  setup: async (ctx) => {
    const { runner, tools } = definitions()
    if (!tools.length) {
      console.error("[se-kit] no se pudieron cargar las herramientas: ¿uv instalado y /se-init ejecutado?")
      return
    }
    await ctx.tool.transform((registry) => {
      for (const t of tools) {
        registry.add({
          name: t.name,
          description: t.description,
          jsonSchema: t.inputSchema,
          execute: async (input) => {
            const res = await call(runner, t.name, input)
            const text = res.output || (res.ok ? "OK" : "KO")
            return { structured: res, content: [{ type: "text", text: res.ok ? text : `KO (exit ${res.exit_code})\n${text}` }] }
          },
        })
      }
    })
  },
}

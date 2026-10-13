# Kit SE · Solutions Engineering (datos, IA y desarrollo Python/.NET)
#
#   make opencode [DEST=ruta] [FORCE=1]   Prepara/instala para OpenCode
#   make claude   [DEST=ruta] [FORCE=1]   Genera .claude/ y lo instala
#   make codex    [DEST=ruta] [FORCE=1]   Genera .codex/agents y lo instala
#   make all      [DEST=ruta] [FORCE=1]   Las tres herramientas
#
#   make uninstall DEST=ruta              Quita el kit SE sin tocar otros kits ni el workspace
#
#   make global [TOOL=all|opencode|claude|codex]      Instala el kit para todos tus repositorios (~/)
#   make global-uninstall [TOOL=...]                  Lo quita de tu carpeta personal
#   PLUGIN=1                              Instala además el plugin nativo de OpenCode 2 (opcional)
#
# Sin DEST se trabaja sobre la propia carpeta del kit. Solo se tocan elementos con prefijo se-.

PYTHON ?= uv run --no-project python
DEST   ?=
FORCE  ?=
TOOL   ?= all
PLUGIN ?=

INSTALL = $(PYTHON) scripts/install.py
ARGS    = $(DEST) $(if $(FORCE),--force,) $(if $(PLUGIN),--opencode-plugin,)

.DEFAULT_GOAL := help
.PHONY: help opencode claude codex all uninstall global global-uninstall mcp-test sync check test clean

help: ## Muestra esta ayuda
	@echo "Uso: make <objetivo> [DEST=ruta] [FORCE=1]   (requiere uv)"
	@echo ""
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*## "}{printf "  %-10s %s\n", $$1, $$2}'

opencode: ## Instala agentes, comandos y skills para OpenCode
	$(INSTALL) --tool opencode $(ARGS)

claude: ## Genera e instala la variante de Claude Code (.claude/, CLAUDE.md)
	$(INSTALL) --tool claude $(ARGS)

codex: ## Genera e instala la variante de Codex (.codex/agents, .agents/skills)
	$(INSTALL) --tool codex $(ARGS)

all: ## Instala para OpenCode, Claude Code y Codex
	$(INSTALL) --tool all $(ARGS)

uninstall: ## Quita el kit SE de DEST (conserva se.config.json y el workspace)
	$(PYTHON) scripts/install.py --uninstall $(DEST)

global: ## Instala el kit en tu carpeta personal para todos los repositorios (TOOL=all|opencode|claude|codex)
	$(INSTALL) --tool $(TOOL) --global $(if $(PLUGIN),--opencode-plugin,)

global-uninstall: ## Quita la instalación global (TOOL=all|opencode|claude|codex)
	$(INSTALL) --uninstall --global --tool $(TOOL)

mcp-test: ## Arranca el servidor MCP y comprueba que responde (initialize + tools/list)
	@printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"make","version":"1"}}}' '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' | uv run --no-project .agents/se/tools/se_mcp.py | python3 -c "import sys,json;r=[json.loads(l) for l in sys.stdin];print('OK se-tools', r[0]['result']['serverInfo']['version'], '·', len(r[1]['result']['tools']), 'herramientas')"

sync: ## Regenera .claude/ y .codex/ desde las fuentes
	$(PYTHON) scripts/sync_agents.py

check: ## Falla si .claude/ o .codex/ están desactualizados (para CI)
	$(PYTHON) scripts/sync_agents.py --check

test: ## Prueba rápida de instalación y scripts
	$(PYTHON) scripts/smoke_test.py

clean: ## Borra las variantes generadas y cachés
	rm -rf .claude/agents/se-* .claude/commands/se-* .claude/skills/se-* .claude/se .claude/se-lider-proyecto.md .codex/agents/se-* .codex/se-lider-proyecto.md
	find . -name __pycache__ -type d -prune -exec rm -rf {} +

# Kit SE · Solutions Engineering (datos, IA y desarrollo Python/.NET)
#
#   make opencode [DEST=ruta] [FORCE=1]   Prepara/instala para OpenCode
#   make claude   [DEST=ruta] [FORCE=1]   Genera .claude/ y lo instala
#   make codex    [DEST=ruta] [FORCE=1]   Genera .codex/agents y lo instala
#   make all      [DEST=ruta] [FORCE=1]   Las tres herramientas
#
#   make uninstall DEST=ruta              Quita el kit SE sin tocar otros kits ni el workspace
#
# Sin DEST se trabaja sobre la propia carpeta del kit. Solo se tocan elementos con prefijo se-.

PYTHON ?= uv run --no-project python
DEST   ?=
FORCE  ?=

INSTALL = $(PYTHON) scripts/install.py
ARGS    = $(DEST) $(if $(FORCE),--force,)

.DEFAULT_GOAL := help
.PHONY: help opencode claude codex all uninstall sync check test clean

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

sync: ## Regenera .claude/ y .codex/ desde las fuentes
	$(PYTHON) scripts/sync_agents.py

check: ## Falla si .claude/ o .codex/ están desactualizados (para CI)
	$(PYTHON) scripts/sync_agents.py --check

test: ## Prueba rápida de instalación y scripts
	$(PYTHON) scripts/smoke_test.py

clean: ## Borra las variantes generadas y cachés
	rm -rf .claude/agents/se-* .claude/commands/se-* .claude/skills/se-* .claude/se .claude/se-lider-proyecto.md .codex/agents/se-* .codex/se-lider-proyecto.md
	find . -name __pycache__ -type d -prune -exec rm -rf {} +

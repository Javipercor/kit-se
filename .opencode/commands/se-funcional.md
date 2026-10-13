---
description: "Kit SE · Fase 1 · Propuesta de HUs con cobertura de requisitos → aprobar → documento funcional completo"
agent: se-analista-funcional
---
Instrucción: `$ARGUMENTS`.
Ejecuta la skill `se-hu-enfoque-funcional` resolviendo la etapa con `hu_gate.py status`:
- Sin aprobación y sin la palabra `aprobar` en la instrucción: propón o revisa las HUs (aplicando los cambios que pida la instrucción) y detente pidiendo aprobación.
- Con `aprobar` en la instrucción: registra la aprobación y genera el resto del documento a partir de las HUs aprobadas.
Devuelve el Informe de retorno.

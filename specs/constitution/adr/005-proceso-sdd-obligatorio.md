# ADR-005: Proceso SDD obligatorio (briefing → spec → plan → tasks → gate humano) antes de código de producción

**Estado:** Aceptado

## Contexto
Un sistema multi-agente que escribe código automáticamente necesita un punto de control humano antes de que el código llegue a producción, para evitar que agentes generen features no alineadas con la intención real del negocio.

## Decisión
Toda funcionalidad nueva sigue el proceso descrito en `specs/constitution/workflow.md`: briefing.md → spec.md → plan.md → tasks.md → gate humano, antes de escribir código. No se permite código de producción para una feature nueva sin pasar por esos 4 documentos y el gate.

## Alternativas consideradas
Generación directa de código a partir del requerimiento (spec_agent → impl_agent sin gate intermedio) — descartada por riesgo de que el agente implemente una interpretación incorrecta del requerimiento sin que un humano la revise a tiempo.

## Consecuencias
Mayor latencia por feature (4 documentos + revisión humana antes de codear), a cambio de trazabilidad completa de por qué existe cada pieza de código y un punto de corrección barato (antes de escribir código) en vez de caro (después, vía code review o revert).

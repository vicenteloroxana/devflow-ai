# Backlog de features — DevFlow AI

> Lista priorizada de features del sistema. Se actualiza a medida que
> se construyen (marcar [x] y linkear la carpeta en `specs/features/`).
> Derivado de los componentes declarados en `../constitution/mission.md`.

- [x] 001 — Agente Spec → [001-spec-agent](001-spec-agent/)
- [x] 002 — Agente Implementador → [002-impl-agent](002-impl-agent/)
- [ ] 003 — Agente Revisor (Maker/Checker, severidad critical/warning/info)
- [ ] 004 — Agente Eval (PromptFoo, pass/fail contra criterios de la spec)
- [ ] 005 — Agente Orquestador (coordina el flujo, máx. 3 reintentos, webhook si falla)
- [ ] 006 — Endpoints API workflows (`POST /api/workflows`, `GET .../{id}`, `.../spec`, `.../review`, `POST .../approve`)

## Cómo agregar una feature nueva
1. Agregar línea `- [ ] 00N — nombre` acá.
2. Seguir el proceso de `../constitution/workflow.md` (briefing → spec → plan → tasks → gates).
3. Al mergear el PR, marcar `[x]` y linkear la carpeta.

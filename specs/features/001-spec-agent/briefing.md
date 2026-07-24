# Briefing — Spec Agent

## Qué hace
El Spec Agent recibe un requerimiento de software en lenguaje natural
(texto libre, escrito por un humano) y genera una especificación técnica
estructurada en Markdown, lista para que el Agente Implementador la use
como input.

Es el primer eslabón del flujo de DevFlow AI: sin una spec clara y
completa, el Implementador no tiene base para generar código correcto.

## Input
- **Campo principal**: `requirement` (string, texto libre) — la
  descripción del requerimiento tal como la escribiría un humano. Ej:
  "Necesito un endpoint que liste los workflows de un usuario paginados".
- **Campos opcionales** (metadata para dar contexto sin obligar a
  estructurar todo):
  - `context`: contexto adicional del sistema o módulo afectado.
  - `priority`: prioridad del requerimiento (baja/media/alta).
  - `area`: área del sistema al que pertenece (ej: "API", "agents",
    "infra").

No se espera que el usuario estructure el requerimiento — el agente es
responsable de interpretar texto libre y producir una spec estructurada.

## Output
Un documento Markdown con secciones estandarizadas, consistente con el
formato ya usado en `specs/constitution/mission.md`:

1. **Objetivo** — qué problema resuelve el requerimiento.
2. **Alcance** — qué incluye y qué explícitamente NO incluye.
3. **Contexto técnico** — dónde encaja en la arquitectura existente
   (capa, módulo, agente).
4. **Diseño propuesto** — approach técnico a alto nivel (sin código).
5. **Criterios de aceptación** — lista verificable de condiciones que
   determinan que la implementación es correcta.
6. **Fuera de alcance** — qué queda explícitamente excluido de esta spec.

El archivo se guarda en `specs/` siguiendo la convención de numeración
existente (`specs/0N-nombre-descriptivo.md`).

## Restricciones técnicas
- **LLM**: Groq `llama-3.3-70b-versatile` (LLM de desarrollo definido en
  CLAUDE.md, costo $0). No usar Anthropic en este agente — está
  reservado para demo.
- **Temperatura**: 0.3 — output semi-determinista, evitar creatividad
  excesiva en una spec técnica.
- **Framework**: FastAPI + Pydantic para validación de input/output.
  `async/await` en todos los endpoints (regla del CLAUDE.md, nunca sync
  en FastAPI).
- **Prompts**: el prompt del LLM debe vivir como template parametrizado.
  Dado que este agente es Python (no la capa .NET), el equivalente a
  "Prompts en Application/Prompts/" es mantenerlo en un módulo dedicado
  dentro de `spec_agent/` (ej. `spec_agent/prompts.py`), no hardcodeado
  inline en la lógica del endpoint.
- **Type hints** en todas las funciones; docstrings en español para
  funciones de negocio (regla del CLAUDE.md).
- El agente NO debe inventar detalles de arquitectura que no estén en
  `CLAUDE.md` o `specs/constitution/mission.md` — si el requerimiento es
  ambiguo, la spec generada debe señalar explícitamente los supuestos
  hechos.

## Contexto del proyecto
- Este agente corre dentro de `src/agents/spec_agent/`, expuesto vía
  FastAPI (ver `src/agents/main.py`, ya monta el router en
  `/api/agents/spec`).
- Se integra al flujo mayor descrito en `specs/constitution/mission.md`:
  el Agente Orquestador invoca al Spec Agent como primer paso del
  workflow.
- Fase actual (Fase 2 del proyecto): estamos construyendo el Spec Agent
  de forma aislada, con SDD (Spec-Driven Development) — se aprueba la
  spec y el plan antes de escribir código.

## Criterios de éxito de este agente
- Dado un requerimiento ambiguo o incompleto, el agente genera una spec
  igual, marcando explícitamente los supuestos o vacíos de información
  (no falla, no inventa silenciosamente).
- La spec generada es consistente en formato con `specs/constitution/mission.md`.
- El endpoint responde en un tiempo razonable para uso interactivo
  (referencia: unos pocos segundos, dependiente de la latencia de Groq).
- El prompt es evaluable con PromptFoo (Paso 8 del roadmap de esta
  fase) — por lo tanto debe ser determinista dado el mismo input y
  temperatura.

# Briefing — Agente Implementador

## Qué hace
El Agente Implementador recibe la ruta a una spec técnica ya aprobada
(generada por el Spec Agent) y devuelve el contenido de un archivo de
código que implementa esa spec, siguiendo las convenciones del
CLAUDE.md.

Es el segundo eslabón del flujo de DevFlow AI: consume el output del
Spec Agent (Fase 2) como su propio input.

## Input
- **Campo principal**: `spec_path` (string) — ruta relativa a un
  archivo `spec.md` ya existente y aprobado, ej.
  `specs/features/003-algo/spec.md`. El agente lee el archivo del
  filesystem, no recibe el markdown en el body del request.
- **Campos opcionales**:
  - `target_file`: ruta relativa sugerida de dónde debería crearse o
    modificarse el código (ej. `src/agents/impl_agent/models.py`). Si
    no se provee, el agente debe inferirla de la sección "Contexto
    técnico" / "Diseño propuesto" de la spec.

## Output
- **Un solo archivo de código por request** (alcance acotado, igual
  que el Spec Agent genera una sola spec por request).
- El agente **escribe el archivo a disco** (mismo patrón que
  `persist_spec` en el Spec Agent) y también lo devuelve en la
  respuesta HTTP para que el caller vea el resultado sin tener que
  leer el filesystem aparte.
- Respuesta:
  - `code`: contenido completo del archivo generado.
  - `file_path`: ruta donde se escribió.
  - `spec_path`: la spec de origen (trazabilidad).
  - `notes`: lista de observaciones del agente sobre la implementación
    (ej. supuestos hechos, partes de la spec que no pudo resolver
    completamente) — mismo espíritu que `assumptions` en el Spec
    Agent.

## Restricciones técnicas
- **LLM**: Groq `llama-3.3-70b-versatile` (igual que el Spec Agent,
  LLM de desarrollo, costo $0).
- **Temperatura**: a definir en la spec — el código requiere más
  determinismo que una spec en prosa; probablemente menor a 0.3.
- **Framework**: FastAPI + Pydantic, async/await siempre (regla del
  CLAUDE.md).
- **Prompts**: en módulo dedicado `impl_agent/prompts.py`, no inline.
- **Convenciones a inyectar en el prompt**: el prompt debe incluir
  las reglas relevantes del CLAUDE.md (type hints, Pydantic para
  validación, async/await, docstrings en español para funciones de
  negocio) para que el código generado las respete.
- **Escritura a disco**: dado que escribe código real al repo, debe
  ser explícito y seguro — no debe sobrescribir un archivo existente
  sin señal clara (a definir el comportamiento exacto en la spec:
  ¿error si ya existe? ¿requiere flag explícito de "overwrite"?).
- El agente NO debe inventar detalles de arquitectura que no estén en
  la spec de origen, `CLAUDE.md`, o `specs/constitution/mission.md`.

## Contexto del proyecto
- Corre en `src/agents/impl_agent/` (carpeta ya existe, vacía desde
  la Fase 1).
- Se integra al flujo mayor descrito en `specs/constitution/mission.md`:
  el Agente Orquestador (todavía no construido) invocaría al
  Implementador después del Spec Agent.
- Sigue el proceso definido en `specs/constitution/workflow.md`:
  briefing → spec → plan → tasks → gate humano → código → gate de
  revisión de código.
- Se construye y valida de forma aislada (como el Spec Agent), sin
  depender de que el Orquestador exista.

## Criterios de éxito de este agente
- Dada una spec real (ej. `specs/features/001-spec-agent/spec.md`),
  genera código que compila/importa sin errores de sintaxis.
- El código generado respeta las convenciones del CLAUDE.md de forma
  verificable (type hints presentes, docstrings en español donde
  aplica).
- Si la spec es ambigua o insuficiente para generar código completo,
  el agente lo señala explícitamente en `notes`, no inventa
  silenciosamente.
- El endpoint responde en un tiempo razonable para uso interactivo.
- El prompt es evaluable con PromptFoo, igual que el Spec Agent.

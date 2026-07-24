# Spec Agent — Tasks

> Desglose ejecutable de `specs/features/001-spec-agent/plan.md` (aprobado en el
> gate del Paso 4). Claude Code implementa siguiendo este orden.
> Tareas `[P]` son paralelizables entre sí (tocan archivos distintos,
> sin dependencias cruzadas).

## Fase 1 — Setup
- [ ] T1. Agregar `pytest`, `pytest-asyncio`, `httpx` a
      `src/agents/requirements.txt` e instalar en el `.venv`.

## Fase 2 — Foundational (bloquea todo lo demás)
- [ ] T2. Crear `spec_agent/models.py` con `SpecRequest` y
      `SpecResponse` (Pydantic), según `01-spec-agent.md` § Diseño
      propuesto.
- [ ] T3. Escribir `tests/agents/test_spec_agent.py` con los tests de
      los 7 criterios de aceptación de `01-spec-agent.md` —
      **deben fallar en este punto** (no existe implementación aún).
      Cubre:
      - T3a. Requerimiento claro → `200` con las 6 secciones no vacías.
      - T3b. Requerimiento ambiguo → `assumptions` no vacío.
      - T3c. Archivo persistido en `specs/` con nombre único, no
        sobrescribe uno existente.
      - T3d. Cadena de llamadas es `async` (test con `httpx.AsyncClient`).
      - T3e. Ninguna API key hardcodeada (test estático simple:
        grep del código fuente, o test funcional con env var mockeada).
      - T3f. Mismo input + misma temperatura → misma estructura de
        salida (mock del LLM con respuesta fija, valida el parseo).
      - T3g. Fallo del LLM (mock lanza excepción) → `502`, sin
        reintentos observables.

## Fase 3 — Implementación (User Story única: generar la spec)
- [ ] T4. Crear `spec_agent/prompts.py` con `build_prompt()`, según
      `01-spec-agent-plan.md` § Estructura de archivos. Incluye
      instrucciones para marcar supuestos y no inventar arquitectura.
- [ ] T5. Crear `spec_agent/service.py`:
      - `persist_spec()` — cálculo de siguiente número disponible +
        slug, según convención aprobada
        (`specs/0N-{area-o-generico}-{slug-requerimiento}.md`).
      - `generate_spec()` — orquesta prompt → Groq → parseo → persistencia.
      - Manejo de error del LLM → `HTTPException(502)`, sin retry.
      - Validación de las 6 secciones antes de persistir; si falta
        alguna, mismo camino que fallo de LLM (502).
- [ ] T6. Modificar `spec_agent/router.py`: agregar
      `POST /generate` que delega a `service.generate_spec()`, sin
      lógica de negocio en el router.
- [ ] **CHECKPOINT — correr `pytest tests/agents/test_spec_agent.py`.**
      Todos los tests de T3 deben pasar en verde antes de continuar.

## Fase 4 — Polish
- [ ] T7. Revisar que todas las funciones nuevas tengan type hints
      completos y docstrings en español (regla del CLAUDE.md).
- [ ] T8. Validación manual: levantar `docker-compose up`, hacer un
      `POST` real a `http://localhost:8000/api/agents/spec/generate`
      con un requerimiento de ejemplo, confirmar que el archivo
      aparece en `specs/`.

## Dependencias entre tareas
```
T1 ─┐
T2 ─┼─→ T3 (tests, deben fallar) ─→ T4 [P] ─┐
    │                                T5 [P] ─┼─→ T6 ─→ CHECKPOINT ─→ T7 ─→ T8
    └────────────────────────────────────────┘
```
T4 y T5 pueden desarrollarse en paralelo (no dependen entre sí, ambos
dependen de T2/T3). T6 depende de que T4 y T5 existan, porque el
router los importa.

## Definición de "hecho" para esta fase
- Los 7 tests de `test_spec_agent.py` pasan.
- El checkpoint manual (T8) confirma un archivo real generado en
  `specs/` vía request HTTP contra el contenedor Docker.
- No quedan `TODO`/`FIXME` en el código nuevo.
- Continúa con el Paso 6 del roadmap de fase (revisión humana del
  código generado).

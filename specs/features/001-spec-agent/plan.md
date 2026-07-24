# Spec Agent — Plan de Implementación

> Basado en `specs/features/001-spec-agent/spec.md`. Pendiente de revisión y
> aprobación humana (Paso 4) antes de generar `tasks.md` y de que
> Claude Code toque código.

## Resumen
Implementar el endpoint `POST /api/agents/spec/generate` dentro de
`spec_agent/`, con un módulo de modelos Pydantic, un módulo de prompt
parametrizado, un cliente LLM (Groq vía `langchain-groq`), y la lógica
de persistencia del archivo generado en `specs/`.

## Contexto técnico
- **Lenguaje/runtime**: Python 3.12, async/await en toda la cadena.
- **Dependencias ya instaladas**: `fastapi`, `pydantic`,
  `langchain-groq`, `python-dotenv`, `pydantic-settings`.
- **Config existente reutilizable**: `shared/config.py` (`Settings`)
  ya expone `groq_api_key`, `llm_model`, `llm_temperature` — no
  requiere cambios.
- **Testing**: `pytest` (pendiente de agregar a `requirements.txt`,
  no está instalado todavía) + `promptfoo` para evals (Paso 8, fuera
  del alcance de este plan de código).
- **Target**: servicio existente `src/agents/`, corre en contenedor
  Docker ya validado (Fase 1).
- **Performance**: sin objetivo numérico estricto — referencia de la
  spec es "unos pocos segundos", dependiente de latencia de Groq. No
  se diseña con caché ni optimización prematura.
- **Scale/scope**: un solo endpoint, sin concurrencia especial más
  allá de lo que FastAPI/uvicorn manejan por defecto.

## Chequeo contra CLAUDE.md (equivalente a "Constitution Check")
| Regla del CLAUDE.md | Cómo se cumple en este plan |
|---|---|
| Type hints en todas las funciones | Todos los módulos nuevos tipados explícitamente |
| Pydantic para validación input/output | `SpecRequest`/`SpecResponse` en `spec_agent/models.py` |
| async/await siempre, nunca sync en FastAPI | Endpoint y llamada a Groq ambos `async def` |
| Docstrings en español para funciones de negocio | Aplica a `generate_spec()`, `build_prompt()`, `persist_spec()` |
| API keys nunca en código | Se leen vía `Settings`, ya configurado |
| Prompts como templates parametrizados, no inline | `spec_agent/prompts.py` dedicado |

Ninguna regla del CLAUDE.md requiere una excepción — no hay entradas
para una tabla de "Complexity Tracking".

## Estructura de archivos (nuevos y modificados)

```
src/agents/spec_agent/
├── __init__.py          (existente, sin cambios)
├── router.py             (MODIFICAR: agregar endpoint /generate)
├── models.py              (NUEVO: SpecRequest, SpecResponse)
├── prompts.py             (NUEVO: build_prompt())
└── service.py              (NUEVO: generate_spec(), persist_spec())

tests/agents/
└── test_spec_agent.py     (NUEVO: pytest — Paso 7 del roadmap de fase,
                             pero el archivo se crea en este plan)
```

### Responsabilidad de cada módulo
- **`models.py`**: define `SpecRequest` y `SpecResponse` (Pydantic),
  tal como se especificaron en `01-spec-agent.md` § Diseño propuesto.
- **`prompts.py`**: función `build_prompt(request: SpecRequest) -> str`
  que arma el prompt inyectando el requerimiento, campos opcionales, y
  el contexto de `CLAUDE.md`/`specs/constitution/mission.md` como texto
  fijo embebido (no leído en runtime — evita I/O innecesario y acopla
  el prompt a una versión conocida del contexto).
- **`service.py`**:
  - `generate_spec(request: SpecRequest) -> SpecResponse`: orquesta
    prompt → llamada a Groq → parseo → persistencia.
  - `persist_spec(markdown: str, request: SpecRequest) -> str`:
    calcula el siguiente número disponible en `specs/`, genera el
    slug del nombre de archivo, escribe el archivo, devuelve la ruta.
  - Manejo de errores del LLM: capturar excepciones de
    `langchain-groq` y re-lanzar como `HTTPException(502, ...)`.
- **`router.py`**: agrega `POST /generate` que valida `SpecRequest`,
  llama a `service.generate_spec()`, devuelve `SpecResponse`. Sin
  lógica de negocio en el router mismo (delega todo a `service.py`).

## Pasos de implementación (alto nivel — el desglose fino va en tasks.md)
1. Agregar `pytest`, `pytest-asyncio`, `httpx` (para `TestClient` async)
   a `requirements.txt`.
2. Crear `models.py` con `SpecRequest`/`SpecResponse`.
3. Crear `prompts.py` con `build_prompt()`, incluyendo instrucciones
   explícitas al LLM para marcar supuestos y no inventar arquitectura.
4. Crear `service.py` con `generate_spec()` y `persist_spec()`.
5. Modificar `router.py` para exponer `POST /generate`.
6. Escribir tests en `tests/agents/test_spec_agent.py` cubriendo los
   7 criterios de aceptación de `01-spec-agent.md`.
7. Validar manualmente con `curl`/Postman contra el contenedor
   `agents` levantado vía `docker-compose up`.

## Riesgos y mitigaciones
- **Parseo de la respuesta del LLM en 6 secciones fijas**: el LLM
  puede no respetar el formato exacto. Mitigación: el prompt pide
  headers Markdown literales (`## Objetivo`, etc.) y `service.py`
  valida que las 6 secciones estén presentes antes de persistir; si
  falta alguna, se trata como error 502 (mismo camino que fallo de
  LLM), no como éxito parcial silencioso.
- **Concurrencia al calcular "siguiente número disponible" en
  `specs/`**: dos requests simultáneos podrían colisionar en el mismo
  número. Fuera de alcance mitigarlo en v1 (single-user, uso
  interno) — se documenta como limitación conocida, no se implementa
  locking.

## Supuestos — aprobados en revisión humana (Paso 4)
Confirmados sin cambios respecto a lo propuesto:
1. Nombrado de archivo: `specs/0N-{area-o-generico}-{slug-requerimiento}.md`.
2. Fallo de LLM → `HTTPException(502)`, sin retry (retry es
   responsabilidad del Orquestador, fuera de este agente).
3. Sin indexado en pgvector en v1.

## Próximo paso
Con este plan aprobado (o corregido) en el gate del Paso 4, el
siguiente artefacto es `specs/features/001-spec-agent/tasks.md`: desglose de
los 7 pasos de arriba en tareas atómicas, ordenadas, con tests
escritos antes que la implementación de cada pieza cuando aplique.

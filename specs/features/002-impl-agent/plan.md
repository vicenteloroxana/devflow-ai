# Agente Implementador — Plan de Implementación

> Basado en `specs/features/002-impl-agent/spec.md`.
> Gate 1 (revisión humana) aprobado — ver "Supuestos" al final.

## Resumen

Implementar el endpoint `POST /api/agents/impl/generate` dentro de
`impl_agent/`, con un módulo de modelos Pydantic, un módulo de prompt
parametrizado (con convenciones del `CLAUDE.md` inyectadas), un cliente
LLM (Groq vía `langchain-groq`), y la lógica de lectura de spec desde
filesystem, inferencia de ruta de destino, y escritura segura del
archivo generado.

## Contexto técnico

- **Lenguaje/runtime**: Python 3.12, async/await en toda la cadena.
- **Dependencias ya instaladas**: `fastapi`, `pydantic`, `langchain-groq`,
  `python-dotenv`, `pydantic-settings`, `pytest`, `pytest-asyncio`,
  `httpx` (instaladas en la Fase del Spec Agent).
- **Config existente reutilizable**: `shared/config.py` (`Settings`)
  expone `groq_api_key`, `llm_model`, `llm_temperature` — no requiere
  cambios.
- **Temperatura**: `0.1` — aprobada en Gate 1 para mayor determinismo
  en código vs. prosa (0.3 del Spec Agent).
- **Timeout de Groq**: `30s` (default de `langchain-groq`) — aprobado
  en Gate 1.
- **Patrón de referencia**: `spec_agent/` — misma estructura de módulos,
  mismas convenciones. No reinventar lo que ya funciona.
- **Target**: `src/agents/impl_agent/` (carpeta vacía desde Fase 1).

## Constitution Check (contra CLAUDE.md)

| Regla del CLAUDE.md | Cómo se cumple en este plan |
|---|---|
| Type hints en todas las funciones | Todos los módulos nuevos tipados explícitamente |
| Pydantic para validación input/output | `ImplRequest`/`ImplResponse` en `impl_agent/models.py` |
| async/await siempre, nunca sync en FastAPI | Endpoint y llamada a Groq ambos `async def` |
| Docstrings en español para funciones de negocio | `generate_code()`, `build_prompt()`, `write_file()` |
| API keys nunca en código | Se leen vía `Settings`, ya configurado |
| Prompts como templates parametrizados, no inline | `impl_agent/prompts.py` dedicado |

## Estructura de archivos (nuevos y modificados)

```
src/agents/impl_agent/
├── __init__.py          (existente, sin cambios)
├── router.py             (NUEVO: endpoint POST /generate)
├── models.py             (NUEVO: ImplRequest, ImplResponse)
├── prompts.py            (NUEVO: build_prompt())
└── service.py            (NUEVO: generate_code(), write_file(), infer_target())

tests/agents/
└── test_impl_agent.py    (NUEVO: pytest — se escribe antes que la implementación)
```

### Responsabilidad de cada módulo

- **`models.py`**: define `ImplRequest` y `ImplResponse` (Pydantic)
  según `spec.md` § Diseño propuesto.
- **`prompts.py`**: función `build_prompt(spec_content: str, request: ImplRequest) -> str`
  que arma el prompt inyectando la spec completa + las convenciones
  relevantes del `CLAUDE.md` como texto fijo. El LLM debe aplicar type
  hints, async/await y docstrings en español en el código generado.
- **`service.py`**:
  - `generate_code(request: ImplRequest) -> ImplResponse`: orquesta
    lectura de spec → inferencia de ruta → prompt → Groq → extracción
    de código → escritura a disco.
  - `infer_target(spec_content: str) -> str`: extrae la ruta de destino
    del archivo desde las secciones "Contexto técnico" o "Diseño
    propuesto" de la spec usando regex o parsing de Markdown.
  - `write_file(path: str, content: str, overwrite: bool) -> None`:
    verifica existencia, crea directorios intermedios, escribe el archivo.
    Lanza `HTTPException(409)` si el archivo existe y `overwrite=False`.
    Lanza `HTTPException(403)` si el archivo existe, `overwrite=True`,
    y `path` está fuera de `src/agents/impl_agent/` (usar
    `Path.resolve()` + comparación de ancestros, no comparación de
    strings, para evitar bypass con `../`).
  - Manejo de errores: `HTTPException(404)` si `spec_path` no existe,
    `HTTPException(502)` si Groq falla o la respuesta no contiene código.
- **`router.py`**: `POST /generate` que delega a `service.generate_code()`.
  Sin lógica de negocio en el router.

## Correctness Properties

Las siguientes propiedades son garantías universales del sistema,
verificables con `hypothesis` (property-based testing). Se escriben
antes de las tareas de testing y cada una mapea a un requisito de
`spec.md`.

### Property 1: Idempotencia de lectura de spec

*Para cualquier* `spec_path` que apunte a un archivo existente,
el sistema SIEMPRE leerá el mismo contenido en llamadas sucesivas
sin modificar el archivo.
**Validates: Requisito 1.1**

### Property 2: Unicidad de escritura sin overwrite

*Para cualquier* `target_file` que ya exista en disco,
cuando `overwrite=False`, el sistema NUNCA modifica el archivo
y SIEMPRE retorna HTTP 409.
**Validates: Requisito 3.1**

### Property 3: Creación segura de archivo nuevo

*Para cualquier* `target_file` que NO exista en disco,
el sistema SIEMPRE crea el archivo (incluyendo directorios intermedios),
NUNCA retorna error por ausencia de directorios padre,
y el contenido escrito es igual al `code` retornado en `ImplResponse`.
**Validates: Requisito 3.3**

### Property 4: Trazabilidad del spec_path

*Para cualquier* request exitoso,
`ImplResponse.spec_path` SIEMPRE es igual a `ImplRequest.spec_path`
— nunca se modifica, normaliza ni transforma.
**Validates: Requisito 5.1**

### Property 5: Ausencia de llamada al LLM ante spec inexistente

*Para cualquier* `spec_path` que NO exista en el filesystem,
el sistema NUNCA invoca a la API de Groq y SIEMPRE retorna HTTP 404.
**Validates: Requisito 4.1**

### Property 6: Contención de errores del LLM

*Para cualquier* fallo de la API de Groq (excepción, timeout,
respuesta sin bloque de código), el sistema NUNCA escribe nada a disco
y SIEMPRE retorna HTTP 502 con mensaje descriptivo.
**Validates: Requisito 4.2, Requisito 4.3**

### Property 7: Overwrite confinado a impl_agent/

*Para cualquier* `target_file` que ya exista en disco y esté fuera de
`src/agents/impl_agent/` (incluyendo intentos de escape con `../`),
el sistema SIEMPRE retorna HTTP 403 y NUNCA modifica el archivo,
sin importar el valor de `overwrite`.
**Validates: Requisito 3.3**

## Riesgos y mitigaciones

- **Extracción del bloque de código de la respuesta del LLM**: el LLM
  puede no envolver el código en un bloque markdown (\`\`\`python...\`\`\`).
  Mitigación: el prompt instruye explícitamente el formato esperado y
  `service.py` valida con regex antes de persistir; si no hay bloque
  extraíble → 502 (Property 6).
- **Inferencia de `target_file` desde la spec**: la sección "Contexto
  técnico" puede no contener una ruta de archivo explícita.
  Mitigación: si la inferencia falla, el agente incluye la observación
  en `notes` y usa una ruta genérica predecible
  (`src/agents/impl_agent/generated_{timestamp}.py`). Nunca falla
  silenciosamente.
- **Concurrencia al escribir el mismo archivo**: dos requests
  simultáneos con el mismo `target_file` y `overwrite=True` pueden
  producir race condition. Fuera de alcance en v1 (single-user, uso
  interno) — documentado como limitación conocida.
- **Bypass de la restricción de carpeta con rutas relativas (`../`)**:
  un `target_file` como `../spec_agent/service.py` podría escapar de
  `impl_agent/` si se compara por string en vez de por path resuelto.
  Mitigación: `write_file()` usa `Path.resolve()` y verifica que
  `impl_agent/` sea un ancestro real de la ruta resuelta (Property 7).

## Pasos de implementación (alto nivel — el desglose fino va en tasks.md)

1. Crear `impl_agent/models.py` con `ImplRequest`/`ImplResponse`.
2. Escribir `tests/agents/test_impl_agent.py` cubriendo las 6
   Correctness Properties y los criterios de aceptación de `spec.md`
   — **deben fallar antes de implementar**.
3. Crear `impl_agent/prompts.py` con `build_prompt()`.
4. Crear `impl_agent/service.py` con `generate_code()`, `infer_target()`,
   `write_file()`.
5. Crear `impl_agent/router.py` con `POST /generate`.
6. CHECKPOINT: correr `pytest tests/agents/test_impl_agent.py` — todos
   en verde antes de continuar.
7. Validación manual: request real con `spec.md` del `001-spec-agent`
   como input, verificar archivo generado en disco.

## Supuestos — aprobados en Gate 1

1. **Temperatura del LLM**: `0.1`. Aprobado tal como propuesto.
2. **Timeout de Groq**: `30s` (default de `langchain-groq`). Aprobado
   tal como propuesto.
3. **Overwrite restringido a `impl_agent/`**: identificado en el gate
   como necesario por seguridad (evitar sobrescritura automática de
   código de producción existente). Agrega Requisito 3.3 y Property 7.

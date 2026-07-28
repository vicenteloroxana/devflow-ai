# Agente Implementador — Tasks

> Desglose ejecutable de `specs/features/002-impl-agent/plan.md`.
> Requiere Gate 1 aprobado antes de tocar código de producción.
> Tareas `[P]` son paralelizables entre sí (tocan archivos distintos).
> Tests se escriben ANTES que la implementación y DEBEN fallar primero.

## Fase 1 — Setup

- [ ] T1. Verificar que `pytest`, `pytest-asyncio`, `httpx` y
      `hypothesis` estén en `src/agents/requirements.txt`.
      Agregar `hypothesis` si no está.
      _Sin trazabilidad directa — prerequisito de infraestructura de testing._

## Fase 2 — Foundational (bloquea todo lo demás)

- [ ] T2. Crear `impl_agent/models.py` con `ImplRequest` e `ImplResponse`
      (Pydantic), según `spec.md` § Diseño propuesto.
      _Valida: base estructural para Requisitos 1, 2, 3, 4, 5._

- [ ] T3. Escribir `tests/agents/test_impl_agent.py` — **deben fallar
      en este punto** (no existe implementación aún). Cubre:

  - [ ] T3a. Spec válida + `target_file` nuevo → `200` con `code`,
        `file_path`, `spec_path`, `notes`.
        _Valida: Requisito 1.1_

  - [ ] T3b. `target_file` no provisto → ruta inferida desde la spec
        aparece en `file_path`.
        _Valida: Requisito 1.2_

  - [ ] T3c. Archivo existente + `overwrite=False` → HTTP 409, archivo
        sin modificar.
        _Valida: Requisito 3.1, Property 2_

  - [ ] T3d. Archivo existente + `overwrite=True` → HTTP 200, archivo
        reemplazado.
        _Valida: Requisito 3.2_

  - [ ] T3e. `target_file` inexistente → archivo creado incluyendo
        directorios intermedios.
        _Valida: Requisito 3.3, Property 3_

  - [ ] T3f. `spec_path` inexistente → HTTP 404 sin invocar al LLM
        (mock del LLM no debe ser llamado).
        _Valida: Requisito 4.1, Property 5_

  - [ ] T3g. LLM lanza excepción → HTTP 502, nada escrito a disco.
        _Valida: Requisito 4.2, Property 6_

  - [ ] T3h. LLM retorna respuesta sin bloque de código → HTTP 502,
        nada escrito a disco.
        _Valida: Requisito 4.3, Property 6_

  - [ ] T3i. `ImplResponse.spec_path` es igual a `ImplRequest.spec_path`
        en cualquier respuesta exitosa.
        _Valida: Requisito 5.1, Property 4_

  - [ ] T3j. Cadena de llamadas es `async` (verificar con `inspect`).
        _Valida: Requisito 3.3_

  - [ ] T3k. Ninguna API key hardcodeada (grep estático del código fuente).
        _Valida: Requisito 3.4_

  - [ ] T3l. **Property-based tests con `hypothesis`**:
        - `@given(spec_path=st.text())` → spec inexistente siempre → 404
          sin llamar al LLM.
          _Valida: Property 5_
        - `@given(overwrite=st.just(False))` con archivo existente
          → siempre → 409, contenido original intacto.
          _Valida: Property 2_
        - `@given(code=st.text(min_size=1))` → contenido escrito en disco
          es exactamente igual a `ImplResponse.code`.
          _Valida: Property 3_

## Fase 3 — Implementación [P]

- [ ] T4. Crear `impl_agent/prompts.py` con `build_prompt()`.
      Incluye convenciones del `CLAUDE.md` inyectadas como texto fijo.
      _Valida: Requisito 2.1_

- [ ] T5. Crear `impl_agent/service.py`:
      - `infer_target(spec_content: str) -> str` — extrae ruta de destino
        desde la spec; si no encuentra, usa ruta genérica con timestamp
        y agrega observación a `notes`.
        _Valida: Requisito 1.2_
      - `write_file(path: str, content: str, overwrite: bool) -> None`
        — verifica existencia, crea directorios intermedios, escribe.
        `HTTPException(409)` si existe y `overwrite=False`.
        _Valida: Requisitos 3.1, 3.2, 3.3 — Properties 2, 3_
      - `generate_code(request: ImplRequest) -> ImplResponse` — orquesta
        lectura → inferencia → prompt → Groq → extracción → escritura.
        `HTTPException(404)` si `spec_path` no existe.
        `HTTPException(502)` si Groq falla o no hay bloque de código.
        _Valida: Requisitos 1.1, 4.1, 4.2, 4.3 — Properties 1, 4, 5, 6_

- [ ] **CHECKPOINT — correr `pytest tests/agents/test_impl_agent.py`.**
      Todos los tests de T3 (incluyendo property-based) deben pasar en
      verde antes de continuar.

- [ ] T6. Crear `impl_agent/router.py` con `POST /generate` que delega
      a `service.generate_code()`. Sin lógica de negocio en el router.
      _Valida: Requisito 3.3 (async), Requisito 1.1_

## Fase 4 — Polish

- [ ] T7. Revisar que todas las funciones nuevas tengan type hints
      completos y docstrings en español (regla del `CLAUDE.md`).
      _Valida: Requisito 2.3_

- [ ] T8. Validación manual: levantar `docker-compose up`, hacer un
      `POST` real a `http://localhost:8000/api/agents/impl/generate`
      usando `specs/features/001-spec-agent/spec.md` como `spec_path`,
      confirmar que el archivo aparece en disco con código válido.

## Dependencias entre tareas

```
T1 ─┐
T2 ─┼─→ T3 (tests, deben fallar) ─→ T4 [P] ─┐
    │                                T5 [P] ─┼─→ CHECKPOINT ─→ T6 ─→ T7 ─→ T8
    └────────────────────────────────────────┘
```

T4 y T5 pueden desarrollarse en paralelo (no dependen entre sí).
T6 depende de T4 y T5 porque el router los importa.
El CHECKPOINT debe estar en verde antes de T6.

## Definición de "hecho" para esta fase

- Todos los tests de `test_impl_agent.py` pasan, incluyendo los
  property-based tests con `hypothesis`.
- La validación manual (T8) confirma un archivo real generado en disco
  vía request HTTP contra el contenedor Docker.
- No quedan `TODO`/`FIXME` en el código nuevo.
- Todos los supuestos de `plan.md` están resueltos en Gate 1.
- Continúa con Gate 2 (revisión de seguridad y correctitud del código).

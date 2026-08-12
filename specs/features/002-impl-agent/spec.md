# Agente Implementador — Especificación Técnica

> Generado a partir de `specs/features/002-impl-agent/briefing.md`.
> `plan.md` y `tasks.md` generados. Gate 1 (revisión humana) aprobado —
> ver "Supuestos" al final para las decisiones tomadas.

## Glosario

- **Spec aprobada**: archivo `spec.md` que ya pasó el Gate 1 del proceso
  definido en `specs/constitution/workflow.md`. El Implementador solo
  acepta specs aprobadas como input.
- **Archivo generado**: el único archivo de código que el agente produce
  por request. Un request = un archivo.
- **`notes`**: lista de observaciones explícitas del agente sobre la
  implementación (supuestos hechos, partes de la spec que no pudo
  resolver completamente). Equivalente a `assumptions` del Spec Agent.
- **Sobrescritura**: reemplazar un archivo ya existente en disco con el
  contenido generado. Requiere señal explícita del caller.
- **Inferencia de ruta**: cuando `target_file` no se provee, el agente
  deduce la ruta del archivo de destino a partir de la sección
  "Contexto técnico" / "Diseño propuesto" de la spec leída.

## Objetivo

Construir un agente (`impl_agent`) que reciba la ruta a una spec técnica
ya aprobada y genere el contenido de un único archivo de código que la
implementa, respetando las convenciones del `CLAUDE.md`. Es el segundo
eslabón del flujo de DevFlow AI, convirtiendo specs estructuradas en
código verificable.

## Alcance

### Incluye
- Endpoint HTTP `POST /api/agents/impl/generate` que recibe `spec_path`
  y opcionalmente `target_file`, y devuelve el código generado.
- Lectura del archivo `spec.md` desde el filesystem (no recibe markdown
  en el body).
- Inferencia de `target_file` desde la spec cuando no se provee.
- Escritura del archivo generado a disco con comportamiento seguro ante
  sobrescritura (ver Requisito 3).
- Módulo de prompt parametrizado (`impl_agent/prompts.py`) con las
  convenciones del `CLAUDE.md` inyectadas.
- Observaciones explícitas del agente en `notes` cuando la spec es
  ambigua o incompleta.

### No incluye
- Generación de múltiples archivos por request — alcance acotado a
  uno por llamada.
- Validación de que el código generado compila o pasa tests — eso es
  responsabilidad del Agente Eval (fuera de alcance).
- Integración con el Agente Orquestador — se construye y valida de
  forma aislada.
- Autenticación/autorización del endpoint.
- Persistencia en base de datos (solo filesystem, igual que el Spec
  Agent).

## Contexto técnico

- **Ubicación**: `src/agents/impl_agent/`, expuesto vía FastAPI desde
  `src/agents/main.py` en `/api/agents/impl`.
- **Dependencias**: `fastapi`, `pydantic`, `langchain-groq`,
  `python-dotenv` — ya instaladas en `src/agents/requirements.txt`.
- **Configuración**: `shared/config.py` (`Settings`) para leer
  `GROQ_API_KEY`, `LLM_MODEL`, `LLM_TEMPERATURE` desde variables de
  entorno.
- **Patrón de referencia**: `spec_agent/` — misma estructura de módulos
  (`models.py`, `prompts.py`, `service.py`, `router.py`).
- **Encaja en el flujo**: es el paso 2 del workflow descrito en
  `specs/constitution/mission.md` (Spec Agent → **Implementador** →
  Revisor → Eval → PR).

## Diseño propuesto

### Modelo de datos (Pydantic)
- `ImplRequest`:
  - `spec_path: str` — ruta relativa a la spec aprobada (obligatorio)
  - `target_file: str | None` — ruta de destino sugerida (opcional)
  - `overwrite: bool = False` — permite sobrescribir archivo existente
- `ImplResponse`:
  - `code: str` — contenido completo del archivo generado
  - `file_path: str` — ruta donde se escribió el archivo
  - `spec_path: str` — ruta de la spec de origen (trazabilidad)
  - `notes: list[str]` — observaciones del agente

### Flujo del endpoint
1. Recibe y valida `ImplRequest`.
2. Lee el archivo `spec_path` del filesystem.
3. Determina `target_file`: usa el provisto o lo infiere de la spec.
4. Verifica si el archivo de destino ya existe:
   - Si existe y `overwrite=False` → retorna error 409.
   - Si existe y `overwrite=True`:
     - Si `target_file` está dentro de `src/agents/impl_agent/` → procede.
     - Si `target_file` está fuera de `src/agents/impl_agent/` → retorna
       error 403, aunque `overwrite=True` — requiere intervención manual.
5. Arma el prompt con `impl_agent/prompts.py`, inyectando la spec
   completa y las convenciones del `CLAUDE.md`.
6. Invoca a Groq (`llama-3.3-70b-versatile`, temperatura `0.1`,
   timeout `30s`) vía `langchain-groq`, de forma asíncrona.
7. Extrae el bloque de código de la respuesta del LLM.
8. Escribe el archivo en `target_file`.
9. Devuelve `ImplResponse`.

### Temperatura y timeout del LLM
Temperatura `0.1` — más determinismo que specs en prosa (0.3 del
Spec Agent) porque el código requiere sintaxis exacta. Timeout `30s`,
default de `langchain-groq`. Ambos aprobados en Gate 1.

## Requirements

### Requisito 1: Generación de código desde spec

**Historia:** Como agente orquestador quiero enviar una spec aprobada
al Implementador para obtener código generado que la implemente,
sin tener que escribirlo manualmente.

#### Criterios de aceptación

1. CUANDO `POST /api/agents/impl/generate` recibe un `spec_path` válido
   que apunta a un archivo existente ENTONCES el sistema DEBERÁ leer
   ese archivo, construir el prompt, invocar a Groq y retornar `200`
   con `code`, `file_path`, `spec_path` y `notes`.

2. CUANDO `target_file` no se provee en el request ENTONCES el sistema
   DEBERÁ inferir la ruta de destino a partir de las secciones
   "Contexto técnico" o "Diseño propuesto" de la spec leída, e incluir
   la ruta inferida en `file_path` de la respuesta.

3. CUANDO `target_file` se provee explícitamente ENTONCES el sistema
   DEBERÁ usar esa ruta como destino, ignorando cualquier inferencia.

4. El sistema DEBERÁ incluir en `notes` cualquier supuesto hecho al
   interpretar la spec, en lugar de inventar silenciosamente.

### Requisito 2: Conformidad con convenciones del CLAUDE.md

**Historia:** Como desarrollador quiero que el código generado respete
las convenciones del proyecto para no tener que corregirlo manualmente
antes de hacer commit.

#### Criterios de aceptación

1. El sistema DEBERÁ inyectar en el prompt las reglas relevantes del
   `CLAUDE.md` (type hints, Pydantic, async/await, docstrings en
   español) para que el LLM las aplique en el código generado.

2. CUANDO el código generado contiene funciones de negocio ENTONCES el
   sistema DEBERÁ verificar que el LLM haya incluido docstrings en
   español; si no los incluyó, DEBERÁ agregarlo en `notes` como
   observación pendiente de revisión humana.

3. El sistema DEBERÁ usar `async def` en el endpoint y en toda la
   cadena de llamadas internas — nunca `def` síncrono en FastAPI.

### Requisito 3: Comportamiento seguro ante sobrescritura

**Historia:** Como desarrollador quiero que el agente no sobrescriba
código existente accidentalmente para evitar pérdida de trabajo.

#### Criterios de aceptación

1. CUANDO `target_file` ya existe en disco y `overwrite=False` (default)
   ENTONCES el sistema DEBERÁ retornar HTTP 409 con un mensaje que
   indique la ruta del archivo existente, sin modificar el archivo.

2. CUANDO `target_file` ya existe en disco, `overwrite=True`, Y
   `target_file` está dentro de `src/agents/impl_agent/` ENTONCES el
   sistema DEBERÁ sobrescribir el archivo y retornar `200`.

3. CUANDO `target_file` ya existe en disco, `overwrite=True`, Y
   `target_file` está fuera de `src/agents/impl_agent/` ENTONCES el
   sistema DEBERÁ retornar HTTP 403 sin modificar el archivo — el
   overwrite automático queda limitado a la carpeta propia del agente;
   sobrescribir código de otras partes del repo requiere intervención
   manual (regla de "ambigüedad — preguntar, nunca asumir" del
   `CLAUDE.md`, aplicada a acciones difíciles de revertir).

4. CUANDO `target_file` no existe ENTONCES el sistema DEBERÁ crear el
   archivo (incluyendo directorios intermedios si no existen) y
   retornar `200`, sin importar si la ruta está dentro o fuera de
   `impl_agent/`.

### Requisito 4: Resiliencia ante errores del LLM y el filesystem

**Historia:** Como sistema orquestador quiero que los errores del
Implementador sean predecibles y no causen crashes para poder
manejarlos correctamente.

#### Criterios de aceptación

1. SI `spec_path` no existe en el filesystem ENTONCES el sistema
   DEBERÁ retornar HTTP 404 sin invocar al LLM.

2. SI la API de Groq retorna error o no responde en el tiempo límite
   ENTONCES el sistema DEBERÁ retornar HTTP 502 sin reintentos
   (`[NEEDS CLARIFICATION: timeout propuesto 30s, igual que Groq
   por defecto; a confirmar en gate]`).

3. SI la respuesta del LLM no contiene un bloque de código extraíble
   ENTONCES el sistema DEBERÁ retornar HTTP 502 con mensaje descriptivo,
   sin escribir nada a disco.

4. El sistema DEBERÁ leer `GROQ_API_KEY` exclusivamente desde variables
   de entorno — nunca hardcodeada en el código fuente.

### Requisito 5: Trazabilidad del output

**Historia:** Como desarrollador quiero saber de qué spec proviene cada
archivo generado para poder auditar el proceso de generación.

#### Criterios de aceptación

1. El sistema DEBERÁ incluir en `ImplResponse.spec_path` la ruta exacta
   de la spec usada como input, igual a la recibida en el request.

2. MIENTRAS el archivo generado exista en disco ENTONCES el sistema
   DEBERÁ poder reconstruir qué spec lo originó a partir de los logs
   o de la respuesta original del endpoint.

## Fuera de alcance

- Validación de que el código generado compila, importa sin errores, o
  pasa tests — responsabilidad del Agente Eval.
- Generación de múltiples archivos en un solo request.
- Integración con el Agente Orquestador (se valida este agente de forma
  aislada).
- Autenticación/autorización del endpoint.
- Indexado del código generado en pgvector.
- Diff o versionado entre generaciones del mismo archivo.

## Supuestos — aprobados en Gate 1

1. **Temperatura del LLM**: `0.1`. Aprobado tal como propuesto.
2. **Timeout de Groq**: `30s` (default de `langchain-groq`). Aprobado
   tal como propuesto.
3. **Overwrite restringido por carpeta** (no era `[NEEDS
   CLARIFICATION]` en la spec original, pero se identificó como punto
   crítico de seguridad en el gate): `overwrite=True` solo tiene efecto
   si `target_file` está dentro de `src/agents/impl_agent/`. Fuera de
   esa carpeta, retorna `403` aunque el flag esté en `True` —
   coherente con la regla del `CLAUDE.md` de preguntar antes de
   acciones difíciles de revertir. Ver Requisito 3.3.

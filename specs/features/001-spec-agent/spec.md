# Spec Agent — Especificación Técnica

> Generado a partir de `specs/features/001-spec-agent/briefing.md`.
> Formato actualizado al estándar definido en `specs/constitution/workflow.md`
> (EARS + Glosario + Requirements estructurados). Implementación ya completada
> y aprobada en Gate 2.

## Glosario

- **Requerimiento**: texto libre en lenguaje natural escrito por un humano
  que describe una necesidad de software. Input del Spec Agent.
- **Spec generada**: documento Markdown estructurado con 6 secciones fijas
  que el agente produce como output a partir del requerimiento.
- **Supuesto**: decisión de diseño que el agente toma ante información
  ambigua o ausente, marcada explícitamente con el prefijo `[SUPUESTO]`
  en la spec generada y expuesta en el campo `assumptions` de la respuesta.
- **Temperatura 0.3**: parámetro del LLM que produce output
  semi-determinista — suficientemente creativo para interpretar texto libre,
  suficientemente estable para evals con PromptFoo.
- **PromptFoo**: herramienta de evaluación de prompts que verifica que la
  misma entrada produzca estructuralmente el mismo output entre corridas.

## Objetivo
Construir un agente (`spec_agent`) que reciba un requerimiento de
software en lenguaje natural y devuelva una especificación técnica
estructurada en Markdown, consistente en formato con
`specs/constitution/mission.md`, apta para ser consumida como input por
el Agente Implementador.

El problema que resuelve: hoy no existe un paso automatizado que
transforme "lo que el usuario pidió" en "lo que hay que construir,
estructurado" — ese paso manual es el cuello de botella que DevFlow AI
busca eliminar en el primer eslabón del flujo.

## Alcance

### Incluye
- Un endpoint HTTP `POST /api/agents/spec/generate` que recibe un
  requerimiento y devuelve la spec generada.
- Un módulo de prompt parametrizado (`spec_agent/prompts.py`) que
  arma el prompt enviado a Groq a partir del input del usuario.
- Validación de input/output con Pydantic.
- Manejo explícito de requerimientos ambiguos: la spec generada debe
  señalar supuestos, nunca inventar silenciosamente.
- Persistencia del resultado como archivo en `specs/` (ver sección
  "Diseño propuesto" para el mecanismo de nombrado).

### No incluye
- No incluye la integración con el Agente Orquestador (invocación
  encadenada) — se construye y valida este agente de forma aislada.
- No incluye autenticación/autorización del endpoint — se asume acceso
  interno en esta fase.
- No incluye persistencia en base de datos (Postgres/pgvector) — el
  output se guarda como archivo, no como registro. `[NEEDS CLARIFICATION:
  el briefing no aclara si a futuro la spec debe indexarse en
  pgvector para búsqueda semántica; se asume que no, para v1]`.

## Contexto técnico
- **Ubicación**: `src/agents/spec_agent/`, expuesto vía FastAPI desde
  `src/agents/main.py`, que ya monta el router en
  `/api/agents/spec` (ver `spec_agent/router.py`, existente desde la
  Fase 1 como placeholder de health check).
- **Dependencias del proyecto**: `fastapi`, `pydantic`,
  `langchain-groq`, `python-dotenv` — ya instaladas en
  `src/agents/requirements.txt`.
- **Configuración**: usa `shared/config.py` (`Settings`, ya existente)
  para leer `GROQ_API_KEY`, `LLM_MODEL`, `LLM_TEMPERATURE` desde
  variables de entorno — no hardcodear ninguna.
- **Encaja en el flujo mayor** descrito en `specs/constitution/mission.md`:
  es el primer paso de un workflow que continúa con Implementador →
  Revisor → Eval → PR (fuera de alcance de esta spec).

## Diseño propuesto

### Modelo de datos (Pydantic)
- `SpecRequest`:
  - `requirement: str` (obligatorio, texto libre)
  - `context: str | None`
  - `priority: Literal["baja", "media", "alta"] | None`
  - `area: str | None`
- `SpecResponse`:
  - `spec_markdown: str` — el documento generado completo
  - `file_path: str` — ruta relativa donde se persistió el archivo
  - `assumptions: list[str]` — supuestos explícitos hechos por el
    agente al interpretar el requerimiento

### Flujo del endpoint
1. Recibe y valida `SpecRequest`.
2. Arma el prompt con `spec_agent/prompts.py`, inyectando el
   requerimiento y los campos opcionales presentes.
3. Invoca a Groq (`llama-3.3-70b-versatile`, temperatura 0.3) vía
   `langchain-groq`, de forma asíncrona.
4. Parsea la respuesta del LLM a las 6 secciones estandarizadas
   (Objetivo, Alcance, Contexto técnico, Diseño propuesto, Criterios
   de aceptación, Fuera de alcance).
5. Genera el nombre de archivo siguiendo la convención
   `specs/0N-nombre-descriptivo.md`. `[NEEDS CLARIFICATION: el
   briefing no define cómo se calcula el número N ni el
   nombre-descriptivo — se asume: N = siguiente número disponible en
   `specs/`, nombre-descriptivo derivado de un slug del campo
   `area` + primeras palabras del requerimiento; a confirmar en
   revisión]`.
6. Escribe el archivo en `specs/`.
7. Devuelve `SpecResponse` con el markdown, la ruta, y los supuestos
   detectados.

### Prompt (diseño, no implementación)
- Vive en `spec_agent/prompts.py` como función que recibe
  `SpecRequest` y devuelve el string del prompt — nunca inline en el
  router.
- Instruye explícitamente al LLM a:
  - No inventar detalles de arquitectura fuera de lo provisto en
    `CLAUDE.md` / `specs/constitution/mission.md` (se le pasan como
    contexto en el prompt).
  - Marcar supuestos con un formato reconocible (para poder
    extraerlos y poblar `assumptions` en la respuesta).
  - Producir las 6 secciones en el orden y nombres exactos definidos
    en el briefing.

## Requirements

### Requisito 1: Generación de spec estructurada desde requerimiento

**Historia:** Como agente orquestador quiero enviar un requerimiento en
lenguaje natural al Spec Agent para obtener una spec técnica estructurada
lista para ser consumida por el Agente Implementador.

#### Criterios de aceptación

1. CUANDO `POST /api/agents/spec/generate` recibe un requerimiento claro
   y completo ENTONCES el sistema DEBERÁ retornar `200` con las 6
   secciones presentes y no vacías en `spec_markdown`.

2. CUANDO el requerimiento es ambiguo (ej. no menciona en qué capa del
   sistema aplica) ENTONCES el sistema DEBERÁ incluir al menos un ítem
   en `assumptions` y reflejarlo en la sección correspondiente de la
   spec con el prefijo `[SUPUESTO]`, en lugar de inventar silenciosamente.

3. El sistema DEBERÁ producir las 6 secciones en el orden y con los
   nombres exactos definidos en el briefing: Objetivo, Alcance, Contexto
   técnico, Diseño propuesto, Criterios de aceptación, Fuera de alcance.

### Requisito 2: Persistencia del resultado

**Historia:** Como desarrollador quiero que cada spec generada se
guarde automáticamente en disco para poder consultarla y usarla como
input del Implementador sin pasos manuales adicionales.

#### Criterios de aceptación

1. CUANDO el endpoint genera una spec exitosamente ENTONCES el sistema
   DEBERÁ persistir el archivo en `specs/` con nombre único siguiendo
   la convención `specs/0N-{area-o-generico}-{slug-requerimiento}.md`.

2. El sistema DEBERÁ garantizar que cada archivo generado tenga un
   nombre único — nunca sobrescribir una spec existente.

3. CUANDO el archivo se persiste ENTONCES el sistema DEBERÁ retornar
   en `file_path` la ruta relativa donde quedó guardado.

### Requisito 3: Asincronía y conformidad técnica

**Historia:** Como operador del sistema quiero que el Spec Agent no
bloquee el event loop de FastAPI para que múltiples requests puedan
procesarse concurrentemente.

#### Criterios de aceptación

1. El sistema DEBERÁ implementar el endpoint y toda la cadena de llamadas
   internas con `async def` — nunca `def` síncrono en FastAPI.

2. El sistema DEBERÁ leer `GROQ_API_KEY` exclusivamente desde `Settings`
   (`shared/config.py`) — nunca hardcodeada en el código fuente.

3. El sistema DEBERÁ mantener el prompt en `spec_agent/prompts.py` como
   función parametrizada — nunca inline en el router o el servicio.

### Requisito 4: Determinismo evaluable y resiliencia ante errores

**Historia:** Como operador de calidad quiero poder evaluar el prompt
con PromptFoo y confiar en que los errores del LLM no causen crashes
para mantener el sistema estable en producción.

#### Criterios de aceptación

1. CUANDO la misma entrada se envía dos veces con temperatura 0.3
   ENTONCES el sistema DEBERÁ producir salidas con las mismas 6
   secciones presentes (estructura equivalente, evaluable con PromptFoo).

2. SI la API de Groq retorna error (timeout, rate limit, respuesta
   malformada) ENTONCES el sistema DEBERÁ retornar HTTP 502 sin
   reintentos y sin crashear el proceso — el retry es responsabilidad
   del Agente Orquestador.

3. SI la respuesta del LLM no contiene alguna de las 6 secciones
   requeridas ENTONCES el sistema DEBERÁ retornar HTTP 502 con mensaje
   descriptivo, sin persistir el archivo parcial.

## Fuera de alcance
- Integración real con el Agente Orquestador (se probará este agente
  de forma aislada vía requests directos al endpoint).
- Autenticación/autorización del endpoint.
- Indexado de specs generadas en pgvector.
- Versionado o diffing de specs (regenerar una spec no actualiza una
  existente, crea una nueva).
- Soporte multi-idioma del requerimiento de entrada (se asume español
  o inglés, sin traducción).

## Supuestos — aprobados en revisión humana (Paso 4)
Estos puntos fueron marcados `[NEEDS CLARIFICATION]` y quedaron
resueltos y aprobados en el gate de revisión humana:

1. **Nombrado de archivo**: `specs/0N-{area-o-generico}-{slug-requerimiento}.md`,
   con N = siguiente número disponible en `specs/`. Aprobado tal como
   propuesto.
2. **Fallo del LLM**: `HTTPException(502)`, sin retry automático — el
   retry es responsabilidad del futuro Agente Orquestador. Aprobado
   tal como propuesto.
3. **Indexado en pgvector**: fuera de alcance en v1. Solo se persiste
   como archivo Markdown. Aprobado tal como propuesto.

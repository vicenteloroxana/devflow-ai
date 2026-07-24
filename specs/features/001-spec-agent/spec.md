# Spec Agent — Especificación Técnica

> Generado a partir de `specs/features/001-spec-agent/briefing.md`.
> Fase 2 del proyecto (SDD) — pendiente de revisión y aprobación humana.

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

## Criterios de aceptación
1. `POST /api/agents/spec/generate` con un requerimiento claro y
   completo devuelve `200` con las 6 secciones presentes y no vacías.
2. Dado un requerimiento ambiguo (ej. sin mencionar en qué capa del
   sistema aplica), la respuesta incluye al menos un ítem en
   `assumptions` y la sección correspondiente de la spec lo refleja.
3. El archivo generado se persiste físicamente en `specs/` con
   nombre único (no sobrescribe specs existentes).
4. El endpoint responde en async — no bloquea el event loop de
   FastAPI (verificable con type hints `async def` en toda la cadena
   de llamada).
5. Ninguna API key aparece hardcodeada — todas se leen desde
   `Settings` (`shared/config.py`).
6. El prompt es determinista lo suficiente para evals con PromptFoo:
   misma entrada + misma temperatura (0.3) → salida estructuralmente
   equivalente (mismas 6 secciones presentes) entre corridas.
7. Errores del LLM (timeout, rate limit, respuesta malformada) no
   crashean el proceso — devuelven un error HTTP claro (`[NEEDS
   CLARIFICATION: el briefing no especifica el código de error ni el
   comportamiento de retry; se asume 502 sin retry automático para
   v1, ya que el retry es responsabilidad del Agente Orquestador según
   specs/constitution/mission.md]`).

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

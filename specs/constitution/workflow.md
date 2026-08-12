# Proceso SDD — cómo se construye cada feature

> Este documento define el proceso obligatorio para construir cualquier
> funcionalidad nueva en este proyecto. Se aplicó por primera vez para
> el Spec Agent (`specs/features/001-spec-agent/`) y debe repetirse
> igual para cada feature siguiente.

## Regla general
Ninguna funcionalidad nueva se implementa en código sin pasar antes
por sus 4 documentos de diseño y sin dos aprobaciones humanas
explícitas (gates). El código llega último, no primero.

## Estructura de carpetas
```
specs/
├── constitution/          ← reglas de todo el sistema (una sola vez)
│   ├── mission.md          ← qué construye el sistema y para quién
│   └── workflow.md          ← este archivo
└── features/
    └── 00N-nombre-feature/   ← una carpeta por funcionalidad, numerada
        ├── briefing.md
        ├── spec.md
        ├── plan.md
        └── tasks.md
```

El número `00N` es correlativo y no se reutiliza. El nombre de la
carpeta es un slug corto de la feature (ej. `001-spec-agent`).

## Los 4 artefactos, en orden

1. **`briefing.md`** — el pedido en lenguaje natural, expandido con
   input/output esperado, restricciones técnicas y contexto del
   proyecto. Lo escribe un humano (con ayuda de Claude si hace falta
   estructurar la conversación).

2. **`spec.md`** — Claude convierte el briefing en una especificación
   formal. Cualquier ambigüedad se marca explícitamente con el prefijo
   `[NEEDS CLARIFICATION]` en vez de resolverse en silencio.

   **Secciones obligatorias (en este orden):**
   - **Glosario** — términos del dominio con definición precisa.
     Evita ambigüedad en los criterios de aceptación.
   - **Objetivo** — qué problema resuelve. 2-3 líneas máximo.
   - **Alcance** — Incluye / No incluye.
   - **Contexto técnico** — dónde encaja en la arquitectura.
   - **Diseño propuesto** — approach técnico a alto nivel (sin código).
   - **Requirements** — uno por cada área funcional distinguible.
     Cada requisito tiene:
     - *Historia de usuario*: `Como [rol] quiero [acción] para [valor]`
     - *Criterios de aceptación* en sintaxis **EARS**:
       - `CUANDO [evento] ENTONCES el sistema DEBERÁ [comportamiento]`
       - `MIENTRAS [estado] el sistema DEBERÁ [comportamiento]`
       - `SI [condición no deseada] ENTONCES el sistema DEBERÁ [respuesta]`
       - `El sistema DEBERÁ [comportamiento permanente]` (ubiquitous)
   - **Fuera de alcance**
   - **Supuestos** — `[NEEDS CLARIFICATION]` resueltos en el gate.

3. **`plan.md`** — Claude traduce la spec en decisiones técnicas
   concretas: qué archivos se crean, qué responsabilidad tiene cada
   uno, un chequeo explícito contra las reglas de `CLAUDE.md`
   ("Constitution Check"), y los riesgos conocidos con su mitigación.

   **Sección obligatoria adicional: Correctness Properties**
   Cada property tiene la forma:
   ```
   ### Property N: [Nombre descriptivo]
   *Para cualquier* [sujeto], cuando [condición],
   el sistema [garantía verificable y testeable].
   **Validates: Requisito X.Y**
   ```
   Las Correctness Properties son el puente entre los criterios de
   aceptación (legibles por humanos) y los property-based tests
   (verificables por máquina con `hypothesis` en Python / `FsCheck`
   en .NET). Deben escribirse antes de las tareas de testing.

4. **`tasks.md`** — Claude desglosa el plan en tareas atómicas y
   ordenadas por dependencia (Setup → Foundational → Implementación →
   Polish). Los tests se escriben antes que el código que los hace
   pasar, y deben fallar primero.

   Cada tarea de test referencia explícitamente:
   `_Valida: Requisito X.Y, Property N_`

## Los 2 gates humanos (obligatorios, no opcionales)

**Gate 1 — después de `tasks.md`, antes de tocar código.**
Se revisan los 4 documentos juntos. Cualquier `[NEEDS CLARIFICATION]`
debe resolverse explícitamente acá — queda registrado en el propio
`spec.md`/`plan.md` como "aprobado en revisión humana". Sin esta
aprobación, Claude Code no escribe ni una línea de código de
producción.

**Gate 2 — después de implementar, antes de dar la feature por
terminada.**
Revisión de seguridad y correctitud sobre el código ya escrito
(hallazgos confirmados vs. descartados, con justificación). En el
Spec Agent este gate encontró y corrigió 2 bugs reales antes de
seguir.

## Cuándo corren los tests — regla explícita

El flujo distingue dos tipos de tests con comportamientos distintos:

### Tests unitarios (pytest con casos fijos)

| Momento | Estado esperado | Por qué |
|---|---|---|
| Se escriben en Fase Foundational, antes de implementar | 🔴 **Deben fallar** | Confirma que el test detecta ausencia de implementación. Un test que pasa sin código no prueba nada — es documentación, no test. |
| CHECKPOINT (después de implementar) | 🟢 **Deben pasar** | Confirma que la implementación cumple los criterios de aceptación. |
| Antes del PR y en CI | 🟢 **Deben pasar** | Regresión — ningún cambio futuro rompe lo que ya funcionaba. |

### Property-based tests (hypothesis en Python / FsCheck en .NET)

| Momento | Estado | Por qué |
|---|---|---|
| Se *escriben* en Fase Foundational (junto a los unitarios) | — No se ejecutan aún | Sin implementación, `hypothesis` genera contraejemplos aleatorios que producen ruido, no información útil. |
| CHECKPOINT (después de implementar) | 🟢 **Deben pasar** | `hypothesis` genera 100+ inputs aleatorios para intentar romper cada Correctness Property. |
| Antes del PR y en CI | 🟢 **Deben pasar** | Mayor cobertura que los unitarios — detectan casos borde que los tests fijos no cubren. |

### Resumen del ciclo completo

```
[Gate 1 aprobado]
      ↓
Escribir tests unitarios      → 🔴 fallan (esperado y positivo)
Escribir property-based tests → no ejecutar aún
      ↓
Implementar código
      ↓
[CHECKPOINT]
Tests unitarios      → 🟢 deben pasar
Property-based tests → 🟢 deben pasar (hypothesis genera casos aleatorios)
      ↓
[Gate 2 aprobado]
      ↓
Correr evals del prompt (si el agente usa LLM)
Verificar endpoint manualmente
      ↓
Abrir PR → CI verde (ambos tipos de tests) → merge
```

## Después de los gates
Con ambos gates pasados: correr tests → correr evals del prompt (si
el agente usa LLM) → verificar el endpoint contra el servicio real →
abrir PR → CI verde → merge → **actualizar el backlog**.

### Actualizar el backlog (último paso, no opcional)
Al mergear el PR de una feature, marcar su línea en
[`../features/backlog.md`](../features/backlog.md) como `[x]` y linkear
la carpeta de la feature:

```
- [x] 002 — Agente Implementador → [002-impl-agent](002-impl-agent/)
```

El backlog es la única vista de "qué está construido y qué falta" del
proyecto. Si no se marca, queda desincronizado y deja de ser confiable
para decidir qué sigue.

Este paso es manual por ahora. El CI valida que no se olvide: un PR que
toca `specs/features/00N-*/` sin actualizar `backlog.md` falla el check
`backlog-sync` (ver `.github/workflows/backlog-check.yml`).

## Por qué existe este documento
Sin este archivo, el proceso de 10 pasos solo vivía en el historial de
una conversación puntual con Claude — no era reproducible ni
verificable por otra persona (o por otra sesión de Claude Code) que
retomara el proyecto. Este archivo es la fuente de verdad del "cómo se
construye acá", igual que `mission.md` es la fuente de verdad del
"qué se construye".

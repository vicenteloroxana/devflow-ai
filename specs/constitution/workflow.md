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
   formal con 6 secciones fijas: Objetivo, Alcance, Contexto técnico,
   Diseño propuesto, Criterios de aceptación, Fuera de alcance.
   Cualquier ambigüedad se marca explícitamente con el prefijo
   `[NEEDS CLARIFICATION]` en vez de resolverse en silencio.

3. **`plan.md`** — Claude traduce la spec en decisiones técnicas
   concretas: qué archivos se crean, qué responsabilidad tiene cada
   uno, un chequeo explícito contra las reglas de `CLAUDE.md`
   ("Constitution Check"), y los riesgos conocidos con su mitigación.

4. **`tasks.md`** — Claude desglosa el plan en tareas atómicas y
   ordenadas por dependencia (Setup → Foundational → Implementación →
   Polish). Los tests se escriben antes que el código que los hace
   pasar, y deben fallar primero.

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

## Después de los gates
Con ambos gates pasados: correr tests → correr evals del prompt (si
el agente usa LLM) → verificar el endpoint contra el servicio real →
abrir PR → CI verde → merge.

## Por qué existe este documento
Sin este archivo, el proceso de 10 pasos solo vivía en el historial de
una conversación puntual con Claude — no era reproducible ni
verificable por otra persona (o por otra sesión de Claude Code) que
retomara el proyecto. Este archivo es la fuente de verdad del "cómo se
construye acá", igual que `mission.md` es la fuente de verdad del
"qué se construye".

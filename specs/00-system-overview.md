# DevFlow AI — System Overview Spec

## Problema que resuelve
Los equipos de desarrollo no tienen un sistema que orcheste el ciclo
completo: requerimiento → spec → código → review → PR. Se hace todo
manualmente, tardando horas por feature simple.

## Qué hace el sistema
1. Recibe un requerimiento en lenguaje natural via API REST
2. Agente Spec genera la especificación técnica en markdown
3. Agente Implementador genera el código contra la spec
4. Agente Revisor audita el código con criterio de seguridad y calidad
5. Agente Eval valida que el código cumple los criterios de la spec
6. Si los evals pasan, el sistema abre un PR en GitHub automáticamente

## Qué NO hace (fuera de scope v1)
- No hace fine-tuning de modelos
- No genera frontend
- No gestiona ambientes de deploy (solo genera el código y el PR)
- No reemplaza la revisión humana — la complementa

## Agentes del sistema

### Agente Orquestador (Python)
- Coordina el flujo entre todos los subagentes
- Decide si reintentar o escalar a humano
- Máximo 3 reintentos por workflow
- Si falla → notifica via webhook

### Agente Spec (Python + LLM)
- Input: requerimiento en lenguaje natural
- Output: spec técnica en markdown con secciones estandarizadas
- Usa: Groq llama-3.3-70b-versatile
- Temperatura: 0.3 (output semi-determinista)

### Agente Implementador (Python + LLM)
- Input: spec técnica aprobada
- Output: archivos de código generados
- Usa: Groq llama-3.3-70b-versatile
- Respeta las convenciones del CLAUDE.md

### Agente Revisor (Python + LLM)
- Input: código generado
- Output: lista de issues con severidad (critical/warning/info)
- Lee el código "en frío" — sin el contexto del implementador
- Patrón: Maker/Checker

### Agente Eval (Python + PromptFoo)
- Input: spec + código generado
- Output: pass/fail por cada criterio de éxito de la spec
- Si hay un criterio critical en fail → no abre PR

## Endpoints principales (ASP.NET Core 9 API)
- POST /api/workflows          → inicia un workflow nuevo
- GET  /api/workflows/{id}     → estado del workflow
- GET  /api/workflows/{id}/spec → spec generada
- GET  /api/workflows/{id}/review → resultado del review
- POST /api/workflows/{id}/approve → aprobación humana → abre PR

## Criterios de éxito del sistema completo
- Un workflow de punta a punta completa en menos de 3 minutos
- El Agente Revisor detecta N+1 queries en código de ejemplo
- El CI/CD corre evals automáticos en cada PR del proyecto mismo
- La infraestructura se levanta completa con terraform apply
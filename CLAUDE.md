# DevFlow AI — Agent Orchestration System

## Lo que hace este proyecto
Sistema multi-agente que automatiza el ciclo de desarrollo:
recibe un requerimiento → genera spec → implementa código →
revisa con criterio técnico → abre PR en GitHub.

## Stack
- API principal: ASP.NET Core 9, C#, Clean Architecture, CQRS + MediatR
- Agentes: Python 3.12 + FastAPI + LangChain / Claude Agent SDK
- Orquestación: Microsoft Agent Framework (MAF)
- BD: PostgreSQL 16 + pgvector (Docker local, RDS en AWS)
- LLM dev: Groq API (llama-3.3-70b-versatile) — $0
- LLM demo: Anthropic API (claude-haiku-4-5)
- Vector store: pgvector (misma instancia PostgreSQL)
- CI/CD: GitHub Actions
- IaC: Terraform (AWS Lambda + RDS + S3)
- Containerización: Docker + Docker Compose

## Estructura de carpetas — RESPETAR SIEMPRE
devflow-ai/
├── CLAUDE.md
├── .github/workflows/ ← CI/CD pipelines
├── terraform/ ← infraestructura AWS como código
├── docker-compose.yml ← ambiente local completo
├── src/
│ ├── DevFlowAI/ ← solución .NET (Visual Studio)
│ │ ├── DevFlowAI.API/ ← ASP.NET Core 10
│ │ ├── DevFlowAI.Application/
│ │ ├── DevFlowAI.Domain/
│ │ ├── DevFlowAI.Infrastructure/
│ │ └── DevFlowAI.Tests/
│ └── agents/ ← Python FastAPI (VS Code)
│ ├── spec_agent/
│ ├── impl_agent/
│ ├── review_agent/
│ └── eval_agent/
├── specs/ ← specs técnicas del proyecto (SDD)
│ ├── constitution/workflow.md ← PROCESO OBLIGATORIO para crear features nuevas
│ ├── constitution/adr/ ← Architecture Decision Records (histórico, no se editan una vez aceptados)
│ └── features/00N-nombre/ ← briefing.md, spec.md, plan.md, tasks.md por feature
├── docs/ ← documentación de proceso de equipo (convenciones de commits, etc.)
└── tests/
├── DevFlowAI.Tests/ ← xUnit
└── agents/ ← pytest + promptfoo
## Ambigüedad — preguntar, nunca asumir
- Ante un requerimiento ambiguo, incompleto o con más de una
  interpretación razonable: PREGUNTAR antes de actuar. No resolver la
  ambigüedad en silencio eligiendo la interpretación más probable.
- Aplica a todo pedido, no solo a features nuevas: correcciones,
  refactors, comandos, cambios de configuración.
- Preguntar es especialmente obligatorio antes de: borrar o sobrescribir
  archivos, tocar `Domain/Entities/`, `docker-compose.yml` o `terraform/`,
  y cualquier acción difícil de revertir.
- Si el pedido es ambiguo pero hay un default obvio y reversible, se
  puede actuar informando explícitamente el supuesto asumido en la
  respuesta, para que pueda corregirse.
- Esto es distinto de `[NEEDS CLARIFICATION]` y NO lo reemplaza: ese
  marcador se escribe dentro de `spec.md`/`plan.md` y se resuelve
  diferido en el Gate 1. Esta regla es conversacional y se resuelve
  en el momento, antes de seguir.

## Reglas de arquitectura — NUNCA VIOLAR
- Toda funcionalidad nueva SIEMPRE sigue el proceso descrito en
  `specs/constitution/workflow.md` (briefing → spec → plan → tasks →
  gate humano → código). No se escribe código de producción para una
  feature nueva sin haber pasado por esos 4 documentos y el gate.
- Decisiones de arquitectura relevantes se documentan como ADR en
  `specs/constitution/adr/`. Un ADR aceptado no se edita: si la decisión
  cambia, se crea un ADR nuevo que supera al anterior.
- Prompts SIEMPRE en Application/Prompts/ como templates con parámetros
- Llamadas al LLM SIEMPRE en Infrastructure/AI/
- Domain NO referencia Infrastructure ni agents/
- Controllers NO tienen lógica de negocio
- API keys NUNCA en código — siempre desde variables de entorno
- AsNoTracking() en TODOS los queries de solo lectura
- ConfigureAwait(false) en toda la capa Infrastructure

## Convenciones de código C#
- Records para DTOs inmutables
- Nombres completos: customerId no custId, isValid no flg
- Tests: MetodoNombre_Escenario_ResultadoEsperado
- Máximo 20 líneas por método

## Convenciones Python
- Type hints en todas las funciones
- Pydantic para validación de inputs/outputs
- async/await siempre — nunca sync en FastAPI
- Docstrings en español para funciones de negocio

## NO tocar sin preguntar
- Domain/Entities/ — cambios requieren discusión de diseño
- docker-compose.yml — cambios afectan todo el ambiente
- terraform/ — cambios afectan infraestructura real

## Variables de entorno necesarias (ver .env.example)
- GROQ_API_KEY
- ANTHROPIC_API_KEY (solo para demo)
- POSTGRES_CONNECTION_STRING
- GITHUB_TOKEN (para el agente que abre PRs)
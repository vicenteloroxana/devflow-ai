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
└── tests/
├── DevFlowAI.Tests/ ← xUnit
└── agents/ ← pytest + promptfoo
## Reglas de arquitectura — NUNCA VIOLAR
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
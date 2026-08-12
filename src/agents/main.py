# main.py
from fastapi import FastAPI
from spec_agent.router import router as spec_router
from impl_agent.router import router as impl_router

app = FastAPI(
    title="DevFlow AI — Agents API",
    description="Sistema multi-agente para automatización del ciclo de desarrollo",
    version="1.0.0"
)

app.include_router(spec_router, prefix="/api/agents/spec", tags=["Spec Agent"])
app.include_router(impl_router, prefix="/api/agents/impl", tags=["Implementer Agent"])

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "devflow-agents"}
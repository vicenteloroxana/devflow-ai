from fastapi import APIRouter

from impl_agent.models import ImplRequest, ImplResponse
from impl_agent.service import generate_code

router = APIRouter()


@router.get("/health")
async def health():
    """Verifica que el Agente Implementador está disponible."""
    return {"status": "healthy", "agent": "impl_agent"}


@router.post("/generate", response_model=ImplResponse)
async def generate(request: ImplRequest) -> ImplResponse:
    """Genera código a partir de una spec técnica aprobada."""
    return await generate_code(request)

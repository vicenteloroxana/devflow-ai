from fastapi import APIRouter

from spec_agent.models import SpecRequest, SpecResponse
from spec_agent.service import generate_spec

router = APIRouter()


@router.get("/health")
async def health():
    """Verifica que el Spec Agent está disponible."""
    return {"status": "healthy", "agent": "spec_agent"}


@router.post("/generate", response_model=SpecResponse)
async def generate(request: SpecRequest) -> SpecResponse:
    """Genera una spec técnica a partir de un requerimiento en lenguaje natural."""
    return await generate_spec(request)

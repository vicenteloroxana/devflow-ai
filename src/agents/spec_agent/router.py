from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health():
    """Verifica que el Spec Agent está disponible."""
    return {"status": "healthy", "agent": "spec_agent"}

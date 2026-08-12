from pydantic import BaseModel, Field


class ImplRequest(BaseModel):
    """Requerimiento para generar código a partir de una spec aprobada."""

    spec_path: str = Field(..., min_length=1)
    target_file: str | None = None
    overwrite: bool = False


class ImplResponse(BaseModel):
    """Código generado a partir de un ImplRequest."""

    code: str
    file_path: str
    spec_path: str
    notes: list[str] = Field(default_factory=list)

from typing import Literal

from pydantic import BaseModel, Field


class SpecRequest(BaseModel):
    """Requerimiento en lenguaje natural para generar una spec técnica."""

    requirement: str = Field(..., min_length=1)
    context: str | None = None
    priority: Literal["baja", "media", "alta"] | None = None
    area: str | None = None


class SpecResponse(BaseModel):
    """Spec técnica generada a partir de un SpecRequest."""

    spec_markdown: str
    file_path: str
    assumptions: list[str] = Field(default_factory=list)

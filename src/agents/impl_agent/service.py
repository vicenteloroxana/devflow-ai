import re
from pathlib import Path

from fastapi import HTTPException

from shared.config import settings
from impl_agent.models import ImplRequest, ImplResponse
from impl_agent.prompts import build_prompt

TEMPERATURE = 0.1
TIMEOUT_SECONDS = 30

IMPL_AGENT_DIR = Path(__file__).resolve().parent


def _resolver_repo_root() -> Path:
    """Ubica la raíz del repo: 3 niveles arriba de impl_agent/ en el repo
    local (.../src/agents/impl_agent), o el ancestro disponible más alto
    dentro del contenedor (donde solo se monta src/agents/ como /app —
    no hay volumen que exponga la raíz completa del repo todavía)."""
    candidato = IMPL_AGENT_DIR.parents[2] if len(IMPL_AGENT_DIR.parents) > 2 else None
    if candidato is not None and candidato.is_dir():
        return candidato
    return IMPL_AGENT_DIR.parent


REPO_ROOT = _resolver_repo_root()

_CODE_BLOCK_RE = re.compile(r"```(?:python)?\s*\n(.*?)```", re.DOTALL)
_TARGET_HINT_RE = re.compile(r"`([^`\n]+\.py)`")
_SECCION_HEADER_RE = re.compile(r"^##\s*(.+?)\s*$", re.MULTILINE)


async def _call_llm(prompt: str) -> str:
    """Invoca al LLM configurado (Groq) y devuelve el texto de la respuesta."""
    import os

    from langchain_groq import ChatGroq

    os.environ.setdefault("GROQ_API_KEY", settings.groq_api_key)
    llm = ChatGroq(
        model=settings.llm_model,
        temperature=TEMPERATURE,
        timeout=TIMEOUT_SECONDS,
    )
    result = await llm.ainvoke(prompt)
    return result.content


_SECCIONES_PARA_INFERIR = {"Contexto técnico", "Diseño propuesto"}


def infer_target(spec_content: str) -> str | None:
    """Infiere la ruta de destino del código desde la spec.

    Busca un .py entre backticks, pero solo dentro de las secciones
    "Contexto técnico" o "Diseño propuesto" (como define plan.md) —
    ignora menciones de archivos .py en otras secciones (ej. "Fuera de
    alcance" podría nombrar un archivo que explícitamente no hay que tocar).
    """
    partes = _SECCION_HEADER_RE.split(spec_content)
    # re.split con grupo de captura intercala: [previo, titulo1, contenido1, ...]
    for i in range(1, len(partes) - 1, 2):
        titulo, contenido = partes[i], partes[i + 1]
        if titulo in _SECCIONES_PARA_INFERIR:
            match = _TARGET_HINT_RE.search(contenido)
            if match:
                return match.group(1)
    return None


def _extraer_codigo(llm_output: str) -> str | None:
    """Extrae el único bloque de código Python de la respuesta del LLM.

    Si hay cero o más de un bloque, devuelve None — ambigüedad se trata
    como fallo, nunca se adivina cuál es el bloque correcto.
    """
    bloques = _CODE_BLOCK_RE.findall(llm_output)
    if len(bloques) != 1:
        return None
    return bloques[0].strip()


def _es_ancestro(base: Path, path: Path) -> bool:
    """Verifica si `base` es ancestro de `path` (protege contra bypass con '../')."""
    try:
        path.relative_to(base)
        return True
    except ValueError:
        return False


def write_file(path: str, content: str, overwrite: bool) -> None:
    """Escribe el código generado a disco, con reglas seguras ante sobrescritura.

    Toda escritura (exista o no el archivo) debe caer dentro del repo.
    Sobrescribir un archivo ya existente además requiere que esté dentro
    de impl_agent/ — fuera de esa carpeta se considera código de
    producción y requiere intervención manual.
    """
    destino = Path(path).resolve()

    if not _es_ancestro(REPO_ROOT, destino):
        raise HTTPException(
            status_code=403,
            detail=f"{destino} está fuera del repo. No se permite escribir ahí.",
        )

    if destino.exists():
        if not overwrite:
            raise HTTPException(
                status_code=409,
                detail=f"El archivo {destino} ya existe. Use overwrite=true para reemplazarlo.",
            )
        if not _es_ancestro(IMPL_AGENT_DIR, destino):
            raise HTTPException(
                status_code=403,
                detail=(
                    f"{destino} está fuera de src/agents/impl_agent/. "
                    "El overwrite automático solo aplica dentro de esa carpeta; "
                    "sobrescribir código de otras partes del repo requiere "
                    "intervención manual."
                ),
            )

    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(content, encoding="utf-8")


async def generate_code(request: ImplRequest) -> ImplResponse:
    """Genera código a partir de una spec aprobada y lo persiste a disco."""
    spec_file = Path(request.spec_path)
    if not spec_file.is_file():
        raise HTTPException(status_code=404, detail=f"spec_path no existe: {request.spec_path}")

    spec_content = spec_file.read_text(encoding="utf-8")

    notes: list[str] = []
    target_file = request.target_file
    if not target_file:
        target_file = infer_target(spec_content)
        if not target_file:
            raise HTTPException(
                status_code=502,
                detail="No se pudo inferir target_file desde la spec y no fue provisto explícitamente.",
            )
        notes.append(f"target_file inferido automáticamente de la spec: {target_file}")

    prompt = build_prompt(spec_content, request)

    try:
        llm_output = await _call_llm(prompt)
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=502, detail=str(error)) from error

    code = _extraer_codigo(llm_output)
    if code is None:
        raise HTTPException(
            status_code=502,
            detail="La respuesta del LLM no contiene un bloque de código extraíble.",
        )

    write_file(target_file, code, request.overwrite)

    return ImplResponse(
        code=code,
        file_path=target_file,
        spec_path=request.spec_path,
        notes=notes,
    )

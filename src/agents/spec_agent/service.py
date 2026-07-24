import re
from pathlib import Path

from fastapi import HTTPException

from shared.config import settings
from spec_agent.models import SpecRequest, SpecResponse
from spec_agent.prompts import SECCIONES, build_prompt

def _resolver_specs_dir() -> Path:
    """Ubica el directorio specs/: /specs en el contenedor (volumen montado),
    o la carpeta specs/ del repo cuando se corre localmente."""
    ruta_contenedor = Path("/specs")
    if ruta_contenedor.is_dir():
        return ruta_contenedor

    for ancestro in Path(__file__).resolve().parents:
        candidato = ancestro / "specs"
        if candidato.is_dir():
            return candidato

    return Path(__file__).resolve().parents[2] / "specs"


SPECS_DIR = _resolver_specs_dir()

_SECCION_HEADER_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
_SUPUESTO_RE = re.compile(r"\[SUPUESTO\]\s*(.+)")


async def _call_llm(prompt: str) -> str:
    """Invoca al LLM configurado (Groq) y devuelve el texto de la respuesta."""
    import os

    from langchain_groq import ChatGroq

    os.environ.setdefault("GROQ_API_KEY", settings.groq_api_key)
    llm = ChatGroq(
        model=settings.llm_model,
        temperature=settings.llm_temperature,
    )
    result = await llm.ainvoke(prompt)
    return result.content


def _validar_secciones(markdown: str) -> None:
    """Verifica que las 6 secciones estandarizadas estén presentes y con contenido."""
    partes = re.split(_SECCION_HEADER_RE, markdown)
    # re.split con grupo de captura intercala: [texto_previo, titulo1, contenido1, titulo2, contenido2, ...]
    contenido_por_seccion = {
        partes[i]: partes[i + 1].strip() for i in range(1, len(partes) - 1, 2)
    }

    faltantes = [s for s in SECCIONES if s not in contenido_por_seccion]
    if faltantes:
        raise HTTPException(
            status_code=502,
            detail=f"La spec generada no incluye las secciones: {faltantes}",
        )

    vacias = [s for s in SECCIONES if not contenido_por_seccion[s]]
    if vacias:
        raise HTTPException(
            status_code=502,
            detail=f"La spec generada tiene secciones vacías: {vacias}",
        )


def _extraer_supuestos(markdown: str) -> list[str]:
    """Extrae los supuestos marcados con [SUPUESTO] en el markdown generado."""
    return [match.strip() for match in _SUPUESTO_RE.findall(markdown)]


def _siguiente_numero_disponible() -> int:
    """Calcula el siguiente número de feature disponible en specs/features/."""
    features_dir = SPECS_DIR / "features"
    numeros = []
    if features_dir.is_dir():
        for carpeta in features_dir.iterdir():
            match = re.match(r"^(\d+)-", carpeta.name)
            if match:
                numeros.append(int(match.group(1)))
    return max(numeros, default=0) + 1


def _slugify(texto: str) -> str:
    """Convierte un texto libre en un slug apto para nombre de archivo."""
    texto = texto.lower().strip()
    texto = re.sub(r"[^a-z0-9\s-]", "", texto)
    texto = re.sub(r"[\s_]+", "-", texto)
    return texto.strip("-")[:50] or "spec"


def persist_spec(markdown: str, request: SpecRequest) -> str:
    """Persiste la spec generada en specs/features/00N-{slug}/spec.md y
    devuelve la ruta.

    No es seguro ante escrituras concurrentes (dos requests simultáneos
    podrían calcular el mismo número); se detecta la colisión y se
    reintenta con el siguiente número en vez de sobrescribir en silencio.
    """
    features_dir = SPECS_DIR / "features"
    area_o_generico = request.area or "spec-agent-generated"
    slug_requerimiento = _slugify(request.requirement)

    numero = _siguiente_numero_disponible()
    while True:
        nombre_carpeta = f"{numero:03d}-{_slugify(area_o_generico)}-{slug_requerimiento}"
        carpeta_feature = features_dir / nombre_carpeta
        if not carpeta_feature.exists():
            break
        numero += 1

    carpeta_feature.mkdir(parents=True, exist_ok=False)
    ruta = carpeta_feature / "spec.md"
    ruta.write_text(markdown, encoding="utf-8")
    return str(ruta)


async def generate_spec(request: SpecRequest) -> SpecResponse:
    """Genera una spec técnica a partir de un requerimiento en lenguaje natural."""
    prompt = build_prompt(request)

    try:
        markdown = await _call_llm(prompt)
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=502, detail=str(error)) from error

    _validar_secciones(markdown)
    assumptions = _extraer_supuestos(markdown)
    file_path = persist_spec(markdown, request)

    return SpecResponse(
        spec_markdown=markdown,
        file_path=file_path,
        assumptions=assumptions,
    )

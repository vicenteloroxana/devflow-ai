from spec_agent.models import SpecRequest

SECCIONES = [
    "Objetivo",
    "Alcance",
    "Contexto técnico",
    "Diseño propuesto",
    "Criterios de aceptación",
    "Fuera de alcance",
]

CONTEXTO_PROYECTO = """
Contexto del proyecto DevFlow AI:
- Sistema multi-agente que automatiza el ciclo de desarrollo:
  requerimiento -> spec -> código -> review -> PR.
- Stack: ASP.NET Core 9 (API), Python 3.12 + FastAPI (agentes),
  PostgreSQL 16 + pgvector, Terraform (AWS).
- El Spec Agent es el primer paso del flujo: convierte un
  requerimiento en lenguaje natural en una especificación técnica.
"""


def build_prompt(request: SpecRequest) -> str:
    """Arma el prompt enviado al LLM a partir de un SpecRequest."""
    metadata_lines = []
    if request.context:
        metadata_lines.append(f"Contexto adicional: {request.context}")
    if request.priority:
        metadata_lines.append(f"Prioridad: {request.priority}")
    if request.area:
        metadata_lines.append(f"Área del sistema: {request.area}")
    metadata = "\n".join(metadata_lines)

    secciones_fmt = "\n".join(f"## {seccion}" for seccion in SECCIONES)

    return f"""Sos un asistente técnico que convierte requerimientos de \
software en especificaciones técnicas estructuradas.

{CONTEXTO_PROYECTO}

Requerimiento del usuario:
{request.requirement}

{metadata}

Generá una especificación técnica en Markdown con EXACTAMENTE estas \
6 secciones, en este orden y con estos títulos literales:

{secciones_fmt}

Reglas obligatorias:
- No inventes detalles de arquitectura que no estén en el contexto \
del proyecto provisto arriba.
- Si el requerimiento es ambiguo o le falta información (por ejemplo, \
no aclara en qué capa o módulo aplica), marcá el supuesto que hiciste \
con el prefijo literal "[SUPUESTO]" dentro de la sección \
correspondiente.
- No agregues secciones adicionales ni texto fuera de las 6 secciones \
pedidas.
"""

from impl_agent.models import ImplRequest

CONVENCIONES_CLAUDE_MD = """
Convenciones obligatorias del proyecto (CLAUDE.md):
- Type hints en todas las funciones.
- Pydantic para validación de inputs/outputs.
- async/await siempre — nunca funciones síncronas en FastAPI.
- Docstrings en español para funciones de negocio.
- API keys nunca hardcodeadas — siempre desde variables de entorno.
"""


def build_prompt(spec_content: str, request: ImplRequest) -> str:
    """Arma el prompt enviado al LLM para generar código a partir de una spec."""
    target_hint = f"\nArchivo de destino sugerido: {request.target_file}" if request.target_file else ""

    return f"""Sos un asistente técnico que genera código Python a partir \
de una especificación técnica ya aprobada.

{CONVENCIONES_CLAUDE_MD}

Spec técnica:
{spec_content}
{target_hint}

Generá el contenido completo de UN SOLO archivo Python que implemente \
esta spec, siguiendo las convenciones listadas arriba.

Reglas obligatorias:
- Devolvé el código completo dentro de un bloque de código Markdown \
con el lenguaje indicado, por ejemplo:
```python
# código acá
```
- No inventes detalles de arquitectura que no estén en la spec.
- Si la spec es ambigua o insuficiente para completar alguna parte, \
agregá un comentario `# SUPUESTO: ...` en el lugar correspondiente del \
código en vez de inventar silenciosamente.
- No agregues explicación fuera del bloque de código.
"""

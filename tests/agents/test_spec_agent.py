import os
import sys
from pathlib import Path

import pytest
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient

AGENTS_ROOT = Path(__file__).resolve().parents[2] / "src" / "agents"
sys.path.insert(0, str(AGENTS_ROOT))

os.environ.setdefault("GROQ_API_KEY", "test-key")
os.environ.setdefault("POSTGRES_URL", "postgresql://test:test@localhost:5432/test")

from spec_agent.models import SpecRequest  # noqa: E402
from spec_agent import service  # noqa: E402

VALID_LLM_RESPONSE = """## Objetivo
Resolver el problema descrito.

## Alcance
Incluye lo pedido.

## Contexto técnico
Aplica a la capa API.

## Diseño propuesto
Approach a alto nivel.

## Criterios de aceptación
- Criterio 1

## Fuera de alcance
Nada más.
"""

AMBIGUOUS_LLM_RESPONSE = """## Objetivo
Resolver el problema descrito.

## Alcance
Incluye lo pedido.

## Contexto técnico
[SUPUESTO] No se especificó la capa del sistema; se asume API.

## Diseño propuesto
Approach a alto nivel.

## Criterios de aceptación
- Criterio 1

## Fuera de alcance
Nada más.
"""


@pytest.fixture(autouse=True)
def limpiar_specs_generadas(tmp_path, monkeypatch):
    """Redirige la persistencia de specs a un directorio temporal por test."""
    monkeypatch.setattr(service, "SPECS_DIR", tmp_path)
    yield


async def _post_generate(monkeypatch, llm_response=None, llm_side_effect=None):
    if llm_side_effect is not None:
        async def fake_call_llm(prompt: str) -> str:
            raise llm_side_effect

    else:
        async def fake_call_llm(prompt: str) -> str:
            return llm_response

    monkeypatch.setattr(service, "_call_llm", fake_call_llm)

    from main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post(
            "/api/agents/spec/generate",
            json={"requirement": "Necesito un endpoint que liste usuarios"},
        )


@pytest.mark.asyncio
async def test_requerimiento_claro_devuelve_200_con_secciones_completas(monkeypatch):
    response = await _post_generate(monkeypatch, llm_response=VALID_LLM_RESPONSE)

    assert response.status_code == 200
    body = response.json()
    for seccion in [
        "## Objetivo",
        "## Alcance",
        "## Contexto técnico",
        "## Diseño propuesto",
        "## Criterios de aceptación",
        "## Fuera de alcance",
    ]:
        assert seccion in body["spec_markdown"]


@pytest.mark.asyncio
async def test_requerimiento_ambiguo_reporta_supuestos(monkeypatch):
    response = await _post_generate(monkeypatch, llm_response=AMBIGUOUS_LLM_RESPONSE)

    assert response.status_code == 200
    body = response.json()
    assert len(body["assumptions"]) >= 1


@pytest.mark.asyncio
async def test_archivo_se_persiste_con_nombre_unico(monkeypatch, tmp_path):
    monkeypatch.setattr(service, "SPECS_DIR", tmp_path)
    response = await _post_generate(monkeypatch, llm_response=VALID_LLM_RESPONSE)

    body = response.json()
    archivo_generado = Path(body["file_path"])
    assert archivo_generado.exists()

    response_2 = await _post_generate(monkeypatch, llm_response=VALID_LLM_RESPONSE)
    body_2 = response_2.json()
    assert body["file_path"] != body_2["file_path"]


@pytest.mark.asyncio
async def test_endpoint_es_async_no_bloquea_event_loop():
    import inspect

    from spec_agent import router as router_module

    assert inspect.iscoroutinefunction(router_module.generate)
    assert inspect.iscoroutinefunction(service.generate_spec)


def test_no_hay_api_keys_hardcodeadas():
    codigo = (AGENTS_ROOT / "spec_agent" / "service.py").read_text(encoding="utf-8")
    assert "gsk_" not in codigo
    assert "sk-ant-" not in codigo


@pytest.mark.asyncio
async def test_misma_entrada_misma_estructura_de_salida(monkeypatch):
    response_1 = await _post_generate(monkeypatch, llm_response=VALID_LLM_RESPONSE)
    response_2 = await _post_generate(monkeypatch, llm_response=VALID_LLM_RESPONSE)

    secciones_1 = [line for line in response_1.json()["spec_markdown"].splitlines() if line.startswith("## ")]
    secciones_2 = [line for line in response_2.json()["spec_markdown"].splitlines() if line.startswith("## ")]
    assert secciones_1 == secciones_2


@pytest.mark.asyncio
async def test_seccion_vacia_devuelve_502(monkeypatch):
    respuesta_con_seccion_vacia = VALID_LLM_RESPONSE.replace(
        "## Objetivo\nResolver el problema descrito.\n",
        "## Objetivo\n\n",
    )
    response = await _post_generate(monkeypatch, llm_response=respuesta_con_seccion_vacia)

    assert response.status_code == 502


@pytest.mark.asyncio
async def test_fallo_del_llm_devuelve_502_sin_reintentos(monkeypatch):
    llamadas = {"contador": 0}

    async def fake_call_llm(prompt: str) -> str:
        llamadas["contador"] += 1
        raise RuntimeError("Groq no disponible")

    monkeypatch.setattr(service, "_call_llm", fake_call_llm)

    from main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/agents/spec/generate",
            json={"requirement": "Necesito un endpoint que liste usuarios"},
        )

    assert response.status_code == 502
    assert llamadas["contador"] == 1

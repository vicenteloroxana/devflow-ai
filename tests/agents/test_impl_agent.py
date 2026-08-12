import os
import sys
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from httpx import ASGITransport, AsyncClient

AGENTS_ROOT = Path(__file__).resolve().parents[2] / "src" / "agents"
sys.path.insert(0, str(AGENTS_ROOT))

os.environ.setdefault("GROQ_API_KEY", "test-key")
os.environ.setdefault("POSTGRES_URL", "postgresql://test:test@localhost:5432/test")

from impl_agent import service  # noqa: E402

VALID_LLM_RESPONSE = '''Acá está el código:

```python
def hola() -> str:
    """Saluda."""
    return "hola"
```
'''

NO_CODE_LLM_RESPONSE = "No puedo generar código para esto, la spec es insuficiente."

SPEC_CONTENT = """# Spec de ejemplo

## Contexto técnico
Ubicación: `src/agents/impl_agent/saludo.py`

## Diseño propuesto
Una función que saluda.
"""


async def _post_generate(
    monkeypatch,
    tmp_path,
    llm_response=None,
    llm_side_effect=None,
    spec_path=None,
    target_file=None,
    overwrite=False,
):
    # El sandbox de escritura (REPO_ROOT) se mockea a tmp_path para que los
    # tests no dependan de ni ensucien el repo real. impl_agent_dir (la
    # subcarpeta con permiso de overwrite) queda dentro de ese sandbox.
    monkeypatch.setattr(service, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(service, "IMPL_AGENT_DIR", tmp_path / "impl_agent")

    if spec_path is None:
        spec_file = tmp_path / "spec.md"
        spec_file.write_text(SPEC_CONTENT, encoding="utf-8")
        spec_path = str(spec_file)

    if llm_side_effect is not None:
        async def fake_call_llm(prompt: str) -> str:
            raise llm_side_effect
    else:
        async def fake_call_llm(prompt: str) -> str:
            return llm_response

    monkeypatch.setattr(service, "_call_llm", fake_call_llm)

    from main import app

    transport = ASGITransport(app=app)
    payload = {"spec_path": spec_path, "overwrite": overwrite}
    if target_file is not None:
        payload["target_file"] = target_file

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post("/api/agents/impl/generate", json=payload)


@pytest.mark.asyncio
async def test_spec_valida_target_nuevo_devuelve_200(monkeypatch, tmp_path):
    target = tmp_path / "impl_agent" / "saludo.py"
    response = await _post_generate(
        monkeypatch, tmp_path, llm_response=VALID_LLM_RESPONSE, target_file=str(target)
    )

    assert response.status_code == 200
    body = response.json()
    assert "def hola" in body["code"]
    assert body["file_path"] == str(target)
    assert target.exists()


@pytest.mark.asyncio
async def test_target_file_no_provisto_infiere_ruta_de_la_spec(monkeypatch, tmp_path):
    # La spec debe apuntar a una ruta absoluta dentro de tmp_path — si fuera
    # relativa, write_file la resolvería contra el cwd real del proceso y
    # ensuciaría el repo (bug real encontrado al correr la suite completa).
    inferred_target = tmp_path / "impl_agent" / "saludo.py"
    spec_file = tmp_path / "spec.md"
    spec_file.write_text(
        f"# Spec\n\n## Contexto técnico\nUbicación: `{inferred_target}`\n",
        encoding="utf-8",
    )

    response = await _post_generate(
        monkeypatch, tmp_path, llm_response=VALID_LLM_RESPONSE, spec_path=str(spec_file)
    )

    assert response.status_code == 200
    body = response.json()
    assert body["file_path"] == str(inferred_target)
    assert inferred_target.exists()


@pytest.mark.asyncio
async def test_archivo_existente_sin_overwrite_devuelve_409(monkeypatch, tmp_path):
    target = tmp_path / "impl_agent" / "saludo.py"
    target.parent.mkdir(parents=True)
    target.write_text("contenido original", encoding="utf-8")

    response = await _post_generate(
        monkeypatch, tmp_path, llm_response=VALID_LLM_RESPONSE,
        target_file=str(target), overwrite=False,
    )

    assert response.status_code == 409
    assert target.read_text(encoding="utf-8") == "contenido original"


@pytest.mark.asyncio
async def test_archivo_existente_dentro_de_impl_agent_con_overwrite_devuelve_200(monkeypatch, tmp_path):
    # impl_agent/ queda mockeado a tmp_path/impl_agent por _post_generate.
    target = tmp_path / "impl_agent" / "test_overwrite_target.py"
    target.parent.mkdir(parents=True)
    target.write_text("contenido viejo", encoding="utf-8")

    response = await _post_generate(
        monkeypatch, tmp_path, llm_response=VALID_LLM_RESPONSE,
        target_file=str(target), overwrite=True,
    )

    assert response.status_code == 200
    assert "def hola" in target.read_text(encoding="utf-8")


@pytest.mark.asyncio
async def test_archivo_existente_fuera_de_impl_agent_con_overwrite_devuelve_403(monkeypatch, tmp_path):
    target = tmp_path / "fuera" / "otro_agente.py"
    target.parent.mkdir(parents=True)
    target.write_text("codigo de produccion existente", encoding="utf-8")

    response = await _post_generate(
        monkeypatch, tmp_path, llm_response=VALID_LLM_RESPONSE,
        target_file=str(target), overwrite=True,
    )

    assert response.status_code == 403
    assert target.read_text(encoding="utf-8") == "codigo de produccion existente"


@pytest.mark.asyncio
async def test_target_file_inexistente_crea_directorios_intermedios(monkeypatch, tmp_path):
    target = tmp_path / "impl_agent" / "sub" / "nuevo.py"
    response = await _post_generate(
        monkeypatch, tmp_path, llm_response=VALID_LLM_RESPONSE, target_file=str(target)
    )

    assert response.status_code == 200
    assert target.exists()


@pytest.mark.asyncio
async def test_spec_path_inexistente_devuelve_404_sin_llamar_llm(monkeypatch, tmp_path):
    llamadas = {"contador": 0}

    async def fake_call_llm(prompt: str) -> str:
        llamadas["contador"] += 1
        return VALID_LLM_RESPONSE

    monkeypatch.setattr(service, "_call_llm", fake_call_llm)

    from main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/agents/impl/generate",
            json={"spec_path": str(tmp_path / "no_existe.md")},
        )

    assert response.status_code == 404
    assert llamadas["contador"] == 0


@pytest.mark.asyncio
async def test_fallo_del_llm_devuelve_502_sin_escribir_nada(monkeypatch, tmp_path):
    target = tmp_path / "impl_agent" / "saludo.py"
    response = await _post_generate(
        monkeypatch, tmp_path, llm_side_effect=RuntimeError("Groq no disponible"),
        target_file=str(target),
    )

    assert response.status_code == 502
    assert not target.exists()


@pytest.mark.asyncio
async def test_llm_sin_bloque_de_codigo_devuelve_502_sin_escribir_nada(monkeypatch, tmp_path):
    target = tmp_path / "impl_agent" / "saludo.py"
    response = await _post_generate(
        monkeypatch, tmp_path, llm_response=NO_CODE_LLM_RESPONSE, target_file=str(target)
    )

    assert response.status_code == 502
    assert not target.exists()


@pytest.mark.asyncio
async def test_llm_con_multiples_bloques_de_codigo_devuelve_502_sin_adivinar(monkeypatch, tmp_path):
    # Hallazgo de Gate 2: si el LLM incluye un bloque de ejemplo antes del
    # real, el sistema no debe adivinar cuál persistir — debe fallar.
    respuesta_ambigua = '''Ejemplo de estructura:
```python
# solo un ejemplo
```

Código real:
```python
def hola() -> str:
    return "hola"
```
'''
    target = tmp_path / "impl_agent" / "saludo.py"
    response = await _post_generate(
        monkeypatch, tmp_path, llm_response=respuesta_ambigua, target_file=str(target)
    )

    assert response.status_code == 502
    assert not target.exists()


@pytest.mark.asyncio
async def test_target_file_solo_se_infiere_de_contexto_tecnico_o_diseno(monkeypatch, tmp_path):
    # Hallazgo de Gate 2: infer_target no debe tomar un .py mencionado en
    # otra sección (ej. "Fuera de alcance" nombrando un archivo a NO tocar).
    ruta_correcta = tmp_path / "impl_agent" / "correcto.py"
    spec_con_mencion_enganosa = f"""# Spec

## Fuera de alcance
No modificar `legacy/no_tocar.py` bajo ninguna circunstancia.

## Contexto técnico
Ubicación: `{ruta_correcta}`
"""
    spec_file = tmp_path / "spec.md"
    spec_file.write_text(spec_con_mencion_enganosa, encoding="utf-8")

    response = await _post_generate(
        monkeypatch, tmp_path, llm_response=VALID_LLM_RESPONSE, spec_path=str(spec_file)
    )

    assert response.status_code == 200
    assert response.json()["file_path"] == str(ruta_correcta)


@pytest.mark.asyncio
async def test_spec_path_en_response_es_igual_al_request(monkeypatch, tmp_path):
    spec_file = tmp_path / "mi_spec.md"
    spec_file.write_text(SPEC_CONTENT, encoding="utf-8")
    target = tmp_path / "impl_agent" / "saludo.py"

    response = await _post_generate(
        monkeypatch, tmp_path, llm_response=VALID_LLM_RESPONSE,
        spec_path=str(spec_file), target_file=str(target),
    )

    assert response.json()["spec_path"] == str(spec_file)


@pytest.mark.asyncio
async def test_endpoint_es_async():
    import inspect

    from impl_agent import router as router_module

    assert inspect.iscoroutinefunction(router_module.generate)
    assert inspect.iscoroutinefunction(service.generate_code)


def test_no_hay_api_keys_hardcodeadas():
    codigo = (AGENTS_ROOT / "impl_agent" / "service.py").read_text(encoding="utf-8")
    assert "gsk_" not in codigo
    assert "sk-ant-" not in codigo


# ---- Property-based tests ----


@given(spec_path=st.text(min_size=1, max_size=50))
@settings(max_examples=25)
def test_property_spec_inexistente_siempre_404_sin_llamar_llm(spec_path):
    import asyncio

    async def run():
        llamadas = {"contador": 0}

        async def fake_call_llm(prompt: str) -> str:
            llamadas["contador"] += 1
            return VALID_LLM_RESPONSE

        import pytest as _pytest
        mp = _pytest.MonkeyPatch()
        mp.setattr(service, "_call_llm", fake_call_llm)
        try:
            from main import app
            transport = ASGITransport(app=app)
            # Un path generado al azar casi nunca existe en disco.
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/agents/impl/generate", json={"spec_path": f"/no/existe/{spec_path}"}
                )
            assert response.status_code == 404
            assert llamadas["contador"] == 0
        finally:
            mp.undo()

    asyncio.run(run())


@given(target_file=st.sampled_from([
    "../x.py",
    "../../CLAUDE.md",
    "src/agents/spec_agent/service.py",
]))
@settings(max_examples=10)
def test_property_overwrite_fuera_de_impl_agent_siempre_403(target_file):
    import asyncio
    import tempfile

    async def run():
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            spec_file = tmp_path / "spec.md"
            spec_file.write_text(SPEC_CONTENT, encoding="utf-8")

            # Aseguramos que el destino "existente" realmente exista y sea
            # detectable como fuera de impl_agent/: usamos un path absoluto
            # bajo tmp_path que no está dentro de impl_agent/.
            target = tmp_path / "fuera" / Path(target_file).name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("original", encoding="utf-8")

            import pytest as _pytest
            mp = _pytest.MonkeyPatch()

            async def fake_call_llm(prompt: str) -> str:
                return VALID_LLM_RESPONSE

            # REPO_ROOT = tmp_path para que el 403 sea por "fuera de
            # impl_agent/" (lo que este test verifica), no por "fuera del
            # repo real" (que dispararía el chequeo del Fix 1 primero).
            mp.setattr(service, "REPO_ROOT", tmp_path)
            mp.setattr(service, "IMPL_AGENT_DIR", tmp_path / "impl_agent")
            mp.setattr(service, "_call_llm", fake_call_llm)
            try:
                from main import app
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.post(
                        "/api/agents/impl/generate",
                        json={
                            "spec_path": str(spec_file),
                            "target_file": str(target),
                            "overwrite": True,
                        },
                    )
                assert response.status_code == 403
                assert target.read_text(encoding="utf-8") == "original"
            finally:
                mp.undo()

    asyncio.run(run())

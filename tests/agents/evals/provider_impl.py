"""Provider custom de PromptFoo que invoca el Agente Implementador real
(mismo código que corre en producción: build_prompt + _call_llm contra Groq)."""

import asyncio
import sys
from pathlib import Path

AGENTS_ROOT = Path(__file__).resolve().parents[3] / "src" / "agents"
sys.path.insert(0, str(AGENTS_ROOT))

from impl_agent.models import ImplRequest  # noqa: E402
from impl_agent.prompts import build_prompt  # noqa: E402
from impl_agent.service import _call_llm  # noqa: E402


def call_api(prompt: str, options: dict, context: dict) -> dict:
    """Punto de entrada que PromptFoo invoca por cada test case."""
    config = context.get("vars", {})
    spec_content = config.get("spec_content", "")
    request = ImplRequest(
        spec_path="eval-fixture.md",
        target_file=config.get("target_file"),
        overwrite=False,
    )
    prompt_real = build_prompt(spec_content, request)
    output = asyncio.run(_call_llm(prompt_real))
    return {"output": output}

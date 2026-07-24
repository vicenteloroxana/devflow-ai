"""Provider custom de PromptFoo que invoca el Spec Agent real (mismo
código que corre en producción: build_prompt + _call_llm contra Groq)."""

import asyncio
import sys
from pathlib import Path

AGENTS_ROOT = Path(__file__).resolve().parents[3] / "src" / "agents"
sys.path.insert(0, str(AGENTS_ROOT))

from spec_agent.models import SpecRequest  # noqa: E402
from spec_agent.prompts import build_prompt  # noqa: E402
from spec_agent.service import _call_llm  # noqa: E402


def call_api(prompt: str, options: dict, context: dict) -> dict:
    """Punto de entrada que PromptFoo invoca por cada test case."""
    config = context.get("vars", {})
    request = SpecRequest(
        requirement=config.get("requirement", prompt),
        context=config.get("context"),
        priority=config.get("priority"),
        area=config.get("area"),
    )
    prompt_real = build_prompt(request)
    output = asyncio.run(_call_llm(prompt_real))
    return {"output": output}

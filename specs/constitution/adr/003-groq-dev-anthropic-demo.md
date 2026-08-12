# ADR-003: Groq en desarrollo, Anthropic solo para demo

**Estado:** Aceptado

## Contexto
El desarrollo iterativo de los agentes (spec_agent, impl_agent, review_agent, eval_agent) requiere muchas llamadas a LLM; pagar por cada una durante el desarrollo es costoso.

## Decisión
Groq API (`llama-3.3-70b-versatile`) es el LLM de desarrollo por ser gratuito. Anthropic (`claude-haiku-4-5`) se reserva para demos, donde la calidad de salida importa más que el costo.

## Alternativas consideradas
Usar Anthropic en todos los entornos — descartado por costo en fase de desarrollo con iteración alta. Usar un modelo local (Ollama) — no evaluado en profundidad, mencionado como posible alternativa futura si Groq deja de ser viable.

## Consecuencias
El código de `Infrastructure/AI/` debe abstraer el proveedor LLM detrás de una interfaz común para poder alternar entre Groq y Anthropic sin cambiar Application. Riesgo: diferencias de calidad/comportamiento entre modelos pueden no detectarse hasta la demo.

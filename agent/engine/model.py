"""``PROVIDER``/``MODEL``/``BASE_URL`` → a Pydantic AI ``Model``.

This is the ONLY place a provider is chosen. OpenRouter, Ollama, and any other
OpenAI-compatible endpoint ride the OpenAI provider with a ``base_url``; only
Anthropic gets its own provider. Adding a provider here is the entire cost of
supporting it — every tool, the console, and the server are provider-agnostic.
"""

from __future__ import annotations

from pydantic_ai.models import Model
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.providers.openai import OpenAIProvider

from ..runtime.config import Config


def build_model(config: Config) -> Model:
    """Map a loaded :class:`Config` to a concrete Pydantic AI ``Model``."""
    provider = config.provider

    if provider == "anthropic":
        return AnthropicModel(
            config.model,
            provider=AnthropicProvider(api_key=config.api_key or ""),
        )

    # openai · openrouter · ollama · any OpenAI-compatible endpoint
    if provider in ("openai", "openrouter", "ollama") or config.base_url:
        kwargs: dict = {"api_key": config.api_key or "not-needed"}
        if config.base_url:
            kwargs["base_url"] = config.base_url
        return OpenAIChatModel(config.model, provider=OpenAIProvider(**kwargs))

    raise ValueError(
        f"Unknown PROVIDER={provider!r}. Use one of: "
        "openai, anthropic, openrouter, ollama (or set BASE_URL for a "
        "custom OpenAI-compatible endpoint)."
    )

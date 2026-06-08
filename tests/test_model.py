"""Provider mapping: the one place a provider is chosen."""

from pathlib import Path

import pytest
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.openai import OpenAIChatModel

from agent.runtime.config import Config
from agent.engine.model import build_model


def _cfg(provider: str, base_url: str | None = None) -> Config:
    return Config(
        root=Path("."),
        provider=provider,
        model="test-model",
        api_key="sk-test",
        base_url=base_url,
        persona="x",
        settings={},
    )


def test_anthropic_maps_to_anthropic_model():
    assert isinstance(build_model(_cfg("anthropic")), AnthropicModel)


@pytest.mark.parametrize("provider", ["openai", "openrouter", "ollama"])
def test_openai_compatible_providers(provider):
    assert isinstance(build_model(_cfg(provider)), OpenAIChatModel)


def test_custom_base_url_uses_openai_path():
    assert isinstance(
        build_model(_cfg("anything", base_url="http://localhost:1234/v1")),
        OpenAIChatModel,
    )


def test_unknown_provider_raises():
    with pytest.raises(ValueError):
        build_model(_cfg("nonsense"))

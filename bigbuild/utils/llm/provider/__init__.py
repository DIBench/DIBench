from typing import TypeAlias

from .azure import AzureOpenaiProvider
from .openai import OpenAIProvider

LLMProvider: TypeAlias = AzureOpenaiProvider | OpenAIProvider


def make_provider(
    model: str,
    backend: str,
    # only for openai
    base_url: str | None = None,
):
    if backend == "openai":
        from .openai import OpenAIProvider

        return OpenAIProvider(model, base_url=base_url)
    elif backend == "azure":
        from .azure import AzureOpenaiProvider

        return AzureOpenaiProvider(model)
    elif backend == "anthropic":
        from .anthropic import AnthropicProvider

        return AnthropicProvider(model)
    elif backend == "google":
        from .google import GoogleProvider

        return GoogleProvider(model)
    else:
        raise ValueError(f"Unknown backend: {backend}")

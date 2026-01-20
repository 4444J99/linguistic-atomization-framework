"""
LLM Abstraction Layer - Provider-agnostic interface for language model calls.

Supports multiple backends:
- Anthropic (Claude models)
- OpenAI (GPT models)
- Ollama (local models)
- Local (Hugging Face transformers)

Usage:
    from framework.llm import get_provider

    provider = get_provider({
        "provider": "anthropic",
        "model": "claude-sonnet-4-20250514",
        "api_key_env": "ANTHROPIC_API_KEY"
    })

    response = provider.complete(
        prompt="Analyze this text for rhetorical strengths...",
        context={"text": "..."}
    )
"""

from .providers import (
    LLMProvider,
    AnthropicProvider,
    OpenAIProvider,
    OllamaProvider,
    LocalProvider,
    get_provider,
    LLM_AVAILABLE,
)

__all__ = [
    "LLMProvider",
    "AnthropicProvider",
    "OpenAIProvider",
    "OllamaProvider",
    "LocalProvider",
    "get_provider",
    "LLM_AVAILABLE",
]

"""
LLM Abstraction Layer - Provider-agnostic interface for language model calls.

Supports multiple backends:
- Anthropic (Claude models)
- OpenAI (GPT models)
- Ollama (local models)
- Local (Hugging Face transformers)

Includes prompt chain infrastructure for multi-step reasoning:
- PromptTemplate: Structured prompts with schemas and examples
- RhetoricalPromptLibrary: Full 9-step evaluation prompt library
- PromptChainExecutor: Multi-step execution with context accumulation
- OutputParsers: JSON, section, and composite parsing

Usage:
    from framework.llm import get_provider, PromptChainExecutor, prompt_library

    provider = get_provider({
        "provider": "anthropic",
        "model": "claude-sonnet-4-20250514",
        "api_key_env": "ANTHROPIC_API_KEY"
    })

    # Simple completion
    response = provider.complete(
        prompt="Analyze this text for rhetorical strengths...",
        context={"text": "..."}
    )

    # Chain execution for full evaluation
    chain = PromptChainExecutor(provider)
    chain.set_text("Content to analyze...")
    results = chain.execute_all()
"""

from .providers import (
    LLMProvider,
    LLMResponse,
    AnthropicProvider,
    OpenAIProvider,
    OllamaProvider,
    LocalProvider,
    get_provider,
    list_available_providers,
    LLM_AVAILABLE,
)

from .prompts import (
    PromptTemplate,
    RhetoricalPromptLibrary,
    RHETORICAL_PROMPTS,
    prompt_library,
)

from .parsing import (
    OutputParser,
    JSONOutputParser,
    SectionParser,
    KeyValueParser,
    CompositeParser,
    RhetoricalOutputParser,
    default_parser,
)

from .chain import (
    ChainStep,
    ChainContext,
    PromptChainExecutor,
)

__all__ = [
    # Providers
    "LLMProvider",
    "LLMResponse",
    "AnthropicProvider",
    "OpenAIProvider",
    "OllamaProvider",
    "LocalProvider",
    "get_provider",
    "list_available_providers",
    "LLM_AVAILABLE",
    # Prompts
    "PromptTemplate",
    "RhetoricalPromptLibrary",
    "RHETORICAL_PROMPTS",
    "prompt_library",
    # Parsing
    "OutputParser",
    "JSONOutputParser",
    "SectionParser",
    "KeyValueParser",
    "CompositeParser",
    "RhetoricalOutputParser",
    "default_parser",
    # Chain execution
    "ChainStep",
    "ChainContext",
    "PromptChainExecutor",
]

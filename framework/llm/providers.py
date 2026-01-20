"""
LLM Providers - Implementations for various LLM backends.

Each provider implements the same interface, allowing seamless switching
between backends via configuration.
"""

from __future__ import annotations

import os
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

# Track which providers are available
ANTHROPIC_AVAILABLE = False
OPENAI_AVAILABLE = False
OLLAMA_AVAILABLE = False
TRANSFORMERS_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    anthropic = None

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    openai = None

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    ollama = None

try:
    from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    pipeline = None
    AutoModelForCausalLM = None
    AutoTokenizer = None
    torch = None

LLM_AVAILABLE = ANTHROPIC_AVAILABLE or OPENAI_AVAILABLE or OLLAMA_AVAILABLE or TRANSFORMERS_AVAILABLE


@dataclass
class LLMResponse:
    """Response from an LLM provider."""
    text: str
    model: str
    usage: Dict[str, int] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    All providers implement the same interface for text completion,
    allowing the evaluation module to work with any backend.
    """

    name: str = "base"
    default_model: str = ""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the provider.

        Args:
            config: Provider configuration dict containing:
                - model: Model identifier
                - api_key_env: Environment variable name for API key
                - api_key: Direct API key (not recommended)  # allow-secret
                - max_tokens: Maximum response tokens
                - temperature: Sampling temperature
        """
        self.config = config or {}
        self.model = self.config.get("model", self.default_model)
        self.max_tokens = self.config.get("max_tokens", 4096)
        self.temperature = self.config.get("temperature", 0.3)

        # Get API key from env var or direct config
        api_key_env = self.config.get("api_key_env")
        if api_key_env:
            self.api_key = os.environ.get(api_key_env)  # allow-secret
        else:
            self.api_key = self.config.get("api_key")  # allow-secret

    @abstractmethod
    def complete(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None,
    ) -> LLMResponse:
        """
        Generate a completion for the given prompt.

        Args:
            prompt: The user prompt/question
            context: Optional context dict (will be formatted into prompt)
            system_prompt: Optional system prompt for instruction

        Returns:
            LLMResponse with the generated text or error
        """
        pass

    def format_prompt(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Format prompt with context variables."""
        if context:
            # Simple variable substitution
            for key, value in context.items():
                placeholder = f"{{{key}}}"
                if placeholder in prompt:
                    prompt = prompt.replace(placeholder, str(value))
        return prompt

    @property
    def is_available(self) -> bool:
        """Check if this provider is available (dependencies installed)."""
        return True


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider."""

    name = "anthropic"
    default_model = "claude-sonnet-4-20250514"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._client = None

        if ANTHROPIC_AVAILABLE and self.api_key:
            self._client = anthropic.Anthropic(api_key=self.api_key)  # allow-secret

    @property
    def is_available(self) -> bool:
        return ANTHROPIC_AVAILABLE and self._client is not None

    def complete(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None,
    ) -> LLMResponse:
        if not self.is_available:
            return LLMResponse(
                text="",
                model=self.model,
                error="Anthropic provider not available (missing API key or anthropic package)"
            )

        formatted_prompt = self.format_prompt(prompt, context)

        try:
            kwargs = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "messages": [{"role": "user", "content": formatted_prompt}],
            }
            if system_prompt:
                kwargs["system"] = system_prompt

            response = self._client.messages.create(**kwargs)

            return LLMResponse(
                text=response.content[0].text,
                model=self.model,
                usage={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                },
                metadata={"stop_reason": response.stop_reason},
            )

        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            return LLMResponse(
                text="",
                model=self.model,
                error=str(e)
            )


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider."""

    name = "openai"
    default_model = "gpt-4o"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._client = None

        if OPENAI_AVAILABLE and self.api_key:
            self._client = openai.OpenAI(api_key=self.api_key)  # allow-secret

    @property
    def is_available(self) -> bool:
        return OPENAI_AVAILABLE and self._client is not None

    def complete(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None,
    ) -> LLMResponse:
        if not self.is_available:
            return LLMResponse(
                text="",
                model=self.model,
                error="OpenAI provider not available (missing API key or openai package)"
            )

        formatted_prompt = self.format_prompt(prompt, context)

        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": formatted_prompt})

            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )

            return LLMResponse(
                text=response.choices[0].message.content,
                model=self.model,
                usage={
                    "input_tokens": response.usage.prompt_tokens,
                    "output_tokens": response.usage.completion_tokens,
                },
                metadata={"finish_reason": response.choices[0].finish_reason},
            )

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return LLMResponse(
                text="",
                model=self.model,
                error=str(e)
            )


class OllamaProvider(LLMProvider):
    """Ollama local model provider."""

    name = "ollama"
    default_model = "llama3"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._host = self.config.get("host", "http://localhost:11434")

    @property
    def is_available(self) -> bool:
        if not OLLAMA_AVAILABLE:
            return False
        # Try to ping the server
        try:
            ollama.list()
            return True
        except Exception:
            return False

    def complete(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None,
    ) -> LLMResponse:
        if not OLLAMA_AVAILABLE:
            return LLMResponse(
                text="",
                model=self.model,
                error="Ollama package not installed"
            )

        formatted_prompt = self.format_prompt(prompt, context)

        try:
            # Build the full prompt with system message
            full_prompt = formatted_prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{formatted_prompt}"

            response = ollama.generate(
                model=self.model,
                prompt=full_prompt,
                options={
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens,
                },
            )

            return LLMResponse(
                text=response["response"],
                model=self.model,
                usage={
                    "input_tokens": response.get("prompt_eval_count", 0),
                    "output_tokens": response.get("eval_count", 0),
                },
                metadata={
                    "total_duration": response.get("total_duration"),
                    "done": response.get("done"),
                },
            )

        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return LLMResponse(
                text="",
                model=self.model,
                error=str(e)
            )


class LocalProvider(LLMProvider):
    """Local Hugging Face transformers provider."""

    name = "local"
    default_model = "microsoft/phi-2"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._pipeline = None
        self._loaded = False

    def _load_model(self):
        """Lazy load the model on first use."""
        if self._loaded or not TRANSFORMERS_AVAILABLE:
            return

        try:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self._pipeline = pipeline(
                "text-generation",
                model=self.model,
                device=device,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            )
            self._loaded = True
        except Exception as e:
            logger.error(f"Failed to load local model: {e}")
            self._loaded = True  # Mark as loaded to avoid repeated attempts

    @property
    def is_available(self) -> bool:
        return TRANSFORMERS_AVAILABLE

    def complete(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None,
    ) -> LLMResponse:
        if not TRANSFORMERS_AVAILABLE:
            return LLMResponse(
                text="",
                model=self.model,
                error="Transformers package not installed"
            )

        self._load_model()

        if self._pipeline is None:
            return LLMResponse(
                text="",
                model=self.model,
                error="Failed to load local model"
            )

        formatted_prompt = self.format_prompt(prompt, context)

        try:
            # Build full prompt
            full_prompt = formatted_prompt
            if system_prompt:
                full_prompt = f"System: {system_prompt}\n\nUser: {formatted_prompt}\n\nAssistant:"

            result = self._pipeline(
                full_prompt,
                max_new_tokens=self.max_tokens,
                temperature=self.temperature,
                do_sample=True,
                pad_token_id=self._pipeline.tokenizer.eos_token_id,
            )

            generated_text = result[0]["generated_text"]
            # Extract only the generated part (after the prompt)
            if full_prompt in generated_text:
                generated_text = generated_text[len(full_prompt):].strip()

            return LLMResponse(
                text=generated_text,
                model=self.model,
                metadata={"device": "cuda" if torch.cuda.is_available() else "cpu"},
            )

        except Exception as e:
            logger.error(f"Local model error: {e}")
            return LLMResponse(
                text="",
                model=self.model,
                error=str(e)
            )


# Provider registry
PROVIDERS: Dict[str, type[LLMProvider]] = {
    "anthropic": AnthropicProvider,
    "openai": OpenAIProvider,
    "ollama": OllamaProvider,
    "local": LocalProvider,
}


def get_provider(config: Optional[Dict[str, Any]] = None) -> Optional[LLMProvider]:
    """
    Factory function to get an LLM provider.

    Args:
        config: Configuration dict with at minimum a "provider" key

    Returns:
        LLMProvider instance or None if not available

    Example:
        provider = get_provider({
            "provider": "anthropic",
            "model": "claude-sonnet-4-20250514",
            "api_key_env": "ANTHROPIC_API_KEY"
        })
    """
    if config is None:
        return None

    provider_name = config.get("provider", "").lower()

    if provider_name not in PROVIDERS:
        logger.warning(f"Unknown provider: {provider_name}. Available: {list(PROVIDERS.keys())}")
        return None

    provider_cls = PROVIDERS[provider_name]
    provider = provider_cls(config)

    if not provider.is_available:
        logger.warning(f"Provider {provider_name} is not available (missing dependencies or credentials)")
        return None

    return provider


def list_available_providers() -> List[str]:
    """Return list of providers with available dependencies."""
    available = []
    if ANTHROPIC_AVAILABLE:
        available.append("anthropic")
    if OPENAI_AVAILABLE:
        available.append("openai")
    if OLLAMA_AVAILABLE:
        available.append("ollama")
    if TRANSFORMERS_AVAILABLE:
        available.append("local")
    return available

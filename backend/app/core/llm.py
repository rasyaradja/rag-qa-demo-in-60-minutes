"""
LLM API abstraction for RAG Q&A Demo (FastAPI backend).

- Provides async LLM completion functions for supported providers (OpenAI, Anthropic, Hugging Face Llama).
- Handles prompt construction, model selection, error handling, and streaming (if needed).
- Used by the RAG pipeline to generate answers from retrieved context.
- Supports prompt versioning and model selection via config.

Dependencies:
- openai
- httpx
- config.py (for settings)
"""

import asyncio
from typing import Optional, Dict, Any, List, Literal

import httpx

from .config import settings

# Try to import OpenAI, fallback gracefully if not installed
try:
    import openai
except ImportError:
    openai = None

# --- Exceptions ---

class LLMError(Exception):
    """Raised when LLM completion fails."""
    pass

# --- LLM Provider Base ---

class LLMProvider:
    """Abstract base for LLM providers."""

    async def complete(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 512,
        stop: Optional[List[str]] = None,
        **kwargs,
    ) -> str:
        raise NotImplementedError

# --- OpenAI LLM Provider ---

class OpenAIProvider(LLMProvider):
    """
    LLM provider using OpenAI Chat Completion API (gpt-3.5-turbo, gpt-4, etc).
    """

    def __init__(self, api_key: str, default_model: str = "gpt-3.5-turbo"):
        if openai is None:
            raise ImportError("openai package is required for OpenAI LLM calls.")
        self.api_key = api_key
        self.default_model = default_model

    async def complete(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 512,
        stop: Optional[List[str]] = None,
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> str:
        """
        Calls OpenAI's ChatCompletion API asynchronously.
        """
        model = model or self.default_model
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Use httpx for async call (openai>=1.0.0 supports async, but we use httpx for consistency)
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                        "stop": stop,
                    },
                )
                if response.status_code != 200:
                    raise LLMError(
                        f"OpenAI LLM API error: {response.status_code} {response.text}"
                    )
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
            except Exception as e:
                raise LLMError(f"OpenAI LLM completion failed: {e}") from e

# --- Anthropic LLM Provider (Placeholder) ---

class AnthropicProvider(LLMProvider):
    """
    Placeholder for Anthropic Claude LLM support.
    """
    def __init__(self, api_key: str, default_model: str = "claude-3-opus-20240229"):
        raise NotImplementedError("Anthropic LLM is not yet implemented.")

# --- Hugging Face Llama Provider (Placeholder) ---

class HuggingFaceLlamaProvider(LLMProvider):
    """
    Placeholder for Hugging Face Llama LLM support.
    """
    def __init__(self, hf_token: str, default_model: str = "meta-llama/Llama-2-7b-chat-hf"):
        raise NotImplementedError("Hugging Face Llama LLM is not yet implemented.")

# --- Provider Factory ---

def get_llm_provider() -> LLMProvider:
    """
    Selects and returns the LLM provider based on config.
    """
    # For now, default to OpenAI; extend as needed
    # Model selection logic can be expanded for Anthropic/HF
    model = getattr(settings, "llm_model", None) or "gpt-3.5-turbo"
    if model.startswith("gpt-"):
        return OpenAIProvider(
            api_key=settings.openai_api_key.get_secret_value(),
            default_model=model,
        )
    # elif model.startswith("claude-"):
    #     return AnthropicProvider(
    #         api_key=settings.anthropic_api_key.get_secret_value(),
    #         default_model=model,
    #     )
    # elif model.startswith("meta-llama") or ...:
    #     return HuggingFaceLlamaProvider(
    #         hf_token=settings.hf_token.get_secret_value(),
    #         default_model=model,
    #     )
    else:
        raise ValueError(f"Unsupported LLM model: {model}")

# --- Public API ---

_provider: Optional[LLMProvider] = None

def get_provider() -> LLMProvider:
    """
    Singleton accessor for LLM provider.
    """
    global _provider
    if _provider is None:
        _provider = get_llm_provider()
    return _provider

async def llm_complete(
    prompt: str,
    model: Optional[str] = None,
    temperature: float = 0.0,
    max_tokens: int = 512,
    stop: Optional[List[str]] = None,
    system_prompt: Optional[str] = None,
    **kwargs,
) -> str:
    """
    Generate a completion from the configured LLM provider.
    """
    provider = get_provider()
    return await provider.complete(
        prompt=prompt,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        stop=stop,
        system_prompt=system_prompt,
        **kwargs,
    )

# --- Synchronous Wrapper (for scripts, migration, etc.) ---

def llm_complete_sync(
    prompt: str,
    model: Optional[str] = None,
    temperature: float = 0.0,
    max_tokens: int = 512,
    stop: Optional[List[str]] = None,
    system_prompt: Optional[str] = None,
    **kwargs,
) -> str:
    """
    Synchronous wrapper for LLM completion (for scripts).
    """
    return asyncio.run(
        llm_complete(
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            stop=stop,
            system_prompt=system_prompt,
            **kwargs,
        )
    )

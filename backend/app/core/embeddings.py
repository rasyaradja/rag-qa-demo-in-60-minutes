"""
Embedding generation module for RAG Q&A Demo (FastAPI backend).

- Provides async embedding functions for supported models/APIs.
- Supports OpenAI, Anthropic (future), and Hugging Face (future) embedding backends.
- Handles batching, error handling, and model selection via config.
- Used by retrieval pipeline and document ingestion.

Dependencies:
- openai
- httpx
- config.py (for settings)
"""

import asyncio
from typing import List, Optional, Union

import httpx

from .config import settings

# Try to import OpenAI, fallback gracefully if not installed
try:
    import openai
except ImportError:
    openai = None

# Optionally, import Anthropic/HF as needed in future
# import anthropic
# from huggingface_hub import InferenceClient

# --- Embedding Provider Base ---

class EmbeddingError(Exception):
    """Raised when embedding generation fails."""
    pass

class EmbeddingProvider:
    """Abstract base for embedding providers."""

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError

    async def embed_text(self, text: str) -> List[float]:
        """Convenience: embed a single string."""
        results = await self.embed_texts([text])
        return results[0]

# --- OpenAI Embedding Provider ---

class OpenAIEmbeddingProvider(EmbeddingProvider):
    """
    Embedding provider using OpenAI API (text-embedding-ada-002 or similar).
    """

    def __init__(self, api_key: str, model: str = "text-embedding-ada-002"):
        if openai is None:
            raise ImportError("openai package is required for OpenAI embeddings.")
        self.api_key = api_key
        self.model = model

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts using OpenAI's async API.
        Handles batching (max 2048 tokens per request, 96 inputs per batch for ada-002).
        """
        if not texts:
            return []

        # OpenAI's API supports up to 8192 tokens per request, but batching is limited by model.
        # We'll use a conservative batch size.
        batch_size = 96
        results: List[List[float]] = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i+batch_size]
                try:
                    response = await client.post(
                        "https://api.openai.com/v1/embeddings",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "input": batch,
                            "model": self.model,
                        },
                    )
                    if response.status_code != 200:
                        raise EmbeddingError(
                            f"OpenAI embedding API error: {response.status_code} {response.text}"
                        )
                    data = response.json()
                    # Sort by 'index' to preserve input order
                    batch_embeddings = [None] * len(batch)
                    for obj in data["data"]:
                        batch_embeddings[obj["index"]] = obj["embedding"]
                    if any(e is None for e in batch_embeddings):
                        raise EmbeddingError("Missing embedding(s) in OpenAI response.")
                    results.extend(batch_embeddings)
                except Exception as e:
                    raise EmbeddingError(f"OpenAI embedding failed: {e}") from e
        return results

# --- (Optional) Anthropic Embedding Provider ---

class AnthropicEmbeddingProvider(EmbeddingProvider):
    """
    Placeholder for Anthropic embedding support.
    """
    def __init__(self, api_key: str, model: str = "claude-3-embeddings-2024-04-08"):
        raise NotImplementedError("Anthropic embedding is not yet implemented.")

# --- (Optional) Hugging Face Embedding Provider ---

class HuggingFaceEmbeddingProvider(EmbeddingProvider):
    """
    Placeholder for Hugging Face embedding support.
    """
    def __init__(self, hf_token: str, model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        raise NotImplementedError("Hugging Face embedding is not yet implemented.")

# --- Provider Factory ---

def get_embedding_provider() -> EmbeddingProvider:
    """
    Selects and returns the embedding provider based on config.
    """
    model = settings.embeddings_model
    if model.startswith("text-embedding-") or model.startswith("text-search-"):
        # OpenAI
        return OpenAIEmbeddingProvider(
            api_key=settings.openai_api_key.get_secret_value(),
            model=model,
        )
    # elif model.startswith("claude-"):
    #     return AnthropicEmbeddingProvider(
    #         api_key=settings.anthropic_api_key.get_secret_value(),
    #         model=model,
    #     )
    # elif model.startswith("sentence-transformers") or ...:
    #     return HuggingFaceEmbeddingProvider(
    #         hf_token=settings.hf_token.get_secret_value(),
    #         model=model,
    #     )
    else:
        raise ValueError(f"Unsupported embeddings model: {model}")

# --- Public API ---

_provider: Optional[EmbeddingProvider] = None

def get_provider() -> EmbeddingProvider:
    """
    Singleton accessor for embedding provider.
    """
    global _provider
    if _provider is None:
        _provider = get_embedding_provider()
    return _provider

async def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a list of texts using the configured provider.
    """
    provider = get_provider()
    return await provider.embed_texts(texts)

async def embed_text(text: str) -> List[float]:
    """
    Generate embedding for a single text string.
    """
    provider = get_provider()
    return await provider.embed_text(text)

# --- Synchronous Wrappers (for migration scripts, etc.) ---

def embed_texts_sync(texts: List[str]) -> List[List[float]]:
    """
    Synchronous wrapper for embedding texts (for scripts).
    """
    return asyncio.run(embed_texts(texts))

def embed_text_sync(text: str) -> List[float]:
    """
    Synchronous wrapper for embedding a single text (for scripts).
    """
    return asyncio.run(embed_text(text))

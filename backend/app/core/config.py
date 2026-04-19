"""
Centralized configuration loader for RAG Q&A Demo (FastAPI backend).

- Loads environment variables from `.env` using pydantic-settings.
- Provides strongly-typed access to all config options.
- Used throughout backend for LLM, DB, vector store, CORS, and evaluation settings.
"""

import os
from typing import List, Optional, Literal

from pydantic import AnyUrl, SecretStr, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # === LLM & Embeddings API Keys ===
    openai_api_key: SecretStr = Field(..., env="OPENAI_API_KEY")
    anthropic_api_key: Optional[SecretStr] = Field(None, env="ANTHROPIC_API_KEY")
    hf_token: Optional[SecretStr] = Field(None, env="HF_TOKEN")

    # === Vector Database Configuration ===
    vector_db: Literal["faiss", "pinecone"] = Field("faiss", env="VECTOR_DB")
    pinecone_api_key: Optional[SecretStr] = Field(None, env="PINECONE_API_KEY")

    # === Database Configuration ===
    database_url: AnyUrl = Field(..., env="DATABASE_URL")

    # === Embeddings Model ===
    embeddings_model: str = Field("text-embedding-ada-002", env="EMBEDDINGS_MODEL")

    # === Backend Configuration ===
    secret_key: SecretStr = Field(..., env="SECRET_KEY")
    port: int = Field(8000, env="PORT")

    # === CORS & Frontend ===
    allowed_origins: str = Field("*", env="ALLOWED_ORIGINS")

    # === Prompt/Context Versioning ===
    prompt_version: str = Field("v1", env="PROMPT_VERSION")

    # === Evaluation ===
    eval_set_path: str = Field("backend/data/eval_set.json", env="EVAL_SET_PATH")

    # === Optional: Other Settings ===
    # log_level: str = Field("info", env="LOG_LEVEL")
    # max_context_docs: int = Field(4, env="MAX_CONTEXT_DOCS")

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def allowed_origins_list(self) -> List[str]:
        """
        Returns allowed origins as a list for CORS middleware.
        Supports comma-separated values or '*' for all.
        """
        if self.allowed_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @property
    def is_pinecone(self) -> bool:
        return self.vector_db == "pinecone"

    @property
    def is_faiss(self) -> bool:
        return self.vector_db == "faiss"


# Singleton settings instance for import throughout backend
settings = Settings()

"""
Prompt template management and versioning utilities for RAG Q&A Demo (FastAPI backend).

- Loads prompt templates from disk based on version (configurable via PROMPT_VERSION).
- Supports switching prompt templates for experimentation and evaluation.
- Provides functions to retrieve the current prompt template and list available versions.
- Used by the RAG pipeline to construct LLM prompts with retrieved context.

Prompt templates are stored as text files in `backend/data/prompts/`, e.g.:
    backend/data/prompts/base_prompt.txt
    backend/data/prompts/v1.txt
    backend/data/prompts/v2.txt

The template may contain placeholders such as:
    {context} - for retrieved document context
    {question} - for the user question
    {citations} - for citation formatting (optional)

If a version is not found, falls back to 'base_prompt.txt'.

Dependencies:
- config.py (for settings)
"""

import os
from typing import Dict, Optional, List

from .config import settings

PROMPT_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../data/prompts")
)

# Cache for loaded prompt templates: {version: template_str}
_prompt_cache: Dict[str, str] = {}

def _get_prompt_path(version: str) -> str:
    """
    Returns the file path for a given prompt version.
    """
    # Try versioned file first (e.g., v1.txt), then fallback to base_prompt.txt
    version_file = os.path.join(PROMPT_DIR, f"{version}.txt")
    if os.path.isfile(version_file):
        return version_file
    # Fallback to base_prompt.txt
    base_file = os.path.join(PROMPT_DIR, "base_prompt.txt")
    if os.path.isfile(base_file):
        return base_file
    raise FileNotFoundError(
        f"No prompt template found for version '{version}' or 'base_prompt.txt' in {PROMPT_DIR}"
    )

def load_prompt_template(version: Optional[str] = None) -> str:
    """
    Loads the prompt template for the given version (or current config version).
    Caches loaded templates for efficiency.
    """
    version = version or settings.prompt_version
    if version in _prompt_cache:
        return _prompt_cache[version]
    path = _get_prompt_path(version)
    with open(path, "r", encoding="utf-8") as f:
        template = f.read()
    _prompt_cache[version] = template
    return template

def get_prompt_template(version: Optional[str] = None) -> str:
    """
    Public accessor for the current prompt template.
    """
    return load_prompt_template(version)

def list_available_prompt_versions() -> List[str]:
    """
    Lists all available prompt template versions in the prompt directory.
    Returns a list of version strings (without .txt extension).
    """
    versions = []
    if not os.path.isdir(PROMPT_DIR):
        return versions
    for fname in os.listdir(PROMPT_DIR):
        if fname.endswith(".txt"):
            version = fname[:-4]  # strip .txt
            versions.append(version)
    return sorted(versions)

def render_prompt(
    context: str,
    question: str,
    citations: Optional[str] = None,
    version: Optional[str] = None,
    extra_vars: Optional[Dict[str, str]] = None,
) -> str:
    """
    Renders the prompt template with provided context, question, and citations.
    Allows for extra variables if needed.
    """
    template = get_prompt_template(version)
    variables = {
        "context": context,
        "question": question,
        "citations": citations or "",
    }
    if extra_vars:
        variables.update(extra_vars)
    try:
        prompt = template.format(**variables)
    except KeyError as e:
        missing = e.args[0]
        raise ValueError(
            f"Missing variable '{missing}' in prompt template for version '{version or settings.prompt_version}'"
        )
    return prompt

def get_current_prompt_version() -> str:
    """
    Returns the currently configured prompt version.
    """
    return settings.prompt_version

def reload_prompt_cache() -> None:
    """
    Clears the prompt template cache (for hot-reloading in dev).
    """
    _prompt_cache.clear()

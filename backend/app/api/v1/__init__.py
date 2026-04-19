"""
API v1 package for FastAPI routing.

- Imports and exposes all v1 endpoint modules for inclusion in the main FastAPI app.
- Ensures Python treats this directory as a package.
"""

# Import endpoint modules to register routers in main.py
from .endpoints import rag, eval, health

"""
Vector database abstraction for RAG Q&A Demo (FastAPI backend).

- Provides async interface for storing and searching document embeddings.
- Supports FAISS (local, in-memory or disk) and Pinecone (cloud) backends.
- Handles initialization, upsert, and similarity search.
- Used by retrieval pipeline for context selection.

Dependencies:
- faiss-cpu (for FAISS backend)
- pinecone-client (for Pinecone backend)
- numpy
- config.py (for settings)
- embeddings.py (for embedding generation)
"""

import os
import asyncio
from typing import List, Tuple, Optional, Dict, Any, Union

import numpy as np

from .config import settings
from .embeddings import embed_texts_sync, embed_texts, embed_text_sync

# --- Exceptions ---

class VectorStoreError(Exception):
    """Raised when vector store operations fail."""
    pass

# --- Document Representation ---

class VectorDocument:
    """
    Represents a document stored in the vector DB.
    """
    def __init__(
        self,
        doc_id: str,
        title: str,
        content: str,
        embedding: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.doc_id = doc_id
        self.title = title
        self.content = content
        self.embedding = embedding
        self.metadata = metadata or {}

# --- Abstract Vector Store ---

class VectorStore:
    """
    Abstract base for vector DB backends.
    """

    async def add_documents(self, docs: List[VectorDocument]) -> None:
        raise NotImplementedError

    async def similarity_search(
        self,
        query_embedding: List[float],
        top_k: int = 4,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[VectorDocument, float]]:
        """
        Returns a list of (VectorDocument, similarity_score) tuples.
        """
        raise NotImplementedError

    async def get_document(self, doc_id: str) -> Optional[VectorDocument]:
        raise NotImplementedError

    async def list_documents(self) -> List[VectorDocument]:
        raise NotImplementedError

# --- FAISS Vector Store ---

class FaissVectorStore(VectorStore):
    """
    FAISS-based vector store (local, in-memory or disk).
    """

    def __init__(self, dim: int, persist_path: Optional[str] = None):
        try:
            import faiss
        except ImportError:
            raise ImportError("faiss-cpu is required for FAISS vector store.")
        self.faiss = faiss
        self.dim = dim
        self.persist_path = persist_path
        self.index = self._load_or_create_index()
        self.doc_store: Dict[int, VectorDocument] = {}  # FAISS idx -> VectorDocument
        self.id_to_faiss_idx: Dict[str, int] = {}       # doc_id -> FAISS idx
        self._next_idx = 0

    def _load_or_create_index(self):
        if self.persist_path and os.path.exists(self.persist_path):
            index = self.faiss.read_index(self.persist_path)
        else:
            index = self.faiss.IndexFlatL2(self.dim)
        return index

    def _save_index(self):
        if self.persist_path:
            self.faiss.write_index(self.index, self.persist_path)

    async def add_documents(self, docs: List[VectorDocument]) -> None:
        """
        Adds documents and their embeddings to the FAISS index.
        """
        new_vecs = []
        new_docs = []
        for doc in docs:
            if doc.embedding is None:
                raise VectorStoreError(f"Document {doc.doc_id} missing embedding.")
            if doc.doc_id in self.id_to_faiss_idx:
                continue  # Skip duplicates
            new_vecs.append(np.array(doc.embedding, dtype=np.float32))
            new_docs.append(doc)
        if not new_vecs:
            return
        vecs_np = np.stack(new_vecs)
        self.index.add(vecs_np)
        for i, doc in enumerate(new_docs):
            faiss_idx = self._next_idx
            self.doc_store[faiss_idx] = doc
            self.id_to_faiss_idx[doc.doc_id] = faiss_idx
            self._next_idx += 1
        self._save_index()

    async def similarity_search(
        self,
        query_embedding: List[float],
        top_k: int = 4,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[VectorDocument, float]]:
        """
        Returns top_k most similar documents to the query embedding.
        """
        if self.index.ntotal == 0:
            return []
        query_np = np.array(query_embedding, dtype=np.float32).reshape(1, -1)
        D, I = self.index.search(query_np, top_k)
        results = []
        for idx, dist in zip(I[0], D[0]):
            doc = self.doc_store.get(idx)
            if doc is None:
                continue
            if filter:
                # Simple metadata filter (all keys must match)
                if not all(doc.metadata.get(k) == v for k, v in filter.items()):
                    continue
            similarity = 1.0 / (1.0 + dist)  # Convert L2 distance to similarity (approx)
            results.append((doc, similarity))
        return results

    async def get_document(self, doc_id: str) -> Optional[VectorDocument]:
        idx = self.id_to_faiss_idx.get(doc_id)
        if idx is not None:
            return self.doc_store.get(idx)
        return None

    async def list_documents(self) -> List[VectorDocument]:
        return list(self.doc_store.values())

# --- Pinecone Vector Store ---

class PineconeVectorStore(VectorStore):
    """
    Pinecone-based vector store (cloud).
    """

    def __init__(self, dim: int, index_name: str = "rag-demo"):
        try:
            import pinecone
        except ImportError:
            raise ImportError("pinecone-client is required for Pinecone vector store.")
        self.pinecone = pinecone
        self.dim = dim
        self.index_name = index_name
        self.api_key = settings.pinecone_api_key.get_secret_value()
        self._init_pinecone()
        self.index = self.pinecone.Index(self.index_name)

    def _init_pinecone(self):
        self.pinecone.init(api_key=self.api_key, environment="us-west1-gcp")
        # Create index if not exists
        if self.index_name not in self.pinecone.list_indexes():
            self.pinecone.create_index(
                self.index_name,
                dimension=self.dim,
                metric="cosine",
            )

    async def add_documents(self, docs: List[VectorDocument]) -> None:
        """
        Upserts documents into Pinecone index.
        """
        vectors = []
        for doc in docs:
            if doc.embedding is None:
                raise VectorStoreError(f"Document {doc.doc_id} missing embedding.")
            vectors.append({
                "id": doc.doc_id,
                "values": doc.embedding,
                "metadata": {
                    "title": doc.title,
                    "content": doc.content,
                    **doc.metadata,
                },
            })
        if not vectors:
            return
        # Pinecone upsert is synchronous; run in thread pool
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, lambda: self.index.upsert(vectors)
        )

    async def similarity_search(
        self,
        query_embedding: List[float],
        top_k: int = 4,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[VectorDocument, float]]:
        """
        Returns top_k most similar documents to the query embedding.
        """
        # Pinecone query is synchronous; run in thread pool
        loop = asyncio.get_event_loop()
        def _query():
            return self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                filter=filter,
            )
        result = await loop.run_in_executor(None, _query)
        docs = []
        for match in result.matches:
            meta = match.metadata or {}
            doc = VectorDocument(
                doc_id=match.id,
                title=meta.get("title", ""),
                content=meta.get("content", ""),
                embedding=None,  # Not returned by Pinecone
                metadata={k: v for k, v in meta.items() if k not in ("title", "content")},
            )
            docs.append((doc, match.score))
        return docs

    async def get_document(self, doc_id: str) -> Optional[VectorDocument]:
        # Pinecone fetch is synchronous; run in thread pool
        loop = asyncio.get_event_loop()
        def _fetch():
            res = self.index.fetch(ids=[doc_id])
            if res and res.vectors and doc_id in res.vectors:
                v = res.vectors[doc_id]
                meta = v.metadata or {}
                return VectorDocument(
                    doc_id=doc_id,
                    title=meta.get("title", ""),
                    content=meta.get("content", ""),
                    embedding=None,
                    metadata={k: v for k, v in meta.items() if k not in ("title", "content")},
                )
            return None
        return await loop.run_in_executor(None, _fetch)

    async def list_documents(self) -> List[VectorDocument]:
        # Pinecone does not support listing all docs efficiently for large indexes.
        # For demo, we can fetch up to 1000.
        loop = asyncio.get_event_loop()
        def _list():
            res = self.index.describe_index_stats()
            total = res.get("total_vector_count", 0)
            # Not efficient for large indexes!
            if total == 0:
                return []
            # Use a dummy query to get all IDs (not recommended for prod)
            # Here, we just return empty for safety.
            return []
        return await loop.run_in_executor(None, _list)

# --- Factory and Singleton ---

_vectorstore: Optional[VectorStore] = None
_vectorstore_dim: Optional[int] = None

def get_vectorstore(dim: Optional[int] = None) -> VectorStore:
    """
    Returns the singleton vector store instance, initializing if needed.
    Dimension must match embedding size.
    """
    global _vectorstore, _vectorstore_dim
    if _vectorstore is not None:
        if dim is not None and _vectorstore_dim != dim:
            raise VectorStoreError(
                f"Vector store already initialized with dim={_vectorstore_dim}, got dim={dim}"
            )
        return _vectorstore

    # Determine embedding dimension by embedding a dummy string if not provided
    if dim is None:
        dummy_emb = embed_text_sync("dummy")
        dim = len(dummy_emb)
    _vectorstore_dim = dim

    if settings.is_faiss:
        persist_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../data/faiss.index")
        )
        _vectorstore = FaissVectorStore(dim=dim, persist_path=persist_path)
    elif settings.is_pinecone:
        _vectorstore = PineconeVectorStore(dim=dim)
    else:
        raise VectorStoreError(f"Unknown vector DB backend: {settings.vector_db}")
    return _vectorstore

async def add_documents_to_vectorstore(docs: List[VectorDocument]) -> None:
    """
    Adds documents to the configured vector store, embedding if needed.
    """
    # Embed any docs missing embeddings
    docs_to_embed = [doc for doc in docs if doc.embedding is None]
    if docs_to_embed:
        texts = [doc.content for doc in docs_to_embed]
        embeddings = await embed_texts(texts)
        for doc, emb in zip(docs_to_embed, embeddings):
            doc.embedding = emb
    # All docs now have embeddings
    dim = len(docs[0].embedding)
    store = get_vectorstore(dim=dim)
    await store.add_documents(docs)

async def similarity_search(
    query: Union[str, List[float]],
    top_k: int = 4,
    filter: Optional[Dict[str, Any]] = None,
) -> List[Tuple[VectorDocument, float]]:
    """
    Performs similarity search for a query string or embedding.
    Returns a list of (VectorDocument, similarity_score).
    """
    if isinstance(query, str):
        query_emb = await embed_texts([query])
        query_embedding = query_emb[0]
    else:
        query_embedding = query
    store = get_vectorstore(dim=len(query_embedding))
    return await store.similarity_search(query_embedding, top_k=top_k, filter=filter)

async def get_document_by_id(doc_id: str) -> Optional[VectorDocument]:
    """
    Retrieves a document by its ID from the vector store.
    """
    store = get_vectorstore()
    return await store.get_document(doc_id)

async def list_all_documents() -> List[VectorDocument]:
    """
    Lists all documents in the vector store (may be limited for Pinecone).
    """
    store = get_vectorstore()
    return await store.list_documents()

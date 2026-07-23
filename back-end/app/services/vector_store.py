"""
Adaptador simple para persistencia de vectores.
Soporta por defecto almacenamiento local (numpy + manifest) y un placeholder
para integrar Qdrant o pgvector si se habilita mediante variables de entorno.
"""
import os
from typing import Any, List, Optional, Tuple

import numpy as np

from app.services.rag_cache import _cache_dir


class VectorStore:
    def __init__(self, data_dir: str):
        self.data_dir = os.path.abspath(data_dir)
        self.mode = os.environ.get("VECTOR_STORE", "local")

    def save(self, manifest: List[dict], chunks: List[dict], embeddings: np.ndarray, model: str) -> None:
        if self.mode == "local":
            base = _cache_dir(self.data_dir)
            np.save(os.path.join(base, "embeddings.npy"), embeddings)
            # manifest and chunks are handled by rag_cache.save_index normally
            return
        # Placeholder: implement Qdrant/pgvector integration here
        raise NotImplementedError("Vector store mode '%s' not implemented" % self.mode)

    def search(self, query_embedding: np.ndarray, top_k: int = 10) -> List[Tuple[int, float]]:
        if self.mode == "local":
            # Local search should be delegated to RagService which keeps embeddings in memory
            raise NotImplementedError("Local search should use in-memory embeddings from RagService")
        raise NotImplementedError("Vector store mode '%s' not implemented" % self.mode)

import os
from typing import Dict, List, Optional, Tuple

import cohere
import numpy as np

from app.config import settings
from app.services.category_registry import category_matches, list_business_categories
from app.services.document_loader import DocumentChunk, DocumentLoader
from app.services.ingest_curation import SKIP_DIR_NAMES, CurationStats, curate_file_paths
from app.services.rag_cache import build_manifest, load_index, save_index


class IngestResult:
    def __init__(
        self,
        docs_processed: int,
        chunks_count: int,
        categories: List[str],
        curation: CurationStats,
        cache_hit: bool,
    ):
        self.docs_processed = docs_processed
        self.chunks_count = chunks_count
        self.categories = categories
        self.curation = curation
        self.cache_hit = cache_hit


class CohereRAGService:
    """
    Servicio RAG: ingesta curada, embeddings Cohere, búsqueda semántica y caché local.
    """

    def __init__(self):
        self.cohere_client = None
        if settings.COHERE_API_KEY:
            try:
                self.cohere_client = cohere.Client(api_key=settings.COHERE_API_KEY)
                print("[CohereRAGService] ✅ Cliente de Cohere inicializado correctamente.")
            except Exception as e:
                print(f"[CohereRAGService] ❌ Error inicializando cliente de Cohere: {e}")
        else:
            print("[CohereRAGService] ⚠️ ATENCIÓN: COHERE_API_KEY no encontrada en .env")

        self.chunks: List[DocumentChunk] = []
        self.embeddings: np.ndarray = np.array([])
        self.categories: set = set()
        self.last_curation = CurationStats()
        self.last_cache_hit = False
        self.indexed_files: List[str] = []

    def _data_roots(self) -> List[str]:
        roots = [os.path.abspath(settings.DATA_DIR)]
        extra = (settings.EXTRA_DATA_DIRS or "").strip()
        if extra:
            for part in extra.split(","):
                path = part.strip()
                if path:
                    roots.append(os.path.abspath(path))
        return roots

    def _discover_raw_paths(self) -> List[str]:
        paths: List[str] = []
        for root in self._data_roots():
            if not os.path.isdir(root):
                os.makedirs(root, exist_ok=True)
                continue
            for walk_root, dirnames, files in os.walk(root):
                dirnames[:] = [d for d in dirnames if d not in SKIP_DIR_NAMES]
                for file_name in files:
                    paths.append(os.path.join(walk_root, file_name))
        return paths

    def _embed_texts(self, texts: List[str]) -> np.ndarray:
        batch_size = 96
        all_embeddings_list = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            response = self.cohere_client.embed(
                texts=batch,
                model=settings.COHERE_EMBEDDING_MODEL,
                input_type="search_document",
            )
            all_embeddings_list.extend(response.embeddings)
        return np.array(all_embeddings_list, dtype=np.float32)

    def ingest_directory(self, dir_path: Optional[str] = None) -> Tuple[int, int, List[str]]:
        """Mantiene compatibilidad con callers existentes (docs, chunks, categories)."""
        result = self.ingest_all(primary_dir=dir_path)
        return result.docs_processed, result.chunks_count, result.categories

    def ingest_all(self, primary_dir: Optional[str] = None) -> IngestResult:
        if primary_dir:
            os.makedirs(os.path.abspath(primary_dir), exist_ok=True)

        raw_paths = self._discover_raw_paths()
        accepted_paths, curation = curate_file_paths(raw_paths)
        self.last_curation = curation
        self.indexed_files = accepted_paths

        manifest = build_manifest(accepted_paths)
        cached = load_index(
            settings.DATA_DIR,
            manifest,
            settings.COHERE_EMBEDDING_MODEL,
        )

        if cached is not None:
            chunks_payload, embeddings = cached
            self.chunks = [DocumentChunk.from_dict(item) for item in chunks_payload]
            self.embeddings = embeddings
            self.categories = {c.category for c in self.chunks}
            self.last_cache_hit = True
            print(f"[CohereRAGService] ♻️ Índice cargado desde caché ({len(self.chunks)} fragmentos).")
            return IngestResult(
                docs_processed=len(accepted_paths),
                chunks_count=len(self.chunks),
                categories=sorted(self.categories),
                curation=curation,
                cache_hit=True,
            )

        self.last_cache_hit = False
        all_chunks: List[DocumentChunk] = []
        docs_processed = 0
        self.categories = set()

        for file_path in accepted_paths:
            category, _ = DocumentLoader.infer_metadata_from_path(file_path)
            self.categories.add(category)
            file_chunks = DocumentLoader.process_and_chunk_file(
                file_path,
                chunk_size=settings.CHUNK_SIZE_CHARS,
                overlap=settings.CHUNK_OVERLAP_CHARS,
            )
            if file_chunks:
                all_chunks.extend(file_chunks)
                docs_processed += 1

        if not all_chunks:
            self.chunks = []
            self.embeddings = np.array([])
            return IngestResult(0, 0, list(self.categories), curation, False)

        self.chunks = all_chunks

        if self.cohere_client:
            try:
                print(
                    f"[CohereRAGService] Generando embeddings para {len(all_chunks)} fragmentos "
                    f"({settings.COHERE_EMBEDDING_MODEL})..."
                )
                texts_to_embed = [c.content for c in all_chunks]
                self.embeddings = self._embed_texts(texts_to_embed)
                save_index(
                    settings.DATA_DIR,
                    manifest,
                    [c.to_dict() for c in all_chunks],
                    self.embeddings,
                    settings.COHERE_EMBEDDING_MODEL,
                )
                print(
                    f"[CohereRAGService] ✅ Indexación completada. "
                    f"Categorías: {len(self.categories)}. Shape: {self.embeddings.shape}"
                )
            except Exception as e:
                print(f"[CohereRAGService] ❌ Error en Cohere API: {e}")
                self.embeddings = np.array([])
        else:
            self.embeddings = np.array([])

        return IngestResult(
            docs_processed=docs_processed,
            chunks_count=len(self.chunks),
            categories=sorted(self.categories),
            curation=curation,
            cache_hit=False,
        )

    def search_relevant_chunks(
        self,
        query: str,
        category_filter: Optional[str] = None,
        top_k: int = 3,
        modified_after: Optional[str] = None,
    ) -> List[Dict]:
        if not self.chunks or self.embeddings.size == 0 or not self.cohere_client:
            return []

        try:
            candidate_indices = list(range(len(self.chunks)))
            if category_filter and category_filter.strip():
                candidate_indices = [
                    i
                    for i, chunk in enumerate(self.chunks)
                    if category_matches(chunk.category, category_filter)
                ]
                if not candidate_indices:
                    candidate_indices = list(range(len(self.chunks)))

            if modified_after:
                candidate_indices = [
                    i
                    for i in candidate_indices
                    if (self.chunks[i].modified_at or "") >= modified_after
                ]
                if not candidate_indices:
                    return []

            query_response = self.cohere_client.embed(
                texts=[query],
                model=settings.COHERE_EMBEDDING_MODEL,
                input_type="search_query",
            )
            query_embedding = np.array(query_response.embeddings[0], dtype=np.float32)

            cand_embeddings = self.embeddings[candidate_indices]
            norm_query = np.linalg.norm(query_embedding)
            norm_docs = np.linalg.norm(cand_embeddings, axis=1)

            norm_docs[norm_docs == 0] = 1e-10
            if norm_query == 0:
                norm_query = 1e-10

            similarities = np.dot(cand_embeddings, query_embedding) / (norm_docs * norm_query)
            top_cand_indices = np.argsort(similarities)[::-1][:top_k]

            results = []
            for c_idx in top_cand_indices:
                orig_idx = candidate_indices[c_idx]
                score = float(similarities[c_idx])
                chunk = self.chunks[orig_idx]
                results.append(
                    {
                        "content": chunk.content,
                        "source": chunk.source,
                        "category": chunk.category,
                        "owner": chunk.owner,
                        "author": chunk.author,
                        "location": chunk.location,
                        "modified_at": chunk.modified_at,
                        "score": round(score, 4),
                    }
                )

            return results

        except Exception as e:
            print(f"[CohereRAGService] ❌ Error en búsqueda semántica: {e}")
            return []

    def list_catalog_categories(self) -> List[str]:
        registered = list_business_categories()
        indexed = sorted(self.categories)
        merged = sorted(set(registered) | set(indexed))
        return merged

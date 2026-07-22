import os
import numpy as np
import cohere
from typing import List, Dict, Tuple, Optional
from app.config import settings
from app.services.document_loader import DocumentLoader, DocumentChunk

class CohereRAGService:
    """
    =============================================================================
    SERVICIO RAG CON API DE COHERE (EMBEDDINGS, CATEGORÍAS Y BÚSQUEDA SEMÁNTICA)
    =============================================================================
    Soporta la ingesta jerárquica de directorios por área (RH, Financiero, Jurídico, IT)
    y el filtrado por metadatos de categoría (Etapa 1: Mapeo y Curaduría de Datos).
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

    def ingest_directory(self, dir_path: str) -> Tuple[int, int, List[str]]:
        """
        Escanea recursivamente el directorio de datos corporativos, identificando
        subcarpetas por área (RH, Financiero, Jurídico, Tecnología, etc.) para
        indexar fragmentos enriquecidos con metadatos.
        """
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            return 0, 0, []

        all_chunks = []
        docs_processed = 0
        self.categories = set()

        # Recorrido recursivo (walk) para detectar subcarpetas de categorías
        for root, _, files in os.walk(dir_path):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                category, owner = DocumentLoader.infer_metadata_from_path(file_path)
                self.categories.add(category)

                file_chunks = DocumentLoader.process_and_chunk_file(file_path)
                if file_chunks:
                    all_chunks.extend(file_chunks)
                    docs_processed += 1


        if not all_chunks:
            self.chunks = []
            self.embeddings = np.array([])
            return docs_processed, 0, list(self.categories)

        self.chunks = all_chunks

        # Generación de Embeddings Vectoriales usando Cohere API
        if self.cohere_client:
            print(f"[CohereRAGService] Generando embeddings para {len(all_chunks)} fragmentos con Cohere ({settings.COHERE_EMBEDDING_MODEL})...")
            texts_to_embed = [c.content for c in all_chunks]
            
            try:
                batch_size = 96
                all_embeddings_list = []
                for i in range(0, len(texts_to_embed), batch_size):
                    batch = texts_to_embed[i:i + batch_size]
                    response = self.cohere_client.embed(
                        texts=batch,
                        model=settings.COHERE_EMBEDDING_MODEL,
                        input_type="search_document"
                    )
                    all_embeddings_list.extend(response.embeddings)

                self.embeddings = np.array(all_embeddings_list, dtype=np.float32)
                print(f"[CohereRAGService] ✅ Indexación de {len(self.categories)} categorías completada. Dimensiones: {self.embeddings.shape}")
            except Exception as e:
                print(f"[CohereRAGService] ❌ Error en Cohere API: {e}")
                self.embeddings = np.array([])
        else:
            self.embeddings = np.array([])

        return docs_processed, len(self.chunks), list(self.categories)

    def search_relevant_chunks(self, query: str, category_filter: Optional[str] = None, top_k: int = 3) -> List[Dict]:
        """
        Realiza búsqueda semántica con la API de Cohere (input_type="search_query")
        pudiendo filtrar por categoría específica si el usuario así lo solicita.
        """
        if not self.chunks or self.embeddings.size == 0 or not self.cohere_client:
            return []

        try:
            # 1. Aplicar filtro de categoría si está especificado
            candidate_indices = list(range(len(self.chunks)))
            if category_filter and category_filter.strip():
                candidate_indices = [
                    i for i, chunk in enumerate(self.chunks)
                    if category_filter.lower() in chunk.category.lower()
                ]
                if not candidate_indices:
                    # Si no hay coincidencias exactas con la categoría, buscar en todos los fragmentos
                    candidate_indices = list(range(len(self.chunks)))

            # 2. Embedding de la consulta
            query_response = self.cohere_client.embed(
                texts=[query],
                model=settings.COHERE_EMBEDDING_MODEL,
                input_type="search_query"
            )
            query_embedding = np.array(query_response.embeddings[0], dtype=np.float32)

            # 3. Similitud Coseno sobre los índices candidatos
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
                results.append({
                    "content": chunk.content,
                    "source": chunk.source,
                    "category": chunk.category,
                    "owner": chunk.owner,
                    "location": chunk.location,
                    "modified_at": chunk.modified_at,
                    "score": round(score, 4)
                })

            return results


        except Exception as e:
            print(f"[CohereRAGService] ❌ Error en búsqueda semántica: {e}")
            return []

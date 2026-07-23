"""
Persistencia local del índice vectorial (Etapa 3) para evitar re-embeddings en cada arranque.
"""
import json
import os
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from app.services.ingest_curation import file_content_hash


def _cache_dir(data_dir: str) -> str:
    path = os.path.join(os.path.abspath(data_dir), ".rag_cache")
    os.makedirs(path, exist_ok=True)
    return path


def build_manifest(file_paths: List[str]) -> List[Dict[str, Any]]:
    manifest: List[Dict[str, Any]] = []
    for path in sorted(file_paths):
        try:
            manifest.append(
                {
                    "path": os.path.abspath(path),
                    "hash": file_content_hash(path),
                    "mtime": os.path.getmtime(path),
                }
            )
        except OSError:
            continue
    return manifest


def save_index(
    data_dir: str,
    manifest: List[Dict[str, Any]],
    chunks_payload: List[Dict[str, Any]],
    embeddings: np.ndarray,
    embedding_model: str,
) -> None:
    base = _cache_dir(data_dir)
    meta = {
        "embedding_model": embedding_model,
        "manifest": manifest,
    }
    with open(os.path.join(base, "meta.json"), "w", encoding="utf-8") as handle:
        json.dump(meta, handle, ensure_ascii=False, indent=2)
    with open(os.path.join(base, "chunks.json"), "w", encoding="utf-8") as handle:
        json.dump(chunks_payload, handle, ensure_ascii=False)
    np.save(os.path.join(base, "embeddings.npy"), embeddings)


def load_index(
    data_dir: str,
    current_manifest: List[Dict[str, Any]],
    embedding_model: str,
) -> Optional[Tuple[List[Dict[str, Any]], np.ndarray]]:
    base = _cache_dir(data_dir)
    meta_path = os.path.join(base, "meta.json")
    chunks_path = os.path.join(base, "chunks.json")
    emb_path = os.path.join(base, "embeddings.npy")

    if not all(os.path.isfile(p) for p in (meta_path, chunks_path, emb_path)):
        return None

    try:
        with open(meta_path, "r", encoding="utf-8") as handle:
            meta = json.load(handle)
        if meta.get("embedding_model") != embedding_model:
            return None
        if meta.get("manifest") != current_manifest:
            return None
        with open(chunks_path, "r", encoding="utf-8") as handle:
            chunks_payload = json.load(handle)
        embeddings = np.load(emb_path)
        return chunks_payload, embeddings.astype(np.float32)
    except (OSError, json.JSONDecodeError, ValueError):
        return None

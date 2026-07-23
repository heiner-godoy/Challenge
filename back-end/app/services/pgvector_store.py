"""
Integración con PostgreSQL + pgvector.

Requisitos:
- Postgres con la extensión `vector` instalada (CREATE EXTENSION IF NOT EXISTS vector;)
- Variable de entorno `DATABASE_URL` configurada.

Nota: este adaptador crea una tabla simple con metadatos y una columna `vector(dim)`.
"""
from typing import List, Optional, Tuple
import os
import psycopg2
import psycopg2.extras
from psycopg2 import sql
import numpy as np

from app.config import settings


def _get_conn():
    if not settings.DATABASE_URL:
        raise RuntimeError("DATABASE_URL no está configurado en .env")
    return psycopg2.connect(settings.DATABASE_URL)


def init_table(dim: int):
    tbl = settings.PGVECTOR_TABLE
    with _get_conn() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            except Exception:
                # No fatal; informativo
                print("[pgvector_store] ⚠️ No se pudo crear/usar extensión 'vector'. Verifica permisos y que la extensión esté disponible.")
            cur.execute(
                sql.SQL(
                    """
                    CREATE TABLE IF NOT EXISTS {table} (
                        id SERIAL PRIMARY KEY,
                        source TEXT,
                        chunk_index INT,
                        category TEXT,
                        owner TEXT,
                        author TEXT,
                        location TEXT,
                        modified_at TEXT,
                        content TEXT,
                        embedding vector({dim})
                    );
                    """
                ).format(table=sql.Identifier(tbl), dim=sql.Literal(dim))
            )
            # unique constraint to allow upserts by source+chunk_index
            cur.execute(
                sql.SQL(
                    "ALTER TABLE {table} ADD CONSTRAINT IF NOT EXISTS uniq_src_chunk UNIQUE (source, chunk_index);"
                ).format(table=sql.Identifier(tbl))
            )
            # Create an index for ANN (ivfflat). If unsupported, will warn.
            try:
                cur.execute(
                    sql.SQL(
                        "CREATE INDEX IF NOT EXISTS {idx} ON {table} USING ivfflat (embedding) WITH (lists = 100);"
                    ).format(table=sql.Identifier(tbl), idx=sql.Identifier(f"{tbl}_emb_idx"))
                )
            except Exception:
                print("[pgvector_store] ⚠️ No se pudo crear índice ivfflat. Revisa versión de pgvector/privilegios.")


def _vec_to_text(vec: np.ndarray) -> str:
    return "[" + ",".join(map(str, vec.astype(float).tolist())) + "]"


def upsert_many(chunks: List[dict], embeddings: np.ndarray):
    """Inserta o actualiza múltiples fragmentos con sus embeddings."""
    if embeddings is None or len(embeddings) == 0:
        return
    tbl = settings.PGVECTOR_TABLE
    dim = embeddings.shape[1]
    init_table(dim)

    with _get_conn() as conn:
        with conn.cursor() as cur:
            for idx, chunk in enumerate(chunks):
                emb_text = _vec_to_text(embeddings[idx])
                # Use parameterized query and cast the text to vector
                cur.execute(
                    sql.SQL(
                        """
                        INSERT INTO {table} (source, chunk_index, category, owner, author, location, modified_at, content, embedding)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::vector)
                        ON CONFLICT (source, chunk_index) DO UPDATE SET
                          category = EXCLUDED.category,
                          owner = EXCLUDED.owner,
                          author = EXCLUDED.author,
                          location = EXCLUDED.location,
                          modified_at = EXCLUDED.modified_at,
                          content = EXCLUDED.content,
                          embedding = EXCLUDED.embedding;
                        """
                    ).format(table=sql.Identifier(tbl)),
                    (
                        chunk.get("source"),
                        chunk.get("chunk_index", idx),
                        chunk.get("category"),
                        chunk.get("owner"),
                        chunk.get("author"),
                        chunk.get("location"),
                        chunk.get("modified_at"),
                        chunk.get("content"),
                        _vec_to_text(embeddings[idx]),
                    ),
                )


def search(query_embedding: np.ndarray, top_k: int = 3, category_filter: Optional[str] = None) -> List[dict]:
    tbl = settings.PGVECTOR_TABLE
    dim = query_embedding.shape[0]
    with _get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            where_clause = ""
            params = []
            if category_filter and category_filter.strip():
                where_clause = "WHERE category ILIKE %s"
                params.append(f"%{category_filter}%")

            # Use Euclidean distance operator '<->' (pgvector)
            qtext = _vec_to_text(query_embedding)
            query = sql.SQL(
                "SELECT source, chunk_index, category, owner, author, location, modified_at, content, embedding <-> %s::vector AS distance "
                "FROM {table} "
                f"{where_clause} ORDER BY embedding <-> %s::vector LIMIT %s"
            ).format(table=sql.Identifier(tbl))

            # params: for where (optional), then query vector for distance, then again for distance, then limit
            exec_params = []
            if where_clause:
                exec_params.extend(params)
            exec_params.append(qtext)
            exec_params.append(qtext)
            exec_params.append(top_k)

            cur.execute(query, tuple(exec_params))
            rows = cur.fetchall()
            results = []
            for r in rows:
                results.append({
                    "content": r["content"],
                    "source": r["source"],
                    "category": r["category"],
                    "owner": r["owner"],
                    "author": r.get("author"),
                    "location": r.get("location"),
                    "modified_at": r.get("modified_at"),
                    "score": float(r.get("distance", 0.0)),
                })
            return results

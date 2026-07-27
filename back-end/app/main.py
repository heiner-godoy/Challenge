"""
=============================================================================
APLICACIÓN PRINCIPAL DE FASTAPI - AGENTE CORPORATIVO DE IA
=============================================================================
Configura las rutas API, los middlewares de CORS, los eventos de inicio
y coordina los servicios principales:
1. CohereRAGService: Búsqueda Semántica Vectorial con Embeddings de Cohere
2. GroqService: Inferencia de Lenguaje Natural con Groq Llama 3.3 70B
"""

import os
import re
from typing import List

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware

# Importaciones de configuración y esquemas Pydantic
from app.config import settings
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    DocumentSource,
    DocumentsListResponse,
    DocumentInventoryItem,
    IngestResponse,
    SourcesMapResponse,
    UploadResponse,
)

# Importaciones de los servicios del backend
from app.services.cohere_rag import CohereRAGService
from app.services.groq_service import GroqService
from app.services.category_registry import FRONTEND_AREA_TO_FOLDER
from app.services.document_loader import DocumentLoader
from app.services.ingest_curation import SUPPORTED_EXTENSIONS, should_skip_file

SAFE_FILENAME = re.compile(r"[^A-Za-z0-9._\- áéíóúñÁÉÍÓÚÑ]")

# ---------------------------------------------------------------------------
# BLOQUE 1: INICIALIZACIÓN DE LA APLICACIÓN FASTAPI Y MIDDLEWARES
# ---------------------------------------------------------------------------
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Backend en FastAPI para el Agente Corporativo de IA. "
        "Soporta Gobernanza de Datos por Categorías y Responsables (Etapa 1), "
        "Extracción Multi-formato Limpia y Chunking Estructurado (Etapa 2), "
        "Búsqueda Semántica Vectorial con Cohere y Inferencia Ultra-Rápida con Groq."
    )
)

# Configuración de Middleware CORS para permitir solicitudes desde el frontend web
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# BLOQUE 2: INSTANCIACIÓN DE SERVICIOS CORE
# ---------------------------------------------------------------------------
rag_service = CohereRAGService()     # Servicio RAG Vectorial con Cohere Embeddings
groq_service = GroqService()         # Servicio LLM Inferencia con Groq

# ---------------------------------------------------------------------------
# BLOQUE 3: EVENTO DE CICLO DE VIDA (STARTUP EVENT)
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    """
    EVENTO DE INICIO DEL SERVIDOR:
    Escanea e indexa automáticamente los documentos corporativos organizados
    en subcarpetas por áreas de negocio dentro del directorio /data.
    """
    data_dir = os.path.abspath(settings.DATA_DIR)
    print("=================================================================")
    print("🚀 INICIANDO AGENTE CORPORATIVO DE IA - DESAFÍO ALURA AGENTES")
    print(f"📁 Directorio de datos por áreas: {data_dir}")
    docs_proc, chunks_proc, categories = rag_service.ingest_directory(data_dir)
    print(f"✅ Ingesta inicial completada: {docs_proc} documentos, {chunks_proc} fragmentos indexados.")
    if rag_service.last_cache_hit:
        print("♻️ Índice reutilizado desde caché local (.rag_cache).")
    print(f"🏷️ Categorías/Áreas detectadas: {categories}")
    print("=================================================================")

# ---------------------------------------------------------------------------
# BLOQUE 4: ENDPOINTS DE DIAGNÓSTICO Y HEALTHCHECK
# ---------------------------------------------------------------------------
@app.get("/", summary="Ruta raíz de bienvenida")
def read_root():
    """Retorna información general sobre el estado de la API y el enlace a Swagger UI."""
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs_swagger": "/docs"
    }


@app.get("/health", summary="Verificación de estado del servidor")
@app.get("/api/health", summary="Verificación de estado del servidor (API v1)")
def health_check():
    """Retorna estadísticas operativas del sistema: documentos vectorizados y áreas disponibles."""
    return {
        "status": "healthy",
        "documents_indexed": len(rag_service.chunks),
        "documents_on_disk": len(rag_service.indexed_files),
        "categories_available": rag_service.list_catalog_categories(),
        "cache_hit_last_ingest": rag_service.last_cache_hit,
        "curation_last_ingest": {
            "scanned": rag_service.last_curation.scanned,
            "accepted": rag_service.last_curation.accepted,
            "skipped_draft": rag_service.last_curation.skipped_draft,
            "skipped_duplicate": rag_service.last_curation.skipped_duplicate,
            "skipped_unsupported": rag_service.last_curation.skipped_unsupported,
        },
    }


def _build_ingest_response(result_docs: int, result_chunks: int, categories: List[str]) -> IngestResponse:
    c = rag_service.last_curation
    return IngestResponse(
        status="success",
        documents_processed=result_docs,
        chunks_created=result_chunks,
        categories_found=categories,
        files_skipped_draft=c.skipped_draft,
        files_skipped_duplicate=c.skipped_duplicate,
        files_skipped_unsupported=c.skipped_unsupported,
        cache_hit=rag_service.last_cache_hit,
        message=(
            f"Ingesta exitosa. Se procesaron {result_docs} documentos en {len(categories)} categorías."
            + (" (caché reutilizada)" if rag_service.last_cache_hit else "")
        ),
    )


@app.get("/api/sources", response_model=SourcesMapResponse, summary="Mapa de fuentes de documentos")
def sources_map():
    extra = [part.strip() for part in (settings.EXTRA_DATA_DIRS or "").split(",") if part.strip()]
    return SourcesMapResponse(
        local_data_dir=os.path.abspath(settings.DATA_DIR),
        extra_data_dirs=extra,
        supported_formats=sorted(SUPPORTED_EXTENSIONS),
        note=(
            "Fuentes activas: carpetas locales bajo DATA_DIR y EXTRA_DATA_DIRS. "
            "Para Drive/SharePoint/OneDrive, monte la carpeta sincronizada y regístrela en EXTRA_DATA_DIRS."
        ),
    )


@app.get("/api/documents", response_model=DocumentsListResponse, summary="Inventario documental indexado")
def list_documents():
    items: List[DocumentInventoryItem] = []
    data_root = os.path.abspath(settings.DATA_DIR)
    for path in rag_service.indexed_files:
        category, owner = DocumentLoader.infer_metadata_from_path(path)
        rel = os.path.relpath(path, data_root)
        if rel.startswith(".."):
            rel = path
        items.append(
            DocumentInventoryItem(
                filename=os.path.basename(path),
                relative_path=rel.replace("\\", "/"),
                category=category,
                owner=owner,
                modified_at=DocumentLoader.get_file_modified_date(path),
            )
        )
    return DocumentsListResponse(
        documents=items,
        total=len(items),
        categories=rag_service.list_catalog_categories(),
    )


@app.post("/api/upload", response_model=UploadResponse, summary="Carga manual de documentos por área")
async def upload_documents(
    category: str = Form(..., description="Slug de área (ej: rh, financiero, logistica) o ID del frontend"),
    files: List[UploadFile] = File(...),
):
    if not files:
        raise HTTPException(status_code=400, detail="Debe enviar al menos un archivo.")

    folder_slug = FRONTEND_AREA_TO_FOLDER.get(category.strip().lower(), category.strip().lower())
    target_dir = os.path.join(os.path.abspath(settings.DATA_DIR), folder_slug)
    os.makedirs(target_dir, exist_ok=True)

    saved: List[str] = []
    for upload in files:
        if not upload.filename:
            continue
        safe_name = SAFE_FILENAME.sub("_", os.path.basename(upload.filename)).strip("._")
        if not safe_name:
            continue
        dest = os.path.join(target_dir, safe_name)
        skip, reason = should_skip_file(dest)
        if skip and reason == "draft":
            raise HTTPException(
                status_code=400,
                detail=f"El archivo parece borrador o copia y fue rechazado: {upload.filename}",
            )

        content = await upload.read()
        if not content:
            continue
        with open(dest, "wb") as handle:
            handle.write(content)
        saved.append(safe_name)

    if not saved:
        raise HTTPException(status_code=400, detail="Ningún archivo válido fue guardado.")

    try:
        rag_service.ingest_directory(os.path.abspath(settings.DATA_DIR))
    except Exception as exc:
        print(f"[upload_documents] ⚠️ Error al reindexar documentos tras la carga: {exc}")
        raise HTTPException(
            status_code=500,
            detail="El archivo se guardó, pero ocurrió un error al indexarlo. Revisa los logs del backend.",
        )

    return UploadResponse(
        status="success",
        saved_files=saved,
        category_folder=folder_slug,
        message=(
            f"Se guardaron {len(saved)} archivo(s) en data/{folder_slug}."
            " Se indexaron automáticamente."
        ),
    )

# ---------------------------------------------------------------------------
# BLOQUE 5: ENDPOINT DE RE-INGESTA Y RE-INDEXACIÓN DE DOCUMENTOS
# ---------------------------------------------------------------------------
@app.post("/api/ingest", response_model=IngestResponse, summary="Re-indexación de documentos corporativos")
def trigger_ingest():
    """
    Vuelve a escanear recursivamente la carpeta /data para cargar y procesar
    nuevos documentos o actualizaciones sin necesidad de reiniciar el backend.
    """
    data_dir = os.path.abspath(settings.DATA_DIR)
    docs_proc, chunks_proc, categories = rag_service.ingest_directory(data_dir)
    return _build_ingest_response(docs_proc, chunks_proc, categories)

# ---------------------------------------------------------------------------
# BLOQUE 6: ENDPOINT PRINCIPAL DE CHAT Y SÍNTESIS CON RAG (+ GOBERNANZA)
# ---------------------------------------------------------------------------
@app.post("/api/chat", response_model=ChatResponse, summary="Endpoint principal de consulta al Agente IA")
async def chat_endpoint(request: ChatRequest):
    """
    ENDPOINT PRINCIPAL DEL CHAT CONVERSACIONAL (/api/chat):
    1. Recibe la pregunta del usuario y el filtro opcional por categoría (RH, Finanzas, etc.).
    2. Ejecuta una búsqueda semántica con Cohere RAG obteniendo los 3 fragmentos más relevantes.
    3. Construye el prompt con las políticas de Gobernanza y Ownership y sintetiza la respuesta con Groq.
    4. Mapea las fuentes citadas detallando la ubicación exacta (Página, Diapositiva, Sección, Hoja/Fila) y fecha.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="La pregunta ingresada no puede estar vacía.")

    # Paso 1: Búsqueda semántica con filtrado por categoría si fue especificado
    relevant_chunks = rag_service.search_relevant_chunks(
        query=request.message,
        category_filter=request.category,
        top_k=3
    )

    # Paso 2: Inferencia de lenguaje natural con Groq Llama 3.3 70B
    history_dict = [msg.model_dump() for msg in request.history] if request.history else []
    answer_text = groq_service.generate_answer(
        query=request.message,
        context_chunks=relevant_chunks,
        history=history_dict
    )

    # Paso 3: Mapeo de fuentes citadas incluyendo Categoría, Ownership, Ubicación Exacta y Fecha
    sources = []
    if relevant_chunks:
        sources = [
            DocumentSource(
                filename=chunk["source"],
                category=chunk["category"],
                owner=chunk["owner"],
                author=chunk.get("author") or None,
                location=chunk.get("location", "General"),
                modified_at=chunk.get("modified_at", ""),
                excerpt=chunk["content"][:200] + "..." if len(chunk["content"]) > 200 else chunk["content"],
                score=chunk["score"],
            )
            for chunk in relevant_chunks
        ]

    return ChatResponse(
        answer=answer_text,
        sources=sources
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

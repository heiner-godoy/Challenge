"""
=============================================================================
APLICACIÓN PRINCIPAL DE FASTAPI - AGENTE CORPORATIVO DE IA
=============================================================================
Configura las rutas API, los middlewares de CORS, los eventos de inicio
y coordina los servicios principales:
1. CohereRAGService: Búsqueda Semántica Vectorial con Embeddings de Cohere
2. GroqService: Inferencia de Lenguaje Natural con Groq Llama 3.3 70B
3. TavilyService: Búsqueda Web en Tiempo Real integrada con LangChain
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Importaciones de configuración y esquemas Pydantic
from app.config import settings
from app.schemas.chat import ChatRequest, ChatResponse, DocumentSource, IngestResponse

# Importaciones de los servicios del backend
from app.services.cohere_rag import CohereRAGService
from app.services.groq_service import GroqService
from app.services.tavily_service import TavilyService

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
        "Búsqueda Semántica Vectorial con Cohere, Inferencia Ultra-Rápida con Groq "
        "y Búsqueda Web con Tavily + LangChain."
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
tavily_service = TavilyService()     # Servicio Búsqueda Web con Tavily + LangChain

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
    print(f"🏷️ Categorías/Áreas detectadas: {categories}")
    print(f"🌐 Estado de Tavily Search (LangChain): {'Activo ✅' if tavily_service.is_available() else 'Pendiente API Key ⚠️'}")
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
    """Retorna estadísticas operativas del sistema: documentos vectorizados, áreas disponibles y estado de Tavily."""
    return {
        "status": "healthy",
        "documents_indexed": len(rag_service.chunks),
        "categories_available": list(rag_service.categories),
        "tavily_search_available": tavily_service.is_available()
    }

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
    return IngestResponse(
        status="success",
        documents_processed=docs_proc,
        chunks_created=chunks_proc,
        categories_found=categories,
        message=f"Ingesta exitosa. Se procesaron {docs_proc} documentos en {len(categories)} categorías."
    )

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
    sources = [
        DocumentSource(
            filename=chunk["source"],
            category=chunk["category"],
            owner=chunk["owner"],
            location=chunk.get("location", "General"),
            modified_at=chunk.get("modified_at", ""),
            excerpt=chunk["content"][:200] + "..." if len(chunk["content"]) > 200 else chunk["content"],
            score=chunk["score"]
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

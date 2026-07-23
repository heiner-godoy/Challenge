from pydantic import BaseModel, Field
from typing import List, Optional

# =============================================================================
# BLOQUE DE ESQUEMAS PYDANTIC PARA VALIDACIÓN Y DOCUMENTACIÓN DE LA API
# =============================================================================

class ChatMessage(BaseModel):
    """
    =============================================================================
    ESQUEMA: MENSAJE INDIVIDUAL DEL HISTORIAL CONVERSACIONAL
    =============================================================================
    Estructura cada turno de conversación (usuario o asistente) enviado en el historial.
    """
    role: str = Field(
        ...,
        description="Rol del emisor del mensaje: 'user' para el colaborador o 'assistant' para el agente corporativo de IA"
    )
    content: str = Field(
        ...,
        description="Contenido textual del mensaje dentro de la sesión de chat"
    )


class ChatRequest(BaseModel):
    """
    =============================================================================
    ESQUEMA: PAYLOAD DE ENTRADA AL ENDPOINT /api/chat
    =============================================================================
    Define la estructura de la consulta recibida desde el frontend web:
    - La pregunta del usuario (message)
    - El filtro opcional por área organizativa (category)
    - El historial conversacional previo (history)
    """
    message: str = Field(
        ...,
        min_length=1,
        description="Pregunta enviada por el colaborador sobre procesos, políticas o documentación interna"
    )
    category: Optional[str] = Field(
        default=None,
        description="Filtro opcional por departamento (ej: 'Recursos Humanos', 'Finanzas y Presupuestos', 'Tecnología y Ciberseguridad')"
    )
    history: Optional[List[ChatMessage]] = Field(
        default=[],
        description="Historial de mensajes previos para ofrecer memoria y contexto conversacional contiguo"
    )


class DocumentSource(BaseModel):
    """
    =============================================================================
    ESQUEMA: FUENTE DOCUMENTAL CITADA EN EL RAG
    =============================================================================
    Representa una cita o fuente de sustento devuelta junto con la respuesta del agente.
    Incluye todos los metadatos de Gobernanza de Datos y Curaduría (Etapas 1 y 2):
    - Nombre del archivo y fecha de modificación
    - Categoría y Ownership (Responsable de Área)
    - Ubicación exacta (Página, Diapositiva, Sección o Hoja/Fila)
    - Extracto de texto y puntaje de relevancia
    """
    filename: str = Field(
        ...,
        description="Nombre del archivo original de la fuente (ej: politicas_rh.pdf)"
    )
    category: str = Field(
        default="General Corporativo",
        description="Categoría o departamento responsable de la fuente"
    )
    owner: str = Field(
        default="soporte@aluratech.com",
        description="Correo electrónico del responsable oficial del documento (Ownership)"
    )
    author: Optional[str] = Field(
        default=None,
        description="Autor del documento cuando está disponible en metadatos del archivo",
    )
    location: str = Field(
        default="General",
        description="Ubicación exacta dentro del documento (Página X, Diapositiva Y, Hoja Z - Fila N, Sección W)"
    )
    modified_at: Optional[str] = Field(
        default=None,
        description="Fecha de última actualización o modificación del documento fuente (YYYY-MM-DD)"
    )
    excerpt: str = Field(
        ...,
        description="Fragmento o extracto relevante de texto extraído del documento fuente"
    )
    score: float = Field(
        ...,
        description="Puntaje de similitud semántica calculado con métrica coseno (0.0 a 1.0)"
    )


class ChatResponse(BaseModel):
    """
    =============================================================================
    ESQUEMA: PAYLOAD DE SALIDA DEL ENDPOINT /api/chat
    =============================================================================
    Devuelve la respuesta final sintetizada por el LLM Groq fundamentada
    exclusivamente en las fuentes oficiales citadas.
    """
    answer: str = Field(
        ...,
        description="Respuesta final fundamentada generada por el agente de IA corporativo"
    )
    sources: List[DocumentSource] = Field(
        default=[],
        description="Lista de fuentes oficiales de la empresa citadas en la respuesta RAG"
    )


class IngestResponse(BaseModel):
    """
    =============================================================================
    ESQUEMA: RESPUESTA DEL PROCESO DE INGESTA DE DOCUMENTOS (/api/ingest)
    =============================================================================
    Resume el resultado del escaneo, limpieza, extracción y generación de embeddings.
    """
    status: str = Field(
        ...,
        description="Estado de la operación ('success' o 'error')"
    )
    documents_processed: int = Field(
        ...,
        description="Número total de archivos leídos y procesados"
    )
    chunks_created: int = Field(
        ...,
        description="Número total de fragmentos vectorizados en la base de conocimientos"
    )
    categories_found: List[str] = Field(
        default=[],
        description="Lista de categorías organizacionales detectadas en el sistema de archivos"
    )
    message: str = Field(
        ...,
        description="Mensaje explicativo del resultado del proceso de ingesta"
    )
    files_skipped_draft: int = Field(default=0, description="Archivos omitidos por parecer borrador o copia")
    files_skipped_duplicate: int = Field(default=0, description="Archivos duplicados omitidos por hash de contenido")
    files_skipped_unsupported: int = Field(default=0, description="Archivos con formato no soportado")
    cache_hit: bool = Field(default=False, description="True si el índice se cargó desde caché local")


class UploadResponse(BaseModel):
    status: str
    saved_files: List[str] = Field(default_factory=list)
    category_folder: str
    message: str


class DocumentInventoryItem(BaseModel):
    filename: str
    relative_path: str
    category: str
    owner: str
    modified_at: str


class DocumentsListResponse(BaseModel):
    documents: List[DocumentInventoryItem]
    total: int
    categories: List[str]


class SourcesMapResponse(BaseModel):
    local_data_dir: str
    extra_data_dirs: List[str] = Field(default_factory=list)
    supported_formats: List[str] = Field(default_factory=list)
    note: str

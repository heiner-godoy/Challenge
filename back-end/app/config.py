import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AliasChoices, Field

class Settings(BaseSettings):
    """
    =============================================================================
    CONFIGURACIÓN GLOBAL DE LA APLICACIÓN (FastAPI, LangChain, Cohere, Groq & Tavily)
    =============================================================================
    Gestiona centralizadamente las credenciales y variables de entorno definidas
    en el archivo .env utilizando Pydantic BaseSettings.
    """

    # ---------------------------------------------------------------------------
    # BLOQUE 1: INFORMACIÓN GENERAL Y METADATOS DEL SERVICIO FASTAPI
    # ---------------------------------------------------------------------------
    PROJECT_NAME: str = Field(
        default="Agente Corporativo IA - Desafío Alura Agentes",
        description="Nombre oficial del proyecto mostrado en la documentación Swagger/OpenAPI"
    )
    VERSION: str = Field(
        default="1.0.0",
        description="Versión semántica del backend"
    )
    API_V1_STR: str = Field(
        default="/api",
        description="Prefijo común para las rutas de la API v1"
    )

    # ---------------------------------------------------------------------------
    # BLOQUE 2: CLAVES DE API Y CREDENCIALES DE PROVEEDORES DE IA
    # ---------------------------------------------------------------------------
    # API Key para Cohere API (Embeddings y Búsqueda Semántica Vectorial)
    COHERE_API_KEY: str = Field(
        default="",
        description="Clave de API para el servicio de embeddings de Cohere"
    )
    
    # API Key para Groq API (LLM de Alta Velocidad llama-3.3-70b)
    GROQ_API_KEY: str = Field(
        default="",
        description="Clave de API para la inferencia de lenguaje natural con Groq"
    )
    
    # API Key para Tavily Search (Búsqueda Web en tiempo real con LangChain)
    # Soporta alias alternativos para evitar fallos si se escribe TAVILI_API_KEY o TAVILY_API_KEY
    TAVILY_API_KEY: str = Field(
        default="",
        validation_alias=AliasChoices("TAVILY_API_KEY", "TAVILI_API_KEY"),
        description="Clave de API para búsquedas en la web usando Tavily y LangChain"
    )

    # ---------------------------------------------------------------------------
    # BLOQUE 3: MODELOS Y RUTAS DE ALMACENAMIENTO
    # ---------------------------------------------------------------------------
    # Modelo Multilingüe de Embeddings para Cohere RAG
    COHERE_EMBEDDING_MODEL: str = Field(
        default="embed-multilingual-v3.0",
        description="Identificador del modelo vectorial de Cohere optimizado para español e inglés"
    )
    
    # Modelo LLM para Groq API
    GROQ_MODEL: str = Field(
        default="llama-3.3-70b-versatile",
        description="Modelo de lenguaje Llama 3.3 70B servido por la infraestructura ultra-rápida de Groq"
    )
    
    # Directorio de almacenamiento de documentos corporativos organizados por áreas
    DATA_DIR: str = Field(
        default="./data",
        description="Ruta relativa o absoluta donde se almacenan los documentos corporativos por categorías"
    )

    # ---------------------------------------------------------------------------
    # BLOQUE 4: CONFIGURACIÓN DE LECTURA DE ENTORNO (.env)
    # ---------------------------------------------------------------------------
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Instancia singleton accesible globalmente en toda la aplicación
settings = Settings()

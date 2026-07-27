import os
import csv
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AliasChoices, Field, field_validator

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    """
    =============================================================================
    CONFIGURACIÓN GLOBAL DE LA APLICACIÓN (FastAPI, Cohere y Groq)
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

    HOST: str = Field(
        default="0.0.0.0",
        description="Host en el que se ejecuta el servidor FastAPI"
    )

    PORT: int = Field(
        default=8000,
        description="Puerto en el que se ejecuta el servidor FastAPI"
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
        default=str(BASE_DIR / "data"),
        description="Ruta relativa o absoluta donde se almacenan los documentos corporativos por categorías"
    )

    EXTRA_DATA_DIRS: str = Field(
        default="",
        description="Rutas adicionales separadas por coma para mapeo de fuentes locales (Etapa 1)",
    )

    @field_validator('DATA_DIR', mode='before')
    @classmethod
    def normalize_data_dir(cls, value: str) -> str:
        if not value:
            return str(BASE_DIR / "data")
        path = Path(value).expanduser()
        if path.is_absolute():
            return str(path.resolve())
        return str((BASE_DIR / path).resolve())

    @field_validator('EXTRA_DATA_DIRS', mode='before')
    @classmethod
    def normalize_extra_dirs(cls, value: str) -> str:
        if not value:
            return ""
        normalized_paths = []
        for part in value.split(","):
            part = part.strip()
            if not part:
                continue
            path = Path(part).expanduser()
            normalized_paths.append(str(path.resolve() if path.is_absolute() else (BASE_DIR / path).resolve()))
        return ",".join(normalized_paths)

    CHUNK_SIZE_CHARS: int = Field(
        default=1000,
        description="Tamaño máximo de cada fragmento en caracteres (Etapa 2)",
    )

    CHUNK_OVERLAP_CHARS: int = Field(
        default=150,
        description="Solapamiento entre fragmentos consecutivos en caracteres (Etapa 2)",
    )

    # ---------------------------------------------------------------------------
    # BLOQUE 5: VECTOR STORE / PERSISTENCIA EXTERNA
    # ---------------------------------------------------------------------------
    VECTOR_STORE: str = Field(
        default="local",
        description="Modo de almacenamiento de vectores: 'local' o 'pgvector'",
    )

    DATABASE_URL: str = Field(
        default="",
        description="URL de conexión a Postgres (ej: postgres://user:pass@host:5432/dbname)",
    )

    PGVECTOR_TABLE: str = Field(
        default="pg_vector_embeddings",
        description="Nombre de la tabla donde guardar embeddings cuando VECTOR_STORE=pgvector",
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

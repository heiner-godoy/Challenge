# ⚙️ Service Backend — Agente Corporativo de IA

![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Cohere](https://img.shields.io/badge/Cohere-39594C?style=for-the-badge&logo=cohere&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-F54E00?style=for-the-badge&logo=groq&logoColor=white)
Backend desarrollado en **FastAPI** para el servidor del **Agente Corporativo de Inteligencia Artificial**. Integra un motor de ingesta y extracción multi-formato, búsqueda semántica vectorial basada en **Cohere Embeddings** y inferencia de respuestas con **Groq (Llama 3.3 70B)**.

---

## 📋 Tabla de Contenidos
- [🎯 Módulos y Arquitectura Backend](#-módulos-y-arquitectura-backend)
- [📄 Pipeline de Ingesta y Gobernanza de Datos](#-pipeline-de-ingesta-y-gobernanza-de-datos)
- [🔧 Descripción de Servicios (`app/services`)](#-descripción-de-servicios-appservices)
- [📦 Instalación y Configuración](#-instalación-y-configuración)
- [🌐 Endpoints de la API REST](#-endpoints-de-la-api-rest)
- [🧪 Pruebas y Diagnóstico](#-pruebas-y-diagnóstico)

---

## 🎯 Módulos y Arquitectura Backend

El backend se organiza en una arquitectura modular limpia orientada a servicios:

```
back-end/
├── main.py                    # Servidor ASGI principal (Uvicorn)
├── requirements.txt           # Lista de dependencias de Python
├── .env.example               # Plantilla de variables de entorno
├── .env                       # Variables de entorno locales
└── app/
    ├── config.py              # Gestión centralizada de credenciales (Pydantic BaseSettings)
    ├── main.py                # Enrutador FastAPI y definición de endpoints HTTP
    ├── schemas/
    │   └── chat.py            # Modelos de validación de datos de entrada/salida (Pydantic)
    └── services/
        ├── document_loader.py # Extracción por formato, Limpieza, Chunking y Metadatos
        ├── cohere_rag.py      # Motor Vectorial y Búsqueda Semántica Coseno
        ├── groq_service.py    # Servicio de Sintetización LLM con Gobernanza
        └── (sin servicios de búsqueda web externa)
```

---

## 📄 Pipeline de Ingesta y Gobernanza de Datos

El backend implementa de forma nativa las 4 etapas del pipeline de procesamiento documental:

### 1. Extracción por Formato Especializado
- **PDF Nativo y Escaneado**: Procesa página por página etiquetando la ubicación (`Página X`). Incluye *fallback* OCR con `pytesseract` si el PDF no posee capa de texto seleccionable.
- **Microsoft Word (`.docx`)**: Mantiene la estructura de encabezados (`Heading 1`, `Heading 2`) para la segmentación y extrae las tablas embebidas.
- **Microsoft PowerPoint (`.pptx`)**: Extrae el texto de las diapositivas e incluye **Notas del Orador** (*Speaker Notes*).
- **Microsoft Excel (`.xlsx`, `.xls`) & CSV**: Convierte planillas en oraciones estructuradas asociando cada valor con la cabecera correspondiente.
- **Markdown, JSON & HTML**: Elimina la sintaxis ruidosa y preserva el contenido técnico legible.

### 2. Limpieza de Texto Práctica (`clean_text`)
- Remueve caracteres nulos y no imprimibles (`\x00`).
- Elimina encabezados y pies de página repetitivos (ej: `Página X de Y`, `Confidencial`).
- Normaliza tabulaciones, espacios dobles y saltos de línea triples.

### 3. Chunking con Overlap
- Fragmenta el texto en ventanas deslizantes de ~500 caracteres con una superposición de 100 caracteres para evitar cortar oraciones por la mitad.

### 4. Atribución de Metadatos & Ownership
- Deduce automáticamente la **Categoría / Área de Negocio** y el **Ownership (Responsable)** basándose en la subcarpeta del archivo (`data/rh/`, `data/financiero/`, etc.).
- Asigna la **Ubicación Exacta** (`Página`, `Diapositiva`, `Hoja/Fila`, `Sección`) y la **Fecha de Modificación**.

---

## 🔧 Descripción de Servicios (`app/services`)

### 1. `DocumentLoader` ([`app/services/document_loader.py`](file:///home/heiner/repositorios-git/Challenge/back-end/app/services/document_loader.py))
Clase estática encargada de la carga, parseo, limpieza, fragmentación y metadatos de documentos corporativos.

### 2. `CohereRAGService` ([`app/services/cohere_rag.py`](file:///home/heiner/repositorios-git/Challenge/back-end/app/services/cohere_rag.py))
Gestiona el almacenamiento vectorial en memoria y utiliza el modelo `embed-multilingual-v3.0` de Cohere para calcular embeddings y realizar búsquedas de similitud coseno con filtrado por categorías.

### 3. `GroqService` ([`app/services/groq_service.py`](file:///home/heiner/repositorios-git/Challenge/back-end/app/services/groq_service.py))
Encargado de la inferencia de lenguaje natural utilizando el modelo `llama-3.3-70b-versatile` en Groq. Garantiza el cumplimiento de las normas de gobernanza corporativa citando fuentes y responsables.

---

## 📦 Instalación y Configuración

### 1. Crear y Activar el Entorno Virtual
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 3. Configurar el Archivo `.env`
Crea o edita el archivo `.env` en la raíz de `back-end/`:
```env
PORT=8000
HOST=0.0.0.0

COHERE_API_KEY="tu_cohere_api_key"
GROQ_API_KEY="tu_groq_api_key"

COHERE_EMBEDDING_MODEL=embed-multilingual-v3.0
GROQ_MODEL=llama-3.3-70b-versatile
DATA_DIR=./data
```

### 4. Iniciar el Servidor de Desarrollo
```bash
python main.py
```

---

## 🌐 Endpoints de la API REST

### `GET /api/health`
Verifica la salud del servidor backend.

**Respuesta**:
```json
{
  "status": "healthy",
  "documents_indexed": 42,
  "categories_available": ["Recursos Humanos", "Finanzas y Presupuestos"]
}
```

---

### `POST /api/ingest`
Re-escanea e indexa el directorio de datos corporativos `/data`.

**Respuesta**:
```json
{
  "status": "success",
  "documents_processed": 5,
  "chunks_created": 35,
  "categories_found": ["Recursos Humanos", "Finanzas y Presupuestos"],
  "message": "Ingesta exitosa. Se procesaron 5 documentos en 2 categorías."
}
```

---

### `POST /api/chat`
Endpoint principal para realizar consultas al agente de IA.

**Body (JSON)**:
```json
{
  "message": "¿Cuál es la política de reembolso de gastos de viaje?",
  "category": "Finanzas y Presupuestos",
  "history": []
}
```

**Respuesta (JSON)**:
```json
{
  "answer": "Los viáticos deben ser rendidos en un plazo máximo de 5 días hábiles adjuntando facturas electrónicas válidas. Para mayor detalle contactar al área de Finanzas.",
  "sources": [
    {
      "filename": "politica_gastos_viaje.pdf",
      "category": "Finanzas y Presupuestos",
      "owner": "finanzas@aluratech.com",
      "location": "Página 2",
      "modified_at": "2026-07-20",
      "excerpt": "Todo reembolso requiere comprobante tributario y aprobación del jefe inmediato...",
      "score": 0.9124
    }
  ]
}
```

---

## 🧪 Pruebas y Diagnóstico

Para probar rápidamente la carga de la aplicación y la inicialización de los servicios desde la terminal:

```bash
source .venv/bin/activate
python -c "from app.main import app; print('✅ Aplicación Backend lista e inicializada sin errores.')"
```

## 🔁 Integración con Vector DB (Qdrant / pgvector)

Este repositorio incluye persistencia local del índice vectorial en `data/.rag_cache` para acelerar reinicios. Si deseas integrar un vector database escalable, sigue estas recomendaciones:

- Opción Qdrant (nube o self-hosted): instala `qdrant-client` y configura `VECTOR_STORE=qdrant` junto con `QDRANT_URL` y `QDRANT_API_KEY`.
- Opción Postgres + pgvector: instala `psycopg2-binary` y configura conexión `DATABASE_URL` apuntando a una base con la extensión `pgvector`.

Se ha añadido un adaptador inicial `app/services/vector_store.py` como punto de extensión. La integración completa requiere decisiones de esquema (colección/index) y credenciales de despliegue.

Si quieres, puedo:

- Implementar la integración completa con Qdrant (crear colección, serializar metadatos y empujar embeddings). 
- O bien implementar almacenado en Postgres/pgvector con índices HNSW y filtros por metadatos.

Indica cuál opción prefieres y la creo en esta rama.

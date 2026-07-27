"""
=============================================================================
PUNTO DE ENTRADA PRINCIPAL DEL SERVIDOR BACKEND (ASGI / FASTAPI)
=============================================================================
Este archivo expone la instancia global de la aplicación FastAPI (`app`)
y permite ejecutar el servidor de desarrollo Uvicorn directamente desde
la raíz de la carpeta `back-end`.

Uso:
    $ python main.py
    o
    $ uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

from app.main import app
from app.config import settings

if __name__ == "__main__":
    import uvicorn
    # Inicializa el servidor web ASGI Uvicorn usando el host y puerto configurados en .env
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)

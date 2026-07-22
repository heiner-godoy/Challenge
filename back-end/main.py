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

if __name__ == "__main__":
    import uvicorn
    # Inicializa el servidor web ASGI Uvicorn en el puerto 8000 con recarga automática en desarrollo
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

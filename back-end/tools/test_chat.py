"""Pruebas locales para re-ingesta y consultas de chat (no usa uvicorn).

Ejecución:
    /home/heiner/repositorios-git/Challenge/back-end/.venv/bin/python tools/test_chat.py
"""
from fastapi.testclient import TestClient
import json

from app.main import app

client = TestClient(app)

print('== Iniciando prueba: POST /api/ingest ==')
resp = client.post('/api/ingest')
print('Status:', resp.status_code)
try:
    print(json.dumps(resp.json(), indent=2, ensure_ascii=False))
except Exception:
    print(resp.text)

print('\n== Prueba: /api/chat -> "¿Cómo rastreo mi pedido?" ==')
payload = {
    'message': '¿Cómo rastreo mi pedido?',
    'category': 'logistica',
    'history': []
}
resp2 = client.post('/api/chat', json=payload)
print('Status:', resp2.status_code)
try:
    print(json.dumps(resp2.json(), indent=2, ensure_ascii=False))
except Exception:
    print(resp2.text)

print('\n== Prueba: /api/chat -> "Quiero restaurar un pedido" ==')
payload3 = {
    'message': 'Quiero restaurar un pedido',
    'category': 'logistica',
    'history': []
}
resp3 = client.post('/api/chat', json=payload3)
print('Status:', resp3.status_code)
try:
    print(json.dumps(resp3.json(), indent=2, ensure_ascii=False))
except Exception:
    print(resp3.text)
